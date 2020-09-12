---
layout: post
title: Imagen Docker para usar la ASK CLI y la AWS CLI 
image: /assets/img/blog/post-headers/alexa-docker.jpg
description: >
   Imagen útil para utilizar la ASK CLI y la AWS CLI en pipelines DevOps
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

El propósito de este contenedor es poder utilizar la [Amazon ASK CLI](https://developer.amazon.com/docs/smapi/ask-cli-intro.html#alexa-skills-kit-command-line-interface-ask-cli) y la [Amazon AWS CLI](https://docs.aws.amazon.com/cli/index.html) en un contenedor Docker en pieplines de DevOps.

# Docker image para la ASK CLI y la AWS CLI 

**NOTE:** Esto es un fork de la imagen de [martindsouza](https://github.com/martindsouza/docker-amazon-ask-cli) con estos cambios:
1. LA imagen base es la última versión LTS en lugar de la versión actual de Node.js.
2. Se ha añadido el argumento ASK_CLI_VERSION para poder trabajar con diferentes versiones de ASK CLI.
3. Se agregaron los paquetes git y zip que ASK CLI usará en sus comandos.
4. Añadido Bespoken.
5. Volúmenes eliminados. Creo que no es necesario en una simple imagen que usaré en mis pipelines DevOps. Además, se puede usar el argumento '-v' en el comando `docker run` cuando se desee.

## ASK Config

Tienes que tener en cuenta que debes tener una [Alexa Developer Account](https://developer.amazon.com/alexa) para poder trabajar con este contenedor.

### ask configure

Puedes ejecutar `ask configure` en ASK v2 y `ask init` en ASK v1 en el contenedor y se lanzarán  un conjunto de preguntas para crear las credenciales de Alexa.
Sigue todos los pasos explicados en [la documentación oficial](https://developer.amazon.com/en-US/docs/alexa/smapi/manage-credentials-with-ask-cli.html).

En cualquier caso, segúrate de pasar `-v $ (pwd) /ask-config:/home/node/.ask \` (donde `$(pwd)/ ask-config` es una ubicación en tu máquina host) como una opción al ejecutar el contenedor para preservar la configuración ASK.

### Estableciendo credenciales usando variables de entorno

Puedes almacenar las credenciales de Alexa en variables de entorno en lugar del archivo de cofiguración de Alexa. 
Si existen las variables de entorno de Alexa, ASK CLI las usa en lugar de los valores en el archivo de configuración de Alexa. 
ASK CLI busca las siguientes variables de entorno de Alexa:

Puede usar las variables de entorno del ASK CLI junto con el archivo de configuración ASK CLI. La siguiente lista describe las variables de entorno ASK CLI.

* `ASK_DEFAULT_PROFILE`: Utiliza esta variable de entorno junto con el archivo de configuración ASK CLI. Cuando estableces el valor de esta variable de entorno en uno de los perfiles en el archivo de configuración, ASK CLI usa las credenciales de ese perfil.
* `ASK_ACCESS_TOKEN`: Usa esta variable de entorno para almacenar un token de acceso de desarrollador de Amazon. Cuando existe esta variable de entorno, ASK CLI la usa en lugar de las credenciales en el archivo de configuración.
* `ASK_REFRESH_TOKEN`: Usa esta variable de entorno para almacenar un token de actualización de desarrollador de Amazon. Cuando existe esta variable de entorno, ASK CLI la usa en lugar de las credenciales en el archivo de configuración. Cuando esta variable de entorno y ASK_ACCESS_TOKEN existen, ASK CLI usa esta.
* `ASK_VENDOR_ID`: Use esta variable de entorno para almacenar el Amazon vendor ID. Cuando existe esta variable de entorno, ASK CLI la usa en lugar de la que está en el archivo de configuración.
* `ASK_CLI_PROXY`: Utilice esta variable de entorno para especificar un proxy HTTP para las requests realizadas con ASK CLI.
  
Si deseas saber cómo obtener `ASK REFRESH_TOKEN` y `ASK ACCESS_TOKEN`, consulta [esta página](https://developer.amazon.com/en-US/docs/alexa/smapi/get-access-token-smapi.html) en la documentación de Alexa.

Si deseas saber cómo obtener el `ASK_VENDOR_ID`, solo tienes que acceder a [esta página](https://developer.amazon.com/settings/console/mycid).

Si estás utilizando las variables de entorno de Alexa, debes agregar un nuevo perfil llamado `__ENVIRONMENT_ASK_PROFILE__` en su archivo `.ask/config`

## AWS Config

Si planeas usar [AWS Lambda](https://aws.amazon.com/lambda/) deberás configurar la AWS CLI. PAra simplificar, puedes configurarlo de varias maneras.

Asegurate que tienes las credenciales en `-v $(pwd)/aws-config:/home/node/.aws \` (donde `$(pwd)/aws-config` es la carpeta de tu máquina local) como opción para perseverar las mismas credenciales entre diferentes ejecuciones.

### aws configure

Para uso general, el comando `aws configure` es la forma más rápida de configurar la instalación de la AWS CLI.
Cuando ejecutas este comando, la AWS CLI te solicita cuatro datos (access key, secret access key, AWS Region, y el output format)

### Estableciendo credenciales usando variables de entorno

Puedes almacenar credenciales de AWS en variables de entorno en lugar del archivo de credenciales de AWS. Si existen las variables de entorno de AWS, ASK CLI las usa en lugar de los valores en el archivo de credenciales de AWS. ASK CLI busca las siguientes variables de entorno de AWS:

* `AWS_ACCESS_KEY_ID`
* `AWS_SECRET_ACCESS_KEY`
  
Para obtener más información sobre las [variables de entorno de AWS](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html), consulta las variables de entorno en la documentación de AWS.

## Uso

Obtener la última versión del contenedor:

```bash
  # Get image
  docker pull xavidop/alexa-ask-aws-cli:2.0
```

Hay dos formas de usar el cli `ask` para este contenedor que se describe a continuación.

### Ejecutar los comandos ASK CLI

Este es un ejemplo que muestra cómo ejecutar un comando `ask`. Después de ejecutar este comando, el contenedor se detendrá.

```bash
docker run -it --rm \
  -v $(pwd)/ask-config:/home/node/.ask \
  -v $(pwd)/ask-config:/home/node/.aws \
  -v $(pwd)/ask-config:/home/node/.bst \
  -v $(pwd)/hello-world:/home/node/app \
  xavidop/alexa-ask-aws-cli:latest \
  ask init -l
```

### Ejecutar los comandos ASK CLI de forma interactiva

En este ejemplo, el contenedor comenzará directamente con la consola bash y luego podrás ejecutar allí todos los comandos ASK CLI que quieras.

```bash
docker run -it --rm \
  -v $(pwd)/ask-config:/home/node/.ask \
  -v $(pwd)/ask-config:/home/node/.aws \
  -v $(pwd)/ask-config:/home/node/.bst \
  -v $(pwd)/app/HelloWorld:/home/node/app \
  xavidop/alexa-ask-aws-cli:latest \
  bash

```

## Build y push de la imagen

PAra la ASK CLI v1:
```bash
docker build --build-arg ASK_CLI_VERSION=1.7.23 -t xavidop/alexa-ask-aws-cli:1.0 .

# Pushing to Docker Hub
# Note: not required since I have a build hook linked to the repo
docker login
docker push xavidop/alexa-ask-aws-cli
```

PAra la ASK CLI v2:
```bash
docker build --build-arg ASK_CLI_VERSION=2.1.1 -t xavidop/alexa-ask-aws-cli:2.0 .

# Pushing to Docker Hub
# Note: not required since I have a build hook linked to the repo
docker login
docker push xavidop/alexa-ask-aws-cli:2.0
```

## Versiones

Para comprobar las versiones os recomiendo que accedais a mi [perfil de DockerHub](https://hub.docker.com/r/xavidop/alexa-ask-aws-cli/tags)

## Links:

- [ASK CLI Quickstart](https://developer.amazon.com/docs/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
- [ASK CLI Full Doc](https://developer.amazon.com/docs/smapi/ask-cli-intro.html#alexa-skills-kit-command-line-interface-ask-cli)


Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-ask-aws-cli-docker)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    