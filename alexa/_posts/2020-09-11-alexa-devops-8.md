---
layout: post
title: DevOps en tu Alexa Skill. End-to-end Tests.
image: /assets/img/blog/post-headers/alexa-bespoken.jpg
description: >
   Bespoken como herramienta clave end-to-end
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
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

Este tipo de prueba nos permite verificar si la interacción de los componentes del software en nuestra Alexa Skill, como, VUI, código lambda o la base de datos, funciona como se esperaba.
En resumen, las pruebas end-to-end evalúan la capacidad de la aplicación para satisfacer todas las solicitudes que el usuario final puede realizar.

# DevOps en tu Alexa Skill: End-to-end Tests

En términos de voz no es fácil lograr este tipo de pruebas debido a la interacción de la voz como entrada de la prueba end-to-end.
Usaremos Bespoken para escribir nuestras pruebas end-to-end. ¡Bespoken nos permite realizar este tipo de pruebas de forma muy sencilla!

Estos tests están automatizadas en el sistema de integración continua (CircleCI) y se ejecutan en cada nueva versión del software.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. CircleCI Account -  [Regístrate aquí gratis](https://circleci.com/)
5. Bespoken Account - [Registrate aquí](https://bespoken.io/)
6. Visual Studio Code

## Bespoken

Bespoken es la mejor herramienta para probar nuestra Skill de Alexa. Desde pruebas unitarias hasta pruebas end-to-end. 

Si echamos un vistazo a su documentación oficial:
* Bespoken facilita la realización de pruebas end-to-end para aplicaciones de voz.
* Usan dispositivos virtuales para hacerlo. Un dispositivo virtual funciona como un dispositivo físico, como un Amazon Echo, pero se puede interactuar con él a través de la sintaxis de scripting para crear pruebas de Bespoken (así como de forma programática a través de Bespoken API).
* Como dice Bespoken, por debajo ocurren varias cosas que son invisbles para nostros. Las pruebas en sí son muy fáciles de escribir y mantener; de hecho, creen que es tan fácil escribir las pruebas como decirlas. Una vez que se han escrito, tenemos un conjunto de pruebas automatizado, que podemos ejecutar en cualquier momento e incorporar a otros procesos automatizados (como continuous integration/continuous delivery).

Hemos escrito, probado y ejecutado pruebas usando Bespoken y podemos concluir que es la mejor herramienta de prueba para aplicaciones de voz que se puede usar.

### Instalación

Las Bespoken Tools se incluye en la [Docker image](https://hub.docker.com/repository/docker/xavidop/alexa-ask-aws-cli) que estamos usando, por lo que no es necesario instalar nada más.

### Configuración

La configuración en Bespoken es realmente sencilla. Solo necesitamos tener una cuenta y crear un dispositivo virtual en su web:

![Full-width image](/assets/img/blog/tutorials/alexa-devops/virtualdevice.png){:.lead data-width="800" data-height="100"}
Virtual device
  {:.figure}


Como nuestra imagen  Docker tiene instalado el paquete npm `bespoken-tools`, mencionado en la sección anterior, podemos ejecutar el comando que configurará nuestro conjunto de pruebas:

~~~bash
  bst init
~~~

Este comando mostrará el siguiente prompt:

![Full-width image](/assets/img/blog/tutorials/alexa-devops/bstinit.png){:.lead data-width="800" data-height="100"}
bst init
  {:.figure}

Donde tendremos que introducir la siguiente información:
1. El tipo de pruebas que estamos creando. En nuestro caso, end-to-end.
2. El nombre de nuestra aplicación de voz. En nuestro caso, hola mundo.
3. Las configuraciones regionales disponibles. En nuestro caso es-ES.
4. La plataforma que estamos usando, en nuestro caso Alexa.
5. Y finalmente, el token del dispositivo virtual que hemos creado anteriormente.

Después de ejecutar ese comando, Bespoken creará un archivo json `testing.json` y una carpeta `e2e` con un ejemplo de una prueba end-to-end.

Primero, echaremos un vistazo a nuestro archivo `testing.json`:

~~~json
  {
      "virtualDeviceToken": "alexa-8ffa4668-0fe2-45dd-8687-4f0b159a4e44",
      "locales": "es-ES",
      "type": "e2e",
      "platform": "alexa"
  }
~~~

Realmente fácil, ¿verdad? En ese archivo podemos ver la información que hemos introducido en el comando `bst init`.

Para tener el repositorio bien estructurado, todos los archivos de Bespoken se encuentran en la carpeta `test/e2e-bespoken-test`.

Ahora estamos listos para escribir nuestro conjunto de pruebas end-to-end.

### Escribiendo tests end-to-end

En este paso del pipeline vamos a desarrollar algunas pruebas end-to-end escritas con Bespoken.

Una vez que hemos probado nuestra interfaz de usuario de voz, nuestro backend y comprobados que todo esté correcto.
Es hora de probar todos los componentes de software interelacionados en una solicitud de una Skill de Alexa. **Pero ahora, usando la voz como input.**

En la carpeta `test/e2e-bespoken-test/e2e` podemos encontrar el archivo del conjunto de pruebas `index.e2e.yml`. 

Este es el archivo de pruebas end-to-end:

~~~yaml

  ---
  configuration:
    locale: es-ES
    description: Test e2e con Bespoken
  ---
  - test : Hola mundo test
  - abre hola mundo: "bienvenido puedes decir hola o ayuda"
  - hola: 

  ---
  - test : Ayuda test con stop intent
  - abre hola mundo: "bienvenido puedes decir hola o ayuda"
  - ayuda: "puedes decirme hola * ayudar"
  - para: "hasta *"

  ---
  - test : Ayuda test con cancel intent
  - abre hola mundo: "bienvenido puedes decir hola o ayuda"
  - ayuda: "puedes decirme hola * ayudar"
  - cancela: "hasta *"

~~~
Como podemos ver, tenemos 3 pruebas en esta suite:
1. La primera probará una solicitud LaunchRequest y el intent HelloWorld.
2. La segunda probará una solicitud LaunchRequest, AMAZON.HelpIntent y finalizará la sesión utilizando AMAZON.StopIntent.
3. La tercera probará una solicitud LaunchRequest, AMAZON.HelpIntent y finalizará la sesión utilizando AMAZON.CancelIntent.

Estas pruebas end-to-end se pueden realizar con el paquete npm `bespoken-tools`. 

usaremos el siguiente comando `bst` para ejecutarlas:

~~~bash
  bst test --config test/e2e-bespoken-test/testing.json
~~~

Cuando ejecutamos esta suite, esto es lo que sucede en Bespoken:

* Bespoken convierte la entrada de texto de la prueba en audio mediante la conversión de texto a voz (text-to-speech) de Amazon Polly.
* Envía el audio del habla a Alexa.
* Alexa invoca la Skill.
* La Sklill proporciona una respuesta: una combinación de audio (la respuesta vocal de Alexa) y metadatos (para la información de las tarjetas).
* Convertimos la respuesta de nuevo en texto usando speech-to-text.
* Lo comparamos con el output esperado.

### Informes

Una vez hemos ejecutado la suite explicada anteriormente, el paquete npm `bespoken-tools` creará un informe HTML ubicado en `test_output/`.

En este informe podemos comprobar cómo fue la ejecución.

Así es como se ve este informe:

![Full-width image](/assets/img/blog/tutorials/alexa-devops/bespokenhtml.png){:.lead data-width="800" data-height="100"}
Bespoken HTML report
  {:.figure}

Este informe se almacenará como un artefacto de este job en CircleCI.

### Integración

No es necesario integrarlo en el archivo `package.json`.

## Pipeline Jobs

Todo está listo para ejecutar y probar nuestro tests de integración, ¡agregémoslo a nuestro pipeline!

Este job ejecutará las siguientes tareas:
1. Restaurar el código que hemos descargado en el paso anterior en la carpeta `/home/node/project`
2. Ejecutar las pruebas end-to-end utilizando el comando `bst test`.
3. Almacenar el informe HTML generado por la ejecución anterior como un artefacto de este job.
4. Conservar nuevamente el código que reutilizaremos en el próximo job
   
~~~yaml

  end-to-end-test:
    executor: ask-executor
    steps:
      - attach_workspace:
          at: /home/node/
      - run: bst test --config test/e2e-bespoken-test/testing.json
      - store_artifacts:
          path: test_output/
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project

~~~

## Recursos

* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Wikipedia reference
* [Documentación oficial de Bespoken](https://read.bespoken.io/end-to-end/getting-started/) - Documentación oficial de Bespoken
* [Documentación oficial de CircleCI](https://circleci.com/docs/) - Documentación oficial de CircleCI

## Conclusión 

La razón principal para realizar esta prueba es determinar dependencias dentro de una aplicación, así como garantizar que se comunique información entre varios componentes del sistema de manera correcta.
Gracias a Bespoken podemos realizar estas complejas pruebas.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-lambda-helloworld/blob/master/CICD.md)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
