---
layout: post
title:  Alexa Skill, AWS CloudFormation y Serverless Application Model (SAM)
image: /assets/img/blog/post-headers/alexa-lambda-cloudformation-sam.jpg
description: >
  Alexa Skill desarrollada en Java usando AWS CloudFormation y Serverless Application Model (SAM)
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - aws
  - cloudformation
  - sam
  - serverless
  - serverless application model
  - java
  - howto
  - skill
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

Este proyecto contiene código fuente y archivos extra para crear una Alexa Skill basado en una aplicación serverless que se puede desplegar con la  Serverless Application Model (SAM) CLI.

# Alexa Skill, AWS CloudFormation y Serverless Application Model (SAM)

 Incluye los siguientes archivos y carpetas:

- HelloWorldFunction/src/main - Código de la Skill desarrollada como una función Lambda de AWS en lenguaje Java.
- events - Eventos de invocación que puedes usar para invocar la Skill.
- template.yaml - Una plantilla que define los resources de la aplicación serverless (incluyendo la función lambda que será el backend de nuestra Alexa Skill) necesarios para desplegarse en AWS.

La aplicación serverles utiliza varios resources de AWS, entre los que se encuentran la función Lambda (Skill), IAM roles y ARN. Estos resources se definen en el fichero `template.yaml` de este proyecto. Puedes actualizar el tempalte para agregar resources de [AWS]((https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md)).

## Requisitos previos

La **Serverless Application Model Command Line Interface (SAM CLI)** es una extensión de la AWS CLI que agrega funcionalidad para crear y probar aplicaciones serverless. 
Usa **Docker** para ejecutar las aplicaciones en un entorno de Amazon Linux que pueda usar AWS. También puedes emular el entorno de compilación de tu aplicación.

Para usar la SAM CLI, necesitas las siguientes herramientas.

* SAM CLI - [Instalar la SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* Java8 - [Instalar Java SE Development Kit 8](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html)
* Maven - [Instalar Maven](https://maven.apache.org/install.html)
* Docker - [Instalar Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

## Usa la SAM CLI para construir tu Skill localmente

Construye tu aplicación con el comando `sam build`.

Para construir y desplegar tu aplicación por primera vez, ejecuta lo siguiente en tu shell:

```bash
sam build HelloWorldFunction --template template.yaml --build-dir HelloWorldFunction\.aws-sam\build
```

La SAM CLI instala las dependencias definidas en `HelloWorldFunction/pom.xml`, crea un deployment package, y lo guarda en el directorio `.aws-sam/build`.


## Ejecutar tu Skill localmente

Puedes probar una sola función lambda (nuestra Skill) invocándola directamente con un evento de prueba. Un evento es un fichero JSON que representa la entrada que la función lambda recibe. Los eventos de prueba están incluidos en el directorio  `events`  de este proyecto. En este proyecto puedes encontrar un ejemplo de `LaunchRequest`

Ejecuta la función lambda (Skill) localmente ejecutando el comando `sam local invoke`.

```bash
sam local invoke HelloWorldFunction --template HelloWorldFunction\.aws-sam\build\template.yaml
```
**NOTA:** Usando LocalDebugger.java es tan sencillo como **ejecutar** desde Visual Studio Code o IntelliJ. Échale un ojo a las cofiguraciones para los dos IDEs en:
For this type of running it is not necessary to run any SAM CLI Command.
1. `.vscode\launch.json`
2. `.idea\runConfigurations\LocalDebugger.xml`

## Debuggea tu Skill localmente

Los eventos de prueba están incluidos en el directorio  `events`  de este proyecto.

Para poder debuggear tu aplicación localmente ejecuta el siguiente comando:

```bash
sam local invoke HelloWorldFunction --template HelloWorldFunction\.aws-sam\build\template.yaml --event events/event.json --debug-port 56531
```

Con AWS Toolkit instalado en el IDE, es fácil configurar y depurar con puntos de ruptura tus Skills dependiendo del `event.json` utilizados como prueba

**NOTA:** Usando LocalDebugger.java es tan sencillo como **debuggear** desde Visual Studio Code o IntelliJ. Échale un ojo a las cofiguraciones para los dos IDEs en:
For this type of running it is not necessary to run any SAM CLI Command.
1. `.vscode\launch.json`
2. `.idea\runConfigurations\LocalDebugger.xml`


## Prueba tu Skill localmente

Los eventos de prueba están incluidos en el directorio  `events`  de este proyecto.

```bash
sam local invoke HelloWorldFunction --template HelloWorldFunction\.aws-sam\build\template.yaml --event  events/event.json
```

**NOTA:** Usando LocalDebugger.java puedes hacer la request de abajo directamente a http://localhost:3001/:

En el fichero event.json tienes un ejemplo de un `LaunchRequest` mockeado de una Skill:

```json
{
  "version": "1.0",
  "session": {
    "new": true,
    "sessionId": "amzn1.echo-api.session.[unique-value-here]",
    "application": {
      "applicationId": "amzn1.ask.skill.[unique-value-here]"
    },
    "user": {
      "userId": "amzn1.ask.account.[unique-value-here]"
    },
    "attributes": {}
  },
  "context": {
    "AudioPlayer": {
      "playerActivity": "IDLE"
    },
    "System": {
      "application": {
        "applicationId": "amzn1.ask.skill.[unique-value-here]"
      },
      "user": {
        "userId": "amzn1.ask.account.[unique-value-here]"
      },
      "device": {
        "supportedInterfaces": {
          "AudioPlayer": {}
        }
      }
    }
  },
  "request": {
    "type": "LaunchRequest",
    "requestId": "amzn1.echo-api.request.[unique-value-here]",
    "timestamp": "2016-10-27T18:21:44Z",
    "locale": "en-US"
  }
}


```
## Testear requests directamente desde Alexa

ngrok es una herramienta genial y liviana que crea un túnel seguro en tu máquina local junto con una URL pública que se puede usar para navegar por tu web en local o API.

Cuando se está ejecutando ngrok, escucha en el mismo puerto en el que se está ejecutando el servidor web local y envía solicitudes externas a tu máquina local.

Veamos como de fácil es publicar nuestra Skill ejecutandose en local para que el cloud de Alexa nos envíe requests. 
Digamos que está ejecutando tu servidor web local en el puerto 3001. En la terminal, escribiría: `ngrok http 3001`. Esto comienza a escuchar a ngrok en el puerto 3001 y crea el túnel seguro:

  ![Full-width image](/assets/img/blog/tutorials/alexa-nodejs/tunnel.png){:.lead data-width="800" data-height="100"}
Túnel
  {:.figure}


Entonces ahora vas a la [Alexa Developer console](https://developer.amazon.com/alexa/console/ask), navegar a tu Skill > endpoints > https, agregas la URL https generada anteriormente . Por ejemplo: https://20dac120.ngrok.io.

Selecciona la opción "My development endpoint is a sub-domain...." desde el menú desplegable y haga clikc en Save endpoint en la parte superior de la página.

Dirígete al tab Test en la Alexa Developer Console y lanza tu skill.

La Alexa Developer Console enviará una solicitud HTTPS al endpoint ngrok (https://20dac120.ngrok.io) que lo redirigirá a tu Skill ejecutándose en el servidor Web en http://localhost:3001.


## Despliega tu Skill en AWS

Para desplegar tu función Lambda (nuestra Skill) por primera vez ejecuta el siguiente comando:

```bash
sam deploy --guided
```

El comando va a empaquetar y desplegar la aplicación serverles a AWS con una serie de prompts:

* **Stack Name**: El nombre del stack a desplegar a CloudFormation. Debe ser único para tu cuenta y región. Cómo buena práctica se recomienda darle un nombre relacionado con el proyecto actual.
* **AWS Region**: La región de AWS donde quieres desplegar la aplicación serverless.
* **Confirm changes before deploy**: Si decides que sí, cualquier conjunto de cambios se te mostrará antes de la ejecución para una revisión manual. Si decides que no, la  AWS SAM CLI ejecutará automáticamente los cambios de la aplicación sin previa revisión.
* **Allow SAM CLI IAM role creation**: Muchos templeates de AWS SAM crean AWS IAM roles necesarios para las funciones de AWS Lambda  para acceder a los servicios de AWS. Por defecto, estos se reducen al mínimo requerido. Para desplegar un stack en AWS CloudFormation que crea o modifica IAM roles, el valor `CAPABILITY_IAM` de la sección `capabilities` debe estar informado. Si no se da el permiso a través de este prompt, para desplegar este ejemplo debes especificar explícitamente `--capabilities CAPABILITY_IAM` en el comando `sam deploy`.
* **Save arguments to samconfig.toml**: Si decides que sí, tus opciones se guardarán en un archivo de configuración dentro del proyecto, para que en el futuro pueda volver a ejecutar `sam deploy` sin parámetros.

## Añade un resource a tu aplicación serverless
El template de la aplicación usa el AWS Serverless Application Model (AWS SAM) para definir todos los resources. AWS SAM es una extensión del AWS CloudFormation con una sintaxis más simple para configurar los resources de aplicaciones serverless como funciones, triggers y APIs. Para resources no definidos en la [SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md), puedes usar el estándard [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html).

## Intégralo en tu editor favorito

Si prefieres usar un IDE para compilar y probar tu aplicación serverless, puedes usar el AWS Toolkit.  
AWS Toolkit es un plug-in de código abierto para los IDE más populares y utiliza la SAM CLI para construir, testear, debuggear y desplegar aplicaciones serverless en AWS. AWS Toolkit también añade la posibilidad de debuggear paso a paso el código de la función Lambda (Skill). Aquí te dejo un listado para instalarlo en dieferentes IDEs.

* [PyCharm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [IntelliJ](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [VS Code](https://docs.aws.amazon.com/toolkit-for-vscode/latest/userguide/welcome.html)
* [Visual Studio](https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/welcome.html)

## Recursos

Echa un ojo a la [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) para tener una breve idea sobre la SAM specification, la SAM CLI, y los conceptos de la aplicaciones serverless.

Después, puedes usar el AWS Serverless Application Repository para desplegar aplicaciones serverless listas para usar y aprender cómo los desarrolladores crean sus propias aplicaciones: [AWS Serverless Application Repository](https://aws.amazon.com/serverless/serverlessrepo/)


## Conclusión

Este proyecto es de gran relevancia ya que nos permite desarrollar localmente nuestra Skill en Java pero además, nos permites compilarla, testearla, debuggearla y desplegarla de una manera muy sencilla. A su vez, gracias a la ASM CLI, se nos abstrae de los requisitos hardware necesarios para ejecutar la función lambda, gracias a Docker, y nos ayuda a poder diseñar en un futuro un sistema de CI/CD dónde podremos hacer un ciclo completo DevOps de nuestra Skill de Alexa.

Podéis encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-java-lambda-helloworld)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

!Happy coding!
