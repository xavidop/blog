---
layout: post
title: Pipeline de una Alexa Skill con GitHub Actions
image: /assets/img/blog/post-headers/alexa-devops-github-actions.jpg
description: >
   Pipeline DevOps usando GitHub Actions  
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

Como vimos en el anterior [post](/alexa/devops/2020-09-11-alexa-devops-1), hemos desarrollado un pipeline entero para una Skill de Alexa usando CircleCI. Ahora vamos a construir lo mismo, pero usando la nueva herramienta de integración continua proporcionada por GitHub, GitHub Actions para así comprender su funcionamiento y ver las diferencias respecto a la anterior plataforma de CI/CD usada.

A su vez, vamos a utilizar la ASK CLI v2 y también utilizaremos una estructura de ficheros de una Alexa Skill proporcionada por esta nueva segunda versión.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. GitHub Account - [Regístrate aquí gratis](https://github.com/)
5. Visual Studio Code

La Alexa Skills Kit Command Line Interface (ASK CLI) es una herramienta para que podamos administrar nuestras Skills de Alexa y recursos relacionados, como las funciones de AWS Lambda.
Con la ASK CLI, tenemos acceso a la Skill Management API, que nos permite administrar las Skills de Alexa mediante la línea de comandos.

Si quieres crear una Skill con ASK CLI v2, sigue los pasos descritos en la [documentación oficial de Amazon Alexa](https://developer.amazon.com/en-US/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html). 

Vamos a utilizar esta herramienta para realizar algunos pasos en nuestro pipeline. 

¡Let's DevOps!

## GitHub Actions
  ![Full-width image](/assets/img/blog/tutorials/alexa-github-actions/github-actions.jpg){:.lead data-width="800" data-height="100"}
GitHub Actions
  {:.figure}

GitHub Actions nos ayuda a automatizar tareas dentro del ciclo de vida del desarrollo de software. GitHub Actions está controlado por eventos, lo que significa que podemos ejecutar una serie de comandos después de que haya ocurrido un evento específico. Por ejemplo, cada vez que alguien crea una pull request para un repositorio, podemos ejecutar automáticamente un pipeline en GitHub Actions.

Un evento activa automáticamente el `workflow`, que contiene uno o varios jobs. Luego, el `jobs` usa `steps` para controlar el orden en que se ejecutan las acciones. Estas acciones son los comandos que automatizan ciertos procesos.

## Pipeline

  ![Full-width image](/assets/img/blog/tutorials/alexa-github-actions/pipeline.png){:.lead data-width="800" data-height="100"}
GitHub Actions Pipeline
  {:.figure}

Vamos a explicar job por job lo que está sucediendo en nuestro pipeline.
En primer lugar, los jobs del workflow se definirán debajo del nodo `jobs` en el archivo de configuración de GitHub Actions:

### Checkout

El job de checkout ejecutará las siguientes tareas:
1. Checkout del código.
2. Dar permiso de ejecución para poder ejecutar todos los tests

```yaml
  checkout:
    runs-on: ubuntu-latest
    name: Checkout
    steps:
      # To use this repository's private action,
      # you must check out the repository
      - name: Checkout
        uses: actions/checkout@v2
      - run: |
          chmod +x -R ./test;
          ls -la
```

### build

El job de build ejecutará las siguientes tareas:
1. Checkout del código.
2. Ejecutar `npm install` para descargar todas las dependencias de Node.js

```yaml
  build:
    runs-on: ubuntu-latest
    name: Build
    needs: checkout
    steps:
      # To use this repository's private action,
      # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        cd lambda;
        npm install

```

### Pretests

El job de pretest ejecutará el checkeo de calidad del código estático. Consulta la explicación completa [aquí](https://github.com/xavidop/alexa-nodejs-lambda-helloworld-v2/blob/master/docs/ESLINT.md).

### Test

El job de test ejecutará las pruebas unitarias. Consulta la explicación completa [aquí](https://github.com/xavidop/alexa-nodejs-lambda-helloworld-v2/blob/master/docs/UNITTESTS.md).

### Code Coverage

El job codecov ejecutará el informe de cobertura de código. Consulta la explicación completa [aquí](https://github.com/xavidop/alexa-nodejs-lambda-helloworld-v2/blob/master/docs/CODECOV.md).

### Deploy

El job de deploy desplegará la Skill de Alexa en la nube de Alexa en el stage de development. Consulta la explicación completa [aquí](https://github.com/xavidop/alexa-nodejs-lambda-helloworld-v2/blob/master/docs/DEPLOY.md).

### Testing de la Voice User Interface

Estos jobs verificarán nuestro interaction model. Consulta la explicación completa [aquí](https://github.com/xavidop/alexa-nodejs-lambda-helloworld-v2/blob/master/docs/VUITESTS.md).

### Integration tests

Estos jobs verificarán el interaction model y nuestro backend también. Consulta la explicación completa [aquí](https://github.com/xavidop/alexa-nodejs-lambda-helloworld-v2/blob/master/docs/INTEGRATIONTESTS.md).

### End to end tests

  ![Full-width image](/assets/img/blog/tutorials/alexa-github-actions/bespoken.png){:.lead data-width="800" data-height="100"}
Bespoken
{:.figure}


Estos jobs verificarán el sistema completo utilizando la voz como entrada gracias a Bespoken. Consulta la explicación completa [aquí](https://github.com/xavidop/alexa-nodejs-lambda-helloworld-v2/blob/master/docs/ENDTOENDTESTS.md).

### Validation tests

Estos jobs validarán la Skill de Alexa antes de enviarla a certificación. Consulta la explicación completa [aquí](https://github.com/xavidop/alexa-nodejs-lambda-helloworld-v2/blob/master/docs/VALIDATIONTESTS.md).

### Store-artifacts

El job de store-artifacts ejecutará las siguientes tareas:
1. Descargar el código.
2. Almacenar el código completo de nuestra Skill de Alexa como un artefacto. Será accesible en GitHub Actions cuando queramos verlo.

```yaml
{% raw %}
  store-artifacts:
    runs-on: ubuntu-latest
    name: Submit
    needs: submit
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2}
    - name: Upload code
      uses: actions/upload-artifact@v2
      with:
        name: code
        path: ${{ github.workspace }}
{% endraw %}
```

### Submit

Estos jobs enviarán la Skill de Alexa a certificación. Consulta la explicación completa [aquí](https://github.com/xavidop/alexa-nodejs-lambda-helloworld-v2/blob/master/docs/SUBMIT.md).

### Workflow

Al final del archivo de configuración GitHub Actions, definiremos nuestro pipeline como un workflow de GitHub Actions que ejecutará los jobs explicados anteriormente:

```yaml
{% raw %}

on: [push]

jobs:
  checkout:
    runs-on: ubuntu-latest
    name: Checkout
    steps:
      # To use this repository's private action,
      # you must check out the repository
      - name: Checkout
        uses: actions/checkout@v2
      - run: |
          chmod +x -R ./test;
          ls -la

  build:
    runs-on: ubuntu-latest
    name: Build
    needs: checkout
    steps:
      # To use this repository's private action,
      # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        cd lambda;
        npm install

  pretest:
    runs-on: ubuntu-latest
    name: Pre-test
    needs: build
    steps:
    # To use this repository's private action,
    # you must check out the repository
      # To use this repository's private action,
      # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        cd lambda;
        npm install;
        npm run lint;
        npm run lint-html
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: eslint-report
        path: lambda/reports/eslint/

  test:
    runs-on: ubuntu-latest
    name: Test
    needs: pretest
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        cd lambda;
        npm install;
        npm run test
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: unit-tests-report-html
        path: lambda/mochawesome-report/
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: unit-tests-report-xml
        path: lambda/reports/mocha/
    
  codecov:
    runs-on: ubuntu-latest
    name: Code Coverage
    needs: test
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        cd lambda;
        npm install;
        npm run codecov
      env: # Or as an environment variable
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

  deploy:
    runs-on: ubuntu-latest
    name: Deploy
    needs: codecov
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        sudo npm install -g ask-cli;
        sudo apt-get install -y jq
        cd lambda;
        npm install;
        npm run copy-package;
        cd src;
        npm run build-production
    - run: ls -la && ask deploy --ignore-hash  
      env: # Or as an environment variable
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
        ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
        ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
        ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        SKILL_ID: ${{ secrets.SKILL_ID }}

  check-utterance-conflicts:
    runs-on: ubuntu-latest
    name: Check Utterance Conflicts
    needs: deploy
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        sudo npm install -g ask-cli;
        chmod +x -R ./test;
        cd test/vui-test/;
        ./interaction_model_checker.sh $SKILL_ID v2
      env: # Or as an environment variable
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
        ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
        ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
        ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        SKILL_ID: ${{ secrets.SKILL_ID }}

  check-utterance-resolution:
    runs-on: ubuntu-latest
    name: Check Utterance Resolution
    needs: deploy
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        sudo npm install -g ask-cli;
        chmod +x -R ./test;
        cd test/vui-test/;
        ./utterance_resolution_checker.sh $SKILL_ID v2
      env: # Or as an environment variable
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
        ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
        ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
        ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        SKILL_ID: ${{ secrets.SKILL_ID }}

  check-utterance-evaluation:
    runs-on: ubuntu-latest
    name: Check Utterance Evaluation
    needs: deploy
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        sudo npm install -g ask-cli;
        chmod +x -R ./test;
        cd test/vui-test/;
        ./utterance_evaluation_checker.sh $SKILL_ID v2
      env: # Or as an environment variable
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
        ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
        ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
        ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        SKILL_ID: ${{ secrets.SKILL_ID }}

  integration-test:
    runs-on: ubuntu-latest
    name: Integration test
    needs: check-utterance-evaluation
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        sudo npm install -g ask-cli;
        chmod +x -R ./test;
        sudo apt-get install -y expect
        cd test/integration-test/;
        ./simple-dialog-checker.sh $SKILL_ID
      env: # Or as an environment variable
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
        ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
        ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
        ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        SKILL_ID: ${{ secrets.SKILL_ID }}

  end-to-test:
    runs-on: ubuntu-latest
    name: End-to-end test
    needs: integration-test
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        sudo npm install -g ask-cli;
        sudo npm install -g bespoken-tools;
        chmod +x -R ./test;
        bst test --config test/e2e-bespoken-test/testing.json
      env: # Or as an environment variable
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
        ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
        ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
        ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        SKILL_ID: ${{ secrets.SKILL_ID }}
    - name: Upload code
      uses: actions/upload-artifact@v2
      with:
        name: bespoken-report
        path: test_output/
  
  validation-test:
    runs-on: ubuntu-latest
    name: Validation test
    needs: end-to-test
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        sudo npm install -g ask-cli;
        chmod +x -R ./test;
        cd test/validation-test/;
        ./skill_validation_checker.sh $SKILL_ID v2
      env: # Or as an environment variable
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
        ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
        ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
        ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        SKILL_ID: ${{ secrets.SKILL_ID }}
    
  submit:
    runs-on: ubuntu-latest
    name: Submit
    needs: validation-test
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - run: |
        sudo npm install -g ask-cli;
        chmod +x -R ./test;
        cd test/submit/;
        ./submit.sh $SKILL_ID v2
      env: # Or as an environment variable
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
        ASK_ACCESS_TOKEN: ${{ secrets.ASK_ACCESS_TOKEN }}
        ASK_REFRESH_TOKEN: ${{ secrets.ASK_REFRESH_TOKEN }}
        ASK_VENDOR_ID: ${{ secrets.ASK_VENDOR_ID }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        SKILL_ID: ${{ secrets.SKILL_ID }}

  store-artifacts:
    runs-on: ubuntu-latest
    name: Store Artifacts
    needs: submit
    steps:
    # To use this repository's private action,
    # you must check out the repository
    - name: Checkout
      uses: actions/checkout@v2
    - name: Upload code
      uses: actions/upload-artifact@v2
      with:
        name: code
        path: ${{ github.workspace }}
{% endraw %}
```

El archivo de configuración GitHub Actions se encuentra en `.github/workflows/main.yml`.

## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia
* [Documentación oficial del SDK de Node.js](https://www.npmjs.com/package/ask-sdk) - La documentación oficial del SDK de Node.js
* [Documentación oficial del Alexa Skills Kit](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - La documentación oficial del Alexa Skills Kit
* [Documentación oficial de GitHub Actions](https://docs.github.com/) - Documentación oficial de GitHub Actions

## Conclusión 

Habiendo desarrollado el mismo pipeline en CircleCI como se puede leer en este [post](/alexa/devops/2020-09-11-alexa-devops-1), podemos sacar las siguientes conclusiones en base a los problemas que nos hemos encontrado durante el desarrollo de este proyecto:
1. GitHub Actions es una plataforma muy joven (apenas tiene año y medio de vida).
2. Podemos encontrar funcionalidad básica para cualquier pipeline de DevOps (flujos de control, steps de aprobación manual, etc.) que no está disponible aún en GitHub Actions.
3. Ejecutar comandos en un contenedor Docker específico solo es posible a través de las Actions disponibles en su [marketplace](https://github.com/marketplace). Debido a esto, complica un poco el trabajo con ejecutores Docker en esta plataforma.

Puedes encontrar el código en mi [**GitHub**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld-v2/blob/master/CICD.md)

¡Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
