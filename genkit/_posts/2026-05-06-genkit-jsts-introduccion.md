---
layout: post
title: Introduccion a Genkit con JavaScript y TypeScript (Guia paso a paso)
description: >
  Aprende a empezar con Genkit en JS/TS desde cero: instalacion, primer flow,
  ejecucion local y uso de la Developer UI.
image: /assets/img/blog/post-headers/genkit-jsts-introduccion.png
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - javascript
  - typescript
  - gemini
  - gcp
keywords:
  - genkit
  - javascript
  - typescript
  - gemini
  - google ai studio
  - developer ui
  - ia generativa
  - flujos

lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduccion

Si vienes del ecosistema Node.js y quieres construir funcionalidades de IA generativa sin pelearte con demasiada infraestructura, **Genkit** es una de las mejores opciones ahora mismo.

En esta guia vas a crear tu primer proyecto con **JavaScript/TypeScript**, definir un **flow tipado**, ejecutarlo en local y probarlo en la **Developer UI**.

Esta introduccion esta basada en la guia oficial de Genkit para JS/TS:
[Get started with Genkit](https://genkit.dev/docs/js/get-started/)

## Que es Genkit y por que usarlo

Genkit es un framework open source para construir aplicaciones de IA con una capa de desarrollo muy práctica para backend:

1. Define inputs y outputs con esquemas (Zod).
2. Crea flows reutilizables y tipados.
3. Prueba todo en local con trazas en la Developer UI.
4. Te deja cambiar de proveedor/modelo con menos fricción.

## Prerrequisitos

Antes de empezar, necesitas:

1. Node.js **v20 o superior**.
2. npm.
3. Una API key de Gemini desde [Google AI Studio](https://aistudio.google.com/apikey).

## 1) Crear el proyecto TypeScript

Desde terminal:

```bash
mkdir my-genkit-app
cd my-genkit-app

npm init -y
npm pkg set type=module

npm install -D typescript tsx
npx tsc --init

mkdir src
touch src/index.ts
```

Con esto ya tienes la base de un proyecto TS en Node.

## 2) Instalar Genkit

Instala primero la CLI (necesaria para la Developer UI):

```bash
npm install -g genkit-cli
```

Instala despues las dependencias del proyecto:

```bash
npm install genkit @genkit-ai/google-genai
```

## 3) Configurar la API key

Exporta la variable de entorno en tu shell:

```bash
export GEMINI_API_KEY=<tu_api_key>
```

Si usas `zsh`, tambien puedes dejarla en tu `.zshrc` para no repetir este paso cada vez.

## 4) Crear tu primer flow con Genkit

Edita `src/index.ts` y pega este ejemplo:

```typescript
import { googleAI } from '@genkit-ai/google-genai';
import { genkit, z } from 'genkit';

// Inicializa Genkit con el plugin de Google AI y modelo por defecto.
const ai = genkit({
  plugins: [googleAI()],
  model: googleAI.model('gemini-3-pro', {
    temperature: 0.8,
  }),
});

const RecipeInputSchema = z.object({
  ingredient: z.string().describe('Ingrediente principal o tipo de cocina'),
  dietaryRestrictions: z
    .string()
    .optional()
    .describe('Restricciones alimentarias, si existen'),
});

const RecipeSchema = z.object({
  title: z.string(),
  description: z.string(),
  prepTime: z.string(),
  cookTime: z.string(),
  servings: z.number(),
  ingredients: z.array(z.string()),
  instructions: z.array(z.string()),
  tips: z.array(z.string()).optional(),
});

export const recipeGeneratorFlow = ai.defineFlow(
  {
    name: 'recipeGeneratorFlow',
    inputSchema: RecipeInputSchema,
    outputSchema: RecipeSchema,
  },
  async (input) => {
    const prompt = `Create a recipe with the following requirements:\nMain ingredient: ${input.ingredient}\nDietary restrictions: ${input.dietaryRestrictions || 'none'}`;

    const { output } = await ai.generate({
      prompt,
      output: { schema: RecipeSchema },
    });

    if (!output) {
      throw new Error('Failed to generate recipe');
    }

    return output;
  }
);

async function main() {
  const recipe = await recipeGeneratorFlow({
    ingredient: 'aguacate',
    dietaryRestrictions: 'vegetariana',
  });

  console.log(recipe);
}

main().catch(console.error);
```

Este ejemplo muestra tres conceptos clave de Genkit:

1. **Esquemas de input/output con Zod** para evitar respuestas ambiguas.
2. **Flow reutilizable** que despues puedes exponer como API.
3. **Structured Output** desde el modelo (no solo texto libre).

## 5) Ejecutar la aplicacion

ejecuta el ejemplo:

```bash
npx tsx src/index.ts
```

Si todo va bien, veras por consola un objeto JSON con la receta generada.

## 6) Probar en la Developer UI

Arranca la UI de desarrollo de Genkit:

```bash
genkit start -- npx tsx --watch src/index.ts
```

Por defecto estara en:

- `http://localhost:4000`

Dentro de la UI:

1. Selecciona `recipeGeneratorFlow`.
2. Introduce un input como este:

```json
{
  "ingredient": "aguacate",
  "dietaryRestrictions": "vegetariana"
}
```

3. Pulsa `Run`.

Veras el structured output y la traza de ejecucion para debuggear prompts y tiempos.

## Script opcional en package.json

Para no recordar el comando largo, puedes añadir este script:

```json
{
  "scripts": {
    "genkit:ui": "genkit start -- npx tsx --watch src/index.ts"
  }
}
```

Y ejecutarlo con:

```bash
npm run genkit:ui
```

## Errores tipicos al empezar

1. `GEMINI_API_KEY` no definida.
2. Usar Node < 20.
3. Intentar correr la UI sin `genkit-cli` instalado globalmente.

## Siguientes pasos recomendados

Cuando ya tengas este primer flow funcionando, te recomiendo seguir por este orden:

1. [Developer tools](https://genkit.dev/docs/js/devtools/)
2. [Generating content](https://genkit.dev/docs/js/models/)
3. [Creating flows](https://genkit.dev/docs/js/flows/)
4. [Tool calling](https://genkit.dev/docs/js/tool-calling/)
5. [Dotprompt](https://genkit.dev/docs/js/dotprompt/)

## Conclusiones

Genkit en JS/TS te permite pasar de idea a prototipo funcional en muy poco tiempo, manteniendo un codigo limpio, tipado y facil de evolucionar.

Si trabajas en Node.js y quieres construir features con IA de forma seria (pero sin sobreingenieria), este stack es una apuesta muy solida.
