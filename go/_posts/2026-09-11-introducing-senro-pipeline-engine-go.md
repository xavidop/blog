---
layout: post
title: "Introducing senro: A Pipeline Engine You Program in Go (English)"
description: >
  CI systems ask you to describe real programming (dependency graphs, retries, branching, recovery) in YAML, a language with no functions, no types, no tests and no debugger. senro is a new open-source pipeline engine that starts from the other end: the pipeline is the Go program. It builds an immutable plan, runs it locally, in containers, on Kubernetes or over SSH, and exposes one event stream you can attach to live.
image: /assets/img/blog/post-headers/senro.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [go]
tags:
  - go
  - golang
  - senro
  - ci-cd
  - pipelines
  - devops
keywords:
  - go
  - golang
  - senro
  - ci-cd
  - pipeline
  - pipeline-as-code
  - build-system
  - dependency-graph
  - caching
  - kubernetes
  - containers
  - ssh
  - devops
  - yaml

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

Every CI configuration I have ever maintained follows the same arc. It starts as twenty lines of YAML. Then a step needs to run only on `main`, so there is an `if`. Then two steps run in parallel and a third needs both, so there is a `needs` block. Then a flaky registry breaks the build weekly, so there is a retry, which also retries the failing test, which is exactly wrong. Then someone needs a loop over six services, the templating language does not have one, and the whole thing collapses into a single `run:` block holding four hundred lines of bash.

At that point the CI configuration is not configuration. It is a program, written in a language with no functions, no types, no tests and no debugger, executed by a service that can only tell you whether it went green.

**[senro](https://github.com/xavidop/senro)** (線路, Japanese for *railway track*) is my answer to that. It is an open-source pipeline engine you program instead of configure: your Go code builds an immutable graph of workflows and steps, senro resolves it into a plan, executes it, and exposes one append-only event stream that a terminal UI, a browser page or a script can attach to, live, to watch and steer the run.

CI/CD is the most familiar thing to build with it, but not the boundary. A data pipeline, a batch job, an infrastructure rollout or a release script is built the same way: steps with dependencies, retries, failure handlers and one event stream.

This article is the tour. Every command and every output in it was run against `senro v1.4.0` on Go 1.27.1.

## The premise

CI systems ask you to describe real programming in a data format. So the logic ends up in shell scripts the YAML merely invokes, and you lose everything a language gives you at exactly the layer that decides whether your build ships.

senro starts from the other end: **the pipeline *is* the Go program**. For the thing that decides whether your code ships, you get the compiler, types, `go test`, and a debugger.

That has practical consequences before it has philosophical ones. A loop over six services is a `for` loop. Shared configuration between two pipelines is a function. A tricky bit of branching logic is a function with a unit test. None of those need a plugin, a marketplace action or a templating dialect.

## Install

The CLI:

```bash
brew install xavidop/tap/senro
# or
go install github.com/xavidop/senro/cmd/senro@latest
```

The library, which is all a pipeline actually needs:

```bash
go get github.com/xavidop/senro
```

> **Heads up:** senro requires **Go 1.26 or newer**, on Linux or macOS. Windows is deliberately unsupported: attach's security boundary is a kernel peer-credential check with no Windows equivalent implemented, and senro fails closed rather than advertising a feature it cannot secure.

Released binaries for linux and darwin on amd64 and arm64, with checksums, SBOMs and SLSA provenance, are on the [releases page](https://github.com/xavidop/senro/releases).

## Getting started

A pipeline is a Go package with a `main` that builds a `senro.Pipeline` and calls `senro.Run`. This one is a diamond: one step, then two in parallel, then one that waits for both.

```go
// Command first is the smallest senro pipeline that says something.
package main

import (
	"context"
	"log"
	"os"

	"github.com/xavidop/senro"
	"github.com/xavidop/senro/exec"
	"github.com/xavidop/senro/retry"
)

func main() {
	ctx := context.Background()

	p := senro.New("first")

	ci := p.Workflow("ci")
	ci.Step("fetch", exec.Command("echo", "fetching dependencies"))
	ci.Step("lint", exec.Command("echo", "linting")).Needs("fetch")
	ci.Step("test", exec.Command("echo", "testing")).Needs("fetch")
	ci.Step("build", exec.Command("echo", "building")).
		Needs("lint", "test").
		Retry(3, retry.OnInfra())

	if err := senro.Run(ctx, p); err != nil {
		log.Print(err)
		os.Exit(1)
	}
}
```

Run it with the CLI, which builds the package, execs it and attaches automatically. On a TTY you get a terminal UI; anywhere else you get plain lines:

```bash
senro run ./first
```

```
fetch stdout | fetching dependencies
fetch succeeded
lint stdout | linting
lint succeeded
test stdout | testing
test succeeded
build stdout | building
build succeeded
run succeeded
```

Those four `Step` calls describe a graph, and the graph is what the engine actually runs. Rendered from the run's own `plan.json`:

```
pipeline: first
  │
  ├─ wave 1                fetch
  │
  ├─ wave 2 (2 parallel)   lint
  │                        test
  │
  └─ wave 3                build             needs lint, test · retry 3/infra
```

`lint` and `test` run at the same time because nothing orders them against each other, and `build` waits for both because it said so. You never wrote a scheduler.

The vocabulary is five words, and the rest of the API is a detail of one of them:

| Term | What it is |
|---|---|
| `Pipeline` | A name and a set of workflows: `senro.New("ci")` |
| `Workflow` | A named group of steps: `p.Workflow("ci")` |
| `Step` | One action: a command, or a registered Go function |
| `Plan` | The validated, immutable graph that `Build()` resolves a pipeline into |
| Event stream | The append-only record of everything a run did |

Step ids are unique across the whole pipeline, not per workflow, because a plan is flat.

That `Retry(3, retry.OnInfra())` is worth a sentence on its own. It allows up to three attempts, but **only when the environment failed the step**: a dropped connection, a killed process, a registry hiccup. It never retries a command that ran and returned non-zero. Retrying a dropped SSH connection is sane. Retrying a failing test until it passes deletes what it just told you.

## Definition, plan, execution

This is the one concept worth internalising, because everything else follows from it.

Your code does not execute anything. It builds a description. `Build()` resolves that description into an immutable, validated `Plan`, and the engine executes **the plan**, never your code:

```go
plan, err := p.Build() // a validated snapshot
if err != nil {
	log.Fatal(err)
}
fmt.Println("about to run", plan.Digest())
if err := senro.RunPlan(ctx, plan); err != nil {
	log.Fatal(err)
}
```

`senro.Run` does the `Build()` for you. Because it builds first, **mistakes surface before anything executes**: a dangling `Needs`, a duplicate step id or an empty command comes back as an error, not as a half-finished run that already deployed something.

The refusals are specific enough to act on directly. A func step that declares a working directory it can never honour:

```
plan: step "summarize/alpha" is a func step and sets WorkDir "/tree", which it never runs in:
a func step on the coordinator runs in the coordinator's own process, where the working directory
is process-global, so honouring it would move every step running alongside it. Reach files through
ctx.Workspace(name), which hands a function the same path a mount gives a command, on every executor
```

A step that opts into caching without saying what it reads:

```
plan: step "summarize/alpha" is Pure() with no Inputs, so its cache key would not change when
its sources do: declare them with Inputs(artifact.Glob(...))
```

Each one names what you wrote, why it cannot hold, and what to write instead.

The separation is also what lets a **second process** watch a run. An attached terminal reads the same `Plan` the engine is executing, which it could never reconstruct by watching your function calls go by.

## One event stream, and nothing else

Every observable fact about a run is an `api.Event`, appended in order, never rewritten. Real lines from a `runs/<id>/events.jsonl`, trimmed for width:

```json
{"seq":21,"type":"cache.hit","run":"20260911T105259-8fc9b32e31","step":"build",
 "payload":{"key":"sha256:a52a9b6c...","from_run":"20260911T105243-8b696eb1d0"}}
{"seq":22,"type":"ws.restored","step":"build","payload":{"name":"src","digest":"sha256:18160d77..."}}
{"seq":23,"type":"step.finished","step":"build","attempt":1,
 "payload":{"state":"cached","duration_ns":28378625,"cached":true}}
```

The live terminal UI, the browser UI, and reading that file a week later all build their view by folding **the same list** through one function. Three things follow:

- If the UI shows a step as cached, event 23 arrived. There is no other way for it to know.
- Replaying the file offline gives you the screen the TUI showed at the time.
- Your own code can fold the same events with `senro.WithSink` and reach the same conclusions.

There is no "the UI is out of date" state in senro, because there is nothing for it to be out of date with.

## Attaching to a run

A pipeline can open a socket that a second process attaches to while it runs. One call, and one option:

```go
att, err := attach.Listen(ctx, attach.Options{Bind: attach.AutoUnixSocket})
if err != nil {
	log.Fatal(err)
}
defer att.Close()

log.Printf("attach with: senro attach --pid %d", os.Getpid())

if err := senro.Run(ctx, p, senro.WithAttach(att)); err != nil {
	os.Exit(1)
}
```

Attaching to a pipeline three seconds into a ten second step, from a second terminal:

```bash
senro attach --pid 36343 --ui=plain
```

```
prepare succeeded
slow stdout | tick 1
slow stdout | tick 2
slow stdout | tick 3
slow started
slow stdout | tick 4
slow stdout | tick 5
```

The client replays what already happened, reports where the run currently is, then follows it live. It does not need to have been there from the beginning, because the event stream is the record and the client just folds it.

Three renderers read that same stream:

| Command | What you get |
|---|---|
| `senro attach` | A terminal UI, or plain streaming lines with `--ui=plain` |
| `senro ui` | A browser view on loopback, a Go client compiled to WebAssembly, with a one-time link |
| `senro attach --run <id>` | A finished run, reopened from disk over the same protocol |

And attach is not read-only. You can cancel, pause and resume a run, retry, skip and re-run from a step, set breakpoints, and open an interactive shell inside a live step's sandbox.

If `attach.Listen` is not in your `main`, `senro.Run` costs exactly what the engine costs: no attach server, no extra goroutine.

## Ten states, not a boolean

A step ends in exactly one of ten states, because "did it pass" hides information a build system should be surfacing.

| State | How a step ends there |
|---|---|
| `succeeded` | Passed without ever failing |
| `recovered` | Failed at least once, then passed on retry |
| `cached` | A `Pure()` step hit the action cache and was skipped entirely |
| `failed` | Ran, failed, exhausted its retries |
| `timed_out` | An attempt outlived the step's `Timeout` |
| `cancelled` | The run was cancelled before it could finish |
| `panicked` | A Go function step panicked; the panic was caught, not fatal |
| `skipped_upstream_failed` | Something it depends on failed |
| `skipped_condition` | Its `When` condition was not met at run start |
| `skipped_manual` | An operator took it out of a live run |

Two distinctions do most of the work.

**`recovered` is not `succeeded`.** A build that needed three attempts and one that needed one are different facts. Collapsing them is how flaky infrastructure stays invisible for months. A run full of `recovered` steps is a passing run that is telling you something.

**`skipped_condition` is not `skipped_upstream_failed`.** Gate a workflow to a branch:

```go
deploy := p.Workflow("deploy", senro.When(senro.Branch("main")))
deploy.Step("apply", exec.Command("echo", "deploying"))
```

On a feature branch:

```
apply    -> skipped_condition
report   -> succeeded
package  -> failed
sign     -> succeeded
RUN      -> failed
```

`apply` is recorded as gated off, not as broken. Had nothing else failed, the run would have ended `succeeded`: the deploy was not supposed to fire on a feature branch, and it did not. Your pull request stays green without a special case.

That run ended `failed` because `package` genuinely failed. `sign` still ran and succeeded, because `package` declared `ContinueOnError()`. `ContinueOnError` is about surviving a failure, and it deliberately does not rescue a `skipped_condition` step, which produced nothing to run against.

## Two kinds of step

A command is one kind. The other is a registered Go function:

```go
type ReportParams struct {
	Env string `json:"env"`
}

func init() { senro.RegisterFunc("ship/report", Report) }

func Report(ctx senro.Ctx, p ReportParams) error {
	fmt.Fprintf(ctx.Stdout(), "run %s, step %s, attempt %d, env %s\n",
		ctx.RunID(), ctx.StepID(), ctx.Attempt(), p.Env)
	return nil
}

// in the pipeline:
build.Step("report", senro.Func("ship/report", ReportParams{Env: "staging"}))
```

```
run 20260911T105408-1d19454e86, step report, attempt 1, env staging
```

Both kinds are built, scheduled, retried, cached and handled by exactly the same code. A function receives a `senro.Ctx` in place of a working directory and an argv:

| Method | What it gives you |
|---|---|
| `ctx.Workspace(name)` | A mounted workspace's path, the same one a command's mount resolves to |
| `ctx.Secret(name)` | A delivered secret's **file path**, never the value |
| `ctx.Stdout()`, `ctx.Stderr()` | The step's real log streams, redacted and recorded |
| `ctx.RunID()`, `ctx.StepID()`, `ctx.Attempt()` | This invocation's identity in the event stream |
| `ctx.Failure()` | What this function is cleaning up after, when it runs as a handler |

`ctx.Attempt()` is what an idempotency key needs to know before you retry against a remote API. And `senro.Ctx` embeds `context.Context`, so it passes straight into any library call that takes one.

A panic inside a func step is caught and reported as the state `panicked` rather than taking the run down. Panics are not retried.

## Where a step runs

The executor belongs to the workflow, chosen with `senro.On(...)`. There are four:

| Target | Package | Runs every step of the workflow |
|---|---|---|
| `senro.Local()` | built in, the default | as processes on the coordinator's own machine |
| `container.Image(ref)` | `executor/container` | in a container on a local Docker daemon |
| `k8s.Pod(ref, k8s.Namespace(ns))` | `executor/k8s` | as a pod in a Kubernetes cluster |
| `ssh.Host(dest)` | `executor/ssh` | as a process on a remote machine, via your own `~/.ssh/config` |

A step behaves the same wherever it lands, because retries, `Timeout`, `ContinueOnError`, the state taxonomy, handlers, workspace snapshots, the action cache, secret delivery and log redaction all live **above** the executor layer. No target re-implements them, so none of them can differ between targets.

Func steps work on all four. A Go function's body only exists inside your compiled binary, and a plan is JSON, so running one elsewhere means moving the binary rather than the plan. senro stages a copy of your pipeline binary on the target and re-enters it there, and `ctx.Workspace(...)` returns paths **on the target**, so the same function body works either way. Run `senro func check` to find out whether your module cross-compiles before a run tells you on a Friday.

If your build does not include a given executor, targeting it is rejected at `Build()`. It never quietly falls back to running locally.

## Secrets are files, not strings

Credentials are a typed struct resolved by [mamori](https://github.com/xavidop/mamori), handed to `senro.WithSecrets`. A step asks for one by field name:

```go
type Config struct {
	RegistryToken secret.String `source:"env:NPM_TOKEN"`
}

cfg, err := mamori.Load[Config](ctx)

w.Step("use", exec.Command("sh", "-c",
	`echo "the variable holds: $NPM_TOKEN"; echo "the file holds: $(cat "$NPM_TOKEN")"`)).
	SecretEnv("NPM_TOKEN", "RegistryToken")

senro.Run(ctx, p, senro.WithSecrets(cfg))
```

With `NPM_TOKEN=super-secret-value`, that step's log:

```
the variable holds: /var/folders/1p/ppx8j26s6jjghmfp1nv9p1zc0000gn/T/senro-secret-880958012/RegistryToken
the file holds: [REDACTED]
```

The environment variable holds a **path**, not the token, because argv is world-readable in `/proc` and environment values leak into crash dumps and child processes. A file has an owner and a mode, and it disappears with the sandbox. And when the step deliberately printed the file's contents, the log shows `[REDACTED]`, because every stream is redacted on the way out.

What senro refuses is more interesting than what it redacts. A plan that would route a resolved value through argv, an environment value, `WorkDir`, `Inputs`, `Outputs` or a mount is rejected **before the run starts**:

```go
w.Step("leak", exec.Command("echo", cfg.RegistryToken.Reveal()))
```

```
senro: engine: step "leak" puts the value of secret "RegistryToken" in command argument 1;
a command argument is visible in ps(1), in shell history and in auditd execve records, where
senro cannot redact it, so senro refuses to run rather than leak it. Deliver it as a file
instead: SecretEnv("VAR", "RegistryToken"), then read "$VAR" as a path in the step
```

Nothing ran. Inside a func step the same credential arrives through `ctx.Secret("RegistryToken")`, which is also a path.

## Webhooks and triggers: the binary decides whether to run

In most CI systems, the decision to start a build belongs to the service, and you describe it in an `on:` block you cannot run locally. In senro that decision belongs to your program: **the pipeline binary is its own webhook matcher.**

Hand it a delivery and it decides whether the event is its business:

```go
err = senro.Run(ctx, pipeline(ev),
	senro.WithTrigger(ev,
		trigger.OnPush(trigger.Branches("main")),
		trigger.OnPush(),
		trigger.OnPullRequest(trigger.Actions("opened", "synchronize")),
	))
```

A push to a topic branch matches and the pipeline runs. A tag push does not, and nothing runs:

```
$ go run ./examples/monorepo --trigger-event /tmp/ev-tag.json
senro: trigger: no trigger matched the event: tag refs/tags/v1.2.3
  push(branches=[main]): only answers push events, this was tag
  push: only answers push events, this was tag
  pull_request(actions=[opened synchronize]): only answers pull_request events, this was tag
exit status 78
```

Exit code 78 is `EX_CONFIG`, the conventional "this was not my business", and you get one line per matcher saying why it declined. That beats staring at a YAML `on:` block that silently did not fire, and because it is a binary you can test the decision on your laptop against a saved payload before it ever reaches a runner.

GitHub, GitLab, Bitbucket and Gitea ship, plus your own provider through a small interface.

The event is also more than a yes or no. It carries what changed, so `change.FromTrigger(ev)` feeds a monorepo fan-out that runs only the units the push actually reaches. That is the subject of [the next article]({% post_url go/2026-09-11-senro-real-pipeline-monorepo-go %}).

### Or be the endpoint yourself

You do not need an event file, or a CI service in front of you at all. `trigger.FromRequest` works out which source sent the delivery, verifies its signature, and parses it into the same event a file would have produced. One line changes:

```go
ev, err := trigger.FromRequest(r, trigger.Secret(hookSecret))  // instead of LoadEvent(path)
```

So the pipeline binary can be the endpoint GitHub posts to:

```go
func (s *server) webhook(w http.ResponseWriter, r *http.Request) {
	ev, err := trigger.FromRequest(r, trigger.Secret(s.secret))
	if err != nil {
		httpError(w, err)
		return
	}

	w.WriteHeader(http.StatusAccepted)

	// Not r.Context(): it is cancelled when the response is written.
	go senro.Run(context.Background(), pipeline(),
		senro.WithTrigger(ev, trigger.OnPush(trigger.Branches("main"))))
}
```

Two things worth copying from that: reply `202` before the run finishes, because a webhook sender times out in seconds and a pipeline takes minutes, and never hand `r.Context()` to `senro.Run`, because it is cancelled the moment the response is written. `trigger.Secret` covers all four providers, which authenticate differently. See [Run it as a server](https://github.com/xavidop/senro/blob/main/site/src/pages/docs/triggers/server.md).

## Two caches, for two different jobs

Both are opt-in, and neither is on unless you ask.

### The action cache: skip a step entirely

Mark a step `Pure()` and declare its inputs. senro hashes those inputs plus the command plus the environment into a key. On a second run with the same key the step is **not executed at all** and its recorded outputs are restored:

```go
verify.Step("build", exec.Command("go", "build", "-o", "bin/app", "./cmd/app")).
	Pure().
	Inputs(artifact.Glob("**/*.go"), artifact.File("go.sum")).
	Outputs(artifact.File("bin/app"))
```

```
$ senro cache explain --run <id> build
HIT  build  key a52a9b6c
```

Change one file and it rebuilds, and the reason is a command rather than a guess:

```
MISS  build  key 0e769472 (previous a52a9b6c)
  ✗ input_digests: greet/greet.go  59d2873d → 57930022
  ✗ workspace_digests: src  f377ce04 → de2069cc
  ✓ command, env, secrets, executor_class, platform, mount_shape, step_shape, func_identity,
    tool_versions, version unchanged
```

Which of the eleven key components changed, both sides of each digest, and an explicit list of what did not.

**Nothing is cached by default**, because `Pure()` is a promise only you can make. A tool that also SSHes into production is not pure and senro cannot tell. What it can do is audit the claim afterwards with `senro verify --recheck-pure`.

### The scratch cache: start warm, never be wrong

The other job is the mutable directories tools keep for their own speed: `~/.npm`, `~/.cargo`, a Go module cache. You want yesterday's copy if there is one and you do not care if there is not:

```go
gomod := senro.ScratchCache("gomod",
	senro.Key(`gomod-{{ hashFiles "go.sum" }}`),
	senro.RestoreKeys("gomod-"))

verify.Step("test", exec.Command("go", "test", "./...")).
	Mount(gomod.At("/root/go/pkg/mod"))
```

A scratch cache is restored best-effort by key and **never enters a cache key**. `RestoreKeys` is the fallback, so a `go.sum` change misses the exact key but still starts from the last module cache rather than from nothing. A miss costs time and nothing else, and a stale entry cannot make a build produce the wrong answer, because nothing downstream is keyed on it.

### One store, so caches are shareable

Artifacts, workspaces, cached results and staged binaries all live in one content-addressed store, normalized so the same bytes hash the same way on any machine. Point `SENRO_REMOTE_CACHE` at an S3-compatible bucket or an OCI registry and a fresh CI runner starts warm on what another machine already built. An unreachable store degrades the run to local disk, and never fails the run.

## Three rules to know before your first pipeline

senro's execution model differs from CI systems that hand you a checkout and a shell. Three consequences are worth knowing up front rather than discovering.

**1. A step does not start in your repository.** Every step runs in an isolated, empty working directory. Code reaches a step through a [workspace](https://github.com/xavidop/senro/blob/main/site/src/pages/docs/data/workspaces.md) that an earlier step populates, usually with a `git clone`. That is what makes a step mean the same thing in a pod as on your laptop.

**2. A step gets exactly the environment you declared.** `Build()` adds nothing, not even a `PATH`; the local executor supplies its own and that is all. Two developers on the same commit therefore produce the same plan, since nothing about their shells leaks into it, and the environment is one of the components a cache key is computed from. Tools that need `HOME`, `GOMODCACHE` or anything else get it from `.Env(...)`.

**3. On the local executor a mount path is a logical name.** `WorkDir` is translated into the sandbox only when it matches a mount point **exactly**. `WorkDir("/src")` against a mount at `/src` works; `WorkDir("/src/services/api")` is passed through as a real host path. Keep `WorkDir` on the mount point and let the tool move: `go -C services/api build ./...`.

## When to reach for senro (and when not)

**Reach for it when** your pipeline logic has outgrown what YAML can honestly express: real branching, loops over units, recovery, anything you want to unit test, anything where you want to attach to a running build and look inside it. Reach for it when you want a build that behaves identically on a laptop and on a runner, and a failure report that distinguishes ten outcomes instead of two.

**Skip it when** your pipeline is genuinely twenty lines of YAML and always will be. GitHub Actions is excellent at twenty lines of YAML, and a Go module and a binary is a lot of machinery for a problem you do not have. Skip it too if you need Windows runners, because that is a decision rather than a gap.

senro is a library first: no global state, no `os.Exit`, no reading your argv, attach is one opt-in call, and the wire contract lives in `github.com/xavidop/senro/api` with no dependency beyond the standard library. You can embed it and never run the CLI at all.

## Wrapping up

senro is MIT licensed and lives at [github.com/xavidop/senro](https://github.com/xavidop/senro). The full documentation is in the repository under `site/`, runnable examples are in `examples/`, and an agent skill ships in-repo for AI coding tools.

Three more articles continue this series:

- **[Building a real pipeline with senro]({% post_url go/2026-09-11-senro-real-pipeline-monorepo-go %})**: monorepo fan-out, running only what a change affects, caching and triggers.
- **[Genkit flows as senro steps]({% post_url genkit/2026-09-11-genkit-flows-senro-ai-pipelines-go %})**: AI pipelines in Go where each model call is a graph node with its own retry, log and cache entry.
- **[Debugging senro pipelines]({% post_url go/2026-09-11-debugging-senro-pipelines %})**: replaying a finished run, shelling into a live step, and auditing a cache.

If you build something with it, I would like to hear about it.
