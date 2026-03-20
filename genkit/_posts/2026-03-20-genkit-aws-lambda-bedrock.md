---
layout: post
title: Running Genkit on AWS Lambda with Bedrock (English)
description: >
  Deploy AI-powered flows to AWS Lambda using Genkit and the AWS Bedrock plugin
image: /assets/img/blog/post-headers/genkit-aws-lambda-bedrock.png
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - gcp
  - aws
keywords:
  - genkit
  - aws
  - lambda
  - bedrock
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

One of the most powerful things about **Genkit** is that it is cloud-agnostic. You are not locked into a single provider. In this post, we will explore how to run Genkit flows on **AWS Lambda** using the **AWS Bedrock plugin**, deploying a full AI-powered story and joke generator with streaming support, all managed by the **Serverless Framework**.

The project uses the `onCallGenkit` helper from the AWS Bedrock plugin, which wraps any Genkit flow as a Lambda handler automatically, handling CORS, request parsing, error formatting, and even streaming via Lambda Function URLs.

## Why Genkit on AWS?

If your infrastructure lives on AWS, you might think Genkit is not for you. Think again. The community-maintained [AWS Bedrock plugin](https://github.com/genkit-ai/aws-bedrock-js-plugin) brings first-class Bedrock support to Genkit, giving you:

- Access to **Amazon Nova**, **Anthropic Claude**, and other Bedrock models
- The `onCallGenkit` helper for zero-boilerplate Lambda handlers
- Full compatibility with the **Genkit Dev UI** for local development
- Streaming support via Lambda Function URLs

## Prerequisites

- **Node.js 20** or later
- **AWS Account** with AWS CLI configured and access to AWS Bedrock
- **Serverless Framework** (installed as dev dependency)
- **Genkit CLI** installed globally

```bash
npm install -g genkit-cli
```

## Project Structure

```
genkit-aws-lambda-bedrock/
├── src/
│   └── index.ts          # Genkit flows + Lambda handlers via onCallGenkit
├── serverless.yml        # Serverless Framework configuration
├── tsconfig.json         # TypeScript configuration
├── package.json          # Dependencies and scripts
└── README.md
```

## Initializing Genkit with Bedrock

The setup is minimal. Import the plugin, initialize Genkit, and pick your model:

```typescript
import { genkit, z } from 'genkit';
import { awsBedrock, amazonNovaProV1, onCallGenkit } from 'genkitx-aws-bedrock';

const ai = genkit({
  plugins: [awsBedrock()],
  model: amazonNovaProV1(),
});
```

That is it. Genkit is now configured to use **Amazon Nova Pro** via Bedrock. You can swap to `anthropicClaude35SonnetV2` or any other supported model with a single line change.

## Defining Flows

Genkit flows are the core building block. Each flow has typed input and output schemas using **Zod**, making everything type-safe from end to end.

### Story Generator Flow

```typescript
const StoryInputSchema = z.object({
  topic: z.string().describe('The main topic or theme for the story'),
  style: z.string().optional().describe('Writing style (e.g., adventure, mystery, sci-fi)'),
  length: z.enum(['short', 'medium', 'long']).default('medium'),
});

const StoryOutputSchema = z.object({
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
    outputSchema: StoryOutputSchema,
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
      output: { schema: StoryOutputSchema },
    });

    if (!output) {
      throw new Error('Failed to generate story');
    }

    return output;
  }
);
```

Notice how `ai.generate` returns a fully structured, typed object. No JSON parsing, no string manipulation. Genkit handles all of that for you.

### Joke Flow with Streaming

Genkit also supports streaming responses. The `jokeStreamingFlow` uses `ai.generateStream` and `sendChunk` to emit text chunks as they arrive from the LLM:

```typescript
const jokeStreamingFlow = ai.defineFlow(
  {
    name: 'jokeStreamingFlow',
    inputSchema: z.object({
      subject: z.string().describe('The subject to tell a joke about'),
    }),
    outputSchema: z.object({
      joke: z.string(),
      type: z.string().optional(),
    }),
    streamSchema: z.string(),
  },
  async (input, sendChunk) => {
    const { stream, response } = await ai.generateStream({
      prompt: `Tell me a funny joke about ${input.subject}. Make it clever and appropriate for all ages.`,
      output: {
        schema: z.object({
          joke: z.string(),
          type: z.string().optional(),
        }),
      },
    });

    for await (const chunk of stream) {
      sendChunk(chunk.text);
    }

    const result = await response;
    return result.output || { joke: result.text };
  }
);
```

## Wrapping Flows as Lambda Handlers

The `onCallGenkit` helper is where the magic happens. It transforms any Genkit flow into a production-ready Lambda handler:

```typescript
// Simple flow handler
export const jokeHandler = onCallGenkit(jokeFlow);

// With CORS and debug options
export const storyGeneratorHandler = onCallGenkit(
  {
    cors: { origin: '*', methods: ['POST', 'OPTIONS'] },
    debug: process.env.NODE_ENV !== 'production',
  },
  storyGeneratorFlow
);

// Streaming handler (requires Lambda Function URL with RESPONSE_STREAM)
export const jokeStreamHandler = onCallGenkit(
  {
    streaming: true,
    cors: { origin: '*', methods: ['POST', 'OPTIONS'] },
    debug: process.env.NODE_ENV !== 'production',
  },
  jokeStreamingFlow
);
```

## The Genkit Dev UI

This is where Genkit truly shines during development. Run:

```bash
npm run genkit:ui
```

This starts the **Genkit Developer UI** at `http://localhost:4000`. From here, you can:

- **Test any flow** visually with different inputs, no cURL needed
- **View detailed traces** of every AI generation, including prompts, model responses, and latency
- **Debug and optimize prompts** interactively
- **Inspect streaming** responses in real-time

The Dev UI is model-agnostic, so even though we are using AWS Bedrock, the same visual debugging experience applies. This is one of the biggest advantages of Genkit: a unified developer experience regardless of the underlying AI provider.

## Local Development with Serverless Offline

For testing the Lambda locally with a real HTTP endpoint:

```bash
npm run dev
```

This starts a local server at `http://localhost:3000` that mimics API Gateway. Test it with:

```bash
curl -X POST http://localhost:3000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "topic": "a robot learning to feel emotions",
      "style": "sci-fi",
      "length": "medium"
    }
  }'
```

## Deployment

Deploy to AWS with a single command:

```bash
npm run deploy
```

After deployment, you will see output like:

```
endpoints:
  POST - https://abc123.execute-api.us-east-1.amazonaws.com/generate
  POST - https://abc123.execute-api.us-east-1.amazonaws.com/joke
functions:
  storyGenerator: genkit-aws-lambda-bedrock-dev-storyGenerator
  jokeGenerator: genkit-aws-lambda-bedrock-dev-jokeGenerator
```

## Using the Genkit Client SDK

You can also call your deployed flows from a frontend or another service using the `genkit/beta/client` SDK:

```typescript
import { runFlow, streamFlow } from 'genkit/beta/client';

// Non-streaming
const result = await runFlow({
  url: 'https://your-api-url.amazonaws.com/generate',
  input: { topic: 'space exploration', style: 'sci-fi', length: 'short' },
});

// Streaming
const result = streamFlow({
  url: 'https://your-api-url.amazonaws.com/joke-stream',
  input: { subject: 'TypeScript' },
});
for await (const chunk of result.stream) {
  process.stdout.write(chunk);
}
```

## Resources

- [Genkit Documentation](https://genkit.dev/docs/)
- [AWS Bedrock Plugin](https://github.com/genkit-ai/aws-bedrock-js-plugin)
- [Serverless Framework Documentation](https://www.serverless.com/framework/docs)
- [AWS Bedrock](https://aws.amazon.com/bedrock/)

## Conclusion

Genkit makes it incredibly easy to build, test, and deploy AI-powered applications on AWS. The combination of typed flows, the Dev UI for visual debugging, and the `onCallGenkit` helper for zero-boilerplate Lambda handlers means you spend your time on AI logic, not infrastructure plumbing.

You can find the full code of this example in the [GitHub repository](https://github.com/xavidop/genkit-aws-lambda-bedrock)

Happy coding!
