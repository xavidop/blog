---
layout: post
title: Alexa Skill con TypeScript
image: /assets/img/blog/post-headers/alexa-typescript.jpg
description: >
   Alexa Skill desarrollada en TypeScript usando Visual Studio Code
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - lambda
  - typescript
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

# Alexa Skill con TypeScript
 
Esto hace que el live debugging de las requests enviadas a Alexa sea una tarea muy difícil.
En este post, implementaremos una custom Skill para Amazon Alexa usando TypeScript, npm y AWS Lambda Functions.
Esta Skill es básicamente un ejemplo de Hello World. 
Con este post, podras crear una custom Skill para Amazon Alexa, implementar la funcionalidad utilizando TypeScript y ejecutar tu Skill tanto desde tu ordenador local como desde AWS.
Esta publicación contiene materiales de diferentes recursos que se pueden ver en la sección Recursos.


## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. Node.js v10.x
5. TypeScript (Version >3.0.0)
6. Visual Studio Code
7. npm Package Manager
8. Alexa ASK for Node.js (Version >2.7.0)
9. ngrok

La Alexa Skills Kit Command Line Interface (ASK CLI) es una herramienta para que puedas administrar tus Skills de Alexa y recursos relacionados, como las funciones de AWS Lambda.
Con la ASK CLI, tienes acceso a la Skill Management API, que te permite administrar las Skills de Alexa mediante programación desde la línea de comandos.
Utilizaremos esta poderosa herramienta para crear, construir, desplegar y gestionar nuestra Skill Hello World. 

¡Empecemos!

## Creando la Skill con ASK CLI

Si deseas cómo crear tu Skill con la CLI ASK, sigue el primer paso explicado en mi ejemplo [Skill en Node.js](https://github.com/xavidop/alexa-nodejs-lambda-helloworld).

Una vez que hemos creado la Skill en Node.js, tenemos que reescribir o 'transpilar' nuestro código a TypeScript. He hecho que esto por ti. ¡

Echemos un vistazo!

## Estructura del proyecto 

Estos son los archivos principales del proyecto:

```bash

    ├───.ask/
    │       config
    ├───.vscode/
    │       launch.json
    ├───hooks/
    ├───lambda/
    │   └───custom/
    │       │   └───build/
    │       │   local-debugger.js
    │       │   package.json
    │       │   tsconfig.json
    │       │   tslint.json
    │       └───src/
    │           ├───index.ts
    │           ├───errors/
    │           ├───intents/
    │           ├───interceptors/
    │           └───utilities/
    │
    ├───models/
    └───skill.json

```

* .ask: carpeta que contiene el archivo de configuración de ASK CLI. Este archivo de configuración permanecerá vacío hasta que ejecutemos el comando `ask deploy`
* `.vscode/launch.json`: Preferencias de ejecución para ejecutar localmente tu Skill para testing local. Esta configuración ejecuta `lambda/custom/local-debugger.js`. Este script ejecuta un servidor en http://localhost:3001 para debuggear la Skill. No se ha transpilado a TypeScript porque no forma parte de nuestra lambda. Es una herramienta local.
* hooks: Una carpeta que contiene los hooks scripts. Amazon proporciona dos hooks, post_new_hook y pre_deploy_hook.
  * `post_new_hook`:  ejecutado después de la creación de la Skill. En Node.js ejecuta `npm install` en el directorio especificado en el sourceDir del `skill.json`
  * `pre_deploy_hook`:  ejecutado antes del despliegue de la Skill. En Node.js ejecuta `npm install` en el directorio especificado en el sourceDir del `skill.json` también.
* lambda/custom/src:  Una carpeta que contiene el código fuente de la función AWS Lambda de la Skill:
  * `index.ts`: El principal entry point de la función Lambda.
  * `package.json`:  Este archivo es esencial para el ecosistema Node.js y es una parte básica para la comprensión y el trabajo con Node.js, npm e incluso TypeScript
  * `tsconfig.json`: archivo de configuración que vamos a utilizar para compilar nuestro código TypeScript
  * `tslint.json`: archivo de configuración utilizado por `gts` (Google TypeScript Style) para verificar el estilo de nuestro código TypeScript
  * `local-debugger.js`: utilizado para depurar nuestra Skill localmente
  * `errors`: carpeta que contiene todos error handlers
  * `intents`: este contiene todos los intent handlers
  * `interceptors`: carpeta de interceptores con la inicialización del i18n
  * `utilities`: esta carpeta contiene las strings i18n, funciones auxiliares, constantes e interfaces TypeScript
  * `build`: la carpeta de salida después de compilar el código TypeScript
* models: Una carpeta que contiene los interactions models para nuestra Skill. Cada interaction model se define en un archivo JSON nombrado de acuerdo con la configuración regional. Por ejemplo, es-ES.json
* `skill.json`: El skill manifest. Uno de los archivos más importantes de nuestro proyecto


## Lambda function en TypeScript

El SDK de ASK para Node.js te facilita el desarrollo de Skills de gran calidad al permitirte pasar más tiempo implementando funciones y menos tiempo escribiendo código repetitivo.

¡Vamos a usar este SDK pero ahora en TypeScript!

Puede encontrar documentación, ejemplos y enlaces útiles en su repositorio oficial de [GitHub](https://github.com/alexa/alexa-skills-kit-sdk-for-nodejs)

El archivo TypeScript principal en nuestro proyecto lambda es `index.ts` situado en la capreta `lambda/custom/src`. Este fichero contiene todos los handlers, interceptors y exporta el Skill handler en `exports.handler`.

La función `exports.handler` se ejecuta cada vez que AWS Lambda es invocado por el cloud de Alexa.
En teoría, una función AWS Lambda es solo una función única. Esto significa que necesitamos definir la lógica para que una request a la función pueda enrutarse al código apropiado, de ahí los handlers.

```typescript
  import * as Alexa from 'ask-sdk-core';
  import { Launch } from './intents/Launch';
  import { Help } from './intents/Help';
  import { Stop } from './intents/Stop';
  import { Reflector } from './intents/Reflector';
  import { Fallback } from './intents/Fallback';
  import { HelloWorld } from './intents/HelloWorld';
  import { ErrorProcessor } from './errors/ErrorProcessor';
  import { SessionEnded } from './intents/SessionEnded';
  import { LocalizationRequestInterceptor } from './interceptors/LocalizationRequestInterceptor';

  export const handler = Alexa.SkillBuilders.custom()
    .addRequestHandlers(
      // Default intents
      Launch,
      HelloWorld,
      Help,
      Stop,
      SessionEnded,
      Reflector,
      Fallback
    )
    .addErrorHandlers(ErrorProcessor)
    .addRequestInterceptors(LocalizationRequestInterceptor)
    .lambda();

```

Es importante echar un vistazo al fichero `Launch.ts`, importado como `Launch` arriba, que es el handler `LaunchRequestHandler` ubicado en la carpeta `intents` como un ejemplo de handler Alexa Skill escrito en TypeScript:

```typescript

  import { RequestHandler, HandlerInput } from 'ask-sdk-core';
  import { RequestTypes, Strings } from '../utilities/constants';
  import { IsType } from '../utilities/helpers';
  import i18n from 'i18next';

  export const Launch: RequestHandler = {
    canHandle(handlerInput: HandlerInput) {
      return IsType(handlerInput, RequestTypes.Launch);
    },
    handle(handlerInput: HandlerInput) {
      const speechText = i18n.t(Strings.WELCOME_MSG);

      return handlerInput.responseBuilder
        .speak(speechText)
        .reprompt(speechText)
        .withSimpleCard(i18n.t(Strings.SKILL_NAME), speechText)
        .getResponse();
    },
  };

```

## Construir la Skill con Visual Studio Code

Dentro del fichero `package.json`, casi siempre encontraremos metadatos específicos para el proyecto. 
Estos metadatos ayudan a identificar el proyecto y actúan como base para que los usuarios y contribuyentes obtengan información sobre el proyecto.

Así es como se ve este archivo:

```json

  {
    "name": "alexa-typescript-lambda-helloworld",
    "version": "1.0.0",
    "description": "Alexa HelloWorld example with TypeScript",
    "main": "index.js",
    "scripts": {
      "clean": "rimraf build",
      "compile": "tsc --build tsconfig.json --pretty",
      "build-final": "cpy package.json build && cd build/ && npm install --production",
      "test": "echo \"No test specified yet\" && exit 0",
      "lint-check": "gts check",
      "lint-clean": "gts clean",
      "lint-fix": "gts fix",
      "build": "npm run clean && npm run test && npm run lint-check && npm run compile && npm run build-final"
    },
    "repository": {
      "type": "git",
      "url": "https://github.com/xavidop/alexa-typescript-lambda-helloworld.git"
    },
    "author": "Xavier Portilla Edo",
    "license": "Apache-2.0",
    "dependencies": {
      "ask-sdk-core": "^2.7.0",
      "ask-sdk-model": "^1.19.0",
      "aws-sdk": "^2.326.0",
      "i18next": "^15.0.5",
      "i18next-sprintf-postprocessor": "^0.2.2"
    },
    "devDependencies": {
      "@types/node": "^10.10.0",
      "@types/i18next-sprintf-postprocessor": "^0.2.0",
      "typescript": "^3.0.2",
      "cpy-cli": "^3.1.0",
      "rimraf": "^3.0.0",
      "ts-node": "^7.0.1",
      "gts": "^1.1.2"
    }
  }


```

Con TypeScript tenemos que compilar nuestro código para generar el código JavaScript. Para compilar nuestra Skill, podemos ejecutar el siguiente comando:

```bash

  npm run build

```

Este comando ejecutará estas acciones:
1. Elimina la carpeta `build` ubicada en `lambda/custom` con el comando `rimraf build`. Esta carpeta contiene el output de compilar el código TypeScript
2. Verifica el estilo de nuestro código TypeScript con el comando `gts check` utilizando el archivo `tslint.json`
3. Compila el código TypeScript y genera el código JavaScript en la carpeta de salida `lambda/custom/build` usando el comando `tsc --build tsconfig.json --pretty`
4. Copie el `package.json` en la carpeta `build` porque es necesario para generar el código lambda final
5. Finalmente, ejecutará el comando `npm install --production` en la carpeta `build` para obtener el código lambda final que vamos a subir a AWS con la ASK CLI.

Como puedes ver, este proceso en un entorno TypeScript es más complejo que en JavaScript.

## Ejecutar la Skill con Visual Studio Code

El fichero `launch.json` situado en la carpeta `.vscode` tiene la configuración para Visual Studio Code que nos permite ejecutar nuestro lambda localmente:

```json

  {
      "version": "0.2.0",
      "configurations": [
          {
              "type": "node",
              "request": "launch",
              "name": "Launch Skill",
              // Specify path to the downloaded local adapter(for nodejs) file
              "program": "${workspaceRoot}/lambda/custom/local-debugger.js",
              "args": [
                  // port number on your local host where the alexa requests will be routed to
                  "--portNumber", "3001",
                  // name of your nodejs main skill file
                  "--skillEntryFile", "${workspaceRoot}/lambda/custom/build/index.js",
                  // name of your lambda handler
                  "--lambdaHandler", "handler"
              ]
          }
      ]
  }

```
Este archivo de configuración ejecutará el siguiente comando:

```bash

  node --inspect-brk=28448 lambda\custom\local-debugger.js --portNumber 3001 --skillEntryFile lambda/custom/build/index.js --lambdaHandler handler

```

Esta configuración utiliza el fichero `local-debugger.js`  que corre un [servidor TCP](https://nodejs.org/api/net.html) escuchando en http://localhost:3001

Para una nueva request a la skill entrante se establece una nueva conexión al socket.
De los datos recibidos en el socket se extrae el cuerpo de la solicitud, se analiza en JSON y se pasa al lambdahandler de la Skill.
La respuesta del lambda handler es parseada como un formato de mensaje HTTP 200 como se especifica [aquí](https://developer.amazon.com/docs/custom-skills/request-and-response-json-reference.html#http-header-1) La respuesta se escribe en la conexión del socket y se devuelve.

Después de configurar nuestro archivo launch.json y comprender cómo funciona el local debugger, es hora de hacer clic en el botón play:

  ![Full-width image](/assets/img/blog/tutorials/alexa-typescript/run.png){:.lead data-width="800" data-height="100"}
Ejecutar la Skill
  {:.figure}

Después de ejecutarlo, puede enviar requests POST de Alexa a http://localhost:3001.

## Debuggeando la Skill con Visual Studio Code

Siguiendo los pasos anteriores, ahora puedes configurar breakpoints donde quieras dentro de todos los archivos TypeScript para depurar tu Skill:

  ![Full-width image](/assets/img/blog/tutorials/alexa-typescript/debug.png){:.lead data-width="800" data-height="100"}
Debuggear la Skill
  {:.figure}

## Testear las requests localmente

Estoy seguro de que ya conoces la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios. Aunque REST se ha vuelto omnipresente, no siempre es fácil probarlo. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir APIs, lo que te ayudará a ti y a tu equipo a ser más productivos a largo plazo.

Después de ejecutar tu aplicación, tendrás un endpoint disponible en http://localhost:3001/. Con Postman puedes emular cualquier request de Alexa.

Por ejemplo, puedes testear un `LaunchRequest`:

```json

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

```

## Desplegar la Alexa Skill

Con el código listo, tenemos que implementarlo en AWS Lambda para que pueda conectarse a Alexa.

Antes de desplegar la Skill Alexa, Podemos ver que el fichero `config` en la carpeta `.ask` está vacio:

```json
    {
      "deploy_settings": {
        "default": {
          "skill_id": "",
          "was_cloned": false,
          "merge": {}
        }
      }
    }

```

Desplegamos la Alexa Skill con la ASK CLI:

```bash
    ask deploy
```

Como dice la documentación oficial:

> When the local skill project has never been deployed, ASK CLI creates a new skill in the development stage for your account, then deploys the skill project. If applicable, ASK CLI creates one or more new AWS Lambda functions in your AWS account and uploads the Lambda function code. Specifically, ASK CLI does the following:
> 1. Looks in your skill project's config file (in the .ask folder, which is in the skill project folder) for an existing skill ID. If the config file does not contain a skill ID, ASK CLI creates a new skill using the skill manifest in the skill project's skill.json file, then adds the skill ID to the skill project's config file.
> 2. Looks in your skill project's manifest (skill.json file) for the skill's published locales. These are listed in the manifest.publishingInformation.locales object. For each locale, ASK CLI looks in the skill project's models folder for a corresponding model file (for example, es-ES.json), then uploads the model to your skill. ASK CLI waits for the uploaded models to build, then adds each model's eTag to the skill project's config file.
> 3. Looks in your skill project's manifest (skill.json file) for AWS Lambda endpoints. These are listed in the manifest.apis.<skill type>.endpoint or manifest.apis.<skill type>.regions.<region code>.endpoint objects (for example, manifest.apis.custom.endpoint or manifest.apis.smartHome.regions.NA.endpoint). Each endpoint object contains a sourceDir value, and optionally a uri value. ASK CLI upload the contents of the sourceDir folder to the corresponding AWS Lambda function and names the Lambda function the same as the uri value. For more details about how ASK CLI performs uploads to Lambda, see AWS Lambda deployment details.
> 4. Looks in your skill project folder for in-skill products, and if it finds any, uploads them to your skill. For more information about in-skill products, see the In-Skill Purchasing Overview.


Después de la ejecución del comando anterior, tendremos el archivo `config` debidamente llenado:

```json

  {
    "deploy_settings": {
      "default": {
        "skill_id": "amzn1.ask.skill.945814d5-9b30-4ee7-ade6-f5ef017a1c17",
        "was_cloned": false,
        "merge": {},
        "resources": {
          "manifest": {
            "eTag": "ea0bd8c176a560f95a64fe7a1ba99315"
          },
          "interactionModel": {
            "es-ES": {
              "eTag": "4a185611054c722446536c5659593aa3"
            }
          },
          "lambda": [
            {
              "alexaUsage": [
                "custom/default"
              ],
              "arn": "arn:aws:lambda:us-east-1:141568529918:function:ask-custom-alexa-typescript-lambda-helloworld-default",
              "awsRegion": "us-east-1",
              "codeUri": "lambda/custom/build",
              "functionName": "ask-custom-alexa-typescript-lambda-helloworld-default",
              "handler": "index.handler",
              "revisionId": "477bcf34-937d-4fa4-8588-8db8ec1e7213",
              "runtime": "nodejs10.x"
            }
          ]
        }
      }
    }
  }

```

**NOTA:** Después de reescribir nuestro código a TypeScript, necesitamos cambiar el `codeUri` de `lambda/custom` a `lambda/custom/build` debido a que nuestro código compilado de TypeScript a JavaScript va a la carpeta `build`.

## Testear requests directamente desde el cloud de Alexa

ngrok es una herramienta genial y liviana que crea un túnel seguro en tu máquina local junto con una URL pública que se puede usar para navegar por tu web en local o API.

Cuando se está ejecutando ngrok, escucha en el mismo puerto en el que se está ejecutando el servidor web local y envía solicitudes externas a tu máquina local.

Veamos como de fácil es publicar nuestra Skill ejecutandose en local para que el cloud de Alexa nos envíe requests. 
Digamos que está ejecutando tu servidor web local en el puerto 8080. En la terminal, escribiría: `ngrok http 3001`. Esto comienza a escuchar a ngrok en el puerto 3001 y crea el túnel seguro:

  ![Full-width image](/assets/img/blog/tutorials/alexa-typescript/tunnel.png){:.lead data-width="800" data-height="100"}
Túnel
  {:.figure}

Entonces ahora vas a la [Alexa Developer console](https://developer.amazon.com/alexa/console/ask), navegar a tu Skill > endpoints > https, agregas la URL https generada anteriormente. Por ejemplo: https://20dac120.ngrok.io.

Selecciona la opción "My development endpoint is a sub-domain...." desde el menú desplegable y haga clic en Save endpoint en la parte superior de la página.

Dirígete al tab Test en la Alexa Developer Console y lanza tu skill.

La Alexa Developer Console enviará una solicitud HTTPS al endpoint ngrok  (https://20dac120.ngrok.io) que lo redirigirá a tu Skill ejecutándose en el servidor http://localhost:3001.


## Recursos

* [Alexa Skills Kit Node.js SDK](https://www.npmjs.com/package/ask-sdk) - La documentación oficial del SDK de Node.js
* [Documentación del Alexa Skills Kit](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - Documentación oficial del Alexa Skills Kit

## Conclusión 

Este fue un tutorial básico para aprender Alexa Skills usando Node.js y TypeScript.
Como has visto en este ejemplo, el Alexa Skill kit para Node.js y las herramientas de Alexa como la ASK CLI nos pueden ayudar mucho y también nos dan la posibilidad de crear Skills de una manera fácil en TypeScript. 

Esta Skill está creada con ASK CLI v1, para migrar ala ASK CLI v2 echa un ojo a este [tutorial](https://developer.amazon.com/es-ES/docs/alexa/smapi/ask-cli-v1-to-v2-migration-guide.html).

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-typescript-lambda-helloworld)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    