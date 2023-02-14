---
layout: post
title: Cómo testear adecuadamente tus Agentes en Dialogflow CX
description: >
  Aprende a configurar correctamente tus agentes en Dialogflow CX y comprueba lo
  fácil que resulta crear tests y configurar tu CI/CD. 
image: /assets/img/blog/post-headers/dialogflow-tests.jpg
comments: true
author: xavi
kate: hl markdown;
categories:
  - dialogflow
tags:
  - dialogflow
keywords:
  - dialogflow
  - dialogflowcx
  - dialogflow cx
  - tests
  - test
  - cxcli
  - conversationalai

lang: en
lastmod: 2023-02-14T08:48:31.024Z
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

# Dialogflow CX Testing strategies

## Requisitos previos 

Estas son las tecnologías utilizadas en este proyecto 
1. Google Cloud Account - [Regístrate aquí de forma gratuita](https://cloud.google.com/)
2. Dialogflow API enabled - [Cómo habilitarla](https://cloud.google.com/dialogflow/cx/docs/reference)
3. Dialogflow CX CLI - [Instala y configura Dialogflow CX CLI](https://cxcli.xavidop.me/)

## ¡Tests, Tests, y Tests! 

Testear las conversaciones garantiza que los componentes de un agente funcionen correctamente a un nivel en el que se incluye la infraestructura del agente (como el NLU), el webhook y la integración con sistemas externos. 

Un test puede evaluar los componentes de una aplicación a un alto nivel. Podemos utilizar tests para comprobar que dos o más componentes de un agente funcionan y generan el resultado esperado. 

Estos tests pueden ejecutarse de forma manual o automatizada en un sistema de integración continua, y se ejecutan en cada nueva versión del agente. 

## Manual

### Simulador

Dialogflow Console es una interfaz web donde puedes diseñar tus conversaciones creando agentes y, dentro de un agente, crear flows, intents, entity types, etc. En la consola de Dialogflow es posible crear tests e interactuar fácilmente con ellos. Para ello, basta con acceder a la URL: [https://dialogflow.cloud.google.com/cx](https://dialogflow.cloud.google.com/cx). Este es su aspecto:

![Full-width image](/assets/img/blog/tutorials/dialogflow-agents/console.png){:.lead data-width="800" data-height="100"}
Dialogflow CX Console
{:.figure}

La consola incluye una herramienta realmente útil para testear tu agente de forma manual. Se trata de un simulador en el que puedes interactuar con tu agente para comprobar que la conversación fluye tal y como está previsto. Para empezar a testear tu agente, haz clic en el botón **Test Agent** en la esquina superior derecha del canvas. Cuando inicies el simulador, deberás elegir el environment, el flow y page que quieres testear. Para interactuar con el simulador puedes simplemente escribir texto y enviarlo al agente, pero también puedes establecer parameters, enviar eventos, etc. Puedes deshacer el último turno de la conversación siempre que quieras. 

Una vez que hayas terminado con la interacción manual, puedes:
1. Guardar toda la conversación como un test.
2. Reproducir la conversación de forma automática.
3. Resetear la conversación en caso de que quieras empezar desde el principio.

![Full-width image](/assets/img/blog/tutorials/dialogflow-tests/simulator.png){:.lead data-width="800" data-height="100"}
Simulador de Dialogflow CX
{:.figure}

## Automatizado

### CICD

En software, tener diferentes environments en los que los desarrolladores puedan desplegar diferentes versiones de su software es un patrón común (además de una buena práctica). Cada environment cuenta con sus propias configuraciones. 

En Dialogflow CX tenemos el mismo concepto. Es posible crear una versión del agente y desplegarla en un environment. Lo mismo ocurre con el webhook: puedes desplegar una versión del webhook y utilizar esa versión en un environment. 

Cuando guardas una conversación que has realizado en el simulador como un caso de test, puedes añadirla a un pipeline de integración continua de un environment específico. Encontrarás tus pipelines CI/CD en la pestaña **Manage** al hacer clic en la sección CI/CD **CI/CD**:

![Full-width image](/assets/img/blog/tutorials/dialogflow-tests/cicd.png){:.lead data-width="800" data-height="100"}
Dialogflow CX CICD
{:.figure}

La [Dialogflow CX CLI](https://cxcli.xavidop.me/) o `cxcli` ies una herramienta de línea de comandos que puedes utilizar para interactuar con tus proyectos en Dialogflow CX en un terminal. Es un proyecto de código abierto creado por [Xavier Portilla Edo](https://xavidop.me/). Con la `cxcli` y puedes interactuar fácilmente con tus pipelines en Dialogflow CX.

Con la `cxcli` puedes también interactuar fácilmente con los pipelines CI/CD de los environments de tus agentes en Dialogflow CX. 

Puedes encontrar el uso del comando CI/CD en el comando `cxcli environment execute-cicd`. Puedes leer la documentación sobre este comando [aquí](https://cxcli.xavidop.me/cmd/cxcli_environment_execute-cicd/).

```sh
cxcli environment execute-cicd [environment] [parameters]
```

Este es un ejemplo simple del comando `cxcli environment execute-cicd`:

```sh
cxcli environment execute-cicd cicd-env --project-id test-cx-346408 --location-id us-central1 --agent-name test-agent
```

El comando anterior te proporcionará un output como este: 

```sh
$ cxcli environment execute-cicd cicd-env --project-id test-cx-346408 --location-id us-central1 --agent-name test-agent
INFO Executing cicd for environment cicd-env      
INFO PASSED                     
```

### NLU Profiling usando la Dialogflow CX CLI

Utiliza el NLU Profiler para testear los utterances de los usuarios y mejorar el modelo de interacción de tu agente.

Con el NLU Profiler puedes comprobar cómo se resuelven los utterancces con los intents y slots de tu modelo de interacción. Si un utterance no se resuelve con el intent o slot correcto, puedes actualizar el modelo de interacción y ejecutar el profiler de nuevo. Con la `cxcli`, puedes comprobar los intents que se han considerado y los que se han descartado. A continuación, puedes determinar cómo utilizar frases de entrenamiento adicionales para entrenar tu modelo para que resuelva los utterances según sus intents y slots previstos. 

Cada suite se ejecuta en una sesión Dialogflow CX, por lo que puedes testear no sólo tu NLU, sino también la propia conversación. 

Todos los comandos que tienes disponibles en la `cxcli` ara ejecutar el NLU Profiler se encuentran bajo el comando [`cxcli profile-nlu`](https://cxcli.xavidop.me/cmd/cxcli_profile-nlu/).

Este comando ejecutará una suite que incluye un conjunto de tests. Es importante saber qué suites y tests se pueden ejecutar. SLas suites y los tests se definen como ficheros `yaml`. Puedes ejecutar estas suites desde tu terminal o tus pipelines de CI/CD mediante la `cxcli`.

Para ejecutar una suite, debes ejecutar el comando `cxcli profile-nlu execute`. Para saber cómo utilizarlo, consulta esta [página](https://cxcli.xavidop.me/cmd/cxcli_profile-nlu_execute).

```sh
cxcli profile-nlu execute [suite-file] [parameters]
```

#### Suites

Una suite es un fichero YAML con la siguiente estructura:

```yaml
# suite.yaml

# Name of the suite.
name: Example Suite
# Brief description of the suite.
description: Suite used as an example
# Project ID on Google Cloud where is located your Dialogflow CX agent.
projectId: test-cx-346408
# Location where your Dialogflow CX agent is running. 
# More info here: https://cloud.google.com/dialogflow/cx/docs/concept/region
locationId: us-central1
# Agent name of your Dialogflow CX agent.
# Notice: it is the agent name, not the agent ID.
agentName: test-agent
# You can have multiple tests defined in separated files
tests:
  # ID of the test.
  - id: test_id
    # File where the test specification is located
    file: ./test.yaml
```

Puedes consultar la referencia completa [aquí](https://cxcli.xavidop.me/nluprofiler/suites/)

#### Tests

Un test es un fichero YAML con la siguiente estructura:

```yaml
# test.yaml

# Name of the test.
name: Example test
# Brief description of the test.
description: These are some tests
# Locale of the interaction model that is gonna be tested. 
# You can find the locales here: https://cloud.google.com/dialogflow/cx/docs/reference/language
localeId: en
# A check is a test itself: given an input, you will validate the intents and the parameters/entities detected by Dialogflow CX
# You can have multiple checks defined
checks:
  # The ID of the check
  - id: test
    input:
      # the input type
      # it could be text or audio
      type: text
      # The input itself in text format. For type: audio, you have to specify the audio tag.
      text: I want 3 pizzas
    validate:
      # Intent that is supposed to be detected
      intent: order_intent
      # You can have multiple parameters/intents
      # Notice: this could be empty if your intent does not have any entities/parameters.
      parameters:
        # Entity name that is supposed to be detected
        - parameter: number
          # Value that is supposed to be detected
          value: 3
```

Puedes consultar la referencia completa [aquï](https://cxcli.xavidop.me/nluprofiler/tests/)

#### Ejemplos

* Un ejemplo simple que muestra el NLU Profiler en acción. Encuéntralo [aquí](https://cxcli.xavidop.me/nluprofiler/examples/simple)
* Un ejemplo de validación de built-in entities en Dialogflow CX. Encuéntralo [aquí](https://cxcli.xavidop.me/nluprofiler/examples/system)
* Un ejemplo completo con múltiples entities definidas por el usuario y built-in entities en Dialogflow CX. Encuéntralo [aquí](https://cxcli.xavidop.me/nluprofiler/examples/text)
* Un ejemplo en el que se utiliza un archivo de audio como input. Find it [here](https://cxcli.xavidop.me/nluprofiler/examples/audio)

Puedes encontrar más ejemplos en nuestro [repositorio de GitHub](https://github.com/xavidop/dialogflow-cx-cli/tree/master/examples) así como en la página de [ejemplos](https://cxcli.xavidop.me/nluprofiler/examples).

Este es un ejemplo simple del comando `cxcli profile-nlu execute`:

```sh
cxcli profile-nlu execute examples/suite.yaml
```

El comando anterior te proporcionará un output como este:

```sh
$ cxcli profile-nlu execute suite.yaml
INFO Suite Information: test-agent                
INFO Test ID: test_1                              
INFO Input: type: text, value: hi                 
INFO Intent Detected: hi_intent                   
INFO Input: type: text, value: hello              
INFO Intent Detected: hi_intent                   
INFO Input: type: audio, value: ./audio/hi.mp3    
INFO Intent Detected: hi_intent                   
INFO Test ID: test_2                              
INFO Input: type: text, value: I want 3 pizzas    
INFO Intent Detected: order_intent                
INFO Param order_type: pizza                      
INFO Param number: 3                              
INFO Input: type: text, value: I want 2 cokes     
INFO Intent Detected: order_intent                
INFO Param number: 2                              
INFO Param order_type: coke                        
```

## Recursos

Comprueba el uso completo del comando `cxcli profile-nlu`, visita esta [página](https://cxcli.xavidop.me/cmd/cxcli_profile-nlu).

Si quieres comprobar el uso completo del comando `cxcli environment`, visita esta [página](https://cxcli.xavidop.me/cmd/cxcli_environment).

Para obtener más información sobre cómo testear en Dialogflow CX, consulta la [documentación oficial](https://cloud.google.com/dialogflow/cx/docs/concept/test-case).

## Conclusión 

Este es un tutorial básico para aprender cómo testear adecuadamente tus Agentes en Dialogflow CX. Como hemos visto en este ejemplo, es muy sencillo crear tests y  establecer pipelines de CI/CD, ya sea mediante la consola o la `cxcli`. 

Espero que este tutorial te resulte útil. 

¡Eso es todo, amigos! 

Happy coding! 