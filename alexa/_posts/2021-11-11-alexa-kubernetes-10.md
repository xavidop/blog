---
layout: post
title: Alexa y Kubernetes
image: /assets/img/blog/post-headers/alexa-kubernetes.jpg
description: >
   Guía paso a paso para construir desplegar Alexa Skill en Kubernetes
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

# Alexa ejecutandose en Kubernetes

En esta serie de publicaciones, encontraréis todos los recursos necesarios para transformar o crear una Skill de Alexa como una aplicación NodeJS Express lista para ejecutarse en Kubernetes.
Estas son las dos opciones posibles que se puede utilizar para ejecutar nustra Skill de Alexa en kubernetes:

**1. Uso de Mongo Atlas Cloud**
  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/atlas.png){:.lead data-width="800" data-height="100"}
Mongo Atlas Cloud
  {:.figure}

**2. Uso del MongoDB proporcionado en el Helm Chart**
  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/provided.png){:.lead data-width="800" data-height="100"}
Mongo proporcionado en la tabla de timones
  {:.figure}
Estas múltiples opciones son compatibles con esta implementación.

Estas son las carpetas principales del proyecto:

~~~bash
    ├───.vscode
    ├───alexa-skill
    ├───app
    ├───docker
    ├───helm
    └───terraform
        ├───eks
        ├───aks
        └───gke
~~~

* **.vscode:** preferencias para ejecutar localmente nuestra Skill y también para pruebas locales.
* **alexa-skill:** esta carpeta contiene todos los metadatos de la Alexa Skill, como el modelo de interacción, los assets, el Skill Manifest, etc. En esta carpeta podrás ejecutar todos los comandos `ask cli`.
* **app:** el backend de la aplicación Alexa Skill en NodeJS usando Express.
* **docker:** donde se puede encontrar el Dockerfile del backend de la Alexa Skill como una aplicación NodeJS.
* **Helm:** el Helm Chart de la Alexa Skill listo para desplegarse en cualquier clúster de Kubernetes.
* **terraform:** Archivos Terraform para diferentes tipos de cloud privadas.
   * **eks:** Todos los archivos necesarios para desplegar una skill de Alexa y un clúster de Kubernetes en AWS Elastic Kubernetes Service.
   * **aks:** Todos los archivos necesarios para desplegar una skill de Alexa y un clúster de Kubernetes en Azure Kubernetes Service.
   * **gke:** Todos los archivos necesarios para idesplegar una skill de Alexa y un clúster de Kubernetes en Google Kubernetes Engine.


Expliquemos todos los pasos necesarios para crear una Skill de Alexa y deplegarla en un clúster de Kubernetes.
En cada paso encontraréis todos los requisitos previos necesarios para ese paso.

## 1. Alexa Skill como servidor web

Cómo crear una Skill de Alexa como una aplicación NodeJS usando Express. Tenéis la explicación completa [aquí](docs/WEBSERVER.md).

## 2. Acoplamiento de la Skill de Alexa

Dockerizar nuestro backend de nuestra Alexa Skill que se transformó en una aplicación NodeJS Express. Tenéis la explicación completa [aquí](docs/DOCKER.md).

## 3. Adaptador de persistencia MongoDB

Uso del nuevo adaptador de persistencia para MongoDB. Tenéis la explicación completa [aquí](https://github.com/xavidop/ask-sdk-mongodb-persistence-adapter).

## 4. Objetos de Kubernetes de la Skill de Alexa

Crear todos los objetos de Kubernetes necesarios para implementar nuestra Skill de Alexa en un clúster de Kubernetes. Tenéis la explicación completa [aquí](docs/KUBERNETES.md).

## 5. Helm Chart de la Skill de Alexa

Creando el Hel Chart con nuestra Alexa Skill + MongoDB. Tenéis la explicación completa [aquí](docs/HELM.md).

## 6. Desarrollo y despliegue local con DevSpace

Cómo desarrollar en un entorno de Kubernetes. Tenéis la explicación completa [aquí](docs/LOCAL_DEVELOPMENT_DEPLOYMENT.md).

## 7. Terraform.

### 7.1. Despliegue de una Alexa Skill en AWS Elastic Kubernetes Services

Cómo desplegar nuestra Skill de Alexa en EKS. Tenéis la explicación completa [aquí](docs/TERRAFORM_EKS.md).

### 7.2. Despliegue de una Skill de Alexa en Azure Kubernetes Services

Cómo deplegar nuestra Skill de Alexa en AKS. Tenéis la explicación completa [aquí](docs/TERRAFORM_AKS.md).

### 7.3. Despliegue de una Alexa Skill en Google Kubernetes Engine

Cómo desplegar nuestra Skill de Alexa en GKE. Tenéis la explicación completa [aquí](docs/TERRAFORM_GKE.md).

Espero que este proyecto de ejemplo te sea de utilidad.

Puede encontrar el código [aquí](https://github.com/xavidop/alexa-nodejs-k8s-helloworld)

¡Eso es todo amigos!

Happy coding!