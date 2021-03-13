---
layout: post
title: DevOps en tu Alexa Skill. Análisis de código estático.
image: /assets/img/blog/post-headers/alexa-static-code.jpg
description: >
   ESLint como Code Style Checker
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

Sin duda, uno de los aspectos a los que debe prestar más atención un desarrollador es intentar generar siempre código claro, comprensibles y mantenible, en definitiva, generar código limpio.

# DevOps en tu Alexa Skill. Análisis de código estático.

Durante el desarrollo del código (módulos, librerías) es importante integrar herramientas objetivas que midan el estado del código y brinden la información para conocer su calidad y así poder detectar y prevenir problemas: funciones duplicadas, métodos excesivamente complejos, estilo de codificación no estándar o de baja calidad.

Estas comprobaciones están automatizadas en el sistema de integración continua (CircleCI) y se ejecutan en cada nueva versión del software.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. CircleCI Account -  [Regístrate aquí gratis](https://circleci.com/)
5. Visual Studio Code

## ESLint

ESLint es una herramienta para identificar e informar sobre patrones encontrados en código ECMAScript/JavaScript, con el objetivo de hacer que el código sea más consistente y evitar errores.
Podemos encontrar dos tipos de reglas. Algunas destinadas a garantizar la calidad de nuestro código,
como la detección de variables declaradas o funciones que no están siendo utilizadas en nuestro código, y otras orientadas a garantizar que el formato de nuestro código mantenga cierta homogeneidad, como el uso de punto y coma al final de nuestras instrucciones, espaciado, etc.

ESLint nos permite arreglar automáticamente casi todas las reglas.

### Instalación

Podemos instalar ESLint usando npm. `--save-dev` se usa para guardar el paquete npm con fines de desarrollo. Ejemplo: pruebas unitarias, minificación.

```bash
    npm install eslint --save-dev
```

### Configuración

Una vez que tenemos ESLint instalado ahora tenemos que configurarlo. Con ESLint puedes definir tus propias reglas y, además, también puedes utilizar un conjunto de reglas definidas por muchas grandes empresas como AirBnb, Facebook o Google. La mayoría de los paquetes npm utilizan este conjunto de reglas.

En nuestro caso vamos a utilizar el conjunto de reglas StrongLoop de IBM. Este paquete se puede instalar con el siguiente comando:

```bash
    npm install --save-dev eslint-config-strongloop
```

Ahora es el momento de configurar este conjunto de reglas. Primero, tenemos que crear el archivo `.eslintrc.json` en la carpeta `lambda/custom`:

```json
    {
        "extends": "strongloop",
        "parserOptions": {
            "ecmaVersion": 2019
        },

        "env": {
            "es6": true,
            "node": true,
            "mocha": true
        },
        "rules":{
            "max-len": [2, 120, 2]
        }
    }

```

Como se puede ver, ampliamos las reglas de strongloop y agregamos algunas configuraciones adicionales:

1. Establecemos el `ecmaVersion` a 2019 para verificar el código con el formato moderno del estándar JavaScript.
2. En el `env` establecemos a true las siguientes propiedades:
   1. `es6` como `ecmaVersion`, esto se debe a la versión de JavaScript.
   2. `node` porque estamos en un proyecto de Node.js.
   3. `mocha` debido al uso de esta librería en nuestras pruebas unitarias.
3. Finalmente, hemos cambiado la regla `max-len` configurándola en 120 caracteres en lugar de 80 definidos por el conjunto de reglas `strongloop`.

El último paso es definir el `.eslintignore` ubicado en la misma carpeta para poder especificar los archivos que no queremos verificar su estilo.

Es algo así como el archivo `.gitignore`:

```properties
    node_modules/
    package-lock.json
    .DS_Store
    local-debugger.js
    *.xml
    mochawesome-report/
    .nyc_output/
    *.lcov
```

### Informes

Una vez que tenemos todo configurado, tenemos que configurar los informes que vamos a utilizar para comprobar la calidad de nuestro código.

El primer informe que necesitamos crear es el informe de JUnit.
Este informe generará un archivo .xml como salida que CircleCI utilizará para mostrar los resultados de la verificación de código:

![Full-width image](/assets/img/blog/tutorials/alexa-devops/eslintcircleci.png){:.lead data-width="800" data-height="100"}
ESLint Report en CircleCI
  {:.figure}

Vamos a dar un paso adelante. Queremos saber un poco más sobre nuestro análisis de ESLint en cada ejecución de nuestro workflow.

Es por eso que vamos a agregar el paquete npm `eslint-detail-reporter` para generar un bonito informe HTML con más información, en lugar del explicado anteriormente:

```bash
    npm install eslint-detailed-reporter --save-dev
```

Así es como se ve este informe:

![Full-width image](/assets/img/blog/tutorials/alexa-devops/eslinthtml.png){:.lead data-width="800" data-height="100"}
ESLint HTML Report
  {:.figure}

Todos estos informes se almacenarán en la carpeta `lambda / custom / reports / eslint /`.

### Integración

¡Ahora es el momento de integrarlo en nuestro `package.json` para usarlo en nuestro pipeline con los comandos `npm run`!

Entonces, en este archivo vamos a agregar los siguientes comandos en el nodo json `script`:

1. `lint`:este comando ejecutará la comprobación de ESLint y generará el informe JUnit:
   1. `eslint . --format junit --output-file reports/eslint/eslint.xml`
2. `lint-fix`: esto solucionará automáticamente la mayoría de los errores de estilo de código
   1. `eslint --fix .`
3. `lint-html`: este comando ejecutará el informe HTML usando el paquete npm explicado anteriormente:
   1. `eslint . -f node_modules/eslint-detailed-reporter/lib/detailed.js -o reports/eslint/report.html`

## Pipeline Job

Todo está completamente instalado, configurado e integrado, ¡agregémoslo a nuestro pipeline!

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Ejecutar `npm run lint` para ejecutar el ESLint chekcer.
3. Ejecutar `npm run lint-html` para ejecutar el informe HTML de ESLint. Se ejecutará siempre tanto en caso de éxito o error del job.
4. Almacenar el informe JUnit como artefactos de CircleCi.
5. Almacenar el informe HTML como un artefacto de este job.
6. Conservar nuevamente el código que reutilizaremos en el próximo job

```yaml
  pretest:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: cd lambda/custom && npm run lint
      - run: 
          command: cd lambda/custom && npm run lint-html
          when: always
      - store_test_results:
          path: lambda/custom/reports/eslint/
      - store_artifacts:
          path: ./lambda/custom/reports/eslint/
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project
```

## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia reference
* [Documentación oficial de ESLint](https://eslint.org/) - Documentación oficial de ESLint
* [Documentación oficial de CircleCI](https://circleci.com/docs/) - Documentación oficial de CircleCI

## Conclusión 

La calidad de las herramientas de análisis estático depende de varios factores.
Los principales suelen ser la eficiencia, la claridad de tus informes de errores y un bajo porcentaje de falsos negativos.
Una ventaja de las herramientas de análisis estático es que suelen ser fáciles de usar. muchos están integrados directamente en el IDE y solo requieren la ejecución de un solo comando como hemos visto con ESLint.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld/blob/master/CICD.md)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
