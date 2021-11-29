---
layout: post
title: Alexa Entities
image: /assets/img/blog/post-headers/alexa-entities.jpg
description: >
   Alexa Entities
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

# Alexa Entities

En el Alexa Live 2020, el equipo de Amazon Alexa lanzó una funcionalidad llamada Alexa Entities. Esta funcionalidad tiene como objetivo utilizar el Alexa Graph Knowledge para recuperar información adicional de algunos built-in slots como por ejemplo de lugares, actores, personas, etc. Después de un año, esta funcionalidad se ha lanzado en más locales, incluidos español, alemán, francés e italiano. Con Alexa Entities, no necesitas acceder a una API externa para obtener datos adicionales. Cada entity proporcionará una URL del grafo de conocimiento de Alexa donde podrás obtener esa información extra.

## Prerrequisitos

Aquí tienes las tecnologías utilizadas en este proyecto:
1. Node.js v14.x
2. Visual Studio Code
3. Extensión de Alexa para VS Code

## Configurando nuestra Skill de Alexa

Como he señalado más arriba, cuando agregamos un built-in slot en nuestro modelo de interacción, por ejemplo `AMAZON.Actor`, y ese slot se matchea con lo que ha dicho el usuario, recibiremos en nuestra AWS Lambda dos cosas.
1. Primero que este slot se ha matcheado 
2. Segundo, algo de información adicional.
   
Esa información adicional será la resolución del slot como una Alexa entity. ¿Qué es esa información? Será un enlace donde podemos obtener todos los datos de esa Alexa entity que se ha matcheado. Este enlace tiene una forma parecida al siguiente: `https://ld.amazonalexa.com/entity/v1/KmHs1W4gVQDE9HHq72eDLs`

Debido a esto, necesitamos configurar nuestro backend de la Alexa Skill. Como vamos a buscar algunos datos en el Alexa Knowledge Graph, el primer paso que debemos hacer es agregar un paquete npm: `axios`

Para instalar esta dependencia, tenemos ejecutar estos comandos:
1. Para npm:
~~~bash
    npm install --save axios
~~~
2. Para yarn:
~~~bash
    yarn add axios
~~~

Axios es una de las librerías más comunes que se utilizan en Node.js para realizar solicitudes HTTP.

¡Con este paquete instalado/actualizado, ya casi tenemos el setup necesario! Continuemos con los siguientes pasos.

## Resolución de las Alexa Entities

Como se explica en la documentación oficial: "Cada Entity es un nodo vinculado a otras Entities en el grafo de conocimiento".

![Full-width image](/assets/img/blog/tutorials/alexa-entities/knowledge_graph.jpeg){:.lead data-width="800" data-height="100"}
Kownledge Graph
  {:.figure}


Así que volvamos a nuestro ejemplo, el del `AMAZON.Actor`. Imagina que tenemos un slot llamado `actor` que usa ese tipo de built-in slot. Cuando solicitamos información de un actor y ese actor coincide con el slot y también ese actor existe en el grafo de conocimiento de Alexa, obtendremos una URL para obtener sus datos.

Pero, ¿dónde podemos encontrar esa URL? ¿Dónde se encuentra esa información dentro de la request? Esto es lo que Alexa llama **Slot resolution**. El Slot resolution es la forma en que Alexa nos dice, como desarrolladores, que un slot ha matchaedo con éxito y cuál es la authority que resolvió el valor de ese slot. Por ejemplo, un slot puede resolverse mediante estas 3 authorities:
1. Como **Custom value**. Por ejemplo, un actor que agregamos manualmente.
2. Como **Dynamic entity**. Los valores personalizados que podemos agregar mediante código.
3. Como **Alexa entity**. Cuando el actor existe en el grafo de conocimiento de Alexa.

Las Slot resolution authorities y sus resoluciones se pueden encontrar dentro de la request aquí:

![Full-width image](/assets/img/blog/tutorials/alexa-entities/entity_resolution.png){:.lead data-width="800" data-height="100"}
Slot Resolution
  {:.figure}

En este ejemplo, cuando obtenemos los datos, vemos algunas propiedades como `birthdate`, `birthplace` o un array llamado `child`. Este array contiene el hijo o los hijos del actor que hemos solicitado. En cada objeto del array `child` encontraremos una URL donde podemos obtener los datos de cada hijo.

![Full-width image](/assets/img/blog/tutorials/alexa-entities/entity_graph.png){:.lead data-width="800" data-height="100"}
Entity Graph
  {:.figure}

Es importante señalar aquí que cada entity tiene su propio esquema. Se explican todos los tipos [aquí](https://developer.amazon.com/en-US/docs/alexa/custom-skills/alexa-entities-reference.html#entity-classes-and-properties).

## Jugando con Alexa Entities

Una vez que tenemos los paquetes que necesitamos instalados/actualizados y entendemos la resolución de las Alexa Entities y cómo funciona, necesitamos modificar nuestro AWS Lambda para jugar con las Alexa Entities.

Para este ejemplo, he creado un intent para obtener información de los actores:

![Full-width image](/assets/img/blog/tutorials/alexa-entities/intent.png){:.lead data-width="800" data-height="100"}
Intent
  {:.figure}

El slot `actor` está usando el built-in slot `AMAZON.Actor`:

![Full-width image](/assets/img/blog/tutorials/alexa-entities/slot.png){:.lead data-width="800" data-height="100"}
Slot
  {:.figure}

Luego tenemos un handler para este intent llamado `EntityIntentHandler`. Lo primero que va a hacer este controlador es verificar si el slot `actor` se ha matchaedo exitósamente y si se ha resuelto como una Alexa Entity:

~~~javascript
const actor = Alexa.getSlot(handlerInput.requestEnvelope, 'actor')

const resolutions = getSlotResolutions(actor);
~~~

Esta es la función `getSlotResolutions`:

~~~javascript
function getSlotResolutions(slot) {
    return slot.resolutions
        && slot.resolutions.resolutionsPerAuthority
        && slot.resolutions.resolutionsPerAuthority.find(resolutionMatch);
}

function resolutionMatch(resolution) {
    return resolution.authority === 'AlexaEntities'
        && resolution.status.code === 'ER_SUCCESS_MATCH';
}
~~~

Cuando tenemos el slot y se resuelve con éxito como una Alexa Entity, necesitamos obtener un token. Este token se incluye en cada request. Para eso solo necesitas llamar a esta función:

~~~javascript
const apiAccessToken = Alexa.getApiAccessToken(handlerInput.requestEnvelope);
~~~

Ten en cuenta que el objeto `Alexa` es el objeto que obtuvimos al importar la biblioteca `ask-sdk-core`:

~~~javascript
const Alexa = require('ask-sdk-core');
~~~

Con toda esta información, podemos llamar al grafo de conocimiento de Alexa usando `axios` (asegúrate de que ya lo has importado):

~~~javascript
const entityURL = resolutions.values[0].value.id;
const headers = {
    'Authorization': `Bearer ${apiAccessToken}`,
    'Accept-Language': Alexa.getLocale(handlerInput.requestEnvelope)
};
const response = await axios.get(entityURL, { headers: headers });
~~~

Es importante agregar el locale para obtener los datos en el idioma adecuado.

Si la request ha ido bien, podemos preparar nuestra string que vamos a devolver a Alexa usando los datos del Alexa Knowledge Graph:

~~~javascript
if (response.status === 200) {
    const entity = response.data;
    const birthplace = entity.birthplace.name[0]['@value']
    const birthdate = new Date(Date.parse(entity.birthdate['@value'])).getFullYear()
    const childsNumber = entity.child.length
    const occupation = entity.occupation[0].name[0]['@value']
    const awards = entity.totalNumberOfAwards[0]['@value']
    const name =  entity.name[0]['@value']
    if (Alexa.getLocale(handlerInput.requestEnvelope).indexOf('es') != -1){
        speakOutput = name + ' nació en ' + birthplace + ' en '+ birthdate +' y tiene ' + childsNumber + ' hijos. Actualmente trabaja como ' + occupation + '. Tiene un total de ' + awards + ' premios.'
    }else{
        speakOutput = name + ' was borned in ' + birthplace + ' in ' + birthdate + ' and has ' + childsNumber + ' children. Now is working as a ' + occupation + '. Has won ' + awards + ' awards.'
    }
    
}else{
    if (Alexa.getLocale(handlerInput.requestEnvelope).indexOf('es') != -1){
        speakOutput = 'No he encontrado informacion sobre ese actor.'
    }else{
        speakOutput = 'Didnt find information about that actor.'
    }
}
~~~

Y este es el resultado final:

![Full-width image](/assets/img/blog/tutorials/alexa-entities/execution_es.png){:.lead data-width="800" data-height="100"}
Simulador
  {:.figure}

## ¿Qué Alexa Entities están disponibles?

Es importante decir que no todas los built-in slots de Alexa están enlazados a Alexa Entities. Depende del locale y del built-in slot en sí. Para asegurarte de cuáles están disponibles, puedes consultar la [documentación oficial](https://developer.amazon.com/en-US/docs/alexa/custom-skills/alexa-entities-reference.html#bist-er-support).


## Recursos
* [Official Alexa Skills Kit Node.js SDK](https://www.npmjs.com/package/ask-sdk) - The Official Node.js SDK Documentation
* [Official Alexa Skills Kit Documentation](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html) - Official Alexa Skills Kit Documentation
* [Official Alexa Entities Documentation](https://developer.amazon.com/en-US/docs/alexa/custom-skills/alexa-entities-reference.html) - Official Alexa Entities Documentation

## Conclusión 

Como puedes ver, las Alexa Entities pueden ayudarnos a crear experiencias de voz muy chulas con contenido enriquecido.

Espero que este proyecto de ejemplo os sea de utilidad.

Puedes encontrar el código [aquí](https://github.com/xavidop/alexa-helloworld-new-vscode-config)

¡Eso es todo amigos!

Happy coding!




