---
layout: post
title: Alexa Skill con Node.js
image: /assets/img/blog/post-headers/alexa-nodejs.jpg
description: >
   Alexa Skill desarrollada en Node.js usando Visual Studio Code
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - lambda
  - javascript
  - node
  - noodejs
  - howto
  - skill
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

Las Skills de Alexa se pueden desarrollar utilizando las funciones Lambda de AWS o un endpoint en una REST API.
La función Lambda es la implementación de Amazon de funciones serverless disponibles en AWS.
Amazon recomienda utilizar las funciones Lambda aunque no sean fáciles de debuggear y trackear.
Si bien puedes loggear en CloudWatch, no puedes poner puntos de ruptura una vez desplegada la Lambda e ir directamente al código. 

# Alexa Skill hecha con Node.js

Esto hace que el live debugging de las requests enviadas a Alexa sea una tarea muy difícil.
En este post, implementaremos una custom Skill para Amazon Alexa usando Node.js, npm y AWS Lambda Functions.
Esta Skill es básicamente un ejemplo de Hello World. 
Con este post, podras crear una custom Skill para Amazon Alexa, implementar la funcionalidad utilizando Node.js y ejecutar tu Skill tanto desde tu ordenador local como desde AWS.
Esta publicación contiene materiales de diferentes recursos que se pueden ver en la sección Recursos.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. Node.js v10.x
5. Visual Studio Code
6. npm Package Manager
7. Alexa ASK para Node.js (Version >2.7.0)
8. ngrok

La Alexa Skills Kit Command Line Interface (ASK CLI) es una herramienta para que puedas administrar tus Skills de Alexa y recursos relacionados, como las funciones de AWS Lambda.
Con la ASK CLI, tienes acceso a la Skill Management API, que te permite administrar las Skills de Alexa mediante programación desde la línea de comandos.
Utilizaremos esta poderosa herramienta para crear, construir, desplegar y gestionar nuestra Skill Hello World. 

¡Empecemos!

## Creando la Skill con ASK CLI

Para crear la Alexa Skill, vamos a usar la ASK CLI previamente configurada. Primero de todo, debemos ejecutar este comando:

~~~bash

    ask new

~~~
Este comando se ejecutará un proceso interactivo de creación paso a paso:

1. Lo primero que nos preguntará la ASK CLI es el runtime de nuestra Skill. En nuestro caso, `Node.js v10`:

  ![Full-width image](/assets/img/blog/tutorials/alexa-nodejs/runtime.png){:.lead data-width="800" data-height="100"}
Runtime
  {:.figure}

1. El segundo paso es el template de la Skill en la que se basará la nuestra.En nuestro caso, seleccionaremos el template `Hello World`:

  ![Full-width image](/assets/img/blog/tutorials/alexa-nodejs/template.png){:.lead data-width="800" data-height="100"}
Template
  {:.figure}


1. Finalmente, ASK CLI nos preguntará sobre el nombre de la Skill:

  ![Full-width image](/assets/img/blog/tutorials/alexa-nodejs/name.png){:.lead data-width="800" data-height="100"}
Nombre de la Skill
  {:.figure}


## Estructura del proyecto 

Estos son los archivos principales del proyecto:

~~~bash

    ├───.ask
    │       config
    │
    ├───.vscode
    │       launch.json
    ├───hooks
    ├───lambda
    │   └───custom
    │        ├───test
    │        │    └─── helloworld-tests.js
    │        └───src
    │             ├───errors
    │             ├───intents
    │             ├───interceptors
    │             ├─── utilities
    │             ├─── index.js
    │             ├─── local-debugger.js
    │             └─── package.json
    ├───models
    │       es-ES.json
    └───skill.json

~~~

* .ask: carpeta que contiene el archivo de configuración de ASK CLI. Este archivo de configuración permanecerá vacío hasta que ejecutemos el comando `ask deploy`
* `.vscode/launch.json`: Preferencias de ejecución para ejecutar localmente tu Skill para testing local. Esta configuración ejecuta `lambda/custom/local-debugger.js`. Este script ejecuta un servidor en http://localhost:3001 para debuggear la Skill.
* hooks: Una carpeta que contiene los hooks scripts. Amazon proporciona dos hooks, post_new_hook y pre_deploy_hook.
  * `post_new_hook`: ejecutado después de la creación de la Skill. En Node.js ejecuta `npm install` en el directorio especificado en el sourceDir del `skill.json`
  * `pre_deploy_hook`: ejecutado antes del despliegue de la Skill. En Node.js ejecuta `npm install` en el directorio especificado en el sourceDir del `skill.json` también.
* lambda/custom/src: Una carpeta que contiene el código fuente de la función AWS Lambda de la Skill:
  * `index.js`: El principal entry point de la función Lambda.
  * `utilities/languageStrings.js`: diccionarios i18n usados por la librería `i18next` que nos permite ejecutar nuestra Skill en diferentes lenguajes.
  * `package.json`: Este archivo es esencial para el ecosistema Node.js y es una parte básica para la comprensión y el trabajo con Node.js, npm e incluso JavaScript.
  * `utilities/util.js`: archivo con funciones útiles.
  * `local-debugger.js`: usado para el debug local de nuestra skill.
  * `errors`: Todos los Error handlers.
  * `intents`: Aquí encontrarás los Intent handlers.
  * `interceptors`: Los interceptors.
* lambda/custom/test/: Todos los test de la funcón lambda.
* models: Una carpeta que contiene los interactions models para nuestra Skill. Cada interaction model se define en un archivo JSON nombrado de acuerdo con la configuración regional. Por ejemplo, es-ES.json.
* `skill.json`: El skill manifest. Uno de los archivos más importantes de nuestro proyecto.


## Lambda function en Javascript

El SDK de ASK para Node.js te facilita el desarrollo de Skills de gran calidad al permitirte pasar más tiempo implementando funciones y menos tiempo escribiendo código repetitivo.

Puede encontrar documentación, ejemplos y enlaces útiles en su repositorio oficial de [GitHub](https://github.com/alexa/alexa-skills-kit-sdk-for-nodejs)

El archivo Javascript principal en nuestro proyecto lambda es `index.js` situado en la capreta `lambda/custom/src/`. Este fichero contiene todos los handlers, interceptors y exporta el Skill handler en `exports.handler`.

La función `exports.handler` se ejecuta cada vez que AWS Lambda es invocado por el cloud de Alexa.
En teoría, una función AWS Lambda es solo una función única. Esto significa que necesitamos definir la lógica para que una request a la función pueda enrutarse al código apropiado, de ahí los handlers.

~~~javascript

  /**
  * This handler acts as the entry point for your skill, routing all request and response
  * payloads to the handlers above. Make sure any new handlers or interceptors you've
  * defined are included below. The order matters - they're processed top to bottom 
  * */
  exports.handler = Alexa.SkillBuilders.custom()
      .addRequestHandlers(
          LaunchRequestHandler,
          HelloWorldIntentHandler,
          HelpIntentHandler,
          CancelAndStopIntentHandler,
          FallbackIntentHandler,
          SessionEndedRequestHandler,
          IntentReflectorHandler)
      .addErrorHandlers(
          ErrorHandler)
      .addRequestInterceptors(
          LocalisationRequestInterceptor)
      .lambda();

~~~
Es importante echar un vistazo al `LaunchRequestHandler` como un ejemplo de handler de Skills de Alexa escrito en Node.js:

~~~javascript

  const LaunchRequestHandler = {
      //Method that returns true if this handler can execute the current request
      canHandle(handlerInput) {
          return Alexa.getRequestType(handlerInput.requestEnvelope) === 'LaunchRequest';
      },
      //Method that will process the request if the method above returns true
      handle(handlerInput) {
          const speakOutput = handlerInput.t('WELCOME_MSG');

          return handlerInput.responseBuilder
              .speak(speakOutput)
              .reprompt(speakOutput)
              .getResponse();
      }
  };

~~~

## Construir la Skill con Visual Studio Code

Dentro del fichero `package.json`, casi siempre encontraremos metadatos específicos para el proyecto. 
Estos metadatos ayudan a identificar el proyecto y actúan como base para que los usuarios y contribuyentes obtengan información sobre el proyecto.

Así es como se ve este archivo:

~~~json

  {
    "name": "alexa-nodejs-lambda-helloworld",
    "version": "1.0.0",
    "description": "Alexa HelloWorld example with NodeJS",
    "main": "index.js",
    "scripts": {
      "test": "echo \"Error: no test specified\" && exit 1"
    },
    "repository": {
      "type": "git",
      "url": "https://github.com/xavidop/alexa-nodejs-lambda-helloworld.git"
    },
    "author": "Xavier Portilla Edo",
    "license": "Apache-2.0",
    "dependencies": {
      "ask-sdk-core": "^2.7.0",
      "ask-sdk-model": "^1.19.0",
      "aws-sdk": "^2.326.0",
      "i18next": "^15.0.5"
    }
  }

~~~

Con Javascript o Node.js, el término de compilación es un poco diferente. Para construir nuestra Skill, podemos ejecutar el siguiente comando:

~~~bash

  npm install

~~~

Este comando instala los paquetes y sus dependecias.
Si el paquete tiene el archivo package-lock, la instalación de dependencias será lelvada por él.

Podría ser la forma de construir nuestra Skill de Alexa.

## Ejecutar la Skill con Visual Studio Code

El fichero `launch.json` situado en la carpeta `.vscode` tiene la configuración para Visual Studio Code que nos permite ejecutar nuestro lambda localmente:

~~~json

  {
    "version": "0.2.0",
    "configurations": [
        {
            "type": "node",
            "request": "launch",
            "name": "Launch Skill",
            // Specify path to the downloaded local adapter(for Node.js) file
            "program": "${workspaceRoot}/lambda/custom/local-debugger.js",
            "args": [
                // port number on your local host where the alexa requests will be routed to
                "--portNumber", "3001",
                // name of your Node.js main skill file
                "--skillEntryFile", "${workspaceRoot}/lambda/custom/src/index.js",
                // name of your lambda handler
                "--lambdaHandler", "handler"
            ]
        }
    ]
}

~~~
Este archivo de configuración ejecutará el siguiente comando:

~~~bash

  node --inspect-brk=28448 lambda\custom\local-debugger.js --portNumber 3001 --skillEntryFile lambda/custom/src/index.js --lambdaHandler handler

~~~

Esta configuración utiliza el fichero `local-debugger.js` que corre un [servidor TCP](https://nodejs.org/api/net.html) escuchando en http://localhost:3001

Para una nueva request a la skill entrante se establece una nueva conexión al socket.
De los datos recibidos en el socket se extrae el cuerpo de la solicitud, se analiza en JSON y se pasa al lambdahandler de la Skill.
La respuesta del lambda handler es parseada como un formato de mensaje HTTP 200 como se especifica [aquí](https://developer.amazon.com/docs/custom-skills/request-and-response-json-reference.html#http-header-1). La respuesta se escribe en la conexión del socket y se devuelve.

Después de configurar nuestro archivo launch.json y comprender cómo funciona el local debugger, es hora de hacer clic en el botón play:


  ![Full-width image](/assets/img/blog/tutorials/alexa-nodejs/run.png){:.lead data-width="800" data-height="100"}
Ejecutar la Skill
  {:.figure}


Después de ejecutarlo, puedes enviar requests POST de Alexa a http://localhost:3001.

## Debuggeando la Skill con Visual Studio Code

Siguiendo los pasos anteriores, ahora puedes configurar breakpoints donde quieras dentro de todos los archivos JS para depurar tu Skill:

  ![Full-width image](/assets/img/blog/tutorials/alexa-nodejs/debug.png){:.lead data-width="800" data-height="100"}
Debuggear la Skill
  {:.figure}

## Testear las requests localmente

Estoy seguro de que ya conoces la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios. Aunque REST se ha vuelto omnipresente, no siempre es fácil probarlo. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir APIs, lo que te ayudará a ti y a tu equipo a ser más productivos a largo plazo.

Después de ejecutar tu aplicación, tendrás un endpoint disponible en http://localhost:3001/. Con Postman puedes emular cualquier request de Alexa.

Por ejemplo, puedes testear un `LaunchRequest`:

~~~json

  {
    "version": "1.0",
    "session": {
      "new": true,
      "sessionId": "amzn1.echo-api.session.[unique-value-here]",
      "application": {
        "applicationId": "amzn1.ask.skill.[unique-value-here]"
      },
      "user": {
        "userId": "amzn1.ask.account.[unique-value-here]"
      },
      "attributes": {}
    },
    "context": {
      "AudioPlayer": {
        "playerActivity": "IDLE"
      },
      "System": {
        "application": {
          "applicationId": "amzn1.ask.skill.[unique-value-here]"
        },
        "user": {
          "userId": "amzn1.ask.account.[unique-value-here]"
        },
        "device": {
          "supportedInterfaces": {
            "AudioPlayer": {}
          }
        }
      }
    },
    "request": {
      "type": "LaunchRequest",
      "requestId": "amzn1.echo-api.request.[unique-value-here]",
      "timestamp": "2020-03-22T17:24:44Z",
      "locale": "en-US"
    }
  }

~~~

## Desplegar la Alexa Skill

Con el código listo, tenemos que implementarlo en AWS Lambda para que pueda conectarse a Alexa.

Antes de desplegar la Skill Alexa, Podemos ver que el fichero `config` en la carpeta `.ask` está vacio:

~~~json
    {
      "deploy_settings": {
        "default": {
          "skill_id": "",
          "was_cloned": false,
          "merge": {}
        }
      }
    }

~~~

Desplegamos la Alexa Skill con la ASK CLI:

~~~bash
    ask deploy
~~~

Como dice la documentación oficial:

> When the local skill project has never been deployed, ASK CLI creates a new skill in the development stage for your account, then deploys the skill project. If applicable, ASK CLI creates one or more new AWS Lambda functions in your AWS account and uploads the Lambda function code. Specifically, ASK CLI does the following:
> 1. Looks in your skill project's config file (in the .ask folder, which is in the skill project folder) for an existing skill ID. If the config file does not contain a skill ID, ASK CLI creates a new skill using the skill manifest in the skill project's skill.json file, then adds the skill ID to the skill project's config file.
> 2. Looks in your skill project's manifest (skill.json file) for the skill's published locales. These are listed in the manifest.publishingInformation.locales object. For each locale, ASK CLI looks in the skill project's models folder for a corresponding model file (for example, es-ES.json), then uploads the model to your skill. ASK CLI waits for the uploaded models to build, then adds each model's eTag to the skill project's config file.
> 3. Looks in your skill project's manifest (skill.json file) for AWS Lambda endpoints. These are listed in the manifest.apis.<skill type>.endpoint or manifest.apis.<skill type>.regions.<region code>.endpoint objects (for example, manifest.apis.custom.endpoint or manifest.apis.smartHome.regions.NA.endpoint). Each endpoint object contains a sourceDir value, and optionally a uri value. ASK CLI upload the contents of the sourceDir folder to the corresponding AWS Lambda function and names the Lambda function the same as the uri value. For more details about how ASK CLI performs uploads to Lambda, see AWS Lambda deployment details.
> 4. Looks in your skill project folder for in-skill products, and if it finds any, uploads them to your skill. For more information about in-skill products, see the In-Skill Purchasing Overview.


Después de la ejecución del comando anterior, tendremos el archivo `config` debidamente llenado:

~~~json

  {
    "deploy_settings": {
      "default": {
        "skill_id": "amzn1.ask.skill.ed038d5e-61eb-4383-a480-04e3398b398d",
        "was_cloned": false,
        "merge": {},
        "resources": {
          "manifest": {
            "eTag": "faa883c92faf9a495407f0d03d5e3790"
          },
          "interactionModel": {
            "es-ES": {
              "eTag": "c9e7fd862be0dd3b21252b8bca53c7f7"
            }
          },
          "lambda": [
            {
              "alexaUsage": [
                "custom/default"
              ],
              "arn": "arn:aws:lambda:us-east-1:141568529918:function:ask-custom-alexa-nodejs-lambda-helloworld-default",
              "awsRegion": "us-east-1",
              "codeUri": "lambda/custom/src",
              "functionName": "ask-custom-alexa-nodejs-lambda-helloworld-default",
              "handler": "index.handler",
              "revisionId": "ef2707ee-a366-484d-a4b7-3826a44692dd",
              "runtime": "nodejs10.x"
            }
          ]
        }
      }
    }
  }

~~~

## Testear requests directamente desde el cloud de Alexa

ngrok es una herramienta genial y liviana que crea un túnel seguro en tu máquina local junto con una URL pública que se puede usar para navegar por tu web en local o API.

Cuando se está ejecutando ngrok, escucha en el mismo puerto en el que se está ejecutando el servidor web local y envía solicitudes externas a tu máquina local.

Veamos como de fácil es publicar nuestra Skill ejecutandose en local para que el cloud de Alexa nos envíe requests. 
Digamos que está ejecutando tu servidor web local en el puerto 8080. En la terminal, escribiría: `ngrok http 3001`. Esto comienza a escuchar a ngrok en el puerto 3001 y crea el túnel seguro:

  ![Full-width image](/assets/img/blog/tutorials/alexa-nodejs/tunnel.png){:.lead data-width="800" data-height="100"}
Túnel
  {:.figure}

Entonces ahora vas a la [Alexa Developer console](https://developer.amazon.com/alexa/console/ask), navegar a tu Skill > endpoints > https, agregas la URL https generada anteriormente. Por ejemplo: https://20dac120.ngrok.io.

Selecciona la opción "My development endpoint is a sub-domain...." desde el menú desplegable y haga clic en Save endpoint en la parte superior de la página.

Dirígete al tab Test en la Alexa Developer Console y lanza tu skill.

La Alexa Developer Console enviará una solicitud HTTPS al endpoint ngrok (https://20dac120.ngrok.io) que lo redirigirá a tu Skill ejecutándose en el servidor http://localhost:3001.


## Recursos
* [Alexa Skills Kit Node.js SDK](https://www.npmjs.com/package/ask-sdk) - La documentación oficial del SDK de Node.js
* [Documentación del Alexa Skills Kit](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - Documentación oficial del Alexa Skills Kit


## Conclusión 

Este fue un tutorial básico para aprender Alexa Skills usando Node.js.
Como has visto en este ejemplo, el Alexa Skill kit para Node.js y las herramientas de Alexa como la ASK CLI nos pueden ayudar mucho y también nos dan la posibilidad de crear Skills de una manera fácil. 

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld)

Esta Skill está creada con ASK CLI v1, para migrar ala ASK CLI v2 echa un ojo a este [tutorial](https://developer.amazon.com/es-ES/docs/alexa/smapi/ask-cli-v1-to-v2-migration-guide.html).

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    