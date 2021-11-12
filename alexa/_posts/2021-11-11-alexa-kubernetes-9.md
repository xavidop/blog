---
layout: post
title: Alexa and Kubernetes. Desplegando una Alexa Skill en Google Kubernetes Engine (IX)
image: /assets/img/blog/post-headers/alexa-gke.jpg
description: >
   Despliegue automático Alexa Skill en GKE con Terraform
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

Ahora tenemos todo preparado y listo para pasar a un clúster de Kubernetes en un proveedor cloud. Es un hecho que crear un clúster en cualquier proveedor cloud de forma manual es una tarea difícil. Además, si queremos automatizar estos despliegues, necesitamos algo que nos ayude en esta tediosa tarea. En esta publicación veremos cómo crear un clúster de Kubernetes y todos sus objetos requeridos y cómo implementar nuestra Skill de Alexa con Terraform usando [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine?)

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/gke/gke.png){:.lead data-width="800" data-height="100"}
Google Kubernetes Engine
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
9. Terraform 12.x
10. Google Cloud Account
11. gcloud CLI

## Terraform

Terraform es una herramienta para construir, cambiar y crear versiones de infraestructuras cloud de manera segura y eficiente. Terraform puede gestionar proveedores de servicios existentes y populares, así como soluciones internas personalizadas.

Los archivos de configuración le indican a Terraform los componentes necesarios para ejecutar una sola aplicación. Terraform genera un plan de ejecución que describe lo que hará para alcanzar el estado deseado y luego lo ejecuta para construir la infraestructura descrita. A medida que cambia la configuración, Terraform puede determinar qué cambió y crear planes de ejecución incrementales que se pueden ir aplicando.

La infraestructura que Terraform puede administrar incluye componentes de bajo nivel como instancias de computación, almacenamiento y redes, así como componentes de alto nivel como entradas de DNS, características de SaaS, etc.

## Ficheros Terraform

Después de la breve descripción general de Terraform, vamos a explicar todos los archivos de terraform y sus objetos que vamos a utilizar para desplegar el clúster y nuestra Skill de Alexa.
Podemos encontrar todos los archivos relacionados con este despliegue en la carpeta`terraform/gke`.

### Terraform Providers

Un provider es el responsable de comprender las interacciones de la API y exponer los resources.
La mayoría de los providers disponibles corresponden a una plataforma de infraestructura cloud o local y ofrecen tipos de resources que corresponden a cada una de las características de esa plataforma.

Para el Google kubernetes Engine, usaremos el provider `google`. Este provider nos permite crear todos los objetos de Google Cloud que necesitamos para crear nuestro Stack para la Skill de Alexa:

~~~hcl
provider "google" {
  project = var.project_id
  region  = var.region
}

~~~

Como vamos a desplegar Helm Charts, se requerirá tener el provider `helm`:
~~~hcl
provider "helm" {

  kubernetes {
    host                   = google_container_cluster.primary.endpoint
    token                  = data.google_client_config.current.access_token
    client_certificate     = base64decode(google_container_cluster.primary.master_auth.0.client_certificate)
    client_key             = base64decode(google_container_cluster.primary.master_auth.0.client_key)
    cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth.0.cluster_ca_certificate)
  }
}

~~~



### Terraform Resources

Uno de los resources más importantes de un clúster de GKE es la red. Por eso, tenemos que crear nuestra red y subredes usando Virtual Private Cloud Network:
~~~hcl
resource "google_compute_network" "vpc" {
  name                    = "${var.project_id}-vpc"
  auto_create_subnetworks = "false"
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.project_id}-subnet"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.10.0.0/24"

}
~~~

Una vez que se ha creado la VPC, podemos crear el clúster que utilizará esa VPC. Para eso, necesitamos usar el módulo `google_container_cluster`:
~~~hcl
resource "google_container_cluster" "primary" {
  name     = "${var.project_id}-gke"
  location = var.region

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

}
~~~

Cada clúster debe tener un grupo de nodos donde se desplegarán los objetos de kubernetes. Para crear ese grupo de nodos en Google Cloud usaremos el resource `google_container_node_pool`:
~~~hcl
resource "google_container_node_pool" "primary_nodes" {
  name       = "${google_container_cluster.primary.name}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.gke_num_nodes

  node_config {
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]

    labels = {
      env = var.project_id
    }

    # preemptible  = true
    machine_type = "n1-standard-1"
    tags         = ["gke-node", "${var.project_id}-gke"]
    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}
~~~

Todos los resources y modules comentados anteriormente están relacionados con el clúster de Kubernetes. Ahora es el momento de desplegar nuestra Skill de Alexa comenzando con el `ngingx-ingress-controller`:
~~~hcl
resource "helm_release" "ingress" {
  name       = "nginx-ingress-controller"
  chart      = "nginx-ingress-controller"
  repository = "https://charts.bitnami.com/bitnami"

  set {
    name  = "rbac.create"
    value = "true"
  }
}
~~~

Después de eso, podemos desplegar con orgullo nuestro el Helm Chart de nuestra Alexa Skill en nuestro clúster de Kubernetes en el Cloud:
~~~hcl
resource "helm_release" "alexa-skill" {
  name       = "alexa-skill"
  chart      = "../../helm/alexa-skill-chart"
  depends_on = [helm_release.ingress]
}
~~~


### Terraform Variables

Hemos proporcionado algunas variables que podemos modificar fácilmente para cambiar el nombre del project_id o la región donde se desplegará el clúster. Para eso podemos modificar las variables en el fihcero `terraform.tfvars`:
~~~properties
project_id = "alexa-k8s"
region     = "us-central1"
~~~

Para crear un proyecto de Google Cloud usando la cli de `gcloud` y configurar este proyecto como el proyecto predeterminado, necesitamos ejecutar los siguientes comandos:
~~~bash
gcloud init
gcloud projects create alexa-k8s
gcloud auth application-default login
gcloud config set project alexa-k8s
gcloud config get-value project
~~~


## Desplegando el Stack

Para que un provider esté disponible en Terraform, necesitamos ejecutar `terraform init`, estos comandos descargan cualquier complemento que necesitemos para nuestros providers.
Después de eso, tenemos que ejecutar `terraform plan`. El comando terraform plan se utiliza para crear un plan de ejecución.
No modificará las cosas en la infraestructura.
Terraform realiza una actualización, a menos que esté explícitamente deshabilitado, y luego determina qué acciones son necesarias para lograr el estado deseado especificado en los archivos de configuración.
Este comando es una forma conveniente de verificar si el plan de ejecución para un conjunto de cambios coincide con nuestras expectativas sin realizar ningún cambio en los recursos reales o en el estado.
Finalmente, necesitamos ejecutar `terraform apply`. El comando terraform apply se utiliza para aplicar los cambios necesarios para alcanzar el estado deseado de la configuración.
Terraform apply también escribirá datos en el archivo terraform.tfstate.
Una vez que se completa la ejecución, los recursos están disponibles de inmediato.

Aquí tienes la lista de comandos completa:
~~~bash
terraform init
terraform plan
terraform appyly
~~~

Después de ejecutar el `terraform apply`, podemos echar un vistazo a Google kubernetes Engine para ver que nuestro clúster ahora aparece:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/gke/cluster-creating.png){:.lead data-width="800" data-height="100"}
Cluster creandose
  {:.figure}

Necesitamos esperar como 10 minutos hasta que se cree el clúster. Una vez creado el clúster, ahora podemos ver el cluster completo:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/gke/cluster-created.png){:.lead data-width="800" data-height="100"}
Cluster creado
  {:.figure}

Después de la creación del clúster, Terraform desplegará todos los gráficos de Helm. Aquí podemos ver todos los pods de Kubernetes desplegados:
  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/gke/gks-pods.png){:.lead data-width="800" data-height="100"}
Pods
  {:.figure}

Y aquí los Servicios de Kubernetes y la IP externa del `nginx-ingress-controller`. Esa IP es la que vamos a utilizar para realizar peticiones típicas de Alexa:
  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/gke/gks-service-ingress.png){:.lead data-width="800" data-height="100"}
Services y Ingress
  {:.figure}

## Probando peticiones

Seguro que ya conoceis la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios web. Aunque REST se ha vuelto omnipresente, no siempre es fácil de probar. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir API, lo que nos ayudará a nosotros y a nuestro equipo a ser más productivos a largo plazo.

Después de ejecutar nuestra aplicación, tendremos un endpoint disponible en http://35.193.101.213. Con Postman podemos emular cualquier solicitud de Alexa.

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


And here the Kubernetes Services and the external IP of the `nginx-ingress-controller`. That IP is the one we are going to use to make Alexa requests:
  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/gke/gks-request.png){:.lead data-width="800" data-height="100"}
Petición a GKE
  {:.figure}

## Destruir el Stack

Si queremos eliminar toda el stack creado por Terraform, simplemente tenemos que ejecutar:
~~~bash
terraform destroy
~~~

## Recursos
* [Official Alexa Skills Kit Node.js SDK](https://www.npmjs.com/package/ask-sdk) - The Official Node.js SDK Documentation
* [Official Alexa Skills Kit Documentation](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - Official Alexa Skills Kit Documentation
* [Official Express Adapter Documentation](https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit-sdk-for-nodejs/host-web-service.html) - Express Adapter Documentation
* [Official Kind Documentation](https://kind.sigs.k8s.io/) - Kind Documentation
* [Official Kubernetes Documentation](https://kubernetes.io/docs) - Kubernetes Documentation
* [Terraform GKE](https://learn.hashicorp.com/tutorials/terraform/gke) - Terraform GKE
* [Terraform GKE Official](https://github.com/hashicorp/learn-terraform-provision-gke-cluster) - Terraform Official
* [Terraform GKE Github](https://github.com/GoogleCloudPlatform/terraform-google-examples/tree/master/example-gke-k8s-helm) - Terraform GKE GitHub
  
## Conclusión 

Ahora tenemos nuestra Skill de Alexa ejecutándose en un clúster de Kubernetes de nuestro proveedor en la nube, todo automatizado con Terraform y listo para usar en nuestras Skill de Alexa.

Espero que este proyecto de ejemplo os sea de utilidad.

Puede encontrar el código [aquí](https://github.com/xavidop/alexa-nodejs-k8s-helloworld)

¡Eso es todo amigos!

Happy coding!