---
layout: post
title: Alexa y Kubernetes. Adaptador de persistencia para MongoDB (III)
image: /assets/img/blog/post-headers/alexa-mongo.jpg
description: >
   Guarda toda la información de tu Alexa skill en MongoDB
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

El paquete ASK SDK MongoDB Persistence Adapter contiene la implementación del adaptador de persistencia del paquete del Core del SDK `ask-sdk-core` basado en AWS SDK.

  ![Full-width image](/assets/img/blog/tutorials/alexa-kubernetes/mongo/image.jpg){:.lead data-width="800" data-height="100"}
Adaptador de persistencia para MongoDB
  {:.figure}

## ¿Qué es el adaptador de persistencia para MongoDB?

ASK SDK v2 para Node.js es un kit de desarrollo de Alexa CustomSkill de código abierto. ASK SDK v2 para Node.js nos facilita el desarrollo de Skill muy atractivas, ya que nos permite dedicar más tiempo a implementar funciones y menos a escribir código básico. Junto con ello trae diferentes interfaces que podemos implementar para crear nuestros propios objectos custom. Este es el ejemplo del adaptador de persistencia para MongoDB y el que viene por defecto de DynamoDB.

## Instalación
El paquete ASK SDK MongoDB Persistence Adapter es un paquete adicional para el SDK principal `ask-sdk-core` y, por lo tanto, tenemos una peer dependency del paquete SDK principal. Desde dentro de nuestro proyecto de NPM, ejecutamos los siguientes comandos en la terminal para instalarlos:

~~~
npm install --save ask-sdk-mongodb-persistence-adapter
~~~

## Uso y primeros pasos

Podéis encontrar toda la documentación [aquí] https://ask-sdk-mongodb-persistence-adapter.netlify.app/).

Cómo crear una instancia de `MongoDBPersistenceAdapter` y `PartitionKeyGenerator`:

1. Pasar la conexión URL de MongoDB como parámetro:
 
~~~javascript
let { MongoDBPersistenceAdapter } = require('ask-sdk-mongodb-persistence-adapter');

let options = {
  collectionName: 'myCollection',
  mongoURI: 'mongodb+srv://<username>:<password>@<cluster>.mongodb.net/',
  partitionKeyGenerator: (requestEnvelope) => {
    const userId = Alexa.getUserId(requestEnvelope);
    return userId.substr(userId.lastIndexOf(".") + 1);
  }
}

let adapter =  new MongoDBPersistenceAdapter(options);
~~~

1. Pasando [MongoClient] (https://mongodb.github.io/node-mongodb-native/3.6/api/MongoClient.html) como parámetro. Usando esto, debemos agregar [el paquete npm `mongodb`.](https://www.npmjs.com/package/mongodb):

~~~javascript
let { MongoDBPersistenceAdapter } = require('ask-sdk-mongodb-persistence-adapter');
let { MongoClient } = require('mongodb');

let mongoClient = new MongoClient('mongodb+srv://<username>:<password>@<cluster>.mongodb.net/')

let options = {
  collectionName: 'myCollection',
  mongoDBClient: mongoClient,
  partitionKeyGenerator: (requestEnvelope) => {
    const userId = Alexa.getUserId(requestEnvelope);
    return userId.substr(userId.lastIndexOf(".") + 1);
  }
}

let adapter =  new MongoDBPersistenceAdapter(options);

~~~

Finalmente tenemos que agregar este nuevo adaptador al objeto `SkillBuilders` con el método `withPersistenceAdapter`:

~~~javascript

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
    .withPersistenceAdapter(adapter)
    .lambda();
~~~

Consulte la especificación completa de `MongoDBPersistenceAdapter` [aquí](https://ask-sdk-mongodb-persistence-adapter.netlify.app/classes/_mongodbpersistenceadapter_.mongodbpersistenceadapter.html#constructor).

Consulte la especificación completa de `PartitionKeyGenerator` [aquí](https://ask-sdk-mongodb-persistence-adapter.netlify.app/modules/_partitionkeygenerators_.html#partitionkeygenerator).

## Uso con TypeScript
El paquete ASK SDK MongoDB Persistence Adapter para Node.js incluye dinifition files de TypeScript para su uso en proyectos de TypeScript y para admitir herramientas que pueden leer archivos .d.ts. Nuestro objetivo es mantener estos dinifition files de TypeScript actualizados con cada release para cualquier API pública.

### Requisitos previos
Antes de que podamos comenzar a usar estos dinifition files  de TypeScript en nuestro proyecto, debemos aseguraranos de que nuestro proyecto cumpla con algunos de estos requisitos:
- TypeScript >= v2.x
- TypeScript definitions for node. Podemos usar npm para instalar esto escribiendo lo siguiente en una ventana de terminal:
- 
~~~
npm install --save-dev @types/node
~~~

### En Node.js
Para usar los dinifition files de TypeScript dentro de un proyecto Node.js, simplemente importamos ask-sdk-mongodb-persistence-adapter como se muestra a continuación:

En un archivo de TypeScript:

~~~typescript
import * as Adapter from 'ask-sdk-mongodb-persistence-adapter';
~~~

En un archivo JavaScript:

~~~javascript
const Adapter = require('ask-sdk-mongodb-persistence-adapter');
~~~

## Abrrir Issues
Si habéis encotrad bugs, feature requests o simplemente tneéis preguntas, me gustaría conocerlo. Podéis encontrar los [bugs existentes](https://github.com/xavidop/ask-sdk-mongodb-persistence-adapter/issues) e intentad aseguraros de que vuestro bug no exista antes de abrir uno nuevo. Es útil si se incluye la versión del SDK, Node.js o el entorno del navegador y el sistema operativo que estais utilizando. Incluid también un stack trace y como reproducirlo cuando corresponda.

## License
Este adaptador se distribuye bajo la licencia Apache, versión 2.0, consultad LICENCE para obtener más información.

## Conclusion 

Como se puede ver, con muy poco código se puede construir un adaptador de persistencia.

Espero que este proyecto de ejemplo te sea de utilidad.

Puede encontrar el código [aquí](https://github.com/xavidop/ask-sdk-mongodb-persistence-adapter)

¡Eso es todo amigos!

Happy coding!
