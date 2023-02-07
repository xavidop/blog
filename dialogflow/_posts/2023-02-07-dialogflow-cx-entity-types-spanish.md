---
layout: post
title: Entity Types en Dialogflow CX
description: >
  Descubre qué es una entity type en Dialogflow CX y lo sencillo que es crear
  entity types y hacer evolucionar tu NLU en Dialogflow CX.
image: /assets/img/blog/post-headers/dialogflow-entity-types.jpg
comments: true
author: xavi
kate: hl markdown;
categories:
  - dialogflow
tags:
  - dialogflow
keywords:
  - dialogflow
  - dialogflowcx
  - dialogflow cx
  - entity type
  - intent
  - cxcli
  - conversationalai

lang: en
lastmod: 2023-02-07T08:36:19.792Z
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

# Entity Types en Dialogflow CX

## Requisitos previos 

Estas son las tecnologías utilizadas en este proyecto 
1. Google Cloud Account - [Regístrate aquí de forma gratuita](https://cloud.google.com/)
2. Dialogflow API enabled - [Cómo habilitarla](https://cloud.google.com/dialogflow/cx/docs/reference)
3. Dialogflow CX CLI - [Instala y configura Dialogflow CX CLI](https://cxcli.xavidop.me/)

## ¿Qué son las Entity Types?

![Full-width image](/assets/img/blog/tutorials/dialogflow-entity-types/entity-type.png){:.lead data-width="800" data-height="100"}
Entity Type
{:.figure}

Una de las partes más importantes del NLU son las entity types, o entities. Constituyen la información clave de un texto: nombres, fechas, productos, organizaciones, lugares o cualquier elemento que queramos extraer del texto. A este tipo de información lo llamamos “entities” (entidades). Por ejemplo, observemos el intent `order_intent`:
1. Quiero una pizza.
2. Quiero 3 colas
3. Dame 2 hamburguesas.

Como podemos ver en el ejemplo anterior, se pueden extraer 2 entity types: `quantity` y `order_type`. Podemos extrapolar los utterances anteriores de la siguiente forma:
1. Quiero {quantity} {order_type}
2. Dame {quantity} {order_type}

También podemos pensar en las entity types como variables.

Una buena práctica consiste en testear las frases de entrenamiento con los usuarios finales. Esto te permitirá detectar las frases de entrenamiento que faltan en tu NLU.

## Dialogflow Console

Dialogflow Console es una interfaz web donde puedes diseñar tus conversaciones creando agentes y, dentro de un agente, crear flows, intents, entity types, etc. En la consola de Dialogflow es posible crear Entity Types e interactuar fácilmente con ellos. Para ello, basta con acceder a la URL: [https://dialogflow.cloud.google.com/cx](https://dialogflow.cloud.google.com/cx). Este es su aspecto:

![Full-width image](/assets/img/blog/tutorials/dialogflow-agents/console.png){:.lead data-width="800" data-height="100"}
Dialogflow CX Console
{:.figure}

Encontrarás tus entity types en la pestaña **Manage** al hacer clic en la sección **entity types**:

![Full-width image](/assets/img/blog/tutorials/dialogflow-entity-types/console-entity-type.png){:.lead data-width="800" data-height="100"}
Dialogflow CX Entity types
{:.figure}

Con la consola de Dialogflow CX, puedes: 
1. Crear una entity type: Cuando crees una entity type, puedes agregar sinónimos.
2. Eliminar una entity type.
3. Entrenar y validar tu NLU.

Al crear una entity type, puedes especificar si esta tiene o no sinónimos, o si es una entity del tipo regexp. Si eliges la opción regexp, el NLU utilizará una expresión regular en lugar de sinónimos para extraer la información. 

Estas son las entity types que puedes utilizar en tus intents: 
1. Custom entities: Entity types creadas por el desarrollador.
2. System entities: Aquellas que están disponibles en Dialogflow CX (números, fechas, colores, etc.).
3. Session entities: Se trata de entities dinámicas que pueden ampliarse durante las sesiones de los usuarios.
4. Regexp entities: Entities que corresponden a expresiones regulares.

Siempre que crees, modifiques o elimines una entity type, es importante que vuelvas a entrenar tus flows en Dialogflow CX. Esto volverá a entrenar tu NLU, y así tu bot “entenderá” cómo interactúas con él, así como los últimos cambios que hayas realizado. 

## Dialogflow CX CLI

La [Dialogflow CX CLI](https://cxcli.xavidop.me/) o `cxcli` ies una herramienta de línea de comandos que puedes utilizar para interactuar con tus proyectos en Dialogflow CX en un terminal. Es un proyecto de código abierto creado por [Xavier Portilla Edo](https://xavidop.me/). Con la `cxcli` y puedes interactuar fácilmente con tus entity types en Dialogflow CX.

Todos los comandos disponibles en la `cxcli` para interactuar con tus entity types se encuentran en el subcomando `cxcli entity-type`.

### Crear

Puedes [crear](https://cxcli.xavidop.me/entitytypes/create) utilizando esta herramienta. Este comando se utiliza así: 

```sh
cxcli entity-type create [entity-type-name] [parameters]
```

Puedes consultar el uso completo [aquí](https://cxcli.xavidop.me/cmd/cxcli_entity-type_create). Es importante explicar el parámetro `--entities`. Se trata de una lista de las entities y sus sinónimos, que se encuentran separadas por comas. Este parámetro tiene el siguiente formato:
```
entity1@synonym1|synonym2,entity2@synonym1|synonym2
```

Aquí tienes un ejemplo: `pikachu@25|pika,charmander@3`


Este es un ejemplo simple del comando `cxcli entity-type create`:

```sh
cxcli entity-type create order_type --entities "pizza@piza|pizzas,burguer@hamburguer|burguers" --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
```

El comando anterior te proporcionará un output como este:

```sh
$ cxcli entity-type create order_type --entities "pizza@pizza|pizzas,coke@coke|cokes" --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
INFO Entity Type created with id: projects/test-cx-346408/locations/us-central1/agents/40278ea0-c0fc-4d9a-a4d4-caa68d86295f/entityTypes/457a451d-f5ce-47da-b8dc-16b17d874a5d 
```

Puedes observar la entity type `order_type` nn la Dialogflow CX Console también:

![Full-width image](/assets/img/blog/tutorials/dialogflow-entity-types/console-entity-type-created.png){:.lead data-width="800" data-height="100"}
order_type
{:.figure}

### Eliminar

Asimismo, puedes [eliminar](https://cxcli.xavidop.me/entitytypes/delete) una entity type. El uso de este comando es bastante similar al utilizado para crear una entity type:

```sh
cxcli entity-type delete [entity-type-name] [parameters]
```

Puedes consultar el uso completo [aquí](https://cxcli.xavidop.me/cmd/cxcli_entity-type_delete). Este es un ejemplo simple del comando `cxcli entity-type delete`:

```sh
cxcli entity-type delete pokemon --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
```

El comando anterior te proporcionará un output como este:

```sh
$ cxcli entity-type delete pokemon --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
INFO Entity Type deleted                 
```
                        
## Recursos

Si deseas comprobar el uso completo del comando `cxcli entity-type`, puedes consultar esta [página](https://cxcli.xavidop.me/cmd/cxcli_entity-type/).

Si deseas saber más sobre entity types en Dialogflow CX, consulta la [documentación oficial](https://cloud.google.com/dialogflow/cx/docs/concept/entity).

## Conclusión 

Este es un tutorial básico para aprender qué es una entity type en Dialogflow CX. Como hemos visto en este ejemplo, es muy sencillo crear entity types y evolucionar tu NLU en Dialogflow CX, ya sea mediante la consola o la cxcli. 

Espero que este tutorial te resulte útil. 

¡Eso es todo, amigos! 

Happy coding! 