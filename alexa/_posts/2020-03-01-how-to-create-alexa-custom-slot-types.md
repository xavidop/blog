---
layout: post
title: How to create Alexa custom slot types
image: /assets/img/blog/post-headers/slots.jpg
description: >
  Easy Alexa custom slot types tutorial
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
lang: en
---

As Alexa best practices say:

The usability of the skill directly depends on how well the sample utterances and custom slot values represent real-world language use.

Building a representative set of custom values and sample utterances is an important process and one that requires iteration. During development and testing, try using many different phrases to invoke each intent. If you can observe other users during testing, note the phrases that they speak to invoke each intent. Continually update the custom values and sample utterances file to ensure that it includes instances of your users' most common phrasings.

# Custom slot types

First of all what you need is to login in [Amazon Alexa Console](https://developer.amazon.com/alexa){:target="_blank"}. Once you have completed this step you must access any of your skills. If you don't have any skills crate yet, it's time to create it. 

Now it is time to create your own custom slot type. 

In Build section, on the left, there is an option called "Slot types" as you can see in the image below. Click there to view the options that Alexa developer console offers to us.

![Full-width image](/assets/img/blog/tutorials/custom-slot-types/custom-slot-types-1.png){:.lead data-width="800" data-height="100"}
Build section
{:.figure}


Clicking the button "Add" you will find a new section with two options:
* **Create custom value type:**
  this is the option we need in order to crate a full new slot ready to use in our skill
* **Use an existing slot type from Alexa's built-in library:**
  here you have all the slots that Amazon have made for you like months, days of the week, movies, etc.

![Full-width image](/assets/img/blog/tutorials/custom-slot-types/custom-slot-types-2.png){:.lead data-width="800" data-height="100"}
Creating a slot
{:.figure}

We are going to focus on the first option. Now you have to set a name of your new custom slot type and then click on "Create custom slot type button":

You have two ways to add custom values to this list:
* **With a bulk edit:**
  This option is very useful for a large set of values. It allows us to enter values with a comma-separated or .csv style. One slot value per line (formatted as VALUE, ID, SYNONYM1, SYNONYM2, …).

  ![Full-width image](/assets/img/blog/tutorials/custom-slot-types/custom-slot-types-4.png){:.lead data-width="800" data-height="100"}
  Bulk edit
  {:.figure}

* **Entering one by one your values:**
  To enter a value manually is as easy as fill the field you have in that screen and then click enter. After entering this new value you can set up the ID and the synonims (**which is the most important part of the custom value!!!**)

  ![Full-width image](/assets/img/blog/tutorials/custom-slot-types/custom-slot-types-3.png){:.lead data-width="800" data-height="100"}
  Creating a slot
  {:.figure}
  

Here you have an example with all pokemons:

![Full-width image](/assets/img/blog/tutorials/custom-slot-types/custom-slot-types-5.png){:.lead data-width="800" data-height="100"}
List of Pokemons
{:.figure}

I have created for you some custom values if you want to reuse. You can find them in this [post](/alexa/2020-03-01-alexa-useful-custom-slots-types)

That's all folks! I hope it will be useful! If you have any doubts or questions do not hesitate to contact me or put a comment below!