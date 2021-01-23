---
layout: post
title: GitHub Action para el uso de la ASK CLI y Bespoken Tools
image: /assets/img/blog/post-headers/alexa-github-action.jpg
description: >
   GitHub Action para ejecutar comandos de la ASK CLI en worflows de GitHub Actions
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [alexa, devops, docker]
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

Siempre es buena práctica en el mundo de la programación intentar desarrollar cosas que sean reusables. Así cualquier persona puede integrar lo que se ha desarrollado y rápidamente puede comenzar a usarlo.

Esta es la filosofía que hay detrás de las GitHub Action. Pequeñas tarea individuales y reutilizables que podemos combinar para crear jobs y personalizar nuestros workflows de GitHub Actions.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. GitHub Account - [Regístrate aquí gratis](https://github.com/)
5. Visual Studio Code

La Alexa Skills Kit Command Line Interface (ASK CLI) es una herramienta para que podamos administrar nuestras Skills de Alexa y recursos relacionados, como las funciones de AWS Lambda.
Con la ASK CLI, tenemos acceso a la Skill Management API, que nos permite administrar las Skills de Alexa mediante la línea de comandos.

## GitHub Actions
  ![Full-width image](/assets/img/blog/tutorials/alexa-github-action/github-actions.jpg){:.lead data-width="800" data-height="100"}
GitHub Actions
  {:.figure}

GitHub Actions nos ayuda a automatizar tareas dentro del ciclo de vida del desarrollo de software. GitHub Actions esta controlado por eventos, lo que significa que podemos ejecutar una serie de comandos después de que haya ocurrido un evento específico. Por ejemplo, cada vez que alguien crea una pull request para un repositorio, podemos ejecutar automáticamente un pipeline en GitHub Actions.

Un evento activa automáticamente el `workflow`, que contiene uno o varios jobs. Luego, el `jobs` usa `steps` para controlar el orden en que se ejecutan las acciones. Estas acciones son los comandos que automatizan ciertos procesos.

## GitHub Action para ejecutar comandos de la ASK CLI

  ![Full-width image](/assets/img/blog/tutorials/alexa-github-action/github-action.png){:.lead data-width="800" data-height="100"}
GitHub Action
  {:.figure}

Una Action es una tarea individuales que podemos combinar para crear jobs y personalizar nuestros workflows de GitHub Actions. 
Podemos crear nuestras propias Actions o usar y personalizar Actions compartidas por la comunidad de GitHub.

Podemos crear una Action escribiendo código personalizado que interactúe con los repositorios de la forma que queramos, incluida la integración con las API de GitHub y cualquier API de terceros disponible públicamente. Por ejemplo, una Action puede publicar módulos npm, enviar alertas por SMS cuando haya algún problema urgente en el pipeline o hacer un deploy de nuestro código si está listo para producción.

Para compartir las Actions que hemos creado, el repositorio debe ser público.

Las Actions se pueden ejecutar directamente en una máquina o en un contenedor Docker. Podemos definir las entradas, salidas y variables de entorno de una Action.

Dicho esto, veamos el archivo de configuración de la GitHub Action que se encuentra en el fichero `action.yml`.

```yaml
{% raw %}

  # action.yml
  name: 'Alexa ASK AWS CLI Action'
  author: 'Xavier Portilla Edo'
  description: 'GitHub Action using Docker image for ASK and AWS CLI '
  branding:
    icon: 'activity'  
    color: 'blue'
  inputs:
    command:  # id of input
      description: 'Command to execute'
      required: true
      default: 'ask --version'
  outputs:
    result: # id of output
      description: 'The result of the command'
  runs:
    using: 'docker'
    image: './.github/action/Dockerfile'
    args:
      - ${{ inputs.command }}
{% endraw %}

```

Como se observa en el fichero anterior, la GitHub Action tiene como input un parámetro llamado `command` el cual será el comando de la ASK CLI que queramos ejecutar.
Este comando se ejecutará en un contendor docker específico cuyo Dockerfile viene especificado en la sección `run` de la GitHub Action. 
A este ejecutor Docker se le pasará el comando introducido mediante el parámetro de entrada `command` para su posterior ejecución y devolverá el resultado de la ejecución en el parámetro de salida `result` de la GitHub Action.

Esta GitHub Action utiliza como base la imagen Docker que hemos estado usando durante toda la [serie de posts sobre Devops](/alexa/devops/2020-09-11-alexa-devops-1) y que podéis encontrar [aquí](https://github.com/xavidop/alexa-ask-aws-cli-docker) para más información. Destacar que esta imagen ya tiene instalada la ASK CLI, las Bespoken Tools, Python, Git, la AWS CLI, entre otros.

Sin embargo, esta nueva imagen Docker que usa GitHub Action extiende de la [imagen Docker original](https://github.com/xavidop/alexa-ask-aws-cli-docker) anteriormente comentada. 

Esta segunda imagen Docker es exactamente igual que la mencionada pero se le ha añadido un `entrypoint`.

Esta nueva imagen Docker se puede encontrar en `.github/action/Dockerfile`:
 
```Dockerfile
  # Original source from https://hub.docker.com/repository/docker/xavidop/alexa-ask-aws-cli
  FROM xavidop/alexa-ask-aws-cli:latest
  LABEL maintainer="Xavier Portilla Edo <xavierportillaedo@gmail.com>"

  ADD --chown=node:node entrypoint.sh /home/node/entrypoint.sh

  RUN chmod 777 /home/node/entrypoint.sh

  ENTRYPOINT ["/home/node/entrypoint.sh"]
```

El `entrypoint` nuevo que le hemos añadido a esta nueva Dockerfile lo único que va a hacer va a ser ejecutar el comando que se le pase a través del parámetro de entrada de la GitHub Action `command`:

```bash

  #!/bin/bash
  result=$($1)
  echo "::set-output name=result::$result"

```
Como output, el `entrypoint` devolverá el resultado de la ejecución del comando recibido desde la GitHub Action a través del parámetro `command` en el formato requerido por GitHub.

Este formato es el siguiente: `::set-outpt name={ID_PARAMETRO_SALIDA}::{VALOR_PARAMETRO_SALIDA}`.

**NOTA:** Es importante añadir que la GitHub Action utiliza la última versión de ASK CLI.

### Ejemplo de uso

Podemos utilizar el siguiente ejemplo:
```yaml
{% raw %}
  - name: Alexa ASK AWS CLI Action
    uses: xavidop/alexa-ask-aws-cli-docker@v1.0.6
    id: command
    with:
      command: 'ask --version'
    env: # Or as an environment variable
      ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
      ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
      ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  # Use the output from the `hello` step
  - name: Get the output
    run: echo "The result was ${{ steps.command.outputs.result }}"
{% endraw %}
```

**NOTA:** Es importante mencionar que para que la GitHub Action funcione le debemos pasar todas las variables de entorno que necesita la ASK CLI como se observa en el ejemplo anterior.

### Uso de la Action en un workflow de GitHub Actions

Este es un ejemplo de cómo se puede integrar la GitHub Action en un workflow de GitHub Actions:

```yaml
{% raw %}
  on: [push]

  jobs:
    test-action:
      runs-on: ubuntu-latest
      name: Test Action
      steps:
        # To use this repository's private action,
        # you must check out the repository
        - name: Checkout
          uses: actions/checkout@v2
        - name: Test action step
          uses: xavidop/alexa-ask-aws-cli-docker@v1.0.6
          id: ask
          with:
            command: 'ask --version'
          env: # Or as an environment variable
            ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
            ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
            ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
            AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
            AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        # Use the output from the `hello` step
        - name: Get the output
          run: echo "The result was ${{ steps.ask.outputs.result }}"
{% endraw %}
```

### Testear la GitHub Action en cada commit

A su vez, hemos creado un workflow de GitHub Actions cuya única finalidad es comprobar que la Action funciona en cada nuevo commit que se hace al repo.
Así podemos detectar que los nuevos cambios que se hagan no romperán el funcionamiento actual de la Action.

Este workflow lo podéis encontrar en `.github/workflows/main.yaml`:

```yaml
{% raw %}
on: [push]

jobs:
  test-action:
    runs-on: ubuntu-latest
    name: Test Action
    steps:
      # To use this repository's private action,
      # you must check out the repository
      - name: Checkout
        uses: actions/checkout@v2
      - name: Test action step
        uses: ./
        id: ask
        with:
          command: 'ask --version'
        env: # Or as an environment variable
          ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
          ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
          ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          SKILL_ID: ${{ secrets.SKILL_ID }}
      # Use the output from the `hello` step
      - name: Get the output
        run: echo "The result was ${{ steps.ask.outputs.result }}"
{% endraw %}
```

Como se puede ver, en la propiedad `uses` del step `Test action step` del workflow, se le indica que coja la Action del directorio raíz del repositorio(`./`) en vez de coger la versión del marketplace(`xavidop/alexa-ask-aws-cli-docker@v1.0.6`)

## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia
* [Documentación oficial del SDK de Node.js](https://www.npmjs.com/package/ask-sdk) - La documentación oficial del SDK de Node.js
* [Documentación oficial del Alexa Skills Kit](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - La documentación oficial del Alexa Skills Kit
* [Documentación oficial de GitHub Actions](https://docs.github.com/) - Documentación oficial de GitHub Actions

## Conclusión 

Creando esta GitHub Action habilitamos a que cualquier desarrollador pueda ejecutar comandos de la ASK CLI y así que pueda automatizar procesos de sus Alexa Skills de una manera muy simple mediante la creación de pipelines de GitHub Actions. 

Puedes encontrar el código en mi [**GitHub**](https://github.com/xavidop/alexa-ask-aws-cli-docker) y la GitHub Action en el [marketplace oficial de GitHub Actions](https://github.com/marketplace/actions/alexa-ask-aws-cli-action).

¡Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
