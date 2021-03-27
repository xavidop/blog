---
layout: post
title: DevOps en tu Alexa Skill. VUI (Voice User Interface) Tests.
image: /assets/img/blog/post-headers/alexa-test-vui.jpg
description: >
  Pruebas de la VUI (Voice User Interface) con ASK CLI
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

Según la definición de Wikipedia, "la Voice User Interface (VUI) permite la interacción humana con las computadoras a través de una plataforma de voz para iniciar procesos o servicios de manera automática. la VUI es la interfaz de cualquier aplicación de voz".

# DevOps en tu Alexa Skill: VUI (Voice User Interface) Tests

Gracias al aprendizaje automático, el big data, la nube y la inteligencia artificial hemos conseguido comunicarnos con los "ordenadores" a través de la forma de comunicación más natural del ser humano: el habla.
Uno de los pasos más importantes de nuestro pipeline es probar la VUI ya que es la interfaz de nuestra Skill de Alexa.
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
Usaremos esta poderosa herramienta para probar nuestra VUI. ¡Empecemos!

### Instalación

La ASK CLI está incluida en la [Docker image](https://hub.docker.com/repository/docker/xavidop/alexa-ask-aws-cli) que estamos usando, por lo que no es necesario instalar nada más.

### Desarrollando Tests

En este paso del pipeline vamos a desarrollar algunas pruebas escritas en bash usando ASK CLI.

Estas pruebas son las siguientes:

#### 1. Detectar Utterance conflicts

Una vez hayamos subido la Skill de Alexa en el job de `deploy`, es hora de saber si el interaction model que hemos subido tiene conflictos.

Para conocer los conflictos usaremos el comando ASK CLI:

1. Para ask cli v1:
~~~bash
    ask api get-conflicts -s ${skill_id} -l ${locale}
~~~

2. Para ask cli v2:
~~~bash
    ask smapi get-conflicts-for-interaction-model -s ${skill_id} -l ${locale} -g development --vers ~current
~~~

Esos comandos están integrados en el archivo de script bash `test/vui-test/interactive_model_checker.sh`.

Aquí podemos encontrar el script bash completo:

~~~bash
    #!/bin/bash
    skill_id=$1

    cli_version=$2

    echo "######### Checking Conflicts #########"

    if [[ ${cli_version} == *"v1"* ]]
    then
        folder="../models/*"
    else
        folder="../skill-package/interactionModels/*"
    fi

    for d in ${folder}; do

        file_name="${d##*/}"
        locale="${file_name%.*}"

        echo "Checking conflicts for locale: ${locale}"
        echo "###############################"

        if [[ ${cli_version} == *"v1"* ]]
        then
            conflicts=$(ask api get-conflicts -s ${skill_id} -l ${locale})
        else
            conflicts=$(ask smapi get-conflicts-for-interaction-model -s ${skill_id} -l ${locale} -g development --vers ~current)
        fi

        number_conflicts=$(jq ".paginationContext.totalCount" <<< ${conflicts})

        if [[ -z ${number_conflicts} || ${number_conflicts} == "null" ]]
        then
            echo "No Conflicts detected"
            exit 0
        else
            echo "Number of conflicts detected: ${number_conflicts}"
            echo "Conflicts: ${conflicts}"
            exit 1
        fi

    done
~~~

La prueba detecta automáticamente los diferentes modelos de interacción de la Skill y comprueba sus conflictos.
Este script tiene dos parámetros:
1. El id de la Skill
2. La versión de ASK CLI que se está ejecutando (v1 o v2).

#### 2. Pruebas de resolución de utterances

Ahora es el momento de comprobar la resolución de los utterances de nuestra interfaz de usuario de voz.
Podemos probar la resoluciones de utterances con el Utterance Profiler a medida que creamos nuestro interaction model.
Podemos evaluar utterances y ver cómo se resuelven según los intents y los slots definidos.
Cuando un utterance no invoca el intent correcto, podemos actualizar nuestros utterances de ejemplo y volver a probar, todo esto antes de escribir cualquier código en el backend de nuestra Skill.

Para ejecutar resoluciones de utterances, usaremos el comando ASK CLI:

1. Para ask cli v1:
~~~bash
    ask api nlu-profile -s ${skill_id} -l ${locale} --utterance "${utterance}"
~~~

2. Para ask cli v2:
~~~bash
    ask smapi profile-nlu -s ${skill_id} -l ${locale} --utterance "${utterance}" -g development
~~~

Estos comandos están integrados en el archivo de script bash `test/vui-test/utterance_resolution_checker.sh`.

Aquí podemos encontrar el script bash completo:

~~~bash
    #!/bin/bash
    skill_id=$1

    cli_version=$2

    echo "######### Checking Utterance Resolutions #########"

    if [[ ${cli_version} == *"v1"* ]]
    then
        folder="../models/*"
    else
        folder="../skill-package/interactionModels/*"
    fi

    for d in  ${folder}; do

        file_name="${d##*/}"
        locale="${file_name%.*}"

        echo "Checking Utterance resolution for locale: ${locale}"
        echo "###############################"

        while IFS="" read -r  utterance_to_test || [ -n "${utterance_to_test}" ]; do

            IFS=$'|' read -r -a utterance_to_test <<< "${utterance_to_test}"
            utterance=${utterance_to_test[0]}
            echo "Utterance to test: ${utterance}"
            expected_intent=${utterance_to_test[1]}
            #clean end of lines
            expected_intent=$(echo ${expected_intent} | sed -e 's/\r//g')

            echo "Expected intent: ${expected_intent}"

            if [[ ${cli_version} == *"v1"* ]]
            then
                resolution=$(ask api nlu-profile -s ${skill_id} -l ${locale} --utterance "${utterance}")
            else
                resolution=$(ask smapi profile-nlu -s ${skill_id} -l ${locale} --utterance "${utterance}" -g development)
            fi

            intent_resolved=$(jq ".selectedIntent.name" <<< ${resolution})

            echo "Intent resolved: ${intent_resolved}"

            if [[ ${intent_resolved} == *"${expected_intent}"* ]]
            then
                echo "No Utterance resolutions errors"
            else
                echo "Utterance resolution error"
                echo "Resolution: ${resolution}"
                exit 1
            fi

        done < "utterance_resolution/${locale}"

    done
~~~

Además, tenemos un conjunto de utterances y los intents esperados por idioma. Este conjunto de utterances para las pruebas están disponibles en `test/utterance_resolution`.
En nuestro caso, esta Skill solo está disponible en español por lo que podemos encontrar en esa carpeta el archivo `es-ES`:

~~~bash
    hola|HelloWorldIntent
    ayuda|AMAZON.HelpIntent 
~~~

Como podemos ver, el formato de este archivo es `Utterance|ExpectedIntent`. Podríamos verificar la resolución de los slots, pero yo no lo hice en este ejemplo.

La prueba detecta automáticamente los diferentes modelos de interacción de la Skill y comprueba la resolución de utterances.
Este script tiene dos parámetros:
1. El id de la Skill
2. La versión de ASK CLI que se está ejecutando (v1 o v2).

#### 3. Evalar y probar nuestro interaction model

Para evaluar nuestro modelo de interacción, definimos un conjunto de utterances junto con los intents y slots esperados cuando se invoque nuestra Skill. Esto se llama annotations sets. 
Posteriormente, comenzamos la evaluación del NLU con el conjunto de annotations que nos hemos creado para determinar qué tan bien se desempeña el interaction model de nuestra Skill frente a lo esperado.
La herramienta puede ayudarnos a medir la precisión de nuestro modelo NLU y ejecutar pruebas de regresión para asegurarse de que los cambios en nuestro modelo no degraden la experiencia del usuario final.

Esta prueba comprobará lo mismo que hemos comprobado en la prueba descrita anteriormente pero de una forma diferente. En esta prueba vamos a probar la resolución de utterances mediante annotations.
En primer lugar, tenemos que crear annotations en todas las configuraciones regionales que tenemos disponibles en nuestra Skill.

Para saber cómo crear una annotation, consulta este [enlace](https://developer.amazon.com/en-US/docs/alexa/custom-skills/batch-test-your-nlu-model.html#create-annotations) de la documentación oficial.

Cuando tengamos las annotations creadas, ahora podemos verificar la resolución de utterances usando estas annotations con los comandos de la ASK CLI.
Este es un proceso asincrónico. por lo que tenemos que comenzar la evaluación con un comando y luego obtener el resultado con otro cuando finalice la evaluación:

1. Para ask cli v1:
~~~bash
    #start the evaluation
    id=ask api evaluate-nlu -a ${annotation} -s ${skill_id} -l ${locale}
    #get the results of the evaluation
    ask api get-nlu-evaluation -e ${id} -s ${skill_id}
~~~

2. Para ask cli v2:
~~~bash
    #start the evaluation
    id=ask smapi create-nlu-evaluations --source-annotation-id ${annotation} -s ${skill_id} -l ${locale} -g development
    #get the results of the evaluation
    ask smapi get-nlu-evaluation --evaluation-id ${id} -s ${skill_id}
~~~

Estos comandos están integrados en el archivo de script bash `test/vui-test/utterance_evaluation_checker.sh`.

Aquí puede encontrar el script bash completo:

~~~bash
    #!/bin/bash
    skill_id=$1

    cli_version=$2

    echo "######### Checking Utterance Evaluation #########"

    if [[ ${cli_version} == *"v1"* ]]
    then
        folder="../models/*"
    else
        folder="../skill-package/interactionModels/*"
    fi

    for d in ${folder}; do

        file_name="${d##*/}"
        locale="${file_name%.*}"

        echo "Checking Utterance evaluation for locale: ${locale}"
        echo "###############################"

        while IFS="" read -r  annotation || [ -n "${annotation}" ]; do

            #clean end of lines
            annotation=$(echo ${annotation} | sed -e 's/\r//g')
            echo "Annotation to test: ${annotation}"
            if [[ ${cli_version} == *"v1"* ]]
            then
                evaluation=$(ask api evaluate-nlu -a ${annotation} -s ${skill_id} -l ${locale})
            else
                evaluation=$(ask smapi create-nlu-evaluations --source-annotation-id ${annotation} -s ${skill_id} -l ${locale} -g development)
            fi

            id=$(jq ".id" <<< ${evaluation})
            #Remove quotes
            id=$(echo "${id}" | sed 's/"//g')
            echo "Id of evaluation: ${id}"
            status="IN_PROGRESS"

            while [[ ${status} == *"IN_PROGRESS"* ]]; do

                if [[ ${cli_version} == *"v1"* ]]
                then
                    status_raw=$(ask api get-nlu-evaluation -e ${id} -s ${skill_id})
                else
                    status_raw=$(ask smapi get-nlu-evaluation --evaluation-id ${id} -s ${skill_id})
                fi

                status=$(jq ".status" <<< ${status_raw})
                echo "Current status: ${status}"
                
                if [[ ${status} == *"IN_PROGRESS"* ]]
                then
                    echo "Waiting for finishing the evaluation..."
                    sleep 15
                fi

            done

            echo "Utterance evaluation finished"

            if [[ ${status} == *"PASSED"* ]]
            then
                echo "No Utterance evaluation errors"
            else
                echo "Utterance evaluation error"
                echo "Evaluation: ${status_raw}"
                exit 1
            fi

        done < "utterance_evaluation/${locale}"

    done

~~~

Además, tenemos un conjunto de annotations según la configuración regional.
Este conjunto de annotations para las pruebas está disponible en `test/utterance_evaluation`. En nuestro caso, esta Skill solo está disponible en español por lo que podemos encontrar en esa carpeta el archivo `es-ES`:

~~~bash
    bcdcd3d8-ed74-4751-bb9f-5d1a4d02259c
~~~

Como podeomos ver, esta es el id de la annotation que hemos creado en la Alexa Developer Console. Si tenemos más de uno, simplemente lo añadimos en una nueva línea.
La prueba detecta automáticamente los diferentes modelos de interacción de la Skill y ejecuta la evaluación de las annotations dadas.

Este script tiene dos parámetros:
1. El id de la Skill
2. La versión de ASK CLI que se está ejecutando (v1 o v2).

### Informes

No hay informes definidos en este job.

### Integración

No es necesario integrarlo en el archivo `package.json`.

## Pipeline Jobs

Todo está listo para ejecutar y probar nuestro VUI, ¡agregémoslo a nuestro pipeline!

Estas 3 pruebas descritas anteriormente se definen en tres jobs diferentes que se ejecutarán en paralelo:

### 1. check-utterance-conflicts

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2.  Ejecutar el script `interaction_model_checker`.

~~~yaml
  check-utterance-conflicts:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: cd test/vui-test/ && ./interaction_model_checker.sh $SKILL_ID v1
~~~

### 2. check-utterance-resolution

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Ejecutar el script `utterance_resolution_checker`.

~~~yaml
  check-utterance-resolution:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: cd test/vui-test/ && ./utterance_resolution_checker.sh $SKILL_ID v1
~~~

### 3. check-utterance-evaluation

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Ejecutar el script `utterance_evaluation_checker`.
3. Conservar nuevamente el código que reutilizaremos en el próximo job

~~~yaml
  check-utterance-evaluation:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: cd test/vui-test/ && ./utterance_evaluation_checker.sh $SKILL_ID v1
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project
~~~

**NOTA:** Para realizar estas pruebas en CircleCI, debemos configurar la variable de entorno `SKILL_ID` con el ID de nuestra Alexa Skill.

## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia reference
* [Documentación Oficial Alexa Skill Management API](https://developer.amazon.com/es-ES/docs/alexa/smapi/skill-testing-operations.html) - Documentación Oficial Alexa Skill Management API
* [Documentación oficial de CircleCI](https://circleci.com/docs/) - Documentación oficial de CircleCI

## Conclusión 

La VUI es nuestra interfaz y una de las cosas más importantes de nuestra Skill de Alexa. Es por eso que estas pruebas son muy relevantes en nuestro pipeline.
Gracias al ASK CLI podemos realizar esta compleja tarea.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld/blob/master/CICD.md)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
