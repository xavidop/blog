---
layout: post
title: Desarrollo local de una Google Action con Firebase Cloud Functions
description: >
  Cómo crear una Google action usando la gactions CLI y NodeJS
image: /assets/img/blog/post-headers/google-action-local-debugging.png
noindex: true
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

# Local Debugging de una Google Action

Las Google Actions se pueden desarrollar utilizando Firebase Cloud functions o un API REST endpoint.
La Firebase Cloud function es la implementación de Google de funciones serverless disponibles en Firebase.
Google recomienda usar las Firebase Cloud functions para el desarrollo de Google Actions.
 
Este es un enfoque muy liviano y potente para desarrollar nuestra Google Action. Sin embargo, es complejo trabajar localmente con funciones serverles como las de Firebase Cloud Functions.

En este artículo, aprenderemos cómo desarrollar nuestra Google Action localmente invocando nuestra Firebase Cloud Functions localmente.

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

También usaremos Firebase CLI para invocar nuestra Firebase Cloud Function de forma local.

## Estructura del Proyecto

Estos son los archivos principales del proyecto:

~~~bash
├── firebase.json
├── package.json
├── .vscode
│   └── launch.json
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
* `firebase.json`: configuración de Firebase para depuración local.
* `.vscode`:
  * `launch.json`: Configuración de VS Code para ejecutar nuestra función Firebase localmente.
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


## Desarrollando la Google Action con Visual Studio Code

Dentro del `package.json` principal (el que se encuentra en la carpeta raíz), encontraremos todas las `devDependencies` y los scripts que nos ayudarán a hacer el linting de nuestro código y ejecutar nuestra Firebase Cloud Function localmente.

Así es como se ve este archivo:

~~~json

  {  
    "name": "google-action-pokemundo",
    "version": "1.0.0",
    "private": true,
    "description": "Google Action Pokemundo.",
    "engines": {
      "node": ">=10"
    },
    "scripts": {
      "lint": "eslint \"**/*.js\"",
      "lint:fix": "eslint --fix \"**/*.js\"",
      "local": "firebase emulators:start --inspect-functions"
    },
    "devDependencies": {
      "eslint": "^5.2.0",
      "eslint-config-google": "^0.9.1"
    }
  }

~~~

Para instalar todos los paquetes y los paquetes de los que dependen.
~~~bash

  yarn install

~~~

### Poniendo a punto nuestro código. Checkeando el estilo (linting).

Para checkear el estilo del código de nuestra Firebase Cloud Function de nuestra Google Action, solo necesitamos ejecutar este comando:

~~~bash
  yarn lint
~~~

La mayoría de los problemas que veremos se pueden solucionar automáticamente. Para eso, podemos usar este comando:

~~~bash
  yarn lint:fix
~~~

### Ejecutando nuestra Firebase Cloud Function localmente

Para ejecutar nuestra Firebase Cloud Function de forma local, necesitaremos configurar el archivo `firebase.json` en nuestra carpeta raíz:

~~~json
    {
        "functions": {
            "source": "sdk/webhooks/ActionsOnGoogleFulfillment"
        },
        "emulators": {
            "functions": {
                "port": 5001
            }
        }
    }
~~~

Este archivo configura el emulador de Firebase para nuestra Firebase Cloud Function:
1. Primero, especificamos que nuestro código fuente está en la carpeta `sdk/webhooks/ ctionsOnGoogleFulfillment`.
2. Luego, configuramos el puerto del emulador en el 5001. Este puerto se utilizará para escuchar las llamadas entrantes del webhook.

Una vez que tenemos el archivo `firebase.yaml` configurado correctamente, podemos ejecutar el siguiente comando:

~~~bash
    firebase emulators:start --inspect-functions
~~~

En este proyecto, he creado un script de yarn que ejecuta el comando anterior para hacerlo más simple. Entonces, podemos ejecutar:
~~~bash
    yarn local
~~~

Esta es la salida de la consola:
~~~bash
    ➜  google-action-pokemundo git:(master) ✗ yarn local
    yarn run v1.22.17
    $ firebase emulators:start --inspect-functions
    i  emulators: Starting emulators: functions
    ⚠  functions: You are running the functions emulator in debug mode (port=9229). This means that functions will execute in sequence rather than in parallel.
    ⚠  functions: The following emulators are not running, calls to these services from the Functions emulator will affect production: auth, firestore, database, hosting, pubsub, storage
    ⚠  Your requested "node" version ">=10" doesn't match your global version "16"
    ⚠  ui: Emulator UI unable to start on port 4000, starting on 4001 instead.
    i  ui: Emulator UI logging to ui-debug.log
    i  functions: Watching "/Users/xavierportillaedo/Documents/personal/repos/google-action-pokemundo/sdk/webhooks/ActionsOnGoogleFulfillment" for Cloud Functions...
    >  Debugger listening on ws://localhost:9229/15a86e20-e7f1-4fc8-a346-c304b1054e7d
    >  Debugger listening on ws://localhost:9229/15a86e20-e7f1-4fc8-a346-c304b1054e7d
    >  For help, see: https://nodejs.org/en/docs/inspector
    ✔  functions[us-central1-ActionsOnGoogleFulfillment]: http function initialized (http://localhost:5001/action-pokemundo/us-central1/ActionsOnGoogleFulfillment).

    ┌─────────────────────────────────────────────────────────────┐
    │ ✔  All emulators ready! It is now safe to connect your app. │
    │ i  View Emulator UI at http://localhost:4001                │
    └─────────────────────────────────────────────────────────────┘

    ┌───────────┬────────────────┬─────────────────────────────────┐
    │ Emulator  │ Host:Port      │ View in Emulator UI             │
    ├───────────┼────────────────┼─────────────────────────────────┤
    │ Functions │ localhost:5001 │ http://localhost:4001/functions │
    └───────────┴────────────────┴─────────────────────────────────┘
    Emulator Hub running at localhost:4400
    Other reserved ports: 4500

    Issues? Report them at https://github.com/firebase/firebase-tools/issues and attach the *-debug.log files.
    

~~~
**NOTA:** asegúrate de especificar nuestro proyecto actual en el que estamos trabajando ejecutando `firebase use <YOUR_PROJECT_ID>`

Puede acceder a la UI del emulador de Firebase localmente aquí: `http://localhost:4001/`:

![Full-width image](/assets/img/blog/tutorials/google-action-local-debugging/firebase-simulator.png){:.lead data-width="800" data-height="100"}
Fireabse Emulator
{:.figure}



### Añadiendo el debugger

El paso anterior simplemente ejecuta la Firebase Cloud Function de forma local. Esto no es suficiente, necesitaremos linkarnos al proceso de node para poder configurar puntos de interrupción e inspeccionar el código Javascript.

El archivo `launch.json` en la carpeta `.vscode` tiene la configuración para Visual Studio Code que nos permite linkarnos al proceso de node:

~~~json

    {
        "configurations": [
            {
                "type": "node",
                "request": "attach",
                "name": "Attach",
                "port": 9229 
            }
        ]
    }

~~~

Cuando ejecutamos el archivo de configuración de VS Code, veremos esta salida en la consola:

~~~bash
    >  Debugger attached.    
~~~

Esta configuración utiliza el puerto de debugging de node estándar `9229` para linkarnos el proceso e interceptar las llamadas e inspeccionar el código.

Después de configurar nuestro archivo launch.json y comprender cómo funciona el depurador local, es hora de hacer clic en el botón de play:

![Full-width image](/assets/img/blog/tutorials/google-action-local-debugging/run.png){:.lead data-width="800" data-height="100"}
Ejecutando el Fireabse Emulator
{:.figure}

A partir de ahora, podemos realizar una solicitud a nuestra Firebase Cloud Function localmente: `http://localhost:5001/action-pokemundo/us-central1/ActionsOnGoogleFulfillment`

## Testeando requests localmente


Estoy seguro de que ya conoces la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios. Aunque REST se ha vuelto omnipresente, no siempre es fácil probarlo. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir APIs, lo que te ayudará a ti y a tu equipo a ser más productivos a largo plazo.

Después de ejecutar tu aplicación, tendrás un endpoint disponible en `http://localhost:5001/action-pokemundo/us-central1/ActionsOnGoogleFulfillment`. Con Postman puedes emular cualquier request de tu Google Action.


## Testeando requests directamente desde Google Assistant

`ngrok` es una herramienta genial y liviana que crea un túnel seguro en tu máquina local junto con una URL pública que se puede usar para navegar por tu web en local o API.

Cuando se está ejecutando ngrok, escucha en el mismo puerto en el que se está ejecutando el servidor web local y envía solicitudes externas a tu máquina local.

Veamos como de fácil es publicar nuestra Google Action ejecutandose en local para que el cloud de Google Assistant nos envíe requests. 
Digamos que está ejecutando tu servidor web local en el puerto 5001. En la terminal, escribiría: `ngrok http 5001`. Esto comienza a escuchar a ngrok en el puerto 5001 y crea el túnel seguro:

![Full-width image](/assets/img/blog/tutorials/google-action-local-debugging/tunnel.png){:.lead data-width="800" data-height="100"}
NGROK
{:.figure}

Así que ahora tenemos que ir a la [Google Action Developer console](https://console.actions.google.com/), vayamos a nuestra Google Action> Test Tab> settings, agregue la URL https generada anteriormente. P.ej: `https://d424-83-138-195-117.ngrok.io:5001/action-pokemundo/us-central1/ActionsOnGoogleFulfillment`.

La Google Action Developer Console enviará una solicitud HTTPS al endpoint de ngrok(https://d424-83-138-195-117.ngrok.io:5001/action-pokemundo/us-central1/ActionsOnGoogleFulfillment) que lo enrutará a tu Google Action que se ejecuta en tu ordenador en `http://localhost:5001/action-pokemundo/us-central1/ActionsOnGoogleFulfillment`.


![Full-width image](/assets/img/blog/tutorials/google-action-local-debugging/console.png){:.lead data-width="800" data-height="100"}
Google Action Console. Test tab.
{:.figure}



## Debugeando la Google Action con Visual Studio Code

Siguiendo los pasos anteriores, ahora podemos configurar puntos de interrupción donde queramos dentro de todos los archivos JS para depurar nuestra Google Action:
![Full-width image](/assets/img/blog/tutorials/google-action-local-debugging/debug.png){:.lead data-width="800" data-height="100"}
Debuggeando nuestra Google Action localmente.
{:.figure}


## Recursos
* [Official Google Assistant Node.js SDK](https://github.com/actions-on-google/assistant-conversation-nodejs) - Official Google Assistant Node.js SDK
* [Official Google Assistant Documentation](https://developers.google.com/assistant/conversational/overview) - Official Google Assistant Documentation


## Conclusión 

Este fue un tutorial básico para aprender a desarrollar Google Actions localmente.
Como hemos visto en este ejemplo, la gactions CLI y la firebase CLI pueden ayudarnos durante el proceso de desarrollo.

Espero que este proyecto de ejemplo os sea de utilidad.

Puedes encontrar el código [aquí](https://github.com/xavidop/google-action-pokedex).

¡Eso es todo amigos!

Happy coding!
