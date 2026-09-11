---
layout: post
title: "LangChainGo vs Genkit Go: Where Genkit Shines (English)"
description: >
  A practical comparison of the two main Go AI frameworks, built around the same production service written twice: RAG, tool calling, typed output, retries, cross-vendor fallback and tracing. 73 lines in Genkit Go against 272 in LangChainGo.
image: /assets/img/blog/post-headers/langchaingo-vs-genkit-go.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - langchaingo
  - golang
  - comparison
keywords:
  - genkit
  - genkit-go
  - langchain
  - langchaingo
  - comparison
  - golang
  - middleware
  - fallback
  - rag
  - observability
  - structured-output
  - generative-ai

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

There are two realistic choices for building AI services in Go today: **[LangChainGo](https://github.com/tmc/langchaingo)**, the Go port of the Python framework everyone knows, and **[Genkit Go](https://genkit.dev/docs/go/get-started/)**, Google's open-source Gen AI framework.

LangChainGo is still the first result most Go developers find. It has 9,677 stars and the biggest provider catalog in the ecosystem. It is also eight months without a commit, eleven months without a release, and still on `0.1.x` after three and a half years.

This article compares them the way that actually matters: by building the same production service in both and looking at what each one costs you. Not a feature checklist, a real application with real requirements.

If you have already decided and want the migration mechanics, that is the companion article: [How to migrate from LangChainGo to Genkit Go](/genkit/2026-09-11-langchaingo-to-genkit-go-migration/).

## The State of Both Projects

| | LangChainGo | Genkit Go |
|---|---|---|
| Latest release | `v0.1.14`, October 2025 | `v1.13.1` |
| Last commit to `main` | January 2026 | active |
| Age and version | 3.5 years, still `0.1.x` | GA since `v1.0` |
| Open issues | 242 | |
| Open pull requests | 171, oldest from June 2023 | |
| Stars | 9,677 | |

LangChainGo is not archived, and "dead" overstates it. But eleven months without a release is long enough for the ecosystem to move underneath a library, and it has.

## What Is Broken in LangChainGo Today

Three concrete things, all of which affect a service in production right now.

**The quickstart returns a 404.** `DefaultOptions()` hardcodes `gemini-2.0-flash`, which Google retired. A fresh `googleai.New(ctx)` fails on the first call.

**The Google provider runs on an end-of-life SDK.** `llms/googleai` imports `github.com/google/generative-ai-go`, whose README states support ended on **November 30, 2025**.

**Streaming is broken on every current Gemini model.** `gemini-2.5-flash`, `gemini-3-flash-preview`, `gemini-3.5-flash` and `gemini-3.6-flash` all fail the same way:

```
error in stream mode: invalid character ']' looking for beginning of value
```

The OpenAI provider streams fine, so this is the Google provider on the legacy SDK, not the library everywhere.

There is a fourth consequence that follows from the third, and it is the nastiest one. LangChainGo installs a streaming function automatically whenever you attach a callbacks handler, in `chains/options.go` and again in `agents/mrkl.go`. Since streaming is broken, **turning on observability breaks your Gemini agents**:

```
WITHOUT callbacks handler: err=<nil> out="The current year is 2026."
WITH    callbacks handler: err=error in stream mode: invalid character ']' looking for beginning of value
```

## Feature by Feature

| Capability | LangChainGo | Genkit Go |
|---|---|---|
| Structured output | Format instructions in the prompt, parse the text back | `genkit.GenerateData[T]`, real response schema |
| Tools | `Call(ctx, string) (string, error)`, no schema | `genkit.DefineTool[In, Out]`, typed with JSON schema |
| Agents | ReAct, driven by parsing `Action:` lines | Native function calling, plus an [agent primitive](https://genkit.dev/docs/go/agents/define/) with sessions (experimental) |
| Composition | `Chain` interfaces over `map[string]any` | Typed Go functions (`DefineFlow`) |
| Retry | Write it yourself | `middleware.Retry` |
| Cross-vendor fallback | Write it yourself | `middleware.Fallback` |
| Observability | 17 observe-only callback methods | Built-in tracing plus a Developer UI |
| OpenTelemetry | None | Built in |
| Local vector store | None, all 15 stores need a server | `localvec`, file-backed |
| Streaming on Gemini | Broken | Works |
| HTTP endpoint | `net/http` boilerplate | `genkit.Handler(flow)` |

The single most important row is **retry and fallback**, and the reason is architectural rather than cosmetic. A Genkit middleware wraps a call and receives a `next()`, so it can decide to call again, or call something else. LangChainGo's `callbacks.Handler` returns nothing from every method. You can watch a call, you cannot change it. That missing seam is why every resilience concern ends up in your application code.

## What We Are Building

A support-ticket triage service. Every requirement here is something a real team asks for:

1. Retrieve the relevant **policy documents** for an incoming ticket.
2. Let the model **call a tool** to act on it.
3. Return a **typed struct**, not free text.
4. **Retry** transient model failures.
5. **Survive a vendor outage** by falling back to a different provider.
6. **Trace** every step, so somebody can debug it at 3am.

## The Genkit Go Version

The whole service, in one file:

```go
g := genkit.Init(ctx, genkit.WithPlugins(
    &googlegenai.GoogleAI{}, &openai.OpenAI{}, &middleware.Middleware{},
))

// RAG store.
embedder := googlegenai.GoogleAIEmbedder(g, "gemini-embedding-001")
store, retriever, err := localvec.DefineRetriever(g, "policy",
    localvec.Config{Dir: "/tmp/gkvec", Embedder: embedder}, nil)
localvec.Index(ctx, docs, store)

// A tool the model can call.
refund := genkit.DefineTool(g, "issue_refund", "Issues a refund for an order.",
    func(ctx *ai.ToolContext, a struct {
        OrderID     string `json:"order_id"`
        AmountCents int    `json:"amount_cents"`
    }) (string, error) {
        return fmt.Sprintf("refunded %d cents for order %s", a.AmountCents, a.OrderID), nil
    })

// The flow.
triage := genkit.DefineFlow(g, "triage", func(ctx context.Context, ticket string) (*Triage, error) {
    found, err := genkit.Retrieve(ctx, g, ai.WithRetriever(retriever), ai.WithTextDocs(ticket))
    if err != nil {
        return nil, err
    }
    out, _, err := genkit.GenerateData[Triage](ctx, g,
        ai.WithModel(googlegenai.GoogleAIModelRef("gemini-3.5-flash", nil)),
        ai.WithDocs(found.Documents...),
        ai.WithTools(refund),
        ai.WithPrompt("Triage this ticket using the policy documents, and act on it: %s", ticket),
        ai.WithUse(
            &middleware.Retry{MaxRetries: 2},
            &middleware.Fallback{Models: []ai.ModelRef{openai.ModelRef("gpt-5-mini", nil)}},
        ),
    )
    return out, err
})
```

**73 lines**, and it returns exactly what you asked for:

```
{Category:billing Severity:1 PolicyQuote:Duplicate charges must be refunded in full within
5 business days, no manager approval required. Action:Issued a refund of $25.50 (2550 cents)
to resolve the duplicate charge on order A-1029.}
```

The interesting part is which requirements are not code. Retry and fallback are two entries in a list. Tracing does not appear at all, because Genkit instruments flows, generate calls, tool calls and retrieval itself. The RAG store is three calls because `localvec` ships in the box.

## The LangChainGo Version

Requirements 1, 2 and 3 port directly. Requirements 4, 5 and 6 do not exist in the library, so they become your code:

| File | Lines | Why it exists |
|---|---|---|
| `main.go` | 110 | the actual application |
| `memstore.go` | 68 | all 15 vector stores need an external service, so the local one is yours |
| `resilience.go` | 58 | no middleware layer, so retry and fallback are yours |
| `tracer.go` | 36 | observability is a 17-method interface to implement |
| **total** | **272** | |

None of those three extra files contain interesting code. `memstore.go` is cosine similarity and a sort. `tracer.go` is six methods that log and eleven empty ones that exist only to satisfy the interface:

```go
// Everything below exists only to satisfy the interface.
func (t *tracer) HandleText(context.Context, string)               {}
func (t *tracer) HandleLLMStart(context.Context, []string)         {}
func (t *tracer) HandleLLMError(context.Context, error)            {}
func (t *tracer) HandleChainStart(context.Context, map[string]any) {}
// ...seven more
```

`resilience.go` wraps the primary model to add retries and a fallback, and it has a sharp edge worth seeing:

```go
clean := make([]llms.CallOption, 0, len(opts))
for _, o := range opts {
    var probe llms.CallOptions
    o(&probe)
    // Model names are vendor-specific, and gpt-5-mini rejects 'stop'
    // outright, which the ReAct agent always sets. Both must go.
    if probe.Model != "" || len(probe.StopWords) > 0 {
        continue
    }
    clean = append(clean, o)
}
return r.backup.GenerateContent(ctx, msgs, clean...)
```

`CallOption` is an opaque function, so to find out what an option does you have to apply it to a probe struct and inspect the result. Miss the stop words and the fallback fails with `Unsupported parameter: 'stop' is not supported with this model`.

Both versions work and produce equivalent results. So far this is a story about volume, not capability. The outage test is where that changes.

## What Happens When a Model Goes Down

Point the primary at a retired model in both versions, which is a real 404 from the live API.

**Genkit heals and finishes:**

```
WARN model call failed, falling back model=openai/gpt-5-mini error="Error 404 ... NOT_FOUND"
WARN model call failed, falling back model=openai/gpt-5-mini error="Error 404 ... NOT_FOUND"
{Category:billing Severity:2 PolicyQuote:Duplicate charges must be refunded in full within
5 business days, no manager approval required. Action:Issued full refund of $25.50 ...}
```

Two calls fail over, once for the initial generate and once for the turn after the tool call. The typed struct survives a vendor switch.

**LangChainGo heals at the model layer, then breaks one layer up:**

```
2026/09/11 20:01:45 primary failed (googleapi: Error 404 ...), falling back
2026/09/11 20:01:54 PARSE FAILED: input text should start with ```json and end with ```
```

The hand-written fallback did its job. The output parser then rejected the answer, because `outputparser.Defined.Parse` hard-requires code fences:

```go
const opening = "```json"
const closing = "```"
if text[:len(opening)] != opening || text[len(text)-len(closing):] != closing {
    return target, fmt.Errorf("input text should start with %s and end with %s", opening, closing)
}
```

Gemini tends to emit those fences. OpenAI does not. The typed output layer is quietly coupled to one vendor's formatting habit, and the coupling surfaces at the exact moment you switch vendors, which is the worst possible time.

That same function has a second problem. When the response is shorter than seven characters, it does not return an error, it panics:

```
input "ok"  PANIC: runtime error: slice bounds out of range [:7] with length 2
input ""    PANIC: runtime error: slice bounds out of range [:7] with length 0
```

An empty completion or a refusal becomes an uncaught panic in your request handler.

## Dependency Weight

The same typed-extraction program, each in its own clean module:

| | LangChainGo | Genkit Go |
|---|---|---|
| Modules in the build graph | 62 | 41 |
| Binary size | 38.0 MB | 28.7 MB |

The LangChainGo-only half of that list is worth reading: the deprecated `generative-ai-go`, plus `cloud.google.com/go/vertexai` and `aiplatform`, plus `sprig`, `gonja` (a Jinja2 template engine), `go.starlark.net` (the calculator tool evaluates expressions in Starlark), `logrus`, `tiktoken-go`, `pkg/errors` and `json-iterator`. A Python-shaped dependency tree, in Go.

## Where Genkit Go Shines

Pulling the thread through all of it, the difference comes down to four things Genkit has and LangChainGo does not.

**Middleware is the first.** Because a Genkit middleware wraps a call and can decide to call it again or call something else, resilience becomes library code. Retry, cross-vendor fallback and tool approval are list entries instead of wrapper types you maintain forever.

**Types are the second.** Typed flows, typed tools and schema-backed output mean the compiler carries the contract. That is not just tidier: it is why the Genkit service survived the failover and the LangChainGo one did not. Nothing in the Genkit path was slicing strings out of a model response to find the data.

**Plugins are the third.** A model is a string reference in a registry, so swapping Gemini for GPT is a configuration change. In LangChainGo, two providers are two concrete structs of two different types, which is why a hand-written fallback has to strip vendor-specific call options and still gets it wrong the first time.

**The Developer UI is the fourth**, and it is the one you feel every day rather than during an incident. LangChainGo has no equivalent to it at all.

One command starts it next to your app:

```bash
genkit start -- go run .
```

It reads the registry your code built, so nothing has to be declared twice. On the triage service it found the flow, the tool, 39 models and 3 embedders without any configuration:

```
Flows (1)      triageTicket
Tools (1)      issue_refund
Models (39)    googleai/gemini-2.5-flash, ...
Embedders (3)  googleai/gemini-embedding-001, ...
```

Open a flow and the input form is generated from your Go struct. A `Ticket` with `Subject` and `Body` fields gives you this, pre-filled and ready to edit:

```json
{
  "body": "",
  "subject": ""
}
```

Press Run and you get the typed output back as a tree, not a blob of text:

```json
{ "category": "Billing", "urgency": 4, "action": "Refund issued" }
```

The part that earns its place is the trace underneath. Every run is a span tree with per-span timings, and the tool call is a span of its own:

```
triageTicket                        4.64s
├─ generate                         2.52s
│  ├─ googleai/gemini-2.5-flash     1.67s
│  ├─ issue_refund                    1ms
│  └─ generate (2)                  846ms
│     └─ googleai/gemini-2.5-flash  844ms
└─ generate                         2.12s
   └─ googleai/gemini-2.5-flash     2.12s
```

You can read the whole shape of the run off that: the first `generate` called the tool, the model went back for a second turn with the tool result, and a separate `generate` did the typed extraction. Nobody wrote a line of logging for it.

Failures land in the same place. A run that hit a real Gemini constraint showed the error inline with a full Go stack trace, and marked every span in the tree that was affected:

```
Error 400, Message: Function calling with a response mime type: 'application/json'
is unsupported, Status: INVALID_ARGUMENT, Details: []
```

That error is worth knowing on its own, and it is model-specific rather than a Genkit limitation. Running the same tools-plus-typed-output call across five models makes the line clear:

```
gemini-2.5-flash         FAIL  Function calling with a response mime type: 'application/json' is unsupported
gemini-3-flash-preview   OK
gemini-3.5-flash         OK
gemini-3.6-flash         OK
gemini-3.8-flash         OK
```

Gemini 2.5 refuses function calling combined with a JSON response mime type, so on that model a tool call and a typed extraction have to be two steps. Every Gemini 3 model lifted the restriction, which is why the triage service above runs both in one call on `gemini-3.5-flash`. The useful part is that the Developer UI told me which span failed and why, instead of leaving me to bisect it.

The sidebar also carries Traces, Evaluations and Datasets, so the same UI covers running an action by hand, reading what it did, and building a dataset out of it. In LangChainGo, the equivalent of all of this is a `callbacks.Handler` you write yourself, which returns nothing from every method and, as shown above, breaks your Gemini agents when you attach it.

Underneath all four, someone is shipping. When `gemini-2.0-flash` was retired, that was a 404 to work around in LangChainGo and a fallback that healed itself in Genkit.

## What LangChainGo Still Does Well

This is not a demolition. There are real reasons it is still in use:

- **Provider catalog.** Seventeen model providers including Bedrock, Cloudflare, Ernie, HuggingFace, Maritaca, Mistral, watsonx and llamafile. Genkit's plugin set is narrower.
- **Vector store catalog.** Fifteen integrations, including Dolt, MariaDB and OpenSearch, which Genkit has no equivalent for.
- **Conversation memory is less typing.** `chains.NewConversation(llm, memory.NewConversationBuffer())` beats passing `resp.History()` around by hand. Genkit's answer is an agent session store, which is more capable but sits behind an experimental flag, so on a plain generate call LangChainGo is still terser.
- **The ReAct agent works.** On a sequential two-tool task it succeeds consistently. The cost is the code you own, not flakiness.
- **Familiarity.** If your team already thinks in chains, memories and retrievers from Python, the vocabulary transfers directly.

If you depend on a provider or a vector store only LangChainGo supports, that is a real reason to stay. Weigh it against an unmaintained dependency rather than against line counts.

## The Scorecard

Non-blank, non-comment lines.

| Requirement | Genkit Go | LangChainGo |
|---|---|---|
| Full service: RAG + tool + typed output + retry + fallback + tracing | 73, one file | 272, four files |
| Behaviour under a vendor outage | heals, typed output intact | heals at model layer, output parser fails |
| Tool with two typed arguments | 31 | 55 (hand-written unmarshalling) |
| Retry and cross-vendor fallback | 2 config lines | 58 lines, vendor-specific options to strip |
| Local vector store for RAG | ships as `localvec` | 68 lines, no local option exists |
| Observability | built in, zero lines | 36 lines, and it breaks Gemini agents |
| Streaming on current Gemini models | works | broken on all four tested |
| Quickstart with no options | works | 404, default model retired |
| Modules / binary for the same program | 41 / 28.7 MB | 62 / 38.0 MB |

## Conclusion

If you are starting a Go AI project today, use Genkit Go. That part is not close.

If you already have LangChainGo in production, the decision is about risk rather than elegance. The library is eight months without a commit, its Google provider is built on an SDK that reached end of life in November 2025, its quickstart returns a 404, its streaming is broken on every current Gemini model, and turning on observability breaks the agents it is meant to observe. Those are not problems that resolve themselves.

The clearest signal is the outage test. Both versions were supposed to survive a vendor failure, and technically both did at the model layer. Only one came back with the data the caller asked for, because in the other one the layer above was matching on code fences.

Further reading:

- [How to migrate from LangChainGo to Genkit Go](/genkit/2026-09-11-langchaingo-to-genkit-go-migration/), the step-by-step guide
- [Genkit Go vs ADK Go 2.0](/genkit/2026-08-05-genkit-go-vs-adk-go/)
- [Building Agents in Go: Where Genkit Shines vs ADK 2.0](/genkit/2026-08-06-building-agents-genkit-vs-adk-go/)
- [Stop using Python for GenAI, use Genkit Go](/genkit/2026-05-04-stop-using-python-genai-use-genkit-go/)
- [Genkit documentation](https://genkit.dev/)
- [LangChainGo repository](https://github.com/tmc/langchaingo)
- [Mastering Genkit: Go Edition](/books/)
