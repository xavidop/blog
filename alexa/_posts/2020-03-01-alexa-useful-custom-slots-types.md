---
layout: post
title: Alexa custom slot types útiles
image: /assets/img/blog/post-headers/dictionaries.jpg
description: >
  Un conjunto de custom slot types de Alexa listas para usa por desarrolladores españoles
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
  - skill
  - pokemon
  - nba
  - football
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

Un custom slot type define una lista de valores representativos para un slot de un o varios utterances. Loscustom slot type se utilizan para listas de elementos que no están cubiertos por el conjunto de tipos incorporado por Amazon.
Cuando utilizas un custom slot, defines el tipo y sus valores, y especificas el nombre del custom slot como parte de la definición del intent.

A continuación puedes encontrar algunos custom slots type hechas por mí. ¡Espero que te sea útil!

# Pokemons
<details>
  <summary>Click para expandir!</summary>
  <p>
    Puedes probar este custom slot type en mi Alexa Skill Pokemundo. Aquí tienes el <a href="https://www.amazon.es/Xavier-Portilla-Edo-Pokemundo/dp/B07Z638QX2" target="_blank">link</a><br/>
    El id es el número de Pokémon en la Pokedex + 1. El API es <a href="https://pokeapi.co/" target="_blank">PokeApi</a>
    <script src="https://gist.github.com/xavidop/dda153f6723bfe1b5b731c70e8a267ab.js"></script>
  </p>
</details>


# Equipos de fútbol
<details>
  <summary>Click para expandir!</summary>
  Puedes probar este custom slot type en mi Alexa Skill Resultados Futbol. Aquí tienes el <a href="https://www.amazon.es/Xavier-Portilla-Edo-Resultados-f%C3%BAtbol/dp/B082R8715G" target="_blank">link</a><br/>
  El id es el id del equipo proporcionado por la API que estoy usando para esta skill. El API es <a href="https://www.football-data.org/documentation/api" target="_blank">Football Data Org</a>
  <script src="https://gist.github.com/xavidop/c0bafcb8e63c74015310da9429326cad.js"></script>
</details>


# Ligas de fútbol
<details>
  <summary>Click para expandir!</summary>
 Puedes probar este custom slot type en mi Alexa Skill Resultados Futbol. Aquí tienes el <a href="https://www.amazon.es/Xavier-Portilla-Edo-Resultados-f%C3%BAtbol/dp/B082R8715G" target="_blank">link</a><br/>
  El id es el id de la liga proporcionado por la API que estoy usando para esta skill. El API es <a href="https://www.football-data.org/documentation/api" target="_blank">Football Data Org</a>
  <script src="https://gist.github.com/xavidop/a8522b21562e552b35df62e343ae6abf.js"></script>
</details>


# Equipos NBA
<details>
  <summary>Click para expandir!</summary>
  Puedes probar este custom slot type en mi Alexa Skill Resultados Baloncesto. Aquí tienes el <a href="https://www.amazon.es/Xavier-Portilla-Edo-Resultados-Baloncesto/dp/B082V9FDLM" target="_blank">link</a><br/>
  El id es el id del equipo de la NBA proporcionado por la API que estoy usando para esta skill. El API es <a href="https://www.balldontlie.io/#introduction" target="_blank">Ball Don't Lie</a>
  <script src="https://gist.github.com/xavidop/cc6e265d3d61f58308f2b469de751341.js"></script>
</details>


¡Eso es todo amigos! ¡Espero que te sea útil! Si tienes dudas o preguntas no dudes en contactarme!