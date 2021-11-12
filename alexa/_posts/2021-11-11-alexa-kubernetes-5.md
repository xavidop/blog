---
layout: post
title: Alexa y Kubernetes. Helm chart de nuestra Alexa skill (V)
image: /assets/img/blog/post-headers/alexa-helm.jpg
description: >
   Templatizar nuestros objetos Kubernetes usando Helm
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

En este paso, tenemos nuestra Skill de Alexa dockerizada correctamente y todos los objetos de Kubernetes creados y ejecutándose en un clúster de Kubernetes. Ahora es el momento de empaquetar todos los componentes software (Alexa Skill + MongoDB), en este paso transformaremos todos nuestros objetos de kubernetes en templates usando Helm y agregaremos una instancia de MongoDB lista para ser desplegada en un clúster de Kubernetes como dependencia de nuestro Helm Chart:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/provided.png){:.lead data-width="800" data-height="100"}
Uso de MongoDB proporcionado en el Chart de Helm
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
9. Helm v3.x

## Helm chart

Para diseñar el Helm Chart de nuestra Skill de Alexa, es importante explicar qué es Helm. Esta herramienta facilitará el desarrollo y el ciclo de vida de la Alexa Skill. También es una herramienta que se utiliza para administrar paquetes de Kubernetes. Estos paquetes se denominan Charts.
Un Chart es una colección de archivos que describen un conjunto de recursos de Kubernetes.
Con Helm podemos realizar las siguientes tareas:
* Empaquetar nuestras aplicaciones como Chart.
* Interactuar con repositorios de Charts (públicos o privados).
* Instalación y desinstalación de Charts en clústeres de Kubernetes.
* Gestión de Charts previamente instalados con Helm.
* 
Además, es una herramienta para administrar recursos de Kubernetes empaquetados y preconfigurados. En otras palabras, Helm nos permite administrar templates que facilitan el despliegue de cualquier objeto de Kubernetes. Entonces, no será necesario tener conocimientos avanzados de esos objetos de Kubernetes para desplegarlos.

Nuestro Helm Chart se encuentra en `helm/alexa-skill-chart`
~~~bash
├── Chart.yaml
├── README.md
├── requirements.yaml
├── templates
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
└── values.yaml
~~~

El Chart de esta Skill de Alexa tendría los siguientes archivos:
1. Chart.yaml: archivo con los metadatos del paquete. Nombre, versión, descripción. En este archivo indicaremos las dependencias de la Alexa Skill (MongoDB). Aquí podemos agregar otros Charts.
2. Templates: los templates se almacenan en este directorio.
3. values.yml: valores predeterminados utilizados en los templates.

Antes de comenzar, como nuestro Chart incluye un MongoDB como dependencia, tendremos que agregarlo en nuestro archivo `Chart.yaml`.

Primero necesitamos agregar el repositorio de Helm donde se almacena el Chart de MongoDB con los siguientes comandos:
~~~bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
~~~
Luego podemos agregar el Chart de MongoDB: https://github.com/bitnami/charts/tree/master/bitnami/mongodb en nuestro archivo `Chart.yaml`:

~~~yaml
apiVersion: v2
name: alexa-skill
description: A Helm chart for Kubernetes

# A chart can be either an 'application' or a 'library' chart.
#
# Application charts are a collection of templates that can be packaged into versioned archives
# to be deployed.
#
# Library charts provide useful utilities or functions for the chart developer. They're included as
# a dependency of application charts to inject those utilities and functions into the rendering
# pipeline. Library charts do not define any templates and therefore cannot be deployed.
type: application

# This is the chart version. This version number should be incremented each time you make changes
# to the chart and its templates, including the app version.
version: 1.0.0

# This is the version number of the application being deployed. This version number should be
# incremented each time you make changes to the application.
appVersion: 1.0.0

dependencies:
- name: mongodb
  version: 10.3.3
  repository: alias:bitnami
  alias: mongodb
  condition: mongodb.enabled
~~~

## Creando los templates

La siguiente imagen muestra lo que sucede cuando usamos Helm y cómo transforma nuestros templates en objetos de Kubernetes:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/helm/helm.png){:.lead data-width="800" data-height="100"}
Helm templates
  {:.figure}

Ahora agregaremos la capa Helm para permitir que nuestra Skill de alexa sea escalable, extensible, environment-aware, version-aware, incremental, personalizada, dinámica y reutilizable. Agregar esta capa significa crear templates para todos nuestros objetos de Kubernetes.

### Deployment template

A continuación podemos encontrar el Deployment de nuestra Skill de Alexa pero ahora con la capa Helm que nos permite configurar toda la información a través del archivo `values.yaml`.
{% raw  %}
~~~yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "alexa-skill.fullname" . }}
  labels:
    {{- include "alexa-skill.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "alexa-skill.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "alexa-skill.selectorLabels" . | nindent 8 }}
    spec:
    {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
    {{- end }}
      containers:
        - name: {{ .Chart.Name }}
          image:  .Values.image.repo }}/{{ .Values.image.name }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.NodePort }}
              protocol: TCP
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          env:
            - name: DB_TYPE
              value: {{ .Values.mongodb.type }}
            - name: DB_HOST
              {{ if eq .Values.mongodb.type "provided" }}
              value: {{ include "alexa-skill.fullname" . }}-{{ .Values.mongodb.service.name }}
              {{ else }}
              value: {{ .Values.mongodb.service.name }}
              {{ end }}
            - name: DB_PORT
              value:  .Values.mongodb.service.port }}"
            - name: DB_USER
              value: {{ .Values.mongodb.auth.username }}
            - name: DB_PASSWORD
              value: {{ .Values.mongodb.auth.password }}
            - name: DB_DATABASE
              value: {{ .Values.mongodb.auth.database }}    
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
    {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
    {{- end }}
    {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
    {{- end }}

~~~
{% endraw  %}

### Service template

A continuación podemos encontrar el Servicio de nuestra Skill de Alexa pero ahora con la capa Helm que nos permite configurar toda la información a través del archivo `values.yaml`.

{% raw  %}
~~~yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "alexa-skill.fullname" . }}
  labels:
    {{- include "alexa-skill.labels" . | nindent 4 }}
spec:
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.NodePort }}
      protocol: TCP
  selector:
    {{- include "alexa-skill.selectorLabels" . | nindent 4 }}

~~~
{% endraw  %}


### Ingress template

A continuación podemos encontrar el Ingress de nuestra Skill de Alexa pero ahora con la capa Helm que nos permite configurar toda la información a través del archivo `values.yaml`.

{% raw  %}
~~~yaml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: {{ .Values.ingress.name }}
  labels:
    {{- include "alexa-skill.labels" . | nindent 4 }}
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
            serviceName: {{ include "alexa-skill.fullname" . }} # the exposed svc name and port
            servicePort: {{ .Values.ingress.port }}
~~~
{% endraw  %}


### Ficheros Values

Como podemos ver, todos nuestros objetos de Kubernetes se convierten en templates. Estos templates necesitan un archivo `values.yaml` para obtener el objeto final de Kubernetes.

Si queremos utilizar la **Alexa Skill con MongoDB proporcionado** en el Helm Chart:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/provided.png){:.lead data-width="800" data-height="100"}
MongoDB porporcionado en el Helm Chart
  {:.figure}

Podemos utilizar este archivo `Valores`:

~~~yaml
# Default values for alexa-skill.
# This is a YAML-formatted file.
# Declare variables to be passed into your templates.

replicaCount: 1

image: 
  repo: xavidop
  name: alexa-skill-nodejs-express
  tag: latest
pullPolicy: Always

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

service:
  port: 3000
  NodePort: 3000

ingress:
  enabled: true
  name: alexa-skill-ingress
  port: 3000

resources:
  limits:
    cpu: 50m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 128Mi

# Mongo provided conneciton
mongodb:
  enabled: true
  type: provided # could be atlas or provided
  auth:
    username: root
    password: root
    database: alexa
    rootPassword: root
  service:
    name: mongodb
    port: 27017

nodeSelector: {}

tolerations: []

affinity: {}
~~~


Si queremos utilizar la **Alexa Skill con MongoDB Atlas Cloud**:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/atlas.png){:.lead data-width="800" data-height="100"}
MongoDB con Atlas Cloud
  {:.figure}

Podemos utilizar este archivo `Valores`:

~~~yaml
# Default values for alexa-skill.
# This is a YAML-formatted file.
# Declare variables to be passed into your templates.

replicaCount: 1

image: 
  repo: xavidop
  name: alexa-skill-nodejs-express
  tag: latest
pullPolicy: Always

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

service:
  port: 3000
  NodePort: 3000

ingress:
  enabled: true
  name: alexa-skill-ingress
  port: 3000

resources:
  limits:
    cpu: 50m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 128Mi

# Atlas connection
mongodb:
  enabled: false
  type: atlas # could be atlas or provided
  auth:
    username: root
    password: root
    database: alexa
  service:
    name: cluster0.qlqga.mongodb.net

nodeSelector: {}

tolerations: []

affinity: {}
~~~

## Instalación del Helm Chart

Una vez explicado todo el Chart de Helm. Ahora tenemos que instalarlo en nuestro Kind Cluster. Para eso, tenemos que ejecutar el siguiente comando:
~~~bash
# Update the dependencies
helm dep update helm/alexa-skill-chart/
# Install the chart
helm install alexa-skill helm/alexa-skill-chart/ --namespace alexa-skill
~~~

If we want to remove oour Chart Installer, just run the following command:
~~~bash
## Uninstall
helm uninstall alexa-skill --namespace alexa-skill
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
* [Official Helm Documentation](https://helm.sh/docs/) - Helm Documentation


## Conclusión 

Como se puede ver, tenemos nuestra Skill de Alexa ejecutándose en Kubernetes usando templates y empaquetados como Helm Chart. Gracias al archivo `Values` podemos cambiar todos los parámetros/propiedades clave de nuestra Alexa Skill de una manera fácil.

Espero que este proyecto de ejemplo os sea de utilidad.

Puede encontrar el código [aquí](https://github.com/xavidop/alexa-nodejs-k8s-helloworld)

¡Eso es todo amigos!
Happy coding!