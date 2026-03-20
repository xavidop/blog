---
layout: post
title: Building a Perplexity-like CLI with Genkit, Gemini, and Tavily (English)
description: >
  An interactive CLI chat tool with AI-powered web search using Genkit agents and tool calling
image: /assets/img/blog/post-headers/genkit-perplexity-cli.png
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [gcp, genkit]
tags:
  - genkit
  - gcp
keywords:
  - genkit
  - gemini
  - tavily
  - generative-ai
  - cli
  - agents
  - tool-calling
  - typescript
  - perplexity

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

What if you could build your own **Perplexity AI**, right in your terminal? In this post, we will walk through an interactive command-line chat tool that searches the web and generates comprehensive AI-powered answers with cited sources, all built with **Genkit**, **Gemini 3 Pro**, and the **Tavily Search API**.

This project showcases some of Genkit's most powerful features: **AI agents**, **tool calling**, **chat sessions with persistent history**, and **prompt definitions**, all wired together in a clean TypeScript codebase.

## Features

- Web search powered by Tavily API
- AI-generated comprehensive answers using Genkit with Gemini 3 Pro
- Interactive chat mode with persistent conversation history
- AI agents with tool-calling capabilities
- Cited sources with URLs
- Beautiful terminal output with colors and spinners

## Prerequisites

- **Node.js 18** or higher
- **TypeScript** (installed as dev dependency)
- **Tavily API key** (get it from [tavily.com](https://tavily.com/))
- **Google AI API key** (get it from [Google AI Studio](https://aistudio.google.com/app/apikey))

## Project Structure

```
perplexity-cli/
├── index.ts             # Main entry point with interactive chat interface
├── src/
│   ├── search.ts        # Tavily search integration
│   └── agent.ts         # Genkit AI agent with tool definitions
├── tsconfig.json        # TypeScript configuration
├── package.json
├── .env                 # Environment variables
└── README.md
```

## How It Works

The architecture follows a clean flow:

1. **Interactive Session**: The CLI starts an interactive chat session with persistent conversation history
2. **Query Processing**: When you ask a question, the AI agent decides if it needs current web information
3. **Tool Calling**: If needed, the AI agent automatically calls the web search tool via Tavily
4. **Search**: Tavily searches the web for relevant, up-to-date information
5. **Generate**: Genkit with Gemini 3 Pro analyzes the search results and conversation context to generate a comprehensive answer
6. **Display**: The answer is displayed in the terminal with proper formatting and source citations

## Initializing Genkit

The main entry point sets up Genkit with the Google AI plugin:

```typescript
import { genkit } from 'genkit/beta';
import { googleAI } from '@genkit-ai/googleai';
import { tavily } from '@tavily/core';

const client = tavily({ apiKey: TavilyApiKey });
const ai = genkit({
  plugins: [googleAI({ apiKey: GeminiApiKey })],
});
```

Notice we are using `genkit/beta` here. This gives us access to the chat API, which is key for maintaining conversation history across multiple interactions.

## Defining a Tool: Web Search

One of Genkit's most powerful features is **tool calling**. You define tools with typed schemas, and the LLM decides when to invoke them. Here is the web search tool:

```typescript
import { z } from 'zod';
import { searchWeb } from './search.js';

export function createSearchTool(ai: GenkitBeta, client: TavilyClient) {
  return ai.defineTool(
    {
      name: 'searchWeb',
      description:
        'Search the web for current information to answer user queries. ' +
        'Use this when you need up-to-date or factual information.',
      inputSchema: z.object({
        query: z.string().describe('The search query to look up'),
      }),
      outputSchema: z.string().describe('Search results with titles, URLs, and content'),
    },
    async (input: { query: string }) => {
      const searchResults = await searchWeb(client, input.query, 5);

      const formattedResults = searchResults.results
        .map((result, index) => {
          return `[${index + 1}] ${result.title}\nURL: ${result.url}\nContent: ${result.content}\n`;
        })
        .join('\n');

      return formattedResults;
    }
  );
}
```

The tool is defined with:
- A **name** and **description** that help the LLM understand when to use it
- A typed **input schema** (what the LLM needs to provide)
- A typed **output schema** (what the tool returns)
- An **implementation** that calls the external Tavily API

Genkit handles the entire tool-calling loop: the LLM decides it needs web results, Genkit invokes the tool, feeds the results back to the LLM, and the LLM generates the final answer.

## Creating the Chat Agent

The chat agent combines the search tool with a prompt definition and Genkit's chat API:

```typescript
export function createChatAgent(
  ai: GenkitBeta,
  client: TavilyClient,
  model: ModelReference<typeof GeminiConfigSchema>
) {
  const searchTool = createSearchTool(ai, client);

  const searchPrompt = ai.definePrompt({
    name: 'searchPrompt',
    description: 'Tool that searches the web to answer user queries.',
    input: {
      schema: z.object({
        query: z.string().describe('The user query to be answered using web search results'),
      }),
    },
    tools: [searchTool],
    prompt: `You are a helpful AI assistant that provides comprehensive and accurate answers based on web search results.

User Query: {{query}}

Instructions:
1. Provide a comprehensive answer based on the search results
2. Synthesize information from multiple sources when relevant
3. Be factual and cite specific sources using [1], [2], etc. notation
4. If the search results don't contain enough information, acknowledge this
5. Keep the answer clear and well-structured
6. Use markdown formatting for better readability
7. Please use the tool searchPrompt always when you need to look up current information
8. Add a section at the end titled "Sources" listing the URLs of the references used

Answer:`,
  });

  return ai.chat(searchPrompt, { model: model });
}
```

Key things to notice:
- **`ai.definePrompt`** creates a reusable prompt with typed input, tools, and instructions
- **`ai.chat`** creates a chat session with **persistent memory**, so follow-up questions have full context from previous interactions
- The prompt instructs the LLM to use the search tool and cite sources

## The Interactive Chat Loop

The main loop is a simple readline interface that sends each query to the chat agent:

```typescript
const chat = createChatAgent(ai, client, googleAI.model('gemini-3-pro-preview'));

rl.on('line', async (line: string) => {
  const query = line.trim();

  let spinner = ora('Thinking...').start();

  const { text } = await chat.send(query);

  spinner.succeed('Response generated');
  console.log(chalk.white('\n' + text + '\n'));
});
```

Each call to `chat.send()` automatically includes the full conversation history. The agent decides whether to search the web or answer from context, and Genkit handles the tool-calling orchestration behind the scenes.

## Genkit Dev UI for Agent Debugging

Even though this is a CLI tool, you can still use the **Genkit Dev UI** to debug and test the agent. The Dev UI is invaluable for:

- **Inspecting tool calls**: See exactly when the agent decides to call the search tool, what query it constructs, and what results come back
- **Viewing traces**: Every interaction generates a detailed trace showing the full chain of LLM calls, tool invocations, and final responses
- **Testing prompts**: Tweak the system prompt and test with different queries without restarting the CLI
- **Monitoring latency**: See how long each step takes, from tool calls to LLM generation

To start the Dev UI alongside your project:

```bash
npx genkit start -- npx tsx index.ts
```

This runs your CLI with the Genkit Dev UI available at `http://localhost:4000`.

## Example Session

```bash
╔════════════════════════════════════════════════════╗
║   Welcome to Perplexity CLI - Interactive Mode     ║
╚════════════════════════════════════════════════════╝
Type your questions and get AI-powered answers with sources!
Chat history is maintained during this session.
Commands: exit, quit, or press Ctrl+C to leave

💬 Ask a question (or type "exit" to quit): What is quantum computing?
✓ Response generated

Quantum computing is a revolutionary approach to computation that leverages
the principles of quantum mechanics. Unlike classical computers that use bits
(0s and 1s), quantum computers use quantum bits or "qubits" that can exist
in multiple states simultaneously...

Sources:
[1] https://example.com/quantum-basics
[2] https://example.com/quantum-intro

💬 Ask a question (or type "exit" to quit): How does it differ from classical computing?
✓ Response generated

[AI continues the conversation with context from previous question]
```

## Setup & Development

1. Clone and install dependencies:
```bash
git clone https://github.com/xavidop/perplexity-cli.git
cd perplexity-cli
npm install
```

2. Create a `.env` file with your API keys:
```bash
TAVILY_API_KEY=your_tavily_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

3. Run in development mode:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
npm start
```

## Resources

- [Genkit Documentation](https://genkit.dev/docs/)
- [Google AI Plugin](https://genkit.dev/docs/plugins/google-genai/)
- [Tavily API](https://tavily.com/)
- [Gemini Models](https://ai.google.dev/)

## Conclusion

This project demonstrates some of Genkit's most exciting capabilities: **AI agents** that autonomously decide when to use tools, **tool calling** with typed schemas, **chat sessions** with persistent history, and **prompt definitions** that keep your AI logic clean and reusable. The Genkit Dev UI ties it all together by giving you full visibility into every decision the agent makes.

You can find the full code of this example in the [GitHub repository](https://github.com/xavidop/perplexity-cli)

Happy coding!
