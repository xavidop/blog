---
layout: post
title: "How to Migrate from LangChainGo to Genkit Go (English)"
description: >
  A complete, step-by-step migration guide. Every LangChainGo concept mapped to its Genkit Go equivalent, with before and after code for models, prompts, chains, structured output, tools, agents, RAG and memory.
image: /assets/img/blog/post-headers/langchaingo-to-genkit-go-migration.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - langchaingo
  - golang
  - migration
keywords:
  - genkit
  - genkit-go
  - langchain
  - langchaingo
  - migration
  - golang
  - rag
  - tools
  - middleware
  - structured-output
  - streaming
  - generative-ai

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

If you built a Go AI service in the last two years, there is a good chance it runs on **[LangChainGo](https://github.com/tmc/langchaingo)**. It was the obvious choice: the name was familiar, the concepts came straight from Python, and it had the biggest provider catalog in the Go ecosystem.

That choice has aged badly. LangChainGo's last release was `v0.1.14` in October 2025, its last commit to `main` was January 2026, and it is still on `0.1.x` after three and a half years. Meanwhile the ecosystem moved: models were retired, SDKs were replaced, and APIs changed shape. LangChainGo did not move with them, and parts of it are broken today as a result.

**[Genkit Go](https://genkit.dev/docs/go/get-started/)** is where that workload belongs now. It is GA, it is on `v1.13.1`, and it is actively maintained by Google.

This guide is the complete migration path: every LangChainGo concept mapped to its Genkit equivalent, with before and after code for each one. Follow it top to bottom and you can move a real service in an afternoon.

If you want the case for *why* rather than the *how*, read the companion article: [LangChainGo vs Genkit Go: where Genkit shines](/genkit/2026-09-11-langchaingo-vs-genkit-go/).

## Why Migrate Now

Three things in LangChainGo are broken today, and none of them will be fixed, because nobody is upstream to fix them.

**1. The default model no longer exists.** `DefaultOptions()` in `llms/googleai/option.go` hardcodes `gemini-2.0-flash`, which Google retired. A fresh `googleai.New(ctx)` with no options fails on the first call:

```
googleapi: Error 404: This model models/gemini-2.0-flash is no longer available.
Please update your code to use models/gemini-3.6-flash for the latest features
and improvements.
```

**2. The Google provider runs on an end-of-life SDK.** `llms/googleai` imports `github.com/google/generative-ai-go`, which Google replaced with `google.golang.org/genai`. Its README is explicit:

> **End-of-Life Date:** All support for this repository (including bug fixes) will permanently end on **November 30, 2025**.

**3. Streaming is broken on every current Gemini model.** Because of that dead SDK, any streaming call through the Google provider fails:

```
error in stream mode: invalid character ']' looking for beginning of value
```

This fails on `gemini-2.5-flash`, `gemini-3-flash-preview`, `gemini-3.5-flash` and `gemini-3.6-flash`. Non-streaming calls still work, and the OpenAI provider streams fine, so this is specific to Google on the legacy SDK.

### The trap: observability breaks your agents

This one catches people out, so it is worth knowing before you debug it the hard way.

LangChainGo turns on streaming automatically whenever you attach a callbacks handler. From `chains/options.go`:

```go
if opts.StreamingFunc == nil && opts.CallbackHandler != nil {
    opts.StreamingFunc = func(ctx context.Context, chunk []byte) error {
        opts.CallbackHandler.HandleStreamingFunc(ctx, chunk)
        return nil
    }
}
```

`agents/mrkl.go` does the same thing. Since streaming is broken, attaching the only supported observability hook is also what breaks your agent. Same agent, same tool, one line different:

```
WITHOUT callbacks handler: err=<nil> out="The current year is 2026."
WITH    callbacks handler: err=error in stream mode: invalid character ']' looking for beginning of value
```

On LangChainGo with Gemini today, you can have working agents or you can have instrumentation. Not both.

## What You Need

- **Go 1.24+** (this guide was written against Go 1.27)
- A **Google AI API key**, free from [Google AI Studio](https://aistudio.google.com/)
- Optionally an **OpenAI API key**, if you want cross-vendor fallback
- The **Genkit CLI**, for the Developer UI:

```bash
npm install -g genkit
```

Add Genkit to your module:

```bash
go get github.com/firebase/genkit/go@latest
```

## The Concept Map

This is the whole translation table. Keep it open while you work.

| LangChainGo | Genkit Go | What changes |
|---|---|---|
| `llms.Model` + provider `New()` | plugin + `genkit.Init` | Models become string references like `googleai/gemini-3.5-flash` |
| `llms.GenerateFromSinglePrompt` | `genkit.GenerateText` | Direct swap |
| `prompts.PromptTemplate` | `ai.WithPrompt` or a `.prompt` file | Dotprompt files keep prompts outside the binary |
| `chains.LLMChain` + `chains.Run` | `genkit.DefineFlow` | A typed Go function instead of a `map[string]any` |
| `chains.NewSequentialChain` | ordinary Go code | Just call the next function |
| `outputparser.NewDefined[T]` | `genkit.GenerateData[T]` | Real schema instead of prompt-and-parse |
| `tools.Tool` interface | `genkit.DefineTool[In, Out]` | Typed arguments with a JSON schema |
| `agents.NewOneShotAgent` (ReAct) | `ai.WithTools`, or `genkitx.DefineAgent` | Native function calling instead of text parsing. Genkit also has a real [agent primitive](https://genkit.dev/docs/go/agents/define/) with sessions |
| `memory.NewConversationBuffer` | `resp.History()`, or an agent session store | Explicit history, or `aix.WithSessionStore` if you want the buffer back |
| `embeddings` + `vectorstores` | `localvec` or a vector store plugin | Genkit has a local store, LangChainGo does not |
| `callbacks.Handler` | built-in tracing | Delete the handler entirely |
| nothing | `middleware.Retry`, `middleware.Fallback` | Retry and fallback stop being your code |

## Step 1: Set Up Genkit

In LangChainGo, each provider is a concrete struct you construct and hold:

```go
llm, err := googleai.New(ctx,
    googleai.WithDefaultModel("gemini-3.5-flash"),
    googleai.WithDefaultEmbeddingModel("gemini-embedding-001"))
if err != nil {
    log.Fatal(err)
}
defer llm.Close()
```

In Genkit, plugins register with one runtime object and models become string references:

```go
g := genkit.Init(ctx,
    genkit.WithPlugins(&googlegenai.GoogleAI{}),
    genkit.WithDefaultModel("googleai/gemini-3.5-flash"))
```

That difference matters more than it looks. Registering a second vendor is one more plugin:

```go
g := genkit.Init(ctx, genkit.WithPlugins(
    &googlegenai.GoogleAI{},
    &openai.OpenAI{},
))
```

Now both vendors live in the same registry and a model is just a name, which is what makes swapping and falling back a configuration change later on.

## Step 2: Migrate Your Model Calls

A plain text generation is close to a direct swap.

**Before:**

```go
out, err := llms.GenerateFromSinglePrompt(ctx, llm,
    "In one sentence: what is Go's error handling philosophy?")
```

**After:**

```go
out, err := genkit.GenerateText(ctx, g,
    ai.WithPrompt("In one sentence: what is Go's error handling philosophy?"))
```

If you need the full response rather than just the text, use `genkit.Generate`, which gives you `resp.Text()`, `resp.History()` and usage data.

## Step 3: Turn Chains into Flows

A LangChainGo chain wraps a prompt template and takes a `map[string]any`:

**Before:**

```go
prompt := prompts.NewPromptTemplate(
    "Triage this support ticket.\n{{.format}}\n\nTicket: {{.ticket}}",
    []string{"format", "ticket"},
)
chain := chains.NewLLMChain(llm, prompt)
raw, err := chains.Predict(ctx, chain, map[string]any{
    "format": parser.GetFormatInstructions(),
    "ticket": ticket,
})
```

A Genkit flow is a typed Go function. Your input and output types are the contract and the compiler enforces them:

**After:**

```go
triage := genkit.DefineFlow(g, "triage", func(ctx context.Context, ticket string) (*Triage, error) {
    out, _, err := genkit.GenerateData[Triage](ctx, g,
        ai.WithPrompt("Triage this support ticket: %s", ticket))
    return out, err
})

out, err := triage.Run(ctx, "I was charged twice for order A-1029.")
```

This step deletes the most code, because most of what a chain does is pass a map around. Go does not need that.

**Sequential chains have no equivalent, and do not need one.** `chains.NewSequentialChain` becomes calling the next function:

```go
summary, err := summarize.Run(ctx, doc)
if err != nil {
    return nil, err
}
return classify.Run(ctx, summary)
```

## Step 4: Migrate Structured Output

Prioritise this step. In LangChainGo, structured output is prompt engineering. In Genkit it is a schema.

**Before:** generate format instructions from your struct, paste them into the prompt, parse the text back.

```go
type Ticket struct {
    Category string `json:"category" describe:"one of: billing, bug, feature, other"`
    Severity int    `json:"severity" describe:"1 (low) to 5 (critical)"`
    Summary  string `json:"summary" describe:"one sentence"`
}

parser, err := outputparser.NewDefined(Ticket{})
// ...put parser.GetFormatInstructions() into the prompt...
out, err := parser.Parse(raw)
```

**After:** one call, with the schema sent to the model as a real response schema.

```go
type Ticket struct {
    Category string `json:"category" jsonschema:"enum=billing,enum=bug,enum=feature,enum=other"`
    Severity int    `json:"severity" jsonschema_description:"1 (low) to 5 (critical)"`
    Summary  string `json:"summary" jsonschema_description:"one sentence"`
}

out, _, err := genkit.GenerateData[Ticket](ctx, g,
    ai.WithPrompt("Triage this support ticket: %s", ticket))
```

Note the tag change: `describe:` becomes `jsonschema_description:`, and enums move into a `jsonschema:` tag where the model actually enforces them.

## Step 5: Migrate Your Tools

The LangChainGo tool interface is `Call(ctx context.Context, input string) (string, error)`. One string in, one string out, no schema. A tool that needs typed arguments has to describe its schema in prose and unmarshal by hand:

**Before:**

```go
func (RefundTool) Name() string { return "issue_refund" }

func (RefundTool) Description() string {
    return `Issues a refund. Input MUST be a JSON object string with exactly these keys:
{"order_id": string, "amount_cents": integer}. Example: {"order_id":"A-1","amount_cents":2500}`
}

func (RefundTool) Call(ctx context.Context, input string) (string, error) {
    input = strings.TrimSpace(input)
    input = strings.TrimPrefix(input, "```json")
    input = strings.TrimPrefix(input, "```")
    input = strings.TrimSuffix(input, "```")
    var a RefundArgs
    if err := json.Unmarshal([]byte(strings.TrimSpace(input)), &a); err != nil {
        return fmt.Sprintf("error: input was not valid JSON (%v). Got: %s", err, input), nil
    }
    return fmt.Sprintf("refunded %d cents for order %s", a.AmountCents, a.OrderID), nil
}
```

In Genkit the tool function is generic over its argument type and the schema comes from the struct:

**After:**

```go
type RefundArgs struct {
    OrderID     string `json:"order_id"`
    AmountCents int    `json:"amount_cents"`
}

refund := genkit.DefineTool(g, "issue_refund", "Issues a refund for an order.",
    func(ctx *ai.ToolContext, a RefundArgs) (string, error) {
        return fmt.Sprintf("refunded %d cents for order %s", a.AmountCents, a.OrderID), nil
    })
```

Delete the fence stripping, the unmarshalling and the prose schema. The model receives a real JSON schema and the arguments arrive typed.

## Step 6: Replace the Agent

A LangChainGo ReAct agent drives tools by parsing the model's text output for `Action:` and `Action Input:` lines, wrapped in an executor with an iteration cap:

**Before:**

```go
agent := agents.NewOneShotAgent(llm, []tools.Tool{RefundTool{}}, agents.WithMaxIterations(6))
out, err := chains.Run(ctx, agents.NewExecutor(agent),
    "Refund order A-1029 for 25 dollars and 50 cents.")
```

In Genkit, native function calling means a one-shot agent is just a generate call with tools attached:

**After:**

```go
out, err := genkit.GenerateText(ctx, g,
    ai.WithPrompt("Refund order A-1029 for 25 dollars and 50 cents."),
    ai.WithTools(refund))
```

No executor, no iteration cap, no text parsing. Genkit runs the tool loop for you.

### When you want a real agent, Genkit has one

The generate call above replaces a `OneShotAgent`. For anything that has to hold a conversation, Genkit Go ships an actual [agent primitive](https://genkit.dev/docs/go/agents/define/) with sessions and persisted state, which LangChainGo has no equivalent for:

```go
import (
    aix "github.com/firebase/genkit/go/ai/exp"
    "github.com/firebase/genkit/go/ai/exp/localstore"
    genkitx "github.com/firebase/genkit/go/genkit/exp"
)

g := genkit.Init(ctx,
    genkit.WithPlugins(&googlegenai.GoogleAI{}),
    genkit.WithDefaultModel("googleai/gemini-2.5-flash"),
    genkit.WithExperimental())

store := localstore.NewInMemorySessionStore[State]()

agent := genkitx.DefineAgent(g, "taskAgent",
    aix.InlinePrompt{
        ai.WithSystem("Manage a task list. Use tools when changing tasks."),
        ai.WithTools(addTask),
    },
    aix.WithSessionStore(store),
    aix.WithDescription[State]("Task management assistant"),
)
```

Three constructors are available: `DefineAgent` for an inline prompt, `DefinePromptAgent` to wrap a prompt already in the registry, and `DefineCustomAgent` to replace the prompt loop with your own code. Options cover a session store, `WithStateTransform` to reshape state on the way out to a client, and `WithStreamTransform` for chunks. You drive one with `Run`, `RunText`, or `Connect` for a streaming connection.

> **These live in the `exp` packages.** Agents are experimental in Genkit Go v1.13.1, and calling `genkitx.DefineAgent` without `genkit.WithExperimental()` on `genkit.Init` panics with a message telling you so. The API may change between minor releases, so weigh that before putting one in production.

## Step 7: Migrate RAG

Check this step before planning your timeline, because it has an infrastructure consequence.

LangChainGo ships fifteen vector stores: AlloyDB, Azure AI Search, Bedrock Knowledge Bases, Chroma, CloudSQL, Dolt, MariaDB, Milvus, MongoDB, OpenSearch, pgvector, Pinecone, Qdrant, Redis and Weaviate. **Every one of them needs an external service running.** There is no in-memory or local option, and the pull request adding one has been open since February 2024. If you needed a local store, you wrote it yourself.

Genkit ships `localvec`, a file-backed local store, so the same thing is three calls:

**After:**

```go
embedder := googlegenai.GoogleAIEmbedder(g, "gemini-embedding-001")
store, retriever, err := localvec.DefineRetriever(g, "policy",
    localvec.Config{Dir: "/tmp/gkvec", Embedder: embedder}, nil)
if err != nil {
    return err
}

// Index your documents once.
localvec.Index(ctx, docs, store)

// Retrieve at request time.
found, err := genkit.Retrieve(ctx, g, ai.WithRetriever(retriever), ai.WithTextDocs(ticket))
```

Then hand the documents straight to the model:

```go
out, _, err := genkit.GenerateData[Triage](ctx, g,
    ai.WithDocs(found.Documents...),
    ai.WithPrompt("Triage this ticket using the policy documents: %s", ticket))
```

If you were on a hosted store, Genkit has Pinecone, Weaviate, Postgres and AlloyDB plugins.

## Step 8: Migrate Memory

LangChainGo keeps conversation history in a buffer attached to the chain:

**Before:**

```go
c := chains.NewConversation(llm, memory.NewConversationBuffer())
chains.Run(ctx, c, "My name is Xavi and I work in Go.")
chains.Run(ctx, c, "What is my name and what language do I use?")
```

Genkit passes history explicitly:

**After:**

```go
resp, err := genkit.Generate(ctx, g, ai.WithPrompt("My name is Xavi and I work in Go."))
if err != nil {
    return err
}

resp, err = genkit.Generate(ctx, g,
    ai.WithMessages(resp.History()...),
    ai.WithPrompt("What is my name and what language do I use?"))
```

For a plain generate call this is the one mapping where LangChainGo is less typing. The trade is that Genkit has no hidden buffer to keep in sync, which is what you want the moment your conversation state lives in Redis or Postgres and your handlers are stateless.

If you want the buffer back, that is what an agent's session store is for. Give the agent a store and pass a session id, and the history is the framework's problem again:

```go
store := localstore.NewInMemorySessionStore[State]()

agent := genkitx.DefineAgent(g, "taskAgent",
    aix.InlinePrompt{
        ai.WithSystem("Manage a task list. Use tools when changing tasks. Be terse."),
        ai.WithTools(addTask),
    },
    aix.WithSessionStore(store))

for _, turn := range []string{
    "Add 'buy milk' to my list.",
    "What did I just ask you to add?",
} {
    out, err := agent.RunText(ctx, turn, aix.WithSessionID[State]("demo-session"))
    if err != nil {
        return err
    }
    fmt.Printf("> %s\n%s\n\n", turn, out.Message.Text())
}
```

```
> Add 'buy milk' to my list.
Task added.

> What did I just ask you to add?
You asked me to add 'buy milk' to your list.
```

Nothing in that loop passes the first turn into the second. The session id does it. `localstore.NewInMemorySessionStore` is the one that ships for local development; the `SessionStore` interface is what you implement to put sessions in Redis or Postgres.

So the honest version of this row is: Genkit gives you both ends. Explicit `resp.History()` when you want stateless handlers, and a store-backed session when you want the buffer.

## Step 9: Delete Your Resilience Code

This is the step that usually surprises people with how much it removes.

LangChainGo has no middleware layer. `callbacks.Handler` is seventeen methods that all return nothing:

```go
HandleText(ctx, text)
HandleLLMGenerateContentStart(ctx, ms)
HandleLLMGenerateContentEnd(ctx, res)
HandleToolStart(ctx, input)
// ...and thirteen more
```

You can watch a call. You cannot wrap it, retry it, rewrite its request or substitute a model, because there is no `next()`. There is no retry, no fallback and no OpenTelemetry anywhere in the library, so if your service has those, you wrote them.

In Genkit they are configuration:

**After:**

```go
out, _, err := genkit.GenerateData[Triage](ctx, g,
    ai.WithModel(googlegenai.GoogleAIModelRef("gemini-3.5-flash", nil)),
    ai.WithDocs(found.Documents...),
    ai.WithTools(refund),
    ai.WithPrompt("Triage this ticket and act on it: %s", ticket),
    ai.WithUse(
        &middleware.Retry{MaxRetries: 2},
        &middleware.Fallback{Models: []ai.ModelRef{openai.ModelRef("gpt-5-mini", nil)}},
    ),
)
```

Register the middleware plugin at init and those two lines are live:

```go
g := genkit.Init(ctx, genkit.WithPlugins(
    &googlegenai.GoogleAI{}, &openai.OpenAI{}, &middleware.Middleware{},
))
```

Point the primary at a dead model and the request heals onto the other vendor on its own:

```
WARN model call failed, falling back model=openai/gpt-5-mini error="Error 404 ... NOT_FOUND"
{Category:billing Severity:2 PolicyQuote:Duplicate charges must be refunded in full within 5
business days, no manager approval required. Action:Issued full refund of $25.50 (2550 cents)
for the duplicate charge on order A-1029.}
```

Gemini went down, OpenAI picked it up, the tool still ran, and the typed struct came back intact.

**Delete your callbacks handler too.** Genkit traces flows, generate calls, tool calls and retrieval automatically. Run the Developer UI to see them:

```bash
genkit start -- go run .
```

## Step 10: Wrap the Entrypoints

Finally, expose your flows over HTTP. Where LangChainGo left you writing `net/http` handlers around chains, Genkit turns a flow into an endpoint:

```go
mux := http.NewServeMux()
mux.HandleFunc("POST /triage", genkit.Handler(triage))
log.Fatal(server.Start(ctx, "127.0.0.1:3400", mux))
```

The flow's input and output types define the request and response shapes, so the whole path is typed end to end.

## Before You Commit

The migration is not free. Check these three things first:

**Provider and vector store catalog.** LangChainGo has seventeen model providers and fifteen vector stores. Genkit Go covers Google AI, Vertex, OpenAI, Anthropic, Ollama and the OpenAI-compatible vendors, plus Pinecone, Weaviate, Postgres and AlloyDB. If you are on Dolt, MariaDB or Bedrock Knowledge Bases as a vector store, confirm you have a path.

**Conversation buffers.** There is no drop-in `ConversationBuffer`. You pass history explicitly, as in Step 8.

**Specialised chains.** Helpers like `chains.NewSQLDatabaseChain` and the map-reduce summarisation chains have no one-to-one equivalent. In Genkit they are Go functions you write, which is usually shorter than the chain was, but it is work.

## Conclusion

The migration is smaller than it looks, because most of a LangChainGo program is plumbing that Go does not need: maps passed between chains, format instructions pasted into prompts, JSON unmarshalled out of tool strings, and a resilience layer you wrote yourself. Typed flows, typed tools, schema-backed output and middleware delete all four.

The reason to start now is not ergonomics. It is that the library your service depends on has a retired default model, an end-of-life SDK underneath its Google provider, broken streaming, and an observability hook that breaks the agents it is supposed to observe. Those are not problems you can wait out.

For the side-by-side numbers and the full picture, read the companion: [LangChainGo vs Genkit Go: where Genkit shines](/genkit/2026-09-11-langchaingo-vs-genkit-go/).

Further reading:

- [Genkit documentation](https://genkit.dev/)
- [Genkit Go plugins](https://genkit.dev/go/docs/plugins/)
- [LangChainGo repository](https://github.com/tmc/langchaingo)
- [Google Gen AI SDK for Go](https://github.com/googleapis/go-genai), the replacement for the SDK LangChainGo still uses
- [Stop using Python for GenAI, use Genkit Go](/genkit/2026-05-04-stop-using-python-genai-use-genkit-go/)
- [Mastering Genkit: Go Edition](/books/)
