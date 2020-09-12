---
layout: post
title: DevOps en tu Alexa Skill. Submit.
image: /assets/img/blog/post-headers/alexa-submit.jpg
description: >
   Submitear una Skill para certificar
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
Este es el último paso de nuestro pipeline. Anteriormente, hemos realizado muchas pruebas diferentes y, si todo está bien, es hora de enviar nuestra Skill de Alexa a certificación. Es decir, hemos concluido la parte de integración continua.

# DevOps en tu Alexa Skill: Submit

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
Usaremos esta poderosa herramienta para submitear la Skill. ¡Empecemos!

### Instalación

La ASK CLI está incluida en la [Docker image](https://hub.docker.com/repository/docker/xavidop/alexa-ask-aws-cli) que estamos usando, por lo que no es necesario instalar nada más.

### Submit

En este paso del pipeline, vamos a enviar nuestra Skill de Alexa utilizando ASK CLI.
Cuando enviamos nuestra Skill a la Tienda, debe pasar un proceso de certificación por parte personal de Amazon antes de que pueda publicarse a los usuarios finales de Amazon Alexa.
Podemos utilizar los siguientes comandos de la Alexa Skill Management API (SMAPI) para gestionar la certificación y publicación de una Skill de Alexa.
En nuestro caso, solo enviaremos a certificar y no la publicaremos automáticamente, solo certificaremos.

1. Para ask cli v1:
```bash
    ask api submit -s ${skill_id} --publication-method MANUAL_PUBLISHING
```

2. Para ask cli v2:
```bash
    ask smapi submit-skill-for-certification -s ${skill_id} --publication-method MANUAL_PUBLISHING
```

Estos comandos están integrados en el archivo de script bash `test/submit/submit.sh`.

Aquí podemos encontrar el script bash completo:

```bash
    #!/bin/bash
    skill_id=$1

    cli_version=$2

    echo "######### Submiting Skill for certification without publishing #########"

    if [[ ${cli_version} == *"v1"* ]]
    then
        submit=$(ask api submit -s ${skill_id} --publication-method MANUAL_PUBLISHING)
        exit 0
    else
        submit=$(ask smapi submit-skill-for-certification -s ${skill_id} --publication-method MANUAL_PUBLISHING)
        exit 0
    fi
```

Este script tiene dos parámetros:
1. El id de la Skill
2. La versión de ASK CLI que se está ejecutando (v1 o v2). 

### Informes

No hay informes definidos en este trabajo.

Pero podemos ver en la [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask) el nuevo estado de nuestra Skill de Alexa en la pestaña Certificación:

![Full-width image](/assets/img/blog/tutorials/alexa-devops/submit.jpg){:.lead data-width="800" data-height="100"}
Skill enviada a certificación
  {:.figure}

### Integración

No es necesario integrarlo en el archivo `package.json`.

## Pipeline Job

Everything is ready to submit our Alexa Skill, let's add it to our pipeline!

Todo está listo para ejecutar y probar nuestro VUI, ¡agregémoslo a nuestro pipeline!

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Ejecutar el script `submit`.

```yaml
  submit:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: cd test/submit/ && ./submit.sh $SKILL_ID v1
```

**NOTE:** To perform these tests in CircleCI you have to set the environment variable `SKILL_ID` with the id of your Alexa Skill.


## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia reference
* [Documentación Oficial Alexa Skill Management API](https://developer.amazon.com/es-ES/docs/alexa/smapi/skill-testing-operations.html) - Documentación Oficial Alexa Skill Management API
* [Documentación oficial de CircleCI](https://circleci.com/docs/) - Documentación oficial de CircleCI

## Conclusión 

Gracias al ASK CLI podemos realizar esta compleja tarea.
Este es el final, ¡gracias por leerlo hasta aquí!

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld/blob/master/CICD.md)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
