---
layout: post
title: Agentes en Dialogflow CX
description: >
  Una introducción a los agentes de dialogflow CX y cómo interactuar con ellos
  usando la consola y la CXCLI
image: /assets/img/blog/post-headers/dialogflow-agents.jpg
comments: true
author: xavi
kate: hl markdown;
categories:
  - dialogflow
tags:
  - dialogflow
keywords:
  - dialogflow
  - agent
  - dialogflowcx
  - dialogflow cx
  - cxcli
  - conversationalai

lang: en
lastmod: 2023-02-07T08:36:45.795Z
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

# Agentes en Dialogflow CX

## Requisitos previos 

Estas son las tecnologías utilizadas en este proyecto 
1. Google Cloud Account - [Regístrate aquí de forma gratuita](https://cloud.google.com/)
2. Dialogflow API enabled - [Cómo habilitarla](https://cloud.google.com/dialogflow/cx/docs/reference)
3. Dialogflow CX CLI - [Instala y configura Dialogflow CX CLI](https://cxcli.xavidop.me/)

## ¿De qué se trata? 

En Dialogflow CX, un agente es la entidad que maneja todas las conversaciones que hemos definido en la consola de Dialogflow CX. 

Un agente es básicamente un asistente que gestiona el estado de la conversación de cada usuario cuando interactúan con el agente a través de texto o audio en múltiples canales. 

## Dialogflow Console

Dialogflow CX Console es una interfaz web que permite diseñar tus conversaciones creando agentes, así como dentro de un agente, creando flows, intents, entity types, etc. En la consola de Dialogflow puedes crear e interactuar fácilmente con tus agentes. Para ello, solo necesitas acceder a la consola de Dialogflow CX: [https://dialogflow.cloud.google.com/cx](https://dialogflow.cloud.google.com/cx). This is what it looks like:

![Full-width image](/assets/img/blog/tutorials/dialogflow-agents/console.png){:.lead data-width="800" data-height="100"}
Dialogflow CX Console
{:.figure}

Una vez creado un agente, ¡ya puedes empezar a crear conversaciones! Lo que puedes hacer en la consola es: 
1. Exportar un agente: en formato blob o JSON 
2. Eliminar un agente 
3. Crear componentes conversacionales como flows o pages 
4. Modificar tu NLU creando intents y entity types 
5. Testear tu agente 

![Full-width image](/assets/img/blog/tutorials/dialogflow-agents/agent.png){:.lead data-width="800" data-height="100"}
Agente en Dialogflow CX
{:.figure}

## Dialogflow CX CLI

La [Dialogflow CX CLI](https://cxcli.xavidop.me/) o `cxcli` ies una herramienta de línea de comandos que puedes utilizar para interactuar con tus proyectos en Dialogflow CX en un terminal. Es un proyecto de código abierto creado por [Xavier Portilla Edo](https://xavidop.me/). Con la `cxcli` ypuedes interactuar fácilmente con tus agentes en Dialogflow CX.

Todos los comandos disponibles en la `cxcli` para interactuar con tus agentes se encuentran en el subcomando `cxcli agent`.

### Restaurar

Puedes [restaurar](https://cxcli.xavidop.me/agents/restore) un agente utilizando un archivo `blob`. Ahora mismo, la API de Dialogflow CX que utiliza la `cxcli` funciona solamente con el formato `blob`. 

La `cxcli` cuenta con un comando que permite restaurar un agente. 

Este es un ejemplo del comando `cxcli agent restore`: 

```sh
cxcli agent restore test-agent --project-id test-cx-346408 --location-id us-central1 --input agent.blob
```

El comando anterior te proporcionará un output como este:

```sh
$ cxcli agent restore test-agent --project-id test-cx-346408 --location-id us-central1 --input agent.blob
INFO Agent restored 
```

### Exportar

Asimismo, puedes [exportar](https://cxcli.xavidop.me/agents/export) un agente como un archivo `blob`. Ahora mismo, la API de Dialogflow CX que utiliza la `cxcli` funciona solamente en formato `blob`. 

La `cxcli` cuenta con un comando que permite restaurar un agente. 

Este es un ejemplo simple del comando `cxcli agent restore`: 

```sh
cxcli agent export test-agent --project-id test-cx-346408 --location-id us-central1
```

El comando anterior te proporcionará un output como este:

```sh
$ cxcli agent export test-agent --project-id test-cx-346408 --location-id us-central1
INFO Agent exported to file: agent.blob                    
```

### Eliminar

La `cxcli` cuenta con un comando que permite [eliminar](https://cxcli.xavidop.me/agents/delete) un agente.

A continuación, tenemos un ejemplo del comando `cxcli agent delete`: 
```sh
cxcli agent delete test-agent --project-id test-cx-346408 --location-id us-central1
```

El comando anterior te proporcionará un output como este:

```sh
$ cxcli agent delete test-agent --project-id test-cx-346408 --location-id us-central1
INFO Agent deleted                          
```

## Recursos

Si deseas ver el uso completo del comando `cxcli agent`, puedes consultar esta [página](https://cxcli.xavidop.me/cmd/cxcli_agent).

Si deseas saber más sobre agentes en Dialogflow CX, consulta la [documentación oficial](https://cloud.google.com/dialogflow/cx/docs/concept/agent).

## Conclusión  

Este es un tutorial básico para aprender qué es un Agente en Dialogflow CX. Como hemos visto en este ejemplo, es muy sencillo crear un agente e interactuar con él, ya sea mediante la consola o la cxcli.

Espero que este tutorial te resulte útil.

¡Eso es todo, amigos!

Happy coding!