---
layout: post
title: DevOps en tu Alexa Skill. Tests Unitarios.
image: /assets/img/blog/post-headers/alexa-unit-tests.jpg
description: >
   Test unitarios en una Alexa Skill
comments: true
author: xavi
kate: hl markdown;
categories: [alexa, devops]
tags:
  - alexa
keywords:
  - alexa
  - lambda
  - docker
  - ask
  - devops
  - howto
  - skill
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

Una prueba unitaria es un método que llama a funciones o fragmentos de códigos de nuestro código fuente con varios inputs
y luego valida si los outputs son los que desean esperar. Así, estas pruebas validan si el resultado es el esperado.
El método o función a probar se conoce como System Under Test (SUT).

# DevOps en tu Alexa Skill. Pruebas Unitarias.

Estos tests están automatizadas en el sistema de integración continua (CircleCI) y se ejecutan en cada nueva versión del software.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. CircleCI Account -  [Regístrate aquí gratis](https://circleci.com/)
5. Visual Studio Code

## Alexa Skill Test Framework

Vamos a utilizar el paquete npm `ask-sdk-test`, que es la versión más reciente del paquete npm `alexa-skill-test-framework`.

Esta nueva versión está escrita en TypeScript y es realmente fácil de usar tanto en Alexa Skills escritas en JavaScript como en TypeScript.

Este framework facilita la creación de pruebas de caja negra para una Skill de Alexa usando `Mocha`.

### Instalación

Podemos instalar `ask-sdk-test` usando npm. `--save-dev` se usa para guardar el paquete npm con fines de desarrollo. Ejemplo: pruebas unitarias, minificación.


~~~bash
    npm install ask-sdk-test --save-dev
~~~

Este marco utiliza el paquete npm `mocha` para ejecutar las pruebas. Así que necesitamos instalarlo también:

~~~bash
    npm install mocha chai --save-dev 
~~~

### Desarrollando Tests

Una vez que tenemos el frameworks para nuestras pruebas instalado y sus dependencias, ahora tenemos que desarrollar algunas pruebas unitarias.

Puede encontrar todas las pruebas en el fichero `helloworld-tests.js` en la carpeta `lambda/custom/test`.

Vamos a explicar paso a paso este fichero.

Primero, se requiere la inicialización del framework de prueba y la librería i18n para desarrollar pruebas unitarias:

~~~javascript
    // include the testing framework
    const test = require('ask-sdk-test');
    const skillHandler = require('../src/index.js').handler;
    // i18n strings for all supported locales
    const languageStrings = require('../src/utilities/languageStrings.js');
    const i18n = require('i18next');


    // initialize the testing framework
    const skillSettings = {
    appId: 'amzn1.ask.skill.00000000-0000-0000-0000-000000000000',
    userId: 'amzn1.ask.account.VOID',
    deviceId: 'amzn1.ask.device.VOID',
    locale: 'es-ES',
    };

    i18n.init({
    lng: skillSettings.locale,
    resources: languageStrings,
    });

    const alexaTest = new test.AlexaTest(skillHandler, skillSettings);

~~~

Con las líneas anteriores ahora podemos comenzar a escribir pruebas unitarias tan fácil como esto:

~~~javascript

    describe('Hello World Skill', function() {
        // tests the behavior of the skill's LaunchRequest
        describe('LaunchRequest', function() {
            alexaTest.test([
            {
                request: new test.LaunchRequestBuilder(skillSettings).build(),
                saysLike: i18n.t('WELCOME_MSG'), repromptsNothing: false, shouldEndSession: false,
            },
            ]);
        });

        // tests the behavior of the skill's HelloWorldIntent
        describe('HelloWorldIntent', function() {
            alexaTest.test([
            {
                request: new test.IntentRequestBuilder(skillSettings, 'HelloWorldIntent').build(),
                saysLike: i18n.t('HELLO_MSG'), repromptsNothing: true, shouldEndSession: true,
            },
            ]);
        });

        // tests the behavior of the skill's Help with like operator
        describe('AMAZON.HelpIntent', function() {
            alexaTest.test([
            {
                request: new test.IntentRequestBuilder(skillSettings, 'AMAZON.HelpIntent').build(),
                saysLike: i18n.t('HELP_MSG'), repromptsNothing: false, shouldEndSession: false,
            },
            ]);
        });

        describe('AMAZON.CancelIntent and AMAZON.CancelIntent', function(){
            alexaTest.test([
            { request: new test.IntentRequestBuilder(skillSettings, 'AMAZON.CancelIntent').build(),
                says: i18n.t('GOODBYE_MSG'), shouldEndSession: true },
            { request: new test.IntentRequestBuilder(skillSettings, 'AMAZON.CancelIntent').build(),
                says: i18n.t('GOODBYE_MSG'), shouldEndSession: true },
            ]);
        });

    });

~~~


### Informes

Una vez que tenemos todo configurado, tenemos que configurar los informes que vamos a utilizar para comprobar el resultado de las pruebas unitarias.

El primer informe que necesitamos crear es el informe de JUnit.

Necesitamos instalar este informe:

~~~bash
    npm install mocha-junit-reporter --save-dev 
~~~

Este informe generará un archivo .xml como salida que CircleCI utilizará para mostrar los resultados de la verificación de código:

![Full-width image](/assets/img/blog/tutorials/alexa-devops/mochacircleci.png){:.lead data-width="800" data-height="100"}
Unit tests Report en CircleCI
  {:.figure}


Vamos a dar un paso adelante. Queremos saber un poco más sobre los resultados de nuestras pruebas unitarias en cada ejecución del pipeline.

Es por eso que vamos a agregar el paquete npm `mochawesome` para generar un bonito informe HTML con más información en lugar del explicado anteriormente:

~~~bash
    npm install mochawesome --save-dev
~~~

Así es como se ve este informe:

![Full-width image](/assets/img/blog/tutorials/alexa-devops/mochahtml.jpg){:.lead data-width="800" data-height="100"}
Unit tests HTML Report 
  {:.figure}

Finalmente, para generar dos informes con un solo comando instalaremos otro paquete npm: `mocha-multi-reporters`

~~~bash
    npm install mocha-multi-reporters --save-dev
~~~

Luego tenemos que configurar este paquete npm para especificar los dos informes que vamos a ejecutar y su configuración.

The configuration file is `mocha.json` file in `lambda/custom` folder:

~~~json
    {
        "reporterEnabled": "mocha-junit-reporter, mochawesome",
        "mochaJunitReporterReporterOptions": {
            "mochaFile": "reports/mocha/test-results.xml"
        }
    }  
~~~

El informe JUnit se almacenará en la carpeta `lambda/custom/reports/mocha/` y el de HTML se almacenará en `lambda/custom/mochawesome-report`.

### Integración

¡Ahora es el momento de integrarlo en nuestro `package.json` para usarlo en nuestro pipeline con los comandos `npm run`!

Entonces, en este archivo vamos a agregar los siguientes comandos en el nodo json `script`:

1. `test`: este comando ejecutará las pruebas unitarias y generará los informes:
   * `mocha --reporter mocha-multi-reporters --reporter-options configFile=mocha.json`

## Pipeline Job

Todo está completamente instalado, configurado e integrado, ¡agregémoslo a nuestro pipeline!

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Ejecutar `npm run test` para ejecutar las pruebas unitarias.
3. Almacenar el informe JUnit como artefactos de CircleCi.
4. Almacenar el informe HTML como un artefacto de este job.
5. Conservar nuevamente el código que reutilizaremos en el próximo job

~~~yaml
  test:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: cd lambda/custom && npm run test
      - store_test_results:
          path: lambda/custom/reports/mocha/
      - store_artifacts:
          path: ./lambda/custom/mochawesome-report/
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project
~~~

## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia reference
* [Documentación del framework de pruebas del SDK de Alexa](https://github.com/taimos/ask-sdk-test) - Documentación del framework de pruebas del SDK de Alexa
* [Documentación oficial de CircleCI](https://circleci.com/docs/) - Documentación oficial de CircleCI

## Conclusión 

El objetivo principal de las pruebas unitarias es detectar errores dentro de los componentes de software de manera individual.
La idea es garantizar la calidad del funcionamiento del código durante todo el proceso de desarrollo.
Es necesario escribir pruebas unitarias constantemente.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld/blob/master/CICD.md)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
