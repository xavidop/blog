---
layout: post
title: Cómo crear Alexa custom slot types
image: /assets/img/blog/post-headers/slots.jpg
description: >
  Sencillo tutorial sobre cómo crear Alexa custom slot types
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - slot
  - customslot
  - howto
  - skill
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

La usabilidad de la Skill depende directamente de cómo esten definidos los utterances de ejemplo y los custom slot types representen el uso del lenguaje del mundo real.

Como dicen las mejores prácticas de Alexa:

Building a representative set of custom values and sample utterances is an important process and one that requires iteration. During development and testing, try using many different phrases to invoke each intent. If you can observe other users during testing, note the phrases that they speak to invoke each intent. Continually update the custom values and sample utterances file to ensure that it includes instances of your users' most common phrasings.

# Custom slot types

En primer lugar, lo que necesitas es login in [Amazon Alexa Console](https://developer.amazon.com/alexa){:target="_blank"}. Una vez que haya completado este paso, debes acceder a cualquiera de tus Skills. Si aún no tienes ninguna Skill, es hora de crearla. 

Ahora vamos a crear un custom slot type. 

En la sección Build, a la izquierda, hay una opción llamada "Slot Types", como puedes ver en la imagen a continuación. haz clic ahí para ver las opciones que la Alexa developer console nos ofrece.

![Full-width image](/assets/img/blog/tutorials/custom-slot-types/custom-slot-types-1.png){:.lead data-width="800" data-height="100"}
Sección Build
{:.figure}


Al hacer clic en el botón "Add" encontraras una nueva sección con dos opciones:
* **Create custom value type:**
 esta es la opción que necesitamos para crear un nuevo slot que estará listo para usar en nuestra Skill
* **Use an existing slot type from Alexa's built-in library:**
  Aquí tienes todas las slots que Amazon ha creado para ti, como meses, días de la semana, películas, etc.

![Full-width image](/assets/img/blog/tutorials/custom-slot-types/custom-slot-types-2.png){:.lead data-width="800" data-height="100"}
Creando un slot
{:.figure}

Nos vamos a centrar en la primera opción. Ahora debes establecer un nombre para tu nuevo custom slot type y luego hacer clic en el botón "Create custom slot type":

Tiene dos formas de agregar valores personalizados a esta lista:
* **Con una edición masiva:**
  Esta opción es muy útil para un gran conjunto de valores. Nos permite insertar valores al estilo .csv. Un valor por línea (formatted as VALUE, ID, SYNONYM1, SYNONYM2, …).

  ![Full-width image](/assets/img/blog/tutorials/custom-slot-types/custom-slot-types-4.png){:.lead data-width="800" data-height="100"}
  Edición masiva
  {:.figure}

* **INsertando los valores uno por uno:**
  Ingresar un valor manualmente es tan fácil como rellenar el campo que tienes en esa pantalla y luego pulsar Intro. Después de meter este nuevo valor, puedes configurar el ID y los sinónimos (**que es la parte más importante del custom value!!!**)

  ![Full-width image](/assets/img/blog/tutorials/custom-slot-types/custom-slot-types-3.png){:.lead data-width="800" data-height="100"}
 Creando un slot
  {:.figure}
  

Aquí tienes un ejemplo con todos los pokemons configurados correctamente en Alexa Developer Console:

![Full-width image](/assets/img/blog/tutorials/custom-slot-types/custom-slot-types-5.png){:.lead data-width="800" data-height="100"}
Lista de Pokemons
{:.figure}

He creado para ti algunoscustom slot types por si quieres reutilizarlos. Puedes encontrarlos en este [post](/alexa/2020-03-01-alexa-useful-custom-slots-types)

¡Eso es todo amigos! ¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.