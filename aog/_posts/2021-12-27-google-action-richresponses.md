---
layout: post
title: Multimodal Design en Google Actions. Rich Responses usando Cards
description: >
  Creando diseño multimodal gracias a las Cards en Google Action
image: /assets/img/blog/post-headers/google-action-richresponses.jpeg
comments: true
author: xavi
kate: hl markdown;
categories: [aog]
tags:
  - aog
keywords:
  - aog
  - google assistant
  - google actions
  - actions on google
  - firebase
  - google cloud
  - gcp

lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

# Rich Responses usando Cards

Crear conversaciones es una tarea realmente difícil. Esta tarea es un proceso que puede llevar mucho tiempo. En cuanto a los asistentes de voz, este proceso es aún más complejo debido a la capacidad de interactuar con el usuario mediante sonido y pantalla simultáneamente. Cuando mezclas esas 2 interacciones, estás creando una experiencia multimodal.

En este artículo, aprenderemos cómo crear conversaciones atractivas usando la multimodalidad en nuestra Google Action gracias a sus Respuestas enriquecidas o Rich Responses usando Cards.

## Requisitios Previos

Aquí tienes las tecnologías utilizadas en este proyecto
1. Google Action Developer Account - [How to get it](https://console.actions.google.com/)
2. Google Cloud Account - [Sign up here for free](https://cloud.google.com/)
3. Firebase Account - [Sign up here for free](https://firebase.google.com/)
4. gactions CLI - [Install and configure gactions CLI](https://github.com/actions-on-google/gactions)
5. Firebase CLI - [Install and configure Firebase CLI](https://firebase.google.com/docs/cli)
6. Node.js v10.x
7. Visual Studio Code
8. yarn Package Manager
9. Google Action SDK for Node.js (Version >3.0.0)

La CLI de Google Actions (gactions CLI) es una herramienta que nos permite administrar nuestras Google Actions y sus recursos relacionados, como las Firebase Cloud Functions.
Usaremos esta herramienta para crear, desplegar y administrar nuestro ejemplo. ¡Empecemos!

## Caso de Uso

El escenario que queremos crear es cuando un usuario solicita información sobre un pokemon, podemos mostrar esa información usando multimodalidad. ¿Cómo?
1. Primero, lo que le vamos a decir al usuario, usando voz/sonido es la explicación completa del Pokémon solicitado.
2. En segundo lugar, gracias a la pantalla, le mostraremos al usuario información adicional sobre este Pokémon, como su tipo, imagen, descripción y un enlace en el que el usuario puede hacer clic y buscar más información.

Aquí es importante equilibrar la información que vamos a decir/mostrar a nuestros usuarios para no perderlos. Por ejemplo, una buena práctica es mostrar en la pantalla solo información adicional o un resumen de lo que se está diciendo mediante sonido. Es mejor utilizar la pantalla como plataforma para ayudar/guiar a los usuarios en lugar de confundirlos.

Además, es importante añadir aquí que no todos los usuarios tienen un altavoz inteligente con pantalla. Por lo tanto, tendremos que descubrir cómo gestionar el escenario usando audio+pantalla y solo audio:

![Full-width image](/assets/img/blog/tutorials/google-action-richresponses/multimodal-spectrum.jpeg){:.lead data-width="800" data-height="100"}
Multimodal Spectrum
{:.figure}

## Google Actions y las Rich Responses

El Asistente de Google y sus Google Actions tienen múltiples formas de crear respuestas visuales. En este artículo, vamos a hablar sobre las respuestas enriquecidas o Rich Responses. Estas son las disponibles:
1. Basic Card: Con estas Cards le mostrarás al usuario un resumen de la información, alguna información extra/adicional o información más específica. Con estas Cards, puedes mostrar al usuario una imagen, un título, un subtítulo, un pequeño texto y un botón con un enlace. El enlace no está disponible en Smart Speakers.
2. Image Card: Esta Card es más simple que la Basic Card. Puedes mostrar una imagen solo.
3. Table Card: esta Card se utiliza para visualizar una tabla en una pantalla.

Puedes consultar la explicación completa [aquí](https://developers.google.com/assistant/conversational/prompts-rich).

## Rich Responses en nuestra Firebase Cloud Function

Usar esta Rich Response en nuestras Firebase Cloud Functions es muy fácil gracias al SDK de Google Action `@assistant/conversation`.

Para este ejemplo, lo que vamos a crear es un intent global llamado `GetInfoIntent`:

~~~yaml
  parameters:
  - name: pokemon
    type:
      name: pokemon
  trainingPhrases:
  - háblame sobre ($pokemon 'pikachu' auto=false)
  - quién es ($pokemon 'pikachu' auto=false)
  - dame más información sobre ($pokemon 'pikachu' auto=false)
  - ($pokemon 'pikachu' auto=false)
  - qué pokemon es ($pokemon 'pikachu' auto=false)
~~~

Como puedes ver arriba, tenemos slots que usan el tipo personalizado `pokemon`.

Cuando se active este intent global, pasaremos a la Escena `GetInfoScene`.

~~~yaml
  transitionToScene: GetInfoScene
~~~

![Full-width image](/assets/img/blog/tutorials/google-action-richresponses/global-getinfoscene.png){:.lead data-width="800" data-height="100"}
GetInfo Global Intent
{:.figure}

Finalmente, aquí tienes la especificación de la Escena `GetInfoScene`:

~~~yaml
  onSlotUpdated:
    webhookHandler: GetInfoHandler
  slots:
  - name: pokemon
    required: true
    type:
      name: pokemon
~~~

![Full-width image](/assets/img/blog/tutorials/google-action-richresponses/getinfoscene.png){:.lead data-width="800" data-height="100"}
Escena GetInfo
{:.figure}


Como puedes ver en la escena anterior, configuramos el slot `pokemon` como obligatorio y cada vez que cambie el valor del slot, llamaremos a nuestra Firebase Cloud Function. El controlador que manejará las solicitudes de esta escena se llama `GetInfoHandler`.

Este handler detectará si el dispositivo que está realizando la petición acepta respuestas enriquecidas, y si es así, creará una `Card` (Basic Card). De lo contrario, usará solo sonido.

Entonces, ¿cómo podemos detectar si un dispositivo acepta Rich Responses o no? Fácil, puedes consultar las capacidades del dispositivo de la siguiente manera:

~~~javascript

  const supportsRichResponse = conv.device.capabilities.includes('RICH_RESPONSE');

  if (supportsRichResponse) {
    // Rich Response
  } else{
    // Simple Response
  }

~~~

Como vamos a utilizar los objetos `Card`, `Image`, `Link` y `Simple` necesitaremos importarlos:
~~~javascript
  const {
    conversation,
    Card,
    Simple,
    Link,
    Image,
  } = require('@assistant/conversation');
~~~

Si tenemos claros los conceptos anteriores, solo necesitamos configurar nuestro controlador:

~~~javascript

  app.handle('GetInfoHandler', async (conv) => {
    const pokemon = conv.intent.params.pokemon.resolved;
    const pokemonOriginal = conv.intent.params.pokemon.original;

    const pokemonId = pokemon - 1;
    const locale = conv.user.locale;
    if (pokemon != pokemonOriginal) {
      const pokemonIdString = String(pokemonId).padStart(3, '0'); // It sets 3 to 003 or 25 to 025

      const p = await getPokemon(pokemonId);

      const specie = await getPokemonSpecie(pokemonId);

      await showInforForOnePokemon(conv, specie, p, pokemonIdString, locale);
    } else {
      conv.add(
        new Simple({
          speech: 'Sorry, I didn\'t understand you, can you try again?',
          text: 'Sorry, I didn\'t understand you, can you try again?',
        })
      );
    }

    conv.overwrite = true;
  });

~~~

Usaremos algunas funciones adicionales para obtener información sobre Pokémon usando la [PokeAPI](https://pokeapi.co/):
1. Primero, obtendremos la información general sobre el pokemon que el usuario está solicitando. Ese código es la función `getPokemon`.
2. Luego, obtendremos la especie Pokémon para obtener la descripción usando la función llamada `getPokemonSpecie`.
3. Finalmente, estamos listos para preparar la respuesta llamando a `showInforForOnePokemon`.

La función `showInforForOnePokemon` es la más importante. Es donde vamos a preparar la respuesta para nuestros usuarios:

~~~javascript
/**
 * Capitalizes a string
 * @param {string} conv The conversation object.
 * @param {string} specie The Specie of the Pokemon for PokeAPI.
 * @param {string} pokemon The pokemon object from PokeAPI.
 * @param {string} pokemonIdString The Pokemon Id in string format.
 * @param {string} locale The locale of the user.
 */
  async function showInforForOnePokemon(
    conv,
    specie,
    pokemon,
    pokemonIdString,
    locale
  ) {
    let descriptionString = getPokemonDescription(
      specie.data.flavor_text_entries,
      locale
    );
    const types = await getPokemonTypes(pokemon.data.types, locale);

    const supportsRichResponse =
      conv.device.capabilities.includes('RICH_RESPONSE');

    if (supportsRichResponse) {
      conv.add(
        new Card({
          title: capitalize(pokemon.data.species.name),
          subtitle: types,
          text: capitalize(descriptionString),
          image: new Image({
            height: 500,
            width: 500,
            url: 'https://assets.pokemon.com/assets/cms2/img/pokedex/full/' + pokemonIdString +'.png',
            alt: capitalize(pokemon.data.species.name),
          }),
          button: new Link({
            name: 'More info',
            open: {
              url: 'https://www.pokemon.com/en/pokedex/' + pokemonIdString,
            },
          }),
        })
      );
    }

    conv.add(
      new Simple({
        speech: descriptionString,
        text: 'Info about ' + capitalize(pokemon.data.species.name),
      })
    );
  }
~~~

Al leer el código anterior, veremos que si el dispositivo tiene la capacidad de Rich Responses, agregaremos a la conversación una nueva `Card`. Esa Card tendrá estas propiedades:
1. Título: el nombre del Pokémon
2. Subtítulo: Los tipos del Pokémon que obtenemos usando la función `getPokemonTypes`.
3. Imagen: la imagen oficial de ese Pokémon accediendo a pokemon.com
4. Enlace: en dispositivos que no sean smart speakers, mostraremos un enlace que redirigirá a la página web oficial de Pokémon.

### Resultado

Teniendo todo desarrollado, este será el resultado final en un Smart Speaker:
![Full-width image](/assets/img/blog/tutorials/google-action-richresponses/speaker.png){:.lead data-width="800" data-height="100"}
Smart Speaker
{:.figure}

Y este será el resultado en el móvil con el botón `Link`:

![Full-width image](/assets/img/blog/tutorials/google-action-richresponses/mobile.png){:.lead data-width="800" data-height="100"}
Móvil
{:.figure}


## Recursos
* [Official Google Assistant Node.js SDK](https://github.com/actions-on-google/assistant-conversation-nodejs) - Official Google Assistant Node.js SDK
* [Official Google Assistant Documentation](https://developers.google.com/assistant/conversational/overview) - Official Google Assistant Documentation


## Conclusión 

Este fue un tutorial básico para aprender a crear una experiencia multimodal usando Google Actions.
Como has visto en este ejemplo, el SDK de Google Actions nos ayuda mucho mientras desarrollamos nuestras Google Actions.

Espero que este proyecto de ejemplo os sea de utilidad.

Puedes encontrar el código [aquí](https://github.com/xavidop/google-action-pokedex).

¡Eso es todo amigos!

Happy coding!