---
layout: post
title: "A Software Factory on Kubernetes: Gemini Builds, jev Decides (Genkit + senro in Go) (English)"
description: >
  A feature request goes in; a designed, planned, implemented, tested and reviewed Go module comes out, or a brief for a human explaining why the factory stopped. Every stage is a Genkit flow running as a pod through senro, Gemini does the writing, and jev, a decision model, holds every gate: is the design ready, should the code ship, go back, or stop. A practical guide with a local kind cluster and every output pasted from a real run.
image: /assets/img/blog/post-headers/genkit-k8s-software-factory.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - senro
  - kubernetes
  - golang
  - ai
  - agents
keywords:
  - genkit
  - genkit-go
  - senro
  - kubernetes
  - kind
  - jev
  - system-one
  - decision-model
  - typesafe
  - software-factory
  - ai-coding
  - golang
  - go
  - gemini
  - mamori
  - pipelines
  - guardrails
  - generative-ai
  - llm

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

[The previous article]({% post_url genkit/2026-10-20-genkit-flows-kubernetes-senro-jev-decision-model %}) put Genkit flows in Kubernetes pods with [senro](https://github.com/xavidop/senro) and let [jev](https://typesafe.ai), a decision model, route a support ticket. The decisions there were small: which team, how urgent, send or hold.

This one hands jev something bigger to judge: software. A **software factory** takes a feature request and produces a Go module: a design, a plan, the code, a green build, passing tests and a pull request description. Gemini writes every one of those. jev decides, at every gate, whether the work moves on, goes back, or stops for a human. Each stage runs as a pod, each stage is a Genkit flow, and the whole thing is a few hundred lines of Go.

Everything below ran against the real Gemini API (`gemini-3.8-flash`) and the real TypeSafe API (`jev-latest`), on Genkit Go v1.14.0, senro v1.4.5 and a local [kind](https://kind.sigs.k8s.io) cluster. The code is in [genkit-k8s-flows-jev-software-factory](https://github.com/xavidop/genkit-k8s-flows-jev-software-factory).

## Why a factory needs a judge, not a second writer

The usual way to review model-written code is to ask another chat model. It works, up to a point. The reviewer writes a paragraph, you parse the paragraph, the paragraph is sometimes wrong in the same way the code is, and a well-written pull request description can talk the reviewer into "looks good to me".

A decision model does not write. It takes a state (the request, the plan, the code, the test log) and answers typed questions with probabilities, in a few hundred milliseconds. There is no prose to parse and nothing to be talked into: `BuildGreen` is a number, and a red test log drags it down whatever the pull request says.

| | Chat model as reviewer | Decision model as reviewer |
|---|---|---|
| Verdict | A paragraph you parse | `Choice[CodeVerdict]`: `ship`, `rework` or `human`, with a probability each |
| Evidence | Mentioned, maybe | A `Noul` per question: covers the request, tests are meaningful, build is green |
| Feedback for the next round | Whatever it felt like writing | Each question that scored "yes" is one line of feedback |
| Latency and cost | Seconds, thousands of output tokens | Milliseconds, tokens for the state only |
| Can be persuaded by the author | Yes | No: it never reads instructions, only state |

The split that falls out of this is the whole design: **Gemini builds, jev decides.** And senro is what gives each build step a pod, a workspace, a log, a retry policy and a secret, and each decision a place in the graph.

## What we are building

A feature request goes in. A reviewed Go module comes out, or a brief for a human saying why not.

![Full-width image](/assets/img/blog/genkit-k8s-factory/state-machine.png){:.lead data-width="800" data-height="100"}

The factory is three senro pipelines and a small state machine over them:

| Run | Step | Where | Who | What it leaves behind |
|---|---|---|---|---|
| `design` | `clean` | coordinator | none | an empty workspace with `request.md` in it |
| `design` | `design` | pod | Gemini and jev, in a loop | `design.json`, `DESIGN.md` and one record per review round |
| `design` | `plan` | pod | Gemini | `plan.json`, `PLAN.md` |
| `implement` | `implement` | pod | Gemini | the module's files |
| `implement` | `vet`, `test` | pod | `go vet`, `go test` | `vet.log`, `test.log` and their exit codes |
| `implement` | `review` | pod | jev | `review.json`: ship, rework or human |
| `rework` | `fix`, then `vet`, `test`, `review` | pod | Gemini, Go, jev | the same, after a fix |
| `finish` | `pr` then `publish` | pod, coordinator | Gemini | `PR.md` and the module under `out/<request>/src` |
| `finish` | `brief` then `notify` | pod, coordinator | Gemini | `BRIEF.md` for a human |

jev decides three times. Inside the `design` step, it reviews each design Gemini writes and the loop revises until jev says ready, says reject, or three rounds are up. After `test`, it reviews the code with the logs in hand and picks `ship`, `rework` or `human`. And the state machine in `main` turns each verdict into the next senro run, with `rework` bounded at two.

## What you need

- Go 1.27 or newer, Docker, [kind](https://kind.sigs.k8s.io) and `kubectl`
- `GEMINI_API_KEY` and `TYPESAFE_API_KEY` in your environment
- the [senro CLI](https://xavidop.github.io/senro/docs/install/) if you want the terminal UI (optional)

```bash
go get github.com/firebase/genkit/go@v1.14.0
go get github.com/xavidop/senro@v1.4.5
go get github.com/xavidop/mamori
```

## Step 1: a cluster and an image with a Go toolchain

The cluster setup is the one from the previous article: kind, a namespace, a ServiceAccount with the permissions senro's Kubernetes executor needs (including `get` on `pods/exec`), and three environment variables, since senro never reads your kubeconfig. The repo's `scripts/cluster-up.sh` does it and `source scripts/cluster-env.sh` exports them.

The one difference is the image. A func step needs only `sh` and `tar` in the pod, but this factory also runs `go vet` and `go test` as plain command steps, so every step uses the official Go image, pinned to its digest as senro requires:

```go
const stepImage = "docker.io/library/golang:1.27-alpine@sha256:f2c872bcee949b7be9c490efd02b48a8a2fbf947cdf533f1c58525ec9d8170fd"

func pods() senro.ExecutorTarget {
	return k8s.Pod(stepImage,
		k8s.Namespace("factory"),
		k8s.Resources(
			map[string]string{"cpu": "500m", "memory": "512Mi"},
			map[string]string{"cpu": "2", "memory": "2Gi"},
		))
}
```

Your pipeline binary is still not in that image. senro cross-compiles it and sends it into each pod, exactly as before.

## Step 2: the design loop, with jev inside the flow

The first gate is the one that saves the most money: a bad design produces bad code, a green build and a confident pull request. So the design is reviewed before anything is planned, and the review is a loop inside one Genkit flow.

![Full-width image](/assets/img/blog/genkit-k8s-factory/design-loop.png){:.lead data-width="800" data-height="100"}

The questions are a Go type. Every yes/no question is one a revision can act on: a "yes" becomes a line of feedback for the next round.

```go
type DesignVerdict string

func (DesignVerdict) Criteria() map[DesignVerdict]string {
	return map[DesignVerdict]string{
		"ready":  "Complete, unambiguous, scoped to the request, and testable as described",
		"revise": "The right direction, with gaps a revision can close",
		"reject": "The request is too vague or too large to design from; a human has to clarify it first",
	}
}

type Risk int

func (Risk) Levels() []string { return []string{"Low", "Medium", "High"} }

type DesignReview struct {
	Verdict        systemonex.Choice[DesignVerdict] `json:"verdict" jsonschema_description:"Is this design ready to implement?"`
	RequestClear   systemonex.Noul                  `json:"request_clear" jsonschema_description:"Does the request say what to build precisely enough that two engineers would build the same thing?"`
	ScopeCreep     systemonex.Noul                  `json:"scope_creep" jsonschema_description:"Does the design add things the request did not ask for?"`
	Underspecified systemonex.Noul                  `json:"underspecified" jsonschema_description:"Is any component described too loosely to implement without guessing: missing fields, signatures, edge cases or error behaviour?"`
	MissingTests   systemonex.Noul                  `json:"missing_tests" jsonschema_description:"Does the test plan leave any requirement of the request untested?"`
	Risk           systemonex.Score[Risk]           `json:"risk" jsonschema_description:"How risky is implementing this design as written?"`
}
```

And the loop. Gemini designs; jev reviews; if the verdict is `revise`, Gemini gets the previous design plus the feedback and tries again:

```go
f.Design = genkit.DefineFlow(g, "designFeature", func(ctx context.Context, request string) (DesignResult, error) {
	var res DesignResult
	feedback := ""
	for round := 1; round <= maxDesignRounds; round++ {
		prompt := "Request:\n" + request
		if round > 1 {
			prompt += "\n\nYour previous design:\n" + asJSON(res.Design) + "\n\nReviewer feedback:\n" + feedback
		}
		d, _, err := genkit.GenerateData[Design](ctx, g,
			ai.WithModelName("googleai/gemini-3.8-flash"),
			ai.WithSystem("You are a senior Go engineer writing a short design for exactly what the request asks. "+
				"Stay inside the request: no extra features. Components are the Go types and functions you will create. "+
				"The test plan names concrete, deterministic test cases. Be brief."),
			ai.WithPrompt("%s", prompt))
		if err != nil {
			return res, err
		}
		res.Design = *d

		out, resp, err := genkit.GenerateData[DesignReview](ctx, g,
			ai.WithModelName("typesafe/jev-latest"),
			ai.WithSystem("The state has a feature request and a design written for it."),
			ai.WithPromptParts(ai.NewDataPart(map[string]any{"request": request, "design": res.Design})))
		if err != nil {
			return res, err
		}

		// jev's verdict, then our rules on top.
		verdict := string(out.Verdict.Choice)
		var notes []string
		if out.RequestClear.Probability < 0.4 {
			verdict = "reject" // nobody should design from a request two engineers would read differently
		}
		if out.ScopeCreep.Probability >= 0.5 {
			notes = append(notes, "remove everything the request did not ask for")
		}
		if out.Underspecified.Probability >= 0.5 {
			notes = append(notes, "specify every component fully: fields, signatures, edge cases and error behaviour")
		}
		if out.MissingTests.Probability >= 0.5 {
			notes = append(notes, "add a test case for every requirement in the request")
		}
		if verdict == "ready" && len(notes) > 0 {
			verdict = "revise"
		}
		res.Rounds = append(res.Rounds, DesignRound{Round: round, Verdict: verdict,
			Ready: out.Verdict.Probabilities["ready"], Feedback: notes /* ... */})
		res.Verdict = verdict
		if verdict != "revise" {
			break
		}
		feedback = fmt.Sprintf("The reviewer rated the design %q (probability of ready %.2f). Do the following:\n- %s",
			verdict, out.Verdict.Probabilities["ready"], strings.Join(notes, "\n- "))
	}
	return res, nil
})
```

Two things to notice. The verdict is jev's, but the **rules around it are yours**: a request that two engineers would read differently is rejected whatever the design looks like, and a design with a flagged problem is not ready even if jev leaned that way. And the feedback is built from the questions, not from prose: a decision model never writes a sentence, so the sentences live in your code, one per question, and the next round gets exactly the ones that applied.

The whole loop is one flow, so it is one senro step, one pod, one log, with every round recorded in `design.json`.

## Step 3: plan, implement, and let Go have its say

The plan and the implementation are ordinary Gemini calls with typed outputs: a `Plan` with files and steps, then a `Code` with every file in full. The step writes the files into the workspace, refusing anything that would escape it:

```go
type Code struct {
	Files []File `json:"files"`
	Notes string `json:"notes,omitempty"`
}

func writeCode(ctx senro.Ctx, code Code) error {
	root := wsPath(ctx, ".")
	for _, f := range code.Files {
		rel := filepath.Clean(f.Path)
		if rel == "." || strings.HasPrefix(rel, "..") || filepath.IsAbs(rel) || strings.HasPrefix(rel, factoryDir) {
			return fmt.Errorf("refusing to write outside the module: %q", f.Path)
		}
		path := filepath.Join(root, rel)
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(path, []byte(f.Content), 0o644); err != nil {
			return err
		}
		fmt.Fprintf(ctx.Stdout(), "wrote %s (%d bytes)\n", rel, len(f.Content))
	}
	return nil
}
```

Then the compiler and the tests run, as **command steps in the same pod image**, with no model anywhere near them:

```go
func goStep(w *senro.WorkflowBuilder, id, after, cmd string, ws *senro.WorkspaceRef) *senro.StepBuilder {
	script := "mkdir -p .factory; " + cmd + " > .factory/" + id + ".log 2>&1; echo $? > .factory/" + id + ".exit; " +
		"cat .factory/" + id + ".log; exit $(cat .factory/" + id + ".exit)"
	return w.Step(id, exec.Command("sh", "-c", script)).
		Needs(after).
		Mount(ws.At("/repo", senro.RW)).
		WorkDir("/repo").
		Env("HOME", "/tmp").
		Env("GOCACHE", "/tmp/gocache").
		Env("GOFLAGS", "-mod=mod").
		Env("GOPROXY", "off").
		Env("GOTOOLCHAIN", "local").
		Env("CGO_ENABLED", "0").
		Timeout(stepTimeout).
		Retry(3, retry.OnInfra()).
		ContinueOnError()
}

goStep(code, "vet", "implement", "go vet ./...", ws)
goStep(code, "test", "vet", "go test -count=1 ./...", ws)
```

Each one leaves its output and exit code under `.factory/` in the workspace, so the reviewer can read them. `GOPROXY=off` and `GOTOOLCHAIN=local` keep the pod honest: the request said standard library only, and the pod cannot download anything to pretend otherwise. And `ContinueOnError` is the important one: a red test is a failed step, but the review still runs. **jev gets to see why the build failed**, which is exactly the evidence a rework needs.

## Step 4: the code review gate

The second gate reads everything a human reviewer would open: the request, the plan, every source file, and what `go vet` and `go test` printed.

```go
type CodeVerdict string

func (CodeVerdict) Criteria() map[CodeVerdict]string {
	return map[CodeVerdict]string{
		"ship":   "Builds, tests pass, does what the request asked, no obvious defects",
		"rework": "Fixable problems: failing or missing tests, a missed requirement, sloppy code",
		"human":  "Something a model should not decide: security, data loss, or the request was misunderstood",
	}
}

type Quality int

func (Quality) Levels() []string { return []string{"Poor", "Acceptable", "Good", "Excellent"} }

type CodeReview struct {
	Verdict         systemonex.Choice[CodeVerdict] `json:"verdict" jsonschema_description:"Should this change ship?"`
	Quality         systemonex.Score[Quality]      `json:"quality" jsonschema_description:"How good is the code?"`
	CoversRequest   systemonex.Noul                `json:"covers_request" jsonschema_description:"Does the implementation do everything the request asked for?"`
	TestsMeaningful systemonex.Noul                `json:"tests_meaningful" jsonschema_description:"Do the tests exercise the behaviour the request cares about, rather than just compile?"`
	BuildGreen      systemonex.Noul                `json:"build_green" jsonschema_description:"According to the logs and exit codes, did go vet and go test both pass?"`
}
```

![Full-width image](/assets/img/blog/genkit-k8s-factory/gates.png){:.lead data-width="800" data-height="100"}

The flow sends the whole `ReviewInput` as a data part, reads the answers, and applies the factory's rules on top. A red build never ships, whatever the overall verdict:

```go
f.Review = genkit.DefineFlow(g, "reviewChange", func(ctx context.Context, in ReviewInput) (Review, error) {
	out, resp, err := genkit.GenerateData[CodeReview](ctx, g,
		ai.WithModelName("typesafe/jev-latest"),
		ai.WithSystem("The state has the feature request, the implementation plan, every source file, "+
			"and the output and exit codes of go vet and go test. Exit code 0 means success."),
		ai.WithPromptParts(ai.NewDataPart(in)))
	if err != nil {
		return Review{}, err
	}
	r := Review{
		Verdict:         string(out.Verdict.Choice),
		Confidence:      out.Verdict.Confidence,
		Quality:         out.Quality.Label(),
		CoversRequest:   out.CoversRequest.Probability,
		TestsMeaningful: out.TestsMeaningful.Probability,
		BuildGreen:      out.BuildGreen.Probability,
		Model:           systemonex.ResponseInfo(resp).Model,
	}
	if in.VetExit != 0 {
		r.Reasons = append(r.Reasons, "go vet failed")
	}
	if in.TestExit != 0 {
		r.Reasons = append(r.Reasons, "go test failed")
	}
	if r.CoversRequest < 0.6 {
		r.Reasons = append(r.Reasons, "the implementation does not cover the request")
	}
	if r.TestsMeaningful < 0.5 {
		r.Reasons = append(r.Reasons, "the tests do not exercise the requested behaviour")
	}
	if out.Quality.Level() == 0 {
		r.Reasons = append(r.Reasons, "code quality is poor")
	}
	if r.Verdict == "ship" && len(r.Reasons) > 0 {
		r.Verdict = "rework"
	}
	return r, nil
})
```

The `Reasons` are what the `fix` flow gets, together with the logs. Again: the decision model decides, your code says it in words.

## Step 5: three pipelines and a state machine

The module under construction lives in a **persistent workspace**, so every run of one request works on the same tree. senro insists a persistent workspace is bounded, and refuses one without both bounds:

```go
func repo() *senro.WorkspaceRef {
	return senro.Workspace("factory-repo",
		senro.Scope(senro.ScopePersistent),
		senro.MaxAge(24*time.Hour),
		senro.MaxSize(256<<20))
}
```

The three pipelines are short. Every AI step gets the same shape through a helper, with only the secrets it needs:

```go
func aiStep(s *senro.StepBuilder, ws *senro.WorkspaceRef, secrets ...string) *senro.StepBuilder {
	s = s.Mount(ws.At("/repo", senro.RW)).Timeout(stepTimeout).Retry(3, retry.OnInfra())
	for _, name := range secrets {
		s = s.SecretEnv("SENRO_"+name, name)
	}
	return s
}

func buildPipeline(outDir string, rework bool) *senro.Pipeline {
	name, fn := "implement", "factory/implement"
	if rework {
		name, fn = "rework", "factory/fix"
	}
	p := senro.New(name)
	ws := repo()

	code := p.Workflow("code", senro.On(pods()))
	aiStep(code.Step(name, senro.Func(fn, NoParams{})), ws, "Gemini")
	goStep(code, "vet", name, "go vet ./...", ws)
	goStep(code, "test", "vet", "go test -count=1 ./...", ws)
	aiStep(code.Step("review", senro.Func("factory/review", NoParams{})), ws, "TypeSafe").Needs("test")

	handoff := p.Workflow("handoff", senro.Needs("code"), senro.On(senro.Local()))
	handoff.Step("collect", senro.Func("factory/collect", DirParams{Dir: outDir})).
		Mount(ws.At("/repo", senro.RO))

	return p
}
```

`finish` declares both endings and lets a run parameter pick one, the same `senro.When` pattern as the previous article:

```go
func finishPipeline(outDir, reason string) *senro.Pipeline {
	p := senro.New("finish")
	ws := repo()

	ship := p.Workflow("ship", senro.On(pods()), senro.When(senro.ParamIs("verdict", "ship")))
	aiStep(ship.Step("pr", senro.Func("factory/pr", NoParams{})), ws, "Gemini")

	publish := p.Workflow("publish", senro.Needs("ship"), senro.On(senro.Local()),
		senro.When(senro.ParamIs("verdict", "ship")))
	publish.Step("publish", senro.Func("factory/publish", DirParams{Dir: outDir})).
		Mount(ws.At("/repo", senro.RO))

	escalate := p.Workflow("escalate", senro.On(pods()), senro.When(senro.ParamIs("verdict", "human")))
	aiStep(escalate.Step("brief", senro.Func("factory/brief", BriefParams{Reason: reason})), ws, "Gemini")
	// ...and a notify workflow on the coordinator that collects BRIEF.md
	return p
}
```

And `main` is the state machine. Each run ends with a record jev produced, and the record picks the next run:

```go
state, reason, reworks := "design", "", 0
for {
	switch state {
	case "design":
		if err := run(designPipeline(request, out)); err != nil {
			exit(err)
		}
		var d DesignResult
		read(out, "design.json", &d)
		if d.Verdict == "ready" {
			state = "implement"
		} else {
			state, reason = "human", fmt.Sprintf("the design review ended %q after %d round(s)", d.Verdict, len(d.Rounds))
		}

	case "implement", "rework":
		// A red vet or test is a failed step, so the run is partial; the
		// review still ran (ContinueOnError) and its verdict is what counts.
		if err := run(buildPipeline(out, state == "rework")); err != nil && !partial(err) {
			exit(err)
		}
		var r Review
		read(out, "review.json", &r)
		switch r.Verdict {
		case "ship":
			state = "ship"
		case "rework":
			if reworks >= *maxRework {
				state, reason = "human", fmt.Sprintf("jev asked for rework %d times: %v", reworks+1, r.Reasons)
			} else {
				reworks++
				state = "rework"
			}
		default:
			state, reason = "human", fmt.Sprintf("the code review ended %q: %v", r.Verdict, r.Reasons)
		}

	case "ship", "human":
		if err := run(finishPipeline(out, reason), senro.WithParams(senro.Params{"verdict": state})); err != nil {
			exit(err)
		}
		return
	}
}
```

Every arrow in the state diagram is one of those cases, and every run is a directory under `runs/` with its plan, its events and one log per step.

## Step 6: run it

The first request is a token-bucket rate limiter, the kind of package every service ends up with:

```
# Feature request: a token-bucket rate limiter package

We need a small, dependency-free Go package `ratelimit` (module path
`github.com/acme/ratelimit`) that other services can import.

- `New(rate float64, burst int) *Limiter`: `rate` is tokens added per second,
  `burst` is the bucket capacity.
- `(*Limiter) Allow() bool`: takes one token if available, otherwise returns false
  without blocking.
- `(*Limiter) AllowN(n int) bool` for batches.
- Safe for concurrent use from many goroutines.
- Time must be injectable so tests are deterministic (no sleeping in tests).
- Standard library only. Tests included, run with `go test ./...`.
```

```bash
go run . -request requests/token-bucket.md
```

The first run is the design. Read back with `senro attach --run <id> --ui=plain`:

```
clean succeeded
design stdout | round 1: jev-1.13.0 decided "revise" (p_ready 0.44) request_clear=0.62 scope_creep=0.36 underspecified=0.56 missing_tests=0.38 risk=Low
design stdout |   - specify every component fully: fields, signatures, edge cases and error behaviour
design stdout | round 2: jev-1.13.0 decided "ready" (p_ready 0.57) request_clear=0.57 scope_creep=0.49 underspecified=0.28 missing_tests=0.34 risk=Low
design succeeded
plan stdout | module github.com/acme/ratelimit, 3 files, 11 steps
plan succeeded
collect succeeded
run succeeded
```

Two rounds. jev found the first design underspecified (0.56), the feedback said so in one sentence, and the second design named every field, signature and edge case. The ready probability moved from 0.44 to 0.57, and the design that came out of it is the one Gemini implemented; this is its component list in `DESIGN.md`:

```
## Components

- type Limiter struct { mu sync.Mutex; rate float64; burst float64; tokens float64;
  last time.Time; now func() time.Time } - concurrency-safe state tracking ...
- func New(rate float64, burst int) *Limiter - public constructor delegating to
  newWithClock using time.Now; clamps negative rate to 0.0 and negative burst to 0 ...
- func newWithClock(rate float64, burst int, now func() time.Time) *Limiter - internal
  constructor enabling time injection for tests; ... panics if now is nil.
- func (l *Limiter) Allow() bool - convenience method returning l.AllowN(1) ...
- func (l *Limiter) AllowN(n int) bool - thread-safe token deduction; edge cases: returns
  true immediately if n <= 0 without modifying state; returns false immediately if
  n > int(l.burst); advances tokens by elapsed.Seconds() * l.rate capped at l.burst ...
```

The plan turns that into three files and eleven steps, and the second run executes it.

```
implement stdout | wrote go.mod (42 bytes)
implement stdout | wrote ratelimit.go (1371 bytes)
implement stdout | wrote ratelimit_test.go (3172 bytes)
implement succeeded
vet succeeded
test stdout | ok  	github.com/acme/ratelimit	0.009s
test succeeded
review stdout | jev-1.13.0 decided "ship" (confidence 0.66) quality=Excellent covers_request=0.87 tests_meaningful=0.95 build_green=0.98
review succeeded
collect succeeded
run succeeded
```

Gemini wrote the module, `go vet` and `go test` ran in the pod against it, and jev read the three files and the logs and said ship, with the build at 0.98 and the tests at 0.95. The module it reviewed:

```go
// AllowN reports whether n tokens can be consumed immediately.
func (l *Limiter) AllowN(n int) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	if n <= 0 {
		return true
	}
	if float64(n) > l.burst {
		return false
	}

	curr := l.now()
	elapsed := curr.Sub(l.last)
	if elapsed > 0 {
		l.tokens += elapsed.Seconds() * l.rate
		if l.tokens > l.burst {
			l.tokens = l.burst
		}
		l.last = curr
	}

	if l.tokens >= float64(n) {
		l.tokens -= float64(n)
		return true
	}
	return false
}
```

with six tests beside it: clamping, a nil clock panic, burst capacity, `AllowN` edge cases, deterministic replenishment against an injected clock, and a race test over concurrent goroutines. No sleeping anywhere, as the request demanded.

The third run has both endings declared and runs one:

```
pr stdout | # Implement token-bucket rate limiter package
pr stdout | ## Summary
pr stdout | Introduces `github.com/acme/ratelimit`, a thread-safe, zero-dependency token-bucket rate limiter. ...
pr stdout | ## Tests
pr stdout | ok  	github.com/acme/ratelimit	0.009s
pr stdout | ## Risk
pr stdout | Low. Mutex contention under high concurrency is mitigated by keeping critical sections limited to basic in-memory arithmetic. ...
pr succeeded
publish stdout | published 3 files to .../out/token-bucket/src
publish succeeded
brief skipped_condition
notify skipped_condition
run succeeded
```

Three senro runs, seven pods, two Gemini designs, two jev design reviews, one implementation, one vet, one test, one jev code review and one pull request, in a little over a minute and a half. `out/token-bucket/` holds every record and the module under `src/`.

## Step 7: when jev says no

The second request is the kind every team gets:

```
# Request

The app feels slow lately, especially in the afternoon. Can you make it faster?
Nothing specific, just whatever you think is best. Thanks.
```

```bash
go run . -request requests/make-it-faster.md
```

```
clean succeeded
design stdout | round 1: jev-1.13.0 decided "reject" (p_ready 0.13) request_clear=0.05 scope_creep=0.87 underspecified=0.70 missing_tests=0.79 risk=Low
design stdout |   - remove everything the request did not ask for
design stdout |   - specify every component fully: fields, signatures, edge cases and error behaviour
design stdout |   - add a test case for every requirement in the request
design succeeded
plan stdout | design ended "reject", nothing to plan
plan succeeded
collect succeeded
run succeeded
```

Gemini did what a chat model does with a vague request: it invented a feature, in this case `pprof` routes and a latency middleware. jev put the probability that the request is clear at 0.05, and the factory's rule turned that into `reject` in the first round, before a plan, a line of code or a second model call. The `finish` run then takes the other ending:

```
pr skipped_condition
publish skipped_condition
brief stdout | ### What was asked
brief stdout | A user submitted a vague performance complaint stating the app "feels slow lately, especially in the afternoon" and asked to "make it faster" without providing specific endpoints, metrics, or reproduction steps.
brief stdout | ### Why it stopped
brief stdout | The design was rejected on Round 1 (Readiness: 13%, Clarity: 5%). The factory attempted to introduce Go `net/http/pprof` diagnostic routes and custom in-memory latency middleware, triggering a rejection for high scope creep (87%) ...
brief stdout | ### What a human should decide
brief stdout | 1. **Clarify the issue:** Contact the user to identify affected routes, user workflows, and target latency SLOs.
brief stdout | 2. **Authorize observability work:** Determine if the team should prioritize a dedicated ticket for production profiling/metrics ...
brief succeeded
notify succeeded
run succeeded
```

The brief is written by Gemini, from the record jev produced. The two models keep their jobs even in the failure path.

### A request jev cannot be talked into

The third request is a glob matcher: `*`, `**`, `?`, character classes with ranges and negation, backslash escapes, and an error for an unterminated class. It is precise, it is testable, and the factory never got to write it:

```
clean succeeded
design stdout | round 1: jev-1.13.0 decided "revise" (p_ready 0.39) request_clear=0.68 scope_creep=0.35 underspecified=0.49 missing_tests=0.32 risk=Medium
design stdout | round 2: jev-1.13.0 decided "revise" (p_ready 0.39) request_clear=0.65 scope_creep=0.40 underspecified=0.34 missing_tests=0.22 risk=Medium
design stdout | round 3: jev-1.13.0 decided "revise" (p_ready 0.47) request_clear=0.59 scope_creep=0.66 underspecified=0.33 missing_tests=0.20 risk=Medium
design stdout |   - remove everything the request did not ask for
design succeeded
```

Gemini's design transpiles the glob into a Go regular expression. jev never called it ready, the ready probability never crossed 0.5 in three rounds, and in two of those rounds none of the specific questions crossed the line either, so the feedback Gemini got was the generic "tighten the approach". The loop cannot converge on a complaint it has no question for, and after three rounds the factory stops and writes the brief:

```
## What was asked
Implement a standard-library Go package (`github.com/acme/glob`) providing `Compile(pattern string)
(*Glob, error)` and `(*Glob) Match(path string) bool`. ...

## Why it stopped
The design review failed after 3 rounds, ending in a "revise" verdict (`p_ready` plateaued at 0.46).
Automated reviewers flagged persistent specification risks and scope creep regarding the chosen
approach (transpiling globs into Go `regexp`), specifically around complex regex metacharacter
escaping and separator handling in negated character classes.

## What a human should decide
1. **Architecture:** Approve regex transpilation (accepting edge-case escaping risks) or mandate a
   dedicated AST/rune-based glob parser.
2. **Path boundaries:** Explicitly define exact semantics for `**` edge cases and `/` exclusions
   inside negated classes.
```

That brief is the factory working as designed. A decision model only answers the questions you ask, and when it keeps saying no without any of them firing, the honest move is to stop and ask a person, with the evidence attached. The fix for the next version of the factory is one more field on `DesignReview`: a question about the approach itself, so that "this should be a parser, not a regex" becomes a sentence Gemini can act on.

## What the combination gives you

| Concern | Who handles it |
|---|---|
| Design, plan, code, fix, pull request text | Gemini, through `genkit.GenerateData` and `GenerateText` |
| Is the design ready, should the code ship | jev, through the same `GenerateData` call with a decision type |
| Feedback for the next round | Your code, one sentence per question jev answered "yes" |
| Compiling and testing | `go vet` and `go test`, as command steps in the pod, with no model involved |
| A red build reaching the reviewer | `ContinueOnError` on the Go steps |
| The module between runs | A bounded persistent workspace |
| Which ending runs | `senro.When(senro.ParamIs("verdict", ...))` |
| Credentials | mamori resolves, senro delivers a file per pod, per step |
| Evidence | `runs/<id>/` per run, plus `.factory/` records that travel with the code |

## Conclusion

A software factory is not one big agent. It is a handful of small, typed calls with a judge between them, and the judge is the part most people leave out. jev makes that part cheap: a design review is one call that answers six typed questions in a few hundred milliseconds, and the questions are Go fields you choose. Put the loop inside a Genkit flow, the flow inside a senro step, the step in a pod, and the verdict in a run parameter, and the factory is a state machine you can read in one screen.

- The code: [genkit-k8s-flows-jev-software-factory](https://github.com/xavidop/genkit-k8s-flows-jev-software-factory)
- The previous article: [Genkit flows on Kubernetes, routed by a decision model]({% post_url genkit/2026-10-20-genkit-flows-kubernetes-senro-jev-decision-model %})
- [Decision models in Genkit Go](https://genkit.dev/docs/go/integrations/system-one/) and [Flows](https://genkit.dev/docs/go/flows/)
- [senro's Kubernetes executor](https://xavidop.github.io/senro/docs/executors/kubernetes/) and [persistent workspaces](https://xavidop.github.io/senro/docs/data/persistent/)
