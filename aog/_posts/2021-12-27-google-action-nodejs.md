---
layout: post
title: Crea una Google Action usando NodeJS
description: >
  Cómo crear una Google action usando la gactions CLI y NodeJS
image: /assets/img/blog/post-headers/google-action-nodejs.jpg
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

# Google Actions con Node.js

Las Google Actions se pueden desarrollar utilizando Firebase Cloud functions o un API REST endpoint.
La Firebase Cloud function es la implementación de Google de funciones serverless disponibles en Firebase.
Google recomienda usar las Firebase Cloud functions para el desarrollo de Google Actions.
 
En esta publicación, implementaremos una Google Action para el Asistente de Google usando Node.js, yarn y Firebase Cloud Functions. Esta Google Action es básicamente un ejemplo de un Hello World.

Esta publicación contiene materiales de diferentes recursos que se pueden ver en la sección Recursos.

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
10. ngrok
    
La CLI de Google Actions (gactions CLI) es una herramienta que nos permite administrar nuestras Google Actions y sus recursos relacionados, como las Firebase Cloud Functions.
Usaremos esta herramienta para crear, desplegar y administrar nuestro ejemplo de Hello World en una Google Action. ¡Empecemos!

## Creando la Google Action con la gactions CLI

Para crear la Google Action, utilizaremos la gactions CLI previamente configurada. En primer lugar, tenemos que ejecutar este comando:

~~~bash

    gactions init hello-world

~~~

Este comando debe ejecutarse en un directorio vacío.

Una vez que tengas tu código de la Google Action inicializado, tienes que ir a la [Google Action Developer Console](https://console.actions.google.com/) and create a new project:

![Full-width image](/assets/img/blog/tutorials/google-action-nodejs/creation.png){:.lead data-width="800" data-height="100"}
Creando una Google Action
{:.figure}


Una vez que hayas creado tu proyecto de la Google Action en la consola, debe obtener el ID del proyecto y poner ese valor en la propiedad `projectId` en el archivo `sdk/settings/settings.yaml`:


~~~yaml
category: GAMES_AND_TRIVIA
defaultLocale: en
localizedSettings:
  displayName: Hello world sample
  pronunciation: Hello world sample
projectId: action-helloworld # Tu Project ID aqui
~~~

**NOTA:** Podemos encontrar el ID del proyecto en la URL de la Google Action Developer Console al acceder a nuestra Google Action. La URL tendrá este formato: `https://console.actions.google.com/u/0/project/<YOUR-PROJECT-ID>/scenes/Start`. En mi caso será: `https://console.actions.google.com/u/0/project/action-helloworld/scenes/Start`

And that's it, with these steps you have created your first Google Action and linked to your source code locally using the gactions CLI. You only have to deploy your local changes. We are going to explain it in the next steps.

## Estructura del Proyecto

Estos son los archivos principales del proyecto:

~~~bash

└── sdk
    ├── actions
    │   └── actions.yaml
    ├── custom
    │   ├── global
    │   ├── intents
    │   ├── scenes
    │   └── types
    ├── manifest.yaml
    ├── settings
    │   └── settings.yaml
    └── webhooks
        ├── ActionsOnGoogleFulfillment
        │   ├── index.js
        │   └── package.json
        └── ActionsOnGoogleFulfillment.yaml

~~~

* `package.json`: archivo raíz para ejecutar el debug y el linting local.
* `sdk`: La carpeta principal del proyecto. Aquí ejecutaremos todos los comandos de la gactions CLI.
  * `actions`:
    * `actions.yaml`: archivo que contiene algunos metadatos de la Google Action, como el Assistant Link.
  * `custom`: En esta carpeta, vamos a especificar nuestro modelo de interacción y el flujo de conversación.
    * `global`: En esta carpeta, encontraremos todas las intenciones que se pueden activar en cualquier momento ya que son globales.
    * `intents`: Intents o intenciones (en español) definidos por nosotros. Cada intent tendrá una lista de expresiones o enunciados que el Asistente de Google usará para entrenar su IA.
    * `scenes`: Las diferentes escenas de nuestra Google Action. Usaremos escenas para gestionar el flujo de nuestra conversación.
    * `types`: los tipos/entidades que vamos a usar en nuestras intenciones/expresiones.
  * `settings`:
    * `settings.yaml`: este archivo contendrá todos los metadatos de nuestra Google Action, como descripción, logotipo, política de privacidad, ID del proyecto, etc.
  * `webhooks`: una carpeta que contiene el código fuente de la Firebase Cloud Function:
    * `ActionsOnGoogleFulfillment`: Carpeta con todo el código de Firebase Cloud Function.
      * `index.js`: el entry point principal de la Firebase Cloud Function.
      * `package.json`: este archivo es fundamental para el ecosistema Node.js y es una parte básica para trabajar con Node.js, npm/yarn e incluso JavaScript moderno.
    * `ActionsOnGoogleFulfillment.yaml`: Archivo que especifica los handlers y la carpeta del código fuente.

## Firebase Cloud function en Javascript

El SDK de Google Action para Node.js nos facilita la creación de Google Actions al permitirnos dedicar más tiempo a implementar funciones y menos tiempo a escribir código repetitivo.

Puedes encontrar documentación, ejempls y enlaces útiles en su web oficial: [GitHub](https://github.com/actions-on-google)

El archivo Javascript principal en nuestro proyecto de Firebase Cloud Function es el `index.js` ubicado en la carpeta `sdk/webhooks/ActionsOnGoogleFulfillment`. Este archivo contiene todos los controladores y exporta el objeto principal de nuestra Google Action en `exports.ActionsOnGoogleFulfillment`.

La función `exports.ActionsOnGoogleFulfillment` se ejecuta cada vez que se llama al webhook desde nuestra Google Action.

~~~javascript

    const {conversation} = require('@assistant/conversation');
    const functions = require('firebase-functions');

    const app = conversation({debug: true});

    app.handle('start_scene_initial_prompt', (conv) => {
        console.log('Start scene: initial prompt');
        conv.overwrite = false;
        conv.scene.next.name = 'actions.scene.END_CONVERSATION';
        conv.add('Hello world from fulfillment');
    });

    exports.ActionsOnGoogleFulfillment = functions.https.onRequest(app);

~~~

Es importante echar un vistazo al controlador `start_scene_initial_prompt` como un ejemplo del controlador de Google Action escrito en Node.js:

~~~javascript

    app.handle('start_scene_initial_prompt', (conv) => {
        console.log('Start scene: initial prompt');
        conv.overwrite = false;
        conv.scene.next.name = 'actions.scene.END_CONVERSATION';
        conv.add('Hello world from fulfillment');
    });

~~~

**NOTA:** Cada vez que agreguemos un nuevo controlador, debemos especificarlo en el archivo `sdk/webhooks/ActionsOnGoogleFulfillment.yaml`.

## Desplegando nuestra Google Action

Con el código listo para funcionar, debemos desplegarlo en Firebase y en la Google Action Developer Console para que pueda conectarse al Asistente de Google.

En este punto podemos desplegar nuestra Google Action con la gactions CLI desde la carpeta `sdk`:

~~~bash
    gactions push
~~~

Este comando realizará las siguientes tareas:

1. Desplegará todos los metadatos, el modelo de interacción, los ajustes y las configuraciones de nuestra Google Action en la Google Actions Developer Console.
2. Desplegará el código de nuestra Cloud Function en Firebase.

Después de el comando anterior, tenemos que ejecutar este comando:
~~~bash
    gactions deploy preview
~~~

Este comando desplegará todo en el stage "preview" de nuestra Google Action. Listo para ser probado.

## Testeadno nuestra Google Action

Una vez que hayamos desplegado nuestros cambios, podemos ir a nuestro proyecto de la Google Action en la Google Action Developer Console y probarlo:

![Full-width image](/assets/img/blog/tutorials/google-action-nodejs/testing.png){:.lead data-width="800" data-height="100"}
Google Action Simulator
{:.figure}


## Descagando nuestro código de la Google Action Console

Cada vez que realizamos un cambio en la Google Action Console, podemos descargarlos ejecutando este comando:

~~~bash
    gactions pull
~~~

O si queremos sobrescribir nuestros cambios locales, podemos ejecutar este comando:
~~~bash
    gactions pull --force
~~~

## Recursos
* [Official Google Assistant Node.js SDK](https://github.com/actions-on-google/assistant-conversation-nodejs) - Official Google Assistant Node.js SDK
* [Official Google Assistant Documentation](https://developers.google.com/assistant/conversational/overview) - Official Google Assistant Documentation

## Conclusión 

Este fue un tutorial básico para aprender Google Actions usando Node.js.
Como has visto en este ejemplo, el SDK de Google Action para Node.js y las Herramientas de Google Actions como la gactions CLI nos pueden ayudar mucho y también nos dan la posibilidad de crear Google Actions fácilmente.

Espero que este proyecto de ejemplo os sea de utilidad.

Puedes encontrar el código [aquí](https://github.com/xavidop/google-action-nodejs-helloworld).

¡Eso es todo amigos!

Happy coding!