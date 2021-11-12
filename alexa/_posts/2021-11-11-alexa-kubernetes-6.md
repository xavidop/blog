---
layout: post
title: Alexa y Kubernetes. Desarrollo y despliegue local con DevSpace (VI)
image: /assets/img/blog/post-headers/alexa-kubernetes-local.jpg
description: >
   Uso de DevSpace para el desarrollo local de nuestra Alexa Skill en entornos Kubernetes
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

Es un hecho que el proceso de desarrollo en un entorno de Kubernetes no es fácil. Hay muchas herramientas que nos ayudan en este proceso. Para este caso de uso, usaremos DevSpace. Una herramienta para desarrolladores que facilita el ciclo del desarrollo en entornos Kubernetes.

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/devspace/devspace.svg){:.lead data-width="800" data-height="100"}
DevSpace
  {:.figure}

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Node.js v12.x
2. Visual Studio Code
3. Docker 19.x
5. MongoDB Atlas Account
6. Kubectl CLI
7. Kind
8. go >=1.11
9. DevSpace CLI
   
## DevSpace

DevSpace es una herramienta de desarrollo de código abierto y solo client-side para Kubernetes:

* Podemos crear, pruebar y depurar aplicaciones directamente dentro de Kubernetes
* Desarrollar con hot reloading: actualizar los contenedores en ejecución sin reconstruir imágenes o reiniciar contenedores
* Unificar los flujos de trabajo de implementación dentro de nuestro equipo y en todo el desarrollo, staging y producción
* Automatizar las tareas repetitivas para la creación y el despliegue de imágenes

Así es como funciona DevSpace:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/devspace/workflow.png){:.lead data-width="800" data-height="100"}
Devspace workflow
  {:.figure}

### Beneficios

Mencionando la documentación de DevSpace:
DevSpace nos permite almacenar todos nuestros workflows en un archivo de configuración declarativo: `devspace.yaml`
* Codificar el workflow sobre la creación de imágenes, el despliegue de nuestro proyecto y nuestras dependencias, etc.
* Versionado de nuestros workflows junto con su código (es decir, podemos poner en marcha cualquier versión anterior con un solo comando)
* Compartir nuestros workflow con nuestros compañeros de equipo

DevSpace ayuda a nuestro equipo a estandarizar los workflow de despliegue y desarrollo sin que todos los miembros de nuestro equipo se conviertan en expertos en Kubernetes.
* El experto en DevOps y Kubernetes de nuestro equipo puede configurar DevSpace usando `devspace.yaml` y simplemente lo commitea a través de git
* Si otros desarrolladores de nuestro equipo revisan el proyecto, solo necesitan ejecutar el despliegue de devspace para levantar el proyecto (incluida la creación de imágenes y el despligue de otros proyecto relacionados, etc.) y tener una instancia del proyecto en ejecución.
* La configuración de DevSpace es altamente dinámica, por lo que podemos configurar todo usando variables de configuración que hacen que sea mucho más fácil tener una configuración base pero aún se pudan permitir diferencias entre desarrolladores (por ejemplo, diferentes subdominios para pruebas)

En lugar de reconstruir imágenes y volver a desplegar contenedores, DevSpace te permite recargar contenedores en ejecución mientras estás codificando:
* Simplemente editamos nuestros archivos con nuestro IDE y veremos cómo se recarga nuestra aplicación dentro del contenedor en ejecución.
* La sincronización de archivos bidireccional de alto rendimiento detecta los cambios de código de inmediato y sincroniza los archivos de inmediato entre el entorno de desarrollo local y los contenedores que se ejecutan en Kubernetes.
*  Stream logs, conectar debuggers o abrir una terminal en los contenedores directamente desde nuestro IDE con un solo comando.

El deslpiegue y depuración de servicios con Kubernetes requiere mucho conocimiento y nos obliga a ejecutar repetidamente comandos como `kubectl get pod` y copiar los ids de pod de ida y vuelta. Ya no vamos a perder el tiempo más y DevSpace automatizará las tediosas partes del trabajo con Kubernetes:
* DevSpace nos permite crear varias imágenes en paralelo, etiquetarlas automáticamente y desplegar toda nuestra aplicación (incluidas las dependencias) con un solo comando
* DevSpace inicie automáticamente la transferencia de puertos y la transmisión de registros, para que no tengamos que copiar y pegar identificadores de pod o ejecutar 10 comandos constantemente para que todo comience.

DevSpace se ha probado con muchas distribuciones de Kubernetes, que incluyen:
* Clústeres locales de Kubernetes como minikube, k3s, MikroK8s, kind
* Clústeres de Kubernetes administrados en GKE (Google), EKS (AWS), AKS (Azure), DOKS (Digital Ocean)
* Clústeres de Kubernetes autogestionados (por ejemplo, creados con Rancher)

**Lo más importante de DevSpace es que es independiente de la nube. Eso significa que depende de su contexto de Kubernetes.**

## Archivo de configuración

Una vez que se ha explicado DevSpace, echemos un vistazo a nuestro archivo de configuración de DevSpace: `devspace.yaml`:
~~~yaml
version: v1beta9

images:
  app:
    image: xavidop/alexa-skill-nodejs-express
    dockerfile: ./docker/Dockerfile
    preferSyncOverRebuild: true
    entrypoint:
    - npm
    - run
    - dev

deployments:
- name: alexa-skill
  helm:
    chart:
      name: ./helm/alexa-skill-chart
    values:
      image:
        tag: tag(xavidop/alexa-skill-nodejs-express)

dev:
  open:
  - url: http://localhost:3000
  autoReload:
    paths:
    - ./app/package.json
    - ./docker/Dockerfile
  sync:
  - imageName: app
    disableDownload: true
    localSubPath: ./app
    excludePaths:
    - ./node_modules

~~~

Echemos un vistazo a este archivo paso a paso:
**1. `images`:** aquí vamos a especificar el nombre de la imagen que vamos a utilizar y donde se almacena el `Dockerfile`. Una característica interesante de DevSpace es que puedes sobrescribir el entrypoint de nuestra imagen Docker para depuración.
**2. `deployments`:** aquí podemos especificar toda el despliegue que queremos despelgar en nuestro clúster de Kubernetes. Aquí puede especificar Charts de Helm con sus valores, objetos de Kubernetes o Charts de componente de Helm. Estos últimos son charts hechos on-the-fly.
**3. `dev`:** aquí especificaremos toda la configuración que necesitamos para desarrollar nuestras aplicaciones. En este ejemplo especificamos la recarga automática de la imagen de Docker cuando hay un cambio en los archivos `package.json` y `Dockerfile`. Luego especificamos la carpeta de sincronización que queremos mantener sincronizada entre nuestra máquina y el Clúster de Kubernetes.

Una de las características interesantes que tiene DevSpace es que si tenemos dependencias con otros repositorios GIT, podemos agregarlo al objeto `dependencies` en el archivo de configuración YAML de esta manera:

~~~yaml
dependencies:
- source:
    git: https://github.com/my-api-server
    branch: stable
- source:
    git: https://github.com/my-auth-server
    revision: c967392
  profile: production
- source:
    git: https://github.com/my-database-server
    tag: v3.0.1
    subPath: /configuration
~~~
## Iniciar el desarrollo y el desarrollo

Tenemos el archivo de configuración debidamente condfigurado. Ahora tenemos que ejecutar los siguientes comandos para comenzar nuestro desarrollo con DevSpace:
~~~bash
devspace use namespace alexa-skill
devspace dev
~~~

Cuando DevSpace se está ejecutando y todo está desplegado y todos los archivos sincronizados, DevSpace crea una WebUI donde podemos explorar nuestro despliegue. La web está disponible en http://localhost:8090/

Por ejemplo, podemos ver los logs de nuestros pods:
  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/devspace/logs.png){:.lead data-width="800" data-height="100"}
DevSpace Logs
  {:.figure}

O podemos ejecutar una terminal de shell dentro de nuestros pods directamente a través del sitio web:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/devspace/console.png){:.lead data-width="800" data-height="100"}
DevSpace Console
  {:.figure}

Ahora podemos comenzar a desarrollar nuestra Skill de Alexa localmente y sincronizarnos automáticamente con nuestro Clúster de Kubernetes gracias a DevSpace

## Probando peticiones localmente

Seguro que ya conoceis la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios web. Aunque REST se ha vuelto omnipresente, no siempre es fácil de probar. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir API, lo que nos ayudará a nosotros y a nuestro equipo a ser más productivos a largo plazo.

Después de ejecutar nuestra aplicación, tendremos un endpoint disponible en http://localhost:3008. Con Postman podemos emular cualquier solicitud de Alexa.

Por ejemplo, podemos probar una `LaunchRequest`:

~~~json

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
      "timestamp": "2020-03-22T17:24:44Z",
      "locale": "en-US"
    }
  }
~~~

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/devspace/request.png){:.lead data-width="800" data-height="100"}
Devspace Request
  {:.figure}

## Destrucción o parar el desarrollo

Si queremos eliminar toda la pila creada por DevSpace, simplemente ejecutamos:
~~~bash
devspace purge -d alexa-skill
~~~

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/devspace/remove.png){:.lead data-width="800" data-height="100"}
Eliminando el despliegue de Devspace
  {:.figure}

## Recursos
* [Official Alexa Skills Kit Node.js SDK](https://www.npmjs.com/package/ask-sdk) - The Official Node.js SDK Documentation
* [Official Alexa Skills Kit Documentation](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - Official Alexa Skills Kit Documentation
* [Official Express Adapter Documentation](https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit-sdk-for-nodejs/host-web-service.html) - Express Adapter Documentation
* [Official Kind Documentation](https://kind.sigs.k8s.io/) - Kind Documentation
* [Official Kubernetes Documentation](https://kubernetes.io/docs) - Kubernetes Documentation
* [Devspace Documentation](https://devspace.sh/cli/docs/introduction) - Devspace Documentation
  
## Conclusión 

Como se puede ver, DevSpace facilita nuestro proceso de desarrollo en un clúster de Kubernetes. Con solo un archivo de configuración y 3 comandos tenemos todo configurados y podemos comenzar a desarrollar nuestra Alexa Skill.

Espero que este proyecto de ejemplo te sea de utilidad.

Puede encontrar el código [aquí](https://github.com/xavidop/alexa-nodejs-k8s-helloworld)

¡Eso es todo amigos!

Happy coding!

