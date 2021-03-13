---
layout: post
title: Alexa Skill Auto-Deployer
image: /assets/img/blog/post-headers/alexa-skill-autodeployer.jpg
description: >
   Despliegue automático de un template de una Alexa Skill
comments: true
author: xavi
kate: hl markdown;
categories: [alexa]
tags:
  - alexa
keywords:
  - alexa
  - lambda
  - docker
  - ask
  - devops
  - howto
  - skill
lang: es
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}


Imagina que encuentras un template de una skill de Alexa en Internet y quieres probarla de inmediato.

# Alexa Skill Auto-Deployer

Esto es posible gracias a esta nueva herramienta llamada Alexa Skill Auto-Deployer.
Los pasos que ejecuta esta tool se automatizan utilizando el sistema de integración continua circleCI y se ejecutan utilizando su API REST oficial.

## Requisitos previos

Aquí tienes las tecnologías utilizadas en este proyecto
1. ASK CLI - [Instalar y configurar ASK CLI](https://developer.amazon.com/es-ES/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html)
2. Cuenta en CircleCI - [Registrate aquí](https://circleci.com/)
3. Visual Studio Code

## ASK CLI (Alexa Skill Kit CLI)

La Alexa Skills Kit Command Line Interface (ASK CLI) es una herramienta que nos permite administrar nuestras Skills de Alexa y los recursos relacionados, como las funciones de AWS Lambda.
Con la ASK CLI, tenemos acceso a la Skill Management API, que nos permite administrar las Skills de Alexa programáticamente desde la línea de comandos.
Usaremos esta herramienta para desplegar automáticamente nuestro template de una Skill de Alexa. ¡Empecemos!

### Instalación

Necesitamos instalar la ASK CLI y algunas otras herramientas de bash como `git`,`expect` o `curl`. No os preocupeis, os he preparado una imagen de Docker donde están todas esas herramientas [incluidas](https://hub.docker.com/repository/docker/xavidop/alexa-ask-aws-cli).
Usaremos esta imagen Docker como ejecutor principal en todos los pasos del pipeline de CircleCI.

## CircleCI

CircleCi es una de las plataformas de CI/CD más potentes y utilizadas del mundo. CircleCI se integra con GitHub, GitHub Enterprise y Bitbucket. En cada commit, CircleCI crea y ejecuta un pipeline. CircleCI ejecuta automáticamente nuestro pipeline en un contenedor o máquina virtual, lo que nos permite testear cada commit.
Además, tiene una API muy potente que usaremos en este tutorial.

## Proceso de automatización

Expliquemos job por job lo que está sucediendo en este proceso automático.

  ![Full-width image](/assets/img/blog/tutorials/alexa-skill-autodeployer/pipeline.png){:.lead data-width="800" data-height="100"}
CircleCI Pipeline
  {:.figure}

### Configurar los parámetros

En primer lugar, debemos de tener en cuneta que vamos a utilizar la API de CircleCI, por eso crearemos algunos parámetros para que este proceso sea reutilizable:

**NOTA:** Si queremos ejecutar con éxito todos los comandos de la ASK CLI, debemos  configurar estos parámetros correctamente:

* `ASK_ACCESS_TOKEN`: el Alexa Access Token generado previamente.
* `ASK_REFRESH_TOKEN`: el Alexa refresh token generado previamente también.
* `ASK_VENDOR_ID`: nuestro Vendor ID.
* `ASK_VERSION`: la versión de la ASK CLI que queremos usar. podéis encontrar todas las versiones disponibles [aquí](https://hub.docker.com/repository/docker/xavidop/alexa-ask-aws-cli/). Por defecto, 2.0.
* `GIT_TEMPLATE_URL`: el template de la Alexa Skill que queremos desplegar en nuestra cuenta de AWS. Este parámetro debe ser una URL de un repositorio de git. Ejemplo: https://github.com/alexa/skill-sample-nodejs-highlowgame.git
* `GIT_BRANCH`: la rama del repositorio git del template de la Alexa Skill que queremos desplegar. Por defecto, master.

Cómo obtener el variables relacionadas con la ASK se explica en [este post](https://dzone.com/articles/docker-image-for-ask-and-aws-cli-1)

Aquí tienes la sección de parámetros del pipeline de CircleCI:
```yaml
  parameters:
    ASK_ACCESS_TOKEN:
        type: string
        default: ""
    ASK_REFRESH_TOKEN:
        type: string
        default: ""
    ASK_VENDOR_ID:
        type: string
        default: ""
    ASK_VERSION:
        type: string
        default: "2.0"
    GIT_TEMPLATE_URL:
        type: string
        default: ""
    GIT_BRANCH:
        type: string
        default: "master"

```

### Configurar el ejecutor

Tenemos que definir en nuestro pipeline el ejecutor que vamos a ejecutar. Este ejecutor será una imagen Docker que hemos creado y hemos instalado la ASK CLI y la AWS CLI.

Este ejecutor también tiene más herramientas bash instaladas. Esta imagen Docker tiene una etiqueta por versión de ASK CLI, por lo que podemos especificar la versión en el parámetro del pipeline `ASK_VERSION`.

Podéis encontrar todas las versiones de ASK CLI disponibles [aquí](https://hub.docker.com/repository/docker/xavidop/alexa-ask-aws-cli/tags).

```yaml
  executors:
    ask-executor:
        docker:
        - image: xavidop/alexa-ask-aws-cli:<< pipeline.parameters.ASK_VERSION >>

```

### Checkout

Lo segundo que debemos hacer es descargar el código de esta herramienta porque hay algún script que vamos a ejecutar en este pipeline.

Una vez descargado, agregaremos los permisos de ejecución para que esos scripts puedan ejecutarse correctamente.
Finalmente, mantenemos todo el código descargado para poder reutilizarlo en los siguientes pasos.

```yaml
  checkout:
    executor: ask-executor
    environment:
      ASK_ACCESS_TOKEN: << pipeline.parameters.ASK_ACCESS_TOKEN >>
      ASK_REFRESH_TOKEN: << pipeline.parameters.ASK_REFRESH_TOKEN >>
      ASK_VENDOR_ID: << pipeline.parameters.ASK_VENDOR_ID >>
      ASK_VERSION: << pipeline.parameters.ASK_VERSION >>
      GIT_TEMPLATE_URL: << pipeline.parameters.GIT_TEMPLATE_URL >>
      GIT_BRANCH: << pipeline.parameters.GIT_BRANCH >>
    steps:
      - checkout
      - run: chmod +x -R ./create_hosted_skill_v2.sh
      - run: chmod +x -R ./create_hosted_skill_v1.sh
      - run: chmod +x -R ./deploy_hosted_skill_v1.sh
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project
            - .ask
```

### Creación de una Alexa Hosted Skill

Aquí es donde comienza la magia. Una vez que hayamos descargado todo el código, crearemos una nueva Alexa Hosted Skill.

Para este proceso usaremos la herramienta de bash `expect`. Esto se debe a que la creación de Alexa Hosted Skill requiere la interacción con un teclado.

Estos scripts funcionan así: esperarán algunas cadenas (`strings`) conocidas y luego, introducirán un valor o simplemente simularán presionar la tecla enter (`\r`) automáticamente. Dependiendo de la entrada necesaria en el proceso de creación de la Skill.

1. Para la versión de la **ASK CLI 1.x**:
   
```bash
#!/usr/bin/expect

set timeout 6000

spawn ask create-hosted-skill
expect "Please type in your skill name"
send -- "template\r"
expect "Please select the runtime"
send -- "\r"
expect "Alexa hosted skill is created. Do you want to clone the skill"
send -- "\r"
expect "successfuly cloned."
```

1. Para la versión de la **ASK CLI 2.x**:
   
```bash
#!/usr/bin/expect

set template [lindex $argv 0];

set timeout 6000

spawn ask new 
expect "Choose the programming language you will use to code your skill"
send -- "\r"
expect "Choose a method to host your skill's backend resources"
send -- "\r"
expect "Choose the default locale for your skill"
send -- "\r"
expect "Choose the default region for your skill"
send -- "\r"
expect "Please type in your skill name:"
send -- "${template}\r"
expect "Please type in your folder name"
send -- "../template\r"
expect "Hosted skill provisioning finished"
```

Los scripts anteriores crearán una Skill usando el template por defecto, els HelloWorld:

  ![Full-width image](/assets/img/blog/tutorials/alexa-skill-autodeployer/helloworld.png){:.lead data-width="800" data-height="100"}
HelloWorld Skill deployed
  {:.figure}

Una cosa importante aquí es que en este paso vamos a establecer las variables de entorno en el ejecutor que son necesarias para ejecutar el comando de la ASK CLI pra crear una Alexa Hosted. Los valores de estas variables de entorno serán los recibidos como parámetros.

Aquí podéis encontrar el código completo de este job:

```yaml
  create_hosted_skill:
    executor: ask-executor
    environment:
      ASK_ACCESS_TOKEN: << pipeline.parameters.ASK_ACCESS_TOKEN >>
      ASK_REFRESH_TOKEN: << pipeline.parameters.ASK_REFRESH_TOKEN >>
      ASK_VENDOR_ID: << pipeline.parameters.ASK_VENDOR_ID >>
      ASK_VERSION: << pipeline.parameters.ASK_VERSION >>
      GIT_TEMPLATE_URL: << pipeline.parameters.GIT_TEMPLATE_URL >>
      GIT_BRANCH: << pipeline.parameters.GIT_BRANCH >>
    steps:
      - attach_workspace:
          at: /home/node/
      - run: 
          name: create hosted skill
          command: |
            base_file=$(basename $GIT_TEMPLATE_URL)
            repo_folder=${base_file%.*} 
            
             if [ "$ASK_VERSION" == "1.0" ]; then
              ./create_hosted_skill_v1.sh $repo_folder
            else
             ./create_hosted_skill_v2.sh $repo_folder
            fi           
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project
            - .ask
```

### Descarga del template

Ahora tenemos una Alexa Hosted Skill (que es un HelloWorld) creada y desplegada con un ARN. Es hora de descargar elAlexa Skill Template que se nos ha introducido como parámetro. Este template debe ser un repositorio de git.
Podemos especificar la rama del repositorio de git del template. Si no se especifica, por defecto usaremos la rama `master`.

Cuando hayamos descargado el template de la Skill de Alexa, ahora tenemos que fusionar ambas Skills (la HelloWorld creada en el paso anterior y la descargada recientemente).
Esto se debe a que la plantilla de Alexa Skill no sabemos cómo está estructurada y qué "deployer" está usando (Alexa Hosted, CloudFormation o AWS-lambda). ¡Es por eso que estamos haciendo este paso que es el más importante!

Así que una vez hemos mencionado las razones para ejecutar este paso. Expliquemos paso a paso este job:
1. Lo primero que vamos a hacer es limpiar la Skill HelloWorld creada anteriormente. Esto significa eliminar el interaction model y su código lambda.
2. Luego, dependiendo de la Vvrsion de la ASK CLI que se haya elegido, migraremos toda la información del template de la Alexa Skill descargada a la HelloWorld Skill:
   1. Para la versión **ASK CLI 1.x**:
      1. Para esta versión que está en desuso, solo fusionamos las siguientes cosas del template:
         1. La información de publicación o publishing information.
         2. El código lambda.
      2. También eliminamos la carpeta `.ask` y `.git` del template descargado.
   2. Para la versión **ASK CLI 2.x**:
      1. Obtenemos toda la información los `endpoints` y las `regions` de la Helloworld Skill y colocamos esa información en el template descargado.
      2. Eliminamos la carpeta `.ask` y `.git` del template descargada.
      3. Luego reemplazamos el código lambda, el skill-package y todos los metadatos de la skill HelloWorld con los que se descargaron en la plantilla.

En este paso también configuramos las variables de entorno.

Aquí podéis encontrar el código completo de este job:

```yaml
  download_template:
    executor: ask-executor
    environment:
      ASK_ACCESS_TOKEN: << pipeline.parameters.ASK_ACCESS_TOKEN >>
      ASK_REFRESH_TOKEN: << pipeline.parameters.ASK_REFRESH_TOKEN >>
      ASK_VENDOR_ID: << pipeline.parameters.ASK_VENDOR_ID >>
      ASK_VERSION: << pipeline.parameters.ASK_VERSION >>
      GIT_TEMPLATE_URL: << pipeline.parameters.GIT_TEMPLATE_URL >>
      GIT_BRANCH: << pipeline.parameters.GIT_BRANCH >>
    steps:
      - attach_workspace:
          at: /home/node/
      #removing ask cli template lambda + skill-packages
      - run: 
          name: cleanup skill created
          command: | 
            rm -rf template/lambda/

            if [ "$ASK_VERSION" == "1.0" ]; then
              rm -rf template/models
            else
              rm -rf template/skill-package/interactionModels
            fi           
      - run: git clone -b $GIT_BRANCH $GIT_TEMPLATE_URL
       #cleanup template downloaded metada, getting only lambda + skill-packages objeects 
       #copy downloaded template fully cleaned to final template to push
      - run: 
          name: merge donwloaded template
          command: |
            base_file=$(basename $GIT_TEMPLATE_URL)
            repo_folder=${base_file%.*}

            rm -rf $repo_folder/.git 
            if [ "$ASK_VERSION" == "1.0" ]; then
              info=$(cat $repo_folder/skill.json | jq -rc .manifest.publishingInformation)
              skill_info=$(jq -rc --argjson info "$info" '.manifest.publishingInformation = $info' template/skill.json)
              echo $skill_info > template/skill.json

              dir=$(cat $repo_folder/skill.json | jq -r .manifest.apis.custom.endpoint.sourceDir)

              rm -rf $repo_folder/.ask
              rm -rf $repo_folder/skill.json
              cp -R $repo_folder/. template/
              
              if [ "$dir" != "lambda/" ]; then
                cp -R  template/${dir}/. template/lambda/
                rm -rf template/${dir}
              fi
            else
               endpoint=$(cat template/skill-package/skill.json | jq -rc .manifest.apis.custom.endpoint)
               regions=$(cat template/skill-package/skill.json | jq -rc .manifest.apis.custom.regions)
               
               skill_info=$(jq -rc --argjson endpoint "$endpoint" '.manifest.apis.custom.endpoint = $endpoint' $repo_folder/skill-package/skill.json)
               echo $skill_info > $repo_folder/skill-package/skill.json
               skill_info=$(jq -rc --argjson regions "$regions" '.manifest.apis.custom.regions = $regions' $repo_folder/skill-package/skill.json)
               echo $skill_info > $repo_folder/skill-package/skill.json

               dir=$(cat $repo_folder/ask-resources.json | jq -r .profiles.default.code.default.src)

               rm -rf $repo_folder/.ask 
               rm -rf $repo_folder/ask-resources.json 
               cp -R $repo_folder/. template/
              
               if [ "$dir" != "./lambda" ]; then
                cp -R  template/${dir}/. template/lambda/
                rm -rf template/${dir}
               fi
            fi
            
      - persist_to_workspace:
          root: /home/node/
          paths:
            - project
            - .ask
```

### Despliegue de la Alexa Skill con todos los cambios

En este momento, tenemos nuestra HelloWorld Alexa Hosted Skill fusionada con éxito con el template de la Alexa Skill descargada. Ahora es el momento de desplegar los cambios.

Dependiendo de la versión de ASK CLI, ejecutaremos uno u otro comando:
1. Para la versión **ASK CLI 1.x**:
   1. Ejecutaremos otro script `expect`. En este caso ejecutaremos el `deploy_hosted_skill_v1.sh`:
   
   ```bash
    #!/usr/bin/expect

    set timeout 6000

    spawn ask deploy --force
    expect "Do you want to proceed with the above deployments"
    send -- "\r"
    expect "Your skill code deployment has started"
   ```

2. Para la versión **ASK CLI 2.x**:
   1. Simplemente ejecutaremos: `git push origin master`

En este paso también configuramos las variables de entorno.

Aquí podéis encontrar el código completo de este job:

```yaml
  deploy_hosted_skill:
    executor: ask-executor
    environment:
      ASK_ACCESS_TOKEN: << pipeline.parameters.ASK_ACCESS_TOKEN >>
      ASK_REFRESH_TOKEN: << pipeline.parameters.ASK_REFRESH_TOKEN >>
      ASK_VENDOR_ID: << pipeline.parameters.ASK_VENDOR_ID >>
      ASK_VERSION: << pipeline.parameters.ASK_VERSION >>
      GIT_TEMPLATE_URL: << pipeline.parameters.GIT_TEMPLATE_URL >>
      GIT_BRANCH: << pipeline.parameters.GIT_BRANCH >>
    steps:
      - attach_workspace:
          at: /home/node/
      #init some git global variables
      - run: git config --global user.email "you@example.com"
      - run: git config --global user.name "Your Name"
      #push the final skill
      - run: 
          name: deploy
          command: |
            cd template/
            echo "" >> .gitignore
            echo "deploy_hosted_skill_v1.sh" >> .gitignore
            git add . 
            git commit -m "template added" 
            if [ "$ASK_VERSION" == "1.0" ]; then
              cp ../deploy_hosted_skill_v1.sh ./  
              ./deploy_hosted_skill_v1.sh
            else
              git push origin master
            fi
      - store_artifacts:
          path: ./
```

Finalmente, nuestra HelloWorld Skill se transformará en el template de la Alexa Skill descargada:

  ![Full-width image](/assets/img/blog/tutorials/alexa-skill-autodeployer/final.png){:.lead data-width="800" data-height="100"}
Template desplegado
  {:.figure}

### Pipeline

Aquí podemos encontrar la especificación del pipeline con todos los jobs comentados anteriormente:

```yaml
  workflows:
    skill-pipeline:
        jobs:
        - checkout
        - create_hosted_skill:
            requires:
                - checkout
        - download_template:
            requires:
            - create_hosted_skill
        - deploy_hosted_skill:
            requires:
            - download_template
```

**NOTA:** todos los archivos de configuración de CircleCI se encuentran en la carpeta `.circleci`.

## Invocación & Uso

Ahora el proceso de automatización está completamente explicado. Comencemos explicando cómo usarlo usando la API de CircleCI.

Es importante mencionar que ninguna credencial es almacenada. Las usaremos solo para el proceso de automatización. Por favor, consulte el código fuente si tiene alguna duda.

Así es como se puede llamar al pipeline utilizando la API REST de CircleCI:

```bash
 curl --request POST \
      --url https://circleci.com/api/v2/project/<your-vcs>/<your-username>/<your-repo-name>/pipeline?circle-token=<your-circle-ci-token> \
      --header 'content-type: application/json' \
      --data-binary @- << EOF  
      { 
        "parameters": { 
            "ASK_ACCESS_TOKEN": "your-access-token", 
            "ASK_REFRESH_TOKEN": "your-refresh-token", 
            "ASK_VENDOR_ID": "your-vendor-id", \
            "GIT_TEMPLATE_URL": "the-git-template-url", 
            "GIT_BRANCH": "the-git-template-branch", 
            "ASK_VERSION": "ask-cli-version" 
        } 
    }
    EOF
```

### Ejemplo

Imaginemos que queremos deplegar este template https://github.com/alexa/skill-sample-nodejs-highlowgame.git como una Alexa Hosted Skill en nuestra cuenta de AWS:

  ![Full-width image](/assets/img/blog/tutorials/alexa-skill-autodeployer/template.png){:.lead data-width="800" data-height="100"}
Ejemplo de un templete de una Alexa Skill
  {:.figure}


La llamada REST será así:
1. Para la versión **ASK CLI 1.x**:
  
```bash
 curl --request POST \
      --url https://circleci.com/api/v2/project/github/xavidop/alexa-skill-autodeployer/pipeline?circle-token=a96e83d347a52c19d2b38dd981f3fc2fa0217f7e \
      --header 'content-type: application/json' \
      --data-binary @- << EOF 
      { 
        "parameters": { 
            "ASK_ACCESS_TOKEN": "your-access-token", 
            "ASK_REFRESH_TOKEN": "your-refresh-token", 
            "ASK_VENDOR_ID": "your-vendor-id", 
            "GIT_TEMPLATE_URL": "https://github.com/alexa/skill-sample-nodejs-highlowgame.git", 
            "GIT_BRANCH": "master", 
            "ASK_VERSION": "1.0" 
        } 
    }
    EOF
```

1. Para la versión **ASK CLI 2.x**:
   
```bash
 curl --request POST \
      --url https://circleci.com/api/v2/project/github/xavidop/alexa-skill-autodeployer/pipeline?circle-token=a96e83d347a52c19d2b38dd981f3fc2fa0217f7e \
      --header 'content-type: application/json' \
      --data-binary @- << EOF 
      { 
        "parameters": { 
            "ASK_ACCESS_TOKEN": "your-access-token", 
            "ASK_REFRESH_TOKEN": "your-refresh-token", 
            "ASK_VENDOR_ID": "your-vendor-id", 
            "GIT_TEMPLATE_URL": "https://github.com/alexa/skill-sample-nodejs-highlowgame.git", 
            "GIT_BRANCH": "ask-cli-x", 
            "ASK_VERSION": "2.0" 
        } 
    }
    EOF
```


## Recursos
* [DevOps Wikipedia](https://en.wikipedia.org/wiki/DevOps) - Referencia de Wikipedia
* [Documentación oficial de la Alexa Skill Management API](https://developer.amazon.com/es-ES/docs/alexa/smapi/skill-testing-operations.html) - Documentación oficial de la Alexa Skill Management API
* [Documentación oficial de CircleCI](https://circleci.com/docs/) - [Documentación oficial de CircleCI
* [Documentación oficial de la API deCircleCI](https://circleci.com/docs/api/v2/) - Documentación oficial de la API deCircleCI

## Conclusión 

Gracias al ASK CLI podemos realizar esta compleja tarea.

Espero que esta herramienta te sea de utilidad.

Podemos utilizar esta herramienta, por ejemplo, para los siguientes casos de uso:
1. Agregar un botón en nuestros repositorios de git que sean templates de una Alexa Skill para deplegarlas automáticamente en nuestra cuenta de AWS.
2. Agregar un botón en una página web que haga una llamada a este proceso.
3. Transformar nuestras Self Hosted skills por alojadas por Alexa Hosted.
4. ¡Probar nuevas Skills de Alexa y seguir aprendiendo!

Puedes encontrar el código en mi [**GitHub**](https://github.com/xavidop/alexa-skill-autodeployer)

!Eso es todo!

¡Espero que te sea útil! Si tienes alguna duda o pregunta, no dudes en ponerte en contacto conmigo o poner un comentario a continuación.

Happy coding!
    