---
layout: post
title: Alexa Skill con .NET Core
image: /assets/img/blog/post-headers/alexa-dotnet.jpg
description: >
  Alexa Skill desarrollada en .NET Core usando Visual Studio
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - dotnet
  - dotnetcore
  - lambda
  - csharp
  - howto
  - skill
lang: es
---

Las Skills de Alexa se pueden desarrollar utilizando las Lambda functions de AWS o usando un servidor REST.
Lambda function es la implementación de Amazon de funciones serverless disponibles en AWS.
Amazon recomienda usar las Lambda functions a pesar de que no sean fáciles de debuggear.
Si bien puedes loggear en CloudWatch, no puedes poner un breakpoint y revisor el código.
 
# Alexa Skill con .NET Core

Esto hace que debuggear una request que nos envía Alexa sea un completo desafío.
Este post explica una solución simple pero útil: levantar un proyecto Web API para debug local y un proyecto de función Lambda para luego poder desplegar en AWS. 
Ambos proyectos ejecutarán el mismo código escrito en C#.

## Estructurando la solución
 
Este enfoque requiere un mínimo de dos proyectos en la solución:
1. Lambda function project (.NET Core 2.1)
2. Web API project (.NET Core 2.1)

### Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto.
1. .NET Core 2.1
2. Visual Studio Community 2019
3. Nugget Package Manager
4. Alexa .NET (Version 1.13.0)
5. ngrok

Este artículo asume familiaridad con la creación de Lambda functions. 
El [AWS Toolkit para Visual Studio](https://aws.amazon.com/visualstudio/) incluye proyectos para poder crear Lambda functions usando .NET Core. 
Toda lógica significativa debe estar contenida dentro de la carpeta `BusinessLogic` y ser referenciada por el proyecto Lambda y el proyecto Web API.
Tanto el proyecto Lambda como el proyecto de Web API deben ser wrappers de la lógica de negocio de nuestra Skill.

Cómo instalar las `Amazon.Lambda.Tools` de manera global si aún no están instaladas:
```bsh
    dotnet tool install -g Amazon.Lambda.Tools
```

Si ya están instaladas, verifica si hay una nueva versión disponible.
```bash
    dotnet tool update -g Amazon.Lambda.Tools
```

### Archivos del proyecto

Estos son los archivos principales del proyecto:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dotnet/structure.png){:.lead data-width="800" data-height="100"}
Estructura
  {:.figure}

* serverless.template - template de AWS CloudFormation, concretamente basado en Serverless Application Model, usado para declarar tu función serverless y otros AWS resources
* aws-lambda-tools-defaults.json -  configuración por defecto para ser usada por el Visual Studio y la Command Line Deployment Tool de AWS
* Function.cs - clase que deriva de **Amazon.Lambda.AspNetCoreServer.APIGatewayProxyFunction**. El código de esta clase arranca el ASP.NET Core hosting framework. La función Lambda se define en la clase base
* LocalEntryPoint.cs - para el desarrollo local. Contiene el método ejecutable `Main` que arranca el ASP.NET Core hosting framework con Kestrel, igual que en las aplicaciones típicas de ASP.NET Core
* Startup.cs - clase habitual de inicio de ASP.NET Core utilizada para configurar los servicios que utilizará ASP.NET Core
* web.config - utilizado para el desarrollo local
* Controllers\AlexaController.cs - controlador API REST que recibirá todas las requests desde el cloud de Alexa. Este controlador nos permite debuggear nuestra Skill también localmente
* BsuinessLogic\AlexaProcessor.cs - el código que procesará todas las requests de Alexa recibidas desde la función Lambda en la clase Function.cs y del POST controller en la clase AlexaController.cs

Una vez que se ha explicado la estructura, es hora de comprender cómo funciona todo el proyecto:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dotnet/works.png){:.lead data-width="800" data-height="100"}
Cómo funciona
  {:.figure}


### Alexa Request Processor 

Alexa.NET es una librería auxiliar para trabajar con requests/responses de Skills de Alexa en C#.
Bien utilices el servicio AWS Lambda o alojes tu Skill en un servidor, esta librería tiene como objetivo hacer que trabajar con la API de Alexa sea más natural para un desarrollador de C# que utiliza un modelo de objetos fuertemente tipado.

Puedes encontrar toda la documentación en su repositorio [GitHub](https://github.com/timheuer/alexa-skills-dotnet) oficial.

A continuación, tienes la clase `AlexaRequestProcessor.cs` que ejecutará todas las requests de Alexa utilizando el paquete Nugget Alexa.NET y muestra lo fácil que es desarrollar este tipo de aplicaciones de voz en .NET core:

```csharp
    public class AlexaRequestProcessor
    {
        public SkillResponse Process(SkillRequest input)
        {

            Session session = input.Session;
            if (session.Attributes == null)
                session.Attributes = new Dictionary<string, object>();

            Type requestType = input.GetRequestType();
            if (input.GetRequestType() == typeof(LaunchRequest))
            {
                string speech = "Welcome! Hello world!";
                Reprompt rp = new Reprompt("You can Say hello or help");
                return ResponseBuilder.Ask(speech, rp, session);
            }
            else if (input.GetRequestType() == typeof(SessionEndedRequest))
            {
                return ResponseBuilder.Tell("Goodbye!");
            }
            else if (input.GetRequestType() == typeof(IntentRequest))
            {
                var intentRequest = (IntentRequest)input.Request;
                switch (intentRequest.Intent.Name)
                {
                    case "AMAZON.CancelIntent":
                    case "AMAZON.StopIntent":
                        return ResponseBuilder.Tell("Goodbye!");
                    case "AMAZON.HelpIntent":
                        {
                            Reprompt rp = new Reprompt("What's next?");
                            return ResponseBuilder.Ask("Here's some help. What's next?", rp, session);
                        }
                    case "HelloWorldIntent":
                        {
                            string helloWorld = "HelloWorld";
                            Reprompt rp = new Reprompt(helloWorld);
                            return ResponseBuilder.Ask(helloWorld, rp, session);
                        }
                    default:
                        {
                            string speech = "I didn't understand - try again?";
                            Reprompt rp = new Reprompt(speech);
                            return ResponseBuilder.Ask(speech, rp, session);
                        }
                }
            }
            return ResponseBuilder.Tell("Goodbye!");
        }
    }

```


## Compila la Skill con Visual Studio

Visual Studio ofrece una gran cantidad de funcionalidades integradas. Si quieres construir la solución completa dentro del IDE, puedes hacerlo de manera interactiva:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dotnet/build.png){:.lead data-width="800" data-height="100"}
Hacer el build del proyecto
  {:.figure}

## Ejecuta la Skill con Visual Studio

Ejecutar Alexa Skill es tan fácil como hacer click en el botón de Play en Visual Studio. Usando la configuración `alexa_dotnet_lambda_helloworld`:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dotnet/run.png){:.lead data-width="800" data-height="100"}
Ejecutar el proyecto
  {:.figure}

Después de ejecutarlo, puedes enviar requests POST de Alexa a http://localhost:5000/api/alexa.

Esta ejecución lanzará el proyecto Web API. Si quieres ejecutar la función Lambda, debes ejecutar la configuración `Mock Lambda Test Tool`:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dotnet/run-lambda.png){:.lead data-width="800" data-height="100"}
Ejecutar la lambda
  {:.figure}

Esta ejecución lanzará un navegador con la **Mock Lambda Test Tool** y podrás ejecutar allí todas las requests directamente hacia la clase Function.cs, enpoint de la función Lambda:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dotnet/lambda-tool.png){:.lead data-width="800" data-height="100"}
Mock Lambda Test Tool
  {:.figure}

## Debuggear la Skill con Visual Studio

Siguiendo los pasos anteriores, ahora puedes configurar breakpoints donde lo desees dentro de todos los ficheros C# para debuggear tu Skill:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dotnet/debug.png){:.lead data-width="800" data-height="100"}
Debuggear el proyecto
  {:.figure}

## Testear requests localmente

Estoy seguro de que ya conoces la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios. Aunque REST se ha vuelto omnipresente, no siempre es fácil probarlo. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir APIs, lo que te ayudará a ti y a tu equipo a ser más productivos a largo plazo.

Después de ejecutar tu aplicación, tendrás un endpoint disponible en http://localhost:5000/api/alexa. Con Postman puedes emular cualquier request de Alexa.

Por ejemplo, puedes testear un `LaunchRequest`:

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
      "timestamp": "2020-03-22T17:24:44Z",
      "locale": "en-US"
    }
  }
```

También puedes ejecutar pruebas unitarias:
```bash
    cd "alexa_dotnet_lambda_helloworld/test/alexa_dotnet_lambda_helloworld.Tests"
    dotnet test
```

## Desplegar tu Alexa Skill

Puedes hacerlo directamente desde Visual Studio o desde la CLI:

### Pasos a seguir desde Visual Studio:

Para desplegar la Skill, haz click con el botón derecho en el proyecto dentro del explorador de soluciones y selecciona *Publish to AWS Lambda*.

Para ver tus Lambda desplegadas, abre la ventana *Stack View* haciendo doble click en el nombre del stack que se muestra debajo del nodo de AWS CloudFormation en el *AWS Explorer*. La *Stack View* muestra también la URL de tus Lambda publicadas.

  ![Full-width image](/assets/img/blog/tutorials/alexa-dotnet/deploy.png){:.lead data-width="800" data-height="100"}
Desplegar la lambda en AWS
  {:.figure}

### Pasos a seguir desde la CLI:

Una vez hayas editado el template y el código, puedes desplegar la aplicación utilizando las [Amazon.Lambda.Tools](https://github.com/aws/aws-extensions-for-dotnet-cli#aws-lambda-amazonlambdatools) desde la command line.

Desplegar la aplicación:
```bash
    cd "alexa_dotnet_lambda_helloworld/src/alexa_dotnet_lambda_helloworld"
    dotnet lambda deploy-serverless
```
## Testear requests directamente desde Alexa

ngrok es una herramienta genial y liviana que crea un túnel seguro en tu máquina local junto con una URL pública que se puede usar para navegar por tu web en local o API.

Cuando se está ejecutando ngrok, escucha en el mismo puerto en el que se está ejecutando el servidor web local y envía solicitudes externas a tu máquina local.

Veamos como de fácil es publicar nuestra Skill ejecutandose en local para que el cloud de Alexa nos envíe requests. 
Digamos que está ejecutando tu servidor web local en el puerto 5000. En la terminal, escribiría: `ngrok http 5000`. Esto comienza a escuchar a ngrok en el puerto 5000 y crea el túnel seguro:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dotnet/tunnel.png){:.lead data-width="800" data-height="100"}
Túnel
  {:.figure}


Entonces ahora vas a la [Alexa Developer console](https://developer.amazon.com/alexa/console/ask), navegar a tu Skill > endpoints > https, agregas la URL https generada anteriormente seguido de /api/alexa. Por ejemplo: https://4525b7af.ngrok.io/api/alexa.

Selecciona la opción "My development endpoint is a sub-domain...." desde el menú desplegable y haga clikc en Save endpoint en la parte superior de la página.

Dirígete al tab Test en la Alexa Developer Console y lanza tu skill.

La Alexa Developer Console enviará una solicitud HTTPS al endpoint ngrok (https://4525b7af.ngrok.io/api/alexa) que lo redirigirá a tu Skill ejecutándose en el servidor Web en http://localhost:5000/api/alexa.

## Conclusión 

Este ejemplo puede ser útil para todos aquellos desarrolladores que no quieran escribir su código en Java, NodeJS o Pyhton, que son los lenguajes oficialmente compatibles con Alexa.
Tenemos que tener en cuenta que el Paquete Nugget de Alexa.NET no es un Alexa Skill Kit(ASK) oficial.
Esto implica que puedes encontrar bugs o funcionalidades que no están disponibles a pesar de que esta librería está en constante cambio.
Te recomiendo acceder a su repositorio [GitHub](https://github.com/timheuer/alexa-skills-dotnet) oficial para verificar el estado del proyecto, bugs, actualizaciones, etc.
Como has visto en este ejemplo, la comunidad de desarrolladores de Alexa te brinda la posibilidad de crear Skills de diferentes maneras. 

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-dotnet-lambda-helloworld)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
