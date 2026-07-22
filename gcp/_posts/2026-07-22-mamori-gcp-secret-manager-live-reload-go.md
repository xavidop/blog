---
layout: post
title: "GCP Secret Manager, Live-Reloaded in Go with mamori (English)"
description: >
  In GCP Secret Manager, secret versions are immutable and you rotate by adding a new version and moving the "latest" alias. But your Go service resolved "latest" once at boot and froze it there. mamori watches the secret, notices when "latest" moves, and reconciles the new version into your running process, validated and redacted.
image: /assets/img/blog/post-headers/mamori-gcp.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [gcp]
tags:
  - gcp
  - go
  - golang
  - mamori
  - secrets
  - secret-manager
  - secret-rotation
keywords:
  - gcp
  - google-cloud
  - google-cloud-platform
  - gcp-secret-manager
  - secret-manager
  - go
  - golang
  - mamori
  - secrets
  - hot-reload
  - secret-rotation
  - workload-identity

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

Google Cloud Secret Manager has a clean, opinionated model: a **secret** is a container, and inside it live immutable, numbered **versions**. You never edit a version — you *add* a new one (`1`, `2`, `3`, …) and, when it's ready, you move traffic to it, usually by resolving the `latest` alias (or by disabling the old version).

It's a genuinely good design. But it collides with how most Go services consume secrets: you call `AccessSecretVersion("latest")` exactly once, at startup, and cache the result. From that moment your process is pinned to whatever `latest` meant *at boot*. Add version `4`, disable version `3`, and your service happily keeps using `3` until someone restarts it — which, at best, is a scheduled redeploy and, at worst, an incident when the disabled version stops resolving.

[**mamori**](https://mamorigo.dev) is a Go library I built to make config and secrets *watchable*. Point it at a GCP secret and it notices when `latest` moves, pulls the new version, re-validates your whole config, and swaps it in atomically — **while your service keeps running.**

> This is the GCP-focused companion to the launch article, [Introducing mamori: Typed, Watchable Config & Secrets for Go](/go/2026-07-21-introducing-mamori-config-secrets-go/). That one covers the full model; here we focus on Secret Manager's version semantics.

## The `gcp-sm` scheme

The `providers/gcp` module registers the `gcp-sm` scheme. The grammar is `gcp-sm://<project>/<secret>[#json-key][?version=<v>]`:

```text
gcp-sm://my-project/db-password        # resolves the "latest" enabled version
gcp-sm://my-project/api-key?version=3  # pin to version 3, forever
gcp-sm://my-project/creds#password     # one key out of a JSON secret payload
```

That `?version=` option is the important knob, and it maps directly onto GCP's version model:

- **No `?version`** → mamori tracks `latest`. When you add a new version and it becomes `latest`, mamori reconciles it in. This is what you want for rotating credentials.
- **`?version=N`** → mamori pins to an immutable version `N`. It will never move. This is what you want for config you want to promote deliberately and reproducibly (think: "this deploy runs config version 7, full stop").

## Setup

```bash
go get github.com/xavidop/mamori
go get github.com/xavidop/mamori/providers/gcp
```

Register with a blank import; it uses Application Default Credentials, so on GKE it picks up **Workload Identity** automatically, and locally it uses your `gcloud auth application-default` login:

```go
import _ "github.com/xavidop/mamori/providers/gcp"
```

The service account you bind needs `roles/secretmanager.secretAccessor` on the secrets it reads (and the ability to see version metadata to detect a new `latest`). Scope it to the specific secrets, not the whole project.

## Load, then watch `latest` move

```go
package main

import (
	"context"
	"log"
	"time"

	"github.com/xavidop/mamori"
	"github.com/xavidop/mamori/secret"

	_ "github.com/xavidop/mamori/providers/gcp"
)

type Config struct {
	// Tracks "latest": rotates in when you add a new enabled version.
	DBPassword secret.String `source:"gcp-sm://my-project/db-password"`

	// Pinned to an immutable version: deliberate, reproducible.
	StripeKey secret.String `source:"gcp-sm://my-project/stripe-key?version=7"`

	// One field out of a JSON secret.
	APIToken secret.String `source:"gcp-sm://my-project/creds#api_token"`
}

func main() {
	ctx := context.Background()

	w, err := mamori.Watch[Config](ctx,
		mamori.WithPollInterval(60*time.Second),
		mamori.OnChange(func(ev mamori.Change[Config]) {
			if ev.Changed("DBPassword") {
				pool.Rotate(ev.New.DBPassword.Reveal()) // live, no restart
				log.Println("db-password: new version reconciled")
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

Every secret field here is a `secret.String`, which redacts itself in `fmt`, `slog`, and JSON — so nothing leaks into logs — and only reveals plaintext through an explicit `.Reveal()`. mamori's `go vet` analyzer will even fail your build if you store a `gcp-sm://` value in a plain `string`.

## What reconciliation actually does here

When you rotate — add version `4` to `db-password` and let it become `latest` — mamori's poll cycle notices that the resolved version changed, fetches it, and then:

1. **Re-validates the entire struct.** If the new secret somehow fails a `validate` rule, the update is rejected: `Get()` keeps returning the last good value and `OnError` gets a `*ValidationError`. A bad version can't take your service down.
2. **Swaps atomically.** `w.Get()` transitions from old to new in one lock-free store — no reader ever sees a partially-updated config.
3. **Fires a diff-aware callback.** `OnChange` tells you *which* fields moved (`ev.Fields`) with old/new versions, so you only rebuild what actually changed.

Because Secret Manager has no push channel for "latest moved", mamori **polls** — and it polls politely: the interval is jittered by ±20% so a large fleet doesn't stampede the API on the same tick, and change detection compares version metadata before pulling the payload, so an unchanged secret is cheap.

## Structured secrets with `flatten`

Teams often store a whole connection blob as one JSON secret. Decode it straight into a nested struct:

```go
type Config struct {
	DB DBConfig `source:"gcp-sm://my-project/db-conn" flatten:"json"`
}

type DBConfig struct {
	Host     string        `mapstructure:"host"`
	Port     int           `mapstructure:"port"`
	Password secret.String `mapstructure:"password"`
}
```

One `AccessSecretVersion` call, one JSON document, cleanly typed — with the password still redacting itself.

## Version pinning as a deploy strategy

The `?version=` toggle enables a genuinely nice workflow. Keep operational secrets on `latest` so rotations flow in automatically, but pin *config that changes behavior* to explicit versions so a rollout is deterministic and rollback is trivial:

```go
type Config struct {
	DBPassword   secret.String `source:"gcp-sm://my-project/db-password"`             // latest: auto-rotate
	FeatureFlags []byte        `source:"gcp-sm://my-project/flags?version=12"`         // pinned: promote on purpose
}
```

Bumping `?version=12` to `?version=13` becomes a reviewable, revertible change in your code — while credentials keep rotating themselves in the background.

## Wrapping up

GCP Secret Manager's immutable-versions model is great, but only if your app actually follows `latest` at runtime. mamori makes it do that: it watches the secret, reconciles a new version into your running Go process, validated and redacted, and lets you pin the fields you want frozen.

```bash
go get github.com/xavidop/mamori/providers/gcp
```

- **Full introduction:** [Introducing mamori](/go/2026-07-21-introducing-mamori-config-secrets-go/)
- **Docs:** [mamorigo.dev/docs](https://mamorigo.dev/docs)
- **Source:** [github.com/xavidop/mamori](https://github.com/xavidop/mamori)

mamori is MIT-licensed and at `v0.1.0` — early and moving fast, so issues and feedback are very welcome. Happy coding!
