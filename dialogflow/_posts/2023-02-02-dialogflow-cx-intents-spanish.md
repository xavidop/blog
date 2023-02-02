---
layout: post
title: Intents en Dialogflow CX
description: >
  Este tutorial te enseñará a crear intents de manera sencilla, así como a mejorar tu NLU en Dialogflow CX, ya sea a través de la consola o de la CX CLI. 
image: /assets/img/blog/post-headers/dialogflow-intents.jpg
comments: true
author: xavi
kate: hl markdown;
categories: [dialogflow]
tags:
  - dialogflow
keywords:
  - dialogflow
  - dialogflowcx
  - cxcli
  - conversationalai

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

# Intents en Dialogflow CX

## Requisitos previos 

Estas son las tecnologías utilizadas en este proyecto 
1. Google Cloud Account - [Regístrate aquí de forma gratuita](https://cloud.google.com/)
2. Dialogflow API enabled - [Cómo habilitarla](https://cloud.google.com/dialogflow/cx/docs/reference)
3. Dialogflow CX CLI - [Instala y configura Dialogflow CX CLI](https://cxcli.xavidop.me/)

## ¿De qué se trata? 

![Full-width image](/assets/img/blog/tutorials/dialogflow-intents/intent.png){:.lead data-width="800" data-height="100"}
Intent
{:.figure}

Antes de empezar a hablar de intents, es importante entender qué es el NLU. El Natural Language Understanding, la comprensión del lenguaje natural (NLU) es un subconjunto del Natural Language Processing, o procesamiento del lenguaje natural (NLP). Ayuda a que una “máquina” sea capaz de entender el lenguaje humano. Esta es una parte importante en Dialogflow CX, ya que ayuda a predecir la intención del usuario y nos permite actuar de una manera más “inteligente” para así evitar la ya típica pregunta: “No le he entendido, ¿podría repetirlo?”. Llamamos intents a las propuestas o peticiones de los usuarios que la máquina debe clasificar. 

 Cada intent cuenta con frases de entrenamiento o enunciados. También lo podéis encontrar como utterances. Por ejemplo, el `welcome_intent` intent puede tener estas tres frases de entrenamiento: 

1. “Hola” 
2. “Qué tal”
3. “¿Cómo estás?” 

Como se puede observar en el ejemplo anterior, nuestra intención con el intent `welcome_intent` es iniciar una conversación en cuanto un usuario pronuncie cualquiera de estas frases de entrenamiento. Un intent puede tener múltiples entities o entidades. Las entities se explicarán próximamente en otro artículo. 

Para mostrar otro ejemplo, si observamos la imagen anterior, veremos el intent `get_info`. Este intent también cuenta con múltiples frases de entrenamiento: 

1. “Cuéntame algo sobre Pikachu” 
2. “Dame información sobre Pikachu” 
3. “Información Pikachu” 
4. “Pikachu” 

Por lo tanto, podemos solicitar información sobre un determinado Pokémon de muchas formas. En este ejemplo, `pikachu` es una entity. 

Una buena práctica puede consistir en probar las frases de entrenamiento con los usuarios finales. Esto te permitirá detectar las frases de entrenamiento que falten en tu NLU. 

## Dialogflow Console

Dialogflow Console es una interfaz web donde puedes diseñar tus conversaciones creando agentes y, dentro de un agente, crear flows, intents, entity types, etc. En la consola de Dialogflow es posible crear intents e interactuar fácilmente con ellos. Para ello, basta con acceder a la: [https://dialogflow.cloud.google.com/cx](https://dialogflow.cloud.google.com/cx). Este es su aspecto:

![Full-width image](/assets/img/blog/tutorials/dialogflow-agents/console.png){:.lead data-width="800" data-height="100"}
Dialogflow CX Console
{:.figure}

Encontrarás tus intents en la pestaña **Manage** al hacer clic en la sección **intents**:

![Full-width image](/assets/img/blog/tutorials/dialogflow-intents/console-intent.png){:.lead data-width="800" data-height="100"}
Dialogflow CX Intent
{:.figure}

Con la consola de Dialogflow CX, puedes: 
1. Crear un intent: Cuando crees un intent, puedes añadir frases de entrenamiento y añadir una descripción o etiquetas a ese intent. También puedes agregar entity types a un intent. 
2. Eliminar un intent. 
3. Entrenar y validar tu NLU. 

Siempre que crees, modifiques o elimines un intent, es importante que vuelvas a entrenar tus flows en Dialogflow CX. Esto volverá a entrenar tu NLU. De este modo, tu bot “entenderá” como interactúas con él junto con tus últimos cambios. 

## Dialogflow CX CLI

La [Dialogflow CX CLI](https://cxcli.xavidop.me/) o `cxcli` ies una herramienta de línea de comandos que puedes utilizar para interactuar con tus proyectos en Dialogflow CX en un terminal. Es un proyecto de código abierto creado por [Xavier Portilla Edo](https://xavidop.me/). Con la `cxcli` ypuedes interactuar fácilmente con tus intents en Dialogflow CX.

Todos los comandos disponibles en la `cxcli` para interactuar con tus intents se encuentran en el subcomando `cxcli intent`.

### Crear

Puedes [crear](https://cxcli.xavidop.me/intents/create) utilizando esta herramienta Este comando se utiliza así: 

```sh
cxcli intent create [intent-name] [parameters]
```

Puedes consultar el uso completo [aquí](https://cxcli.xavidop.me/cmd/cxcli_intent_create). Es importante explicar el parámetro `--training-phrases`. Se trata de una lista de las frases de entrenamiento para este intent, que se encuentran separadas por comas. Para las entities utilizadas en este intent, añade `@entity-type` a la palabra en la frase de entrenamiento. Este es el formato:
```
word@entity-type
```

Aquí tienes un ejemplo: `hello, hi how are you today@sys.date, morning!`

Este es un ejemplo simple del comando `cxcli intent create`:

```sh
cxcli intent create test_intent --training-phrases "hello, hi how are you today@sys.date, morning"  --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
```

El comando anterior te proporcionará un output como este:
```sh
$ cxcli intent create test_intent --training-phrases "hello, hi how are you today@sys.date, morning"  --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
INFO Intent created with id: projects/test-cx-346408/locations/us-central1/agents/40278ea0-c0fc-4d9a-a4d4-caa68d86295f/intents/a7870357-e942-43dd-99d2-4de8c81a3c09 
```

Puedes observar el `test_intent` en la Dialogflow CX Console:

![Full-width image](/assets/img/blog/tutorials/dialogflow-intents/console-intent-created.png){:.lead data-width="800" data-height="100"}
test_intent
{:.figure}

### Eliminar

Asimismo, puedes [eliminar](https://cxcli.xavidop.me/intents/delete) un intent. TEl uso de este comando es bastante similar al utilizado para crear un intent:

```sh
cxcli intent delete [intent-name] [parameters]
```

Puedes consultar el uso completo del comando [aquí](https://cxcli.xavidop.me/cmd/cxcli_intent_delete). Este es un ejemplo simple del comando `cxcli intent delete`:

```sh
cxcli intent delete test_intent --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
```

El comando anterior te proporcionará un output como este: 

```sh
$ cxcli intent delete test_intent --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
INFO Intent deleted                 
```
                        
## Recursos

Si deseas comprobar el uso completo del comando `cxcli intent`, puedes consultar esta [página](https://cxcli.xavidop.me/cmd/cxcli_intent).

Si deseas saber más sobre intents en Dialogflow CX, consulta la [documentación oficial](https://cloud.google.com/dialogflow/cx/docs/concept/intent).

## Conclusion 

Este es un tutorial básico para aprender qué es un Intent en Dialogflow CX. Como hemos visto en este ejemplo, es muy sencillo crear intents y evolucionar tu NLU en Dialogflow CX, ya sea mediante la consola o la `cxcli`. 

Espero que este tutorial te resulte útil. 

¡Eso es todo, amigos! 

Happy coding! 