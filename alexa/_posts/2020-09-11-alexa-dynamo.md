---
layout: post
title: Alexa Skill con DynamoDB local
image: /assets/img/blog/post-headers/alexa-dynamo.jpg
description: >
   Alexa Skill desarrollada en Node.js usando DynamoDB en tu propio ordenador
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - lambda
  - javascript
  - node
  - noodejs
  - dynamodb
  - howto
  - skill
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

Mockear las dependencias, especialmente las externas, es una práctica común al escribir pruebas o cuando se está desarrollando localmente.
La inyección de dependencia generalmente hace que sea fácil proporcionar una implementación mockeada para nuestras dependencias, e.g. la base de datos.

En este artículo discutiremos cómo mockear un [DynamoDB](https://aws.amazon.com/dynamodb/).

Mockear una base de datos es una técnica que nos permite establecer el estado de base de datos deseado en nuestras pruebas para permitir que conjuntos de datos específicos estén listos para la ejecución de pruebas futuras. 
Con esta técnica, podemos concentrarnos en preparar los conjuntos de datos de prueba una vez y luego usarlos en diferentes fases de prueba gracias al mockeo.

# Alexa Skill con DynamoDB local 

Esta técnica también es útil cuando escribes tu código en tu ordenador local.
En otras palabras, mockear la base de datos es una simulación de una base de datos con pocos registros o con una base de datos vacía.

Alexa Skills puede usar DynamoDB para conservar los datos entre sesiones. DynamoDB es una base de datos NoSQL que ofrece Amazon Web Services.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Amazon Developer Account - [Cómo crear una cuenta](http://developer.amazon.com/)
2. AWS Account - [Regístrate aquí gratis](https://aws.amazon.com/)
3. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
4. AWS CLI - [Instalar y configurar AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
5. Node.js v10.x
6. Java Runtime Environment (JRE) version 6.x o más nueva
7. Visual Studio Code
8. npm Package Manager

La Alexa Skills Kit Command Line Interface (ASK CLI) es una herramienta para que puedas administrar tus Skills de Alexa y recursos relacionados, como las funciones de AWS Lambda.
Con la ASK CLI, tienes acceso a la Skill Management API, que te permite administrar las Skills de Alexa mediante programación desde la línea de comandos.

Si quieres crear una Skill con ASK CLI, sigue el primer paso explicado en mi ejemplo de [Node.js Skill](https://github.com/xavidop/alexa-nodejs-lambda-helloworld). 
¡Empecemos!

## Creando la DynamoDB local

En este proyecto vamos a usar el paquete npm `dynamodb-localhost`. Esta librería funciona como un wrapper para AWS DynamoDB Local, destinado para su uso en devops. Esta librería es capaz de descargar e instalar DynamoDB Local con un conjunto simple de comandos y pasar atributos opcionales definidos en [Documentación local de DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html).

Si está utilizando Docker, esta librería npm ejecuta exactamente los mismos comandos pero de manera diferente. La imagen de Docker y esta librería ejecutará el mismo [archivo jar](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html).

Utilizaremos esta librería para que sea más fácil mockear la DynamoDB.

Necesitamos ejecutar estos pasos para ejecutar nuestro DynamoDB local.
* Lo primero que necesitamos es instalar este DynamoDB local usando la librería. Este paso se logra ejecutando el método `dynamodbLocal.install()`. Este método descargará la última versión del archivo jar oficial que puedes encontrar más arriba.
* Una vez que DynamoDB se instala localmente, ahora podemos ejecutarlo el método `dynamodbLocal.start(options)`.P ara ejecutar estos dos pasos sincrónicamente, utilizaremos el paquete npm `synchronized-promise`. El objeto `options` tiene estas propiedades descritas en la documentación oficial:
  >* **port:** Port to listen on. Default: 8000
  >* **cors:**  Enable CORS support (cross-origin resource sharing) for JavaScript. You must provide a comma-separated "allow" list of specific domains. The default setting for cors is an asterisk (*), which allows public access.
  >* **inMemory:** DynamoDB; will run in memory, instead of using a database file. When you stop DynamoDB;, none of the data will be saved. Note that you cannot specify both dbPath and inMemory at once. 
  >* **dbPath:** The directory where DynamoDB will write its database file. If you do not specify this option, the file will be written to the current directory. Note that you cannot specify both dbPath and inMemory at once. For the path, current working directory is <projectroot>/node_modules/dynamodb-localhost/dynamob. For example to create <projectroot>/node_modules/dynamodb-localhost/dynamob/<mypath> you should specify '<mypath>/' with a forwardslash at the end. 
  >* **sharedDb:** DynamoDB will use a single database file, instead of using separate files for each credential and region. If you specify sharedDb, all DynamoDB clients will interact with the same set of tables regardless of their region and credential configuration.
  >* **delayTransientStatuses:** Causes DynamoDB to introduce delays for certain operations. DynamoDB can perform some tasks almost instantaneously, such as create/update/delete operations on tables and indexes; however, the actual DynamoDB service requires more time for these tasks. Setting this parameter helps DynamoDB simulate the behavior of the Amazon DynamoDB web service more closely. (Currently, this parameter introduces delays only for global secondary indexes that are in either CREATING or DELETING status.)
  >* **optimizeDbBeforeStartup:** Optimizes the underlying database tables before starting up DynamoDB on your computer. You must also specify -dbPath when you use this parameter.
  >* **heapInitial:** A string which sets the initial heap size e.g., heapInitial: '2048m'. This is input to the java -Xms argument 
  >* **heapMax:**  A string which sets the maximum heap size e.g., heapMax: '1g'. This is input to the java -Xmx argument
* Una vez que tenemos DynamoDB ejecutándose en `http:localhost:8000`, tenemos que crear un nuevo cliente DynamoDB que se conectará a este DynamoDB local.

Por lo tanto, si quieres mantener la información entre tus ejecuciones, puede establecer `inMemory` a `false` y, además, puedes especificar el `dbPath` donde se almacenarán los datos.

Este código se encuentra en el archivo `utilities/utils.js`:

```javascript

  function getLocalDynamoDBClient(options) {

        //Javascript Promise used for installing and starting local DynamoDB
        const initializeClient = () => {
            return new Promise((resolve, reject) => {
                dynamodbLocal.install(() => {
                    if (!options) reject(new Error('no options passed in!'))
                    dynamodbLocal.start(options);
                    resolve();
                });    
            })
        };

        //install & start synchronously
        let syncInitialization = sp(initializeClient)
        syncInitialization();

        //configuration for creating a DynamoDB client that will connect to the local instance
        AWS.config.update({
          region: 'local',
          endpoint: 'http://localhost:' + options.port,
          accessKeyId: 'fake',
          secretAccessKey: 'fake',
        });
    
        return new AWS.DynamoDB();
  }

```

## Usando DynamoDB local

Ahora tenemos nuestro DynamoDB ejecutándose en nuestro ordenador y un cliente configurado listo para conectarse a él. Es hora de configurar Alexa Skill para usar este cliente.
Antes de esto, es importante destacar que una característica muy importante del nuevo SDK de Alexa, es la capacidad de guardar datos de sesión en DynamoDB con una sola línea de código. 
Pero para activar esta función, tienes que decirle al adaptador de persistencia de tu Skill qué cliente usará en el momento de la creación.
Necesitamos agregar el paquete npm `ask-sdk-dynamodb-persistence-adapter` para crear nuestro adaptador de persistencia.

Este código se encuentra en el archivo `utilities/utils.js`:

```javascript

  function getPersistenceAdapter(tableName, createTable, dynamoDBClient) {

    let options = {
        tableName: tableName,
        createTable: createTable,
        partitionKeyGenerator: (requestEnvelope) => {
          const userId = Alexa.getUserId(requestEnvelope);
          return userId.substr(userId.lastIndexOf(".") + 1);
        }
    }
    //if a DynamoDB client is specified, this adapter will use it. e.g. the one that will connect to our local instance
    if(dynamoDBClient){
        options.dynamoDBClient = dynamoDBClient
    }

   return new DynamoDbPersistenceAdapter(options);
  }

```
Una vez que tenemos DynamoDB local ejecutándose, el cliente creado, el adaptador de persistencia creado y utilizando este cliente, es hora de configurar el adaptador a nuestra Skill.

Así es como se ve nuestro `index.js`:

```javascript

  var local = process.env.DYNAMODB_LOCAL
  let persistenceAdapter;
  //depending if we have enabled the local DynamoDB, we create de persistence adapter with or without local client
  if(local === 'true'){
    let options = { port: 8000 }
    let dynamoDBClient = getLocalDynamoDBClient(options); 
    persistenceAdapter = getPersistenceAdapter("exampleTable", true, dynamoDBClient);
  }else{
    persistenceAdapter = getPersistenceAdapter("exampleTable", true);
  }

  /**
   * This handler acts as the entry point for your skill, routing all request and response
   * payloads to the handlers above. Make sure any new handlers or interceptors you've
   * defined are included below. The order matters - they're processed top to bottom 
   * */
  exports.handler = Alexa.SkillBuilders.custom()
      .addRequestHandlers(
          LaunchRequestHandler,
          HelloWorldIntentHandler,
          HelpIntentHandler,
          CancelAndStopIntentHandler,
          FallbackIntentHandler,
          SessionEndedRequestHandler,
          IntentReflectorHandler)
      .addErrorHandlers(
          ErrorHandler)
      .withPersistenceAdapter(persistenceAdapter)
      .addRequestInterceptors(
          LocalisationRequestInterceptor)
      .addResponseInterceptors(
          SaveAttributesResponseInterceptor)
      .lambda();

```

Finalmente, tenemos un ejemplo de persistencia de los datos en nuestro interceptor `SaveAttributesResponseInterceptor` ubicado en la carpeta `interceptors`:

```javascript

  const Alexa = require("ask-sdk-core");

  module.exports = {
    SaveAttributesResponseInterceptor: {
      async process(handlerInput, response) {
        if (!response) return; 

        const { attributesManager, requestEnvelope } = handlerInput;

        console.log(
          "Saving to persistent storage:" + JSON.stringify(requestEnvelope)
        );
        attributesManager.setPersistentAttributes(requestEnvelope);
        await attributesManager.savePersistentAttributes();
      },
    },
  };

```

Como puedes ver, el interceptor anterior está almacenando en DynamoDB la request entrante. Este es solo un ejemplo tonto que se utiliza para mostrarle cómo funciona.

## Ejecutar DynamoDB localmente con Visual Studio Code

El fichero `launch.json` situado en la carpeta `.vscode` tiene la configuración para Visual Studio Code que nos permite ejecutar nuestro lambda localmente:

```json

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

```
Este archivo de configuración ejecutará el siguiente comando:

```bash

  node --inspect-brk=28448 lambda\custom\local-debugger.js --portNumber 3001 --skillEntryFile lambda/custom/index.js --lambdaHandler handler

```

This configuration uses the `local-debugger.js` file which runs a [TCP server](https://nodejs.org/api/net.html) listening on http://localhost:3001

Para una nueva request a la skill entrante se establece una nueva conexión al socket.
De los datos recibidos en el socket se extrae el cuerpo de la solicitud, se analiza en JSON y se pasa al lambdahandler de la Skill.
La respuesta del lambda handler es parseada como un formato de mensaje HTTP 200 como se especifica [aquí](https://developer.amazon.com/docs/custom-skills/request-and-response-json-reference.html#http-header-1). La respuesta se escribe en la conexión del socket y se devuelve.

Después de configurar nuestro archivo launch.json y comprender cómo funciona el local debugger, es hora de hacer clic en el botón play:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dynamo/run.png){:.lead data-width="800" data-height="100"}
Ejecutar la Skill
  {:.figure}


Después de ejecutarlo, puedes enviar requests POST de Alexa a http://localhost:3001.

**NOTa:** Si quieres iniciar DynamoDB local, debes establecer a `true` la variable de entorno `DYNAMODB_LOCAL` en este archivo.

## Debuggeando la Skill con Visual Studio Code

Siguiendo los pasos anteriores, ahora puedes configurar breakpoints donde quieras dentro de todos los archivos JS para depurar tu Skill:

En mi post hablando sobre [Skills en Node.js](https://github.com/xavidop/alexa-nodejs-lambda-helloworld) puedes ver cómo probar tu Skill directamente con Alexa Developer Console o localmente con Postman.

## Comprobación del DynamoDB local

Cuando ejecutamos DynamoDB localmente, esta instancia local configura un shell en http://localhosta:8000/shell

  ![Full-width image](/assets/img/blog/tutorials/alexa-dynamo/shell.png){:.lead data-width="800" data-height="100"}
DynamoDB Shell
  {:.figure}

En ese shell podemos ejecutar consultas para verificar el contenido de nuestra base de datos local. Estos son algunos ejemplos de consultas que puede hacer:

1. Obtener todo el contenido de nuestra tabla:

```javascript

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

```

Luego podemos mostrar los datos de la tabla:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dynamo/table.png){:.lead data-width="800" data-height="100"}
Contenido de la tabla
  {:.figure}


2. Obtener la información de nuestra tabla:

```javascript

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

```

Ahora podemos mostrar la información de nuestra tabla:

  ![Full-width image](/assets/img/blog/tutorials/alexa-dynamo/info.png){:.lead data-width="800" data-height="100"}
Información de la tabla
  {:.figure}

Estas consultas están utilizando el [AWS SDK para JavaScript](https://docs.aws.amazon.com/sdk-for-javascript/v2/developer-guide/dynamodb-examples.html). 

AWS CLI también puede acceder a este DynamoDB local. Antes de usar la CLI, necesitamos crear un perfil `fake` que usará la región, accessKeyId y secretAccessKey utilizados por nuestra base de datos local y el cliente. Así que en nuestro `~/.aws/credentials` nosotros tenemos que crear el perfil `fake` :

```bash

  [fake]
  aws_access_key_id=fake
  aws_secret_access_key=fake

```

Y en nuestro `~/.aws/config` establecemos la región local para nuestro perfil `fake`:

```bash

  [fake]
  region = local

```

Después de crearlo, ahora podemos ejecutar consultas utilizando la AWS CLI utilizando nuestro perfil `fake`:

```bash

  aws dynamodb list-tables --endpoint-url http://localhost:8000 --region local --profile fake

```

Este comando devolverá una lista de tablas de nuestra base de datos local:

```json

  {
      "TableNames": [
          "exampleTable"
      ]
  }

```

Puedes encontrar más información sobre cómo realizar consultas con la AWS CLI [aquí](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/index.html)

## Extra

Por supuesto, si no quieres utilizar el paquete npm `dynamodb-localhost`, AWS nos ofrece otras formas de ejecutar una instancia local.
Estas formas son:
1. Docker image. Toda la información [aquí](https://hub.docker.com/r/amazon/dynamodb-local).
2. Dependencia de Maven si tienes tu Skill en Java usando Maven o Gradle. Toda la información [aquí](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.Maven.html)


Al final, esas soluciones ejecutarán exactamente lo mismo que el paquete npm `dynamodb-localhost` pero de diferentes maneras. 
¡Elige el que más le convenga!


## Conclusión 

Este fue un tutorial básico para mockear un DynamoDB con nuestras Skills de Alexa usando Node.js.
Con esta técnica, puede realizar fácilmente cambios en los datos de prueba y realizar experimentos. Esto hará que tus pruebas sean más creíbles con datos "reales" y un entorno "real".

¿Cuántos de vosotros habéis tenido un problema con producción y funciona en staging, pero no en producción y el código fuente es el mismo en ambos entornos?.

Este es un ejemplo de poder traer/guardar datos de/a un DynamoDB local (con las consultas anteriores), ejecutarlo para descubrir problemas, cómo funciona, etc.

A la larga, esto hace que unit tests sean aún más valiosas para ti.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-nodejs-dynamo-local)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    