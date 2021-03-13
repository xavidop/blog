---
layout: post
title: DevOps en tu Alexa Skill. Deploy.
image: /assets/img/blog/post-headers/alexa-deploy.jpg
description: >
   Despliegue de una Skill con la ASK CLI
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

Cuando se verifica el código en los pasos anteriores, es hora de desplegar la Skill de Alexa para comenzar los siguientes pasos que ejecutarán diferentes tipos de pruebas. 
Hay algunas pruebas como pruebas de VUI, pruebas de integración, pruebas end-to-end y pruebas de validación que no podemos ejecutar en localhost con nuestro código. 
Es por eso que necesitamos desplegar neustra Alexa Skill en el stage de desarrollo.

# DevOps en tu Alexa Skill: Deploy

Estos pasos están automatizadas en el sistema de integración continua (CircleCI) y se ejecutan en cada nueva versión del software.

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
Usaremos esta poderosa herramienta para desplegar nuestra Skill de Alexa. ¡Empecemos!

### Instalación

La ASK CLI está incluida en la [Docker image](https://hub.docker.com/repository/docker/xavidop/alexa-ask-aws-cli) que estamos usando, por lo que no es necesario instalar nada más.

### Deploy

En este paso del pipeline, desplegaremos nuestra Skill de Alexa usando ASK CLI en el stage de desarrollo.
Cuando desplegemos nuestra Skill en el stage de desarrollo, actualizaremos el manifest de nuestra Skill, lo sinteraction models, los Buckets, los In-Skill Purchasing products y el código lambda en el Cloud de Alexa y AWS.
Podemos usar los siguientes comandos en ASK CLI para desplegar nuestra Skill de Alexa:

1. Para ask cli v1:
```bash
    ask deploy --debug --force
```

2. Para ask cli v2:
```bash
    ask deploy --debug --ignore-hash
```

### Informes

No hay informes definidos en este job.

### Integración

No es necesario integrarlo en el archivo `package.json`.

## Pipeline Job

Todo está completamente instalado, configurado e integrado, ¡agregémoslo a nuestro pipeline!

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Copiar el archivo `package.json` en la carpeta `src/`.
3. Ejecutar el comando `npm run build-production` que instalará solo las librerías de producción en la carpeta `src/`.
4. Ejecutar `ask deploy --debug --force` que desplegará todo el código de la carpeta `src/`como una lambda de AWS.
5. Conservar nuevamente el código que reutilizaremos en el próximo job

```yaml
  deploy:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: cd lambda/custom && npm run copy-package
      - run: cd lambda/custom/src && npm run build-production
      - run: ask deploy --debug --force
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project
```
**NOTA:** Si queremos ejecutar con éxito todos los comandos ASK CLI, debemos configurar 5 variables de entorno:

* `ASK_DEFAULT_PROFILE`
* `ASK_ACCESS_TOKEN`
* `ASK_REFRESH_TOKEN`
* `ASK_VENDOR_ID`
* `AWS_ACCESS_KEY_ID`
* `AWS_SECRET_ACCESS_KEY`

Y configurar el perfil `__ENVIRONMENT_ASK_PROFILE__` en el archivo `.ask/config`.

Cómo obtener estas variables y cómo configurar este perfil se explica en [esta publicación](https://dzone.com/articles/docker-image-for-ask-and-aws-cli-1)

## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia reference
* [Documentación Oficial Alexa Skill Management API](https://developer.amazon.com/es-ES/docs/alexa/smapi/skill-testing-operations.html) - Documentación Oficial Alexa Skill Management API
* [Documentación oficial de CircleCI](https://circleci.com/docs/) - Documentación oficial de CircleCI

## Conclusión 

Gracias al ASK CLI podemos realizar esta compleja tarea.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld/blob/master/CICD.md)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
