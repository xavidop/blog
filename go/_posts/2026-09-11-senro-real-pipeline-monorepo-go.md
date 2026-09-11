---
layout: post
title: "Building a Real Pipeline with senro: Monorepos, Caching and Triggers (English)"
description: >
  A practical guide to the parts of senro you use every day: checking code out into a workspace, caching a step so it never runs twice, fanning one step out over every module in a monorepo, narrowing that fan-out to only what a change affects, and letting the pipeline binary decide for itself whether a webhook is its business.
image: /assets/img/blog/post-headers/senro-real-pipeline.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [go]
tags:
  - go
  - golang
  - senro
  - monorepo
  - ci-cd
  - caching
keywords:
  - go
  - golang
  - senro
  - monorepo
  - fan-out
  - affected
  - go-workspace
  - action-cache
  - caching
  - triggers
  - webhooks
  - ci-cd
  - pipelines
  - devops

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

In the [introduction to senro]({% post_url go/2026-09-11-introducing-senro-pipeline-engine-go %}) I covered the model: a pipeline is a Go program, it builds an immutable plan, and the engine executes that plan while anything can attach to the event stream.

This article is the practical follow-up. It covers the five things you will actually write on your first real pipeline: getting your code into a step, caching a step so it never runs the same work twice, fanning one step out over every module in a monorepo, narrowing that fan-out to only what a change touches, and deciding whether a webhook should start a run at all.

Everything below was run against `senro v1.4.0`.

## A pipeline that builds a real repository

Here is the shape of a Go CI pipeline in senro. Check the code out into a workspace, vet and test it in parallel, then build:

```go
// Command ci checks the repo out into a workspace, then vets, tests and
// builds it.
package main

import (
	"context"
	"log"
	"os"

	"github.com/xavidop/senro"
	"github.com/xavidop/senro/artifact"
	"github.com/xavidop/senro/exec"
	"github.com/xavidop/senro/retry"
)

func main() {
	ctx := context.Background()

	repo := os.Getenv("REPO_URL")
	home := os.Getenv("HOME")

	p := senro.New("ci")

	// One directory for this run, mounted by every step that needs the code.
	src := senro.Workspace("src", senro.Scope(senro.ScopeRun))

	verify := p.Workflow("verify")

	verify.Step("checkout", exec.Command("git", "clone", "--depth", "1", repo, ".")).
		WorkDir("/src").
		Mount(src.At("/src", senro.RW)).
		Retry(3, retry.OnInfra())

	verify.Step("vet", exec.Command("go", "vet", "./...")).
		Needs("checkout").
		WorkDir("/src").
		Mount(src.At("/src", senro.RO)).
		Env("HOME", home)

	verify.Step("test", exec.Command("go", "test", "./...")).
		Needs("checkout").
		WorkDir("/src").
		Mount(src.At("/src", senro.RO)).
		Env("HOME", home)

	verify.Step("build", exec.Command("go", "build", "-o", "bin/app", "./cmd/app")).
		Needs("vet", "test").
		WorkDir("/src").
		Mount(src.At("/src", senro.RW)).
		Env("HOME", home).
		Pure().
		Inputs(artifact.Glob("**/*.go"), artifact.File("go.sum")).
		Outputs(artifact.File("bin/app")).
		Retry(3, retry.OnInfra())

	if err := senro.Run(ctx, p); err != nil {
		log.Print(err)
		os.Exit(1)
	}
}
```

```
test stdout | ?   	senrolab/ci	[no test files]
test stdout | ?   	senrolab/cmd/app	[no test files]
test stdout | ok  	senrolab/greet	0.360s
```

The graph those `Needs` calls describe, rendered from the run's own `plan.json`:

```
pipeline: ci
  │
  ├─ wave 1                checkout          retry 3/infra
  │
  ├─ wave 2 (2 parallel)   test
  │                        vet
  │
  └─ wave 3                build             needs vet, test · retry 3/infra
```

Two things in there are not obvious coming from a CI system that hands you a checkout and a shell.

### Workspaces: how code reaches a step

Every step runs in an **isolated, empty working directory**. Nothing hands you a checkout, because "hand the step a checkout" means four different things across a local process, a container, a pod and an SSH host.

A `Workspace` is a named, versioned directory that steps mount. senro snapshots it into a content-addressed store when a step that mounts it finishes, and restores it for the next step that needs it. So the code gets into the run the way it gets into any CI runner: the `checkout` step clones it, and the `src` workspace carries the result to the other three.

Mount modes matter:

| Mode | Use it when |
|---|---|
| `senro.RW` | The step writes into the workspace, including its declared `Outputs` |
| `senro.RO` | The step only reads |

In the pipeline above, `checkout` is `RW` because it writes the tree, `vet` and `test` are `RO` because they only read it, and `build` is `RW` because its output lands there.

`ws.At(path, mode)` always needs a mode, `Mount` accumulates so one step can mount several things, and two mounts at one path are refused at build time.

Workspaces come in three scopes:

| Scope | What you get |
|---|---|
| `senro.ScopeRun` | The default. One directory for this run, shared by every step that mounts it |
| `senro.ScopePersistent` | One directory on this machine that outlives the run. Requires explicit bounds |
| `senro.ScopeStep` | One fresh directory per step, shared with nobody |

### Declaring the environment

`Build()` adds nothing to a step's environment. Not a `HOME`, not a `GOPATH`, nothing. The local executor supplies its own `PATH` and that is all.

This is deliberate: two developers on the same commit produce the same plan because nothing about their shells leaks into it, and the environment is one of the eleven components a cache key is computed from. In practice it means tools that need something get told about it:

```go
.Env("HOME", home)
```

`Env` takes one pair per call, and it is not variadic on purpose: `Env("A", "1", "B")` would compile and mean nothing.

## Caching a step with `Pure()`

`Pure()` is a promise: given these inputs, this command produces these outputs, and nothing else matters. senro hashes the inputs, the command, the environment, the workspaces, the mount shape and six other things into a key. On a second run with the same key the step is **not executed at all** and its recorded outputs are restored.

Running the pipeline above twice:

```
RUN ID                      PIPELINE  STATUS     STARTED              DURATION
20260911T105259-8fc9b32e31  ci        succeeded  2026-09-11 19:52:59  1s
20260911T105243-8b696eb1d0  ci        succeeded  2026-09-11 19:52:43  2s
```

```
$ senro cache explain --run 20260911T105259-8fc9b32e31 build
HIT  build  key a52a9b6c
```

The event stream records it as a state, not a label:

```json
{"type":"cache.hit","step":"build",
 "payload":{"key":"sha256:a52a9b6c...","from_run":"20260911T105243-8b696eb1d0"}}
{"type":"step.finished","step":"build","payload":{"state":"cached","cached":true}}
```

Touch a source file and the same command tells you exactly why it has to run again:

```
MISS  build  key 0e769472 (previous a52a9b6c)
  ✗ input_digests: ci/main.go  ee7563f3 → 4f7d4315
  ✗ input_digests: greet/greet.go  59d2873d → 57930022
  ✗ input_digests: probe/main.go  added
  ✗ workspace_digests: src  f377ce04 → de2069cc
  ✓ command, env, secrets, executor_class, platform, mount_shape, step_shape, func_identity,
    tool_versions, version unchanged
```

One rule about the key is worth memorising, because it decides how you structure a fan-out:

> **`Mount` puts the whole mounted workspace into the cache key.** `Inputs` narrows what you declare as sources, but it does not narrow the workspace component. A step that mounts a big shared tree has a key that depends on that entire tree.

The practical consequence: when you cache expensive per-unit work, give each unit its own workspace instead of sharing one.

## Read-only mounts are enforced

A step that writes through an `RO` mount fails, and says so:

```
engine: step "build[unit=services/api]" wrote through its read-only mount of workspace "tree"
(c9271303 became 832bb638); a read-only mount that changes makes every cache key computed from
it wrong
```

That one is `go build` dropping a compiled binary next to the source. The fix is `go build -o /dev/null ./...`, which is what a build check wanted anyway.

How the rule is enforced depends on the executor, and it is worth knowing which you are relying on:

| Executor | What `senro.RO` does | When a write is caught |
|---|---|---|
| Container | A real read-only bind mount | At the write. It fails |
| Kubernetes | `readOnly` on the volume mount | At the write. It fails |
| Local | Nothing at mount time | Right afterwards, when the workspace is found changed |
| SSH | Nothing on the far side | On read-back. The write is reported, not carried home |

On local and SSH, read-only is a request senro checks after the fact rather than a rule the kernel enforces. Keep sensitive input out of any workspace a step could overwrite by mistake.

## Monorepos: fan out with `Expand`

`Expand(id, graph)` adds one step per unit that a graph discovers. Add a module, get a step, and nobody has to write it.

Here is a Go workspace with four modules and a dependency chain three deep:

```
libs/log  <-  libs/config  <-  services/api
libs/log  <-  services/worker
```

```go
verify.Expand("build", gowork.Modules()).
	MaxParallel(4).
	Needs("checkout").
	Affected(src).
	Template(func(u senro.Unit) *senro.StepBuilder {
		// WorkDir is the mount point itself, and go -C moves into the unit.
		return senro.NewStep(exec.Command("go", "-C", u.Dir, "build", "-o", "/dev/null", "./...")).
			WorkDir("/tree").
			Mount(tree.At("/tree", senro.RO)).
			Env("HOME", home)
	})
```

```
checkout                     -> succeeded
build[unit=libs/log]         -> succeeded
build[unit=libs/config]      -> succeeded
build[unit=services/worker]  -> succeeded
build[unit=services/api]     -> succeeded
```

One `Expand` call, four nodes in the plan:

```
pipeline: mono (no change filter)
  │
  ├─ wave 1                checkout
  │
  └─ wave 2 (4 parallel)   build[unit=libs/config]
                           build[unit=libs/log]
                           build[unit=services/api]
                           build[unit=services/worker]
```

`Template` is called once per unit in sorted order and must return a **fresh** `*senro.StepBuilder`, built with `senro.NewStep`. Each unit gives you:

| On `Unit` | What it is |
|---|---|
| `u.ID`, `u.Name` | The unit's stable identity |
| `u.Dir` | The unit's directory, relative to the root |
| `u.Base()` | The last path segment: `"web"` for `"apps/web"` |
| `u.Sources()` | Every file under the unit, ready for `.Inputs(...)` on a `Pure()` template |

Child ids come from the expansion id and the unit (`build[unit=libs/log]`), never a name the template picks, so the same repository always builds the same graph and a re-run reconstitutes the same children.

Two bounds are worth setting. `MaxParallel(n)` limits how many children of this expansion run at once. `MaxNodes(n)` rejects an expansion wider than `n` at **build** time, default 500, so a scheduler never discovers mid-run that it has forty thousand sandboxes to hold open.

Expansion happens once, at `Build()`. Every unit is discovered and written into the plan before the first step starts.

### The eight unit graphs

| Graph | Discovers |
|---|---|
| `glob.Dirs` / `glob.Files` | One unit per matching directory, or per directory containing a matching file |
| `gowork` | Go workspace modules |
| `cargo` | Rust workspace crates |
| `jswork` | npm, pnpm or yarn workspaces |
| `maven`, `gradle` | JVM modules |
| `pyproject` | Python projects |
| `bazel` | Bazel packages |

`glob` just matches paths. The others read the ecosystem's own manifests, which is what makes the next section work.

### Running only what a change affects

`Affected(src)` narrows the fan-out to the units a change reaches: the ones owning a changed file, **and everything that depends on them, at any depth**.

The same pipeline, told that one file changed:

```
=== changed: services/api/main.go ===
   build[unit=services/api]

=== changed: libs/config/config.go ===
   build[unit=libs/config]
   build[unit=services/api]

=== changed: libs/log/log.go ===
   build[unit=libs/config]
   build[unit=libs/log]
   build[unit=services/api]
   build[unit=services/worker]
```

The third case is the point. `services/api` does not import `libs/log`. It imports `libs/config`, which does. That transitive hop is why reading manifests beats globbing paths, and it is why `Affected` over a `glob` graph is **refused at build time**: a path does not know what imports it, and senro would rather say so than quietly run everything.

Unaffected units are not skipped, they are not in the plan at all. That is visible in the plan itself. Same pipeline, same `Expand`, told that `libs/config/config.go` changed:

```
pipeline: mono (libs/config changed)
  │
  ├─ wave 1                checkout
  │
  └─ wave 2 (2 parallel)   build[unit=libs/config]
                           build[unit=services/api]
```

Two nodes instead of four, decided at build time. `libs/log` and `services/worker` are not present to be skipped, so a re-run of this recorded plan reconstitutes exactly these two.

The change source is pluggable:

| Source | What it is |
|---|---|
| `change.FromTrigger(ev)` | What the webhook that started the run recorded |
| `change.Paths("a/x.go", ...)` | A literal list, for your own logic and for tests |
| `change.Everything()` | Every unit runs |
| `change.Ignoring(src, "docs/**")` | The above, minus paths you do not care about |

> `change.Paths()` with no arguments means **nothing changed**, not everything. Use `change.Everything()` for that. They are different answers.

### Keep the run directory out of the tree

senro writes each run to `runs/<id>/` under the working directory. That directory holds the run's workspaces, and a workspace usually holds a checkout of the repository. Unit graphs walk the filesystem for manifests, pruning only `.git` and `node_modules`, so a second run will discover the first run's checkout as a second copy of every module:

```
build[unit=runs/20260911T105558-08e7daff14/ws/tree/services/api]
```

Pin the run directory somewhere outside the tree you fan out over:

```go
senro.Run(ctx, p, senro.WithDir("/var/lib/senro/runs/"+runID))
```

Adding `runs/` to `.gitignore` does not help, because the unit graph is walking the filesystem, not asking git.

## Triggers: the pipeline decides whether to run

Instead of a CI service deciding whether to invoke your pipeline, **the pipeline binary is its own matcher**. Hand it a webhook delivery and it decides whether the event is its business:

```go
err = senro.Run(ctx, pipeline(ev),
	senro.WithTrigger(ev,
		// A push to main reports mode "all", which change.FromTrigger passes
		// straight through: everything builds there.
		trigger.OnPush(trigger.Branches("main")),
		// Everything else is narrowed to what it touched.
		trigger.OnPush(),
		trigger.OnPullRequest(trigger.Actions("opened", "synchronize")),
	))
```

A push to a topic branch that touched `services/api/main.go` runs one step. A tag push, which this pipeline does not want, runs nothing and says why:

```
$ go run ./examples/monorepo --trigger-event /tmp/ev-tag.json
senro: trigger: no trigger matched the event: tag refs/tags/v1.2.3
  push(branches=[main]): only answers push events, this was tag
  push: only answers push events, this was tag
  pull_request(actions=[opened synchronize]): only answers pull_request events, this was tag
exit status 78
```

Exit code 78 is `EX_CONFIG`, the conventional "this was not my business". One line per matcher explaining why it declined, which is a better answer than a GitHub Actions `on:` block that silently did not fire.

GitHub, GitLab, Bitbucket and Gitea ship, plus your own provider. And the event file is optional: `trigger.FromRequest` verifies and parses a delivery straight off the wire, per source, so the pipeline binary can be the HTTP endpoint itself.

Because the matcher is a binary, you can test a trigger decision locally against a saved payload before it ever reaches a runner.

## Handlers: cleanup and evidence

`OnFailure` runs its handlers once retries are exhausted and the step still failed. `Always` runs whatever the outcome. A handler can be a Go function, and it knows what it is cleaning up after:

```go
func Collect(ctx senro.Ctx, _ ReportParams) error {
	f, ok := ctx.Failure()
	if !ok {
		return errors.New("ship/collect only makes sense as a handler")
	}
	fmt.Fprintf(ctx.Stdout(), "%s ended %s (exit %d) on attempt %d\n",
		f.Step, f.State, f.ExitCode, f.Attempt)
	fmt.Fprintf(ctx.Stdout(), "log tail: %q\n", f.LogTail)
	return nil
}

// in the pipeline:
build.Step("package", exec.Command("sh", "-c", "echo packaging; exit 1")).
	OnFailure(senro.Handler("collect", senro.Func("ship/collect", ReportParams{}))).
	ContinueOnError()
```

```
package ended failed (exit 1) on attempt 1
log tail: "packaging\n"
```

The log tail arrives with the failure, so a handler that classifies errors never has to open a file. Handlers run in the order listed, and a handler that fails never masks the step's own failure: the recorded cause stays the original step.

Use `senro.Handler(id, action)` rather than a workflow's `Step`. Passing a real step to `OnFailure` is rejected at build time, because that step would otherwise run twice. A handler also gets its parent's workspaces read-only at the same paths automatically, so `Mount` on one is refused.

## Conclusion

Put the pieces together and the argument is not about syntax.

The fan-out is a function called once per unit, so what your build does is testable with `go test`. The `Affected` graph reads your ecosystem's manifests, so a change to a shared library rebuilds the things that transitively depend on it and nothing else. The cache tells you which of eleven key components changed when it misses. The trigger decision happens in a binary you can run locally against a saved payload. And the whole thing is a Go module with a `go.sum`, reviewed like the rest of your code.

None of that is impossible in YAML. It is that in YAML each one is a plugin, a marketplace action, a service feature or four hundred lines of bash, and here they are library calls in a language with a compiler.

Next in this series:

- **[Genkit flows as senro steps]({% post_url genkit/2026-09-11-genkit-flows-senro-ai-pipelines-go %})**: AI pipelines where every model call is a graph node with its own retry, log and cache entry.
- **[Debugging senro pipelines]({% post_url go/2026-09-11-debugging-senro-pipelines %})**: replaying a finished run, shelling into a live step, and auditing a cache.

senro lives at [github.com/xavidop/senro](https://github.com/xavidop/senro).
