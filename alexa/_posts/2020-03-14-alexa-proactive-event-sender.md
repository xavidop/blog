---
layout: post
title:  Cliente Java para enviar Proactive Events
image: /assets/img/blog/post-headers/alexa-proactive-event-sender.jpg
description: >
  Cliente Java para enviar Proactive Events
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - proactive events
  - proactive event
  - event
  - events
  - java
  - howto
  - skill
lang: es
---
# Cliente Java de proactive events (notificaciones)

Este proyecto tiene como objetivo simplificar el envío de proactive events (notificaciones) a una skill desde un proceso externo desarrollado en Java.

Basándome en el video [De Cero a Héroe, Parte 13: Proactive Events Notifications](https://www.youtube.com/watch?v=COnuc-LX-1Y&t=714s) de [German Viscuso](https://twitter.com/germanviscuso?s=20) y el proyecto de Github de [Luca Rosellini](https://github.com/lucarosellini/proactive-events-standalone-sender) he creado este cliente Java para que sea fácil de enviar notificaciones desde cualquier backend basado en Java/Kotlin o por ejemplo, desde cualquier dispositivo Android.

<iframe width="560" height="315" src="https://www.youtube.com/embed/COnuc-LX-1Y" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

Esta libreria realiza las siguientes operaciones:
1. Obtiene un token de autenticación de Alexa mediante el uso del ```client_id``` y ```client_secret``` de la skill.
2. Utiliza el token obtenido en el paso anterior para las notificaciones *broadcast* a aquellos usuarios de la skill que tienen permisos a notificaciones en la aplicación Alexa. Envía eventos siguiendo el esquema [```AMAZON.MessageAlert.Activated```](https://developer.amazon.com/docs/smapi/schemas-for-proactive-events.html#message-alert).

## Agregar proactive events (notificaciones) a tu skill

Recuerda que si quieres enviar proactive events (notificaciones) a tu skill, debes modificar el manifest de la skilll (skill.json) para agregar permisos de notificación y declarar el schema(s) de los proactive events (notificaciones) que su skill puede enviar. Usando SMAPI, debes:

1. Agregar el objeto ```permissions``` al ```manifiest``` de la skill (skill.json):


```json
    "permissions": [
        {
            "name": "alexa::devices:all:notifications:write"
        }
    ]
```

2. Agregar el objeto ```events``` al ```manifiest``` de la skill:


```json
    "events": {
      "publications": [
        {
          "eventName": "AMAZON.MessageAlert.Activated"
        }
      ],
      "endpoint": {
        "uri": "** TODO: REPLACE WITH YOUR Lambda ARN after created **"
      },
      "subscriptions": [
        {
          "eventName": "SKILL_PROACTIVE_SUBSCRIPTION_CHANGED"
        }
      ]
    }
```

3. volver a desplegar la skill:


```bash
   ask deploy -t skill
```

Si quieres que la skill acpete más de un schema, simplemente agrégalos a ```events.publications```  y recuerda cambiar el tipo de evento en la clase ```Event``` del package ```com.xavidop.alexa.model.event```.

El proceso se describe más a fondo en la [documentación oficial de la API de proactive events de Alexa](https://developer.amazon.com/docs/smapi/proactive-events-api.html#onboard-smapi).

Puede encontrar un ejemplo de cómo configurar una skill para proactive events en el repositorio oficial de Gihub de Alexa: https://github.com/alexa/alexa-cookbook/tree/master/feature-demos/skill-demo-proactive- eventos

## Prerrequisitos

Necesitas al menos Java> = 1.8 para ejecutar el código y Maven para descargar las dependencias.


## Instalar

Para descargar las dependencias del proyecto, simplemente añade esta dependencia de maven en el ```pom.xml``` del proyecto:

```xml
    <dependency>
      <groupId>com.xavidop.alexa</groupId>
      <artifactId>alexa-proactive-event-sender</artifactId>
      <version>LATEST</version>
    </dependency>
```

## Cómo usarlo

Después de agregar la dependencia, puede usar el cliente de la siguiente manera:

```java
    String clientId = "YOUR-CLIENT";
    String secretId = "YOUR-SECRET";

    AlexaProactiveEventSenderClient client = new AlexaProactiveEventSenderClient(clientId, secretId);

    ProactiveEvent event = new ProactiveEvent();
    event.getEvent().getPayload().getMessageGroup().getCreator().setName("Test");

    URLRegion urlRegion = new URLRegion();
    urlRegion.setRegion(Region.NA);
    urlRegion.setEnvironment(Environment.DEV);

    client.sendProactiveEvent(event, urlRegion);
```
    
* ```Environment```: los proactive events se puede enviar a los endpoints de las skills en estado ```live``` o ```development```. Los valores permitidos son ``` DEV``` y ```PRO```.
* ```Región ```: identifica la región del endpoint de Alexa que se utilizará para enviar proactive events. Los valores permitidos son ```EU``` (Europa), ```NA``` (Norteamérica) y ```FE``` (Oriente). ** Recuerda **: si sus usuarios estan en NA y está enviando proactive events a través del endpoint de la UE, los usuarios ubicados en NA no recibirán ninguna notificación.

Estos son los valores por defecto de un proactive events cuando lo creas:

```json
    {
        "timestamp": "",
        "referenceId": "UUID-AUTOGENERATED",
        "expiryTime": "",
        "event": {
          "name": "AMAZON.MessageAlert.Activated",
          "payload": {
            "state": {
              "status": "UNREAD",
              "freshness": "NEW"
            },
            "messageGroup": {
              "urgency": "URGENT",
              "creator": {
                "name": ""
              },
              "count": 1
            }
          }
        },
        "relevantAudience": {
            "type": "Multicast",
            "payload": {}
        }
    }
```

El código y la librería la teneis disponible en mi [**Github**](https://github.com/xavidop/alexa-proactive-event-sender)

¡Eso es todo!

Happy coding!