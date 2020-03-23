---
layout: post
title: Alexa Skill con Spring Boot
image: /assets/img/blog/post-headers/alexa-springboot.jpg
description: >
  Alexa Skill desarrollada en Java usando Spring Boot
noindex: true
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - springboot
  - spring
  - servlet
  - java
  - howto
  - skill
lang: es
---

Puedes crear una custom Skill para Alexa extendiendo un servlet que acepta solicitudes y envía respuestas al servicio Alexa en la nube.

# Alexa Skill con Spring Boot


En este post explicaré cómo construir una Alexa Skill con Spring Boot junto con un ejemplo Http Servlet mapping.
 
El servlet mapping se puede lograr mediante el uso de la clase `ServletRegistrationBean` en Spring Boot, así como también mediante anotaciones de Spring.
En este ejemplo, vamos a utilizar la clase `ServletRegistrationBean` para registrar el Servlet de Alexa como un Spring bean.

## Requisito previo

Aquí tienes las tecnologías utilizadas en este proyecto.
1. Java 1.8
2. Alexa Skill Kit 2.29.0
3. Spring Boot 2.5.0.RELEASE
4. Maven 3.6.1
5. IntelliJ IDEA
6. ngrok

## Estructura del proyecto
A continuación, tienes la estructura de este proyecto:

```bash
  ├────src
  │    └───main
  │        ├───java
  │        │   └───com
  │        │       └───xavidop
  │        │           └───alexa
  │        │               ├───configuration
  │        │               ├───handlers
  │        │               ├───properties
  │        │               └───servlet
  │        │
  │        └───resources
  │                application.properties
  │                log4j2.xml
  └── pom.xml
```

Estas son las principales carpetas y archivos de este proyecto:
* **configuration**: esta carpeta tiene la clase `WebConfig` que registrará el Servlet Http de Alexa.
* **handlers**: todos los Alexa handlers. Son los que procesarán todas las request de Alexa.
* **properties**:aquí puede encontrar la clase `Properties Utils` que lee el archivo de configuración de Spring `application.properties`.
* **servlet**: el punto de entrada de las requests POST está aquí. Éste es el `AlexaServlet`.
* **resources**: configuración de Alexa, Spring y Log4j2.
* **pom.xml**: dependencias del proyecto.

## Dependencias Maven

Estas son las dependencias utilizadas en este ejemplo. Puedes encontrarlos en el archivo `pom.xml`:

* Spring Boot:
```xml
   <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.2.5.RELEASE</version>
  </parent>
```

* Alexa Skill Kit:
```xml
  <dependency>
      <groupId>com.amazon.alexa</groupId>
      <artifactId>ask-sdk</artifactId>
      <version>2.29.0</version>
  </dependency>
```

* Spring Boot starter web:
```xml
  <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
  </dependency>
```

* Log4j2:
```xml
  <dependency>
      <groupId>org.apache.logging.log4j</groupId>
      <artifactId>log4j-api</artifactId>
      <version>2.13.1</version>
  </dependency>
  <dependency>
      <groupId>org.apache.logging.log4j</groupId>
      <artifactId>log4j-core</artifactId>
      <version>2.13.1</version>
  </dependency>
```

* Spring Boot Maven build plug-in:
```xml
  <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
```

## El Http Servlet de Alexa

Gracias al soporte de Alexa a los Http Servlet que puedes encontrar en el [Repositorio GitHub oficial de Alexa](https://github.com/alexa/alexa-skills-kit-sdk-for-java/tree/2.0.x/ask-sdk-servlet-support). Este proyecto incluye la clase  `SkillServlet`  que nos permite registrarlo dentro de nuestra aplicación Spring Boot usando la clase `ServletRegistrationBean` como puedes ver más abajo.

La clase `SkillServlet` registra la instancia de la Skill del objeto SkillBuilder y proporciona un método doPost que es responsable de la deserialización de la request entrante, la verificación de la solicitud de entrada antes de invocar la Skill y la serialización de la respuesta generada.

Nuestra clase `AlexaServlet`, ubicada en la carpeta `servlet`, extiende `SkillServlet` y, después de registrarla como servlet, será nuestro principal punto de entrada.

Echa un vistazo a la clase `AlexaServlet`:

```java
  public class AlexaServlet extends SkillServlet {

      public AlexaServlet() {
          super(getSkill());
      }

      private static Skill getSkill() {
          return Skills.standard()
                  .addRequestHandlers(
                          new CancelandStopIntentHandler(),
                          new HelloWorldIntentHandler(),
                          new HelpIntentHandler(),
                          new LaunchRequestHandler(),
                          new SessionEndedRequestHandler())
                  // Add your skill id below
                  //.withSkillId("")
                  .build();
      }

  }
```

Recibirá todas las solicitudes POST de Alexa y las enviará al handler específico, ubicado en las carpetas `handlers`, que puede ejecutar esa solicitud.

## Registrando el Http Servlet de Alexa como Spring Beans usando ServletRegistrationBean

`ServletRegistrationBean` se utiliza para registrar Servlets. Necesitaremos crear un bean de esta clase en `WebConfig`, nuestra clase de configuración de Spring.
Los métodos más relevantes de la clase `ServletRegistrationBean` que utilizamos en este proyecto son:
* `setServlet`: establece el servlet que se registrará. En nuestro caso, `AlexaServlet`.
* `addUrlMappings`: agrega URL mappings para el Servlet. Nosotros asignaremos la URL `/ alexa`.
* `setLoadOnStartup`: Establece prioridad para cargar el Servlet en el inicio. No es tan importante como los dos métodos anteriores porque solo tenemos un Servlet en este ejemplo.

La clase `WebConfig` es donde registramos el Servlet Http de Alexa. 
Así es como registramos el servlet:
```Java
  @Bean
  public ServletRegistrationBean<HttpServlet> alexaServlet() {

      loadProperties();

      ServletRegistrationBean<HttpServlet> servRegBean = new ServletRegistrationBean<>();
      servRegBean.setServlet(new AlexaServlet());
      servRegBean.addUrlMappings("/alexa/*");
      servRegBean.setLoadOnStartup(1);
      return servRegBean;
  }
```
## Configurando properties

El servlet debe cumplir ciertos requisitos para manejar las solicitudes enviadas por Alexa y cumplir con los estándares de interfaz del Alexa Skill Kit.
Para más información, mira la sección "Host a Custom Skill as a Web Service" en la [Documentación oficial del Alexa Skills Kit](https://developer.amazon.com/es-ES/docs/alexa/custom-skills/host-a-custom-skill-as-a-web-service.html).

En este ejemplo, tienes 4 properties que puedes configurar en el archivo `application.properties`:

* **server.port**: el puerto que usará la aplicación Spring Boot.
* **com.amazon.ask.servlet.disableRequestSignatureCheck**: activar/desactivar la seguridad.
* **com.amazon.speech.speechlet.servlet.timestampTolerance**: el gap máximo entre el timestamp de la solicitud y la hora actual de ejecución. En milisegundos.
* **javax.net.ssl.keyStore**: Si la primera property se establece a `false`, entonces se debe especificar el path completo al fichero KeyStore.
* **javax.net.ssl.keyStorePassword**: Si la primera property se establece a `false`, entonces se debe especificar la contraseña del keystore.

## Build de la Skill con Spring Boot

Al ser un proyecto maven, se puede compilar la aplicación Spring Boot ejecutando este comando:

```bash
  mvn clean package
```

## Ejecutar la Skill con Spring Boot

Ejecuta la clase AlexaSkillAppStarter.java como aplicación Java, si estás en eclipse, puedes ir a Ejecutar → Ejecutar como → Aplicación Java

O también puedes usar:
```bash
mvn spring-boot:run
```

O, si usas IntelliJ IDEA, puedes hacer clic derecho en el método Main de la clase `AlexaSkillAppStarter`:

  ![Full-width image](/assets/img/blog/tutorials/alexa-springboot/debug.png){:.lead data-width="800" data-height="100"}
Ejecutando en IntelliJ IDEA
  {:.figure}

Después de ejecutar la clase principal, puedes enviar requests POST de Alexa a http://localhost:8080/alexa.

## Debuggear la Skill con Spring Boot

Para debuggear la aplicación Spring boot como aplicación Java, si estás en eclipse, puedes ir a Debug → Debug as → Java Application

O, si usas IntelliJ IDEA, puedes hacer clic derecho en el método Main de la clase `AlexaSkillAppStarter`:

  ![Full-width image](/assets/img/blog/tutorials/alexa-springboot/debug.png){:.lead data-width="800" data-height="100"}
Debuggeando en IntelliJ IDEA
  {:.figure}

Después de ejecutar la clase principal en modo debug, puedes enviar requests POST de Alexa a http://localhost:8080/alexa y debuggear tu skill.

## Testear requests localmente

Estoy seguro de que ya conoces la famosa herramienta llamada [Postman](https://www.postman.com/). Las API REST se han convertido en el nuevo estándar para proporcionar una interfaz pública y segura para nuestros servicios. Aunque REST se ha vuelto omnipresente, no siempre es fácil probarlo. Postman, hace que sea más fácil probar y administrar las API REST HTTP. Postman nos brinda múltiples funciones para importar, probar y compartir APIs, lo que te ayudará a ti y a tu equipo a ser más productivos a largo plazo.

Después de ejecutar tu aplicación, tendrás un endpoint disponible en http://localhost:8080/alexa. Con Postman puedes emular cualquier request de Alexa.

Por ejemplo, puedes testear un `LaunchRequest`:

```json
  {
    "version": "1.0",
    "session": {
      "new": true,
      "sessionId": "amzn1.echo-api.session.[unique-value-here]",
      "application": {
        "applicationId": "amzn1.ask.skill.[unique-value-here]"
      },
      "user": {
        "userId": "amzn1.ask.account.[unique-value-here]"
      },
      "attributes": {}
    },
    "context": {
      "AudioPlayer": {
        "playerActivity": "IDLE"
      },
      "System": {
        "application": {
          "applicationId": "amzn1.ask.skill.[unique-value-here]"
        },
        "user": {
          "userId": "amzn1.ask.account.[unique-value-here]"
        },
        "device": {
          "supportedInterfaces": {
            "AudioPlayer": {}
          }
        }
      }
    },
    "request": {
      "type": "LaunchRequest",
      "requestId": "amzn1.echo-api.request.[unique-value-here]",
      "timestamp": "2020-03-22T17:24:44Z",
      "locale": "en-US"
    }
  }

```

Ten cuidado con el campo timestamp de la request para cumplir con la propiedad `com.amazon.speech.speechlet.servlet.timestampTolerance`.

## Testear requests directamente desde el cloud de Alexa

ngrok es una herramienta genial y liviana que crea un túnel seguro en tu máquina local junto con una URL pública que se puede usar para navegar por tu web en local o API.

Cuando se está ejecutando ngrok, escucha en el mismo puerto en el que se está ejecutando el servidor web local y envía solicitudes externas a tu máquina local.

Veamos como de fácil es publicar nuestra Skill ejecutandose en local para que el cloud de Alexa nos envíe requests. 
Digamos que está ejecutando tu servidor web local en el puerto 8080. En la terminal, escribiría: `ngrok http 8080`. Esto comienza a escuchar a ngrok en el puerto 8080 y crea el túnel seguro:

  ![Full-width image](/assets/img/blog/tutorials/alexa-springboot/tunnel.png){:.lead data-width="800" data-height="100"}
túnel con ngrok
  {:.figure}

Entonces ahora vas a la [Alexa Developer console](https://developer.amazon.com/alexa/console/ask), navegar a tu Skill > endpoints > https, agregas la URL https generada anteriormente seguido de /alexa. Por ejemplo: https://fe8ee91c.ngrok.io/alexa.

Selecciona la opción "My development endpoint is a sub-domain...." desde el menú desplegable y haga clic en Save endpoint en la parte superior de la página.

Dirígete al tab Test en la Alexa Developer Console y lanza tu skill.

La Alexa Developer Console enviará una solicitud HTTPS al endpoint ngrok (https://fe8ee91c.ngrok.io/alexa) que lo redirigirá a tu Skill ejecutándose en el servidor Spring Boot en http://localhost:8080/alexa.


## Conclusión 

Este ejemplo puede ser útil para todos aquellos desarrolladores que no quieran alojar su código en la nube o no quieran usar las funciones de AWS Lambda. Esto no es un problema ya que, como has visto en este ejemplo, Alexa te da la posibilidad de crear Skills de diferentes maneras. Espero que este proyecto de ejemplo te sea útil.

Puedes encontrar el código en mi [**Github**](https://github.com/xavidop/alexa-java-springboot-helloworld)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
