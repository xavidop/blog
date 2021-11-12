---
layout: post
title: Alexa and Kubernetes. Desplegando una Alexa Skill en AWS Elastic Kubernetes Services (VII)
image: /assets/img/blog/post-headers/alexa-eks.jpg
description: >
   Despliegue automático Alexa Skill en EKS con Terraform
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


Ahora tenemos todo preparado y listo para pasar a un clúster de Kubernetes en un proveedor cloud. Es un hecho que crear un clúster en cualquier proveedor cloud de forma manual es una tarea difícil. Además, si queremos automatizar estos despliegues, necesitamos algo que nos ayude en esta tediosa tarea. En esta publicación veremos cómo crear un clúster de Kubernetes y todos sus objetos requeridos y cómo implementar nuestra Skill de Alexa con Terraform usando [Elastic Kubernetes Service](https://aws.amazon.com/eks/)

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/eks/eks.jpg){:.lead data-width="800" data-height="100"}
Elastic Kubernetes Service
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
10. AWS Account
11. AWS CLI
12. AWS IAM Authenticator CLI

## Terraform

Terraform es una herramienta para construir, cambiar y crear versiones de infraestructuras cloud de manera segura y eficiente. Terraform puede gestionar proveedores de servicios existentes y populares, así como soluciones internas personalizadas.

Los archivos de configuración le indican a Terraform los componentes necesarios para ejecutar una sola aplicación. Terraform genera un plan de ejecución que describe lo que hará para alcanzar el estado deseado y luego lo ejecuta para construir la infraestructura descrita. A medida que cambia la configuración, Terraform puede determinar qué cambió y crear planes de ejecución incrementales que se pueden ir aplicando.

La infraestructura que Terraform puede administrar incluye componentes de bajo nivel como instancias de computación, almacenamiento y redes, así como componentes de alto nivel como entradas de DNS, características de SaaS, etc.

## Ficheros Terraform

Después de la breve descripción general de Terraform, vamos a explicar todos los archivos de terraform y sus objetos que vamos a utilizar para desplegar el clúster y nuestra Skill de Alexa.
Podemos encontrar todos los archivos relacionados con este despliegue en la carpeta `terraform/eks`.

### Terraform Providers

Un provider es el responsable de comprender las interacciones de la API y exponer los resources.
La mayoría de los providers disponibles corresponden a una plataforma de infraestructura cloud o local y ofrecen tipos de resources que corresponden a cada una de las características de esa plataforma.

Para el Elastic Kubernetes Service, usaremos el provider `aws`. Este provider nos permite crear todos los objetos de AWS que necesitamos para crear nuestro Stack para la Skill de Alexa:

~~~hcl
provider "aws" {
  region = "eu-central-1"
}
~~~

Como vamos a desplegar Helm Charts, se requerirá tener el provider `helm`:
~~~hcl
provider "helm" {
  kubernetes {
    host                   = data.aws_eks_cluster.cluster.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority.0.data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}
~~~

Como vamos a interactuar con el clúster, será útil tener el provider `kubernetes`:
~~~hcl
provider "kubernetes" {
  host                   = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority.0.data)
  token                  = data.aws_eks_cluster_auth.cluster.token
  load_config_file       = false
}
~~~

### Terraform Modules y Resources

Uno de los resources más importantes de un clúster EKS son las redes. Por eso, tenemos que crear nuestra Red y Subredes usando Virtual Private Cloud. Para eso, necesitamos usar el módulo `vpc` :
~~~hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "2.64.0"

  name                 = "k8s-vpc"
  cidr                 = "172.16.0.0/16"
  azs                  = data.aws_availability_zones.available.names
  private_subnets      = ["172.16.1.0/24", "172.16.2.0/24", "172.16.3.0/24"]
  public_subnets       = ["172.16.4.0/24", "172.16.5.0/24", "172.16.6.0/24"]
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  public_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                      = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"             = "1"
  }
}
~~~

Una vez que se ha creado la VPC, podemos crear el clúster que utilizará esa VPC. Para eso, necesitamos usar el módulo `eks`:
~~~hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "13.2.1"

  cluster_name    = local.cluster_name
  cluster_version = "1.18"
  subnets         = module.vpc.private_subnets
  wait_for_cluster_cmd          = "until curl -k -s $ENDPOINT/healthz >/dev/null; do sleep 4; done"
  wait_for_cluster_interpreter = ["C:/Program Files/Git/bin/sh.exe", "-c"]

  vpc_id = module.vpc.vpc_id

  node_groups = {
    first = {
      desired_capacity = 2
      max_capacity     = 10
      min_capacity     = 2

      instance_type = "m5.large"
    }
  }

  write_kubeconfig   = true
  config_output_path = "./"

  workers_additional_policies = [aws_iam_policy.worker_policy.arn]
}
~~~

Además, crearemos algunas políticas de IAM de AWS específicas para nuestros nodos del clúster de Kubernetes para poder acceder a ellos desde Internet. Para eso usaremos el resources `aws_iam_policy`:
~~~hcl
resource "aws_iam_policy" "worker_policy" {
  name        = "worker-policy"
  description = "Worker policy for the ALB Ingress"

  policy = file("iam-policy.json")
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

Hemos proporcionado algunas variables que podemos modificar fácilmente para cambiar el nombre del clúster o la región donde se desplegará el clúster. Para eso puedes modificar las variables locales en el fichero `main.tf`:
~~~hcl
locals {
  cluster_name = "alexa-cluster"
  region       = "eu-central-1"
}
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

Después de ejecutar el comando `terraform apply`, podemos echar un vistazo a Elastic Kubernetes Service para ver que nuestro clúster ahora aparece:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/eks/cluster-creating.png){:.lead data-width="800" data-height="100"}
Cluster creandose
  {:.figure}

Necesitamos esperar como 10 minutos hasta que se cree el clúster. Una vez creado el clúster, ahora podemos ver el cluster completo:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/eks/cluster-created.png){:.lead data-width="800" data-height="100"}
Cluster Creado
  {:.figure}


Después de la creación del clúster, Terraform desplegará todos los gráficos de Helm. Aquí podemos ver todos los pods de Kubernetes desplegados:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/eks/eks-pods.png){:.lead data-width="800" data-height="100"}
Pods
  {:.figure}

Y aquí los Servicios de Kubernetes y la IP externa del `nginx-ingress-controller`. Esa IP es la que vamos a utilizar para realizar peticiones típicas de Alexa:

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/eks/eks-service-ingress.png){:.lead data-width="800" data-height="100"}
Services y Ingress
  {:.figure}

## Probando peticiones

Seguro que ya conoceis la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios web. Aunque REST se ha vuelto omnipresente, no siempre es fácil de probar. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir API, lo que nos ayudará a nosotros y a nuestro equipo a ser más productivos a largo plazo.

Después de ejecutar nuestra aplicación, tendremos un endpoint disponible en http://a6ae89bc3ff9745de8bd095000264ff6-1697202105.eu-central-1.elb.amazonaws.com. Con Postman podemos emular cualquier solicitud de Alexa.

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

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/eks/eks-request.png){:.lead data-width="800" data-height="100"}
Petición a EKS
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
* [Terraform EKS](https://learnk8s.io/terraform-eks) - Terraform EKS
* [Terraform EKS Github](https://github.com/k-mitevski/terraform-k8s/tree/master/04_terraform_helm_provider) - Terraform EKS GitHub
  
## Conclusión 

Ahora tenemos nuestra Skill de Alexa ejecutándose en un clúster de Kubernetes de nuestro proveedor en la nube, todo automatizado con Terraform y listo para usar en nuestras Skill de Alexa.

Espero que este proyecto de ejemplo os sea de utilidad.

Puede encontrar el código [aquí](https://github.com/xavidop/alexa-nodejs-k8s-helloworld)

¡Eso es todo amigos!

Happy coding!
