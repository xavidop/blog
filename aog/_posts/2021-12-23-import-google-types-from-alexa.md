---
layout: post
title: Crea Google Custom Types desde Alexa Custom Slots
description: >
  Una CLI simple que transforma los Alexa Custom Slots en Google Custom Types
image: /assets/img/blog/post-headers/google-types-importer.jpg
noindex: true
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

# Google Action Type Importer

Esta CLI te permite transformar tus Alexa Custom Slots en Google Custom Types.

## Prefacio

### Natural Language Understanding

NLU o Natural Language Understanding es un campo de la IA que nos permite comprender el input de los usuarios en forma de voz o texto.

Para eso, debes especificar el modelo de interacción (Interaction Model). En términos de Google Assistant y sus Google Actions, será el Voice Interaction Model o VUI. Con la VUI, tú, como voice app developer, especificarás cómo vas a interactuar con el asistente.

En la Google Action, crearás intents (globales o específicas de una Scene) que contendrán Uttrances. Estos Utterances determinarán la misma acción/intención del usuario. Además, esas expresiones pueden contener variables también llamadas slots o entities. Cada slot puede tener su tipo.

Habiendo definido bien la VUI, el proceso de NLU puede identificar lo que el usuario solicita en cualquier momento:

![Full-width image](/assets/img/blog/tutorials/google-actions-type-importer/nlu.png){:.lead data-width="800" data-height="100"}
NLU. Foto de Chatbots Magazine.
{:.figure}

### Custom Types y su importancia

Google Assistant tiene sus propios tipos personalizados como `actions.type.Date`, `actions.type.DateTime`, `actions.type.Time` o `actions.type.Number`. Es importante que si estás desarrollando tus Google Actions y estás trabajando con tus propias palabras, aquellas que sean específicas/relacionadas con tu negocio, deberás crear tus tipos personalizados. El Asistente de Google utilizará estos tipos para entrenar su IA. Así podrá entenderte mientras interactúas con él. La usabilidad de tus Google Action depende directamente de qué tan bien los utterances y los valores de los custom types representen el uso del lenguaje en el mundo real.

Es por eso que creé esta herramienta, para transformar adecuadamente tus Custom Slots creados en Alexa en Custo Types de tus Google Actions.

## Instalación

Puede descargar la última versión desde [aquí](https://github.com/xavidop/google-action-type-importer/releases)

### Hombrew

Si usas el administrador de paquetes Homebrew, puede instalar esta CLI siguiendo estos pasos:

1. Añade mi Hombre tab:
~~~bash
  brew tap xavidop/tap git@github.com:xavidop/homebrew-tap.git
  brew update
~~~
2. Instala la CLI:
~~~bash
  brew install google-action-type-importer
~~~

## Uso

Esta es la descripción general de la herramienta:

~~~bash
  ➜  google-action-type-importer git:(master) ✗ google-action-type-importer 
  Welcome to google-action-type-importer!

  This utility provides you with an easy way to create custom types 
  for your Google Actions projects importing those values from files. 

  You can find the documentation at https://github.com/xavidop/google-action-type-importer/master/README.md.

  Please file all bug reports on Github at https://github.com/xavidop/google-action-type-importer/issues.

  Usage:
    google-action-type-importer [flags]
    google-action-type-importer [command]

  Available Commands:
    completion  generate the autocompletion script for the specified shell
    help        Help about any command
    import      Imports a type
    version     Get google-action-type-importer version

  Flags:
    -h, --help      help for google-action-type-importer
    -v, --verbose   verbose error output (with stack trace)

  Use "google-action-type-importer [command] --help" for more information about a command.
~~~

### Importar un Custom Slot de una Alexa Skill a un Custom Type de una Google Action

Para importar un Slot de Alexa, debes tener tu Slot en un CSV con el formato que acepta [Alexa](https://developer.amazon.com/en-US/docs/alexa/custom-skills/create-and-edit-custom-slot-types.html):

~~~csv
  Slot value,identifier,synonym,synonym,...
~~~

Teniendo ese archivo, puedes ejecutar el subcomando `import`:

~~~bash
  ➜  google-action-type-importer git:(master) ✗ google-action-type-importer import --help
  Imports a type

  Usage:
    google-action-type-importer import [flags]

  Flags:
    -f, --file string        CSV to read (default "file.csv")
    -e, --header             Specifies if the CSV contains headers or not
    -h, --help               help for import
    -t, --type-name string   Type to create (default "type")

  Global Flags:
    -v, --verbose   verbose error output (with stack trace)
~~~

### Ejemplo

~~~bash
  google-action-type-importer import -f examples/pokemon.csv --header -t pokemon
~~~

El comando anterior creará el archivo `pokemon.yaml`. Puedes encontrar el CSV de ejemplo [aquí](/assets/img/blog/tutorials/google-actions-type-importer/pokemon.csv) y el fichero YAML resultante [aquí](/assets/img/blog/tutorials/google-actions-type-importer/pokemon.yaml).

Alexa Custom Slot:

![Full-width image](/assets/img/blog/tutorials/google-actions-type-importer/alexa.png){:.lead data-width="800" data-height="100"}
Alexa Custom Slot
{:.figure}

Google Action Custom Type:

![Full-width image](/assets/img/blog/tutorials/google-actions-type-importer/google.png){:.lead data-width="800" data-height="100"}
Google Action Custom type
{:.figure}

Fácil ¿Verdad?


## Recursos

* [Official Google Assistant Node.js SDK](https://github.com/actions-on-google/assistant-conversation-nodejs) - Official Google Assistant Node.js SDK
* [Official Google Assistant Documentation](https://developers.google.com/assistant/conversational/overview) - Official Google Assistant Documentation
* [Official Google Actions Custom Types Documentation](https://developer.amazon.com/en-US/docs/alexa/custom-skills/alexa-entities-reference.html) - Official Google Actions Custom Types Documentation
  
## Conclusión 

Como puedes ver, puedes transferir tus Alexa Slots fácilmente a tus Google Actions. ¡Deseando ver las Google Actions que vas a desarrollar utilizando esta CLI!

Espero que esta herramienta te sea de utilidad.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/google-action-type-importer)

!Eso es todo!

Happy coding!
