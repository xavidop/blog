---
layout: post
title: "Genkit Go vs ADK Go 2.0: a Hands-On Look at Boilerplate and Low-Level Control (English)"
description: >
  I built the same eight programs twice, once with Genkit Go and once with Google's ADK Go 2.0, and ran them all against Gemini: hello world, structured output, streaming, tools, middleware, custom models, multi-turn and HTTP serving. This is what the code actually looks like in each, where ADK makes you pay an "agent tax", where Genkit lets you drop lower, and where ADK's ceremony genuinely pays off.
image: /assets/img/blog/post-headers/genkit-go-vs-adk-go.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - adk
  - golang
  - gemini
keywords:
  - genkit
  - genkit-go
  - adk
  - adk-go
  - agent-development-kit
  - golang
  - gemini
  - generative-ai
  - structured-output
  - middleware
  - ollama
  - comparison

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

**Genkit** and **ADK (Agent Development Kit)** are both Google-backed Gen AI frameworks with first-class Go SDKs, and I keep getting the same question: *what is actually different when you sit down and write the code?*

This is not a "which one is better" article. They point at different problems: ADK is an **agent orchestration framework** (agents, sessions, multi-agent transfer, and since 2.0 a graph-based workflow engine), while Genkit is a **Gen AI application framework** (model calls, flows, structured output, middleware). But they overlap on the everyday tasks every Go developer does (call a model, get typed output, stream, add tools, intercept requests), and on those tasks the developer experience diverges a lot.

So instead of comparing docs, I wrote the same eight programs twice and ran every single one against a live Gemini backend:

1. One prompt → one answer
2. A raw model call with no framework machinery
3. Structured output into a Go struct
4. Streaming
5. Tool calling
6. Intercepting / wrapping the model call
7. A custom model backend
8. Multi-turn conversation and HTTP serving

Everything below compiled and ran on **Genkit Go v1.11.0** and **ADK Go v2.1.0** (the `google.golang.org/adk/v2` module, GA since June 30, 2026) with `gemini-3-flash-preview`, on 2026-08-05. Where I quote framework internals, they come from those released versions, not from the main branch. Nothing in this article is speculated from documentation.

## TL;DR

| Task | Genkit Go | ADK Go 2.0 |
|---|---|---|
| One prompt → text | `genkit.GenerateText(...)`: 21 lines, 2 error paths | model + agent + runner + session + event loop: 49 lines, 8 error paths |
| Structured output | `genkit.GenerateData[Recipe](...)`, schema inferred from struct tags, typed result | hand-written `genai.Schema` tree, raw JSON text back, unmarshal it yourself |
| Streaming | callback receives deltas, final response is ready-assembled | SSE partial events; the final event **repeats the full text**, you deduplicate by hand |
| Tools | typed Go func, loop runs inside `Generate` | typed Go func (genuinely elegant), but agent/runner/session around it |
| Wrap the model call | `WithUse` middleware with a real `next()`, applied per call | fixed-signature callbacks (no wrapping) or decorate the `model.LLM` interface, per agent |
| Local models (Ollama) | official plugin, first-class provider | no native support; OpenAI-compatible adapter with `BaseURL` |
| Custom model backend | one function, works instantly with `Generate` | two-method interface (the smallest contract in either SDK), but invoking it needs the full stack |
| Multi-turn | automatic via agents + session stores (experimental track); `resp.History()` for plain generate calls | automatic via the GA session services |
| Multi-agent | delegation via the `Agents` middleware (experimental track) | first-class: sub-agents, transfer, workflow graph engine |
| Serve over HTTP | `genkit.Handler(flow)` on plain `net/http` | full REST platform API (sessions, SSE, events) + embedded Web UI |
| Ecosystem | 16 Go plugins: multi-vendor models, vector stores, telemetry, MCP | Google Cloud integrations (Vertex, GCS, BigQuery, Apigee, Cloud Run) + OpenAI-compatible + MCP |

The pattern that emerged: **Genkit's primitive is the model call; ADK's primitive is the agent.** When the thing you need *is* a model call, Genkit hands it to you directly and ADK makes you rent the whole agent apparatus. When the thing you need *is* a long-lived, multi-agent system, ADK's apparatus stops being boilerplate and starts being the product.

## The mental model

### Genkit: the model call is the unit

Genkit Go has exactly one setup object (`*genkit.Genkit`) and everything else is a package-level function call:

```go
g := genkit.Init(ctx, genkit.WithPlugins(&googlegenai.GoogleAI{}))

text, err := genkit.GenerateText(ctx, g,
    ai.WithModelName("googleai/gemini-3-flash-preview"),
    ai.WithPrompt("Why is Go a great language for building AI agents? One short sentence."),
)
```

That is the complete program (plus imports and an error check). `Init` doesn't even return an error: configuration problems panic at startup, and from there on there is a single `err` to handle per generation. My runnable version is **21 non-blank lines with 2 error-handling lines**.

### ADK: the agent is the unit

ADK has no "just generate" entry point at the framework level. The unit of execution is an agent, and an agent runs inside a runner, and a runner requires a session service. This is the minimal equivalent program:

```go
model, err := gemini.NewModel(ctx, "gemini-3-flash-preview", &genai.ClientConfig{
    APIKey: os.Getenv("GOOGLE_API_KEY"),
})
// if err != nil ...

a, err := llmagent.New(llmagent.Config{
    Name:        "assistant",
    Model:       model,
    Instruction: "You are a helpful assistant.",
})
// if err != nil ...

r, err := runner.NewInMemory("hello-app", a) // in-memory session/artifact/memory services
// if err != nil ...

msg := genai.NewContentFromText("Why is Go a great language for building AI agents? One short sentence.", genai.RoleUser)

var text string
for event, err := range r.Run(ctx, "user-1", "session-1", msg, agent.RunConfig{}) {
    if err != nil { /* ... */ }
    if event.LLMResponse.Content == nil {
        continue
    }
    if event.IsFinalResponse() {
        for _, part := range event.LLMResponse.Content.Parts {
            text += part.Text
        }
    }
}
```

**49 non-blank lines, 8 error-handling lines** for the same output. And to be fair, `runner.NewInMemory` is already ADK being nice: the explicit form makes you wire `runner.Config{AppName, Agent, SessionService, AutoCreateSession}` yourself.

Count the concepts you must hold for one prompt: a model, an agent with a `Name` (mandatory), an app name, a user ID, a session ID (both meaningless for a one-shot call, both mandatory positional arguments), a `RunConfig`, an event iterator, an `IsFinalResponse()` predicate, and manual concatenation of `Content.Parts`. There is **no `.Text()` helper on events**. Even ADK's own console launcher spends ~45 lines turning events into printable text (`cmd/launcher/console/console.go`), because every consumer re-implements this loop.

None of this is *bad* design: sessions, users and apps are exactly the right vocabulary for a deployed multi-agent platform. It is simply the wrong altitude when what you wanted was an answer to a prompt, and there is no lower altitude offered (almost; see the escape hatch below).

## Structured output: where the gap is widest

This was the experiment with the biggest difference, and the one where I initially got ADK *wrong* in an instructive way.

### Genkit

You describe the shape as a Go type. The JSON Schema is inferred from the struct (via reflection over `json`/`jsonschema` tags), constrained decoding is enabled by default, and you get the struct back, parsed and typed:

```go
type Recipe struct {
    Name        string   `json:"name"`
    PrepMinutes int      `json:"prep_minutes"`
    Ingredients []string `json:"ingredients"`
}

recipe, _, err := genkit.GenerateData[Recipe](ctx, g,
    ai.WithModelName("googleai/gemini-3-flash-preview"),
    ai.WithSystem("You generate recipes."),
    ai.WithPrompt("A simple tortilla de patatas recipe"),
)

fmt.Println(recipe.Name, recipe.PrepMinutes, recipe.Ingredients)
```

Output from my run:

```
Classic Spanish Tortilla de Patatas (15 min): 5 ingredients
```

28 lines total. The schema definition **is** the Go type.

### ADK

ADK's `llmagent.Config.OutputSchema` takes a `*genai.Schema`: a hand-built tree, field by field, with a hand-maintained `Required` list. There is no "infer from struct" path for agent output (curiously, ADK *does* have schema inference, but only for tool inputs):

```go
recipeSchema := &genai.Schema{
    Type: genai.TypeObject,
    Properties: map[string]*genai.Schema{
        "name":         {Type: genai.TypeString},
        "prep_minutes": {Type: genai.TypeInteger},
        "ingredients":  {Type: genai.TypeArray, Items: &genai.Schema{Type: genai.TypeString}},
    },
    Required: []string{"name", "prep_minutes", "ingredients"},
}

a, err := llmagent.New(llmagent.Config{
    Name:         "chef",
    Model:        model,
    Instruction:  "You generate recipes.",
    OutputSchema: recipeSchema,
})
```

The schema enforcement worked perfectly in my runs: Gemini returned valid JSON every time. The interesting part is what happens next. My first attempt read the event's `Output` field, which looks exactly like what you want. It was always `nil`.

Digging into the released v2.1.0 source: the LlmAgent *does* parse the structured output internally, and *does* attach it to the event, but the runner **deliberately strips it before the event reaches you**. In `runner/runner.go`, every non-partial agent reply gets cloned with `clone.Output = nil`. The parsed value exists to feed ADK 2.0's graph workflow engine (typed routing between nodes), not for you. As a consumer of `Runner.Run`, you receive raw JSON as text and parse it yourself:

```go
var jsonText string
for event, err := range r.Run(ctx, "user-1", "session-1", msg, agent.RunConfig{}) {
    // ... error handling, nil checks, IsFinalResponse, Parts loop ...
    jsonText += part.Text
}

var recipe Recipe
if err := json.Unmarshal([]byte(jsonText), &recipe); err != nil { /* ... */ }
```

(If you set `OutputKey`, the same **raw string** is also copied into session state, still not parsed for you.)

Two more sharp edges I hit in the source while verifying this:

- The `OutputSchema` doc comment in v2.1.0 still warns: *"when this is set, agent can only reply and cannot use any tools, such as function tools, RAGs, agent transfer, etc."* The implementation has grown workarounds (on some backends it injects a synthetic `set_model_response` tool; on Vertex AI with Gemini ≥2.0 it can use native constrained output alongside tools), which means combining tools and output schema behaves **differently depending on backend and model name**, silently.
- Final tally: **68 lines vs Genkit's 28**, and the typed half of "typed output" is entirely yours to write.

## Streaming: deltas vs partial events

Both frameworks stream. The difference is who assembles the result.

**Genkit** gives you a callback that receives *deltas*, and the final response arrives already assembled:

```go
resp, err := genkit.Generate(ctx, g,
    ai.WithModelName("googleai/gemini-3-flash-preview"),
    ai.WithPrompt("Count from one to ten in words, one per line."),
    ai.WithStreaming(func(ctx context.Context, chunk *ai.ModelResponseChunk) error {
        fmt.Print(chunk.Text())
        return nil
    }),
)
```

My run printed `streamed chars: 48, final response chars: 48`. Chunks and final response account for the same text exactly once each.

**ADK** streams by setting `agent.RunConfig{StreamingMode: agent.StreamingModeSSE}` and then flags chunk events with `LLMResponse.Partial`. The gotcha: after all the partial events, ADK emits a final non-partial event that **repeats the entire text**. My run: `partial (streamed) chars: 48, final event chars: 48`. Print events naively and you output everything twice. Every ADK consumer must carry this filter:

```go
for event, err := range r.Run(ctx, "user-1", "session-1", msg, agent.RunConfig{
    StreamingMode: agent.StreamingModeSSE,
}) {
    // ...
    if event.LLMResponse.Partial {
        fmt.Print(part.Text) // the streamed deltas
    }
    // the final event repeats the full text: skip it, or you print it twice
}
```

This isn't hypothetical: ADK's own example code and console launcher both contain hand-rolled deduplication (`if text != prevText` in `cmd/launcher/console/console.go`). It's a small thing, but it's a small thing *every single ADK streaming consumer* writes, and no Genkit consumer does. As a bonus, Genkit's `GenerateDataStream[T]` even streams *partially-parsed typed structs* (your `Recipe` filling in field by field), which has no ADK equivalent.

## Tool calling: closer than I expected

Here I expected a bigger gap and didn't find one: ADK's function tools are genuinely well designed. Both frameworks let a tool be an ordinary typed Go function, with the JSON Schema inferred from the input struct:

```go
// Genkit
weather := genkit.DefineTool(g, "getWeather", "Gets the current weather for a city",
    func(ctx *ai.ToolContext, in WeatherInput) (string, error) {
        return fmt.Sprintf("22C and sunny in %s", in.City), nil
    })

resp, err := genkit.Generate(ctx, g,
    ai.WithModelName("googleai/gemini-3-flash-preview"),
    ai.WithPrompt("What is the weather in Valencia right now?"),
    ai.WithTools(weather),
)
```

```go
// ADK: also nice! Generics, schema inferred, type params never spelled out.
weatherTool, err := functiontool.New(functiontool.Config{
    Name:        "get_weather",
    Description: "Gets the current weather for a city",
}, func(_ agent.Context, in WeatherInput) (WeatherOutput, error) {
    return WeatherOutput{Report: fmt.Sprintf("22C and sunny in %s", in.City)}, nil
})
```

Both ran the tool and produced the right answer. The differences are around the edges:

- **Ceremony**: the Genkit program is 29 lines; the ADK one is 66, because the tool still needs the agent/runner/session stack around it.
- **Where the loop lives**: Genkit's tool loop runs *inside* `Generate` (with parallel tool execution and a `WithMaxTurns` bound), so tools work in a plain one-shot call. In ADK the loop belongs to the agent flow, which is consistent with its philosophy, but it means there is no way to use ADK tools without an agent.
- **A public-API gotcha**: ADK's public `tool.Tool` interface is only `Name()/Description()/IsLongRunning()`. The *executable* contract (`Declaration()`, `Run()`) lives in an `internal/` package you cannot reference, so you can't hand-implement a runnable tool against a public interface; you go through `functiontool.New`. Genkit's equivalent (`ai.ToolFunc` + `DefineTool`) is fully public.
- **Composability limit**: ADK documents (in its own `examples/tools/multipletools`) that you cannot mix built-in Gemini tools like `geminitool.GoogleSearch{}` with custom function tools on one agent; the workaround is wrapping each in a sub-agent.
- Genkit also has **tool interrupts/resume** as a stable API (pause generation from inside a tool, get an `Interrupts()` list, resume with `RespondWith`/`RestartWith`). ADK's equivalents are tool confirmation flows wired through its HITL machinery.

## Getting low-level

You can go deeper in Genkit than in ADK, and its middleware system is the reason: Genkit exposes the model call, the tool executions and the whole generation loop as wrappable layers, while ADK exposes fixed callback points and one wrappable interface. Here is what that means in code.

### Wrapping the model call

**Genkit** middleware is a real onion: you get the request *and* a `next()` you control. Timing, retry, caching and request rewriting are all one closure, applied per call:

```go
timing := ai.MiddlewareFunc(func(ctx context.Context) (*ai.Hooks, error) {
    return &ai.Hooks{
        WrapModel: func(ctx context.Context, params *ai.ModelParams, next ai.ModelNext) (*ai.ModelResponse, error) {
            start := time.Now()
            resp, err := next(ctx, params)
            log.Printf("model call: %d messages in, took %s",
                len(params.Request.Messages), time.Since(start))
            return resp, err
        },
    }, nil
})

resp, err := genkit.Generate(ctx, g, /* ... */, ai.WithUse(timing))
```

Ran, printed `model call: 1 messages in, took 3.323s`. There are `WrapGenerate` and `WrapTool` hooks at the other two altitudes (the whole tool loop, and each tool execution), middleware can inject tools, and the built-ins (`Retry`, `Fallback`, tool approval, filesystem sandbox) compose the same way.

**ADK** has callbacks, not middleware: `BeforeModelCallback` and `AfterModelCallback` with fixed signatures. They can short-circuit (return a response from `Before` and the model is never called, the documented caching hook) and they can replace the response, but they cannot *wrap*. There is no `next()`. To time a call I had to smuggle state between two separate functions:

```go
var start time.Time

before := func(ctx agent.Context, req *model.LLMRequest) (*model.LLMResponse, error) {
    start = time.Now()
    return nil, nil // nil means "continue to the model"
}
after := func(ctx agent.Context, resp *model.LLMResponse, respErr error) (*model.LLMResponse, error) {
    log.Printf("took %s", time.Since(start))
    return nil, nil
}
```

This works (ran, `took 1.631s`) but it's a workaround, it's attached per-agent rather than per-call, and anything genuinely wrap-shaped (hedged requests, per-attempt timeouts, fallbacks across models) has to move to a different mechanism entirely: decorating the model. Which brings me to the thing ADK gets *really* right:

### Custom model backends: local Gemma on Ollama

Nobody plugs in an echo model, so no toy examples here. The realistic scenario is a backend the framework didn't bless for you: a local model server, an internal gateway, a provider without an official plugin. I tested two levels of this: running Google's Gemma locally on Ollama, and writing a backend from scratch.

Genkit ships an official Ollama plugin, so the local model is a first-class provider:

```go
oll := &ollama.Ollama{ServerAddress: "http://localhost:11434"}
g := genkit.Init(ctx, genkit.WithPlugins(oll))

gemma := oll.DefineModel(g, ollama.ModelDefinition{Name: "gemma3n:e4b", Type: "chat"}, nil)

resp, err := genkit.Generate(ctx, g,
    ai.WithModel(gemma),
    ai.WithPrompt("Why is Go a great language for building AI agents? One short sentence."),
)
```

**23 lines**, ran on the first try against `gemma3n:e4b` on my Mac, and the local model gets the same `Generate`, flows, middleware and structured output as any cloud model. The plugin covers embedders too.

ADK has no Ollama integration of its own. The path that works is the OpenAI-compatible adapter pointed at Ollama's OpenAI endpoint:

```go
gemma, err := openaimodel.NewModel(ctx, "gemma3n:e4b", &openaimodel.ClientConfig{
    BaseURL: "http://localhost:11434/v1",
    APIKey:  "ollama", // any non-empty value; Ollama ignores it
})
```

This also ran (**47 lines** with the usual agent, runner and session around it), and it is a documented path: the package README lists Ollama, LM Studio and vLLM. The difference is the shape of the support. In Genkit the local model is a provider with its own plugin; in ADK it rides on OpenAI compatibility, so anything Ollama offers outside that API surface is out of reach, and then you are writing the backend yourself, which is the next scenario.

### And when there is no plugin at all

When the backend has no plugin and no OpenAI-compatible endpoint (an internal LLM gateway, a niche provider), you write the integration yourself. I did, in both frameworks: the same minimal OpenAI `chat/completions` client, roughly 45 lines of identical plain-`net/http` glue, run against the real OpenAI API.

ADK's `model.LLM` interface is the smallest custom-backend contract I've seen in any framework:

```go
type LLM interface {
    Name() string
    GenerateContent(ctx context.Context, req *LLMRequest, stream bool) iter.Seq2[*LLMResponse, error]
}
```

Two methods, and this interface is also ADK's genuine wrapping seam: ADK's own examples ship a `resilientModel` decorator doing retries and per-attempt timeouts this way. My OpenAI-backed `model.LLM` worked, with two costs on top of the shared HTTP glue. First, the vocabulary: requests and responses are `google.golang.org/genai` types, so you translate both ways, and some of it is non-obvious. The agent's `Instruction` arrives in `Config.SystemInstruction`, not in `Contents`; miss that and your backend silently drops the system prompt. (ADK's own OpenAI adapter is four files of translation code, which tells you how deep that rabbit hole goes. Also, parts of ADK sniff behavior from `llm.Name()`, so a renaming wrapper can silently change how output schemas are handled.) Second, the invocation: those two beautiful methods still need the agent, runner and session stack around them to run. Total: **116 lines**.

The Genkit version of the same backend is the HTTP glue, a capability declaration, and nothing else:

```go
func callOpenAI(ctx context.Context, req *ai.ModelRequest, cb func(context.Context, *ai.ModelResponseChunk) error) (*ai.ModelResponse, error) {
    body := oaRequest{Model: "gpt-4o-mini"}
    for _, m := range req.Messages {
        role := string(m.Role) // "system" | "user" | "model"
        if role == "model" {
            role = "assistant"
        }
        body.Messages = append(body.Messages, oaMessage{Role: role, Content: m.Text()})
    }
    // ... plain net/http POST to api.openai.com/v1/chat/completions ...
    return &ai.ModelResponse{
        FinishReason: ai.FinishReasonStop,
        Message:      ai.NewModelTextMessage(out.Choices[0].Message.Content),
    }, nil
}

gpt := genkit.DefineModel(g, "myco/gpt-4o-mini", &ai.ModelOptions{
    Supports: &ai.ModelSupports{Multiturn: true, SystemRole: true},
}, callOpenAI)

resp, err := genkit.Generate(ctx, g,
    ai.WithModel(gpt),
    ai.WithSystem("You are a helpful assistant."),
    ai.WithPrompt("Why is Go a great language for building AI agents? One short sentence."),
)
```

Total: **79 lines**, and `Generate` calls it directly; the model immediately works with structured output, streaming, middleware and flows. The messages arrive as provider-neutral structs (`ai.Message`, with system prompt as a regular `system`-role message), so the translation is one role-mapping loop instead of a genai round-trip. One honest note: my first attempt failed at runtime because I passed `nil` options, since a Genkit model must declare what it `Supports`. That cost me one extra struct literal, and it's the flip side of a real feature: the framework validates every request against the declared capabilities and even simulates a system prompt for models that don't support one.

### The raw call escape hatch

I didn't want to write "you can't go low-level in ADK" without trying it myself, so I tried. `model.LLM` is public, and this compiles and runs (33 lines in my experiment):

```go
llm, _ := gemini.NewModel(ctx, "gemini-3-flash-preview", &genai.ClientConfig{APIKey: key})

for resp, err := range llm.GenerateContent(ctx, &model.LLMRequest{
    Contents: []*genai.Content{genai.NewContentFromText(prompt, genai.RoleUser)},
}, false) {
    // resp.Content.Parts ...
}
```

But notice what you're holding: this is the bare genai transport with an ADK-shaped envelope. No instruction templating, no tool loop, no callbacks, no structured output processing, no telemetry: all of that lives inside the agent flow you just bypassed. There are no helpers (`Text()`, message builders) at this layer, and no example in the entire ADK repo uses it; only tests do. It's an escape hatch, not a supported altitude.

That's the crux of the low-level story: **in Genkit, dropping down doesn't cost you the framework.** `Generate` *is* the low-level call: raw messages in, with middleware, tools, schemas and tracing still active. In ADK, the abstraction is a cliff: you're either at agent altitude with everything, or at transport altitude with nothing.

## Where ADK's ceremony pays off

I also ran the experiments where I expected ADK's extra structure to earn its keep. It mostly did.

**Multi-turn conversation.** Both frameworks carry the conversation for you; neither makes you thread history by hand.

In ADK, I called `r.Run` twice with the same session ID and the second turn knew my name and city. The session service *is* the conversation, and swapping `InMemoryService` for the database or Vertex AI implementation brings persistence with it.

In Genkit, the agents API does the same job with a session store. I ran the equivalent two turns on v1.11.0:

```go
g := genkit.Init(ctx,
    genkit.WithPlugins(&googlegenai.GoogleAI{}),
    genkit.WithExperimental(),
)

assistant := genkitx.DefineAgent(g, "assistant",
    aix.InlinePrompt{
        ai.WithModelName("googleai/gemini-3-flash-preview"),
        ai.WithSystem("You are a helpful assistant."),
    },
    aix.WithSessionStore(localstore.NewInMemorySessionStore[any]()),
)

first, err := assistant.RunText(ctx, "My name is Xavi and I live in Valencia. Say hi in one sentence.")
// ...
second, err := assistant.RunText(ctx, "Where do I live? Answer with just the city name.",
    aix.WithSessionID[any](first.SessionID))
```

Both frameworks answered `turn 2: Valencia` in my runs, with zero history plumbing on either side. And Genkit's session layer goes further than a message log: session snapshots, detach/resume (the client disconnects, the server keeps working, you resume from a snapshot) and artifacts, with in-memory and file stores shipping today plus a `SessionStore` interface for your own persistence. For conversation state, the two frameworks are at parity. (If you are outside an agent, composing plain `Generate` calls, `ai.WithMessages(resp.History()...)` threads history in one line, but that is a choice, not a limitation.)

The one difference I would plan around is the maturity label. ADK's session services are GA and are the default path; Genkit's agents API is on the experimental track behind `genkit.WithExperimental()` and can change between minor releases, which is also why the rest of this article compares the stable surfaces. If you are comfortable riding the experimental track, Genkit gives you all of it today; if you need the stability guarantee, ADK has it.

**Multi-agent.** ADK's sub-agents get an auto-injected `transfer_to_agent` tool, there are sequential/parallel/loop workflow agents, and 2.0's headline feature is a full graph workflow engine with typed routing between nodes, retries and human-in-the-loop pauses.

Genkit delegates too. The `Agents` middleware injects one `delegate_to_<name>` tool per sub-agent, discovers each sub-agent's description automatically for the orchestrator's prompt, forwards recent conversation history, and can merge sub-agent artifacts back into the orchestrator's session. I ran an orchestrator delegating to a poet sub-agent:

```go
orchestrator := genkitx.DefineAgent(g, "orchestrator",
    aix.InlinePrompt{
        ai.WithModelName("googleai/gemini-3-flash-preview"),
        ai.WithSystem("You are a coordinator. Delegate writing tasks to the right sub-agent using its delegation tool, then return its result verbatim."),
        ai.WithUse(&middlewarex.Agents{
            Agents:         []aix.AgentRef{poet.Ref()},
            MaxDelegations: 2,
        }),
    },
    aix.WithSessionStore(localstore.NewInMemorySessionStore[any]()),
)
```

43 lines, worked on the first run (I got my haiku back through the orchestrator), and the full researcher-plus-engineer version is in the official [basic-agents sample](https://github.com/genkit-ai/genkit/tree/main/go/samples/basic-agents). Same maturity note as sessions: this is the experimental track.

And ADK's workflow layer, the sequential/parallel/loop agents and the 2.0 graph engine? Genkit's answer is that the orchestration language is Go itself. [Flows compose](https://genkit.dev/docs/go/flows/): a flow calls other flows, sequence is code order, parallel is a goroutine group, a loop is a loop, and every flow stays traced and individually servable. I ran a brief-writing flow that fans out to two sub-flows in parallel and then synthesizes:

```go
brief := genkit.DefineFlow(g, "briefFlow",
    func(ctx context.Context, topic string) (string, error) {
        // Parallel: plain Go concurrency.
        var facts, structure string
        eg, egCtx := errgroup.WithContext(ctx)
        eg.Go(func() error {
            var err error
            facts, err = research.Run(egCtx, topic)
            return err
        })
        eg.Go(func() error {
            var err error
            structure, err = outline.Run(egCtx, topic)
            return err
        })
        if err := eg.Wait(); err != nil {
            return "", err
        }

        // Sequential: the next line of code.
        return genkit.GenerateText(ctx, g,
            ai.WithModelName(model),
            ai.WithPrompt("Write a two-sentence brief about %s using these facts:\n%s\nand this outline:\n%s", topic, facts, structure))
    })
```

**53 lines** including both sub-flows, ran on stable APIs, and `genkit.Handler(brief)` serves it over HTTP like any other flow. So the difference between the two workflow stories is representation, not capability. ADK reifies the pipeline as a data structure (edges, typed routes) executed by an engine that owns retries, pauses and resumability at the graph level; Genkit keeps the pipeline as ordinary Go and covers those concerns with its own pieces (tool interrupts for human-in-the-loop, the retry middleware, and durable execution through integrations like Temporal). Pick by taste: an inspectable graph object, or code you read top to bottom.

**The serving platform.** Genkit's HTTP story is its philosophy in miniature. A flow becomes a handler on plain `net/http`:

```go
mux := http.NewServeMux()
mux.HandleFunc("POST /greetingFlow", genkit.Handler(greetingFlow))
server.Start(ctx, "127.0.0.1:9090", mux)
```

```bash
$ curl -X POST localhost:9090/greetingFlow -d '{"data":"Xavi"}'
{"result":"Hello, Xavi!"}
```

ADK's `adkrest.NewServer` is also a plain `http.Handler` (nice), but what it mounts is a *platform*: app listing, session CRUD, SSE runtime, artifacts, debug/trace endpoints. My curl transcript needed two calls (create the session, then run) and got back the full event envelope with usage metadata, state deltas and node info. On top of that, ADK's launcher embeds the entire ADK Web UI into your binary via `go:embed`: `go run . web webui` gives you a chat UI with no npm and no separate process, which is honestly great. (Genkit's Developer UI is a separate CLI process, though it's also more than a chat UI: it traces every generate call, middleware hop and tool execution.)

These aren't contradictions of the boilerplate findings; they're the same design measured on its own terrain. ADK's five constructors are the price of a system where conversations persist, agents transfer to each other, and a REST platform falls out of a config struct.

## The plugin ecosystems

One more thing I checked in the released modules, because it changes the decision for real projects: what each framework integrates with out of the box.

Genkit Go v1.11.0 ships sixteen plugins in the module: model providers for Google (Gemini API and Vertex AI), **Anthropic**, **OpenAI plus any OpenAI-compatible endpoint**, and **Ollama**; vector stores for **AlloyDB, PostgreSQL/pgvector, Pinecone, Weaviate** and a local dev store; **Firebase** and **Google Cloud** telemetry; **MCP**; evaluators; and the middleware pack. And that is the Go module alone, before you count the wider JS ecosystem the framework shares its design with.

ADK Go v2.1.0's integrations are a coherent Google Cloud story: Gemini and Vertex models, the OpenAI-compatible adapter, **Apigee**; sessions in memory, in a SQL database or on **Vertex AI**; **GCS** artifacts; **Vertex AI** memory; **BigQuery** agent analytics; MCP toolsets; and deploy tooling for **Cloud Run** and **Agent Engine**. What it does not have is a provider ecosystem beyond that: no Anthropic plugin, no vector store integrations, nothing aimed at other clouds.

If your stack is pure Google Cloud, ADK's set covers it end to end, deploy included. The moment you need Anthropic next to Gemini, a Postgres vector store, or observability outside Google Cloud, Genkit has the plugin and ADK expects you to build it.

## The scorecard

Numbers from my runnable programs (non-blank lines including imports; error-handling lines in parentheses):

| Experiment | Genkit Go | ADK Go 2.0 |
|---|---|---|
| Hello world | 21 (2) | 49 (8) |
| Raw model call | same as hello | 33 (4), undocumented path |
| Structured output → typed struct | 28 (2) | 68 (9) |
| Streaming | 27 (2) | 54 (8) |
| One tool | 29 (2) | 66 (10) |
| Time the model call | 34 (2) | 61 (8) |
| Local Gemma via Ollama, invoked | 23 (2) | 47 (8) |
| Custom model backend (real OpenAI), invoked | 79 (5) | 116 (13) |
| Multi-turn (2 turns) | 37 (4) with agents + sessions; 30 (4) with plain `Generate` | 51 (8) |

Line counts are a blunt instrument; the interesting part is *what the extra lines are*. In every ADK program they are the same lines: construct model, construct agent, construct runner, invent user/session IDs, iterate events, filter partials, concatenate parts. It's a fixed tax, roughly 25-30 lines, charged on every program regardless of whether sessions and events are relevant to it.

## A concrete decision guide

I would reach for **Genkit Go** when:

- The unit of my product is a **model call or a flow**: an API endpoint, a pipeline step, a CLI, a backend feature.
- I want **typed structured output** without maintaining schema trees by hand.
- I want to **wrap, retry, fall back, cache or rewrite** model calls with composable per-call middleware.
- I'm integrating a **custom or non-Google model backend** and want the framework features to keep working on top of it.
- I value the Dev UI's per-call tracing during development.
- I want sessions and agents too, and I'm fine with the experimental track while that API stabilizes.
- My stack mixes vendors: Anthropic or OpenAI next to Gemini, Ollama locally, or Postgres/Pinecone/Weaviate for retrieval. The plugin shelf already covers them.

I would reach for **ADK Go 2.0** when:

- The unit of my product is a **persistent, session-based agent**: a chat product, a support agent, anything where conversation state is the point, and I want it on GA APIs today.
- I need **multi-agent coordination**: sub-agent transfer, workflow agents, or 2.0's graph engine with typed routing and HITL pauses.
- I want the **serving platform for free**: session REST API, SSE, the embedded Web UI, A2A, Cloud Run / Agent Engine deploy tooling.
- My stack is Gemini/Vertex-first and the `genai`-typed vocabulary is a feature, not a translation burden.

And these compose better than you'd think: nothing stops you from building your model-centric services with Genkit flows and standing up an ADK agent where you genuinely need the agent platform. They're both idiomatic modern Go (both lean on `iter.Seq2` and generics nicely), and they're solving different layers of the same problem.

## Conclusion

After running everything, the facts are these: Genkit lets you get lower-level, and ADK charges more boilerplate. In detail:

- The boilerplate is real and remarkably consistent: ADK charges a fixed ~25-30 line agent tax on every program, because **there is no supported altitude between "full agent" and "bare transport"**. Genkit's `Generate` occupies exactly that missing middle: raw request access with the framework still on.
- The low-level gap is sharpest in **structured output** (typed structs vs hand-built schema trees plus DIY parsing, and a runner that deliberately strips the parsed value it already has) and in **middleware** (a real `next()` vs fixed-signature callbacks).
- But ADK's ceremony is not waste: it buys GA session persistence, multi-agent transfer, a graph engine and an embedded serving platform, and some of its individual designs (the two-method `model.LLM`, generic function tools) are excellent Go.

Pick the altitude that matches your product, and don't confuse "more setup" with "more capable", or "less setup" with "less serious." They're different tools that happen to share a language and a model provider.

Further reading:

- [Genkit Go Get Started guide](https://genkit.dev/docs/go/get-started/)
- [ADK 2.0 release notes](https://adk.dev/2.0/)
- [Genkit GitHub repository](https://github.com/genkit-ai/genkit)
- [ADK Go GitHub repository](https://github.com/google/adk-go)
- [Genkit Go basic-agents sample (orchestrator, delegation, artifacts)](https://github.com/genkit-ai/genkit/tree/main/go/samples/basic-agents)
- [Genkit Go flows documentation](https://genkit.dev/docs/go/flows/)
- [Stop Using Python for Gen AI: Genkit Go](/genkit/2026-05-04-stop-using-python-genai-use-genkit-go/)
- [Vercel AI SDK Middleware vs Genkit Middleware](/genkit/2026-05-13-vercel-ai-sdk-vs-genkit-middleware/)
