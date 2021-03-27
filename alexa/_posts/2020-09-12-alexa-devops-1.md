---
layout: post
title: DevOps en tu Alexa Skill
image: /assets/img/blog/post-headers/alexa-devops1.jpg
description: >
   Creación de un pipeline DevOps usando CircleCI  
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

"DevOps es la unión de personas, procesos y productos para permitir la entrega continua de valor a nuestros usuarios finales." - Donovan Brown, Microsoft

DevOps es una "cultura" que tiene un conjunto de prácticas que combina el desarrollo de software (Dev) y las operaciones IT (Ops) que tiene como objetivo acortar el ciclo de vida del desarrollo y proporcionar una entrega continua con alta calidad de software. La cultura DevOps desarrolla una mentalidad de "production-first". 

# DevOps en tu Alexa Skill

En términos de Alexa, DevOps puede ayudarnos a entregar rápidamente la más alta calidad de nuestra Skill a los clientes finales.
Este post contiene materiales de diferentes recursos que se pueden ver en la sección Recursos.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. CircleCI Account -  [Regístrate aquí gratis](https://circleci.com/)
5. Visual Studio Code

La Alexa Skills Kit Command Line Interface (ASK CLI) es una herramienta para que puedas administrar tus Skills de Alexa y recursos relacionados, como las funciones de AWS Lambda.
Con la ASK CLI, tienes acceso a la Skill Management API, que te permite administrar las Skills de Alexa mediante programación desde la línea de comandos.

Si quieres crear una Skill con ASK CLI, sigue el primer paso explicado en mi ejemplo de [Node.js Skill](https://github.com/xavidop/alexa-nodejs-lambda-helloworld). 

Vamos a utilizar esta poderosa herramienta para hacer algunos pasos en nuestro pipeline. 

¡Let's DevOps!

## Dockerfile

Antes de explicar el pipeline, es importante explicar la imagen de Docker que vamos a utilizar.
Puedes encontrar toda la explicación en [este repositorio](https://github.com/xavidop/alexa-ask-aws-cli-docker).

## Pipeline

  ![Full-width image](/assets/img/blog/tutorials/alexa-devops/pipeline.png){:.lead data-width="800" data-height="100"}
CircleCI Pipeline
  {:.figure}

Antes de explicar el pipeline, vale la pena señalar la parte común al pipeline, el `executor`. Un `executor` define la tecnología subyacente o el entorno en el que ejecutar un job. Configura tus jobs para que se ejecuten en windows, una máquina, macOS o Docker especificando una imagen con las herramientas y paquetes que necesitas.

En nuestro caso, utilizaremos un `executor` de Docker usando la imagen explicada anteriormente:

~~~yaml
  executors:
    ask-executor:
      docker:
        - image: xavidop/alexa-ask-aws-cli:1.0
~~~

Vamos a explicar job por job lo que está sucediendo en nuestr pipeline.
En primer lugar, cada caja representada en la imagen de arriba es un job y se definirán debajo del nodo `job` en el archivo de configuración de CircleCI:

### Checkout

El job de checkout ejecutará las siguientes tareas:
1. Checkout del código en `/home/node/project`
2. Dar permiso de ejecución al usuario `node` para poder ejecutar todos los hooks
3. Persistir el código para reutilizarlo en el próximo job

~~~yaml
  checkout:
    executor: ask-executor
    steps:
      - checkout
      - run: chmod +x -R ./hooks
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project
~~~

### build

El job de build ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Ejecutar `npm install` para descargar todas las dependencias de Node.js
3. Persistir el código para reutilizarlo en el próximo job

~~~yaml
  build:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: ls -la
      - run: cd lambda/custom && npm install
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project

~~~


### Pretests

El job de pretest ejecutará el checkeo de calidad del código estático. Consulta la explicación completa [aquí](/alexa/devops/2020-09-11-alexa-devops-2).

### Test

El job de test ejecutará las pruebas unitarias.. Consulta la explicación completa [aquí](/alexa/devops/2020-09-11-alexa-devops-3).

### Code Coverage

El job codecov ejecutará el informe de cobertura de código. Consulta la explicación completa [aquí](/alexa/devops/2020-09-11-alexa-devops-4).

### Deploy

El job de deploy desplegará la Skill de Alexa en la nube de Alexa en el stage de development. Consulta la explicación completa [aquí](/alexa/devops/2020-09-11-alexa-devops-5).

### Testing the Voice User Interface

Estos jobs verificarán nuestro interaction model. Consulta la explicación completa [aquí](/alexa/devops/2020-09-11-alexa-devops-6).

### Integration tests

Estos jobs verificarán el interaction model y nuestro backend también. Consulta la explicación completa [aquí](/alexa/devops/2020-09-11-alexa-devops-7).

### End to end tests

Estos jobs verificarán el sistema completo utilizando la voz como entrada. Consulta la explicación completa [aquí](/alexa/devops/2020-09-11-alexa-devops-8).

### Validation tests

Estos jobs validarán la Skill de Alexa antes de enviarla a certificación. Consulta la explicación completa [aquí](/alexa/devops/2020-09-11-alexa-devops-9).

### Store-artifacts

El job de store-artifacts ejecutará las siguientes tareas:
1. Restaurar el código que hemos usado en el paso anterior en la carpeta `/home/node/project`
2. Limpiar la carpeta `node_modules`
3. Almacenar el código completo de nuestra Skill de Alexa como un artefacto. Será accesible en CircleCI cuando queramos verlo.

~~~yaml
  store-artifacts:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: ls -la
      - run: rm -rf lambda/custom/node_modules
      - store_artifacts:
          path: ./

~~~

### Wait for Approval

Hay algunas ocasiones en las que se prefiere mantener las aprobaciones manuales en un pipeline. Para ello, debes configurar el proceso de aprobación manual agregando al workflow un job especial que contenga una entrada `type: approval`. Este job es necesario para verificar lo que se desee de la Skill de Alexa antes de enviarlo a certificación. Así cuando todo está verificado, se puede aprobar o rechazar la ejecución.

Este job es un job diferente que solo existe en el nodo `workflows` en el archivo de configuración. No es necesario agregarlo como un `job`.

~~~yaml

  - wait-for-decision:
      type: approval
      requires:
        - store-artifacts
~~~

### Submit

Estos jobs enviarán la Skill de Alexa a certificación. Consulta la explicación completa [aquí](/alexa/devops/2020-09-11-alexa-devops-10).

### Workflow

Al final del archivo de configuración CircleCi, definiremos nuestro pipeline como un workflow de CircleCI que ejecutará los jobs explicados anteriormente:

~~~yaml
  workflows:
    skill-pipeline:
      jobs:
        - checkout
        - build:
            requires:
              - checkout
        - pretest:
            requires:
              - build
        - test:
            requires:
              - pretest
        - codecov:
            requires:
              - test
        - deploy:
            requires:
              - test
        - check-utterance-conflicts:
            requires:
              - deploy
        - check-utterance-resolution:
            requires:
              - deploy
        - check-utterance-evaluation:
            requires:
              - deploy
        - integration-test:
            requires:
              - check-utterance-evaluation
        - end-to-end-test:
            requires:
              - integration-test
        - validation-test:
            requires:
              - end-to-end-test
        - store-artifacts:
            requires:
              - validation-test
        - wait-for-decision:
            type: approval
            requires:
              - store-artifacts
        - submit:
            requires:
              - wait-for-decision

~~~

El archivo de configuración CircleCI se encuentra en `.circleci/config.yml`.

## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia
* [Documentación oficial del SDK de Node.js](https://www.npmjs.com/package/ask-sdk) - La documentación oficial del SDK de Node.js
* [Documentación oficial del Alexa Skills Kit](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - La documentación oficial del Alexa Skills Kit
* [Documentación oficial de CircleCI](https://circleci.com/docs/) - Documentación oficial de CircleCI

## Conclusión 

Este es el primer paso para saber cómo crear un pipeline DevOps de tus Skills de Alexa usando CircleCI.
Como has visto en este ejemplo, las herramientas de Alexa como ASK CLI pueden ayudarnos mucho. 
Escribiré nuevos posts cuando actualicé el pipeline.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld/blob/master/CICD.md)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
