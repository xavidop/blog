---
layout: post
title: Firebase GenKit with Gemma using Ollama (English)
description: >
  Firebase project that uses the Gen AI Kit with Gemma using Ollama
image: /assets/img/blog/post-headers/firebase-genkit-ollama.png
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
  - ollama
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

## Introduction

This is a simple example of a Firebase function that uses Genkit and Ollama to translate any test to Spanish.

This project uses the following technologies:
1. Firebase Functions
2. Firebase Genkit
3. Ollama

This project uses the following Node.js Packages:
1. `@genkit-ai/firebase`: Genkit Firebase SDK to be able to use Genkit in Firebase Functions
2. `genkitx-ollama`: Genkit Ollama plugin to be able to use Ollama in Genkit
3. `genkit`: Genkit AI Core SDK

## Setup

1. Clone this repository: [GitHub repository](https://github.com/xavidop/firebase-genkit-ollama).
2. Run `npm install` to install the dependencies in the functions folder
3. Run `firebase login` to login to your Firebase account
4. Install genkit-cli by running `npm install -g genkit`

This repo is supposed to be used with NodeJS version 20.


### Open Genkit UI

Go to the functions folder and run `npm run genkit:start` to open the Genkit UI. The UI will be available at `http://localhost:4000`.

![Full-width image](/assets/img/blog/tutorials/firebase-genkit-ollama/genaikitui.png){:.lead data-width="800" data-height="100"}
Firebase Genkit UI
{:.figure}

### Run the Firebase emulator

To run the function locally, run `firebase emulators:start --inspect-functions`.

The emulator will be available at `http://localhost:4001`

### Run Gemma with Ollama

You will need to install Ollama by running `brew install ollama` and then run `ollama run gemma` to start the Ollama server running the Gemma LLM.

## Code explanation

The code is in the `functions/index.ts` file. The function is called `translatorFlow` and it uses the Genkit SDK to translate any given text to Spanish.

First, we have to configure the Genkit SDK with the Ollama plugin:

```typescript
const ai = genkit({
  plugins: [
    ollama({
      models: [{ name: 'gemma' }],
      serverAddress: 'http://127.0.0.1:11434', // default ollama local address
    }),
  ]
});
logger.setLogLevel('debug');
```

Then, we define the function, in the Gen AI Kit they call it Flows. A Flow is a function with some additional characteristics: they are strongly typed, streamable, locally and remotely callable, and fully observable. Firebase Genkit provides CLI and Developer UI tooling for working with flows (running, debugging, etc):

```typescript
export const translatorFlow = onFlow(
  ai,
  {
    name: "translatorFlow",
    inputSchema: z.object({ text: z.string() }),
    outputSchema: z.string(),
    authPolicy: noAuth(), // Not requiring authentication, but you can change this. It is highly recommended to require authentication for production use cases.
  },
  async (toTranslate) => {
    const prompt =
      `Translate this ${toTranslate.text} to Spanish. Autodetect the language.`;

    const llmResponse = await ai.generate({
      model: 'ollama/gemma',
      prompt: prompt,
      config: {
        temperature: 1,
      },
    });

    return llmResponse.text;
  }
);
```

As we saw above, we use Zod to define the input and output schema of the function. We also use the `generate` function from the Genkit SDK to generate the translation.

We also have disabled the authentication for this function, but you can change this by changing the `authPolicy` property:

```typescript
firebaseAuth((user) => {
  if (!user.email_verified) {
    throw new Error('Verified email required to run flow');
  }
});
```

For the example above you will need to import the `firebaseAuth` function from the `@genkit-ai/firebase/auth` package:

```typescript
import { firebaseAuth } from '@genkit-ai/firebase/auth';
```

## Invoke the function locally

Now you can invoke the function by running `genkit flow:run translatorFlow '{"text":"hi"}'` in the terminal.

You can also make a curl command by running `curl -X GET -H "Content-Type: application/json" -d '{"data": { "text": "hi" }}' http://127.0.0.1:5001/<firebase-project>/<region>/translatorFlow` in the terminal.

For example:
```bash
> curl -X GET -H "Content-Type: application/json" -d '{"data": { "text": "hi" }}' http://127.0.0.1:5001/action-helloworld/us-central1/translatorFlow
{"result":"Hola\n\nThe translation of \"hi\" to Spanish is \"Hola\"."}
```

You can also use Postman or any other tool to make a GET request to the function:

![Full-width image](/assets/img/blog/tutorials/firebase-genkit-ollama/postman.png){:.lead data-width="800" data-height="100"}
Postman Request
{:.figure}

## Deploy

To deploy the function, run `firebase deploy --only functions`. You will need to change the ollama URL in the function to the URL of the Ollama server.

## Resources

- [Firebase Genkit](https://firebase.google.com/products/genkit)
- [Ollama](https://ollama.com/)
- [Firebase Functions](https://firebase.google.com/docs/functions)

## Conclusion

As you can see, it is very easy to use Genkit and Ollama in Firebase Functions. You can use this example as a starting point to create your own functions using Genkit and Ollama.

You can find the full code of this example in the [GitHub repository](https://github.com/xavidop/firebase-genkit-ollama)

Happy coding!