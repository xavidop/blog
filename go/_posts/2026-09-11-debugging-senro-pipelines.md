---
layout: post
title: "Debugging senro Pipelines: Replay a Run, Shell Into a Live Step, Audit a Cache (English)"
description: >
  Debugging a CI failure usually means adding a print statement and pushing again. senro records every run as an append-only event stream you can replay with the same client that watched it live, lets you open a shell inside a step while it is still running, explains cache misses component by component, and will re-execute a step to check whether it lied about being pure. This is the field guide, in the order you should use it.
image: /assets/img/blog/post-headers/debugging-senro-pipelines.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [go]
tags:
  - go
  - golang
  - senro
  - debugging
  - ci-cd
  - observability
keywords:
  - go
  - golang
  - senro
  - debugging
  - ci-cd
  - pipelines
  - event-stream
  - replay
  - cache
  - reproducibility
  - observability
  - devops
  - troubleshooting

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

The usual way to debug a CI failure is to add `echo "HERE"` to a YAML file, push, wait four minutes, read forty thousand lines of log, and repeat until you understand something that would have taken thirty seconds at a shell prompt. The machine that produced the failure is gone, so there is nowhere else to look.

[senro](https://github.com/xavidop/senro) is built so that loop is not necessary. This article is the field guide: what to run when a pipeline goes wrong, in roughly the order you should run it. It follows the [introduction]({% post_url go/2026-09-11-introducing-senro-pipeline-engine-go %}) and the [monorepo guide]({% post_url go/2026-09-11-senro-real-pipeline-monorepo-go %}).

Every output below comes from a real broken run.

## The one idea underneath all of it

**Every observable fact about a run is an event, appended in order, never rewritten.** The live terminal UI, the browser UI, and reading the file a week later all build their view by folding the same list through the same function.

So there is no difference between watching a run and investigating one afterwards. It is the same protocol and the same client, reading a socket in one case and a file in the other. senro has no separate offline mode that could be worse than the online one.

Every run writes a directory:

```
runs/20260911T105325-4410b2c052/
├── events.jsonl      the append-only ledger, the source of truth
├── plan.json         the immutable graph that was executed
├── run.json          id, pipeline, start time
├── logs/<step>/<attempt>/{stdout,stderr}
├── ws/<workspace>    the workspaces this run used
└── work/<step>       each step's sandbox
```

Note `logs/<step>/<attempt>/`. Attempts get separate directories, so a step that failed twice and passed on the third try keeps all three sets of logs.

### Reading the graph that ran

`plan.json` is the graph the engine executed, and it is plain JSON with no dependency beyond the standard library behind it. When a run did not do what you expected, the first question is often whether the plan was what you expected, and `jq` answers it in one line:

```bash
jq -r '.nodes[] | . as $n | (($n.needs // ["(root)"])[] | "\(.) -> \($n.id)")' runs/<id>/plan.json
```

```
(root) -> checkout
checkout -> vet
checkout -> test
vet -> build
test -> build
```

This is worth reaching for before anything else on a fan-out, where the plan is built from your repository rather than written by hand. A missing unit, a phantom unit, or an edge you did not mean to declare shows up here rather than three steps into a run.

## 1. Find the run

```bash
$ senro runs -n 6
RUN ID                      PIPELINE  STATUS     STARTED              DURATION
20260911T110526-57739ce41a  slow      running    2026-09-11 20:05:26  14s
20260911T110510-de69b88fe7  slow      cancelled  2026-09-11 20:05:10  9s
20260911T105408-1d19454e86  ship      failed     2026-09-11 19:54:08  0s
20260911T105325-4410b2c052  ci        failed     2026-09-11 19:53:25  1s
20260911T105314-bc1a4e9d3d  ci        succeeded  2026-09-11 19:53:14  1s
20260911T105259-8fc9b32e31  ci        succeeded  2026-09-11 19:52:59  1s
```

`-n` caps how many are printed. This answers "what ran" without already knowing a run ID.

## 2. Replay the run

```bash
senro attach --run 20260911T105325-4410b2c052 --ui=plain
```

```
checkout stderr | Cloning into '.'...
checkout stderr | done.
checkout succeeded
vet succeeded
test stdout | ?   	senrolab/ci	[no test files]
test stdout | --- FAIL: TestHello (0.00s)
test stdout |     greet_test.go:7: got "HELLO, senro"
test stdout | FAIL
test stdout | FAIL	senrolab/greet	0.376s
test failed
build skipped_upstream_failed
run failed
```

This is the same client that watches a live run, reading recorded events instead of a socket. On a TTY you get the full interactive terminal UI, with the same key bindings, on a run that finished yesterday. `--follow` tails a run from disk with no socket needed.

The last two lines carry most of the diagnosis. **`test failed`** is a step that ran and returned non-zero. **`build skipped_upstream_failed`** is a step that never ran because of it. Those are different states, so nobody has to read upwards through a log wondering whether `build` broke too.

Five of the ten states are the ones you meet while debugging:

| State | What it tells you |
|---|---|
| `failed` | It ran, returned non-zero, retries are exhausted |
| `timed_out` | An attempt outlived the `Timeout` you declared |
| `panicked` | A Go function step panicked; the stack is in its stderr |
| `skipped_upstream_failed` | It never ran, something it needs broke |
| `recovered` | It passed, but not on the first attempt |

`recovered` is not a failure and it is the most useful of the five. A run full of `recovered` steps is a passing run telling you your infrastructure is flaky, and it stays visible instead of being collapsed into "green".

If you only want the states, the ledger is one command away:

```bash
grep step.finished runs/<id>/events.jsonl | jq -r '"\(.step) -> \(.payload.state)"'
```

```
checkout -> succeeded
vet -> succeeded
test -> failed
build -> skipped_upstream_failed
```

## 3. Look at the files the step had

The log says what the step printed. Often you need what the step was looking at. Workspaces are snapshotted into a content-addressed store, so a failed run's directories survive it:

```bash
$ senro ws ls 20260911T105325-4410b2c052
src    sha256:f37f35faa76ae965f92e410a877b7c0c90da14cd926711fde5b0a2137be1c5cf  13 files  3.2 KiB
```

```bash
$ senro ws pull 20260911T105325-4410b2c052 src /tmp/broken-src
$ ls /tmp/broken-src
ci  cmd  go.mod  go.sum  greet  probe
```

That is the exact tree the failing step saw, on your laptop, from a run on a machine that may no longer exist.

`ws pull` prints what a snapshot does and does not preserve, which matters exactly once, when a permission looks wrong: modes are normalized to 0644 or 0755, mtimes are fixed at the epoch, and uid, gid, extended attributes, ACLs, hard links and devices are not stored at all. That normalization is what makes a snapshot's digest depend only on content, not on which machine produced it.

For "it worked yesterday", compare two runs:

```bash
$ senro ws diff <run-a> <run-b> src
+ added   - removed   M content changed   P mode changed   K kind changed

workspace "src"
  a  20260911T105314-bc1a4e9d3d  sha256:3c3503f85c99ced855d5564624e31f350608c5b029410f65811b5898bc54b81a
  b  20260911T105325-4410b2c052  sha256:f37f35faa76ae965f92e410a877b7c0c90da14cd926711fde5b0a2137be1c5cf
  - bin             dir
  - bin/app         0755  2.3 MiB  53d0659f
  M greet/greet.go  113 B -> 113 B  57930022 -> 6bd8b782
  0 added, 2 removed, 1 modified, 0 mode, 0 kind, 12 unchanged
```

`greet/greet.go` changed, and the binary is missing because the build never ran. `ws ls` and `ws diff` read stored indexes without downloading any file contents, so both are instant on a tree of any size. Use `ws pull` when a workspace's last state came from a cache hit, since a cache entry stores a body digest rather than an index.

## 4. Get inside a step that is still running

While a run is live, open a session on one of its steps:

```bash
$ senro shell --pid 36343 --step slow -- ls -la
senro shell: this session runs against pipes: no prompt, no line editing, no job control.
Type a command and press enter; ^D ends the session. Pass --tty for a real terminal.
total 16
drwxr-xr-x  4 xavierportillaedo  wheel  128 Sep 11 20:05 .
drwxr-xr-x  3 xavierportillaedo  wheel   96 Sep 11 20:05 ..
-rw-r--r--  1 xavierportillaedo  wheel    4 Sep 11 20:05 a.txt
-rw-r--r--  1 xavierportillaedo  wheel    4 Sep 11 20:05 b.txt

$ senro shell --pid 36343 --step slow -- cat a.txt
one
```

That is the step's own workspaces, read-only, at the paths the step sees them, on the step's own executor. Not a copy and not a reconstruction. If the step is running in a pod, the session is in that pod.

Pair it with a breakpoint to stop the run **before** a step and inspect exactly what it was about to run against. Add `--tty` for a real terminal with a prompt and line editing, which the local, container and Kubernetes executors host.

Two deliberate limits: no secrets are delivered into a session, and a finished run has no engine to host one, so use `ws pull` for a run that is over.

## 5. Attach to a live run you did not start watching

If your pipeline called `attach.Listen`, you can join a run in progress from any terminal:

```bash
$ senro attach --pid 36343 --ui=plain
prepare succeeded
slow stdout | tick 1
slow stdout | tick 2
slow stdout | tick 3
slow started
slow stdout | tick 4
slow stdout | tick 5
```

Attaching three seconds in replays what already happened, reports where the run currently is, then follows it live. The client does not need to have been there from the start.

From there, attach is not read-only. You can cancel, pause and resume the run, retry, skip or re-run from a step, set a breakpoint, and force a workspace snapshot. `senro ui` serves the same thing as a browser page on loopback with a one-time link, offering the same control operations except the shell.

## 6. Ask why the cache did what it did

Caching bugs are the worst class of build bug, because the symptom is that something did **not** happen. `senro cache explain` answers it component by component.

A hit:

```
$ senro cache explain --run <id> build
HIT  build  key a52a9b6c
```

A miss, after one file changed:

```
MISS  build  key 0e769472 (previous a52a9b6c)
  ✗ input_digests: ci/main.go  ee7563f3 → 4f7d4315
  ✗ input_digests: greet/greet.go  59d2873d → 57930022
  ✗ input_digests: probe/main.go  added
  ✗ workspace_digests: src  f377ce04 → de2069cc
  ✓ command, env, secrets, executor_class, platform, mount_shape, step_shape, func_identity,
    tool_versions, version unchanged
```

Which components changed, both digests for each, which path was added, and an explicit list of what stayed the same.

A surprising miss is almost always a component you forgot about, so it is worth knowing all eleven: `command`, `env`, `secrets` (identity, never values), `executor_class`, `platform`, `input_digests`, `workspace_digests`, `mount_shape`, `step_shape`, `func_identity` and `version`.

The one that catches people is **`workspace_digests`: every mounted workspace enters the key in full**. Narrow `Inputs` do not narrow it. A step that mounts a big shared tree misses on any change anywhere in that tree, however precisely its inputs were declared.

## 7. Check whether a step lied about being pure

`Pure()` is a promise only you can make. senro does not sandbox network access, so it cannot tell that a tool which also SSHes into production is impure. What it can do is audit the claim afterwards:

```bash
senro verify --recheck-pure --run <id> --rerun
```

It re-executes the run's cached pure steps in throwaway trees restored from the workspace content each step's own cache key records, and compares what they produce against what the cache stored. Nothing runs without `--rerun`, deliberately: the premise is that a purity claim may be false, so its safety corollary is not assumed either. No cache entry is ever written.

Pointed at a `go build` step:

```
NONDETERMINISTIC build  key a52a9b6ce84a  entry from run 20260911T105243-8b696eb1d0
  ✗ output     bin/app   cached cf1663a0  re-run 739ebb3d  again e86c2b3d
  ✗ workspace  src       cached 18160d77  re-run 07c2a015  again a7e507af
  declared inputs   glob:**/*.go, file:go.sum
  declared outputs  file:bin/app
  the two re-runs disagreed with each other as well as with the entry, so this step does not
  produce the same bytes twice from the same input; that is a reproducibility problem (an
  archive embedding a build timestamp looks exactly like this) and it is NOT evidence about
  purity either way

1 nondeterministic of 1 cached Pure() step(s)
1 step(s) cannot reproduce their own output twice, so their entries hold bytes a re-run would
not produce. That is worth fixing and it is not evidence about purity.
```

It ran the step twice, noticed the two re-runs disagreed with **each other** and not only with the cache, and declined to draw the wrong conclusion. The build is not byte-reproducible, which is real and worth fixing, and that is separate from whether the step reaches the network. A cruder tool would report "impure" and send you hunting a bug that is not there.

`verify` exits 0 whether or not it finds anything, because a finding is an answer rather than a failed run. Use `--fail-on-mismatch` in CI if you want the opposite.

## 8. Repeat the run instead of rediscovering it

```bash
senro rerun --run <id>
```

`rerun` re-executes the plan a previous run recorded, from `plan.json` rather than by rebuilding your pipeline. That is the distinction: it **repeats** a run instead of re-discovering one, so a fan-out that would find different units today still runs the graph that actually failed. Unchanged steps come from the action cache.

`--step` re-runs one step and everything below it. `--regenerate` asks generators for a fresh subgraph, and it is a separate verb because that run may do different work than the one it repeats.

## Failures that are not a step's fault

Two categories look nothing alike and are worth recognising immediately.

### Build-time refusals

`senro.Run` builds first, so a dangling `Needs`, a duplicate step id, an empty command or a plan that would leak a credential comes back before anything executes. The messages do the diagnosis:

```
plan: step "summarize/alpha" is a func step and sets WorkDir "/tree", which it never runs in:
a func step on the coordinator runs in the coordinator's own process, where the working
directory is process-global, so honouring it would move every step running alongside it.
Reach files through ctx.Workspace(name) [...]
```

```
plan: step "summarize/alpha" is Pure() with no Inputs, so its cache key would not change when
its sources do: declare them with Inputs(artifact.Glob(...))
```

```
engine: step "leak" puts the value of secret "RegistryToken" in command argument 1; a command
argument is visible in ps(1), in shell history and in auditd execve records, where senro cannot
redact it, so senro refuses to run rather than leak it. Deliver it as a file instead [...]
```

Each names what you wrote, why it cannot hold, and what to write instead. Read them rather than searching.

### Exit code with no output

A step fails with exit code 127 and both `stdout` and `stderr` are zero bytes. Exit 127 normally means "command not found", but the real cause here is usually the **working directory**: the process never started, so it never wrote anything.

The common trigger is a `WorkDir` that is a subpath of a mount. On the local executor a mount path is a logical name, and senro translates `WorkDir` into the sandbox only when it matches a mount point **exactly**:

```go
func CmdDir(workDir string, mounts []Mount) string {
	for _, mt := range mounts {
		if mt.At == workDir {
			return ""
		}
	}
	return workDir
}
```

So with a workspace mounted at `/tree`, `WorkDir("/tree")` works and `WorkDir("/tree/services/api")` is passed through as a literal host path that does not exist. Keep `WorkDir` on the mount point and let the tool do the moving:

```go
exec.Command("go", "-C", u.Dir, "build", "-o", "/dev/null", "./...")
```

The general rule: **an exit code with no output means the process never started**, so check the working directory and the executable path before you look at the command itself.

### Writes through a read-only mount

```
engine: step "build[unit=services/api]" wrote through its read-only mount of workspace "tree"
(c9271303 became 832bb638); a read-only mount that changes makes every cache key computed from
it wrong
```

That is `go build` dropping a compiled binary next to the source. On the container and Kubernetes executors the kernel refuses the write; on local and SSH, `senro.RO` is checked after the fact. The failure is the point, because a read-only mount that silently changed would poison every cache key computed from it.

## Instrument it yourself

None of the above requires the CLI. The event stream is a public contract in `github.com/xavidop/senro/api`, which depends on nothing outside the standard library, and you can fold it in your own process:

```go
senro.Run(ctx, p, senro.WithSink(mySink))
```

That is how the trace exporter works, and it is how you push run facts into whatever you already use. Anything the TUI can conclude, your code can conclude from the same events.

## Conclusion

The checklist, in order:

1. `senro runs` to find the run.
2. `senro attach --run <id>` to replay it, and read the **states**, not just the log.
3. `jq` over `plan.json` when you need to check the graph that actually ran.
4. `senro ws pull` for the files it left behind, `senro ws diff` for what changed since the run that worked.
5. `senro shell --step <id>` if it is still running, ideally stopped on a breakpoint.
6. `senro cache explain` when the surprise is that something did not happen.
7. `senro verify --recheck-pure --rerun` when you suspect a cached result is wrong.
8. `senro rerun` to repeat the recorded plan rather than build a new one.

None of these require pushing a commit, and none require the machine that produced the failure to still exist.

senro is at [github.com/xavidop/senro](https://github.com/xavidop/senro), MIT licensed. The other articles in this series:

- **[Introducing senro]({% post_url go/2026-09-11-introducing-senro-pipeline-engine-go %})**
- **[Building a real pipeline with senro]({% post_url go/2026-09-11-senro-real-pipeline-monorepo-go %})**
- **[Genkit flows as senro steps]({% post_url genkit/2026-09-11-genkit-flows-senro-ai-pipelines-go %})**
