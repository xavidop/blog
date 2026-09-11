---
layout: post
title: "Genkit Flows as senro Steps: Extremely Powerful AI Pipelines in Go (English)"
description: >
  A Genkit flow is a great unit of AI work and a poor unit of orchestration. senro is a pipeline engine where every step already has retries, caching, an event stream and live attach. Put a flow inside a step and each model call becomes a graph node: change one document out of three and you pay for one call, not three. A practical guide, with every example running against the real Gemini API.
image: /assets/img/blog/post-headers/genkit-senro-ai-pipelines.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - senro
  - golang
  - ai
  - pipelines
keywords:
  - genkit
  - genkit-go
  - senro
  - golang
  - go
  - ai-pipelines
  - flows
  - orchestration
  - caching
  - gemini
  - generative-ai
  - llm
  - batch-inference
  - failure-analysis

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

A [Genkit](https://genkit.dev) flow is an excellent unit of AI work. It is typed, traced, testable, and `genkit.DefineFlow` gives you something you can call from anywhere.

What a flow is not is a unit of **orchestration**. The moment you have twelve documents to summarise, a flow whose output feeds two other flows, or a model call that fails on the third of forty items, you end up writing the same scaffolding again: a worker pool, a retry loop, a way to avoid re-running the eleven items that already succeeded, logs you can actually read, and some way to find out what happened at three in the morning.

[senro](https://github.com/xavidop/senro) is a pipeline engine where a step already has all of that: retries that distinguish infrastructure from workload, an action cache that skips work it has already done, an append-only event stream, and a live attach protocol. I covered it in [the introduction]({% post_url go/2026-09-11-introducing-senro-pipeline-engine-go %}) and [the monorepo article]({% post_url go/2026-09-11-senro-real-pipeline-monorepo-go %}).

This article shows how to combine them. **Put a Genkit flow inside a senro step and every model call becomes a graph node** with its own log, state, retry policy and cache entry.

Every example below ran against the real Gemini API with `googleai/gemini-2.5-flash`, on Genkit Go v1.13.1 and senro v1.4.0. The summaries are what the model actually returned.

## What you need

```bash
go get github.com/firebase/genkit/go
go get github.com/xavidop/senro
```

The example is a small corpus of release notes in `docs/*.md` that gets summarised one document at a time, then merged into a digest.

## Step 1: the flow

Nothing senro-specific here. This is an ordinary Genkit flow:

```go
// SummarizeInput is what the summarize flow takes.
type SummarizeInput struct {
	Path string `json:"path"`
	Text string `json:"text"`
}

// Summary is what it returns.
type Summary struct {
	Path    string `json:"path"`
	Summary string `json:"summary"`
}

func defineFlows(g *genkit.Genkit) *core.Flow[SummarizeInput, Summary, struct{}] {
	return genkit.DefineFlow(g, "summarize",
		func(ctx context.Context, in SummarizeInput) (Summary, error) {
			text, err := genkit.GenerateText(ctx, g,
				ai.WithSystem("You summarize release notes for an operator. "+
					"Answer in one sentence, no preamble."),
				ai.WithPrompt(fmt.Sprintf("Summarize these release notes:\n\n%s", in.Text)))
			if err != nil {
				return Summary{}, err
			}
			return Summary{Path: in.Path, Summary: text}, nil
		})
}
```

Called on its own it does what you expect:

```
The billing reconciliation job was moved to a queue worker, accelerating invoice
settlement from up to 24 hours to within two minutes.
```

## Step 2: wrap the flow in a step

senro has two kinds of step: a command, and a registered Go function. A Genkit flow is a Go function, so it is the second kind:

```go
// summarize is the registered flow. A func step runs in the pipeline's own
// process, so a package-level handle is all the wiring the two need.
var summarize *core.Flow[SummarizeInput, Summary, struct{}]

type SummarizeParams struct {
	Path string `json:"path"`
	Name string `json:"name"`
}

func init() { senro.RegisterFunc("ai/summarize", RunSummarize) }

// RunSummarize runs the flow and writes the summary into the one workspace
// this step mounts.
func RunSummarize(ctx senro.Ctx, p SummarizeParams) error {
	dir, ok := ctx.Workspace("doc-" + p.Name)
	if !ok {
		return fmt.Errorf("step %s mounts no doc-%s workspace", ctx.StepID(), p.Name)
	}

	text, err := os.ReadFile(filepath.Join(string(dir), "doc.md"))
	if err != nil {
		return err
	}

	res, err := summarize.Run(ctx, SummarizeInput{Path: p.Path, Text: string(text)})
	if err != nil {
		return err
	}

	fmt.Fprintf(ctx.Stdout(), "%s\n", res.Summary)
	return os.WriteFile(filepath.Join(string(dir), "summary.txt"), []byte(res.Summary+"\n"), 0o644)
}
```

Three details make this work smoothly:

- **`senro.Ctx` embeds `context.Context`**, so it passes straight into `summarize.Run` with no adapter. Genkit's tracing and cancellation behave exactly as they always did.
- **`ctx.Stdout()` is the step's real log stream**, recorded and redacted like a command's output. Writing to `os.Stdout` instead reaches your terminal and no log file.
- **`ctx.Workspace(name)` hands the function the same path a mount gives a command**, on every executor. The function body does not change when the step later runs in a container or a pod.

`RegisterFunc` registers the function once, from an `init`. The name is the function's identity: it is what the plan records and what feeds the step's cache key, so renaming it invalidates the cache exactly as renaming a command would. Parameters must be JSON-serializable, and decoding is strict, so a renamed field fails loudly instead of running with a zero value.

## Step 3: build the graph

Because the pipeline is a Go program, fanning out over a corpus is a `for` loop:

```go
func main() {
	ctx := context.Background()

	g := genkit.Init(ctx,
		genkit.WithPlugins(&googlegenai.GoogleAI{}),
		genkit.WithDefaultModel("googleai/gemini-2.5-flash"))
	summarize = defineFlows(g)

	docs, err := filepath.Glob("docs/*.md")
	if err != nil {
		log.Fatal(err)
	}
	sort.Strings(docs)

	p := senro.New("ai")
	w := p.Workflow("summarize")

	var names, ids []string
	var wss []*senro.WorkspaceRef
	corpus := map[string]string{}

	for _, doc := range docs {
		text, err := os.ReadFile(doc)
		if err != nil {
			log.Fatal(err)
		}
		name := strings.TrimSuffix(filepath.Base(doc), ".md")
		names = append(names, name)
		ids = append(ids, "summarize/"+name)
		corpus[name] = string(text)

		// One workspace per document, so one document changing does not
		// invalidate the other summaries' cache keys.
		wss = append(wss, senro.Workspace("doc-"+name, senro.Scope(senro.ScopeRun)))
	}

	seed := w.Step("seed", senro.Func("ai/seed", SeedParams{Docs: corpus}))
	for i, ws := range wss {
		seed.Mount(ws.At("/doc-"+names[i], senro.RW))
	}

	for i, name := range names {
		// One AI call, one node: its own log, state, retry and cache entry.
		w.Step(ids[i], senro.Func("ai/summarize", SummarizeParams{
			Path: docs[i],
			Name: name,
		})).
			Needs("seed").
			Mount(wss[i].At("/doc", senro.RW)).
			Retry(3, retry.OnInfra()).
			Pure().
			Inputs(artifact.File("doc.md")).
			Outputs(artifact.File("summary.txt"))
	}

	digestStep := w.Step("digest", senro.Func("ai/digest", DigestParams{Names: names})).
		Needs(ids...)
	for i, ws := range wss {
		digestStep.Mount(ws.At("/doc-"+names[i], senro.RO))
	}

	if err := senro.Run(ctx, p); err != nil {
		log.Print(err)
		os.Exit(1)
	}
}
```

`seed` writes each document into a workspace of its own. Then one summarize step per document, running in parallel. Then `digest`, which waits for all of them and merges the results.

That loop produces this graph, rendered straight from the run's own `plan.json`:

```
pipeline: ai
  │
  ├─ wave 1                seed                  func
  │
  ├─ wave 2 (3 parallel)   summarize/alpha       func · retry 3/infra
  │                        summarize/beta        func · retry 3/infra
  │                        summarize/gamma       func · retry 3/infra
  │
  └─ wave 3                digest                needs summarize/alpha, summarize/beta,
                                                 summarize/gamma · func
```

Three documents give three parallel nodes. Thirty would give thirty, from the same `for` loop, with no change to the code.

## Step 4: run it

Run the pipeline binary directly, the way any Go program runs:

```bash
go run .
```

Or hand the package to the senro CLI, which builds it, execs it and attaches automatically. You get a terminal UI on a TTY and plain streaming lines anywhere else:

```bash
senro run .
```

```
seed             -> succeeded
summarize/beta   -> succeeded
summarize/alpha  -> succeeded
summarize/gamma  -> succeeded
digest           -> succeeded
```

```
- alpha: The billing reconciliation job now uses a queue worker for invoice settlement
  within two minutes, replacing the nightly cron.
- beta: The search index now rebuilds incrementally in under a second without blocking
  writes, replacing the old full rebuild and requiring operators to delete the
  `rebuild-search` cron job.
- gamma: Service gamma's public API now features per-tenant rate limiting set at 100
  requests per second, which may cause HTTP 429 errors for existing bursting integrations.
```

Three real model calls in parallel, each with its own log file, and a merge step that ran once they were all done.

While that is running, a second terminal can watch it, or steer it:

```bash
senro attach          # terminal UI
senro ui              # browser view, prints a one-time link
senro attach --run <id>   # reopen a finished run from disk
```

Every run also lands in `runs/<id>/`, so `senro runs` lists what happened and each step's stdout is a file you can read afterwards.

> **One thing to know when you switch between `go run` and `senro run`.** A func step's cache key includes the **binary digest**, so the first run after changing how the binary is built re-runs every func step once, then caches normally from there. That is correct behaviour rather than a bug: the function's body lives in the binary, and senro cannot tell whether it changed without hashing it.

## Step 5: stop paying for the same call twice

Each summarize step declares `Pure()`. Run the pipeline again with nothing changed:

```
seed             -> succeeded
summarize/beta   -> cached
summarize/alpha  -> cached
summarize/gamma  -> cached
digest           -> succeeded
```

`cached` is a real state, not a label. Those three steps **did not execute**: no model call, no tokens, no latency. Their recorded outputs were restored from the content-addressed store, so `digest` still read three summaries and produced the same result.

Now change one document out of three:

```
seed             -> succeeded
summarize/alpha  -> cached
summarize/beta   -> cached
summarize/gamma  -> succeeded
digest           -> succeeded
```

One document changed, one model call made. And senro will tell you which component of the key moved:

```
$ senro cache explain --run <id> summarize/gamma
MISS  summarize/gamma  key d3eb7450 (previous f68652ad)
  ✗ input_digests: docs/gamma.md  6750cb09 → ef0fdb64
  ✗ workspace_digests: doc-gamma  16774a4e → d43e13c8
  ✓ command, env, secrets, executor_class, platform, mount_shape, step_shape, func_identity,
    tool_versions, version unchanged
```

For a few dozen documents this is a convenience. For a nightly re-index over ten thousand where one file changed, it is the difference between a bill you notice and one you do not.

Note `func_identity` in that list. For a func step the cache key covers the **binary digest, the registered name and the parameter digest**. So changing your prompt, your model or the flow's code all correctly invalidate the cache. It is not keyed on the input file alone, which is the mistake a hand-rolled cache usually makes.

### Give each call its own workspace

This is the one structural rule to follow when caching model calls.

`Inputs` feeds the `input_digests` component of the key, but **`Mount` feeds `workspace_digests`, which is the digest of the entire mounted workspace**. Narrow `Inputs` do not narrow it.

Mount one shared tree across a fan-out and every step's key depends on every document, so changing one document re-runs all of them and the cache buys you nothing. One workspace per unit of work, as in the loop above, keeps each key dependent on its own input.

## Step 6: let a model explain a failure

senro has a second place a model belongs: explaining a failed step. `contrib/genkitanalyzer` is a ready-made failure analyzer built on Genkit:

```bash
go get github.com/xavidop/senro/contrib/genkitanalyzer
```

It is a **nested module with its own `go.mod`**, so senro itself never pulls in an AI SDK. If you never install it, your dependency graph never hears about Genkit.

```go
g := genkit.Init(ctx, genkit.WithPlugins(&googlegenai.GoogleAI{}))

p := senro.New("analyze")
w := p.Workflow("build")
w.Step("migrate", exec.Command("sh", "-c",
	`echo "dial tcp 10.0.3.7:5432: connect: connection refused" >&2; exit 1`))

err := senro.Run(ctx, p,
	senro.WithAnalyzer(
		genkitanalyzer.New(g, genkitanalyzer.Model("googleai/gemini-2.5-flash")),
		senro.AnalyzerName("genkit"),
		senro.AnalyzeTimeout(20*time.Second)))
```

That is the whole integration. When the step fails, an `analysis.proposed` event lands in the run's ledger:

```json
{
 "id": "migrate@1",
 "analyzer": "genkit",
 "duration_ns": 8344562458,
 "summary": "The 'migrate' step failed because its command explicitly reported a database
             connection refusal error and exited.",
 "detail": "... The error message \"dial tcp 10.0.3.7:5432: connect: connection refused\"
            typically indicates that a client attempted to establish a TCP connection to a
            server at 10.0.3.7 on port 5432, but the server actively rejected the connection.
            This could be due to the database server not running, not listening on the
            specified address/port, or being blocked by a firewall ..."
}
```

Because it is an event, the explanation shows up in the TUI, in `events.jsonl`, and in anything else folding the run.


## What the combination gives you

Genkit gives you the model call: typed, traced, provider-agnostic, testable. senro gives you everything around it.

| Concern | What senro already does for a step |
|---|---|
| Ordering | A dependency edge, not a place in a loop |
| Outcome | Ten states, so a call that passed on the second attempt is `recovered`, not silently a success |
| Retries | `retry.OnInfra()` retries a dropped connection, never a model answer you did not like |
| Logs | One log file per step per attempt, redacted |
| Cost | An action cache keyed on the prompt, parameters, model and binary |
| Observability | One append-only event stream you can attach to live or replay later |
| Failure analysis | An analyzer gated behind a human or an explicit policy |

You can build every one of those yourself. It is never quite the same twice, and it is rarely tested well.

## Conclusion

The pattern is small enough to summarise in four lines:

1. Define the flow with `genkit.DefineFlow` as you always would.
2. Register a func step with `senro.RegisterFunc` that calls `flow.Run(ctx, ...)`.
3. Give each call its own workspace and declare `Pure()` with `Inputs` and `Outputs`.
4. Add `senro.WithAnalyzer` if you want failures explained.

From there the graph is a Go program, so the loop over your corpus is a `for` loop and the logic that decides what runs is testable with `go test`.

- [senro](https://github.com/xavidop/senro) on GitHub
- [Genkit](https://genkit.dev), and the [Go documentation](https://genkit.dev/go/docs/get-started-go/)
- The last article in this series: **[Debugging senro pipelines]({% post_url go/2026-09-11-debugging-senro-pipelines %})**
