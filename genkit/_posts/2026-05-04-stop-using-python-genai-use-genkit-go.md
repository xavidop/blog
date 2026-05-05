---
layout: post
title: Stop Using Python for Your Gen AI Apps, Use Go and Genkit Instead (English)
description: >
  Python has dominated the Gen AI conversation, but it is not the only, nor the best, option for production. Here is why Go (and Genkit Go in particular) is a stronger bet for serious AI services in 2026.
image: /assets/img/blog/post-headers/genkit-go-getting-started.png
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - gcp
  - go
keywords:
  - firebase
  - go
  - golang
  - genkit
  - generative-ai
  - googlecloud
  - gcp
  - google-cloud-platform
  - google-cloud
  - python

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

For the last few years, every Gen AI tutorial, framework, and "hello world" has assumed one thing: that you are writing Python. It made sense at the start. The research community lives in Python, the model providers ship Python SDKs first, and the notebook culture is hard to beat for prototyping. But there is a quiet, important shift happening in 2026: the teams actually shipping AI features at scale are increasingly moving their **production** Gen AI workloads off Python, and onto languages built for services.

Go is at the center of that shift. And **[Genkit Go](https://genkit.dev/docs/go/get-started/)**, the Go flavor of Google's open-source Gen AI framework, is the cleanest path I have seen to build production-ready AI services in Go: typed flows, structured output, built-in HTTP serving, observability, and a Developer UI, all from a single binary.

This article is two things at once. First, an honest argument about why Python is a poor fit for production Gen AI services. Second, a hands-on getting-started with Genkit Go so you can replace that Python microservice this week.

## Why Python Hurts in Production Gen AI

Python is great for research and prototyping. But Gen AI applications are not really "AI code", they are mostly **I/O-heavy network services** that happen to call a model. And that is exactly where Python struggles.

### Concurrency is a constant fight

Gen AI workloads are dominated by long, concurrent network calls: streaming completions, tool calls, embedding requests, vector DB lookups, MCP servers. Go's goroutines and channels were literally designed for this. In Python you have a choice between three uncomfortable options: threads (limited by the GIL), `asyncio` (which infects your entire codebase and breaks the moment one library is sync), or multiprocessing (heavy, awkward, and unfriendly to shared state). None of them feel native. All of them leak through your abstractions.

### Cold starts and memory footprint

A Python AI service typically pulls in `pydantic`, `httpx`, an SDK or two, and a tokenizer. You are easily looking at 200, 400 MB of resident memory and several seconds of cold start before you serve a single request. A Go binary doing the same job is one statically linked file, tens of MB of RAM, and starts in milliseconds. On Cloud Run, Lambda, Azure Functions, or any autoscaling platform, this difference is not a micro-optimization, it is the difference between a service that scales to zero gracefully and one that does not.

### Dependency hell is worse for AI

`pip`, `poetry`, `uv`, `conda`, `venv`, `requirements.txt`, `pyproject.toml`. Pin a Torch version, break a transitive dep. Upgrade an SDK, break Pydantic v1 vs v2. Every Python AI repo I have inherited has spent at least a day fixing the environment before running a single prompt. Go's module system, with a single `go.mod` and `go.sum`, is boring, reproducible, and just works.

### Types are optional, and it shows

Structured output, tool calling, and MCP all rely on **schemas**. In Python, the schema lives in Pydantic models, in docstrings, in comments, and sometimes in your head. In Go, the schema **is** the struct. The compiler enforces it. Genkit picks it up automatically via JSON schema tags. You cannot ship a flow whose input does not match what the model returns, because it will not compile.

### Deployment is a packaging exercise

Python deployments are Dockerfiles full of system packages, base images that drift, and "works on my machine" surprises. Go deploys as a single static binary. `FROM scratch`, copy the binary, done. For AI services that need to run on Cloud Run, on Kubernetes, on the edge, or as a sidecar, that is a massive operational win.

### The performance ceiling is real

Yes, the heavy lifting happens on the model provider's GPUs. But your service still has to parse tokens off a streaming response, fan out tool calls, merge results, enforce timeouts, and push telemetry, **per request, at concurrency**. Go does that work an order of magnitude more efficiently than CPython, and without you having to think about it.

> None of this means Python is wrong for **research**. It means Python is the wrong default for the **service** that exposes that research to your users.

## Go Is the Best Language for Agentic Coders

There is one more reason to pick Go in 2026 that did not really exist two years ago: **agentic coders**. Tools like Claude Code, Cursor's agent mode, GitHub Copilot's agent, Gemini Code Assist, Codex, Aider, and the growing ecosystem of autonomous coding agents are now a real part of how software gets written. And it turns out that **Go is the language they thrive in**.

Why? It comes down to three properties of the language that align almost perfectly with how an LLM-based agent reasons about code:

### Strong, static typing closes the feedback loop

Agentic coders work in a tight loop: write code, compile, read the error, fix, repeat. Go's compiler is fast, strict, and brutally honest. When an agent generates a wrong call, the compiler tells it exactly what is wrong and where, in seconds. In Python, the same mistake might only surface at runtime, three layers deep, with a stack trace that requires the agent to spend tokens reasoning about dynamic behavior. Strong typing turns "guess and pray" into "verify and continue".

### There is usually one obvious way to do something

Python has at least four HTTP clients, three async paradigms, two type systems, and an opinion war about every major design decision. An agent has to choose, and choices cost tokens and increase the chance of going off the rails. Go is famously opinionated: one formatter (`gofmt`), one module system, one idiomatic way to handle errors, one standard layout. Less surface area means less ambiguity, which means **less token consumption and more correct code per iteration**.

### Tooling is built for machines, not just humans

`go build`, `go test`, `go vet`, `gopls`, and `staticcheck` produce structured, parseable output. Agents can read it directly without heuristics. Combine that with `go doc` and the standard library being uniformly documented, and you give an agent a self-describing environment it can navigate without hallucinating.

### And then Genkit Go takes it one level further

Genkit Go leans into the same properties:

- Flow inputs and outputs are **Go structs**, the schema is the type. An agent generating a new flow knows exactly what shape the data has, because the compiler will reject anything else.
- The API surface is small and consistent: `genkit.Init`, `genkit.DefineFlow`, `genkit.DefineTool`, `genkit.GenerateData`, `genkit.Handler`. There is one obvious way to define a flow, one obvious way to expose it, one obvious way to call a model.
- Tool definitions are typed end-to-end, so an agent writing a new tool gets compile-time guarantees that its signature matches what the runtime expects.

The net effect is that an agentic coder pointed at a Genkit Go codebase will produce **more correct code, in fewer iterations, with fewer tokens** than the same agent pointed at an equivalent Python codebase. In a world where you are increasingly going to be the reviewer of agent-generated code rather than the author, that compounds fast.

## Why Genkit Go Specifically

If you accept the premise that Go is the better runtime for Gen AI services, the next question is: which framework? You can absolutely call the Gemini, OpenAI, or Anthropic SDKs directly from Go. But you will quickly end up rebuilding the same primitives every Genkit user already has for free.

Here is what Genkit Go gives you out of the box, and what you would otherwise have to write yourself:

| Feature | Without Genkit | With Genkit Go |
||||
| Call a model | Hand-rolled HTTP client per provider, manual JSON, manual streaming | `genkit.Generate(...)`, one call, multi-provider |
| Structured output | Parse raw JSON, custom unmarshaling, validate by hand | `genkit.GenerateData[MyStruct]`, typed Go struct returned |
| Expose as an API | `net/http` boilerplate per endpoint, request/response wiring | `genkit.Handler(flow)`, auto HTTP endpoint |
| Tool calling | Parse function call payloads, dispatch, re-submit | `genkit.DefineTool(...)`, automatic execution loop |
| Observability | Wire OpenTelemetry, define spans, ship metrics | Built-in tracing, metrics, latency, zero config |
| Local dev | `curl`, Postman, manual harnesses | **Genkit Developer UI**, visual flow runner, traces, prompt playground |
| Multi-provider | Different SDKs, different auth, different schemas | Unified plugin interface (Google AI, Vertex, OpenAI, Anthropic, Bedrock, Azure, Ollama, ...) |

It is the same philosophy as [Genkit Java]({% post_url genkit/2026-02-10-genkit-java-101 %}) and the JavaScript flavor I covered in [my 2026 JS/TS Gen AI frameworks comparison]({% post_url genkit/2026-04-16-top-jsts-genai-frameworks-2026 %}): a thin, opinionated, cloud-agnostic layer that turns "AI logic" into a **typed function** you can call, test, deploy, and observe.

## What We Are Going to Build

A Go service exposing a single AI flow that generates a structured **recipe** from a main ingredient and optional dietary restrictions. It will:

- Accept a typed `RecipeInput` as input.
- Call **Gemini 3 Pro** via the Google AI plugin.
- Return a strongly-typed `Recipe` struct (no manual JSON parsing).
- Be served as an HTTP endpoint on `:3400`.
- Be testable visually in the **Genkit Developer UI**.

All in **a single `main.go` file**. No web framework. No code generation. Just Go.

## Prerequisites

- **Go 1.24+** ([install](https://go.dev/doc/install))
- **Node.js 18+** (only required for the Genkit CLI / Developer UI)
- A **Google GenAI API key** (free, no credit card, from [Google AI Studio](https://aistudio.google.com/apikey))

### Install the Genkit CLI

The Genkit CLI is your local companion for running and inspecting flows in the Developer UI:

```bash
curl -sL cli.genkit.dev | bash
```

Verify it:

```bash
genkit --version
```

## Set Up the Project

Create a fresh module:

```bash
mkdir genkit-go-recipes && cd genkit-go-recipes
go mod init example/genkit-go-recipes
```

Install the Genkit Go package:

```bash
go get github.com/firebase/genkit/go
```

Set your API key:

```bash
export GEMINI_API_KEY=<your API key>
```

## The Code: a Single `main.go`

Create `main.go` with the following content. This is the entire service.

```go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "net/http"

    "github.com/firebase/genkit/go/ai"
    "github.com/firebase/genkit/go/genkit"
    "github.com/firebase/genkit/go/plugins/googlegenai"
    "github.com/firebase/genkit/go/plugins/server"
)

// Input schema, picked up automatically by Genkit and the Dev UI.
type RecipeInput struct {
    Ingredient          string `json:"ingredient" jsonschema:"description=Main ingredient or cuisine type"`
    DietaryRestrictions string `json:"dietaryRestrictions,omitempty" jsonschema:"description=Any dietary restrictions"`
}

// Output schema, returned directly by the model as a typed Go struct.
type Recipe struct {
    Title        string   `json:"title"`
    Description  string   `json:"description"`
    PrepTime     string   `json:"prepTime"`
    CookTime     string   `json:"cookTime"`
    Servings     int      `json:"servings"`
    Ingredients  []string `json:"ingredients"`
    Instructions []string `json:"instructions"`
    Tips         []string `json:"tips,omitempty"`
}

func main() {
    ctx := context.Background()

    // Initialize Genkit with the Google AI plugin and a default model.
    g := genkit.Init(ctx,
        genkit.WithPlugins(&googlegenai.GoogleAI{}),
        genkit.WithDefaultModel("googleai/gemini-3-pro"),
    )

    // Define a typed flow: (RecipeInput) -> (Recipe, error)
    recipeGeneratorFlow := genkit.DefineFlow(g, "recipeGeneratorFlow",
        func(ctx context.Context, input *RecipeInput) (*Recipe, error) {
            dietary := input.DietaryRestrictions
            if dietary == "" {
                dietary = "none"
            }

            prompt := fmt.Sprintf(`Create a recipe with the following requirements:
                Main ingredient: %s
                Dietary restrictions: %s`, input.Ingredient, dietary)

            // Structured generation: Gemini returns a Recipe directly.
            recipe, _, err := genkit.GenerateData[Recipe](ctx, g,
                ai.WithPrompt(prompt),
            )
            if err != nil {
                return nil, fmt.Errorf("failed to generate recipe: %w", err)
            }
            return recipe, nil
        },
    )

    // Smoke-test the flow once at boot.
    recipe, err := recipeGeneratorFlow.Run(ctx, &RecipeInput{
        Ingredient:          "avocado",
        DietaryRestrictions: "vegetarian",
    })
    if err != nil {
        log.Fatalf("could not generate recipe: %v", err)
    }
    out, _ := json.MarshalIndent(recipe, "", "  ")
    fmt.Println("Sample recipe generated:")
    fmt.Println(string(out))

    // Expose the flow as an HTTP endpoint.
    mux := http.NewServeMux()
    mux.HandleFunc("POST /recipeGeneratorFlow", genkit.Handler(recipeGeneratorFlow))

    log.Println("Starting server on http://localhost:3400")
    log.Println("Flow available at: POST http://localhost:3400/recipeGeneratorFlow")
    log.Fatal(server.Start(ctx, "127.0.0.1:3400", mux))
}
```

Take a moment to count what is **not** in this file:

- No web framework.
- No JSON parsing of the model output.
- No manual OpenTelemetry setup.
- No request/response DTO duplication.
- No Dockerfile yet (we will not need much).

The struct **is** the contract. The flow **is** the endpoint. The compiler enforces both.

## Run It

```bash
go run .
```

You should see a structured recipe printed as JSON, then the server logging that it is listening on `:3400`.

In another terminal, hit it with `curl`:

```bash
curl -X POST "http://localhost:3400/recipeGeneratorFlow" \
  -H "Content-Type: application/json" \
  -d '{"data": {"ingredient": "tomato", "dietaryRestrictions": "vegan"}}'
```

You will get back a fully structured JSON recipe. That is it, you have a production-shaped Gen AI microservice in one file.

## Test It Visually with the Developer UI

The Genkit Developer UI is one of the strongest reasons to adopt Genkit, regardless of language. It gives you a local web app to run flows, inspect traces, tweak prompts, and debug tool calls.

From the project root:

```bash
genkit start -- go run .
```

Open [http://localhost:4000](http://localhost:4000), pick `recipeGeneratorFlow`, paste:

```json
{
  "ingredient": "avocado",
  "dietaryRestrictions": "vegetarian"
}
```

Click **Run**. You will see the typed output and a full trace of the model call: tokens, latency, prompt, response. This is the kind of inner loop Python frameworks are still catching up on.

## Deploying It

Because it is Go, deployment is almost anticlimactic. A minimal `Dockerfile`:

```dockerfile
FROM golang:1.24 AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -o /out/server .

FROM gcr.io/distroless/static
COPY --from=build /out/server /server
ENV PORT=3400
EXPOSE 3400
ENTRYPOINT ["/server"]
```

That is your entire production image. Deploy it to **Cloud Run**, **Cloud Run Jobs**, **Kubernetes**, **AWS Lambda** (via container image), **Azure Container Apps**, or any platform that runs containers. No Python runtime to vendor. No `pip install` at build time. No virtual environment. Just a binary.

If you want to see the same pattern applied to other clouds and languages, I have already covered:

- [Genkit + AWS Lambda + Bedrock]({% post_url genkit/2026-03-20-genkit-aws-lambda-bedrock %})
- [Genkit + Azure Functions + AI Foundry]({% post_url genkit/2026-03-20-genkit-azure-function-ai-foundry %})
- [Genkit Java 101]({% post_url genkit/2026-02-10-genkit-java-101 %})

Genkit Go fits the same mold, with the smallest runtime footprint of all of them.

## "But What About..."

A few honest objections worth addressing.

- **"All the cool research libraries are in Python."** True. Keep them in Python, behind a small Python service that does only the research-y bit. Put your **product surface** (the part your users actually call) in Go. That separation is healthy.
- **"My team only knows Python."** Go is famously the easiest "real" backend language to learn. A Python developer can be productive in Go in days, and Genkit's API surface is small enough that the learning curve is mostly Go itself, not the framework.
- **"What about LangChain / LlamaIndex features?"** Most of what those frameworks give you (flows, tools, RAG, prompts, evaluation, observability) Genkit Go gives you too, with a fraction of the surface area and without the abstraction tax. See my [2026 frameworks comparison]({% post_url genkit/2026-04-16-top-jsts-genai-frameworks-2026 %}) for the long version.
- **"Is Genkit Go production-ready?"** It powers Gen AI features at Google and a growing list of companies. The Go SDK shares the same core philosophy and plugin model as the JS and Java SDKs. It is stable enough to bet on, and the iteration speed is high.

## Wrapping Up

Python earned its place as the language of AI **research**. It did not earn its place as the language of AI **services**. Those are different problems with different constraints, and the constraints of production services, concurrency, footprint, deployment, types, observability, all favor Go.

Genkit Go is the framework that finally makes that switch painless. You get a typed, observable, multi-provider Gen AI service in one file, one binary, and one deploy. If you are still maintaining a Python microservice whose only job is to call an LLM and return structured JSON, you are paying a tax you do not need to pay.

Try it on your next flow. Replace one Python service. See how much smaller the resulting system is, in code, in memory, and in operational surface area.

## References

- [Genkit Go, Get Started](https://genkit.dev/docs/go/get-started/)
- [Genkit Go, Flows](https://genkit.dev/docs/go/flows/)
- [Genkit Go, Tool Calling](https://genkit.dev/docs/go/tool-calling/)
- [Genkit Go, Deployment on Cloud Run](https://genkit.dev/docs/go/deployment/cloud-run/)
- [Genkit GitHub](https://github.com/firebase/genkit)
