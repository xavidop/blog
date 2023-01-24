---
layout: post
title: Dialogflow CX Intents (English)
description: >
  An introduction about dialogflow CX NLU and its intents
image: /assets/img/blog/post-headers/dialogflow-intents.jpg
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

# Dialogflow CX Intents

## Previous Requisites

Here are the technologies used in this project
1. Google Cloud Account - [Sign up here for free](https://cloud.google.com/)
2. Dialogflow API enabled - [How to enable it](https://cloud.google.com/dialogflow/cx/docs/reference)
3. Dialogflow CX CLI - [Install and configure Dialogflow CX CLI](https://cxcli.xavidop.me/)

## What is this?

![Full-width image](/assets/img/blog/tutorials/dialogflow-intents/intent.png){:.lead data-width="800" data-height="100"}
Intent
{:.figure}

Before start talking about intents, it is important to understand what is NLU. Natural Language Understanding (NLU) is a subset of Natural Language Processing (NLP). It helps a "machine" to be able to understand human language.
In Dialogflow CX this is an important part since it will help to predict the user's intention and allow us to act in a more "smart" way, and avoid the already typical: "I did not understand you, could you repeat it?". We call these intentions, proposals or user requests, which the machine must classify. These are the "Intents". Each intent has training phrases. For example the `welcome_intent` intent can have these 3 training phrases:
1. Hi
2. Hello
3. What's up!

As you can see in the example above, our intention with the `welcome_intent` intent is to start a conversation when a user says any of these training phrases. An intent can have multiple entities. The entities are going to be explained in a future article.

Or just to showcase another example, if we take a look at the image above, we will see the `get_info` intent. This intent has multiple training phrases as well:
1. tell me info about pikachu
2. tell me information about pikachu
3. info pikachu
4. pikachu

So we can request information about a certain Pokemon in multiple ways. In this example, `pikachu` is an entity.

It is a good practice to test your training phrases with your end users. This will allow you to detect missing training phrases in your NLU.

## Dialogflow Console

Dialogflow Console is a web interface where you can design your conversations by creating agents and within an agent, creating flows, intents, entity types, etc. On the Dialogflow Console, you can create and interact easily with your intent. To do that you just need to go to the Dialogflow CX Console: [https://dialogflow.cloud.google.com/cx](https://dialogflow.cloud.google.com/cx). This is what it looks like:

![Full-width image](/assets/img/blog/tutorials/dialogflow-agents/console.png){:.lead data-width="800" data-height="100"}
Dialogflow CX Console
{:.figure}

You will find your intents in the **Manage** tab and the clicking in the **intents** section:

![Full-width image](/assets/img/blog/tutorials/dialogflow-intents/console-intent.png){:.lead data-width="800" data-height="100"}
Dialogflow CX Intent
{:.figure}

With the Dialogflow CX Console you can do:
1. Create an intent:
   1. When you create an intent, you can add training phrases and add a description or labels to that intent. You can add Entity Types as well to an intent.
2. Delete an intent
3. Train and validate your NLU

Whenever you create, modify or delete an intent it is important to re-train your Dialogflow CX flows. This will re-train your NLU. By doing this your bot will "understand you" including your latest changes.

## Dialogflow CX CLI

The [Dialoglfow CX CLI](https://cxcli.xavidop.me/) or `cxcli` is a Command Line Interface Tool that you can use to interact with your Dialogflow CX projects in a terminal. It is an open-source project created by [Xavier Portilla Edo](https://xavidop.me/). With the `cxcli` you can interact easily with your Dialogflow CX intents.

All the commands that you have available in the `cxcli` to interact with your intent are located down the `cxcli intent` command.

### Create

You can [create](https://cxcli.xavidop.me/intents/create) an intent using this tool. This command has this usage:

```sh
cxcli intent create [intent-name] [parameters]
```

You can find the full usage [here](https://cxcli.xavidop.me/cmd/cxcli_intent_create). It is important to explain the `--training-phrases` parameter. Why? because it is the most important parameter. It is a list of the training phrases for this intent, comma separated. For the entities used in this intent, add `@entity-type` to the word in the training phrase. This is the format: 
```
word@entity-type
```

Here you have an example: `hello, hi how are you today@sys.date, morning!`

This a simple example of the `cxcli intent create` command:

```sh
cxcli intent create test_intent --training-phrases "hello, hi how are you today@sys.date, morning"  --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
```

The command above will give you an output like this one:

```sh
$ cxcli intent create test_intent --training-phrases "hello, hi how are you today@sys.date, morning"  --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
INFO Intent created with id: projects/test-cx-346408/locations/us-central1/agents/40278ea0-c0fc-4d9a-a4d4-caa68d86295f/intents/a7870357-e942-43dd-99d2-4de8c81a3c09 
```

You can see the `test_intent` on the Dialogflow CX Console:

![Full-width image](/assets/img/blog/tutorials/dialogflow-intents/console-intent-created.png){:.lead data-width="800" data-height="100"}
test_intent
{:.figure}

### Delete

Also, an intent can be [deleted](https://cxcli.xavidop.me/intents/delete). The usage of this command is pretty much similar to the one used for creating an intent:

```sh
cxcli intent delete [intent-name] [parameters]
```

You can find the full usage [here](https://cxcli.xavidop.me/cmd/cxcli_intent_delete). This a simple example of the `cxcli intent delete` command:

```sh
cxcli intent delete test_intent --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
```

The command above will give you an output like this one:

```sh
$ cxcli intent delete test_intent --agent-name test-agent --project-id test-cx-346408 --location-id us-central1
INFO Intent deleted                 
```
                        
## Resources

If you want to check the full usage of the `cxcli intent` command, please refer to this [page](https://cxcli.xavidop.me/cmd/cxcli_intent).

If you want to learn more about Dialogflow CX intents, check the [official documentation](https://cloud.google.com/dialogflow/cx/docs/concept/intent).

## Conclusion 

This was a basic tutorial to learn what is a Dialogflow CX Intent.
As you have seen in this example, creating intents and evolving your NLU in Dialogflow CX either with the console or the `cxcli` is very easy!

I hope this tutorial will be useful to you.

That's all folks!

Happy coding!