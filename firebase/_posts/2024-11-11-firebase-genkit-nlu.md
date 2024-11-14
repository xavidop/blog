---
layout: post
title: NLU powered by LLMs using Firebase GenKit with GitHub Models (English)
description: >
  The NLU powered by LLMs that just works
image: /assets/img/blog/post-headers/firebase-genkit-nlu.png
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

## Introduction

This project implements a Natural Language Understanding (NLU) flow using Firebase Genkit AI and Firebase Functions. The NLU flow detects intents and extracts entities from a given text input.

this project uses GitHub Models using the Genkit GitHub models plugin.

This project uses the following technologies:
1. Firebase Functions
2. Firebase Genkit
3. GitHub Models

This project uses the following Node.js Packages:
1. `@genkit-ai/firebase`: Genkit Firebase SDK to be able to use Genkit in Firebase Functions
2. `genkitx-ollama`: Genkit Ollama plugin to be able to use Ollama in Genkit
3. `genkit`: Genkit AI Core SDK

## Setup

1. Clone this repository: [GitHub repository](https://github.com/xavidop/genkit-nlu).
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

## Configuration

1. Ensure you have the necessary Firebase configuration files (`firebase.json`, `.firebaserc`).

2. Update the `nlu/intents.yml` and `nlu/entities.yml` files with your intents and entities.

## Development

### Linting

Run ESLint to check for code quality issues:
```sh
npm run lint
```

### Building

Compile the TsypeScript code:
```sh
npm run build
```

## Code Explanation
* Configuration: The `genkit` function is called to set up the Genkit environment with plugins for Firebase, GitHub, and Dotprompt. It also sets the log level to "debug" and enables tracing and metrics.

```typescript
const ai = genkit({
  plugins: [github()],
  promptDir: 'prompts',
  model: openAIGpt4o
});
logger.setLogLevel('debug');
```

* Flow Definition: The nluFlow is defined using the onFlow function.
   * Configuration: The flow is named `nluFlow` and has input and output schemas defined using zod. The input schema expects an object with a text string, and the output schema is a string. The flow does not require authentication (noAuth).
   * nluFlow: The flow processes the input:
        * Schema Definition: Defines an `nluOutput` schema with intent and entities.
        * Prompt Reference: Gets a reference to the "nlu" dotprompt file.
        * File Reading: Reads `intents.yml` and `entities.yml` files.
        * Prompt Generation: Uses the `nluPrompt` to generate output based on the input text and the read intents and entities.
        * Return Output: Returns the generated output with type `nluOutput`.

```typescript
export const nluFlow = onFlow(
  ai,
  {
    name: "nluFlow",
    inputSchema: z.object({text: z.string()}),
    outputSchema: z.string(),
    authPolicy: noAuth(), // Not requiring authentication.
  },
  async (toDetect) => {
    const nluOutput = ai.defineSchema(
      "nluOutput",
      z.object({
        intent: z.string(),
        entities: z.map(z.string(), z.string()),
      }),
    );

    const nluPrompt = ai.prompt<
                        z.ZodTypeAny, // Input schema
                        typeof nluOutput, // Output schema
                        z.ZodTypeAny // Custom options schema
                      >("nlu");

    const intents = readFileSync('nlu/intents.yml','utf8');
    const entities = readFileSync('nlu/entities.yml','utf8');

    const result = await nluPrompt({
        intents: intents,
        entities: entities,
        user_input: toDetect.text,
    });

    return JSON.stringify(result.output);
  },
);
```

## Prompt Definition 

This `nlu.prompt` file defines a prompt for a Natural Language Understanding (NLU) model. Here's a breakdown of its components:

1. **Model Specification**:
   ```yaml
   model: github/gpt-4o
   ```
   This specifies the LLM model to be used, in this case, `github/gpt-4o`.

2. **Input Schema**:
   ```yaml
   input:
     schema:
       intents: string
       entities: string
       user_input: string
   ```
   This defines the input schema for the prompt. It expects three string inputs:
   - `intents`: A string representing the intents.
   - `entities`: A string representing the entities.
   - `user_input`: A string representing the user's input text.

3. **Output Specification**:
   ```yaml
   output:
     format: json
     schema: nluOutput
   ```
   This defines the output format and schema. The output will be in JSON format and should conform to the `nluOutput` schema.

4. **Prompt Text**:
   ```yaml
  ---
  model: github/gpt-4o
  input:
    schema:
      intents: string
      entities: string
      user_input: string
  output:
    format: json
    schema: nluOutput
  ---
   You are a NLU that detects intents and extract entities from a given text.

   you have these intents and utterances:
   {% raw %}{{intents}}{% endraw %}
   You also have these entities:
   {% raw %}{{entities}}{% endraw %}

   The user says: {% raw %}{{user_input}}{% endraw %}
   Please specify the intent detected and the entity detected
   
   ```

   This is the actual prompt text that will be used by the model. It provides context and instructions to the model:
   - It describes the role of the model as an NLU system.
   - It includes placeholders ({% raw %}`{{intents}}`{% endraw %}, {% raw %}`{{entities}}`{% endraw %}, {% raw %}`{{user_input}}`{% endraw %}) that will be replaced with the actual input values.
   - It asks the model to specify the detected intent and entity based on the provided user input.

## Usage

The main NLU flow is defined in index.ts. It reads intents and entities from YAML files and uses a prompt defined in `nlu.prompt` to generate responses.

### Intents
The intents are defined in the `nlu/intents.yml` file. Each intent has a name and a list of training phrases.

As an example, the following intent is defined in the `nlu/intents.yml` file:
```yaml
order_shoes:
  utterances: 
    - I want a pair of shoes from {shoes_brand}
    - a shoes from {shoes_brand}
```
The format is as follows:
```yaml
intent-name:
  utterances:
    - training phrase 1
    - training phrase 2
    - ...
```

### Entities
The entities are defined in the `nlu/entities.yml` file. Each entity has a name and a list of synonyms.

As an example, the following entity is defined in the `nlu/entities.yml` file:
```yaml
shoes_brand:
  examples:
    - Puma
    - Nike
```
The format is as follows:
```yaml
entity-name:
  examples:
    - synonym 1
    - synonym 2
    - ...
```

### Example

To trigger the NLU flow, send a request with the following structure:
```json
{
  "text": "Your input text here"
}
```

The response will be a JSON object with the following structure:
```json
{
  "intent": "intent-name",
  "entities": {
    "entity-name": "entity-value"
  }
}
```

## Deploy

To deploy the function, run `firebase deploy --only functions`.

## Resources

- [Firebase Genkit](https://firebase.google.com/products/genkit)
- [GitHub Models](https://github.com/marketplace/models)
- [Firebase Functions](https://firebase.google.com/docs/functions)

## Conclusion

As you can see, it is very easy to use Genkit and GitHub Models in Firebase Functions. You can use this example as a starting point to create your own functions using Genkit and GitHub Models.

You can find the full code of this example in the [GitHub repository](https://github.com/xavidop/genkit-nlu)

Happy coding!