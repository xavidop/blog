---
layout: post
title: "Building Agents in Go: Where Genkit Shines vs ADK 2.0 (English)"
description: >
  A companion to my Genkit Go vs ADK Go 2.0 comparison, this time only about agents. I built a fire-and-forget research team in 90 lines of Genkit: an orchestrator with two sub-agents, artifacts, cross-vendor model fallback and human approval, then tried to build the same thing in ADK. Middleware and the plugin ecosystem are what make the difference, and every program in this article ran.
image: /assets/img/blog/post-headers/building-agents-genkit-vs-adk-go.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - adk
  - golang
  - agents
keywords:
  - genkit
  - genkit-go
  - adk
  - adk-go
  - agents
  - middleware
  - plugins
  - golang
  - sessions
  - human-in-the-loop
  - interrupts
  - snapshots
  - fallback
  - generative-ai
  - comparison

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

In my [previous comparison of Genkit Go and ADK Go 2.0](/genkit/2026-08-05-genkit-go-vs-adk-go/) I covered the everyday tasks. This article is about the agent layer, and instead of comparing features one by one, I did what you would actually do at work: **I built something complex in one framework and then tried to build the same thing in the other.**

Same rules as always: every program here compiled and ran. **Genkit Go v1.11.0** and **ADK Go v2.1.0**, `gemini-3-flash-preview` plus `gpt-5-mini`, 2026-08-05. Where I cite internals, they come from the released module sources.

One caveat upfront so it frames everything: Genkit's agents API sits behind `genkit.WithExperimental()` and can change between minor releases, while ADK's agent stack is GA. That is a real ADK advantage. Everything else in this article is about what you can build.

## The build: a research team you can fire and forget

Here is the spec. It is deliberately the kind of thing a real product asks for:

1. An **orchestrator** agent that coordinates a **researcher** and a **writer**.
2. The sub-agents save their work as **files** (findings.md, draft.md) that end up in one place.
3. The system **survives a model outage**: if the orchestrator's primary model fails, it falls back to a different vendor.
4. Dangerous tools need **human approval** before they run.
5. The client **fires the task and disconnects**; the result waits server-side.

In Genkit this is **one program of 90 lines**, and it ran on the first try. The interesting part is that requirements 1, 2 and 3 are not code at all. They are three entries in a middleware list:

```go
orchestrator := genkitx.DefineAgent(g, "orchestrator",
    aix.InlinePrompt{
        // The primary model is BROKEN on purpose.
        ai.WithModelName("googleai/gemini-nonexistent-model"),
        ai.WithSystem("You coordinate a team. First delegate research to the researcher, then delegate a short draft to the writer. Finally reply with a one-sentence status."),
        ai.WithUse(
            &middleware.Fallback{Models: []ai.ModelRef{
                ai.NewModelRef("openai/gpt-5-mini", nil),      // req 3: cross-vendor healing
            }},
            &middlewarex.Agents{                                // req 1: the team
                Agents:           []aix.AgentRef{researcher.Ref(), writer.Ref()},
                MaxDelegations:   4,
                ArtifactStrategy: middlewarex.ArtifactStrategySession,
            },
            &middlewarex.Artifacts{Readonly: true},             // req 2: read the team's files
        ),
    },
    aix.WithSessionStore(localstore.NewInMemorySessionStore[any]()),
)
```

The researcher and writer are each ~8 lines: an `InlinePrompt` with a Gemini model, a system prompt, and `&middlewarex.Artifacts{}` so they get `write_artifact` tools. Requirement 5 is the client side:

```go
conn.Send(&aix.AgentInput{
    Message: ai.NewUserTextMessage("Research why Go suits AI agents, then have the writer produce a short draft."),
    Detach:  true,
})
out, _ := conn.Output() // returns immediately
// later, from anywhere:
snap, _ := orchestrator.GetSnapshot(ctx, out.SnapshotID)
```

And the run, verbatim:

```
detached after 1ms, snapshot fc70253d-55f8-4890-a587-a6aa74d69438
settled: completed after 58s
artifact "researcher_1/findings.md" (5041 chars) from researcher
artifact "writer_2/draft.md" (3840 chars) from writer
orchestrator: I delegated the research task to the researcher (findings.md saved)
and the short draft to the writer (draft.md saved). Status: research and draft
are complete and saved as researcher_1/findings.md and writer_2/draft.md.
```

Read that output again, because a lot happened in those 58 seconds while no client was connected: the orchestrator's broken Gemini model failed on **every turn** and healed onto OpenAI every time, it delegated to two Gemini-powered sub-agents through auto-generated `delegate_to_*` tools, their artifacts were merged into the orchestrator's session with `source` metadata, and the whole thing settled into a snapshot I could read later from another process. A multi-vendor agent team, running unattended, in 90 lines.

## Why this is easy: middleware composes with agents

The capstone works because of one architectural decision: in Genkit, a middleware is a unit that can **inject tools, wrap the model call, and wrap tool execution**, and the same unit plugs into a plain `Generate` call or an agent's prompt with the same `ai.WithUse(...)` line. Capabilities become list entries.

The shelf in v1.11.0's `plugins/middleware`: `Retry`, `Fallback`, `ToolApproval`, `Filesystem` (sandboxed file tools), `Skills`, plus the experimental `Agents` (delegation) and `Artifacts`. Two of them deserve their own demos, both of which I ran.

### Cross-vendor fallback is configuration

The plugin ecosystem and the middleware system meet here. Any model from any plugin can be a fallback target for any other, so surviving a vendor outage is this, and nothing else:

```go
g := genkit.Init(ctx, genkit.WithPlugins(
    &googlegenai.GoogleAI{},
    &openai.OpenAI{},
))

text, err := genkit.GenerateText(ctx, g,
    ai.WithModelName("googleai/gemini-nonexistent-model"), // broken
    ai.WithPrompt("Say hi in three words."),
    ai.WithUse(
        &middleware.Retry{MaxRetries: 1},
        &middleware.Fallback{Models: []ai.ModelRef{
            ai.NewModelRef("openai/gpt-5-mini", nil),
        }},
    ),
)
```

My run: without the middleware, `Error 404, Message: models/gemini-nonexistent-model is not found`. With it: `Hello there, friend.` from OpenAI. 37 lines total, and the same two lines work inside an agent, which is exactly how the capstone's orchestrator heals itself.

### Human approval is configuration too

`ToolApproval` wraps tool execution and interrupts any tool not on its allowlist. The tool itself knows nothing about approvals:

```go
resp, _ := genkit.Generate(ctx, g,
    ai.WithPrompt("Delete the files in /tmp/scratch please."),
    ai.WithTools(deleteFiles),
    ai.WithUse(&middleware.ToolApproval{}), // nothing pre-approved
)
// resp.FinishReason == "interrupted"

part, _ := deleteFiles.RestartWith(p,
    ai.WithResumedMetadata[DeleteInput](map[string]any{"toolApproved": true}))
final, _ := genkit.Generate(ctx, g,
    ai.WithMessages(resp.History()...), ai.WithToolRestarts(part), /* ... */)
```

My run: `finish reason: interrupted`, then after approval, `OK. I've deleted the files in /tmp/scratch.` Governance became a deployment decision: you can add approval to an existing agent without touching a single tool.

## The same build in ADK 2.0, piece by piece

Now the other side, requirement by requirement, with everything verified against the v2.1.0 sources or actually built.

**The team (req 1): ADK has this, GA.** `SubAgents` with the auto-injected `transfer_to_agent` tool, or `agenttool` for function-call delegation. No complaints; this is ADK's home turf.

**Approval (req 4): ADK has this too, GA, and the declaration is even simpler.** `functiontool.Config{RequireConfirmation: true}` is one flag. I ran the full round-trip in both frameworks and they land within one line of each other (102 vs 101 lines). The difference is the shape: ADK's wire flow is a synthetic `adk_request_confirmation` function call answered with a `map[string]any{"confirmed": true}` payload, while Genkit types the pause payload and the resume payload as Go structs and validates every resume against history. Pick your poison: a flag with an untyped protocol, or a typed protocol you wire yourself.

**Artifacts (req 2): partial.** ADK has an artifact *service* (in-memory or GCS) and a `loadartifactstool`. What it does not have is the merging story: sub-agent artifacts flowing into the parent session with source attribution is what `ArtifactStrategySession` gave me for free.

**Cross-vendor fallback (req 3): you build it yourself, and it bites.** ADK has no middleware and its callbacks cannot wrap the model call, so the seam is writing a custom `model.LLM` decorator. I built it: buffer the primary's output, and on failure call the backup. There is a trap here, and my first version hit it. The backup vendor rejected the call with:

```
"The requested model 'gemini-nonexistent-model' does not exist."
```

ADK's `LLMRequest` carries the model **name inside the request**, so my OpenAI backup was asked to run the Gemini model. The decorator also has to rewrite the request:

```go
backupReq := *req
backupReq.Model = f.backup.Name()
```

After that fix it worked (`Hi there, friend.`). Final tally: **86 lines of decorator and ceremony versus two lines of configuration**, and the 86-line version is per-agent, static, one-level-deep, and has to handle mid-stream failure buffering itself. This is what "no middleware" costs in practice.

**Fire and forget (req 5): not possible.** The v2.1.0 source is unambiguous. `Runner.Run` is a pull-based iterator: nothing executes unless the client consumes events, breaking the loop unwinds the stack, cancelling the context aborts the work, and the REST server passes the request context straight into the run. There is no `context.WithoutCancel` anywhere in the runner or agent paths. ADK *can* park at an interrupt and survive a process restart by replaying the session event log, which is genuinely robust, but pausing at a boundary is not continuing to work after the client leaves.

So the capstone scorecard: two requirements ADK meets as well or better (team, approval flag), one it meets partially (artifacts), one it makes you hand-build with sharp edges (fallback), and one it cannot do (detach). And each of the pieces it does have arrives through a different mechanism: a config field here, a toolset there, a plugin bundle, a hand-written decorator. Genkit's version is one composition model for all of them.

## The pieces in detail

The capstone leaned on agent features that deserve their own numbers. All of these ran, in both frameworks where both have them.

### Typed session state

A Genkit agent's state is a Go struct. A tool mutates it, every change streams to the client as a JSON-Patch, and the client reads it back typed:

```go
type GameState struct {
    Score int      `json:"score"`
    Moves []string `json:"moves"`
}

// inside a tool
if s := aix.SessionFromContext[GameState](ctx); s != nil {
    s.UpdateCustom(func(st GameState) GameState {
        st.Score += in.Points
        st.Moves = append(st.Moves, in.Move)
        return st
    })
}
```

My run streamed `[{"op":"replace","path":"","value":{"moves":["e4"],"score":10}}]` and `conn.Custom()` returned `score=20 moves=[e4 Nf3]` as a struct. Prompts read the same state with `{{@state.score}}`.

ADK's session state is `Get(string) (any, error)` / `Set(string, any)`: a map, type assertions at every read, no schema. It works (my run: `score=20 (int)`), and instruction strings can template state with `{score}`, but nothing checks anything at compile time. The 2.0 graph engine does have typed parameter binding, but only for workflow function nodes, not for session state in a chat agent.

### Custom agent loops

Both frameworks let you write a fully custom agent. In ADK you cannot implement the `agent.Agent` interface directly, since it is sealed and the compiler rejects any attempt with `missing method internal`; the sanctioned path is `agent.New(agent.Config{Run: ...})`, a full execution override, and it ran in my tests.

The difference is what you write. Genkit's `SessionRunner` hands you a turn loop with history, per-turn tracing, snapshot writes and panic recovery built in; my draft-then-self-critique agent is **57 lines**. The ADK version of the same agent is **96 lines**, because a `Run` override means producing raw `session.Event`s: dig the question out of the event log, call the raw model layer, construct and yield events yourself.

### Agents defined in .prompt files

`DefinePromptAgent` binds an agent to a `.prompt` file by name; the model, config and persona are data, not Go:

```go
pirate := genkitx.DefinePromptAgent(g, "pirate",
    aix.WithSessionStore[any](localstore.NewInMemorySessionStore[any]()),
)
```

26 lines of Go, and my run answered: `Rewrite 'em in Python only if ye want yer agents movin' as slow as a barnacle-covered scow in a dead calm.` Non-engineers edit the persona without touching code, and the same dotprompt format works across Genkit's other language SDKs. ADK's equivalent is an `Instruction` string or an `InstructionProvider` where you load files yourself; its YAML agent-config system exists but lives in an `internal/` package only ADK's own CLI can reach.

## Where ADK's agent stack is ahead

The list I would actually weigh on the other side, verified in the same source dive:

- **GA stability**, against everything above being on Genkit's experimental track.
- **The graph engine as the runtime**: every ADK agent runs as a node in the workflow engine, and the node kit (typed function nodes, routing, per-node schema validation, retries, nested graphs) is public API.
- **Schema-validated human input in workflows**: a graph node can declare a JSON schema for the human's answer, validated on resume. For form-like HITL inside a pipeline, that is ahead of anything Genkit ships.
- **Task isolation**: `ModeTask` sub-agents get their own conversation scope with an auto-injected `finish_task` tool and scope-filtered history.
- **Live audio**: `RunLive` with modalities, speech config and transcription has no Genkit Go equivalent.

## The scorecard

Non-blank lines including imports. Every program ran.

| Experiment | Genkit Go | ADK Go 2.0 |
|---|---|---|
| The capstone: team + artifacts + fallback + detach | 90 | not buildable (fallback DIY, detach impossible) |
| Cross-vendor fallback | 37 (configuration) | 86 (hand-written decorator, request-rewrite gotcha) |
| Approval on an existing tool | 45 (middleware config) | flag exists (GA), untyped wire protocol |
| Typed state, 2 turns, live patches | 80, typed | 96, map + casts |
| Custom draft-critique agent | 57 | 96 |
| Agent from a .prompt file | 26 | no equivalent |
| Undo the last exchange | 41 | no API: append-only event log |
| Context caching | 40, one method call | lifecycle DIY with a raw genai client |

## Conclusion

The agent layer is where Genkit's two architectural bets pay off together. The plugin ecosystem means models from different vendors, local runtimes and vector stores are interchangeable references. The middleware system means capabilities (delegation, artifacts, fallback, retries, approval, sandboxed files, skills) are composable list entries that work identically in a one-shot generate and inside an agent. Stack those two on top of typed sessions, snapshots and detach, and a fire-and-forget multi-vendor agent team is a 90-line program. I know because I ran it, and I also know what the same spec costs in ADK because I built the pieces: one requirement hand-written with real sharp edges, and one that cannot be built at all.

ADK's agent stack remains the right pick when its strengths are your requirements: GA guarantees, graph workflows with schema validation, task isolation, live audio, and the Google Cloud platform around it. But if the question is "how hard is it to build something complex", the answer I measured is: in Genkit, complexity composes; in ADK, each capability is its own project.

Further reading:

- [Genkit Go vs ADK Go 2.0: a Hands-On Look at Boilerplate and Low-Level Control](/genkit/2026-08-05-genkit-go-vs-adk-go/)
- [Genkit Go basic-agents sample](https://github.com/genkit-ai/genkit/tree/main/go/samples/basic-agents)
- [Genkit middleware documentation](https://genkit.dev/docs/js/middleware/)
- [ADK 2.0 release notes](https://adk.dev/2.0/)
- [Genkit GitHub repository](https://github.com/genkit-ai/genkit)
- [ADK Go GitHub repository](https://github.com/google/adk-go)
