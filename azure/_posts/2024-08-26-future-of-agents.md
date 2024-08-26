---
layout: post
title: The Evolution of Conversational AI. Blending Determinism with Dynamism (English)
description: >
  Learn how the future of conversational AI lies in the seamless integration of deterministic workflows and dynamic, creative responses.
image: /assets/img/blog/post-headers/future-of-agents.png
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [gcp]
tags:
  - azure
  - gcp
keywords:
  - openai
  - ollama
  - generative-ai
  - azure
  - vertex
  - vertex-ai
  - gcp
  - google-cloud-platform
  - google-cloud

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

Conversational AI agents have come a long way from their early days of simple, scripted interactions. With the explosion of large language models (LLMs) like GPT-3, Gemini and beyond, the landscape of human-computer interaction is undergoing a significant transformation. 

These AI agents are increasingly expected to mimic human-like interactions, which demands a delicate balance between deterministic (convergent) workflows and dynamic, creative responses (divergent). This dual approach is redefining how these agents function across various domains, including education, customer service, and personal assistance.

## The Need for Determinism in Conversational AI

At the core of any effective and complex conversational AI agent lies a structured, deterministic flow. Determinism ensures that the agent follows a predefined path (happy path), making decisions based on set criteria and providing predictable outcomes and accomplished the goals of that specific agent. This is particularly crucial in educational contexts, such as language learning, where the agent must track a user's progress and deliver content in a logical sequence.

Let's consider an AI agent designed to teach Spanish to non-Spanish speakers. The learning process must be carefully structured to ensure that the student builds their knowledge incrementally. The agent needs to assess where the student is in their learning journey and determine the next appropriate step, whether it's introducing new vocabulary, reinforcing grammar rules, or practicing conversation skills. In this scenario, the agent operates within a deterministic framework, governed by **workflows** that handle the control of its main actions.

Platforms like Voiceflow, Langflow, and Dialogflow CX are instrumental in building these deterministic workflows. They allow developers to design conversational experiences where each interaction is mapped out in advance. This ensures that the AI agent can reliably guide the user through the learning process, providing a sense of progression and achievement. In this deterministic mode, the agent is less about simulating human conversation and more about delivering structured, purposeful instruction.

## The Role of Dynamism and Creativity

However, not all interactions can or should be rigidly scripted. Human conversations are inherently dynamic, filled with nuances, unexpected questions, and shifts in context. To address this, modern conversational AI agents are increasingly incorporating LLMs to introduce a level of creativity and natural interaction that deterministic workflows cannot provide.

Returning to the example of the Spanish language learning agent, while the core lessons may be delivered through a deterministic flow, there comes a point where the conversation might need to become more fluid and adaptable. For instance, after completing a structured lesson, the agent could transition to a more open-ended conversation managed by an LLM. Here, the AI could engage the learner in a casual chat in Spanish, responding to any topic the learner introduces, providing explanations, and correcting mistakes in a manner that feels more like conversing with a native speaker than interacting with a machine.

This dynamic mode is powered by the LLM's ability to generate responses that are contextually relevant and varied, offering a more natural and engaging user experience. It allows the AI to handle the unpredictable nature of human interaction, filling in gaps where deterministic systems might falter.

## The Synergy of Determinism and Dynamism

The future of conversational AI lies in the seamless integration of these two approaches. Deterministic workflows provide the structure necessary for achieving specific goals, ensuring that users are guided efficiently and effectively through complex processes. At the same time, the dynamism introduced by LLMs brings the interaction to life, making it more engaging and human-like.

In practical terms, this means designing AI agents that can transition smoothly between these modes. For example, an agent could start a conversation with a user in a deterministic mode, collecting necessary information and performing specific tasks. Once these tasks are complete, the agent could switch to a more dynamic mode, allowing the conversation to flow naturally and adapt to the user's needs and preferences.

The integration of these approaches can significantly enhance the user experience, making AI agents not just tools for completing tasks, but also companions capable of engaging, meaningful interactions. As these technologies continue to evolve, we can expect conversational AI to become even more sophisticated, blending the predictability of deterministic workflows with the creativity and adaptability of LLMs to create truly human-like interactions.

## Large Language Models and the Future of Conversational AI

Large Language Models have revolutionized the field of conversational AI, enabling agents to generate text that is indistinguishable from human writing. But not only that, LLMs have been used to create a wide range of agents from chatbots to assisstants, tutors, etc. By giving to them intructions and data, they can perform a wide range of tasks. Such us for example, detect the correctness, sentiment, agressiveness of a text. This is what we called **Instructional AI**, a new way to interact with LLMs and make them perform specific tasks in conversational AI applications.

An example has been developed to showcase these capabilities. This project implements a simple language correctness detector that detects grammatical errors, sentiment, aggressiveness, and provides solutions for the errors in the text. The project will be part of a bigger conversational AI agent that helps users improve their language skills.

This is an input/output example of the project:
**Input:**
```json
{ language: "Spanish", text: "Yo soy enfadado" }
```

**Output:**
```
{
  result: {
    sentiment: 'angry',
    aggressiveness: 2,
    correctness: 7,
    errors: [
      "The correct form of the verb 'estar' should be used instead of 'ser' when expressing emotions or states."
    ],
    solution: 'Yo estoy enfadado',
    language: 'Spanish'
  }
}
```

The project can be found [here](https://github.com/xavidop/langchain-language-correctness-detector).

## Resources

- [Generative AI is new and exciting but conversation design principles are forever from Alessia Sachi](https://medium.com/google-cloud/generative-ai-is-new-and-exciting-but-conversation-design-principles-are-forever-193371489f99)

## Conclusion

The explosion of LLMs has brought a new dimension to conversational AI, making it possible to create agents that interact with humans in ways that are increasingly natural and engaging. However, the complexity of human interaction requires more than just creativity also demands structure and determinism. By combining deterministic workflows with the dynamic capabilities of LLMs, developers can create AI agents that not only perform tasks efficiently but also offer a level of interaction that feels genuinely human. Moreover, the integration of Instructional AI with LLMs is a new way to interact with them and make them perform specific tasks in conversational AI applications.

This blend of structure and creativity is the key to the next generation of conversational AI, where agents can guide, teach, and interact in ways that are both predictable and profoundly engaging.

Happy coding!