---
layout: post
title: "Azure Key Vault Secrets That Reconcile Themselves in Go, with mamori (English)"
description: >
  Azure Key Vault versions your secrets and lets you rotate them behind the scenes, but your Go service resolved the secret once at boot and never looked again. mamori watches Key Vault and reconciles a new version into your running process, typed, validated, and redacted, without a restart.
image: /assets/img/blog/post-headers/mamori-azure.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [azure]
tags:
  - azure
  - go
  - golang
  - mamori
  - secrets
  - key-vault
  - secret-rotation
keywords:
  - azure
  - azure-key-vault
  - key-vault
  - go
  - golang
  - mamori
  - secrets
  - hot-reload
  - secret-rotation
  - managed-identity
  - workload-identity
  - defaultazurecredential

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

Azure Key Vault is the well-behaved citizen of the Azure secrets world. Every secret is versioned, you get soft-delete and purge protection, access is governed by RBAC or access policies, and `DefaultAzureCredential` means your app authenticates the same way locally (`az login`) and in production (Managed Identity / Workload Identity on AKS) with zero code changes.

And yet the same old gap is there. Your Go service calls `GetSecret` once at startup, decodes the value into a struct, and treats it as immutable for the life of the process. When someone rotates the secret in Key Vault — a new version, the old one disabled — your service has no idea. It keeps using the value it read at boot until the next deploy or pod restart. The rotation was seamless in Azure and invisible to your app, which is exactly the wrong combination.

[**mamori**](https://mamorigo.dev) is a Go library I built to fix this class of problem across every backend. Point it at a Key Vault secret and it watches for new versions, pulls the change, re-validates your whole config, and swaps it in atomically — **while your service keeps running.**

> This is the Azure entry in the mamori launch series. For the full model, start with [Introducing mamori: Typed, Watchable Config & Secrets for Go](/go/2026-07-21-introducing-mamori-config-secrets-go/); here we focus on Key Vault.

## The `azure-kv` scheme

The `providers/azure` module registers the `azure-kv` scheme. The grammar is `azure-kv://<vault-name>/<secret-name>[#json-key][?version=<v>]`:

```text
azure-kv://my-vault/db-password              # latest enabled version
azure-kv://my-vault/api-key?version=abc123   # pin to a specific version id
azure-kv://my-vault/creds#password           # one key out of a JSON secret
```

One Key Vault quirk to keep in mind: versions are identified by **opaque hex ids**, not the sequential `1`, `2`, `3` you get in GCP Secret Manager. So `?version=` here pins to an id like `abc123def456...`, not a number. Leave `?version` off and mamori tracks whatever the latest enabled version resolves to — which is what you want for credentials that rotate.

## Setup

```bash
go get github.com/xavidop/mamori
go get github.com/xavidop/mamori/providers/azure
```

Register it with a blank import. It authenticates through `DefaultAzureCredential`, so it picks up your `az login` locally, a Managed Identity on a VM/App Service, or Workload Identity on AKS — automatically, in that order:

```go
import _ "github.com/xavidop/mamori/providers/azure"
```

The identity you bind needs read access to the vault's secrets. With Key Vault's RBAC model that's the built-in **Key Vault Secrets User** role, scoped to the vault (or to individual secrets):

```bash
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee "<managed-identity-object-id>" \
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/my-vault"
```

If your vault still uses the classic access-policy model instead of RBAC, grant `Get` (and `List`) on secrets.

## Load, then watch the rotation

```go
package main

import (
	"context"
	"log"
	"time"

	"github.com/xavidop/mamori"
	"github.com/xavidop/mamori/secret"

	_ "github.com/xavidop/mamori/providers/azure"
)

type Config struct {
	// Tracks the latest enabled version: rotations flow in automatically.
	DBPassword secret.String `source:"azure-kv://my-vault/db-password"`

	// Pinned to an immutable version id: deliberate, reproducible.
	SigningKey secret.String `source:"azure-kv://my-vault/signing-key?version=abc123"`

	// One field out of a JSON secret.
	APIToken secret.String `source:"azure-kv://my-vault/creds#api_token"`
}

func main() {
	ctx := context.Background()

	w, err := mamori.Watch[Config](ctx,
		mamori.WithPollInterval(60*time.Second),
		mamori.OnChange(func(ev mamori.Change[Config]) {
			if ev.Changed("DBPassword") {
				pool.Rotate(ev.New.DBPassword.Reveal()) // live, no restart
				log.Println("Key Vault: db-password rotated and applied")
			}
		}),
		mamori.OnError(func(err error) { metrics.Inc("config_error") }),
	)
	if err != nil {
		log.Fatal(err)
	}
	defer w.Close()

	cfg := w.Get() // last VALID config, lock-free
	_ = cfg
}
```

Every secret field is a `secret.String`, so it redacts itself in `fmt`, `slog`, and JSON — a stray `log.Printf("%+v", cfg)` prints `[REDACTED]` — and only reveals plaintext through an explicit `.Reveal()`. mamori also ships a `go vet` analyzer that fails your build if an `azure-kv://` value lands in a plain `string` instead of a `secret.String`.

## What reconciliation guarantees

When a new version of `db-password` becomes the latest enabled one, mamori's poll cycle detects the version change, fetches it, and then:

1. **Re-validates the entire struct** — a value that fails a `validate` rule is rejected atomically; `Get()` keeps returning the last good config and `OnError` receives a `*ValidationError`. A bad secret can't break your service.
2. **Swaps atomically** — `w.Get()` moves from old to new in one lock-free store; no reader ever sees a half-updated config.
3. **Fires a diff-aware callback** — `ev.Fields` tells you exactly which fields moved, so you only rebuild what changed.

Key Vault has no push channel for "a new version was created", so mamori **polls** — politely: the interval is jittered by ±20% (tunable with `WithJitter`) so a fleet of pods doesn't hammer the vault on the same tick, and change detection compares the version id before pulling the payload, so an unchanged secret is cheap.

If Key Vault is briefly unreachable, mamori retries with backoff and keeps serving the last good value; wire `WithStale(10*time.Minute)` and check for a `*mamori.StaleError` in `OnError` if you want to page only on a *prolonged* outage rather than a transient blip.

## Structured secrets with `flatten`

Storing a whole connection blob as one JSON secret? Decode it straight into a nested struct:

```go
type Config struct {
	DB DBConfig `source:"azure-kv://my-vault/db-conn" flatten:"json"`
}

type DBConfig struct {
	Host     string        `mapstructure:"host"`
	Port     int           `mapstructure:"port"`
	Password secret.String `mapstructure:"password"`
}
```

One Key Vault call, one JSON document, cleanly typed — with the password still redacting itself.

## When you don't need this

If a secret only ever changes on deploy, a plain `mamori.Load` at boot is all you need — no watching, no poll loop. mamori earns its keep the moment a Key Vault secret rotates *while your process is running* and you'd rather rebuild a client than recycle a pod.

## Wrapping up

Azure Key Vault rotates your secrets cleanly; mamori makes your Go service actually notice. It watches Key Vault, reconciles a new version into your running process — typed, validated, redacted — and lets you pin the versions you want frozen.

```bash
go get github.com/xavidop/mamori/providers/azure
```

- **Full introduction:** [Introducing mamori](/go/2026-07-21-introducing-mamori-config-secrets-go/)
- **Docs:** [mamorigo.dev/docs](https://mamorigo.dev/docs)
- **Source:** [github.com/xavidop/mamori](https://github.com/xavidop/mamori)

mamori is MIT-licensed and at `v0.1.0` — early and moving fast, so issues and feedback are very welcome. Happy coding!
