---
layout: post
title: Externalizar tu i18n en tu Skill de Alexa
image: /assets/img/blog/post-headers/alexa-externalize-i18n.jpg
description: >
   Externacionalización de las traducciones de nuestra Skill
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - lambda
  - poeditor
  - ask
  - i18n
  - howto
  - skill
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

En informática, la internacionalización es el proceso de diseño de software para que se pueda adaptar a diferentes idiomas y regiones sin la necesidad de reingeniería o hacer cambios en el código.
En el caso del software, significa traducir a varios idiomas, utilizar diferentes monedas o diferentes formatos de fecha entre otros.

# Externalizar tu i18n en tu Skill de Alexa

En términos de Alexa Skills, es una buena práctica tener las traducciones separadas del código fuente de AWS Lambda.
Existen muchas herramientas que pueden ayudarnos en este proceso.
Vamos a utilizar para externalizar nuestras traducciones POEditor.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto.
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. AWS CLI - [Instalar y configurar AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
5. POEditor Account - [Registrate aquí](https://poeditor.com/)
6. Node.js v10.x
7. Java Runtime Environment (JRE) version 6.x or newer
8. Visual Studio Code
9. npm Package Manager

La Alexa Skills Kit Command Line Interface (ASK CLI) es una herramienta para que puedas administrar tus Skills de Alexa y recursos relacionados, como las funciones de AWS Lambda.
Con la ASK CLI, tienes acceso a la Skill Management API, que te permite administrar las Skills de Alexa mediante programación desde la línea de comandos.

Si quieres crear una Skill con ASK CLI en Node.js usando DynamoDB en local,siga los pasos explicados en mi repositorio [aquí](https://github.com/xavidop/alexa-nodejs-dynamo-local). 

¡Empecemos!

## POEditor

POEditor es una plataforma de localización online y un sistema de gestión de traducciones, diseñado para que los equipos colaboren fácilmente, pero también adecuado para simples usuarios. Puedes usar POEditor para traducir aplicaciones, sitios web, juegos u otros softwares, y para automatizar el flujo de trabajo de localización. Es Compatible con la mayoría de los formatos de archivo l18n. También tienen una [API RESTFul](https://poeditor.com/docs/api) realmente fácil de usar.

¿Qué POEditor nos ofrece?

1. **API REST simple**
   Utiliza POEditor conectándolo a tu Skill a través de su simple API. La API automatiza el flujo de trabajo de localización y nos permite olvidarnos de administrar manualmente los proyectos de localización.
2. **Integración con GitHub, Bitbucket, GitLab y Azure DevOps**
   Permite conectas los repositorios a la cuenta POEditor para importar rápidamente los datos entre nuestra plataforma de localización y GitHub/Bitbucket/GitLab/Azure Devops.
3. **Integración con Slack y Microsoft Teams**
   Permite conectar tu cuenta POEditor a Slack o Microsoft Teams y nunca pases desaprecivido ningún evento importante durante el proceso de localización.
4. **Proyectos de traducción colaborativos**
   Se puede Eestablecer el proyecto de localización como "Público" para realizar una traducción colaborativa. Se obtiene un enlace que se puede compartir para invitar a las personas como contribuyentes.
5. **Estadísticas enriquecidas**
   La página de estadísticas ofrece información en tiempo real sobre la actividad de los traductores, la cantidad de términos, traducciones, palabras y caracteres que pertenecen a un proyecto de localización, así como gráficos y el porcentaje de completado para cada idioma.
6. **Actualización de traducciones en tiempo real**
   POEditor permite saber excatamante donde están situados tus compañeros cuando se comparte la misma página de traducción y guarda automáticamente cualquier cambio que se realice en ella.
7. **Servicios de traducción externos**
   Se pueden comprar traducciones a empresas para tu Skill directamente desde la cuenta de POEditor.
8. **Traducción automática**
   La traducción automática ofrece la posibilidad de trabajar con los motores de traducción automática de Google, Microsoft y DeepL, para completar automáticamente las traducciones que no se tengan.

## Configurando POEditor

Una vez que nos hemos registrado en POEditor, ahora es el momento de crear un nuevo proyecto para nuestra Skill de Alexa. Es una buena práctica tener un proyecto POEditor por Skill.

Para seguir con el ejemplo, se ha creado un proyecto llamado `test-skill` que contiene 15 cadenas y está disponible en español e inglés:

![Full-width image](/assets/img/blog/tutorials/alexa-externalize-i18n/dashboard.png){:.lead data-width="800" data-height="100"}
Dashboard
{:.figure}

Como se puede ver arriba, se puede visualizar de manera rápida al estado de nuestros proyectos. Podemos ver que tenemos el 57% de nuestro proyecto traducido.
Si hacemos clic en nuestro proyecto, veremos el estado de ese proyecto:

![Full-width image](/assets/img/blog/tutorials/alexa-externalize-i18n/project.png){:.lead data-width="800" data-height="100"}
Proyecto POEditor
{:.figure}

En esta vista podemos ver que tenemos 15 cadenas en 2 idiomas con 7 términos para traducir y solo 8 traducciones disponibles. Debajo de ese pane está disponible la información por idioma, se observa que tenemos todas las traducciones al español pero en inglés solo tenemos el 14%, lo que significa que en inglés solo tenemos una traducción, de las 7 a traducir.

En esta página se puede realizar una importación masiva, agregar términos para traducir, agregar nuevos idiomas, mostrar las estadísticas de las traducciones y configurar alguna configuración de este proyecto, como permisos, contribuyentes, integración del serivicio de git, tranformarlo en un proyecto de código abierto, etc.

Y finalmente, si hacemos clic en un idioma, por ejemplo Español, veremos las traducciones:

![Full-width image](/assets/img/blog/tutorials/alexa-externalize-i18n/language.png){:.lead data-width="800" data-height="100"}
Idioma en POEditor
{:.figure}

Aquí también se puede realizar una importación masiva, exportar las traducciones de idiomas actuales. Si no se tiene todas la traducciones de este idioma, se puede activar la traducción automática (se utilizará Google, Microsoft o DeepL para hacer eso).

## Descargando traducciones en la Skill de Alexa

Entonces, ahora tenemos el proyecto configurado correctamente. Para descargar las traducciones, utilizaremos la API de POEditor para descargar los términos y todas sus traducciones de un idioma en específico:

![Full-width image](/assets/img/blog/tutorials/alexa-externalize-i18n/api.png){:.lead data-width="800" data-height="100"}
API de POEditor
{:.figure}

Este es un ejemplo de request:

~~~bash
  curl -X POST https://api.poeditor.com/v2/terms/list \
      -d api_token="3af6ba0fa02f86fcf38bbe1b533461f1" \
      -d id="7717" \
      -d language="es"
~~~

Este es un ejemplo de la respuesta:

~~~json
  {
    "response": {
      "status": "success",
      "code": "200",
      "message": "OK"
    },
    "result": {
      "terms": [
        {
          "term": "WELCOME_MSG",
          "context": "",
          "plural": "",
          "created": "2020-05-16T16:53:24+0000",
          "updated": "2020-05-24T11:45:59+0000",
          "translation": {
            "content": "Beienvenido en que te puedo ayudar?",
            "fuzzy": 0,
            "updated": "2020-05-24T12:12:21+0000"
          },
          "reference": "",
          "tags": [],
          "comment": ""
        },
        {
          "term": "HELLO_MSG",
          "context": "",
          "plural": "",
          "created": "2020-05-24T11:31:07+0000",
          "updated": "",
          "translation": {
            "content": "Hola Mundo!",
            "fuzzy": 0,
            "updated": "2020-05-24T11:32:13+0000"
          },
          "reference": "",
          "tags": [],
          "comment": ""
        },
        {
          "term": "HELP_MSG",
          "context": "",
          "plural": "",
          "created": "2020-05-24T11:31:20+0000",
          "updated": "",
          "translation": {
            "content": "Puedes decirme hola. Cómo te puedo ayudar?",
            "fuzzy": 0,
            "updated": "2020-05-24T11:32:19+0000"
          },
          "reference": "",
          "tags": [],
          "comment": ""
        },
        {
          "term": "GOODBYE_MSG",
          "context": "",
          "plural": "",
          "created": "2020-05-24T11:31:25+0000",
          "updated": "",
          "translation": {
            "content": "Hasta luego!",
            "fuzzy": 0,
            "updated": "2020-05-24T11:32:23+0000"
          },
          "reference": "",
          "tags": [],
          "comment": ""
        },
        {
          "term": "REFLECTOR_MSG",
          "context": "",
          "plural": "",
          "created": "2020-05-24T11:31:29+0000",
          "updated": "",
          "translation": {
            "content": "Acabas de activar %(intentName)s",
            "fuzzy": 0,
            "updated": "2020-05-24T12:12:26+0000"
          },
          "reference": "",
          "tags": [],
          "comment": ""
        },
        {
          "term": "FALLBACK_MSG",
          "context": "",
          "plural": "",
          "created": "2020-05-24T11:31:34+0000",
          "updated": "",
          "translation": {
            "content": "Lo siento, no se nada sobre eso. Por favor inténtalo otra vez.",
            "fuzzy": 0,
            "updated": "2020-05-24T11:32:34+0000"
          },
          "reference": "",
          "tags": [],
          "comment": ""
        },
        {
          "term": "ERROR_MSG",
          "context": "",
          "plural": "",
          "created": "2020-05-24T11:31:38+0000",
          "updated": "",
          "translation": {
            "content": "Lo siento, ha habido un error. Por favor inténtalo otra vez.",
            "fuzzy": 0,
            "updated": "2020-05-24T11:32:38+0000"
          },
          "reference": "",
          "tags": [],
          "comment": ""
        }
      ]
    }
  }

~~~
Una vez se ha entendido cómo funciona la API, es hora de integrarla en nuestra Skill de Alexa.

Utilizaremos el siguiente flujo para descargar las traducciones:

![Full-width image](/assets/img/blog/tutorials/alexa-externalize-i18n/downloadflowdiagram.png){:.lead data-width="800" data-height="100"}
Diagrama de flujo descarga de traducciones
{:.figure}

El siguiente código ubicado en `utilities/i18nUtils.js` ejecutará lo mismo que explicamos en el diagrama de flujo:

~~~javascript

  async function downloadTranslations(locale, handlerInput) {

        const ISOlocale = locale.split('-')[0];
        const { attributesManager } = handlerInput;
        var sessionAtrributes = attributesManager.getSessionAttributes();
        var download = false;
        //New session stablished
        if(!('translations' in sessionAtrributes)){
            console.log('NO TRANSLATIONS IN SESSION');
            persitentAttributes = await attributesManager.getPersistentAttributes();
            if(!('translations' in persitentAttributes)){
                console.log('NO TRANSLATIONS IN DYNAMODB');
                download = true;
            
            }else{
                //we have translataions
                if((ISOlocale in persitentAttributes.translations)){
                        const lastDowloaded = moment(persitentAttributes.translations[ISOlocale].timestamp);
                        const today = moment();

                        var diffDays = today.diff(lastDowloaded, 'days');
                        if(diffDays >= 7){
                            console.log('THERE ARE TRANSLATIONS IN DYNAMODB FOR CURRENT LOCALE BUT TO OLD');
                            download = true;
                        }else{
                            console.log('THERE ARE TRANSLATIONS IN DYNAMODB FOR CURRENT LOCALE');
                            download = false;
                            translations = persitentAttributes.translations[ISOlocale].strings;
                        }
                        
                }else{
                    console.log('THERE ARE TRANSLATIONS IN DYNAMODB BUT NOT FOR CURRENT LOCALE');
                    download = true
                }
            }
        }

        if(download){
            console.log('DOWNLOADING TRANSLATIONS...');
            translations = await rp.post(poEditorEndpoint, {
                form: {
                    api_token: poEditorToken,
                    id: poEditorProjectId,
                    language: ISOlocale
                }
            }).then(function (body) {
                // Request succeeded but might as well be a 404
                // Usually combined with resolveWithFullResponse = true to check response.statusCode
                return JSON.parse(body).result;
                
            })
            .catch(function (err) {
                // Request failed due to technical reasons...
            });
        }

        
        sessionAtrributes['translations'] = translations;
        sessionAtrributes['translations'].downloaded = download;
        console.log('TRANSLATIONS: ' + JSON.stringify(translations));

        attributesManager.setSessionAttributes(sessionAtrributes);

    }

~~~

Para hacer de manera fácil una request POST `x-www-form-urlencoded` en Node.js, utilizaremos el paquete npm `request-promise`.

Este código se llamará desde el `localisationRequestInterceptor`:

~~~javascript

const Alexa = require('ask-sdk-core');

const i18nUtils = require('../utilities/i18nUtils');

// This request interceptor will bind a translation function 't' to the handlerInput
module.exports = {
    LocalisationRequestInterceptor: {
        async process(handlerInput) {

            const locale = Alexa.getLocale(handlerInput.requestEnvelope);
            await i18nUtils.downloadTranslations(locale, handlerInput);

        }
    }
}
~~~

## Usando traducciones en la Skill Alexa

Ahora que tenemos las traducciones descargadas en nuestra Skill de Alexa, ¡es hora de usarlas!

He eliminado el paquete npm `i18next` porque ya no lo usaremos. Ahora tendremos nuestra propia función de traducción.

Esta función buscará un término en las traducciones descargadas anteriormente. También se encuentra en `i18nUtils.js`:

~~~javascript

  function getTranslation(key, handlerInput, replaceObjects) {

        const { attributesManager } = handlerInput;
        const sessionAtributes = attributesManager.getSessionAttributes();
        const terms = sessionAtributes['translations'].terms;

        for(var i = 0; i < terms.length; i++){
            t = terms[i];
            if(t.term === key){
                return sprintfJs.sprintf(t.translation.content, replaceObjects);
            }
        }

    }

~~~

Ahora podemos llamar a esta función donde queramos en nuestra Skill de Alexa:

~~~javascript
  const Alexa = require('ask-sdk-core');
  const i18nUtils = require('../utilities/i18nUtils');

  module.exports = {
      LaunchRequestHandler: {
          canHandle(handlerInput) {
              return Alexa.getRequestType(handlerInput.requestEnvelope) === 'LaunchRequest';
          },
          handle(handlerInput) {
              const speakOutput = i18nUtils.getTranslation('WELCOME_MSG', handlerInput);
              
              return handlerInput.responseBuilder
                  .speak(speakOutput)
                  .reprompt(speakOutput)
                  .getResponse();
          }
      }
  };

~~~

Esta función admite el reemplazo de cadenas como el paquete `i18next`. En este caso, se usará el paquete npm `sprintf-js`:

~~~javascript
  const Alexa = require('ask-sdk-core');
  const i18nUtils = require('../utilities/i18nUtils');

  /* *
  * The intent reflector is used for interaction model testing and debugging.
  * It will simply repeat the intent the user said. You can create custom handlers for your intents 
  * by defining them above, then also adding them to the request handler chain below 
  * */
  module.exports = {
      IntentReflectorHandler: {
          canHandle(handlerInput) {
              return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest';
          },
          handle(handlerInput) {
            
              const intentName = Alexa.getIntentName(handlerInput.requestEnvelope);
            
              const speakOutput = i18nUtils.getTranslation('REFLECTOR_MSG', handlerInput, {intentName: intentName});

              return handlerInput.responseBuilder
                  .speak(speakOutput)
                  //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
                  .getResponse();
          }
      }
  };
~~~

## Guardando traducciones en la Alexa Skill

Para no descargar las traducciones cada vez que ejecutamos la Skill, las conservaremos en DynamoDB siguiendo este flujo:

![Full-width image](/assets/img/blog/tutorials/alexa-externalize-i18n/persistflowdiagram.png){:.lead data-width="800" data-height="100"}
Diagrama de flujo de presistencia de traducciones
{:.figure}

Este flujo se implementa en el interceptor `saveAttributesResponseInterceptor`:

~~~javascript
  const Alexa = require('ask-sdk-core');
  var moment = require('moment');

  // This request interceptor will bind a translation function 't' to the handlerInput
  module.exports = {
    SaveAttributesResponseInterceptor: {
      async process(handlerInput, response) {
        
        if (!response) return; // avoid intercepting calls that have no outgoing response due to errors
        const { attributesManager, requestEnvelope } = handlerInput;
        const sessionAtributes = attributesManager.getSessionAttributes();
        const translations = sessionAtributes['translations'];
        const downloaded = sessionAtributes['translations'].downloaded;

          if (downloaded) {

            persitentAttributes = await attributesManager.getPersistentAttributes();

            
            const locale = Alexa.getLocale(requestEnvelope);
            const ISOlocale = locale.split('-')[0];
            const timestamp = moment().toISOString();

            if (!('translations' in persitentAttributes)
                || (('translations' in persitentAttributes) && !(ISOlocale in persitentAttributes.translations))) {

              var saveObject = {};
              
              saveObject[ISOlocale] = {
                timestamp: timestamp,
                strings: translations,
              };
              persitentAttributes['translations'] = saveObject;

            } else {
                //Set values
                persitentAttributes.translations[ISOlocale].timestamp = timestamp;
                persitentAttributes.translations[ISOlocale].strings = translations;
            }
            
            console.log(
              'Saving to persistent storage:' + JSON.stringify(persitentAttributes)
            );
            //Persist values
            attributesManager.setPersistentAttributes(persitentAttributes);

            await attributesManager.savePersistentAttributes();
          }
      },
    },
  };


~~~


## Running the Skill and DynamoDB locally with Visual Studio Code

El fichero `launch.json` situado en la carpeta `.vscode` tiene la configuración para Visual Studio Code que nos permite ejecutar nuestro lambda localmente:

~~~json

  {
    "version": "0.2.0",
    "configurations": [
          {
              "type": "node",
              "request": "launch",
              "name": "Launch Skill",
              "env": {
                  "DYNAMODB_LOCAL": "true"
              },
              // Specify path to the downloaded local adapter(for nodejs) file
              "program": "${workspaceRoot}/lambda/custom/local-debugger.js",
              "args": [
                  // port number on your local host where the alexa requests will be routed to
                  "--portNumber", "3001",
                  // name of your nodejs main skill file
                  "--skillEntryFile", "${workspaceRoot}/lambda/custom/index.js",
                  // name of your lambda handler
                  "--lambdaHandler", "handler"
              ]
          }
      ]
  }

~~~
Este archivo de configuración ejecutará el siguiente comando:

~~~bash

  node --inspect-brk=28448 lambda\custom\local-debugger.js --portNumber 3001 --skillEntryFile lambda/custom/index.js --lambdaHandler handler

~~~

This configuration uses the `local-debugger.js` file which runs a [TCP server](https://nodejs.org/api/net.html) listening on http://localhost:3001

Para una nueva request a la skill entrante se establece una nueva conexión al socket.
De los datos recibidos en el socket se extrae el cuerpo de la solicitud, se analiza en JSON y se pasa al lambdahandler de la Skill.
La respuesta del lambda handler es parseada como un formato de mensaje HTTP 200 como se especifica [aquí](https://developer.amazon.com/docs/custom-skills/request-and-response-json-reference.html#http-header-1). La respuesta se escribe en la conexión del socket y se devuelve.

Después de configurar nuestro archivo launch.json y comprender cómo funciona el local debugger, es hora de hacer clic en el botón play:

![Full-width image](/assets/img/blog/tutorials/alexa-externalize-i18n/run.png){:.lead data-width="800" data-height="100"}
Ejecución
{:.figure}

Después de ejecutarlo, puedes enviar requests POST de Alexa a http://localhost:3001.

**NOTa:** Si quieres iniciar DynamoDB local, debes establecer a `true` la variable de entorno `DYNAMODB_LOCAL` en este archivo.

## Debuggeando la Skill con Visual Studio Code

Siguiendo los pasos anteriores, ahora puedes configurar breakpoints donde quieras dentro de todos los archivos JS para depurar tu Skill:

En mi post hablando sobre [Skills en Node.js](https://github.com/xavidop/alexa-nodejs-lambda-helloworld) puedes ver cómo probar tu Skill directamente con Alexa Developer Console o localmente con Postman.

## Comprobación del DynamoDB local

Cuando ejecutamos DynamoDB localmente, esta instancia local configura un shell en http://localhosta:8000/shell

![Full-width image](/assets/img/blog/tutorials/alexa-externalize-i18n/run.png){:.lead data-width="800" data-height="100"}
DynamoDB Shell
{:.figure}

En ese shell podemos ejecutar consultas para verificar el contenido de nuestra base de datos local. Estos son algunos ejemplos de consultas que puede hacer:

1. Obtener todo el contenido de nuestra tabla:

~~~javascript

  //GET ALL VALUES FROM TABLE

  var params = {
      TableName: 'exampleTable',

      Select: 'ALL_ATTRIBUTES', // optional (ALL_ATTRIBUTES | ALL_PROJECTED_ATTRIBUTES |
                                //           SPECIFIC_ATTRIBUTES | COUNT)
      ConsistentRead: false, // optional (true | false)
      ReturnConsumedCapacity: 'NONE', // optional (NONE | TOTAL | INDEXES)
  };


  AWS.config.update({
    region: "local",
    endpoint: "http://localhost:8000",
    accessKeyId: "fake",
    secretAccessKey: "fake"
  });

  var dynamodb = new AWS.DynamoDB();


  dynamodb.scan(params, function(err, data) {
      if (err) ppJson(err); // an error occurred
      else ppJson(data); // successful response
  });

~~~

Luego podemos mostrar los datos de la tabla:

![Full-width image](/assets/img/blog/tutorials/alexa-externalize-i18n/table.png){:.lead data-width="800" data-height="100"}
Tabla
{:.figure}


2. Obtener la información de nuestra tabla:

~~~javascript

  //GET TABLE INFORMATION
  var params = {
      TableName: 'exampleTable',
  };

  AWS.config.update({
    region: "local",
    endpoint: "http://localhost:8000",
    accessKeyId: "fake",
    secretAccessKey: "fake"
  });

  var dynamodb = new AWS.DynamoDB();

  dynamodb.describeTable(params, function(err, data) {
      if (err) ppJson(err); // an error occurred
      else ppJson(data); // successful response
  });

~~~

Ahora podemos mostrar la información de nuestra tabla:

![Full-width image](/assets/img/blog/tutorials/alexa-externalize-i18n/info.png){:.lead data-width="800" data-height="100"}
Contenido de la tabla
{:.figure}

Estas consultas están utilizando el [AWS SDK para JavaScript](https://docs.aws.amazon.com/sdk-for-javascript/v2/developer-guide/dynamodb-examples.html). 

AWS CLI también puede acceder a este DynamoDB local. Antes de usar la CLI, necesitamos crear un perfil `fake` que usará la región, accessKeyId y secretAccessKey utilizados por nuestra base de datos local y el cliente. Así que en nuestro `~/.aws/credentials` nosotros tenemos que crear el perfil `fake` :

~~~bash

  [fake]
  aws_access_key_id=fake
  aws_secret_access_key=fake

~~~

Y en nuestro `~/.aws/config` establecemos la región local para nuestro perfil `fake`:

~~~bash

  [fake]
  region = local

~~~

Después de crearlo, ahora podemos ejecutar consultas utilizando la AWS CLI utilizando nuestro perfil `fake`:

~~~bash

  aws dynamodb list-tables --endpoint-url http://localhost:8000 --region local --profile fake

~~~

Este comando devolverá una lista de tablas de nuestra base de datos local:

~~~json

  {
      "TableNames": [
          "exampleTable"
      ]
  }

~~~

Puedes encontrar más información sobre cómo realizar consultas con la AWS CLI [aquí](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/index.html)

## Conclusión

La internacionalización se lleva a cabo como un paso fundamental en el proceso de diseño y desarrollo, más que como un paso extra a posteriori, que a menudo puede implicar un proceso de reingeniería difícil y costoso. Tenemos que tomar la decisión correcta en términos de i18n al comienzo de nuestro proceso de desarrollo.

POEditor es freemium y puedes comenzar gratis con 1000 cadenas. Tiene precios muy accesibles. Se `puede comprobar los precios [aquí](https://poeditor.com/pricing/).

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-externalize-i18n)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    
