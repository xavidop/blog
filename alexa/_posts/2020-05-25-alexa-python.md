---
layout: post
title: Alexa Skill con Python
image: /assets/img/blog/post-headers/alexa-python.jpg
description: >
   Alexa Skill desarrollada en Python usando Visual Studio Code
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - lambda
  - python
  - python3
  - howto
  - skill
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

Las Skills de Alexa se pueden desarrollar utilizando las funciones Lambda de AWS o un endpoint en una REST API.
La función Lambda es la implementación de Amazon de funciones serverless disponibles en AWS.
Amazon recomienda utilizar las funciones Lambda aunque no sean fáciles de debuggear y trackear.
Si bien puedes loggear en CloudWatch, no puedes poner puntos de ruptura una vez desplegada la Lambda e ir directamente al código. 

# Alexa Skill con Python
 
Esto hace que el live debugging de las requests enviadas a Alexa sea una tarea muy difícil.
En este post, implementaremos una custom Skill para Amazon Alexa usando Python, npm y AWS Lambda Functions.
Esta Skill es básicamente un ejemplo de Hello World. 
Con este post, podras crear una custom Skill para Amazon Alexa, implementar la funcionalidad utilizando Python y ejecutar tu Skill tanto desde tu ordenador local como desde AWS.
Esta publicación contiene materiales de diferentes recursos que se pueden ver en la sección Recursos.


## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. Python 3.x
5. Visual Studio Code
6. pip Package Manager
7. Alexa ASK for Python (Version >1.10.2)
8. ngrok

La Alexa Skills Kit Command Line Interface (ASK CLI) es una herramienta para que puedas administrar tus Skills de Alexa y recursos relacionados, como las funciones de AWS Lambda.
Con la ASK CLI, tienes acceso a la Skill Management API, que te permite administrar las Skills de Alexa mediante programación desde la línea de comandos.
Utilizaremos esta poderosa herramienta para crear, construir, desplegar y gestionar nuestra Skill Hello World. 

¡Empecemos!

## Creando la Skill con ASK CLI

Para crear la Alexa Skill, vamos a usar la ASK CLI previamente configurada. Primero de todo, debemos ejecutar este comando:

```bash

    ask new

```
Este comando se ejecutará un proceso interactivo de creación paso a paso:

1. Lo primero que nos preguntará la ASK CLI es el runtime de nuestra Skill. En nuestro caso, `Python3`:

  ![Full-width image](/assets/img/blog/tutorials/alexa-python/runtime.png){:.lead data-width="800" data-height="100"}
Runtime
  {:.figure}

1. El segundo paso es el template de la Skill en la que se basará la nuestra.En nuestro caso, seleccionaremos el template `Hello World (Using Classes)`:

  ![Full-width image](/assets/img/blog/tutorials/alexa-python/template.png){:.lead data-width="800" data-height="100"}
Template
  {:.figure}

3. Finalmente, ASK CLI nos preguntará sobre el nombre de la Skill: `alexa-python-lambda-helloworld`


## Estructura del proyecto 

Estos son los archivos principales del proyecto:

```bash

    ├───.ask
    │       config
    │
    ├───.vscode
    │       launch.json
    │       tasks.json
    ├───hooks
    ├───lambda
    │   └───py
    │         ├───errors
    │         ├───intents
    │         ├───interceptors
    │         ├───locales
    │         ├─── hello_world.py
    │         └─── requirements.txt
    ├───models
    │       es-ES.json
    ├───skill.json
    └───local_debugger.py


```

* .ask: carpeta que contiene el archivo de configuración de ASK CLI. Este archivo de configuración permanecerá vacío hasta que ejecutemos el comando `ask deploy`
* `.vscode/launch.json`: Preferencias de ejecución para ejecutar localmente tu Skill para testing local y ejecuta tambien las tareas definidas en `.vscode/tasks.json`. Esta configuración ejecuta `lambda/custom/local-debugger.js`. Este script ejecuta un servidor en http://localhost:3001 para debuggear la Skill.
* hooks: Una carpeta que contiene los hooks scripts. Amazon proporciona dos hooks, post_new_hook y pre_deploy_hook.
  * `post_new_hook`: ejecutado después de la creación de la Skill. En Python crea un Virtual Environment en la carpeta `.venv/skill_env`.
  * `pre_deploy_hook`:ejecutado antes del despliegue de la Skill. En python crea la carpeta `lambda/py/lambda_upload`donde se almacenará todo lo necesario para cargar el lambda a AWS.
* lambda/py: Una carpeta que contiene el código fuente de la función AWS Lambda de la Skill:
  * `hello_world.py`: El principal entry point de la función Lambda.
  * `locales`: diccionarios i18n usados por la librería `python-i18n` que nos permite ejecutar nuestra Skill en diferentes lenguajes.
  * `requirementes.txt`: tEste archivo almacena las dependencias de Python de nuestro proyecto y es una parte básica de la comprensión y el trabajo con Python y Pip.
  * `errors`: carpeta que contiene todos error handlers
  * `intents`: este contiene todos los intent handlers
  * `interceptors`: carpeta de interceptores con la inicialización del i18n
* models: Una carpeta que contiene los interactions models para nuestra Skill. Cada interaction model se define en un archivo JSON nombrado de acuerdo con la configuración regional. Por ejemplo, es-ES.json.
* `skill.json`: El skill manifest. Uno de los archivos más importantes de nuestro proyecto.
* `local_debugger.py`: usado para el debug local de nuestra skill.


## Lambda function en Python

El SDK de ASK para Python te facilita el desarrollo de Skills de gran calidad al permitirte pasar más tiempo implementando funciones y menos tiempo escribiendo código repetitivo.

Puede encontrar documentación, ejemplos y enlaces útiles en su repositorio oficial de [GitHub](https://github.com/alexa/alexa-skills-kit-sdk-for-python)

El archivo Python principal en nuestro proyecto lambda es`hello_world.py` situado en la capreta `lambda/py`. TEste fichero contiene todos los handlers, interceptors y exporta el Skill handler en el objeto `handler`.

La función `handler` se ejecuta cada vez que AWS Lambda es invocado por el cloud de Alexa.
En teoría, una función AWS Lambda es solo una función única. Esto significa que necesitamos definir la lógica para que una request a la función pueda enrutarse al código apropiado, de ahí los handlers.
```python

  from ask_sdk_core.skill_builder import SkillBuilder
  from ask_sdk_model import Response
  from intents import LaunchRequestHandler as launch
  from intents import HelloWorldIntentHandler as hello
  from intents import HelpIntentHandler as help
  from intents import CancelOrStopIntentHandler as cancel
  from intents import SessionEndedRequestHandler as session
  from intents import IntentReflectorHandler as reflector
  from errors import CatchAllExceptionHandler as errors
  from interceptors import LocalizationInterceptor as locale

  # The SkillBuilder object acts as the entry point for your skill, routing all request and response
  # payloads to the handlers above. Make sure any new handlers or interceptors you've
  # defined are included below. The order matters - they're processed top to bottom.
  sb = SkillBuilder()

  sb.add_request_handler(launch.LaunchRequestHandler())
  sb.add_request_handler(hello.HelloWorldIntentHandler())
  sb.add_request_handler(help.HelpIntentHandler())
  sb.add_request_handler(cancel.CancelOrStopIntentHandler())
  sb.add_request_handler(session.SessionEndedRequestHandler())
  # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
  sb.add_request_handler(reflector.IntentReflectorHandler())

  sb.add_global_request_interceptor(locale.LocalizationInterceptor())

  sb.add_exception_handler(errors.CatchAllExceptionHandler())

  handler = sb.lambda_handler()

```
Es importante echar un vistazo al `LaunchRequestHandler` como un ejemplo de handler de Skills de Alexa escrito en Python:

```python

  class LaunchRequestHandler(AbstractRequestHandler):
      """Handler for Skill Launch."""

      def can_handle(self, handler_input):
          # type: (HandlerInput) -> bool

          return ask_utils.is_request_type("LaunchRequest")(handler_input)

      def handle(self, handler_input):
          # type: (HandlerInput) -> Response
          speak_output = i18n.t("strings.WELCOME_MESSAGE")

          return (
              handler_input.response_builder
              .speak(speak_output)
              .ask(speak_output)
              .response
          )

```

## Construir la Skill con Visual Studio Code

La compilación de la Skill está totalmente automatizada con el fichero `launch.json` y `task.json` en la carpeta `.vscode`. 
El primer archivo se usa para ejecutar la Skill localmente pero antes de ese momento ejecutaremos algunas tareas definidas en el segundo archivo que son:

1. `create_env`: esta tarea ejecutará los `hooks\post_new_hook`. Este scprit hará estas tareas:
   * Se instalará si no está instalada la librería `virtualenv` usando` pip`.
   *Después de instalarlo, creará un nuevo Python Virtual Environment si no está creado en `.venv/skill_env`
2. `install_dependencies`: esta tarea instalará todas las dependencias ubicadas en `lambda/py/require.txt` usando el Python Virtual Environment creado arriba.
3. `build`: Finalmente, copiará todo el código fuente de `lambda\py` a la carpeta `site-packages` del Python Virtual environment.   

Aquí podéis ver el `task.json` donde están las tareas explicadas anteriormente y los comandos separados por sistema operativo:
```json
  {
      // See https://go.microsoft.com/fwlink/?LinkId=733558
      // for the documentation about the tasks.json format
      "version": "2.0.0",
      "tasks": [
          {
              "label": "create_env",
              "type": "shell",
              "osx": {
                  "command": "${workspaceRoot}/hooks/post_new_hook.sh ."
              },
              "windows": {
                  "command": "${workspaceRoot}/hooks/post_new_hook.ps1 ."
              },
              "linux": {
                  "command": "${workspaceRoot}/hooks/post_new_hook.sh ."
              }
          },{
              "label": "install_dependencies",
              "type": "shell",
              "osx": {
                  "command": ".venv/skill_env/bin/pip -q install -r ${workspaceRoot}/lambda/py/requirements.txt",
              },
              "windows": {
                  "command": ".venv/skill_env/Scripts/pip -q install -r ${workspaceRoot}/lambda/py/requirements.txt",
              },
              "linux": {
                  "command": ".venv/skill_env/bin/pip -q install -r ${workspaceRoot}/lambda/py/requirements.txt",
              },
              "dependsOn": [
                  "create_env"
              ]
          },{
              "label": "build",
              "type": "shell",
              "osx": {
                  "command": "cp -r ${workspaceRoot}/lambda/py/ ${workspaceRoot}/.venv/skill_env/lib/python3.8/site-packages/",
              },
              "windows": {
                  "command": "xcopy \"${workspaceRoot}\\lambda\\py\" \"${workspaceRoot}\\.venv\\skill_env\\Lib\\site-packages\" /s /e /h /y",
              },
              "linux": {
                  "command": "cp -r ${workspaceRoot}/lambda/py/ ${workspaceRoot}/.venv/skill_env/lib/python3.8/site-packages/",
              },            
              "dependsOn": [
                  "install_dependencies"
              ]
          }
      ]
  }

```

¡Después de eso, la Skill está lista para ser lanzada localmente!

Entonces, para desarrollar la Skill, lo único que tiene que hacer es ejecutarlo localmente en Visual Studio Code:

  ![Full-width image](/assets/img/blog/tutorials/alexa-python/run.png){:.lead data-width="800" data-height="100"}
Construir nuestra Skill
  {:.figure}


**NOTA:** presta atención con la carpeta `${workspaceRoot}/.venv/skill_env/lib/python3.8/site-packages/` en Linux y OSX en la tarea `build`. 
Debes reemplazar `python3.8` si estás utilizando otra versión de Python.

## Ejecutar la Skill con Visual Studio Code

El fichero `launch.json` situado en la carpeta `.vscode` tiene la configuración para Visual Studio Code que nos permite ejecutar nuestro lambda localmente:

```json

  {
      "version": "0.2.0",
      "configurations": [
          {
              "type": "python",
              "request": "launch",
              "name": "Launch Skill",
              "justMyCode": false,
              // Specify path to the downloaded local adapter(for python) file
              "program": "${workspaceRoot}/local_debugger.py",
              "osx": {
                  "preLaunchTask": "build",
                  "pythonPath": "${workspaceRoot}/.venv/skill_env/bin/python",
                  "args": [
                      // port number on your local host where the alexa requests will be routed to
                      "--portNumber", "3001",
                      // name of your python main skill file
                      "--skillEntryFile", "${workspaceRoot}/.venv/skill_env/lib/python3.8/site-packages/hello_world.py",
                      // name of your lambda handler
                      "--lambdaHandler", "handler"
                  ],
              },
              "windows": {
                  "preLaunchTask": "build",
                  "pythonPath": "${workspaceRoot}/.venv/skill_env/Scripts/python.exe",
                  "args": [
                      // port number on your local host where the alexa requests will be routed to
                      "--portNumber", "3001",
                      // name of your python main skill file
                      "--skillEntryFile", "${workspaceRoot}/.venv/skill_env/Lib/site-packages/hello_world.py",
                      // name of your lambda handler
                      "--lambdaHandler", "handler"
                  ],
              },
              "linux": {
                  "preLaunchTask": "build",
                  "pythonPath": "${workspaceRoot}/.venv/skill_env/bin/python",
                  "args": [
                      // port number on your local host where the alexa requests will be routed to
                      "--portNumber", "3001",
                      // name of your python main skill file
                      "--skillEntryFile", "${workspaceRoot}/.venv/skill_env/lib/python3.8/site-packages/hello_world.py",
                      // name of your lambda handler
                      "--lambdaHandler", "handler"
                  ],
              },
              
          }
      ]
  }

```

Este archivo de configuración ejecutará los pasos explicados en la sección anterior y ejecutará el siguiente comando:

```bash

  .venv/skill_env/scripts/python local_debugger.py --portNumber 3001 --skillEntryFile .venv/skill_env/Lib/site-packages/hello_world.py --lambdaHandler handler

```

Esta configuración utiliza el fichero `local_debugger.py` que corre un [servidor TCP](https://docs.python.org/3/library/socket.html) listening on http://localhost:3001

Para una nueva request a la skill entrante se establece una nueva conexión al socket.
De los datos recibidos en el socket se extrae el cuerpo de la solicitud, se analiza en JSON y se pasa al lambdahandler de la Skill.
La respuesta del lambda handler es parseada como un formato de mensaje HTTP 200 como se especifica [aquí](https://developer.amazon.com/docs/custom-skills/request-and-response-json-reference.html#http-header-1)
The response is written onto the socket connection and returned.

Después de configurar nuestro archivo launch.json y comprender cómo funciona el local debugger, es hora de hacer clic en el botón play:

  ![Full-width image](/assets/img/blog/tutorials/alexa-python/run.png){:.lead data-width="800" data-height="100"}
Ejecutar nuestra Skill
  {:.figure}

Después de ejecutarlo, puede enviar requests POST de Alexa a http://localhost:3001.

**NOTA:** presta atención con la carpeta `${workspaceRoot}/.venv/skill_env/lib/python3.8/site-packages/hello_world.py`  en Linux y OSX en la tarea `build`. 
Debes reemplazar `python3.8` si estás utilizando otra versión de Python.

## Debuggeando la Skill con Visual Studio Code

Siguiendo los pasos anteriores, ahora puedes configurar breakpoints donde quieras dentro de todos los archivos Python situados en la carpeta `site-package` del Python Virtual Environment para depurar tu Skill:

  ![Full-width image](/assets/img/blog/tutorials/alexa-python/debug.png){:.lead data-width="800" data-height="100"}
Debuggear nuestra Skill
  {:.figure}

## Testear las requests localmente

Estoy seguro de que ya conoces la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios. Aunque REST se ha vuelto omnipresente, no siempre es fácil probarlo. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir APIs, lo que te ayudará a ti y a tu equipo a ser más productivos a largo plazo.

Después de ejecutar tu aplicación, tendrás un endpoint disponible en http://localhost:3001/. Con Postman puedes emular cualquier request de Alexa.

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

## Desplegar la Alexa Skill

Con el código listo, tenemos que implementarlo en AWS Lambda para que pueda conectarse a Alexa.

Antes de desplegar la Skill Alexa, Podemos ver que el fichero `config` en la carpeta `.ask` está vacio:

```json
    {
      "deploy_settings": {
        "default": {
          "skill_id": "",
          "was_cloned": false,
          "merge": {}
        }
      }
    }

```

Desplegamos la Alexa Skill con la ASK CLI:

```bash
    ask deploy
```

Como dice la documentación oficial:

> When the local skill project has never been deployed, ASK CLI creates a new skill in the development stage for your account, then deploys the skill project. If applicable, ASK CLI creates one or more new AWS Lambda functions in your AWS account and uploads the Lambda function code. Specifically, ASK CLI does the following:
> 1. Looks in your skill project's config file (in the .ask folder, which is in the skill project folder) for an existing skill ID. If the config file does not contain a skill ID, ASK CLI creates a new skill using the skill manifest in the skill project's skill.json file, then adds the skill ID to the skill project's config file.
> 2. Looks in your skill project's manifest (skill.json file) for the skill's published locales. These are listed in the manifest.publishingInformation.locales object. For each locale, ASK CLI looks in the skill project's models folder for a corresponding model file (for example, es-ES.json), then uploads the model to your skill. ASK CLI waits for the uploaded models to build, then adds each model's eTag to the skill project's config file.
> 3. Looks in your skill project's manifest (skill.json file) for AWS Lambda endpoints. These are listed in the manifest.apis.<skill type>.endpoint or manifest.apis.<skill type>.regions.<region code>.endpoint objects (for example, manifest.apis.custom.endpoint or manifest.apis.smartHome.regions.NA.endpoint). Each endpoint object contains a sourceDir value, and optionally a uri value. ASK CLI upload the contents of the sourceDir folder to the corresponding AWS Lambda function and names the Lambda function the same as the uri value. For more details about how ASK CLI performs uploads to Lambda, see AWS Lambda deployment details.
> 4. Looks in your skill project folder for in-skill products, and if it finds any, uploads them to your skill. For more information about in-skill products, see the In-Skill Purchasing Overview.
> In Python there are some more steps. Before deploy your Alexa Skill, the script `pre_deploy_hook` in `hooks` folder will be executed. This script will be run the following tasks:
> 1. It will copy all the files of your `site-packages` of your Python Virtual Environment in a new folder called `lambda_upload` located in `lambda/py` folder.
> 2. Then will copy the source code of your skill written in Python located in `lambda/py` in `lambda/py/lambda_puload`.
> 3. Finally, this new folder as a `.zip` will be deployed to AWS.

Después de la ejecución del comando anterior, tendremos el archivo `config` debidamente llenado:

```json

  {
    "deploy_settings": {
      "default": {
        "skill_id": "amzn1.ask.skill.53ad2510-5758-48db-9c43-e4263a2055db",
        "resources": {
          "lambda": [
            {
              "alexaUsage": [
                "custom/default"
              ],
              "arn": "arn:aws:lambda:us-east-1:141568529918:function:ask-custom-alexa-python-lambda-helloworld-default",
              "awsRegion": "us-east-1",
              "codeUri": "lambda/py/lambda_upload",
              "functionName": "ask-custom-alexa-python-lambda-helloworld-default",
              "handler": "hello_world.handler",
              "revisionId": "b95879d0-d039-4fa2-b7e5-96746f36689f",
              "runtime": "python3.6"
            }
          ],
          "manifest": {
            "eTag": "3809be2d04cfb7f90dd0fa023920e0bd"
          },
          "interactionModel": {
            "es-ES": {
              "eTag": "235f49ae9fa329de1b7e2489ec7e4622"
            }
          }
        },
        "was_cloned": false,
        "merge": {}
      }
    }
  }

```

## Testear requests directamente desde el cloud de Alexa

ngrok es una herramienta genial y liviana que crea un túnel seguro en tu máquina local junto con una URL pública que se puede usar para navegar por tu web en local o API.

Cuando se está ejecutando ngrok, escucha en el mismo puerto en el que se está ejecutando el servidor web local y envía solicitudes externas a tu máquina local.

Veamos como de fácil es publicar nuestra Skill ejecutandose en local para que el cloud de Alexa nos envíe requests. 
Digamos que está ejecutando tu servidor web local en el puerto 8080. En la terminal, escribiría: `ngrok http 3001`. Esto comienza a escuchar a ngrok en el puerto 3001 y crea el túnel seguro:

  ![Full-width image](/assets/img/blog/tutorials/alexa-python/tunnel.png){:.lead data-width="800" data-height="100"}
Túnel
  {:.figure}

Entonces ahora vas a la [Alexa Developer console](https://developer.amazon.com/alexa/console/ask), navegar a tu Skill > endpoints > https, agregas la URL https generada anteriormente. Por ejemplo: https://20dac120.ngrok.io.

Selecciona la opción "My development endpoint is a sub-domain...." desde el menú desplegable y haga clic en Save endpoint en la parte superior de la página.

Dirígete al tab Test en la Alexa Developer Console y lanza tu skill.

La Alexa Developer Console enviará una solicitud HTTPS al endpoint ngrok (https://20dac120.ngrok.io) que lo redirigirá a tu Skill ejecutándose en el servidor http://localhost:3001.


## Recursos
-  [Official Alexa Skills Kit Python SDK](https://pypi.org/project/ask-sdk/)
-  [Official Alexa Skills Kit Python SDK Docs](https://alexa-skills-kit-python-sdk.readthedocs.io/en/latest/)
-  [Official Alexa Skills Kit Docs](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html)


## Conclusión 

Este fue un tutorial básico para aprender Alexa Skills usando Python.
Como has visto en este ejemplo, el Alexa Skill kit para Python y las herramientas de Alexa como la ASK CLI nos pueden ayudar mucho y también nos dan la posibilidad de crear Skills de una manera fácil. 

Esta Skill está creada con ASK CLI v1, para migrar ala ASK CLI v2 echa un ojo a este [tutorial](https://developer.amazon.com/es-ES/docs/alexa/smapi/ask-cli-v1-to-v2-migration-guide.html).

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-python-lambda-helloworld)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    