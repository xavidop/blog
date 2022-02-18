---
layout: post
title: Multimodal Design en Google Actions. Visual Selection Responses usando Collections
description: >
  Creando diseño multimodal gracias a las Collections en Google Action
image: /assets/img/blog/post-headers/google-action-collection.jpeg
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

# Visual Selection Responses

Crear conversaciones es una tarea realmente difícil. Esta tarea es un proceso que puede llevar mucho tiempo. En cuanto a los asistentes de voz, este proceso es aún más complejo debido a la capacidad de interactuar con el usuario mediante sonido y pantalla simultáneamente. Cuando mezclas esas 2 interacciones, estás creando una experiencia multimodal.

En este artículo, aprenderemos cómo crear conversaciones atractivas usando la multimodalidad en nuestra Google Action gracias a sus Visual Selection Responses usando Collections.

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

El escenario que queremos crear es el siguiente: cuando un usuario solicita las evoluciones de un pokemon, mostraremos esa información usando multimodalidad. ¿Cómo?
1. Primero, lo que le vamos a decir al usuario, usando sonido es el nombre de las evoluciones de ese pokemon.
2. En segundo lugar, gracias a un display, mostraremos al usuario una colección de imágenes de las evoluciones y su descripción.

Así que estos son los 3 escenarios:
1. Si un pokemon tiene una sola evolución, le mostraremos al usuario una `Card` con la evolución.
2. Si un pokemon tiene múltiples evoluciones, le mostraremos al usuario una `Collection` con todas las evoluciones.
3. Si un pokemon no tiene evoluciones, le mostraremos al usuario una `Card` con la información del pokemon solicitado.

Aquí es importante equilibrar la información que vamos a decir/mostrar a nuestros usuarios para no perderlos. Por ejemplo, una buena práctica es mostrar en la pantalla solo información adicional o un resumen de lo que se está diciendo mediante sonido. Es mejor utilizar la pantalla como plataforma para ayudar/guiar a los usuarios en lugar de confundirlos.

Además, es importante añadir aquí que no todos los usuarios tienen un altavoz inteligente con pantalla. Por lo tanto, tendremos que descubrir cómo gestionar el escenario usando audio+pantalla y solo audio:

![Full-width image](/assets/img/blog/tutorials/google-action-collection/multimodal-spectrum.jpeg){:.lead data-width="800" data-height="100"}
Multimodal Spectrum
{:.figure}

## Google Actions y las Visual Selection Responses usando Collections

El Asistente de Google y sus Google Actions tienen múltiples formas de crear respuestas visuales. En este artículo, vamos a hablar sobre las rVisual Selection Responses usando Collections. Estas son las disponibles:
1. List: Mostrará en vertical una lista de elementos con un Título, Imagen y una breve descripción. Cada elemento se puede seleccionar con la voz o tocándolo.
2. Collection: Igual que `List` pero muestra los elementos en horizontal.
3. Collection browse: igual que `Collection`, pero esta Visual Selection Response solo está disponible en dispositivos con navegador web como los móviles. Estos elementos solo se pueden seleccionar tocándolos.

**NOTA:** Todos los objetos anteriores deben tener al menos 2 elementos y un máximo de 10.

Puedes consultar la explicación completa [aquí](https://developers.google.com/assistant/conversational/prompts-selection).

## Visual Selection Responses en nuestra Firebase Cloud Function

Usar estas Visual Selection Responses en nuestra funciones de Firebase Cloud es bastante fácil gracias al SDK de Google Action `@assistant/conversation`.

Para este Ejemplo lo que vamos a crear es un intent Global llamado `GetEvolutionIntent`:

~~~yaml
    parameters:
    - name: pokemon
    type:
        name: pokemon
    trainingPhrases:
    - Dime la evolución de ($pokemon 'pikachu' auto=false)
    - en quién evoluciona ($pokemon 'pikachu' auto=false)
    - quién es la evolución de ($pokemon 'pikachu' auto=false)
    - evolución de ($pokemon 'pikachu' auto=false)
    - evolucion de ($pokemon 'pikachu' auto=false)
    - evoluciones de ($pokemon 'pikachu' auto=false)

~~~

Como puedes ver arriba, tenemos slots que usan el tipo personalizado `pokemon`.

Cuando se active este intent global, pasaremos a la Escena `GetEvolutionScene`.

~~~yaml
    transitionToScene: GetEvolutionScene
~~~

![Full-width image](/assets/img/blog/tutorials/google-action-collection/global-getevolutionscene.png){:.lead data-width="800" data-height="100"}
GetEvolution global Intent
{:.figure}


Finalmente, aquí tienes la especificación de la Escena `GetEvolutionScene`:

~~~yaml
    conditionalEvents:
    - condition: scene.slots.status == "FINAL"
    handler:
        webhookHandler: option
    slots:
    - name: pokemon
    required: true
    type:
        name: pokemon
    - commitBehavior:
        writeSessionParam: prompt_option
    name: prompt_option
    promptSettings:
        initialPrompt:
        webhookHandler: GetEvolutionHandler
    required: true
    type:
        name: prompt_option

~~~

![Full-width image](/assets/img/blog/tutorials/google-action-collection/getevolutionscene.png){:.lead data-width="800" data-height="100"}
Escena GetEvolution
{:.figure}


Expliquemos la escena de arriba porque es bastante compleja. Echemos un vistazo a la sección de `Slot Filling`:
1. Como puedes ver, configuramos el slot `pokemon` como obligatorio.
2. Luego tenemos un custom type llamado `prompt_option`. La primera vez que entremos en la Escena, cuando se invque el intent `GetEvolutionIntent`, llamaremos a nuestro `GetEvolutionHandler`. Este controlador creará la Visual Selection Response utilizando una Collection.
3. Cuando entremos en esta escena, el slot `pokemon` se completará pero `prompt_option` no. ¿Por qué? porque el valor de ese slot se llenará cuando el usuario elija un artículo de la `Collection`. Cuando se complete este slot, la condición `scene.slots.status == "FINAL"` será verdadera por lo que llamaremos a nuestro controlador `option`.
4. Una vez que el usuario elige una evolución, el controlador `option` le dirá/mostrará la información de ese pokemon seleccionado.

Todos los handlers detectarán si el dispositivo que está realizando la petición acepta visual selection responses, y en caso afirmativo, creará una `Collection` o una `Card` (Basic Card). De lo contrario, usará solo sonido.

Entonces, ¿cómo podemos detectar si un dispositivo acepta rvisual selection responses o no? Fácil, podemos acceder a las propiedades del dispositivo como esta:

~~~javascript

  const supportsRichResponse = conv.device.capabilities.includes('RICH_RESPONSE');

  if (supportsRichResponse) {
    // Rich Response
  } else{
    // Simple Response
  }

~~~

Como vamos a utilizar los objetos `Tarjeta`, `Imagen`, `Enlace`, `Simple` y `Colección` necesitaremos importarlos:
~~~javascript
    const {
    conversation,
    Card,
    Simple,
    Link,
    Image,
    Collection,
    } = require('@assistant/conversation');
~~~

Si tenemos claros los conceptos anteriores, solo necesitamos configurar nuestro controlador:

~~~javascript

  app.handle('GetEvolutionHandler', async (conv) => {
    const pokemon = conv.intent.params.pokemon.resolved;
    const pokemonOriginal = conv.intent.params.pokemon.original;
    console.log('Resolved ' + conv.intent.params.pokemon.resolved);
    console.log('Original ' + conv.intent.params.pokemon.original);
    const pokemonId = pokemon - 1;
    const locale = conv.user.locale;

    if (pokemon != pokemonOriginal) {
        const pokemonIdString = String(pokemonId).padStart(3, '0');
        // const locale = conv.user.locale;

        // const pokemonIdString = String(pokemonId).padStart(3, '0');
        const p = await getPokemon(pokemonId);

        const specie = await getPokemonSpecie(pokemonId);

        let evolutions = await getPokemonEvolutions(
        specie.data.evolution_chain.url
        );

        // one evolution
        if (evolutions.length == 1) {
        
            const pEvolution = await getPokemon(evolutions[0]);

            const specieEvolution = await getPokemonSpecie(evolutions[0]);
            await showInforForOnePokemon(
                conv,
                specieEvolution,
                pEvolution,
                pokemonIdString,
                locale
            );
            conv.add(
                new Simple({
                speech:
                    capitalize(p.data.species.name) +
                    ' Just have only one evolution: ' +
                    capitalize(pEvolution.data.species.name),
                text: 'Info about ' + capitalize(pEvolution.data.species.name),
                })
            );
            return;

        // more than one evolution
        } else if (evolutions.length > 1) {
        
            let evolutionsItems = [];
            let evolutionsKeys = [];

            for (let index = 0; index < evolutions.length; index++) {
                let element = evolutions[index];
                let pItem = await getPokemon(element);
                const pokemonIdStringItem = String(pItem.data.id).padStart(3, '0');
                const specieItem = await getPokemonSpecie(element);
                const descriptionStringItem = getPokemonDescription(
                specieItem.data.flavor_text_entries,
                locale
                );
                
                // Items in the collection
                evolutionsItems[index] = {
                name: element,
                synonyms: ['Item ' + index, element],
                display: {
                    title: capitalize(element),
                    description: descriptionStringItem,
                    image: new Image({
                    url:
                        'https://assets.pokemon.com/assets/cms2/img/pokedex/full/' +
                        pokemonIdStringItem +
                        '.png',
                    alt: capitalize(element),
                    }),
                },
                };

                // List of the keys for the collection
                evolutionsKeys[index] = {
                key: element,
                };
            }

            conv.session.typeOverrides = [
                {
                name: 'prompt_option',
                mode: 'TYPE_REPLACE',
                synonym: {
                    entries: evolutionsItems,
                },
                },
            ];

            // Define prompt content using keys
            conv.add(
                new Collection({
                title: 'Evoluciones',
                subtitle: 'Collection subtitle',
                items: evolutionsKeys,
                })
            );
        } else {

            // No evolutions
            conv.add(
                new Simple({
                speech: 'This pokemon has not any evolutions',
                text: 'Info about ' + capitalize(p.data.species.name),
                })
            );
            await showInforForOnePokemon(conv, specie, p, pokemonIdString, locale);
            return;
        }

        conv.add(
        new Simple({
            speech: 'The evolutions are ' + evolutions.join(', '),
            text: 'Info about ' + capitalize(p.data.species.name),
        })
        );
    } else {
        conv.add(
        new Simple({
            speech: 'Perdona, no te he entendido, ¿Puedes volver a intentarlo?',
            text: 'Perdona, no te he entendido, ¿Puedes volver a intentarlo?',
        })
        );
    }

    conv.overwrite = true;
    });

~~~

Dividamos la explicación en los 3 escenarios posibles:

### Un pokemon solo tiene una evolucion

Esta es la porción del código que maneja cuando un pokemon tiene solo una evolución:

~~~javascript
    const pEvolution = await getPokemon(evolutions[0]);

    const specieEvolution = await getPokemonSpecie(evolutions[0]);
    await showInforForOnePokemon(
        conv,
        specieEvolution,
        pEvolution,
        pokemonIdString,
        locale
    );
    conv.add(
        new Simple({
        speech:
            capitalize(p.data.species.name) +
            ' Just have only one evolution: ' +
            capitalize(pEvolution.data.species.name),
        text: 'Info about ' + capitalize(pEvolution.data.species.name),
        })
    );
    return;
~~~

Usaremos algunas funciones adicionales para obtener información sobre Pokémon usando la [PokeAPI](https://pokeapi.co/):
1. Primero, obtendremos la información general sobre el pokemon que el usuario está solicitando. Ese código es la función `getPokemon`.
2. Luego, obtendremos la especie Pokémon para obtener la descripción usando la función llamada `getPokemonSpecie`.
3. Finalmente, estamos listos para preparar la respuesta llamando a `showInforForOnePokemon`.

La función `showInforForOnePokemon` es una de las más importantes. Allí vamos a preparar la respuesta para nuestros usuarios:

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

Al leer el código anterior, veremos que si el dispositivo tiene la capacidad de respuesta enriquecida, agregaremos a la conversación una nueva `Card`. Esa Card tendrá estas propiedades:
1. Título: el nombre del Pokémon
2. Subtítulo: Los tipos de Pokémon que obtenemos usando la función `getPokemonTypes`.
3. Imagen: la imagen oficial de ese Pokémon accediendo a pokemon.com
4. Enlace: dispositivos que no sean Smart Speakers, mostraremos un enlace que redirigirá a la página web oficial de Pokémon.

### Un pokemon tiene más de una evolución.

Este es el escenario más complejo:

~~~javascript
    let evolutionsItems = [];
    let evolutionsKeys = [];

    for (let index = 0; index < evolutions.length; index++) {
        let element = evolutions[index];
        let pItem = await getPokemon(element);
        const pokemonIdStringItem = String(pItem.data.id).padStart(3, '0');
        const specieItem = await getPokemonSpecie(element);
        const descriptionStringItem = getPokemonDescription(
        specieItem.data.flavor_text_entries,
        locale
        );
        
        // Items in the collection
        evolutionsItems[index] = {
        name: element,
        synonyms: ['Item ' + index, element],
        display: {
            title: capitalize(element),
            description: descriptionStringItem,
            image: new Image({
                url:
                    'https://assets.pokemon.com/assets/cms2/img/pokedex/full/' +
                    pokemonIdStringItem +
                    '.png',
                alt: capitalize(element),
            }),
        },
        };

        // List of the keys for the collection
        evolutionsKeys[index] = {
            key: element,
        };
    }

    conv.session.typeOverrides = [
        {
        name: 'prompt_option',
        mode: 'TYPE_REPLACE',
        synonym: {
            entries: evolutionsItems,
        },
        },
    ];

    // Define prompt content using keys
    conv.add(
        new Collection({
        title: 'Evolutions',
        subtitle: 'Collection of evolutions',
        items: evolutionsKeys,
        })
    );
~~~

Así que vamos a explicar el código. Los 2 objetos principales son los arrays que vamos a utilizar para crear la `Collection`: `evolutionsItems` y `evolutionsKeys`.

Para cada evolución vamos a agregar un objeto en el array `evolutionsItems` con estas propiedades:
1. Name: En nuestro caso, usaremos el nombre de la evolución.
2. Synonyms: aquí vamos a añadir todos los sinónimos de cada evolución. En nuestro caso, vamos a establecer el ID de la evolución y el nombre de la evolución en sí. Esto será utilizado por el Asistente de Google para volver a entrenar su IA para poder detectar la evolución que elegimos usando la voz.
3. Y finalmente un objeto Display con estas propiedades:
   1. Title: en nuestro caso, el nombre de la evolución.
   2. Description: Breve descripción del pokemon.
   3. Image: una imagen de la evolución

Además, en cada iteración, agregaremos un objeto al array `evolutionsKeys`. Cada objeto tendrá solo una propiedad llamada `key`. Asignaremos esa propiedad al nombre de la evolución.

**NOTA:** es importante tener en cuenta aquí que la propiedad `key` en el array `evolutionsKeys` tiene que ser la misma que la propiedad `name` en el array `evolutionsItems` para hacer el match a posteriori.

Una vez que tengamos ambos arrays listos con la información sobre las evoluciones, solo tendremos que hacer 2 cosas:

Primero, sobreescrivir los valores del tipo `prompt_option`:
~~~javascript
    conv.session.typeOverrides = [
        {
        name: 'prompt_option',
        mode: 'TYPE_REPLACE',
        synonym: {
            entries: evolutionsItems,
        },
        },
    ];
~~~

Y finalmente, Crear la `Collection`:

~~~javascript
    conv.add(
        new Collection({
        title: 'Evolutions',
        subtitle: 'Collection of evolution',
        items: evolutionsKeys,
        })
    );
~~~

Cuando se elige una opción de la Colección, el controlador `option` se ejecutará y mostrará la información de la evolución elegida por el usuario:

~~~javascript
  app.handle('option', async (conv) => {
    const pokemon = conv.session.params.prompt_option.toLowerCase();
    const locale = conv.user.locale;

    const p = await getPokemon(pokemon);
    const pokemonId = p.data.id;
    const pokemonIdString = String(pokemonId).padStart(3, '0');

    const specie = await getPokemonSpecie(pokemonId);

    await showInforForOnePokemon(conv, specie, p, pokemonIdString, locale);
  });

~~~

### Un pokemon no tiene evoluciones

En este caso, le diremos/mostraremos al usuario información sobre el pokemon solicitado usando las mismas funciones auxiliares que usamos en los otros escenarios:

~~~javascript
    // No evolutions
    conv.add(
        new Simple({
        speech: 'This pokemon has not any evolutions',
        text: 'Info about ' + capitalize(p.data.species.name),
        })
    );
    await showInforForOnePokemon(conv, specie, p, pokemonIdString, locale);
    return;
~~~

### Resultado

Teniendo todo desarrollado, este será el resultado final en un Smart Speaker:

![Full-width image](/assets/img/blog/tutorials/google-action-collection/evolutions-speaker.png){:.lead data-width="800" data-height="100"}
Smart Speaker
{:.figure}

Y este será el resultado en el móvil:

![Full-width image](/assets/img/blog/tutorials/google-action-collection/evolutions-mobile.png){:.lead data-width="800" data-height="100"}
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
