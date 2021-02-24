---
layout: post
title: Alexa y Kubernetes. Alexa Skill cómo un Web Server (I)
image: /assets/img/blog/post-headers/alexa-webserver.jpg
description: >
   Crear una Alexa Skill como un Servidor Web
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
  - docker
  - ask
  - kubernetes
  - terraform
  - express
  - mongo
  - howto
  - skill
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

La primera tarea que tenemos que hacer para ejecutar nuestra Alexa Skill en un entorno de Kubernetes es transformar nuestro backend de nuestra Alexa Skill en una aplicación NodeJS que se ejecuta en un servidor web Express.

Podemos crear una custom Skill para Alexa implementando un servicio web que acepte peticiones y envíe respuestas al servicio de Alexa en la nube.
El servicio web debe cumplir con ciertos requisitos para manejar las peticiones enviadas por Alexa y cumplir con los estándares del Alexa Skills Kit.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Node.js v12.x
2. Visual Studio Code
3. Postman

## Servidor Express en NodeJS 

Como dice Wikipedia, Express.js, o simplemente Express, es un framework web backend para Node.js, lanzado como software gratuito y de código abierto bajo la licencia MIT. Está diseñado para crear aplicaciones web y API. Se le ha llamado el framework estándar de facto para Node.js.

El autor original, TJ Holowaychuk, lo describió como un servidor inspirado en Sinatra, lo que significa que es relativamente mínimo con muchas funciones disponibles como complementos. Express es el componente backend de la pila MEAN, junto con MongoDB y AngularJS.

## Instalación

El primer paso que debemos hacer es instalar es la dependencia `express`. Esto nos permitirá configurar y ejecutar nuestro servidor web Express:

```bash
    npm install express
```

Una vez que hemos instalado la dependencia de nuestro servidor web Express, necesitamos instalar el adaptador oficial `ask-sdk-express-adapter`.
Este paquete nos ayudará a ejecutar la instancia de Alexa Skill desde el objeto `Alexa.SkillBuilders` en un servidor web Express creando un controlador de pteiciones para ejecutar todas las peticiones entrantes.

```bash
    npm install ask-sdk-express-adapter
```

## Configuración

Una vez que tengamos todos los paquetes instalados ahora tenemos que configurarlo. Es un hecho que el equipo de Amazon Alexa ha hecho un gran esfuerzo en el adaptador express.
Esto se debe a que la transformación de los backends de Alexa Skill que son AWS Lambda a una aplicación Express Web Server requiere solo 4 líneas de código.

Este es un backend AWS Lambda típico de una Skill de Alexa:

```javascript
const Alexa = require('ask-sdk-core');

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
```

Y este es el backend del servidor web Express de una Skill de Alexa:

```javascript
const Alexa = require('ask-sdk-core');
const express = require('express');
const { ExpressAdapter } = require('ask-sdk-express-adapter');

const skill = Alexa.SkillBuilders.custom()
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
  .withPersistenceAdapter(adapter)
  .addRequestInterceptors(
    LocalisationRequestInterceptor)
  .create();

const app = express();
const expressAdapter = new ExpressAdapter(skill, false, false);
app.post('/', expressAdapter.getRequestHandlers());
app.listen(3000);

```

Como se puede ver arriba, en lugar de llamar al método `lambda()` y exportar ese objeto, llamaremos al método `create()` requerido para el adaptador Express.
Después de eso, crearemos una instancia de Express.
Luego vamos a configurar el adaptador Express creando una nueva instancia del `ExpressAdapter` que tiene 3 parámetros:
1. El Alexa Skill object que obtenemos después de llamar al método `create()`.
2. Un booleano que habilita/deshabilita la verificación de la Signature de la petición.
3. Un booleano que habilita/deshabilita la verificación del timestamp de la petición.

Ahora ya tenemos creado el adaptador Express. Con el método `post` del objeto`app`, creamos un listener para peticiones de tipo POST. Este método tiene dos parámetros:
1. El URI que escuchará el servidor web Express.
2. El controlador que gestionará todas las solicitudes a ese URI. Aquí vamos a utilizar el controlador proporcionado llamando al método `getRequestHandlers()` del adaptador Express.

Todo está configurado, ahora solo tenemos que llamar al método `listen` con el puerto que usará el servidor Express para ejecutar nuestro servidor Web.

Podéis encontrar todo el código en la carpeta `app`.

## Ejecutar y depurar la Skill con Visual Studio Code

El archivo `launch.json` en la carpeta `.vscode` tiene la configuración para Visual Studio Code que nos permite ejecutar nuestro Express Server en nuestro ordenador:

```json

{
    "version": "0.2.0",
    "configurations": [
        {
            "type": "node",
            "request": "launch",
            "name": "Launch Skill",
            "program": "${workspaceRoot}/app/index.js"
        }
    ]
}

```

Después de configurar nuestro archivo launch.json, es hora de hacer clic en el botón de play!:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/webserver/run.png){:.lead data-width="800" data-height="100"}
Petición a nuestro Express server
  {:.figure}

Después de ejecutarlo, podemos enviar solicitudes POST típicas de Alexa a http://localhost:3000.

## Probando peticiones localmente

Seguro que ya conoceis la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios web. Aunque REST se ha vuelto omnipresente, no siempre es fácil de probar. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir API, lo que nos ayudará a nosotros y a nuestro equipo a ser más productivos a largo plazo.

Después de ejecutar nuestra aplicación, tendremos un endpoint disponible en http://localhost:3000. Con Postman podemos emular cualquier solicitud de Alexa.

Por ejemplo, podemos probar una `LaunchRequest`:

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

## Recursos
* [Official Alexa Skills Kit Node.js SDK](https://www.npmjs.com/package/ask-sdk) - The Official Node.js SDK Documentation
* [Official Alexa Skills Kit Documentation](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - Official Alexa Skills Kit Documentation
* [Official Express Adapter Documentation](https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit-sdk-for-nodejs/host-web-service.html) - Express Adapter Documentation

## Conclusion 

Como se puede ver, con solo 4 líneas de código transformamos una Skill de Alexa usando AWS Lambda en una aplicación Express gracias al trabajo realizado por el equipo de Amazon Alexa y su fabuloso adaptador.

Espero que este proyecto de ejemplo te sea de utilidad.

Puede encontrar el código [aquí](https://github.com/xavidop/alexa-nodejs-k8s-helloworld)

¡Eso es todo amigos!

Happy coding!
