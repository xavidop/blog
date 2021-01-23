---
layout: post
title: DevOps en tu Alexa Skill. Integration Tests.
image: /assets/img/blog/post-headers/alexa-integration-test.jpg
description: >
   Simulando diálogos usando texto como input
noindex: true
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

Las pruebas de integración aseguran que los componentes de una aplicación se estén ejecutando correctamente a un nivel que incluye toda la infraestructura de la aplicación, como la interfaz de usuario de voz, el backend y la integración con sistemas externos.

# DevOps en tu Alexa Skill: Integration Tests

Las pruebas de integración evalúan los componentes de una aplicación a un nivel más alto que las pruebas unitarias.
Las pruebas unitarias se utilizan para probar componentes de software aislados, como métodos de clases individuales.
Las pruebas de integración verifican que dos o más componentes de una aplicación funcionen juntos y generan un resultado esperado, incluyendo todos los componentes necesarios para procesar completamente una request.

Estos tests están automatizadas en el sistema de integración continua (CircleCI) y se ejecutan en cada nueva versión del software.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. CircleCI Account -  [Regístrate aquí gratis](https://circleci.com/)
5. Visual Studio Code

## ASK CLI (Alexa Skill Kit CLI)

La Alexa Skills Kit Command Line Interface (ASK CLI) es una herramienta para que puedas administrar tus Skills de Alexa y recursos relacionados, como las funciones de AWS Lambda.
Con la ASK CLI, tienes acceso a la Skill Management API, que te permite administrar las Skills de Alexa mediante programación desde la línea de comandos.
Usaremos esta poderosa herramienta para ejecutar los tests de integración. ¡Empecemos!

### Instalación

La ASK CLI y la herramienta bash `expect` se incluyen en la [Docker image](https://hub.docker.com/repository/docker/xavidop/alexa-ask-aws-cli) que estamos usando, por lo que no es necesario instalar nada más.

### Desarrollando integration tests

En este paso del pipeline vamos a desarrollar algunas pruebas escritas en bash usando ASK CLI.

Una vez que hayamos probado nuestra interfaz de usuario de voz y comprobado que todo está correcto.
Es hora de probar todos los componentes de software interelacionados en una request de Alexa.

Estas pruebas de integración se pueden realizar con ASK CLI. utilizaremos el siguiente comando ASK CLI:

1. Para ask cli v1 y v2:
```bash
    ask dialog -s ${skill_id} -l ${locale}
```

Con este comando realizaremos una simulación de un diálogo con nuestra Alexa Skill usando texto plano como entrada. Con esto, podemos probar que todos los componentes software estén funcionando correctamente.

Esos comandos están integrados en el archivo de script bash `test/integration-test/simple-dialog-checker.sh`.

Aquí podemos encontrar el script bash completo:

```bash
    #!/usr/bin/expect

    set skill_id [lindex $argv 0];

    spawn ask dialog -s ${skill_id} -l es-ES
    expect "User"
    send -- "abre hola mundo\r"
    expect "Bienvenido, puedes decir Hola o Ayuda. Cual prefieres?"
    send -- "hola\r"
    expect "Hola Mundo!"
    send -- "abre hola mundo\r"
    expect "Bienvenido, puedes decir Hola o Ayuda. Cual prefieres?"
    send -- "ayuda\r"
    expect "Puedes decirme hola. Cómo te puedo ayudar?"
    send -- "adios\r"
    expect "Hasta luego!"

```
### Informes

No hay informes definidos en este job.

### Integración

No es necesario integrarlo en el archivo `package.json`.

## Pipeline Jobs

Todo está listo para ejecutar y probar nuestro tests de integración, ¡agregémoslo a nuestro pipeline!

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Ejecutar el script `simple-dialog-checker`.
3. Conservar nuevamente el código que reutilizaremos en el próximo job

```yaml

  integration-test:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: cd test/integration-test/ && ./simple-dialog-checker.sh $SKILL_ID
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project

```

**NOTA:** Para realizar estas pruebas en CircleCI, debemos configurar la variable de entorno `SKILL_ID` con el ID de nuestra Alexa Skill.


## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia reference
* [Documentación Oficial Alexa Skill Management API](https://developer.amazon.com/es-ES/docs/alexa/smapi/skill-testing-operations.html) - Documentación Oficial Alexa Skill Management API
* [Documentación oficial de CircleCI](https://circleci.com/docs/) - Documentación oficial de CircleCI
  
## Conclusión 

Comprobar que todos los componentes de nuestra aplicación se estén ejecutando correctamente es una de las cosas más importantes en cada ejecución del pipeline.
Estas pruebas se utilizan para probar la infraestructura de la aplicación y sus componentes. Es por eso que estas pruebas son muy relevantes en nuestro pipeline.
Gracias al ASK CLI podemos realizar estas complejas pruebas.

También podemos escribir pruebas de integración con Bespoken. Ver documentación [aquí](https://read.bespoken.io/end-to-end/guide/#overview). Estabelciendo la prueba de tipo `simulación` en lugar de `e2e`

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld/blob/master/CICD.md)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
