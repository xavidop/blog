---
layout: post
title: Genkit in Node, Building a Weather Service with AI Integration (English)
description: >
  Building a weather service using Genkit in Node.js with AI integration
image: /assets/img/blog/post-headers/firebase-genkit-node-tool.png
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [gcp, firebase]
tags:
  - firebase
  - gcp
keywords:
  - firebase
  - github-models
  - github
  - genkit
  - firebase-genkit
  - generative-ai
  - googlecloud
  - gcp
  - google-cloud-platform
  - google-cloud

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Overview

This project demonstrates how to build an AI-enhanced weather service using Genkit, TypeScript, OpenWeatherAPI and Github Models. The application showcases modern Node.js patterns and AI integration techniques.

## Prerequisites
Before you begin, ensure you have the following:
1. Node.js installed on your machine.
2. GitHub account and access token for GitHub APIs.
3. An OpenWeatherAPI key for fetching weather data.
4. Genkit CLI installed on your machine.

## Technical Deep Dive

### AI Configuration
The core AI setup is initialized with Genkit and GitHub plugin integration. In this case we are going to use the OpenAI o3-mini model:

```typescript
const ai = genkit({
  plugins: [
    github({ githubToken: process.env.GITHUB_TOKEN }),
  ],
  model: openAIO3Mini,
});
```

### Weather Tool Implementation
The application defines a custom weather tool using Zod schema validation:

```typescript
const getWeather = ai.defineTool(
  {
    name: 'getWeather',
    description: 'Gets the current weather in a given location',
    inputSchema: weatherToolInputSchema,
    outputSchema: z.string(),
  },
  async (input) => {

    const weather = new OpenWeatherAPI({
        key: process.env.OPENWEATHER_API_KEY,
        units: "metric"
    })

    const data = await weather.getCurrent({locationName: input.location});

    return `The current weather in ${input.location} is: ${data.weather.temp.cur} Degrees in Celsius`;
  }
);
```

### AI Flow Definition
The service exposes an AI flow that processes weather requests:

```typescript
const helloFlow = ai.defineFlow(
  {
    name: 'helloFlow',
    inputSchema: z.object({ location: z.string() }),
    outputSchema: z.string(),
  },
  async (input) => {
    const response = await ai.generate({
      tools: [getWeather],
      prompt: `What's the weather in ${input.location}?`
    });
    return response.text;
  }
);
```

### Express Server Configuration
The application uses the Genkit Express plugin to create an API server:

```typescript
const app = express({
  flows: [helloFlow],
});
```

## Full Code

The full code for the weather service is as follows:

```typescript
/* eslint-disable  @typescript-eslint/no-explicit-any */

import { genkit, z } from 'genkit';
import { startFlowServer } from '@genkit-ai/express';
import { openAIO3Mini, github } from 'genkitx-github';
import {OpenWeatherAPI } from 'openweather-api-node';
import dotenv from 'dotenv';

dotenv.config();

const ai = genkit({
  plugins: [
    github({ githubToken: process.env.GITHUB_TOKEN }),
  ],
  model: openAIO3Mini,
});

const weatherToolInputSchema = z.object({ 
  location: z.string().describe('The location to get the current weather for')
});

const getWeather = ai.defineTool(
  {
    name: 'getWeather',
    description: 'Gets the current weather in a given location',
    inputSchema: weatherToolInputSchema,
    outputSchema: z.string(),
  },
  async (input) => {

    const weather = new OpenWeatherAPI({
        key: process.env.OPENWEATHER_API_KEY,
        units: "metric"
    })

    const data = await weather.getCurrent({locationName: input.location});

    return `The current weather in ${input.location} is: ${data.weather.temp.cur} Degrees in Celsius`;
  }
);

const helloFlow = ai.defineFlow(
  {
    name: 'helloFlow',
    inputSchema: z.object({ location: z.string() }),
    outputSchema: z.string(),
  },
  async (input) => {

    const response  = await ai.generate({
      tools: [getWeather],
      prompt: `What's the weather in ${input.location}?`
    });

    return response.text;
  }
);

startFlowServer({
  flows: [helloFlow]
});
```

## Setup & Development

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
GITHUB_TOKEN=your_token
OPENWEATHER_API_KEY=your_key
```

3. Start development server:
```bash
npm run genkit:start
```

4. To run the project in debug mode and set breakpoints, you can run:
```bash
npm run genkit:start:debug
```
And then launch the debugger in your IDE. See the `.vscode/launch.json` file for the configuration.

5. If you want to build the project, you can run:
```bash
npm run build
```

6. Run the project in production mode:
```bash
npm run start:production
```

## Dependencies

### Core Dependencies
- `genkit`: ^1.0.5
- `@genkit-ai/express`: ^1.0.5
- `openweather-api-node`: ^3.1.5
- `genkitx-github`: ^1.13.1
- `dotenv`: ^16.4.7

### Development Dependencies
- `tsx`: ^4.19.2
- `typescript`: ^5.7.2

## Project Configuration

- Uses ES Modules (`"type": "module"`)
- TypeScript with `NodeNext` module resolution
- Output directory: lib
- Full TypeScript support with type definitions

## License

Apache 2.0

## Resources

- [Firebase Genkit](https://firebase.google.com/products/genkit)
- [GitHub Models](https://github.com/marketplace/models)
- [Firebase Express Plugin](https://firebase.google.com/docs/genkit/deploy-node)

## Conclusion

This project demonstrates how to build a weather service using Genkit in Node.js with AI integration. The application showcases modern Node.js patterns and AI integration techniques.

You can find the full code of this example in the [GitHub repository](https://github.com/xavidop/genkit-node-tool-example)

Happy coding!