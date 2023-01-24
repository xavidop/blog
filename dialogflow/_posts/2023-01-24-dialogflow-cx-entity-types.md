---
layout: post
title: Dialgflow CX Entity Types (English)
description: >
  What are entity types in Dialogflow CX?
image: /assets/img/blog/post-headers/dialogflow-entity-types.jpg
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [dialogflow]
tags:
  - dialogflow
keywords:
  - dialogflow
  - dialogflowcx
  - cxcli
  - conversationalai

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

# Dialogflow CX Entity Types

## Previous Requisites

Here are the technologies used in this project
1. Google Cloud Account - [Sign up here for free](https://cloud.google.com/)
2. Dialogflow API enabled - [How to enable it](https://cloud.google.com/dialogflow/cx/docs/reference)
3. Dialogflow CX CLI - [Install and configure Dialogflow CX CLI](https://cxcli.xavidop.me/)

## What is this?

![Full-width image](/assets/img/blog/tutorials/dialogflow-entity-types/entity-type.png){:.lead data-width="800" data-height="100"}
Entity Type
{:.figure}

One of the most important parts of NLU is the Entity types or entities. These are the key information in a text, such as names, dates, products, organizations, places, or anything we want to extract from the text. We call this concept “Entities”. For example, let's take a look at the `order_intent` intent:
1. I want a pizza
2. I want 3 cokes
3. Give me two burgers

As you can see in the example above, we can extract 2 Entity Types: `quantity` and `order_type`. We can extrapolate the utterances above like this:
1. I want {quantity} {order_type}
2. Give me {quantity} {order_type}

We can think about Entity Types as variables as well.

It is a good practice to test your training phrases with your end users. This will allow you to detect missing training phrases in your NLU.

## Dialogflow Console

Dialogflow Console is a web interface where you can design your conversations by creating agents and within an agent, creating flows, intents, entity types, etc. On the Dialogflow Console, you can create and interact easily with your intent. To do that you just need to go to the Dialogflow CX Console: [https://dialogflow.cloud.google.com/cx](https://dialogflow.cloud.google.com/cx). This is what it looks like:

![Full-width image](/assets/img/blog/tutorials/dialogflow-agents/console.png){:.lead data-width="800" data-height="100"}
Dialogflow CX Console
{:.figure}

You will find your entity types in the **Manage** tab and the clicking in the **entity types** section:

![Full-width image](/assets/img/blog/tutorials/dialogflow-entity-types/console-entity-type.png){:.lead data-width="800" data-height="100"}
Dialogflow CX Entity types
{:.figure}

With the Dialogflow CX Console, you can do:
1. Create an entity type:
   1. When you create an entity type, you can add synonyms.
2. Delete an entity type
3. Train and validate your NLU

When you are creating an entity type, you can specify whether or not it has synonyms or if it is a regexp entity. If you choose the regexp option, the classifier will use a regular expression instead of synonyms during query classification.

These are the Entity Types that you can use in your intents:
1. Custom entities: entity types created by the developer.
2. System entities: the ones available in dialogflow CX (number, dates, colours, etc.).
3. Session entities: these are dynamic entities that can be extended during the users' sessions.
4. Regexp entities: entities that are a regular expression.

Whenever you create, modify or delete an entity type it is important to re-train your Dialogflow CX flows. This will re-train your NLU. By doing this your bot will "understand you" including your latest changes.

## Dialogflow CX CLI

The [Dialoglfow CX CLI](https://cxcli.xavidop.me/) or `cxcli` is a Command Line Interface Tool that you can use to interact with your Dialogflow CX projects in a terminal. It is an open-source project created by [Xavier Portilla Edo](https://xavidop.me/). With the `cxcli` you can interact easily with your Dialogflow CX entity types.

All the commands that you have available in the `cxcli` to interact with your entity types are located down the `cxcli entity-type` command.

### Create

You can [create](https://cxcli.xavidop.me/entitytypes/create) an entity type using this tool. This command has this usage:

```sh
cxcli entity-type create [entity-type-name] [parameters]
```

You can find the full usage [here](https://cxcli.xavidop.me/cmd/cxcli_entity-type_create). It is important to explain the `--entities` parameter. It is a list of the entities with their synonyms, comma separated. This parameter has the following format: 
```
entity1@synonym1|synonym2,entity2@synonym1|synonym2
```

Here you have an example: `pikachu@25|pika,charmander@3`


This a simple example of the `cxcli entity-type create` command:

```sh
cxcli entity-type create order_type --entities "pizza@piza|pizzas,burguer@hamburguer|burguers" --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
```

The command above will give you an output like this one:

```sh
$ cxcli entity-type create order_type --entities "pizza@pizza|pizzas,coke@coke|cokes" --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
INFO Entity Type created with id: projects/test-cx-346408/locations/us-central1/agents/40278ea0-c0fc-4d9a-a4d4-caa68d86295f/entityTypes/457a451d-f5ce-47da-b8dc-16b17d874a5d 
```

You can see the `order_type` entity type on the Dialogflow CX Console:

![Full-width image](/assets/img/blog/tutorials/dialogflow-entity-types/console-entity-type-created.png){:.lead data-width="800" data-height="100"}
order_type
{:.figure}

### Delete

Also, an entity type can be [deleted](https://cxcli.xavidop.me/entitytypes/delete). The usage of this command is pretty much similar to the one used for creating an entity type:

```sh
cxcli entity-type delete [entity-type-name] [parameters]
```

You can find the full usage [here](https://cxcli.xavidop.me/cmd/cxcli_entity-type_delete). This a simple example of the `cxcli entity-type delete` command:

```sh
cxcli entity-type delete pokemon --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
```

The command above will give you an output like this one:

```sh
$ cxcli entity-type delete pokemon --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
INFO Entity Type deleted                 
```
                        
## Resources

If you want to check the full usage of the `cxcli entity-type` command, please refer to this [page](https://cxcli.xavidop.me/cmd/cxcli_entity-type/).

If you want to learn more about Dialogflow CX entity types, check the [official documentation](https://cloud.google.com/dialogflow/cx/docs/concept/entity).

## Conclusion 

This was a basic tutorial to learn what is a Dialogflow CX Entity Type.
As you have seen in this example, creating entity types and evolving your NLU in Dialogflow CX either with the console or the `cxcli` is very easy!

I hope this tutorial will be useful to you.

That's all folks!

Happy coding!