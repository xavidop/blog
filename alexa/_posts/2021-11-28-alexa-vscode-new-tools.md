---
layout: post
title: Nuevas herramientas para Alexa Skills en VS code
image: /assets/img/blog/post-headers/alexa-vscode-new-tools.jpg
description: >
   Nuevas tools disponibles para desarrollo local de VS Code
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

# Tools para Alexa Skills en VS code

Durante los últimos meses, el equipo de Alexa ha lanzado un montón de herramientas útiles para Visual Studio Code. La finalidad de estas nuevas funcionalidades es tener una sitio donde poder programar y testear nuestras Alexa Skill. Además, al tener todas estas herramientas en el mismo lugar, no tenemos que cambiar entre múltiples aplicaciones o pestañas. En este artículo te mostraré cómo puedes tener un entorno de desarrollo para crear Alexa Skills en Visual Studio Code.

## Prerrequisitos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Node.js v14.x
2. Visual Studio Code
3. Extensión de Alexa para VS Code

## Configurando nuestra Skill de Alexa

El primer paso que debemos hacer para habilitar el debug local en Visual Studio es básicamente instalar 2 paquetes npm: `ask-sdk-model` y `ask-sdk-local-debug`. El primero ya deberías tenerlo al crear la Skill, pero vale la pena actualizarlo a la última versión. ¡Debes usar `v1.29.0` o superior!

El segundo paquete, `ask-sdk-local-debug`, es el más importante, es una `devDependency` en lugar de una `dependency` normal. ¿Por qué? bueno, solo lo necesitamos durante el desarrollo. Este paquete es el que vamos a utilizar para lanzar nuestra AWS Lambda de forma local e interceptar todas las llamadas cuando estemos interactuando con nuestra Alexa Skill.

Para instalar estas dependencias, tenemos ejecutar estos comandos:
1. Usando npm:
~~~bash
    npm install --save ask-sdk-model@^1.29.0
    npm install --save-dev ask-sdk-local-debug
~~~
2. Usando yarn:
~~~bash
    yarn add ask-sdk-model@^1.29.0
    yarn add ask-sdk-local-debug --dev
~~~

¡Con estos paquetes instalados/actualizados, ya casi tenemos el setup necesario! Continuemos con los siguientes pasos.

## Creando la configuración en Visual Studio

Una vez que tenemos los paquetes que necesitamos instalados/actualizados, tenemos crear una configuración en Visual Studio Code para ejecutar nuestra AWS Lambda.

Todas las configuraciones de Visual Studio deben colocarse en la carpeta `.vscode`. En esta carpeta vamos a crear un archivo llamado `launch.json`:

~~~json

    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Debug Alexa Skill (Node.js)",
                "type": "node",
                "request": "launch",
                "program": "${command:ask.debugAdapterPath}",
                "args": [
                    "--accessToken",
                    "${command:ask.accessToken}",
                    "--skillId",
                    "${command:ask.skillIdFromWorkspace}",
                    "--handlerName",
                    "handler",
                    "--skillEntryFile",
                    "${workspaceFolder}/lambda/index.js",
                    "--region",
                    "EU"
                ]
            }
        ]
    }

~~~

Vamos a explicar los parámetros más relevantes que tenemos en esta configuración que le vamos a llamar `Debug Alexa Skill (Node.js)`:
1. `program`: este parámetro detecta automáticamente el ejecutable que necesitamos para lanzar nuestro AWS Lambda localmente. Este ejecutable se instala cuando instalamos el paquete `ask-sdk-local-debug`.
2. argumentos:
    1. `accessToken`: este es el token que necesitamos para interceptar las invocaciones de la Alexa Skill localmente
    2. `skillId`: el id de nuestra Skill de Alexa
    3. `handlerName`: el objeto creado en nuestra AWS Lambda que recibirá todas las invocaciones
    4. `skillEntryFile`: dónde se encuentra el handler (en qué archivo).
    5. `region`; la región de **NUESTRA** cuenta de desarrollador de Alexa. En mi caso lo he configurado en UE porque mi cuenta es de Europa. Los valores disponibles son NA (Norteamérica), FE (Extremo Oriente), UE (Europa).

Al crear esta configuración, podrás ejecutar la AWS Lambda directamente en VS Code desde la pestaña de debug:

![Full-width image](/assets/img/blog/tutorials/alexa-vscode-new-tools/debug-tap.png){:.lead data-width="800" data-height="100"}
Tab de Debug
  {:.figure}


Y verás este resultado en la consola de depuración:

![Full-width image](/assets/img/blog/tutorials/alexa-vscode-new-tools/debug-console.png){:.lead data-width="800" data-height="100"}
Consola de Debug
  {:.figure}

Después de esto, puedes configurar todos los breakpoints que quieras.

## Simulador de Alexa

Cuando instales la extensión de Alexa en VS Code, verás el icono de Alexa en la barra lateral izquierda. Al hacer clic, verá muchas opciones que puedes usar para el desarrollo de Skill, como descargar el modelo de interacción, el visor de APL, descargar el manifest de la Skill o probar directamente la skill en VS Code:

![Full-width image](/assets/img/blog/tutorials/alexa-vscode-new-tools/alexa-extension.png){:.lead data-width="800" data-height="100"}
Extensió de Alexa
  {:.figure}

Si hacemos clic en el simulador, tendremos una pantalla muy similar a la pestaña Test en la Consola de desarrollador de Alexa, ¡pero ahora en tu IDE!

![Full-width image](/assets/img/blog/tutorials/alexa-vscode-new-tools/simulator.png){:.lead data-width="800" data-height="100"}
Alexa Simulator
  {:.figure}

Con estas herramientas configuradas correctamente, es hora de iniciar nuestra Skill de Alexa localmente y ver si el código se detiene en los puntos de interrupción.

## Ejecutando y debuggeando nuestra Skill de Alexa localmente

Cuando invocamos la Skill de Alexa desde el simulador y hayamos lanzado nuestra AWS Lambda localmente, comenzaremos a ver que todas las interacciones se interceptan:

![Full-width image](/assets/img/blog/tutorials/alexa-vscode-new-tools/image.png){:.lead data-width="800" data-height="100"}
Alexa Simulator ejecutándose
  {:.figure}

¡Esto significa que el código que se está ejecutando es el código que tenemos en nuestra carpeta lambda localmente! Pongamos algunos puntos de interrupción y veamos si funciona:

![Full-width image](/assets/img/blog/tutorials/alexa-vscode-new-tools/breakpoints.png){:.lead data-width="800" data-height="100"}
Breakpoints
  {:.figure}

**y voilà! Funciona!**

## Video con la explicación completa

Y eso es todo, aquí tienes la explicación completa en inglés en una sesión de las Alexa Office Hours EU conmigo y Gaetano Ursomanno del equipo de Alexa.

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/9g1grjLBZOc/0.jpg)](https://www.youtube.com/watch?v=9g1grjLBZOc)


## Recursos
* [Official Alexa Skills Kit Node.js SDK](https://www.npmjs.com/package/ask-sdk) - The Official Node.js SDK Documentation
* [Official Alexa Skills Kit Documentation](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - Official Alexa Skills Kit Documentation

## Conclusión 

Como puedes ver, el equipo de Amazon Alexa ha creado buenas herramientas para tener todo en el mismo ecosistema.

Espero que este proyecto de ejemplo os sea de utilidad.

Puedes encontrar el código [aquí](https://github.com/xavidop/alexa-helloworld-new-vscode-config)

¡Eso es todo amigos!

Happy coding!
