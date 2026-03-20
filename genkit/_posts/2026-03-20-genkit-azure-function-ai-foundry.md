---
layout: post
title: Running Genkit on Azure Functions with Azure OpenAI (English)
description: >
  Deploy AI-powered flows to Azure Functions using Genkit and the Azure OpenAI plugin
image: /assets/img/blog/post-headers/genkit-azure-function-ai-foundry.png
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - gcp
  - azure
keywords:
  - genkit
  - azure
  - azure-functions
  - azure-openai
  - generative-ai
  - serverless
  - typescript
  - ai-flows

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

Genkit is not tied to any single cloud. In this post, we will explore how to run Genkit flows on **Azure Functions** powered by **Azure OpenAI**, building a story generator, a joke generator with streaming, and a protected summary endpoint with API key authentication, all using the `onCallGenkit` helper from the Azure OpenAI plugin.

This project shows how Genkit brings the same great developer experience, typed flows, structured output, the Dev UI, to the Azure ecosystem.

## Why Genkit on Azure?

Azure has a first-class AI offering through **Azure OpenAI Service** with GPT-4o and other powerful models. The [Azure OpenAI plugin for Genkit](https://github.com/genkit-ai/azure-foundry-js-plugin) brings all of these models into the Genkit ecosystem, giving you:

- Access to **GPT-4o**, **GPT-3.5 Turbo**, and other Azure OpenAI models
- The `onCallGenkit` helper for zero-boilerplate Azure Function handlers
- Built-in API key authentication via `requireApiKey`
- Full compatibility with the **Genkit Dev UI** for local testing
- Streaming support via SSE (Server-Sent Events)

## Prerequisites

- **Node.js 20** or later
- **Azure Account** with an Azure OpenAI resource deployed
- **Azure Functions Core Tools v4**
- **Genkit CLI** installed globally

```bash
npm install -g genkit-cli
```

## Project Structure

```
genkit-azure-function-ai-foundry/
├── src/
│   └── index.ts          # Main Azure Function handler with Genkit flows
├── host.json             # Azure Functions host configuration
├── local.settings.json   # Local config
├── .env                  # Environment variables
├── tsconfig.json         # TypeScript configuration
├── package.json          # Dependencies and scripts
└── README.md
```

## Initializing Genkit with Azure OpenAI

Setting up Genkit with Azure OpenAI is straightforward:

```typescript
import { genkit, z } from 'genkit';
import {
  azureOpenAI,
  gpt4o,
  onCallGenkit,
  requireApiKey,
} from 'genkitx-azure-openai';
import * as dotenv from 'dotenv';

dotenv.config();

const ai = genkit({
  plugins: [
    azureOpenAI({
      // Reads from environment variables:
      // AZURE_OPENAI_ENDPOINT
      // AZURE_OPENAI_API_KEY
      // OPENAI_API_VERSION
    }),
  ],
  model: gpt4o,
});
```

The plugin reads your Azure credentials from environment variables. No manual HTTP clients, no JSON wrangling. Just configure and go.

## Defining Flows

### Story Generator Flow

The story generator uses **structured output**, which means Genkit instructs the LLM to return a typed object matching your Zod schema directly:

```typescript
const StoryInputSchema = z.object({
  topic: z.string().describe('The main topic or theme for the story'),
  style: z.string().optional().describe('Writing style (e.g., adventure, mystery, sci-fi)'),
  length: z.enum(['short', 'medium', 'long']).default('medium'),
});

const StorySchema = z.object({
  title: z.string(),
  genre: z.string(),
  story: z.string(),
  wordCount: z.number(),
  themes: z.array(z.string()),
});

const storyGeneratorFlow = ai.defineFlow(
  {
    name: 'storyGeneratorFlow',
    inputSchema: StoryInputSchema,
    outputSchema: StorySchema,
  },
  async (input) => {
    const lengthMap = { short: '200-300', medium: '500-700', long: '1000-1500' };
    const wordCount = lengthMap[input.length];

    const prompt = `Create a creative ${input.style || 'fictional'} story with the following requirements:
      Topic: ${input.topic}
      Length: ${wordCount} words
      
      Please provide a captivating story with a clear beginning, middle, and end.
      Include rich descriptions and engaging characters.`;

    const { output } = await ai.generate({
      prompt,
      output: { schema: StorySchema },
    });

    if (!output) {
      throw new Error('Failed to generate story');
    }

    return output;
  }
);
```

The response is a fully typed `StorySchema` object. No `JSON.parse`, no manual deserialization.

### Streaming Joke Flow

The streaming flow uses `ai.generateStream` and emits chunks via `sendChunk`:

```typescript
const jokeStreamingFlow = ai.defineFlow(
  {
    name: 'jokeStreamingFlow',
    inputSchema: JokeInputSchema,
    outputSchema: JokeOutputSchema,
    streamSchema: z.string(),
  },
  async (input, { sendChunk }) => {
    const { stream, response } = await ai.generateStream({
      prompt: `Tell me a long and funny joke about ${input.subject}`,
    });

    for await (const chunk of stream) {
      sendChunk(chunk.text);
    }

    const result = await response;
    return { joke: result.text };
  }
);
```

### Protected Summary Flow with API Key Auth

One of the unique features of the Azure OpenAI plugin is the built-in `requireApiKey` context provider. This lets you protect flows with API key authentication without writing any middleware:

```typescript
export const protectedHandler = onCallGenkit(
  {
    contextProvider: requireApiKey(
      'X-API-Key',
      process.env.API_KEY || 'demo-api-key'
    ),
    cors: {
      origin: ['https://myapp.com', 'http://localhost:3000'],
      credentials: true,
    },
    onError: async (error) => ({
      statusCode: error.message.includes('Unauthorized') ? 401 : 500,
      message: error.message,
    }),
  },
  protectedSummaryFlow
);
```

## Registering Flows as Azure Functions

The `onCallGenkit` helper wraps Genkit flows as Azure Function HTTP triggers:

```typescript
// With CORS and debug
export const storyGeneratorHandler = onCallGenkit(
  {
    cors: { origin: '*' },
    debug: process.env.NODE_ENV !== 'production',
  },
  storyGeneratorFlow
);

// Simplest form
export const jokeHandler = onCallGenkit(jokeFlow);

// Streaming with SSE
export const jokeStreamHandler = onCallGenkit(
  { streaming: true, cors: { origin: '*' } },
  jokeStreamingFlow
);
```

This gives you four Azure Function endpoints:

| Flow | Endpoint | Auth | Features |
|------|----------|------|----------|
| storyGeneratorFlow | POST /api/storyGeneratorFlow | anonymous | CORS, debug |
| jokeFlow | POST /api/jokeFlow | anonymous | Simplest form |
| jokeStreamingFlow | POST /api/jokeStreamingFlow | anonymous | SSE streaming |
| protectedSummaryFlow | POST /api/protectedSummaryFlow | API key | Auth, CORS, custom error handler |

## The Genkit Dev UI

Run the following command to start the Genkit Developer UI:

```bash
npm run genkit:ui
```

This opens the Dev UI at `http://localhost:4000` where you can:

- **Test all four flows** with different inputs visually
- **View detailed traces** of every AI call, including the prompt sent, model response, latency, and token usage
- **Debug streaming flows** and watch chunks arrive in real-time
- **Inspect structured outputs** and verify the schema is being followed

The Dev UI works identically whether you are using Azure OpenAI, Google Gemini, or AWS Bedrock. This unified experience is one of Genkit's greatest strengths: you develop and debug the same way regardless of the backend.

## Local Development

### Run with Azure Functions Core Tools

```bash
npm run func:start
```

This starts a local server at `http://localhost:7071` that mimics the Azure Functions runtime:

```bash
curl -X POST http://localhost:7071/api/storyGeneratorFlow \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "topic": "a robot learning to feel emotions",
      "style": "sci-fi",
      "length": "medium"
    }
  }'
```

### Using the Genkit Client SDK

You can also call your flows using the `genkit/beta/client` SDK:

```typescript
import { runFlow, streamFlow } from 'genkit/beta/client';

const result = await runFlow({
  url: 'http://localhost:7071/api/jokeFlow',
  input: { subject: 'programming' },
});

// Streaming
const result = streamFlow({
  url: 'http://localhost:7071/api/jokeStreamingFlow',
  input: { subject: 'TypeScript' },
});
for await (const chunk of result.stream) {
  process.stdout.write(chunk);
}

// With API key auth
const result = await runFlow({
  url: 'http://localhost:7071/api/protectedSummaryFlow',
  input: { text: 'Your long text...', maxLength: 50 },
  headers: { 'X-API-Key': 'demo-api-key' },
});
```

## Deployment

Build and deploy to Azure:

```bash
npm run build
npm run deploy
```

Make sure to set your environment variables in Azure:

```bash
az functionapp config appsettings set \
  --name myFunctionAppName \
  --resource-group myResourceGroup \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="your-api-key-here" \
    OPENAI_API_VERSION="2024-10-21"
```

## Resources

- [Genkit Documentation](https://genkit.dev/docs/)
- [Azure OpenAI Plugin](https://github.com/genkit-ai/azure-foundry-js-plugin)
- [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- [Azure OpenAI Service](https://azure.microsoft.com/services/cognitive-services/openai-service/)

## Conclusion

Genkit brings a consistent, delightful developer experience to Azure Functions. The combination of typed flows with Zod schemas, structured LLM output, the Dev UI for visual debugging, and the `onCallGenkit` helper makes building AI-powered Azure Functions as straightforward as defining a function.

You can find the full code of this example in the [GitHub repository](https://github.com/xavidop/genkit-azure-function-ai-foundry)

Happy coding!
