---
layout: post
title: Alexa y Kubernetes. Dockerizando una Alexa Skill (II)
image: /assets/img/blog/post-headers/alexa-docker-webserver.jpg
description: >
   Creando la imagen Docker de nuestra Alexa Skill usando Express
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
  - kubernetes
  - terraform
  - express
  - mongo
  - howto
  - skill
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

La segunda tarea que tenemos que hacer para ejecutar nuestra Alexa Skill en un entorno de Kubernetes es dockerizar nuestro backend de la Alexa Skill, que ahora es una aplicación NodeJs Express.

Como Kubernetes es un orquestador de contenedores, este es un paso obligatorio en nuestro proceso para ejecutar la Skills de Alexa en un entorno de Kubernetes.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Node.js v12.x
2. Visual Studio Code
3. Docker 19.x

## Dockerfile

Docker puede crear imágenes automáticamente leyendo las instrucciones de un Dockerfile. Un Dockerfile es un documento de texto que contiene todos los comandos que un usuario puede ejecutar en una la línea de comandos para crear una imagen Docker. Al utilizar la compilación de Docker, los usuarios pueden crear una compilación automatizada que ejecute varias instrucciones que se ejecutan en la línea de comandos en sucesión.

~~~dockerfile
FROM node:12.18-alpine
WORKDIR /usr/src
COPY ./app/ .
RUN npm install
EXPOSE 3000
ENTRYPOINT ["npm", "start"]
~~~

Estos son los pasos que ejecutará el `Dockerfile` cuando hagamos el build de la imagen Docker:
1. Usaremos la versión NodeJS 12.18 que se ejecuta en un contenedor Linux Alpine.
2. Estableceremos el directorio de trabajo del contenedor en `/usr/src`.
3. Luego copiaremos nuestra Skill de Alexa como un servidor web NodeJS Express.
4. Ejecutaremos el comando `npm install` para descargar e instalar todas las dependencias necesarias.
5. Nuestro Express Web Server se está ejecutando en el puerto 3000, por lo que también debemos "exponerlo" en nuestro contenedor.
6. Finalmente, iniciaremos el servidor Web Express ejecutando el comando `npm start`.

El `Dockerfile` se encuentra en la carpeta `docker`.

## Crear la imagen de Docker

Explicado todos los pasos de nuestro `Dockerfile`, es hora de hacer el build para tener nuestro contenedor listo para ejecutarse.

Este es un ejemplo de un comando `build` de Docker:
~~~bash
## Build
docker build -t xavidop/alexa-skill-nodejs-express:latest -f docker/Dockerfile .
~~~

**NOTA:** este comando debe ejecutarse en la carpeta raíz de este proyecto.

## Push de la imagen Docker

Este es un ejemplo de un comando Docker Push:
~~~bash
## Push
docker push xavidop/alexa-skill-nodejs-express:latest
~~~

**NOTA:** este comando debe ejecutarse en la carpeta raíz de este proyecto.

Después de ejecutar el comando push con la imagen, podemos echar un vistazo a nuestro Registro  Docker para inspeccionar toda la información. Podéis encontrar un ejemplo [aquí](https://hub.docker.com/repository/docker/xavidop/alexa-skill-nodejs-express/general). En mi caso, estoy usando [Docker Hub](https://hub.docker.com):

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/docker/hub.png){:.lead data-width="800" data-height="100"}
Docker Hub
  {:.figure}

## Ejecutando el contenedor de Docker

Podemos ejecutar nuestro contenedor docker una vez que hayamos ejecutado el comando build. 
Podemos ejecutarlo con el siguiente comando:
~~~bash
#Run
docker run -i -p 3000:3000 -t xavidop/alexa-skill-nodejs-express:latest
~~~

**NOTA:** este comando debe ejecutarse en la carpeta raíz de este proyecto.

Después de ejecutar esto, podemos ejecutar peticiones de Alexa al endpoint `localhost:3000`.

## Recursos
* [Official Alexa Skills Kit Node.js SDK](https://www.npmjs.com/package/ask-sdk) - The Official Node.js SDK Documentation
* [Official Alexa Skills Kit Documentation](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - Official Alexa Skills Kit Documentation
* [Official Express Adapter Documentation](https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit-sdk-for-nodejs/host-web-service.html) - Express Adapter Documentation
* [Official Docker Documentation](https://docs.docker.com/) - Docker Documentation

## Conclusión 

Ahora tenemos nuestra Skill de Alexa ejecutándose como una aplicación NodeJS Express dentro de un contenedor. Estamos listos para crear todos los objetos de Kubernetes. Pero antes de esto, necesitamos resolver el problema de la persistencia porque ahora no tenemos acceso a un DynamoDB.

Espero que este proyecto de ejemplo te sea de utilidad.

Puede encontrar el código [aquí](https://github.com/xavidop/alexa-nodejs-k8s-helloworld)

¡Eso es todo amigos!

Happy coding!


