---
layout: post
title: DevOps en tu Alexa Skill. Validation Tests.
image: /assets/img/blog/post-headers/alexa-validation.jpg
description: >
   Comprobar que nuestra Skill está lista para su certificación
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

Hay otro paso importante en el proceso de desarrollo de Alexa Skills. No está relacionado con el código o si la Skill y sus componentes se están ejecutando correctamente.
Este paso es la validación de nuestra Skill de Alexa antes de enviarla a certificación. Significa que los metadatos de nuestra Skill (logos, descripción, ejemplos, etc.) están correctamente rellenados. Podemos comprobarlo en nuestro pipeline gracias a ASK CLI y al uso de la Alexa Skill Management API.

# DevOps your Skill: Validation Tests

Uno de los pasos más importantes de nuestro pipeline es validar la Skill de Alexa.
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
Usaremos esta poderosa herramienta para ejecutar los tests de validación. ¡Empecemos!

### Instalación

La ASK CLI está incluida en la [Docker image](https://hub.docker.com/repository/docker/xavidop/alexa-ask-aws-cli) que estamos usando, por lo que no es necesario instalar nada más.

### Desarrollando tests

En este paso del pipeline vamos a desarrollar algunas pruebas escritas en bash usando ASK CLI.

La documentación oficial de Alexa dice que la API de validación de Skills de Alexa es una API asíncrona que los desarrolladores de Skills podemos utilizar para validar nuestras Skills antes de enviarlas a certificar o en cualquier momento durante el desarrollo como prueba de regresión.

Este es un proceso asincrónico. por lo que tenemos que comenzar la validación con un comando y luego obtener el resultado con otro cuando finalice la validación:

1. Para ask cli v1:
```bash
    #start the evaluation
    id=ask api validate-skill -s ${skill_id} -l ${locale}
    #get the results of the evaluation
    ask api get-validation -i ${id} -s ${skill_id}
```

2. Para ask cli v2:
```bash
    #start the evaluation
    id=ask smapi submit-skill-validation -s ${skill_id} -l ${locale} -g developmentx
    #get the results of the evaluation
    ask smapi get-skill-validations --validation-id ${id} -s ${skill_id} -g development
```

Estos comandos están integrados en el archivo de script bash `test/validation-test/skill_validation_checker.sh`.

Aquí podemos encontrar el script bash completo:

```bash
    #!/bin/bash
    skill_id=$1

    cli_version=$2

    echo "######### Checking validations #########"

    if [[ ${cli_version} == *"v1"* ]]
    then
        folder="../../models/*"
    else
        folder="../../skill-package/interactionModels/*"
    fi


    for d in ${folder}; do

        file_name="${d##*/}"
        locale="${file_name%.*}"

        echo "Checking validations for locale: ${locale}"
        echo "###############################"

        if [[ ${cli_version} == *"v1"* ]]
        then
            validations=$(ask api validate-skill -s ${skill_id} -l ${locale})
        else
            validations=$(ask smapi submit-skill-validation -s ${skill_id} -l ${locale} -g development)
        fi


        id=$(jq ".id" <<< ${validations})
        #Remove quotes
        id=$(echo "${id}" | sed 's/"//g')
        echo "Id of validation: ${id}"
        status="IN_PROGRESS"

        while [[ ${status} == *"IN_PROGRESS"* ]]; do

            if [[ ${cli_version} == *"v1"* ]]
            then
                status_raw=$(ask api get-validation -i ${id} -s ${skill_id})
            else
                status_raw=$(ask smapi get-skill-validations --validation-id ${id} -s ${skill_id} -g development)
            fi

            status=$(jq ".status" <<< ${status_raw})
            echo "Current status: ${status}"
            
            if [[ ${status} == *"IN_PROGRESS"* ]]
            then
                echo "Waiting for finishing the validation..."
                sleep 15
            fi

        done

        if [[ ${status} == *"SUCCESSFUL"* ]]
        then
            echo "Validation pass"
            exit 0
        else
            echo "Validation errors: ${status_raw}"
            exit 1
        fi

    done

```

La prueba detecta automáticamente si Alexa Skill está lista para enviar a certificación.

Este script tiene dos parámetros:
1. El id de la Skill
2. La versión de ASK CLI que se está ejecutando (v1 o v2).

### Informes

No hay informes definidos en este job.

### Integración

No es necesario integrarlo en el archivo `package.json`.

## Pipeline Jobs

Todo está listo para ejecutar y probar nuestro VUI, ¡agregémoslo a nuestro pipeline!

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Ejecutar el script `skill_validation_checker`.
3. Conservar nuevamente el código que reutilizaremos en el próximo job

```yaml
  validation-test:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: cd test/validation-test/ && ./skill_validation_checker.sh $SKILL_ID v1
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

Tenemos que tener en cuenta este tipo de pruebas. A pesar de que no estemos verificando el código, esta prueba validará que nuestra Skill de Alexa se verá realmente bien en la Tienda de Skills de la aplicación de Amazon Alexa, así que no olvidemos ejecutarla. Es por eso que estas pruebas son muy relevantes en nuestro pipeline.
Gracias al ASK CLI podemos realizar estas complejas pruebas.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld/blob/master/CICD.md)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
