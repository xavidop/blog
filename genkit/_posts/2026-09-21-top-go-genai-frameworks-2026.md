---
layout: post
title: "Top Gen AI Frameworks for Go in 2026: A Hands-On Comparison (English)"
description: >
  A practical, in-depth comparison of the top Generative AI frameworks for Go in 2026: Genkit Go, Eino, Google ADK Go, tRPC-Agent-Go, and LangChainGo, with real code and real output for each one (English)
image: /assets/img/blog/post-headers/top-go-genai-frameworks-2026.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - golang
  - comparison
keywords:
  - genkit-go
  - eino
  - google-adk-go
  - trpc-agent-go
  - langchaingo
  - generative-ai
  - golang
  - go
  - ai-frameworks
  - 2026
  - comparison
  - agents
  - flows
  - observability
  - dev-ui

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

Go has quietly become the language of AI infrastructure. MCP servers, agent runtimes, model gateways, Kubernetes operators that talk to LLMs: a large share of that plumbing is written in Go, because Go is what you reach for when something has to be a small static binary that handles thousands of concurrent connections without drama. What was missing for a long time was the framework layer on top of the raw provider SDKs. In 2026 that gap is closed, and the question is no longer "Go or Python?" but "which Go framework?".

This article covers the five frameworks a Go developer will actually run into in 2026: **Genkit Go**, **Eino**, **Google ADK Go**, **tRPC-Agent-Go**, and **LangChainGo**. Four of them are alive and moving fast. The fifth, LangChainGo, is the one most Go developers heard of first, and it is now effectively unmaintained. It stays in the list because you will find it in existing codebases, and you need to know what that means for you.

Same rules as the [Java](/genkit/2026-04-16-top-java-genai-frameworks-2026/) and [JavaScript/TypeScript](/genkit/2026-04-16-top-jsts-genai-frameworks-2026/) editions: this is not a benchmark post. Tokens per second go stale in weeks. This is a developer experience and architecture comparison, with working code and the real output of that code for every framework, all against the same model, `gemini-3.8-flash`, on Go 1.27.

Versions used: Genkit Go v1.13.1, Eino v0.9.20, Google ADK Go v2.4.0, tRPC-Agent-Go v1.11.2, LangChainGo v0.1.14. APIs as of **September 2026**.

---

## Genkit Go

### History and Direction

Genkit was announced by Google at I/O 2024 as a TypeScript-first framework. The Go SDK arrived only three months later, with v0.1.0 in August 2024, and unlike the Java SDK, which is a community effort, **Genkit Go is an official, first-party SDK** maintained by the same Firebase team that ships the TypeScript runtime. It reached 1.0 in September 2025 and sits at v1.13.1 as of September 2026, on a cadence of roughly one minor release per month.

The direction is parity with TypeScript plus Go-native ergonomics: generics instead of Zod schemas, `context.Context` everywhere, plain `net/http` handlers for flows, and an agents package, still marked experimental, with session stores, multi-agent delegation, artifacts, and a `Skills` middleware. The monorepo (`firebase/genkit`) has 6.4k stars and 80 commits in the last 30 days across all SDKs.

If you want the long-form introduction, start with [Stop Using Python for Your Gen AI Apps, Use Go and Genkit Instead](/genkit/2026-05-04-stop-using-python-genai-use-genkit-go/).

### What Makes Genkit Go Stand Out

Genkit Go gives you **three levels of abstraction in a single SDK**: direct model calls, typed flows, and agents, all traced by the same OpenTelemetry pipeline and all visible in the same Dev UI. On top of that sits a middleware layer (retry, fallback, tool approval, filesystem, skills) that wraps any of the three. No other Go framework gives you that combination.

**Supported languages:** Go 1.25+ for this SDK. The same framework exists for TypeScript, Python, Dart/Flutter, and, unofficially, Java.

#### Vanilla Generation

```go
import (
    "github.com/firebase/genkit/go/ai"
    "github.com/firebase/genkit/go/genkit"
    "github.com/firebase/genkit/go/plugins/googlegenai"
)

g := genkit.Init(ctx,
    genkit.WithPlugins(&googlegenai.GoogleAI{}),
    genkit.WithDefaultModel("googleai/gemini-3.8-flash"))

text, err := genkit.GenerateText(ctx, g,
    ai.WithPrompt("Explain the CAP theorem in two sentences."))
```

```
The CAP theorem states that a distributed data system can simultaneously provide at most two of three guarantees: Consistency, Availability, and Partition tolerance. Because network partitions are inevitable in the real world, systems must ultimately choose between returning the most up-to-date data (Consistency) or ensuring every request receives a response (Availability).
```

#### Typed Flows: Observable Pipelines

Flows are the heart of Genkit. A flow is a named, typed, traceable unit that you can call in-process, expose as an HTTP endpoint with one line, and run from the Dev UI. The JSON schema for the output comes from the Go struct, and `GenerateData` returns the struct, not a string you have to parse.

```go
type TranslateRequest struct {
    Text           string `json:"text"`
    TargetLanguage string `json:"target_language"`
}

type TranslateResponse struct {
    Translation      string `json:"translation"`
    DetectedLanguage string `json:"detected_language"`
}

translate := genkit.DefineFlow(g, "translateText",
    func(ctx context.Context, req TranslateRequest) (*TranslateResponse, error) {
        out, _, err := genkit.GenerateData[TranslateResponse](ctx, g,
            ai.WithPrompt("Translate %q to %s and detect the source language.",
                req.Text, req.TargetLanguage))
        return out, err
    })

// Call it in-process...
out, err := translate.Run(ctx, TranslateRequest{Text: "Buenos días", TargetLanguage: "English"})
fmt.Printf("%+v\n", *out)

// ...or expose it over HTTP (and to the Dev UI).
mux := http.NewServeMux()
mux.HandleFunc("POST /translateText", genkit.Handler(translate))
log.Fatal(server.Start(ctx, "127.0.0.1:3400", mux))
```

```
{Translation:Good morning DetectedLanguage:Spanish}
INFO server listening addr=127.0.0.1:3400
```

```bash
curl -X POST http://127.0.0.1:3400/translateText \
  -H 'Content-Type: application/json' \
  -d '{"data":{"text":"Buenos días","target_language":"English"}}'
# {"result":{"translation":"Good morning","detected_language":"Spanish"}}
```

#### Tools and Agents

Tools are typed functions. The input schema is inferred from the struct, and the tool loop (model asks, tool runs, model answers) happens inside `Generate`.

```go
type WeatherInput struct {
    City string `json:"city"`
}

weather := genkit.DefineTool(g, "getWeather", "Returns the current weather for a city.",
    func(ctx *ai.ToolContext, in WeatherInput) (string, error) {
        return fmt.Sprintf("Sunny, 24C in %s", in.City), nil
    })

resp, err := genkit.Generate(ctx, g,
    ai.WithPrompt("What's the weather like in Tokyo?"),
    ai.WithTools(weather))
fmt.Println(resp.Text())
```

```
The weather in Tokyo is currently sunny and 24°C.
```

When you need memory across turns, the experimental agents package adds sessions on top of the same tools. Enable it with `genkit.WithExperimental()`:

```go
import (
    aix "github.com/firebase/genkit/go/ai/exp"
    "github.com/firebase/genkit/go/ai/exp/localstore"
    genkitx "github.com/firebase/genkit/go/genkit/exp"
)

advisor := genkitx.DefineAgent(g, "travelAdvisor",
    aix.InlinePrompt{
        ai.WithSystem("You are a helpful travel advisor. Use tools to give accurate advice. Be brief."),
        ai.WithTools(weather),
    },
    aix.WithSessionStore(localstore.NewInMemorySessionStore[any]()))

first, err := advisor.RunText(ctx, "Should I pack a jacket for my trip to Lisbon?")
second, err := advisor.RunText(ctx, "Which city did I ask about?",
    aix.WithSessionID[any](first.SessionID))
```

```
It is currently sunny and 24°C (75°F) in Lisbon. You won't need a heavy coat, but packing a light jacket or sweater is recommended for cooler evenings and coastal breezes.
You asked about Lisbon.
```

Multi-agent delegation, cross-vendor fallback, and tool approval are covered in [Building Agents in Go: Where Genkit Shines vs ADK 2.0](/genkit/2026-08-06-building-agents-genkit-vs-adk-go/).

#### The Dev UI: Same Power as TypeScript

The **same Genkit Developer UI** that TypeScript developers use works with Go, with no code changes. Install the CLI (Node.js) and start your Go program through it:

```bash
npm install -g genkit
genkit start -- go run .
```

```
Genkit Developer UI: http://localhost:4000
```

The flow above shows up as `/flow/translateText` next to every Gemini model the plugin registered, and you get:

- **Flow runner**: execute any flow with a custom input and inspect the typed output.
- **Trace explorer**: OpenTelemetry traces for every `Generate` and flow call, with latency, token counts, and the exact prompts.
- **Model playground**: call any registered model directly.
- **Tool testing**: run tools in isolation.
- **Dotprompt editor**: edit `.prompt` files live.

This is the single biggest advantage Genkit has over every other framework in this list: a zero-config, local trace explorer that replaces Langfuse or LangSmith during development.

#### Provider Support

Official plugins in the Go module: **Google AI (Gemini)**, **Vertex AI**, **Anthropic**, **Ollama**, and an OpenAI-compatible family (`compat_oai`) with ready-made packages for **OpenAI**, **xAI**, **DeepSeek**, **OpenRouter**, **Kimi**, **DashScope**, and **Z.ai**. Vector stores: `localvec` (local, no service needed), **PostgreSQL/pgvector**, **AlloyDB**, **Pinecone**, **Weaviate**, and **Firebase Firestore**. Plus **MCP** (client and server), evaluators, and an **A2UI** plugin for streaming UI components.

#### Pros and Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Best-in-class Dev UI with local trace explorer | Agents package still marked experimental |
| Multi-level abstractions: vanilla, flows, agents | Fewer vector stores than LangChainGo |
| Middleware: retry, fallback, tool approval | Go 1.25+ required |
| Official Google SDK, monthly releases | Dev UI needs Node.js installed |
| Typed output from Go structs, no parsing | |
| Same framework in TS, Python, Dart, Java | |

---

## Eino

### History and Direction

Eino (pronounced "aino") comes from ByteDance's CloudWeGo team, the group behind Kitex and Hertz, the RPC and HTTP frameworks that run a large part of ByteDance's Go services. It was open-sourced in December 2024 after internal use, and it is now the **most-starred LLM framework in Go** at 13.1k stars, ahead of LangChainGo. Releases land every few days: v0.9.20 on September 20, 2026, with v0.10.0 already at alpha 35.

Eino's own description is that it draws from LangChain and Google ADK but follows Go conventions. The framework splits in two: `compose`, for orchestration (Chain, Graph, Workflow), and `adk`, an Agent Development Kit that borrows Google ADK's vocabulary of agents, runners, and events. Components (models, tools, retrievers, indexers, loaders) live in a separate repo, `eino-ext`, together with callback handlers for Langfuse, LangSmith, CozeLoop, and ByteDance's APMPlus.

The 2026 roadmap is all agents: DeepAgent (planning plus sub-agents), agent middleware, interrupt and resume for human-in-the-loop, skills, A2UI streaming components, and a turn loop with preemption. The English documentation on cloudwego.io is now a full eleven-chapter course, a big change from 2025 when most of it was Chinese-first.

### What Makes Eino Stand Out

Orchestration with **automatic stream handling**. Every node in an Eino graph can be invoked or streamed, and the framework concatenates, boxes, merges, and copies streams as data moves between nodes. You build the graph once and get both `Invoke` and `Stream` for free. Graph inputs and outputs are generic types, so the compiler checks that the nodes fit together. Cross-cutting concerns go through callbacks at fixed points (`OnStart`, `OnEnd`, `OnError`, plus the streaming variants) that apply to components, graphs, and agents alike.

**Supported languages:** Go only. The module declares `go 1.18`, the lowest bar in this list. One thing to know: Eino depends on ByteDance's `sonic` JSON library, and on Go 1.27 it prints a warning at startup and falls back to `encoding/json`. Harmless, but noisy.

#### ChatModel

Eino does not own the provider client. You create the `genai` client yourself and hand it to the component.

```go
import (
    "github.com/cloudwego/eino-ext/components/model/gemini"
    "github.com/cloudwego/eino/schema"
    "google.golang.org/genai"
)

client, err := genai.NewClient(ctx, &genai.ClientConfig{APIKey: os.Getenv("GEMINI_API_KEY")})
cm, err := gemini.NewChatModel(ctx, &gemini.Config{Client: client, Model: "gemini-3.8-flash"})

msg, err := cm.Generate(ctx, []*schema.Message{
    schema.UserMessage("Explain the CAP theorem in two sentences."),
})
fmt.Println(msg.Content)
```

```
The CAP theorem states that a distributed data store can simultaneously provide at most two of three guarantees: Consistency, Availability, and Partition tolerance. Because network partitions are practically inevitable in distributed systems, architects must choose between keeping data strictly up-to-date (Consistency) or ensuring the system remains responsive (Availability) during a network failure.
```

#### Chains, Graphs, and Callbacks

A chain is a linear pipeline. Here the callback handler is attached at invocation time and fires for the chain, the template, and the model.

```go
import (
    "github.com/cloudwego/eino/callbacks"
    "github.com/cloudwego/eino/components/prompt"
    "github.com/cloudwego/eino/compose"
)

template := prompt.FromMessages(schema.FString,
    schema.SystemMessage("You are a translator. Reply with the translation only."),
    schema.UserMessage("Translate {text} to {language}."))

chain := compose.NewChain[map[string]any, *schema.Message]()
chain.AppendChatTemplate(template).AppendChatModel(cm)
runnable, err := chain.Compile(ctx)

tracer := callbacks.NewHandlerBuilder().
    OnStartFn(func(ctx context.Context, info *callbacks.RunInfo, in callbacks.CallbackInput) context.Context {
        log.Printf("start %s %s", info.Component, info.Type)
        return ctx
    }).
    OnEndFn(func(ctx context.Context, info *callbacks.RunInfo, out callbacks.CallbackOutput) context.Context {
        log.Printf("end   %s %s", info.Component, info.Type)
        return ctx
    }).
    Build()

out, err := runnable.Invoke(ctx,
    map[string]any{"text": "Buenos días", "language": "English"},
    compose.WithCallbacks(tracer))
fmt.Println(out.Content)
```

```
start Chain
start ChatTemplate Default
end   ChatTemplate Default
start ChatModel Gemini
end   ChatModel Gemini
end   Chain
Good morning
```

Graphs are where Eino earns its name. Nodes are typed, edges are explicit, and plain Go functions slot in as lambda nodes:

```go
graph := compose.NewGraph[map[string]any, string]()
_ = graph.AddChatTemplateNode("template", template)
_ = graph.AddChatModelNode("generate", cm)
_ = graph.AddLambdaNode("shout", compose.InvokableLambda(
    func(ctx context.Context, msg *schema.Message) (string, error) {
        return strings.ToUpper(strings.TrimSpace(msg.Content)), nil
    }))

_ = graph.AddEdge(compose.START, "template")
_ = graph.AddEdge("template", "generate")
_ = graph.AddEdge("generate", "shout")
_ = graph.AddEdge("shout", compose.END)

runnable, err := graph.Compile(ctx)
out, err := runnable.Invoke(ctx, map[string]any{"product": "a Go framework for LLM apps"})
```

```
BUILD PRODUCTION-GRADE LLM APPS AT GO SPEED.
```

Branches, parallel fan-out, and sub-graphs use the same API, and a compiled graph can be wrapped as a tool and handed to an agent.

#### Eino ADK: Agents and Workflows

Tools are inferred from a Go struct with `jsonschema` tags. The agent runs the ReAct loop and emits one event per step, so you see the tool call, the tool result, and the final answer as separate messages.

```go
import (
    "github.com/cloudwego/eino/adk"
    "github.com/cloudwego/eino/components/tool"
    "github.com/cloudwego/eino/components/tool/utils"
)

type WeatherInput struct {
    City string `json:"city" jsonschema:"description=The city to look up"`
}

weather, err := utils.InferTool("get_weather", "Returns the current weather for a city.",
    func(ctx context.Context, in WeatherInput) (string, error) {
        return fmt.Sprintf("Sunny, 24C in %s", in.City), nil
    })

advisor, err := adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{
    Name:        "travel_advisor",
    Description: "Helps with trip planning and weather-based advice.",
    Instruction: "You are a helpful travel advisor. Use tools to give accurate advice. Be brief.",
    Model:       cm,
    ToolsConfig: adk.ToolsConfig{
        ToolsNodeConfig: compose.ToolsNodeConfig{Tools: []tool.BaseTool{weather}},
    },
})

runner := adk.NewRunner(ctx, adk.RunnerConfig{Agent: advisor})
iter := runner.Query(ctx, "Should I pack a jacket for my trip to Lisbon?")
for {
    event, ok := iter.Next()
    if !ok {
        break
    }
    if event.Err != nil {
        log.Fatal(event.Err)
    }
    if event.Output == nil || event.Output.MessageOutput == nil {
        continue
    }
    msg, _ := event.Output.MessageOutput.GetMessage()
    fmt.Printf("[%s] %s\n", msg.Role, msg.Content)
}
```

```
[assistant]
[tool] Sunny, 24C in Lisbon
[assistant] It is currently sunny and 24°C (75°F) in Lisbon. You won't need a heavy coat, but packing a light jacket or cardigan is a good idea for breezy coastal evenings.
```

The first assistant event is the tool call itself, which is why its content is empty. Multi-agent workflows are one constructor away:

```go
pipeline, err := adk.NewSequentialAgent(ctx, &adk.SequentialAgentConfig{
    Name:        "content_pipeline",
    Description: "Research, then write.",
    SubAgents:   []adk.Agent{researcher, writer},
})
```

```
[researcher] 1. Created at Google by Robert Griesemer, Rob Pike, and Ken Thompson; released in 2009.
2. Statically typed, compiled language with built-in garbage collection.
3. Features native, lightweight concurrency through goroutines and channels.

[writer] Created at Google by Robert Griesemer, Rob Pike, and Ken Thompson, the Go programming language was released in 2009. It is a statically typed, compiled language that features built-in garbage collection and native, lightweight concurrency through goroutines and channels.
```

`NewParallelAgent` and `NewLoopAgent` complete the set, and DeepAgent adds planning and delegation on top.

#### Developer Tooling

Eino's answer to observability during development is the **Eino Dev** plugin for GoLand and VS Code, backed by the `devops` module in `eino-ext`. It renders your chains and graphs visually inside the editor and lets you start execution from any node with mock input. It is an IDE feature rather than a browser Dev UI, so there is no trace explorer for a running service. For that you attach one of the callback handlers (Langfuse, LangSmith, CozeLoop, APMPlus).

#### Provider Support

Model components in `eino-ext`: **OpenAI**, **Claude**, **Gemini**, **DeepSeek**, **Qwen**, **Ollama**, **OpenRouter**, **Ark** (Volcano Engine), and **Qianfan** (Baidu), plus "agentic" variants of the main ones for the newer agentic message format. Retrievers and indexers: **Elasticsearch** (7, 8, 9), **Milvus**, **Qdrant**, **Redis**, **OpenSearch**, **Dify**, and **VikingDB**. Tools: **MCP**, Google Search, Bing, DuckDuckGo, SearXNG, Wikipedia, HTTP request, command line, browser use, and sequential thinking.

#### Pros and Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Most active independent Go LLM framework (13.1k stars) | Still 0.x with frequent alphas; expect API churn |
| Typed graph orchestration with automatic streaming | No browser Dev UI; visual debugging lives in the IDE plugin |
| Callback aspects for logging, tracing, and metrics | Verbose: config structs and explicit error checks everywhere |
| ADK-style agents plus DeepAgent and interrupt/resume | ByteDance-flavoured corners (Ark, VikingDB, CozeLoop) |
| Broad component ecosystem in `eino-ext` | `sonic` dependency warns on the newest Go toolchains |
| Runs on Go 1.18+ | Chinese-first history still shows in some docs and examples |

---

## Google ADK Go

### History and Direction

ADK, the Agent Development Kit, was announced at Google Cloud Next 2025 with Python as its first language. The Go SDK made its first tagged release, v0.1.0, in November 2025, went 1.0 on March 23, 2026, and shipped a new major module, `google.golang.org/adk/v2`, on June 30, 2026. It is at v2.4.0 (September 11, 2026), has 8.8k stars, and logged over 100 commits in the last 30 days: the highest commit volume in this list. It is an official Google product with the Python, Java, Kotlin, and TypeScript SDKs as siblings.

The design is the same as its siblings: everything is an agent, a workflow agent, or a tool. Gemini is the native model, with `openaimodel` for anything speaking the OpenAI wire format and an Apigee model for enterprise gateways. Deployment gravity points at **Vertex AI Agent Engine**, Cloud Run, and GKE, with Pub/Sub and Eventarc triggers built into the launcher. The minimum Go version is 1.26.6, the highest bar of the five.

A deeper look at the low-level differences with Genkit is in [Genkit Go vs ADK Go 2.0](/genkit/2026-08-05-genkit-go-vs-adk-go/).

### ADK Go's Position: Agent-Only, Enterprise-Grade

ADK Go is an **agent framework**. There is no vanilla generation primitive and no flow abstraction: you always build an agent, give it to a runner, and iterate the events. In exchange you get sessions, memory, artifacts, workflow agents, agent-to-agent (A2A) protocol support, MCP toolsets, tool confirmation, and an embedded web UI, all first party.

**Supported languages:** Go 1.26.6+. Same framework in Python (primary), Java, Kotlin, and TypeScript.

```go
import (
    "google.golang.org/adk/v2/agent"
    "google.golang.org/adk/v2/agent/llmagent"
    "google.golang.org/adk/v2/model/gemini"
    "google.golang.org/adk/v2/runner"
    "google.golang.org/adk/v2/tool"
    "google.golang.org/adk/v2/tool/functiontool"
    "google.golang.org/genai"
)

model, err := gemini.NewModel(ctx, "gemini-3.8-flash", &genai.ClientConfig{
    APIKey: os.Getenv("GOOGLE_API_KEY"),
})

weather, err := functiontool.New(functiontool.Config{
    Name:        "get_weather",
    Description: "Returns the current weather for a city.",
}, func(_ agent.Context, in WeatherInput) (WeatherOutput, error) {
    return WeatherOutput{Report: fmt.Sprintf("Sunny, 24C in %s", in.City)}, nil
})

advisor, err := llmagent.New(llmagent.Config{
    Name:        "travel_advisor",
    Model:       model,
    Instruction: "You are a helpful travel advisor. Use tools to give accurate advice. Be brief.",
    Tools:       []tool.Tool{weather},
})

r, err := runner.NewInMemory("travel-app", advisor)

msg := genai.NewContentFromText("Should I pack a jacket for my trip to Lisbon?", genai.RoleUser)
for event, err := range r.Run(ctx, "user-1", "session-1", msg, agent.RunConfig{}) {
    if err != nil {
        log.Fatal(err)
    }
    if event.LLMResponse.Content == nil || !event.IsFinalResponse() {
        continue
    }
    for _, part := range event.LLMResponse.Content.Parts {
        fmt.Print(part.Text)
    }
}
```

```
It is currently sunny and warm at 24°C (75°F) in Lisbon. You won't need a heavy jacket during the day, but packing a light jacket or sweater is recommended for cooler evenings and coastal breezes.
```

Two things to notice. The runner returns a Go 1.23 iterator, so you `range` over events with the error as the second value, which is the most idiomatic event loop of the five. And the function tool is generic: input and output structs give the schema, nothing is spelled out twice.

#### Multi-Agent Orchestration

Workflow agents compose LLM agents. The `OutputKey` writes an agent's answer into session state, and the next agent reads it back through a `{placeholder}` in its instruction.

```go
import "google.golang.org/adk/v2/agent/workflowagents/sequentialagent"

researcher, err := llmagent.New(llmagent.Config{
    Name:        "researcher",
    Model:       model,
    Instruction: "List three key facts about the user's topic. Be terse.",
    OutputKey:   "facts", // saved into session state
})
writer, err := llmagent.New(llmagent.Config{
    Name:        "writer",
    Model:       model,
    Instruction: "Write a two-sentence brief using these facts:\n{facts}",
})

pipeline, err := sequentialagent.New(sequentialagent.Config{
    AgentConfig: agent.Config{
        Name:      "content_pipeline",
        SubAgents: []agent.Agent{researcher, writer},
    },
})
```

```
[researcher] * **Origin:** Developed at Google by Robert Griesemer, Rob Pike, and Ken Thompson; released as open source in 2009.
* **Concurrency:** Features built-in, lightweight concurrency primitives known as goroutines and channels, managed by its own runtime.
* **Ecosystem Role:** Statically typed and compiled, it is the primary language behind core cloud-native technologies, including Docker and Kubernetes.

[writer] Developed at Google by Robert Griesemer, Rob Pike, and Ken Thompson and released as open source in 2009, Go is a statically typed, compiled language featuring built-in, lightweight concurrency primitives known as goroutines and channels that are managed by its own runtime. Owing to these strengths, it has become the primary language powering core cloud-native technologies, including Docker and Kubernetes.
```

`parallelagent` and `loopagent` follow the same pattern.

#### The Dev UI: ADK Web, Embedded in Your Binary

The `full` launcher turns any agent into a CLI with `console` and `web` modes. The web mode takes sub-launchers, and `webui` serves the Angular **ADK Web** app straight out of your Go binary via `go:embed`, so there is nothing to install:

```go
import (
    "google.golang.org/adk/v2/cmd/launcher"
    "google.golang.org/adk/v2/cmd/launcher/full"
)

l := full.NewLauncher()
config := &launcher.Config{AgentLoader: agent.NewSingleLoader(advisor)}
if err := l.Execute(ctx, config, os.Args[1:]); err != nil {
    log.Fatalf("%v\n\n%s", err, l.CommandLineSyntax())
}
```

```bash
go run . web -port 8080 api webui
```

```
Web servers starts on http://localhost:8080
       api:  you can access API using http://localhost:8080/api
```

The root URL redirects to `/ui/`, the Agent Development Kit Dev UI, and `/api/list-apps` answers `["assistant"]`. The launcher also wires `a2a`, `pubsub`, and `eventarc` sub-servers, and an `-otel_to_cloud` flag exports traces to Google Cloud. Flags go before the sub-launcher names, or the sub-launcher rejects them.

#### Vertex AI Gravity

You can run ADK Go anywhere. But the session and memory services with persistence are the in-memory ones, a database-backed session store, and **Vertex AI**; the evaluation tooling, the managed scaling, and the telemetry defaults all assume Google Cloud. Same trade-off as ADK Java and ADK Python: the best experience is on GCP.

#### Pros and Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Official Google support, highest commit velocity | Agent-only: no vanilla generation, no flows |
| Idiomatic Go: generics for tools, iterators for events | Go 1.26.6+ required |
| Embedded ADK Web UI, no extra install | Strong pull toward Vertex AI and GCP |
| Sequential, parallel, and loop workflow agents | Gemini-first; other providers only through OpenAI-compatible endpoints |
| A2A, MCP toolsets, tool confirmation, artifacts | No vector store components; RAG goes through tools or Vertex |
| Same mental model as ADK Python/Java/TS | Config structs get long for real agents |

---

## tRPC-Agent-Go

### History and Direction

tRPC-Agent-Go is Tencent's entry, built by the team behind tRPC, the RPC framework that underpins much of Tencent's backend. Development started in May 2025, the first public release (v0.0.1) landed in August 2025, and the project reached 1.x at the end of December 2025. It is now at v1.11.2 (August 20, 2026), with 1.8k stars and 56 commits in the last 30 days. The README credits Tencent Yuanbao, Tencent Video, Tencent News, IMA, and QQ Music with real-world validation, and I have no reason to doubt it.

The framework is unapologetically **ADK-shaped**: `llmagent`, `runner`, `chainagent`, `parallelagent`, `cycleagent`, sessions, memory, `OutputKey`, `{placeholder}` instructions. If you know ADK, you already know most of it. What it adds on top is where it gets interesting: a **GraphAgent** that is a faithful LangGraph in Go (state schemas, conditional edges, checkpoints, time travel), an **AG-UI** server for streaming agent events to frontends, A2A, MCP, Anthropic-style **Agent Skills** with sandboxed execution, agent self-evolution, an evaluation package, model failover and hedging, prompt caching, and OpenTelemetry traces and metrics with Langfuse examples. RAG is covered by a knowledge module with embedders for OpenAI, Gemini, Ollama, and Hugging Face, and stores from in-memory and SQLite-vec up to pgvector, Elasticsearch, Milvus, Qdrant, and TcVector.

### What Makes tRPC-Agent-Go Stand Out

The **GraphAgent**. Nobody else in Go ships a LangGraph-equivalent state graph as a first-class agent type that plugs into the same runner, sessions, and telemetry as the LLM agents.

**Supported languages:** Go only, `go 1.21+`. Model providers: **OpenAI** and anything OpenAI-compatible (DeepSeek, Qwen, and friends through variants), **Anthropic**, **Gemini**, **Bedrock**, **Ollama**, **Hugging Face**, and **Hunyuan**.

```go
import (
    "trpc.group/trpc-go/trpc-agent-go/agent/llmagent"
    "trpc.group/trpc-go/trpc-agent-go/model"
    "trpc.group/trpc-go/trpc-agent-go/model/gemini"
    "trpc.group/trpc-go/trpc-agent-go/runner"
    "trpc.group/trpc-go/trpc-agent-go/tool"
    "trpc.group/trpc-go/trpc-agent-go/tool/function"
)

type weatherReq struct {
    City string `json:"city" jsonschema:"description=The city to look up,required"`
}

type weatherRsp struct {
    Report string `json:"report"`
}

func getWeather(ctx context.Context, req weatherReq) (weatherRsp, error) {
    return weatherRsp{Report: fmt.Sprintf("Sunny, 24C in %s", req.City)}, nil
}

m, err := gemini.New(ctx, "gemini-3.8-flash") // reads GEMINI_API_KEY / GOOGLE_API_KEY

weather := function.NewFunctionTool(getWeather,
    function.WithName("get_weather"),
    function.WithDescription("Returns the current weather for a city."))

advisor := llmagent.New("travel_advisor",
    llmagent.WithModel(m),
    llmagent.WithInstruction("You are a helpful travel advisor. Use tools to give accurate advice. Be brief."),
    llmagent.WithTools([]tool.Tool{weather}))

r := runner.NewRunner("travel-app", advisor)
events, err := r.Run(ctx, "user-1", "session-1",
    model.NewUserMessage("Should I pack a jacket for my trip to Lisbon?"))
for evt := range events {
    if evt.Error != nil {
        log.Fatalf("%s", evt.Error.Message)
    }
    if evt.Response == nil || len(evt.Response.Choices) == 0 {
        continue
    }
    if evt.IsFinalResponse() {
        fmt.Println(evt.Response.Choices[0].Message.Content)
    }
}
```

```
It is currently sunny and warm in Lisbon at 24°C (75°F), so you will not need a heavy coat. However, packing a light jacket or sweater is recommended for cooler, breezy evenings near the coast.
```

Events arrive on a channel and use OpenAI's response shape (`Choices[0].Message` or `Choices[0].Delta` when streaming), which is familiar but means digging through nested structs for every message.

#### Chains

The chain agent is ADK's sequential agent under another name, `OutputKey` and `{facts}` included:

```go
import (
    "trpc.group/trpc-go/trpc-agent-go/agent"
    "trpc.group/trpc-go/trpc-agent-go/agent/chainagent"
)

researcher := llmagent.New("researcher",
    llmagent.WithModel(m),
    llmagent.WithInstruction("List three key facts about the user's topic. Be terse."),
    llmagent.WithOutputKey("facts"))
writer := llmagent.New("writer",
    llmagent.WithModel(m),
    llmagent.WithInstruction("Write a two-sentence brief using these facts:\n{facts}"))

pipeline := chainagent.New("content_pipeline",
    chainagent.WithSubAgents([]agent.Agent{researcher, writer}))
```

```
[researcher] 1. Developed at Google by Robert Griesemer, Rob Pike, and Ken Thompson; released in 2009.
2. Statically typed, compiled language featuring automatic garbage collection.
3. Native concurrency support using lightweight threads called goroutines and channels.

[writer] Developed at Google by Robert Griesemer, Rob Pike, and Ken Thompson and released in 2009, Go is a statically typed, compiled language featuring automatic garbage collection. It is designed with native concurrency support, utilizing channels and lightweight threads called goroutines.
```

#### GraphAgent: LangGraph in Go

A state graph with a routing node, a conditional edge, and two LLM nodes. Short questions go to the quick node, long ones to the deep node.

```go
import (
    "trpc.group/trpc-go/trpc-agent-go/agent/graphagent"
    "trpc.group/trpc-go/trpc-agent-go/graph"
)

sg := graph.NewStateGraph(graph.MessagesStateSchema())
sg.AddNode("route", func(ctx context.Context, state graph.State) (any, error) {
    return nil, nil // pure routing node, no state change
})
sg.AddLLMNode("quick", m, "Answer in one short sentence.", nil)
sg.AddLLMNode("deep", m, "Answer thoroughly. Follow the length the user asks for.", nil)

sg.SetEntryPoint("route")
sg.AddConditionalEdges("route",
    func(ctx context.Context, state graph.State) (string, error) {
        input, _ := state[graph.StateKeyUserInput].(string)
        if len(strings.Fields(input)) > 8 {
            return "deep", nil
        }
        return "quick", nil
    },
    map[string]string{"quick": "quick", "deep": "deep"})
sg.SetFinishPoint("quick")
sg.SetFinishPoint("deep")

g, err := sg.Compile()
router, err := graphagent.New("router", g)
r := runner.NewRunner("graph-app", router)
```

Asked "What is Go?" and then a request for two paragraphs on goroutines and channels:

```
Go is an ancient strategy board game, as well as an open-source programming language developed by Google.

Unlike operating system threads that require megabytes of memory and expensive kernel-level context switching, goroutines are extremely lightweight user-space constructs that start with just a few kilobytes of stack space. [...]
```

The same graph package gives you checkpoints, interrupts for human input, sub-graphs, map-reduce fan-out, per-node callbacks, and a visualization export. It is the most complete workflow engine of the five, and it is the reason to look at this framework even if you never use its LLM agents.

#### Pros and Cons

| ✅ Pros | ❌ Cons |
|---|---|
| GraphAgent: a real LangGraph for Go | Smallest community of the five (1.8k stars) |
| ADK mental model without the GCP gravity | No Dev UI; observability means OpenTelemetry plus Langfuse |
| AG-UI, A2A, MCP, Agent Skills, evaluation | Huge option surface (`llmagent` alone has dozens) |
| Model failover and hedging built in | OpenAI-shaped event structs are verbose to consume |
| OpenTelemetry traces and metrics first party | Tencent-flavoured corners (Hunyuan, tRPC integration) |
| Runs on Go 1.21+ | Documentation partly Chinese-first |

---

## LangChainGo

### History and Direction

LangChainGo was the first. Travis Cline started it in February 2023, weeks after LangChain Python went viral, and for two years it was the default answer to "how do I call an LLM from Go". It has 9.7k stars, 17 LLM providers, and 15 vector stores, and the LangChain names (`chains`, `prompts`, `agents`, `memory`, `outputparser`) make it instantly readable to anyone coming from Python.

And it has stalled. The last release, v0.1.14, is from October 20, 2025. The last commit to `main` is from January 11, 2026. It is still 0.1.x after three and a half years. There are 243 open issues and 174 open pull requests. The repository is not archived, but nobody is merging.

That would be survivable if the code kept working. It does not:

- **The default model is retired.** `googleai.New(ctx)` with no options targets `gemini-2.0-flash`, and Google turned that model off:

  ```
  default model: gemini-2.0-flash
  err: googleapi: Error 404: This model models/gemini-2.0-flash is no longer available. Please update your code to use models/gemini-3.6-flash for the latest features and improvements.
  ```

- **The Gemini provider sits on a dead SDK.** `llms/googleai` is built on `google/generative-ai-go`, whose support ended on November 30, 2025.
- **Streaming is broken on Gemini.** The chunks arrive, and then the call returns an error, so every caller that checks errors treats the request as failed:

  ```
  One, two, three, four, five.
  err: error in stream mode: invalid character ']' looking for beginning of value
  ```

- **No middleware, retry, fallback, or OpenTelemetry anywhere.** The callback handler is seventeen observe-only methods with no way to change the request. Tools are `Call(ctx, string) (string, error)`: no schema, no typed arguments.

The full teardown, with a capstone app built in both frameworks, is in [LangChainGo vs Genkit Go: Where Genkit Shines](/genkit/2026-09-11-langchaingo-vs-genkit-go/).

### LangChainGo's Position: Legacy

None of this means the basics stopped working. Pin a current model and the classic API still runs:

```go
import (
    "github.com/tmc/langchaingo/llms"
    "github.com/tmc/langchaingo/llms/googleai"
)

llm, err := googleai.New(ctx, googleai.WithDefaultModel("gemini-3.8-flash"))

out, err := llms.GenerateFromSinglePrompt(ctx, llm,
    "Explain the CAP theorem in two sentences.")
```

```
The CAP theorem states that a distributed data store can simultaneously provide at most two of three guarantees: Consistency, Availability, and Partition tolerance.

Because network partitions are inevitable in real-world systems, architects must fundamentally choose between serving the most up-to-date data (Consistency) or keeping the system operational (Availability) when a network failure occurs.
```

```go
import (
    "github.com/tmc/langchaingo/chains"
    "github.com/tmc/langchaingo/prompts"
)

prompt := prompts.NewPromptTemplate(
    "Translate {{.text}} to {{.language}}. Reply with the translation only.",
    []string{"text", "language"})
chain := chains.NewLLMChain(llm, prompt)

out, err := chains.Predict(ctx, chain, map[string]any{
    "text": "Buenos días", "language": "English",
})
```

```
Good morning
```

Tools are strings in, strings out. The agent is a ReAct loop driven by prompt text:

```go
import (
    "github.com/tmc/langchaingo/agents"
    "github.com/tmc/langchaingo/tools"
)

type WeatherTool struct{}

func (WeatherTool) Name() string        { return "get_weather" }
func (WeatherTool) Description() string { return "Returns the current weather. Input: a city name." }
func (WeatherTool) Call(ctx context.Context, city string) (string, error) {
    return fmt.Sprintf("Sunny, 24C in %s", city), nil
}

agent := agents.NewOneShotAgent(llm, []tools.Tool{WeatherTool{}}, agents.WithMaxIterations(3))
out, err := chains.Run(ctx, agents.NewExecutor(agent), "What's the weather like in Tokyo?")
```

```
The weather in Tokyo is currently sunny with a temperature of 24°C.
```

If you are on LangChainGo today, the move is not urgent, but it is inevitable: pin your models, avoid streaming on Gemini, and plan the migration. The concept-by-concept guide is in [Migrating from LangChainGo to Genkit Go](/genkit/2026-09-11-langchaingo-to-genkit-go-migration/).

#### Pros and Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Largest catalog: 17 providers, 15 vector stores | Unmaintained since January 2026, still 0.1.x |
| LangChain vocabulary, easy for Python teams | Gemini provider on a retired SDK; streaming broken |
| Conversation memory is ergonomic | No middleware, retry, fallback, or OpenTelemetry |
| Runs on Go 1.24+ | Tools are untyped strings |
| Many existing tutorials and examples | Every vector store needs an external service |

---

## Head-to-Head Comparison

### Developer Experience

| Framework | DX Highlights | Shortcomings |
|---|---|---|
| **Genkit Go** | Dev UI with trace explorer. Typed output from structs. Flows are one line from HTTP. | Agents still experimental; Node.js for the CLI |
| **Eino** | Typed graphs, automatic streaming, callbacks everywhere. | Verbose config structs; 0.x churn |
| **ADK Go** | Iterator-based event loop, generic tools, embedded web UI. | Agent-only; Go 1.26.6 |
| **tRPC-Agent-Go** | GraphAgent, ADK mental model, resilience built in. | OpenAI-shaped events; option overload |
| **LangChainGo** | Familiar names, biggest catalog. | Unmaintained; broken Gemini streaming |

### Abstraction Levels

Genkit Go is the only framework here with all three levels in one SDK: **vanilla generation**, **typed flows**, and **agents**. Eino covers generation and orchestration, plus agents through its ADK module. ADK Go and tRPC-Agent-Go are agent frameworks: every call goes through an agent and a runner. LangChainGo has chains and agents, but no typed pipeline and no session-aware agent.

### Observability

| Framework | Local Dev | Production |
|---|---|---|
| **Genkit Go** | Dev UI with trace explorer | OpenTelemetry export, Google Cloud plugin, any OTEL collector |
| **Eino** | Eino Dev plugin for GoLand and VS Code (graph rendering, node debugging) | Callback handlers: Langfuse, LangSmith, CozeLoop, APMPlus |
| **ADK Go** | Embedded ADK Web UI | OpenTelemetry to Google Cloud (`-otel_to_cloud`) |
| **tRPC-Agent-Go** | Events on a channel, no UI | OpenTelemetry traces and metrics, Langfuse |
| **LangChainGo** | Logging callbacks only | Nothing built in |

### Provider Support

| Framework | Model Providers | Vector Stores |
|---|---|---|
| **Genkit Go** | Gemini (Google AI, Vertex AI), Anthropic, Ollama, OpenAI-compatible family (OpenAI, xAI, DeepSeek, OpenRouter, Kimi, DashScope, Z.ai) | localvec, pgvector, AlloyDB, Pinecone, Weaviate, Firestore |
| **Eino** | OpenAI, Claude, Gemini, DeepSeek, Qwen, Ollama, OpenRouter, Ark, Qianfan | Elasticsearch, Milvus, Qdrant, Redis, OpenSearch, Dify, VikingDB |
| **ADK Go** | Gemini, OpenAI-compatible, Apigee | None as components (Vertex AI Search via tools) |
| **tRPC-Agent-Go** | OpenAI-compatible, Anthropic, Gemini, Bedrock, Ollama, Hugging Face, Hunyuan | In-memory, SQLite-vec, pgvector, Elasticsearch, Milvus, Qdrant, TcVector |
| **LangChainGo** | 17, including OpenAI, Anthropic, Google AI, Vertex, Bedrock, Cohere, Mistral, Ollama | 15, all external services |

### How Go Does It Feel?

| Framework | Min Go | Tools | Streaming | Style |
|---|---|---|---|---|
| **Genkit Go** | 1.25 | Generic, schema from struct | Callback per chunk | Functional options (`ai.With...`) |
| **Eino** | 1.18 | Generic (`utils.InferTool`) | `StreamReader`, automatic across nodes | Config structs plus builder chains |
| **ADK Go** | 1.26.6 | Generic (`functiontool.New`) | `iter.Seq2` over events | Config structs |
| **tRPC-Agent-Go** | 1.21 | Generic plus `jsonschema` tags | Channel of events | Functional options |
| **LangChainGo** | 1.24 | Untyped strings | Callback per chunk (fails on Gemini) | Interfaces plus option funcs |

Only ADK Go uses range-over-func iterators for its event loop. Genkit and Eino use generics the most naturally; LangChainGo predates all of it and shows its age.

### Maintenance Snapshot

Numbers as of September 21, 2026:

| Framework | Stars | Latest Release | Last Commit | Commits, Last 30 Days |
|---|---|---|---|---|
| **Genkit Go** | 6.4k (monorepo) | go/v1.13.1, Sep 3, 2026 | Sep 21, 2026 | 80 (all SDKs) |
| **Eino** | 13.1k | v0.9.20, Sep 20, 2026 | Sep 20, 2026 | 7 on `main`, plus five v0.10 alphas |
| **ADK Go** | 8.8k | v2.4.0, Sep 11, 2026 | Sep 21, 2026 | 100+ |
| **tRPC-Agent-Go** | 1.8k | v1.11.2, Aug 20, 2026 | Sep 21, 2026 | 56 |
| **LangChainGo** | 9.7k | v0.1.14, Oct 20, 2025 | Jan 11, 2026 | 0 |

Stars measure the past. The last two columns measure the present, and they tell the story.

---

## Which Framework Should You Choose?

**Choose Genkit Go if:**
- You want to iterate on your AI fast and get feedback with less back and forth. The Dev UI is the best local development loop in Go, by a distance.
- You need vanilla calls, typed flows, and agents in the same service.
- Provider neutrality matters: mixing Gemini, Claude, OpenAI, and Ollama should be a one-line change.
- Your team also writes TypeScript, Dart, or Java and wants one framework story.

**Choose Eino if:**
- Your application is a real graph: branches, parallel fan-out, sub-graphs, and streaming across all of it.
- You want the most active independent community in Go and are fine living on 0.x.
- Callback-based instrumentation into Langfuse, LangSmith, or your own APM is what you already do.
- You need ByteDance-scale orchestration patterns, or you run on Volcano Engine.

**Choose Google ADK Go if:**
- You are building multi-agent systems and Google Cloud is your runtime.
- You want official Google support, the embedded ADK Web UI, and A2A interoperability.
- Your organization already uses ADK in Python or Java and wants Go services with the same shape.
- The newest Go toolchain is not a problem for you.

**Choose tRPC-Agent-Go if:**
- You want LangGraph-style state graphs with checkpoints and interrupts, in Go, plugged into agents.
- You like the ADK mental model but do not want the GCP gravity.
- AG-UI frontends, Agent Skills, evaluation, and OpenTelemetry out of the box matter more than a Dev UI.
- You can live with a smaller community and a large API surface.

**Stay on LangChainGo only if:**
- You already run it in production, your models are pinned, and you do not stream through Gemini.
- Even then, plan the migration. Nothing is being merged.

---

## Conclusion

Go's Gen AI framework landscape in 2026 is richer than most Go developers realise, and it has a clear shape. **Genkit Go** is the most versatile choice and the best developer experience, with the Dev UI as a category of its own. **Eino** is the ambitious independent, the framework to pick when orchestration is the hard part of your problem. **Google ADK Go** is the enterprise agent runtime, at its best on Google Cloud. **tRPC-Agent-Go** is the dark horse, with the best workflow engine of the five hiding behind a modest star count. And **LangChainGo** is the framework that got everyone started and now needs a farewell plan.

If I had to pick one for a new Go service today with no cloud commitment, it would be Genkit Go, for the same reason as in TypeScript and Java: the combination of multiple abstraction levels, provider neutrality, and local observability shortens the loop between an idea and a working feature more than anything else on this list.

Whatever you pick, pick it deliberately. Go finally has the tooling. Use it.

---

*Last updated: September 2026. Framework versions referenced: Genkit Go v1.13.1, Eino v0.9.20 (with eino-ext gemini v0.1.36), Google ADK Go v2.4.0, tRPC-Agent-Go v1.11.2, LangChainGo v0.1.14. Go 1.27.1, model gemini-3.8-flash.*
