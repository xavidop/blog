---
layout: post
title: Integrando Alexa con MS LUIS
image: /assets/img/blog/post-headers/alexa-luis.jpg
description: >
   Guía paso a paso para integrar MS LUIS en Alexa
comments: true
author: xavi
kate: hl markdown;
categories: [alexa, azure]
tags:
  - alexa
  - azure
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

# Integrando Alexa con Microsoft LUIS

Alexa tiene un motor de procesamiento de lenguaje natural (NLP) muy bueno. Sin embargo, hay otros NLPs en el mercado que se pueden usar y estos incluyen cada vez más capacidades.

## Prerrequisitos

Aquí tienes las tecnologías utilizadas en este proyecto
1. Node.js v12.x
2. Visual Studio Code
3. Cuenta de Azure

## Prefacio

El NLP de Alexa cubre el 99% de los casos de uso de los usuarios más comunes y podemos crear potentes Skills de Alexa utilizando su IA. Sin embargo, es un hecho que MS LUIS, como NLP, ha evolucionado mucho y podemos encontrar ua gran cantidad de funcionalidades que no podemos encontrar dentro de Alexa como sus [Prebuilt Domains](https://docs.microsoft.com/en-us/azure/cognitive-services/luis/howto-add-prebuilt-models) o sus prebuilt entities, subentities y [Regular expression entities](https://docs.microsoft.com/en-us/azure/cognitive-services/luis/luis-how-to-add-entities).


## Configurando nuestra Alexa Skill

Lo primero que debemos hacer es configurar nuestro **modelo de interacción**. Para eso vamos a crear el `OrderIntent`. Este intent tendrá, para este ejemplo, solo un utterance y un slot. Este slot tendrá el tipo `AMAZON.SearchQuery`:

![Full-width image](/assets/img/blog/tutorials/alexa-luis/alexa-interaction-model.png)

Por definición, un slot `AMAZON.SearchQuery` es un tipo de slot un poco diferente del resto. Básicamente es una búsqueda como la que podría introducir en un motor de búsqueda estándar. Para usar este slot, debemos agregar una coletilla en los utterances. En este caso utilizaremos `I want` como coletilla. En definitiva, vamos a enviar a MS LUIS todo lo que Alexa reconoce después de  `I want...`. Por ejemplo, `I want 3 pizzas`, a LUIS enviaremos `3 pizzas`.

## Creando los Azure Cognitive Services

Para interactuar con una aplicación de Microsoft LUIS desde una Skill de Amazon Alexa, necesitamos crear algunos Azure Resources.

Para eso, necesitamos crear un Natural Language Understanding Service dentro de los Cognitive Services en el [Portal de Azure](https://portal.azure.com/):

![Full-width image](/assets/img/blog/tutorials/alexa-luis/azure-resources.png){:.lead data-width="800" data-height="100"}
LUIS Azure Resources
  {:.figure}


**NOTA:** asegurate de haber clickado en los servicios de **prediction** y **authoring** durante el proceso de creación.

Después de esto, asegurate de copiar el endpoint. Vamos a utilizar este endpoint para interactuar con MS LUIS. Podmeos encontrar el endpoint después de la creación en la sección **Keys and Endpoint**:

![Full-width image](/assets/img/blog/tutorials/alexa-luis/endpoint.png){:.lead data-width="800" data-height="100"}
LUIS Endpoint
  {:.figure}


¡También asegurate de haber copiado la `region` y la `Key 1` (esta es el subscription id que usaremos en los siguientes pasos)!

## Creando una App en MS LUIS

Una vez que hayas creado los Azure Resources, debes crear la aplicación de MS Luis en el [Portal de LUIS](https://www.luis.ai/):

![Full-width image](/assets/img/blog/tutorials/alexa-luis/luis-app.png){:.lead data-width="800" data-height="100"}
LUIS App
  {:.figure}


**NOTA:** asegúrese de utilizar el prediction endpoint que has creado en el paso anterior.

Ahora que tenemos nuestra aplicación MS LUIS, añadamos el modelo de interacción:

![Full-width image](/assets/img/blog/tutorials/alexa-luis/luis-interaction-model.png){:.lead data-width="800" data-height="100"}
Modelo de interacción en LUIS
  {:.figure}


Cuando hayas creado tus Entities e Intents, debes entrenar el Modelo y publicar la aplicación LUIS en `Staging`.

## Haciendo una petición a MS LUIS desde la Alexa Skill

Ahora que tenemos todo configurado, ¡es hora de picar código! Para interactuar con MS LUIS desde el código Node.JS de la AWS Lambda de la Alexa Skill, vamos a utilizar el paquete npm llamado `@ zure/cognitivoservices-luis-runtime`. Puedes encontrar la documentación completa de este paquete [aquí](https://www.npmjs.com/package/@azure/cognitiveservices-luis-runtime).

Primero, tenemos que crear nuestro `OrderIntentHandler`, que es el controlador que va a administrar todas las request del `OrderIntent`:

~~~javascript

const OrderIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'OrderIntent';
    },
    async handle(handlerInput) {
        predictionRequest.query = Alexa.getSlotValueV2(handlerInput.requestEnvelope, 'luisquery').value;

        var result = await client.prediction.getSlotPrediction(appId, 
                                                                'Staging', 
                                                                predictionRequest, 
                                                                { verbose: true, showAllIntents: true });
        var speak = intentDispatcher(result.prediction.topIntent, result.prediction.entities)
        return handlerInput.responseBuilder
            .speak(speak)
            .reprompt(speak)
            .getResponse();
    }
};

~~~

Como se puede ver en el código anterior, estamos obteniendo el valor de nuestro slot `AMAZON.SearchQuery` llamado `luisquery` y luego, enviamos ese valor a MS LUIS usando el objeto `client` y la función `getSlotPrediction`.

Para crear el cliente necesitamos tres properties:
1. MS LUIS app id: Puedes encontrar este valor en la Aplicación LUIS en el Portal de LUIS.
2. MS Subscription id. Este id es la que obtuvimos en el paso anterior.
3. MS LUIS Prediction endpoint. Este endpoint es el que hemos obtenido en el paso anterior.

Cuando tenemos estas properties podemos crear nuestro cliente de MS LUIS de la siguiente manera:
~~~javascript

require('dotenv').config({path: '.env'})
const { CognitiveServicesCredentials } = require("@azure/ms-rest-azure-js");
const { LUISRuntimeClient } = require("@azure/cognitiveservices-luis-runtime");
 
let subscriptionKey = process.env["subscription-key"];
const creds = new CognitiveServicesCredentials(subscriptionKey);
 
const client = new LUISRuntimeClient(creds, process.env["endpoint"]);
const appId = process.env["app-id"]; // replace this with your appId.
const predictionRequest = {
    query: "",
    options: {
      datetimeReference: new Date(),
      preferExternalEntities: true
    }
  };
~~~

El resultado que vamos a recibir de MS LUIS será gestionado por el `intentDispatcher`:

~~~javascript

function intentDispatcher(intent, entities) {
    var result = '';
    switch (intent) {
        case 'PizzaIntent':
            result = `Okay, I will give you ${entities['number']} Pizzas`
            break;
        case 'BurgerIntent':
            result = `Okay, I will give you ${entities['number']} Burgers`
            break;
    
        default:
            result = 'Sorry I  didn\'t catch you'
            break;
    }

    return result;

}

~~~

## Resultado Final

Y eso es todo, aquí tienes el código completo ejecutándose. Alexa usando LUIS como su motor NLP:

![Full-width image](/assets/img/blog/tutorials/alexa-luis/final-test.png){:.lead data-width="800" data-height="100"}
Ejecución funcionando
  {:.figure}


## Recursos
* [Official Alexa Skills Kit Node.js SDK](https://www.npmjs.com/package/ask-sdk) - The Official Node.js SDK Documentation
* [Official Alexa Skills Kit Documentation](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - Official Alexa Skills Kit Documentation
* [Official Express Adapter Documentation](https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit-sdk-for-nodejs/host-web-service.html) - Express Adapter Documentation
* [Official Microsoft Azure SDK Documentation](https://github.com/Azure/azure-sdk-for-js) - DOfficial Microsoft Azure SDK Documentation

## Conclusión 

Como se puede ver, podemos integrar de una manera fácil otros motores de NLP dentro de nuestras Skills de Alexa. Este ejemplo es solo un experimento, pero os recomiendo que se use solo el NLP incorporado de Alexa, ya que puedes tener comportamientos inesperados usando `AMAZON.SearchQuery`.

Espero que este proyecto de ejemplo os sea de utilidad.

Puedes encontrar el código [aquí](https://github.com/xavidop/alexa-helloworld-ms-luis)

¡Eso es todo amigos!

Happy coding!