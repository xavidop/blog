---
layout: post
title: Alexa and Kubernetes. Deploying the Alexa Skill on Azure Kubernetes Services (VIII)
image: /assets/img/blog/post-headers/alexa-aks.jpg
description: >
   Despliegue automático Alexa Skill en AKS con Terraform
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

Ahora tenemos todo preparado y listo para pasar a un clúster de Kubernetes en un proveedor cloud. Es un hecho que crear un clúster en cualquier proveedor cloud de forma manual es una tarea difícil. Además, si queremos automatizar estos despliegues, necesitamos algo que nos ayude en esta tediosa tarea. En esta publicación veremos cómo crear un clúster de Kubernetes y todos sus objetos requeridos y cómo implementar nuestra Skill de Alexa con Terraform usando  [Azure Kubernetes Services](https://azure.microsoft.com/en-us/services/kubernetes-service/)

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/aks/azure.png){:.lead data-width="800" data-height="100"}
Azure Kubernetes Service
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
10. Azure Account
11. Azure CLI

## Terraform

Terraform es una herramienta para construir, cambiar y crear versiones de infraestructuras cloud de manera segura y eficiente. Terraform puede gestionar proveedores de servicios existentes y populares, así como soluciones internas personalizadas.

Los archivos de configuración le indican a Terraform los componentes necesarios para ejecutar una sola aplicación. Terraform genera un plan de ejecución que describe lo que hará para alcanzar el estado deseado y luego lo ejecuta para construir la infraestructura descrita. A medida que cambia la configuración, Terraform puede determinar qué cambió y crear planes de ejecución incrementales que se pueden ir aplicando.

La infraestructura que Terraform puede administrar incluye componentes de bajo nivel como instancias de computación, almacenamiento y redes, así como componentes de alto nivel como entradas de DNS, características de SaaS, etc.

## Ficheros Terraform

Después de la breve descripción general de Terraform, vamos a explicar todos los archivos de terraform y sus objetos que vamos a utilizar para desplegar el clúster y nuestra Skill de Alexa.
Podemos encontrar todos los archivos relacionados con este despliegue en la carpeta `terraform/aks`.

### Terraform Providers

Un provider es el responsable de comprender las interacciones de la API y exponer los resources.
La mayoría de los providers disponibles corresponden a una plataforma de infraestructura cloud o local y ofrecen tipos de resources que corresponden a cada una de las características de esa plataforma.

Para el Azure Kubernetes Service, usaremos el provider `azurerm`. Este provider nos permite crear todos los objetos de Azure que necesitamos para crear nuestro Stack para la Skill de Alexa:

~~~hcl
provider "azurerm" {
  features {}
}
~~~

Como vamos a desplegar Helm Charts, se requerirá tener el provider `helm`:
~~~hcl
provider "helm" {
  kubernetes {
    host = azurerm_kubernetes_cluster.cluster.kube_config[0].host
    
    client_key             = base64decode(azurerm_kubernetes_cluster.cluster.kube_config[0].client_key)
    client_certificate     = base64decode(azurerm_kubernetes_cluster.cluster.kube_config[0].client_certificate)
    cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.cluster.kube_config[0].cluster_ca_certificate)
  }
}

~~~



### Terraform Resources

Una vez que se ha creado la VPC, podemos crear el clúster que utilizará esa VPC. Para eso, necesitamos usar el módulo `azurerm_resource_group`:
~~~hcl
resource "azurerm_resource_group" "rg" {
  name     = "aks-cluster"
  location = "uksouth"
}
~~~

Una vez que se ha creado el Resource Group, podemos crear el clúster que utilizará ese RG. Para eso, necesitamos usar el módulo `azurerm_kubernetes_cluster`:
~~~hcl
resource "azurerm_kubernetes_cluster" "cluster" {
  name       = "aks"
  location   = azurerm_resource_group.rg.location
  dns_prefix = "aks"

  resource_group_name = azurerm_resource_group.rg.name
  kubernetes_version  = "1.18.10"

  default_node_pool {
    name       = "aks"
    node_count = "1"
    vm_size    = "Standard_D2s_v3"
  }

  service_principal {
    client_id     = var.appId
    client_secret = var.password
  }

  addon_profile {
    kube_dashboard {
      enabled = true
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

Hemos proporcionado algunas variables que podemos modificar fácilmente para cambiar el nombre del app_id o la contraseña de esta aplicación de Azure. Para eso podemos modificar las variables en el fichero `terraform.tfvars`:
~~~properties
appId    = "your-appid"
password = "your-password"
~~~

Para crear una Azure Service Principal mediante la cli `az` y obtener la contraseña para esa entidad de servicio. Terraform necesita un Service Principal para crear resources en nuestro nombre.
Podemos considerarlo como una identidad de usuario (nombre de usuario y contraseña) con un rol específico y permisos estrictamente controlados para acceder a nuestros resources.
Podriamos tener permisos detallados, como solo para crear máquinas virtuales o leer desde un almacenamiento en particular.

Para eso, necesitamos ejecutar los siguientes comandos:
~~~bash
az login
az account list
az ad sp create-for-rbac --role="Contributor"  --scopes="/subscriptions/YOUR_ID"
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

Después de ejecutar el `terraform apply`, podemos echar un vistazo a Azure Kubernetes Service para ver que nuestro clúster ahora aparece:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/aks/cluster-list.png){:.lead data-width="800" data-height="100"}
Lista de clusters en AKS
  {:.figure}

Necesitamos esperar como 10 minutos hasta que se cree el clúster. Una vez creado el clúster, ahora podemos ver el cluster completo:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/aks/cluster-created.png){:.lead data-width="800" data-height="100"}
Cluster creado
  {:.figure}

Después de la creación del clúster, Terraform desplegará todos los gráficos de Helm. Aquí podemos ver todos los pods de Kubernetes desplegados:
  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/aks/aks-pods.png){:.lead data-width="800" data-height="100"}
Pods
  {:.figure}

Y aquí los Servicios de Kubernetes y la IP externa del `nginx-ingress-controller`. Esa IP es la que vamos a utilizar para realizar peticiones típicas de Alexa:
  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/aks/aks-services-ingress.png){:.lead data-width="800" data-height="100"}
Services y Ingress
  {:.figure}


## Probando peticiones

Seguro que ya conoceis la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios web. Aunque REST se ha vuelto omnipresente, no siempre es fácil de probar. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir API, lo que nos ayudará a nosotros y a nuestro equipo a ser más productivos a largo plazo.

Después de ejecutar nuestra aplicación, tendremos un endpoint disponible en  http://51.143.242.234. Con Postman podemos emular cualquier solicitud de Alexa.

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

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/aks/aks-request.png){:.lead data-width="800" data-height="100"}
Petición a AKS
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
* [Terraform AKS](https://learnk8s.io/blog/get-start-terraform-aks) - Terraform AKS
* [Terraform AKS Github](https://github.com/learnk8s/terraform-aks/tree/master/03-aks-helm) - Terraform AKS GitHub
  
## Conclusión 

Ahora tenemos nuestra Skill de Alexa ejecutándose en un clúster de Kubernetes de nuestro proveedor en la nube, todo automatizado con Terraform y listo para usar en nuestras Skill de Alexa.

Espero que este proyecto de ejemplo os sea de utilidad.

Puede encontrar el código [aquí](https://github.com/xavidop/alexa-nodejs-k8s-helloworld)

¡Eso es todo amigos!

Happy coding!