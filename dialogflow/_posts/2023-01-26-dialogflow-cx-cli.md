---
layout: post
title: "Dialogflow CX CLI: The missing CLI to interact with your agents (English)"
description: >
  An introduction to the most powerful Dialogflow CX CLI ever made
image: /assets/img/blog/post-headers/dialogflow-cx-cli.jpg
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

# Dialogflow CX CLI

## Previous Requisites

Here are the technologies used in this project
1. Google Cloud Account - [Sign up here for free](https://cloud.google.com/)
2. Dialogflow API enabled - [How to enable it](https://cloud.google.com/dialogflow/cx/docs/reference)
3. Dialogflow CX CLI - [Install and configure Dialogflow CX CLI](https://cxcli.xavidop.me/)

## What is this?

<p align="center">
  <img alt="CXCLI Logo" src="/assets/img/blog/tutorials/dialogflow-cx-cli/cxcli.png" height="256" />
  <h3 align="center">Dialogflow CX CLI</h3>
  <p align="center">The missing CLI for your Dialogflow CX projects.</p>
</p>

The [Dialoglfow CX CLI](https://cxcli.xavidop.me/) or `cxcli` is a Command Line Interface Tool that you can use to interact with your Dialogflow CX projects in a terminal. It is an open-source project created by [Xavier Portilla Edo](https://xavidop.me/). This project was created due to the lack of an existing official CLI for the next-gen Dialogflow. This tool has been built using [Golang](https://go.dev/) and the framework [Cobra](https://github.com/spf13/cobra). You can find the source code at [Github](https://github.com/xavidop/dialogflow-cx-cli) to check the implementation of the tool. This CLI is available for MacOS, Linux and Windows.

## Features

When I created this tool, my first intention of it was just for testing purposes. Then once I was developing and evolving `cxcli` I realized that I can add a bunch of features that can help the interaction and the automation with Dialogflow CX Agents. Therefore, you can perform all these actions:
1. Interact with your Intents by creating or deleting them.
2. Create or update Entity Types.
3. Play with your agents: you can create or delete them.
4. It has some testing tools:
   1. Execute your CI/CD pipelines.
   2. Run a NLU profiler.
5. Speech-to-text: You can recognize text from an audio file from your CLI!
6. Text-to-speech: Synthesize voice from text direct from a Command Line Interface. This is really cool!
7. And many more to come, check the Roadmap below!

## Installation

You can install the pre-compiled binary (in several ways), using Docker or compiling it from source.

Below you can find the steps for each of them.

* **homebrew tap**
  * Add the Hombrew tab:
    ```sh
    brew tap xavidop/tap git@github.com:xavidop/homebrew-tap.git
    brew update
    ```
  * Install the Dialogflow CX CLI:
    ```sh
    brew install cxcli
    ```
* **snapcraft**
  ```sh
  sudo snap install cxcli
  ```
* **scoop**
  ```powershell
  scoop bucket add cxcli https://github.com/xavidop/scoop-bucket.git
  scoop install cxcli
  ```
* **apt**
  ```sh
  echo 'deb [trusted=yes] https://apt.fury.io/xavidop/ /' | sudo tee /etc/apt/sources.list.d/cxcli.list
  sudo apt update
  sudo apt install cxcli
  ```
* **yum**
  ```sh
  echo '[cxcli]
  name=Dialogflow CX CLI Repo
  baseurl=https://yum.fury.io/xavidop/
  enabled=1
  gpgcheck=0' | sudo tee /etc/yum.repos.d/cxcli.repo
  sudo yum install cxcli
  ```
* **aur**
  ```sh
  yay -S cxcli-bin
  ```
* **deb, rpm and apk packages**

Download the `.deb`, `.rpm` or `.apk` packages from the [OSS releases page](https://github.com/xavidop/dialogflow-cx-cli/releases) and install them with the appropriate tools.
* **Go install**
  ```sh
  go install github.com/xavidop/dialogflow-cx-cli@latest
  ```
* **Bash script**
  ```sh
  curl -sfL https://cxcli.xavidop.me/static/run | bash
  ```
* **Manually**

Download the pre-compiled binaries from the [releases page](https://github.com/xavidop/dialogflow-cx-cli/releases) and copy them to the desired location.
* **Running with Docker**
  
You can also use it within a Docker container.
To do that, you'll need to execute something more-or-less like the examples below.
Example usage:
  ```sh
  docker run --rm \
      xavidop/cxcli cxcli version
  ```
Note that the image will almost always have the last stable Go version.
If you need more things, you are encouraged to keep your own image. You can
always use cxcli's [own Dockerfile](https://github.com/xavidop/dialogflow-cx-cli/blob/master/Dockerfile) as an example though
and iterate from that.
Registries:
  1. [`xavidop/cxcli`](https://hub.docker.com/r/xavidop/cxcli)
  2. [`ghcr.io/xavidop/cxcli`](https://github.com/xavidop/dialogflow-cx-cli/pkgs/container/cxcli)


## Authentication

`cxcli` uses some Google cloud APIs. By default the tool uses the default configuration that uses the `gcloud` cli. If you want to use another authentication key you can provide a `json` file with the global `--credentials` parameter.

The `cxcli` source code is open source, you can check it out [here](https://github.com/xavidop/dialogflow-cx-cli) to learn more about the actions the tool performs.

Below you can find the roles and the APIs needed to use the tool.

### Roles needed

1. **Dialogflow API Admin**: Provides full access to create, update, query, detect intent, and delete the agent from the console or API. Click [here](https://cloud.google.com/dialogflow/cx/docs/concept/access-control) for more information.

We are using the Admin role because `cxcli` performs the [List agent](https://cloud.google.com/dialogflow/cx/docs/reference/rest/v3beta1/projects.locations.agents/list) action.

This role allows you to execute Speech-to-text and Text-to-speech actions as well.

### APIs enabled needed

These APIs should be enabled on your Google Cloud project if you want to use these `cxcli` capabilities:
1. **Dialogflow CX**: You will need to enable the `Dialogflow API` on your project. More information [here](https://cloud.google.com/dialogflow/cx/docs)
2. **Speech-to-text**: You will need to enable the `Cloud Speech-to-Text API` on your project. More information [here](https://cloud.google.com/speech-to-text/docs/transcribe-api)
3. **Text-to-speech**: You will need to enable the `Cloud Text-to-Speech API` on your project. More information [here](https://cloud.google.com/text-to-speech/docs/apis)

## Roadmap

`cxcli` is in active development. The core product is functioning.

Our goal with the tool is to prove that there's market fit for a solution like this, and if so, we'll invest more time in automation, user experience and more features.

For now, if you're interested in participating and giving feedback, we believe `cxcli` already solves pain at this stage.

Shipped:

* [x] Available in homebrew, snapcraft, apt, yum, scoop, aur package managers 
* [x] Documentation updated
* [x] Profile NLU
* [x] Speech-to-text and Text-to-speech actions
* [x] Container image available for multiple architectures
* [x] SBOM files created
* [x] Artifacts uploaded, signed and available on GitHub

Coming soon:

* [ ] Continuous integration support (GitHub Action, CircleCI, etc.)
* [ ] Intents and entities actions (create, update)
* [ ] Support more environments (create, update) actions
* [ ] Support more agent actions (create, update, train)

## Resources

If you want to check the full usage of the `cxcli`, please refer to this [page](https://cxcli.xavidop.me/cxcli/).

Check the official `cxcli` [page](https://cxcli.xavidop.me/).

If you want to learn more about Dialogflow CX testing, check the [official documentation](https://cloud.google.com/dialogflow/cx/docs/concept/test-case).

## Conclusion 

This was an introduction to the Dialogflow CX CLI. As you have seen in this article, `cxcli` is a powerful tool that will help you during your day-to-day tasks while you are developing your bots!

You can contact us via email at: [dialogflowcxcli@gmail.com](mailto:dialogflowcxcli@gmail.com)

Follow [@dialogflowcxcli on Twitter](https://twitter.com/dialogflowcxcli) for updates and announcements!

That's all folks!

Happy coding!