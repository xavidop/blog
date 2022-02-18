---
layout: post
title: Contextual Design en una Google Action
description: >
  Ejemplo práctico de como implementar Contextual Design en Google Actions
image: /assets/img/blog/post-headers/google-action-contextual-design.jpeg
comments: true
author: xavi
kate: hl markdown;
categories: [aog]
tags:
  - aog
keywords:
  - aog
  - google assistant
  - google actions
  - actions on google
  - firebase
  - google cloud
  - gcp

lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

# Contextual Design en Google Actions

Una de las tareas más complejas al diseñar una conversación es crear interacciones naturales con nuestros usuarios. Hay un proceso que nos ayuda a conseguir ese tipo de interacciones. Este proceso se llama diseño contextual. Con el diseño contextual, podemos diseñar nuestra conversación dependiendo de la situación actual de nuestros usuarios. Por ejemplo, si el usuario es la primera vez que utiliza nuestra Google Action, le enviaremos un mensaje de bienvenida diferente que si accede por segunda vez. Otro ejemplo es el siguiente: si el usuario es de una Ciudad, proporcionaremos información relacionada con esa ciudad accediendo a la geolocalización. El diseño contextual es una de las claves de la Conversational AI.

En este artículo, aprenderemos cómo crear conversaciones atractivas utilizando el diseño contextual en nuestra Google Action.

## Requisitios Previos

Aquí tienes las tecnologías utilizadas en este proyecto
1. Google Action Developer Account - [How to get it](https://console.actions.google.com/)
2. Google Cloud Account - [Sign up here for free](https://cloud.google.com/)
3. Firebase Account - [Sign up here for free](https://firebase.google.com/)
4. gactions CLI - [Install and configure gactions CLI](https://github.com/actions-on-google/gactions)
5. Firebase CLI - [Install and configure Firebase CLI](https://firebase.google.com/docs/cli)
6. Node.js v10.x
7. Visual Studio Code
8. yarn Package Manager
9. Google Action SDK for Node.js (Version >3.0.0)

La CLI de Google Actions (gactions CLI) es una herramienta que nos permite administrar nuestras Google Actions y sus recursos relacionados, como las Firebase Cloud Functions.
Usaremos esta herramienta para crear, desplegar y administrar nuestro ejemplo. ¡Empecemos!

## Caso de Uso

El escenario que queremos crear es cuando un usuario solicita ayuda mientras usa nuestra Google Action. ¿Cómo?
1. Primero, vamos a tener una intent global llamado `HelpIntent` que se activará cuando accedamos a nuestra Google Action o cuando no estemos en ninguna Escena que tenga una parte de `Intent Handling` que maneje este mismo intent (`HelpIntent`). En este caso, daremos una ayuda gnérica.
2. En segundo lugar, gracias a la parte de `Intent Handling` de las Escenas en Google Actions, agregaremos un controlador para el intent `HelpIntent` para proporcionar información específica. En este ejemplo, daremos una ayuda específica relacionado con la Escena.

## Cómo implementar Diseño Contextual en nuestras Google Actions

Lo primero que vamos a hacer es crear nuestro `HelpIntent` y configurarlo como global:

~~~yaml
    trainingPhrases:
    - I need support
    - I need Help
    - support
    - help me
    - help
~~~

Este custom intent se ubicará en la carpeta `sdk/custom/intents`. Así es como se visualiza en la Google Action Developer Console:

![Full-width image](/assets/img/blog/tutorials/google-action-contextual-design/global-getinfoscene.png){:.lead data-width="800" data-height="100"}
Help intent
{:.figure}


### Global Handling de un Intent

Como hemos creado nuestro `HelpIntent` global, podemos crear un deep-link global a este intent y asi, siempre que se ejecute, proporcionaremos una ayuda global a nuestros usuarios:

Este deep-link global se encuentra debajo de `sdk/custom/global`:

~~~yaml
    handler:
    staticPrompt:
        candidates:
        - promptResponse:
            firstSimple:
            variants:
            - speech: You can ask me about the evolutions of your favourite pokemon
                  or just information of any pokemon.

~~~
Así es como se ve en Google Action Developer Console:
![Full-width image](/assets/img/blog/tutorials/google-action-contextual-design/globalhelphandling.png){:.lead data-width="800" data-height="100"}
Global Help Handling
{:.figure}

¿Cuándo se activará este deep-link?
1. Con interacción de tipo **one-shot invocation**. Como si el usuario dijera algo como "Ok Google, habla con <invocation-name> y pídele <HelpIntent Utterance>".
2. Cuando se activa el intent `HelpIntent` y la Escena actual no tiene ninguna sección de `Intent Handling`.

### Intent Handling dentro de una Escene

Entonces, ¿qué sucede si queremos agregar alguna ayuda específica cuando estamos solicitando información, por ejemplo en nuestro caso, sobre un pokemon? para eso, vamos a utilizar la sección Manejo de intents o `Intent Handling` de las Escenas de las Google Actions. En nuestro caso, usaremos la Escena llamada `GetInfoScene`. Esta escena se ejecuta cada vez que nuestros usuarios solicitan información sobre algún pokemon específico.

Echemos un vistazo a su código:

~~~yaml
    intentEvents:
    - handler:
        staticPrompt:
        candidates:
        - promptResponse:
            firstSimple:
                variants:
                - speech: You can ask me for the information of any pokemon,
                     for example, about Pikachu.
    intent: HelpIntent
    onSlotUpdated:
    webhookHandler: GetInfoHandler
    slots:
    - name: pokemon
    required: true
    type:
        name: pokemon
~~~

Como podemos ver arriba, en la sección `intentEvents`, que es la sección de Manejo de intents de nuestra escena, estamos interceptando nuestro intent `HelpIntent` y estamos proporcionando un mensaje específico a nuestros usuarios.

Así es como se ve en la Google Action Developer Console:

![Full-width image](/assets/img/blog/tutorials/google-action-contextual-design/helpinfoscene.png){:.lead data-width="800" data-height="100"}
intent Handling en GetInfoScene
{:.figure}

En los ejemplos anteriores, enviamos el mensaje a nuestros usuarios directamente desde las escenas o el deep-link del intent global pero también podemos llamar a nuestro webhook en Firebase si quisiéramos.

Además, es una buena práctica tener múltiples variantes de nuestros mensajes para tener una rica experiencia conversacional.

### Resultado

Teniendo todo desarrollado, este será el resultado final. En primer lugar, cuando entremos en nuestra Google Action obtendremos una ayuda genérica:

![Full-width image](/assets/img/blog/tutorials/google-action-contextual-design/globalhelp.png){:.lead data-width="800" data-height="100"}
Ayuda genérica
{:.figure}

Y esta será la ayuda que vamos a recibir cuando estemos pidiendo información sobre un pokemon:

![Full-width image](/assets/img/blog/tutorials/google-action-contextual-design/specifichelp.png){:.lead data-width="800" data-height="100"}
Ayuda específica
{:.figure}


## Recursos
* [Official Google Assistant Node.js SDK](https://github.com/actions-on-google/assistant-conversation-nodejs) - Official Google Assistant Node.js SDK
* [Official Google Assistant Documentation](https://developers.google.com/assistant/conversational/overview) - Official Google Assistant Documentation


## Conclusión 

Este fue un tutorial básico para aprender a crear un diseño contextual en nuestras Google Actions.
Como ha visto en este ejemplo, el SDK de Google Actions nos ayuda mucho mientras desarrollamos nuestras Google Actions.

Espero que este proyecto de ejemplo os sea de utilidad.

Puedes encontrar el código [aquí](https://github.com/xavidop/google-action-pokedex).

¡Eso es todo amigos!

Happy coding!