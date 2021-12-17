---
layout: post
title: Alexa y Kubernetes. Objetos de Kubernetes de una Alexa Skill (IV)
image: /assets/img/blog/post-headers/alexa-kubernetes-objects.jpg
description: >
   Objetos Kubernetesnecesarios para desplegar nuestra Alexa Skill
comments: true
author: xavi
kate: hl markdown;
categories: [alexa, kubernetes]
tags:
  - alexa
  - kubernetes
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

En este paso tenemos nuestra habilidad de Alexa correctamente dockerizada. Como todavía no vamos a empaquetar todos los componentes software (Alexa Skill + MongoDB), en este paso configuraremos todos los objetos kubernetes de nuestra Alexa Skill usando [MongoDB Atlas](https://cloud.mongodb.com/):

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/atlas.png){:.lead data-width="800" data-height="100"}
Usando MongoDB Atlas
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

## Creando el clúster de Kubernetes con Kind

Lo primero que debemos hacer es instalar un clúster de Kubernetes en nuestra máquina local para crear todos los objetos de Kubernetes.

Para eso usaremos Kind. kind es una herramienta para ejecutar clústeres de Kubernetes locales mediante los "nodos" de contenedor de Docker.
kind fue diseñado principalmente para probar el propio Kubernetes, pero puede usarse para desarrollo local o CI.

Con Kind puede crear clústeres utilizando un archivo YAML:

~~~yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 3008
    protocol: TCP
  - containerPort: 443
    hostPort: 3009
    protocol: TCP
~~~

Podemos aprovechar la opción de configuración extraPortMapping de Kind al crear un clúster para mapear puertos desde el host a un ingress controller que se ejecuta en un nodo. Expondremos el puerto 80 del clúster Kind al puerto 3008 de nuestra máquina local y el 443 al puerto 3009 de nuestra máquina local.
Este archivo YAML se encuentra en la carpeta raíz llamado `cluster.yaml`.

Podemos desplegar el clúster ejecutando los siguientes comandos:
~~~bash 
kind create cluster --config cluster.yaml

#Get the Kubernetes context to execute kubectl commands
kubectl cluster-info --context kind-kind
~~~ 

Si queremos destruir el clúster, simplemente ejecutamos el siguiente comando:
~~~bash 
kind delete cluster
~~~ 

## Creando los objetos de Kubernetes

Los objetos que vamos a crear son los siguientes para ejecutar nuestra Skill de Alexa lista para ejecutarse en Kubernetes:
**1. Deployment:** el deploymnet es uno de los objetos de kubernetes más importantes. Un deployment proporciona actualizaciones declarativas para pods. Un pod es un grupo de uno o más contenedores, con almacenamiento compartido y recursos de red, y una especificación sobre cómo ejecutar los contenedores.
**2. Service:** es una forma abstracta de exponer una aplicación que se ejecuta en un conjunto de Pods como un servicio dentro de la red.
**3. Ingress:** es un rescurso que administra el acceso externo a los servicios en un clúster. Es una capa creada sobre los servicios de Kubernetes. Requiere un cIngress Controller para administrar todas las peticiones entrantes.

Aquí podemos encontrar un esquema simple de cómo funciona Kubernetes:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/kubernetes/kube.png){:.lead data-width="800" data-height="100"}
Kubernetes
  {:.figure}

Nuestra Alexa Skill será un contenedor en ejecución gracias a nuestro Deployment. Expondremos el puerto de la Alexa Skill gracias al objeto Kubernetes Service y finalmente vamos a acceder al Alexa Skill a través del puerto expuesto gracias al objeto Kuberntes Ingress.

### Deployment

Podemos describir el estado deseado en un deployment, y el Deployment Controller cambia el estado real al estado deseado a una velocidad controlada. Podemos definir deployments para crear nuevos pods o para eliminar deployments existentes y adoptar todos nuestros recursos con nuevos deployments.

~~~yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alexa-skill
  labels:
    helm.sh/chart: alexa-skill-1.0.0
    app.kubernetes.io/name: alexa-skill
    app.kubernetes.io/instance: alexa-skill
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: alexa-skill
      app.kubernetes.io/instance: alexa-skill
  template:
    metadata:
      labels:
        app.kubernetes.io/name: alexa-skill
        app.kubernetes.io/instance: alexa-skill
    spec:
      containers:
        - name: alexa-skill
          image: "xavidop/alexa-skill-nodejs-express:latest"
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 3000
              protocol: TCP
          resources:
            limits:
              cpu: 50m
              memory: 128Mi
            requests:
              cpu: 50m
              memory: 128Mi
          env:
            - name: DB_TYPE
              value: atlas
            - name: DB_HOST      
              value: cluster0.qlqga.mongodb.net         
            - name: DB_PORT
              value: "27017"
            - name: DB_USER
              value: root
            - name: DB_PASSWORD
              value: root
            - name: DB_DATABASE
              value: alexa
~~~

Como se puede ver, nuestro Deployment tendrá una réplica. En caso de que nuestra Skill de alexa tenga muchas peticiones, podemos actualizar la cantidad de réplicas o crear un objeto de Kubernetes [HorizontalPodAutoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/), pero el uso es opcional:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/kubernetes/autoscaler.svg){:.lead data-width="800" data-height="100"}
Autoscaler
  {:.figure}

Veamos la especificación de nuestro deployment:
1. Lo primero que notaremos es que en la lista de `containers` solo tenemos un contenedor definido, que es nuestra Skill de Alexa.
2. La imagen construida en el artículo anterior se establece en el objeto `containers.image`.
3. Exponemos el puerto del cointainer que es el **3000**. Ya que es un puerto que recibirá solicitudes HTTP. El protocolo que tenemos que establecer es `tcp`.
4. Hemos configurado la memoria de nuestro pod en "128Mi", significa 128 MegaBytes. En términos de CPU, lo hemos configurado en `50mi`. Se mide en milicores.
5. En el objeto `env` estableceremos todas las variables de entorno y sus valores que usará nuestro cointaner.

Con eso tenemos listo nuestro Deployment. Este Deployment creará un pod con un contenedor.

Finalmente tenemos que modificar nuestra aplicación NodeJS de nuestra Alexa Skill para obtener toda la información de las variables de entorno que hemos establecido en el Deployment:

~~~javascript
const connOpts = {
  host: process.env.DB_HOST ? process.env.DB_HOST : 'cluster0.qlqga.mongodb.net',
  user: process.env.DB_USER ? process.env.DB_USER : 'root',
  port: process.env.DB_PORT ? process.env.DB_PORT : '27017',
  password: process.env.DB_PASSWORD ? process.env.DB_PASSWORD : 'root',
  database: process.env.DB_DATABASE ? '/' + process.env.DB_DATABASE : '',
};

let uri = '';
if (process.env.DB_TYPE === 'atlas'){
  uri = `mongodb+srv://${connOpts.user}:${connOpts.password}@${connOpts.host}${connOpts.database}`;
} else {
  // eslint-disable-next-line max-len
  uri = `mongodb://${connOpts.user}:${connOpts.password}@${connOpts.host}:${connOpts.port}${connOpts.database}`;
}
~~~

Con todos los cambios realizados, solo tenemos que desplegar nuestro Deployment ejecutando el siguiente comando:

~~~bash
#Create Namespace
kubectl create namespace alexa-skill

#Create deployment
kubectl apply -f deployment.yaml
~~~

### Service

El siguiente paso es crear el servicio de Kubernetes. Con Kubernetes, no necesitamos modificar nuestra aplicación para utilizar un mecanismo de descubrimiento de servicios  Kubernetes da a los pods sus propias direcciones IP y un solo nombre de DNS para un conjunto de pods, y podemos ambién, equilibrar la carga entre ellos.

~~~yaml
apiVersion: v1
kind: Service
metadata:
  name: alexa-skill
  labels:
    helm.sh/chart: alexa-skill-1.0.0
    app.kubernetes.io/name: alexa-skill
    app.kubernetes.io/instance: alexa-skill
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  ports:
    - port: 3000
      targetPort: 3000
      protocol: TCP
  selector:
    app.kubernetes.io/name: alexa-skill
    app.kubernetes.io/instance: alexa-skill
~~~

Lo importante aquí son las especificaciones de `port`, `targetPort` y `protocol`:
**1. port:** El port es el puerto que utilizará el servicio de Kubernetes.
**2. targetPort:** el puerto del contenedor. Esta propiedad vincula el puerto del contenedor que se ejecuta en el pod con el servicio.
**3. protocol:** el protocolo del puerto. Usaremos `TCP` porque este servicio recibirá solicitudes HTTP.

Por defecto, los servicios son del tipo `ClusterIP`. Expone el Servicio en una IP interna del clúster. Elegir este valor hace que el Servicio solo sea accesible desde dentro del clúster

Con todos los cambios realizados, solo tenemos que desplegar nuestro Servicio ejecutando el siguiente comando:
~~~bash
kubectl apply -f service.yaml
~~~

### Ingress

Ingress expone rutas HTTP y HTTPS desde fuera del clúster a servicios dentro del clúster. El enrutamiento del tráfico se controla mediante reglas definidas en el Ingress. Un Ingress puede configurarse para proporcionar a los Servicios URL accesibles externamente, equilibrar la carga del tráfico, SSL/TLS y ofrecer name-based virtual hosting. El Ingress controller es el responsable de interactuar con el Ingress, generalmente con un balanceador de carga, aunque también se puede configurar su edge router o interfaces adicionales para ayudar a manejar el tráfico.

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/kubernetes/ingress.png){:.lead data-width="800" data-height="100"}
Ingress
  {:.figure}

Un Ingress requiere un Ingress controller. Como podemos ver en el esquema en la más arriba de esta publicación, usaremos el Ingress controller de Nginx.

Para instalar este Ingress Controller en nuestro Kind Cluster tenemos que ejecutar el siguiente comando:

~~~bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/kind/deploy.yaml
~~~

Una vez que los pods del Nginx Ingress Controller estén en funcionamiento, podemos crear nuestro Ingress:

~~~yaml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: alexa-skill-ingress
  labels:
    helm.sh/chart: alexa-skill-1.0.0
    app.kubernetes.io/name: alexa-skill
    app.kubernetes.io/instance: alexa-skill
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    # Target URI where the traffic must be redirected
    # More info: https://github.com/kubernetes/ingress-nginx/blob/master/docs/examples/rewrite/README.md
    nginx.ingress.kubernetes.io/rewrite-target: /
    kubernetes.io/ingress.class: nginx
spec:
  rules:
    # Uncomment the below to only allow traffic from this domain and route based on it
    # - host: my-host # your domain name with A record pointing to the nginx-ingress-controller IP
    - http:
        paths:
        - path: / # Everything on this path will be redirected to the rewrite-target
          backend:
            serviceName: alexa-skill # the exposed svc name and port
            servicePort: 3000
~~~
Podemos ver en la especificación del Ingress que todas las solicitudes al URI `/` serán administradas por este Ingress. Este Ingress está vinculado al servicio de Kubernetes a través de las propiedades `serviceName` y `servicePort`.

Con todos los cambios realizados, solo tenemos que desplegar nuestro Ingress ejecutando el siguiente comando:

~~~bash
kubectl apply -f ingress.yaml
~~~

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

## Recursos
* [Official Alexa Skills Kit Node.js SDK](https://www.npmjs.com/package/ask-sdk) - The Official Node.js SDK Documentation
* [Official Alexa Skills Kit Documentation](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - Official Alexa Skills Kit Documentation
* [Official Express Adapter Documentation](https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit-sdk-for-nodejs/host-web-service.html) - Express Adapter Documentation
* [Official Kind Documentation](https://kind.sigs.k8s.io/) - Kind Documentation
* [Official Kubernetes Documentation](https://kubernetes.io/docs) - Kubernetes Documentation

## Conclusión 

Ahora tenemos nuestra Skill de Alexa ejecutándose en un servidor de kubernetes localmente y usando la nube de Mongo Atlas. Ahora tenemos que empaquetar todos los objetos de Kubernetes usando Helm.

Espero que este proyecto de ejemplo os sea de utilidad.

Podéis encontrar el código [aquí](https://github.com/xavidop/alexa-nodejs-k8s-helloworld)

¡Eso es todo amigos!

Happy coding!
