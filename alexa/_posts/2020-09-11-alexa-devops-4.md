---
layout: post
title: DevOps en tu Alexa Skill. Code Coverage.
image: /assets/img/blog/post-headers/alexa-code-coverage.jpg
description: >
   Code Coverage de nuestras pruebas unitarias usando Codecov  
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


# DevOps en tu Alexa Skill: Code Coverage

Durante el desarrollo del código (módulos, librerías) es importante integrar herramientas objetivas que midan el estado del código y brinden la información para conocer su calidad y así poder detectar y prevenir problemas: funciones duplicadas, métodos excesivamente complejos, estilo de codificación no estándar o de baja calidad.

Estas comprobaciones están automatizadas en el sistema de integración continua (CircleCI) y se ejecutan en cada nueva versión del software.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. CircleCI Account -  [Regístrate aquí gratis](https://circleci.com/)
5. Codecov Account -  [Regístrate aquí gratis](https://codecov.io/)
6. Visual Studio Code

## Codecov

Codecov proporciona herramientas altamente integradas para agrupar, fusionar, archivar y comparar informes de code coverage.
Ya sea que el equipo de desarrollo esté comparando cambios en una pull request o revisando un único commit, Codecov mejorará el flujo de trabajo y la calidad de la revisión del código.
Codecov admite las plataformas de CICD más comunes, como la que usamos nosotros, CircleCI.

### Configurar Codecov

Como dice la documentación oficial de Codecov, estas son las pasos que necesitaremos hacer antes de usar Codecov:

1. Regístrarnos en [codecov.io](https://codecov.io/) y vincular nuestra cuenta de GitHub, GitLab o Bitbucket.
2. Una vez vinculado, Codecov sincronizará automáticamente todos los repositorios a los que tenga acceso.
Podemos hacer clic en una organización desde el panel para acceder a los repositorios, o navegar directamente a un repositorio específico usando: https://codecov.io/\<repo-provider>/\<account-name>/\<repo-name>. Ejemplo: https://codecov.io/gh/xavidop/alexa-nodej-lambda-helloworld.
3. Obtener el token de este repositorio generado por Codecov que usaremos en nuestro pipeline.

Ahora podemos volver a nuestro código para configurar el proyecto.

### Instalatción

Después de esto, podemos instalar la librería de Node.js `codecov` usando npm. `--save-dev` se usa para guardar el paquete npm con fines de desarrollo. Ejemplo: pruebas unitarias, minificación.

~~~bash
    npm install codecov --save-dev
~~~

Es importante notar que el code coverage será generado por una herramienta externa llamada `nyc` que su output será utilizado por esta librería para cargarlo en Codecov. 

¡Sigamos!

### Configuración

Una vez que tengamos la librería de Node.js `codecov` ahora tenemos que configurarla.

Para usar la librería, necesitamos establecer una variable de entorno llamada `CODECOV_TOKEN` con el valor que Codecov ha generado en el paso anterior.

Después de eso tenemos que crear el archivo de configuración `codecov.yml` en la raíz de nuestro repositorio con este contenido:

~~~yaml
    fixes:
      - "src/::lambda/custom/src/"
~~~

¿Por qué? Bueno, nuestro código JavaScript no se encuentra en la raíz de nuestro proyecto, por lo que cuando ejecutamos el informe de code coverage, comenzará desde la subcarpeta `src/`.
Entonces, tenemos que cambiar la carpeta del informe para establecer la ruta correcta comenzando desde el directorio raíz del repositorio.
Con este archivo yaml, Codecov cambiará todas las rutas de los archivos de `src/` a `lambda/custom/src`.
Este cambio es necesario si queremos navegar entre archivos en la interfaz web de Codecov.
Este no es un problema solo con Codecov, tuve el mismo problema con la herramienta Coveralls, por ejemplo.

### Informe de Code Coverage 

Una vez que tenemos todo configurado, tenemos que configurar el informe que vamos a utilizar para comprobar la Cobertura del Código.

Usaremos el paquete npm `nyc`, que es la herramienta CLI del famoso paquete npm `Istanbul`.
Tanto `nyc` como `Istanbul` son las bibliotecas de cobertura de código más utilizadas para proyectos de Node.js y JavaScript.
 
Puede instalar `nyc` usando npm. `--save-dev` se usa para guardar el paquete npm con fines de desarrollo. Ejemplo: pruebas unitarias, minificación.

~~~bash
    npm install nyc --save-dev
~~~

Este paquete npm tiene una opción para establecer el output del informe al tipo `.lcov`, que es el tipo que la librería de Node.js `codecov` necesita para poder cargarlo en la plataforma.

Después de que el informe se haya subido a Codecov, así es como se ve:

![Full-width image](/assets/img/blog/tutorials/alexa-devops/codecov.jpg){:.lead data-width="800" data-height="100"}
Codecov
  {:.figure}


### Integración

¡Ahora es el momento de integrarlo en nuestro `package.json` para usarlo en nuestro pipeline con los comandos `npm run`!

Entonces, en este archivo vamos a agregar los siguientes comandos en el nodo json `script`:

1. `codecov`: este comando ejecutará el informe de cobertura de código y lo cargará en Codecov:
   * `nyc npm test && nyc report --reporter=text-lcov > coverage.lcov && codecov`


## Pipeline Job

Todo está completamente instalado, configurado e integrado, ¡agregémoslo a nuestro pipeline!

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Ejecutar `npm run codecov` para ejecutar Code Coverage y luego cargarlo en Codecov.
3. Conservar nuevamente el código que reutilizaremos en el próximo job

~~~yaml
  codecov:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: cd lambda/custom && npm run codecov
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project
~~~
**NOTA:** Recuerda establecer la variable de entorno `CODECOV_TOKEN` en CircleCI.

## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia reference
* [Documentación oficial de Codecov](https://docs.codecov.io/docs) - Documentación oficial de Codecov
* [Documentación oficial de CircleCI](https://circleci.com/docs/) - Documentación oficial de CircleCI

## Conclusión 

Un mínimo de calidad y centrar nuestros esfuerzos en las pruebas es la parte más complicada e importante de nuestro negocio.
Herramientas como Codecov nos ayudan a conseguir estos objetivos y son fundamentales en entornos de mejora continua.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld/blob/master/CICD.md)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
