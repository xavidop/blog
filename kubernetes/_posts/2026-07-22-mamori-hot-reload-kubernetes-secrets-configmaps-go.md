---
layout: post
title: "Hot-Reloading Kubernetes Secrets and ConfigMaps in Go with mamori (No Pod Restarts) (English)"
description: >
  You updated a Kubernetes Secret and then did the ritual: kubectl rollout restart. There is a better way. mamori watches your Secrets and ConfigMaps with native informers and reconciles the change into your running Go process, atomically and validated, without bouncing a single pod.
image: /assets/img/blog/post-headers/mamori-kubernetes.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [kubernetes]
tags:
  - kubernetes
  - go
  - golang
  - mamori
  - secrets
  - configmap
  - secret-rotation
keywords:
  - kubernetes
  - k8s
  - go
  - golang
  - mamori
  - secrets
  - configmap
  - hot-reload
  - secret-rotation
  - informers
  - reloader
  - external-secrets-operator

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

If you run Go services on Kubernetes, you know the ritual. You update a `Secret` or a `ConfigMap`, and then you do one of these:

- `kubectl rollout restart deployment/my-app` and eat the disruption.
- Install [Reloader](https://github.com/stakater/Reloader) so *it* restarts your pods for you when a `Secret` changes.
- Mount the `Secret` as a volume and cross your fingers that your app re-reads the file (spoiler: most apps read it once at boot).

All three share the same flaw: the way you "pick up" a config change is to **throw away the process and start a new one.** For a rotating database password, that means dropping every in-flight request, cold connection pools, and a latency spike — all to change one string.

I built [**mamori**](https://mamorigo.dev) partly because of this exact frustration. mamori watches your Kubernetes `Secret`s and `ConfigMap`s with native **informers**, and when a value changes it reconciles the new value into your running Go process — typed, validated, and atomically swapped — **without restarting anything.**

> New to mamori? Start with the launch article, [Introducing mamori: Typed, Watchable Config & Secrets for Go](/go/2026-07-21-introducing-mamori-config-secrets-go/), for the full picture. This post is the Kubernetes-focused deep cut.

## The two schemes you'll use

mamori's Kubernetes provider gives you two ref schemes:

| Ref | Reads from | Notes |
| --- | --- | --- |
| `k8s-secret://<namespace>/<name>#<key>` | a `Secret` | value is **base64-decoded for you** |
| `k8s-cm://<namespace>/<name>#<key>` | a `ConfigMap` | plain string values |

Drop the `#key` and you get the whole `Secret`/`ConfigMap` as a JSON map, which you can decode into a nested struct with `flatten`. A few concrete examples:

```text
k8s-secret://prod/db-creds#password   # one key from a Secret, base64-decoded
k8s-secret://prod/tls#ca.crt          # a certificate as []byte
k8s-cm://prod/app-config#log_level    # one key from a ConfigMap
k8s-cm://prod/app-config              # the whole ConfigMap as a JSON map
```

## Setup

The provider lives in its own module. Note the import path is `providers/k8s` (not `providers/kubernetes`):

```bash
go get github.com/xavidop/mamori
go get github.com/xavidop/mamori/providers/k8s
```

Register it with a blank import — same convention as `database/sql` drivers. Its `init()` wires the `k8s-secret` and `k8s-cm` schemes into mamori:

```go
import _ "github.com/xavidop/mamori/providers/k8s"
```

In-cluster, the provider uses the pod's mounted ServiceAccount automatically. The only thing you owe it is **RBAC**: it needs to `get`, `list`, and `watch` the resources you reference in the namespaces you reference.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: mamori-reader
  namespace: prod
rules:
  - apiGroups: [""]
    resources: ["secrets", "configmaps"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: mamori-reader
  namespace: prod
subjects:
  - kind: ServiceAccount
    name: my-app
    namespace: prod
roleRef:
  kind: Role
  name: mamori-reader
  apiGroup: rbac.authorization.k8s.io
```

The `watch` verb is the important one — it's what lets mamori use an informer instead of hammering the API server with polls.

## Load once, then watch forever

Describe what you need as a struct. mamori resolves every ref, applies defaults, and validates — all before your `main` gets a config:

```go
package main

import (
	"context"
	"log"

	"github.com/xavidop/mamori"
	"github.com/xavidop/mamori/secret"

	_ "github.com/xavidop/mamori/providers/k8s"
)

type Config struct {
	DBPassword secret.String `source:"k8s-secret://prod/db-creds#password"`
	LogLevel   string        `source:"k8s-cm://prod/app-config#log_level" default:"info" validate:"oneof=debug info warn error"`
	MaxConns   int           `source:"k8s-cm://prod/app-config#max_conns" default:"10" validate:"gte=1,lte=500"`
	CACert     []byte        `source:"k8s-secret://prod/tls#ca.crt"`
}

func main() {
	cfg, err := mamori.Load[Config](context.Background())
	if err != nil {
		log.Fatal(err)
	}
	_ = cfg // fully resolved, defaulted, validated
}
```

Notice `DBPassword` is a `secret.String`, not a plain `string`. That type redacts itself in logs, `fmt`, and JSON — so a stray `log.Printf("%+v", cfg)` prints `[REDACTED]` instead of leaking the password. You only ever see the plaintext when you explicitly call `.Reveal()`.

Now the part that matters. Swap `Load` for `Watch`, and the moment someone runs `kubectl edit secret db-creds`, your process reacts:

```go
w, err := mamori.Watch[Config](ctx,
	mamori.OnChange(func(ev mamori.Change[Config]) {
		if ev.Changed("DBPassword") {
			// Rebuild the pool with the rotated password — live, no restart.
			pool.Rotate(ev.New.DBPassword.Reveal())
		}
		for _, f := range ev.Fields {
			log.Printf("reconciled %s: %s -> %s", f.Path, f.OldVersion, f.NewVersion)
		}
	}),
	mamori.OnError(func(err error) { metrics.Inc("config_error") }),
)
if err != nil {
	log.Fatal(err)
}
defer w.Close()

cfg := w.Get() // lock-free snapshot; always the last VALID config
```

`w.Get()` is lock-free and always returns the last *valid* configuration. If someone pushes a `ConfigMap` with `log_level: banana`, the `validate:"oneof=..."` tag rejects it: the update is dropped atomically, `Get()` keeps returning the good value, and `OnError` receives a `*ValidationError`. **A bad edit never takes your service into a broken state.**

## Informers, not polling

This is the difference between mamori and the mount-a-file-and-poll approach. The Kubernetes provider implements native watching backed by the client-go informer machinery, so change detection is **push-based** — the API server tells your process the instant a `Secret` changes, rather than your process asking every N seconds.

Practically, that means:

- **Near-instant reconciliation.** No polling interval to tune, no `min(sync, interval)` latency floor like the kubelet's ~60s volume refresh.
- **No API-server hammering.** One watch connection per resource, shared, instead of a `GET` loop per pod.
- **Graceful fallback.** If a native watch fails to start for some reason, mamori automatically falls back to polling with jittered intervals, so you never lose reconciliation entirely.

Compare that to the alternatives:

| Approach | How a change is picked up | Restart? |
| --- | --- | --- |
| `kubectl rollout restart` | you, manually | yes |
| Reloader / Stakater | operator restarts the pod | yes |
| Secret mounted as volume | kubelet re-syncs file (~60s), *if* your app re-reads it | no, but you must re-read |
| **mamori** | informer pushes change → validated atomic swap → callback | **no** |

## Whole ConfigMaps and JSON blobs

Sometimes you keep a structured blob in one key. Decode it straight into a nested struct with `flatten`:

```go
type Config struct {
	Redis RedisConfig `source:"k8s-secret://prod/redis-conn" flatten:"json"`
}

type RedisConfig struct {
	Addr     string        `mapstructure:"addr"`
	Password secret.String `mapstructure:"password"`
	DB       int           `mapstructure:"db"`
}
```

That reads the whole `redis-conn` Secret (a JSON document), decodes it, and — because `Password` is a `secret.String` — keeps the password redacted throughout.

## A note on TLS certificates

Certificates rotate too, and a cert reload is the perfect no-restart use case. Because file and Secret updates for certs usually want to apply *immediately* (no coalescing delay), you can set `?debounce=0` on the ref:

```go
type TLS struct {
	Cert []byte       `source:"k8s-secret://prod/tls#tls.crt?debounce=0"`
	Key  secret.Bytes `source:"k8s-secret://prod/tls#tls.key?debounce=0"`
}
```

Wire the `OnChange` callback to swap the `*tls.Certificate` your server hands out in its `GetCertificate` hook, and you've got zero-downtime cert rotation from a Kubernetes `Secret`.

## When you don't need this

Be honest with yourself: if your config is a log level from a `ConfigMap` that only ever changes on deploy, you don't need runtime watching — a plain `Load` at boot is fine, and mamori is happy to do just that. And if you already mount a `Secret` as a file and genuinely re-read it, mamori's built-in `file://` provider (with `fsnotify`) covers that too, without any Kubernetes RBAC at all.

mamori earns its keep the moment a value changes *while your process is running* and you'd rather rotate a pool than recycle a pod.

## Wrapping up

Kubernetes already tells you the instant a `Secret` changes — via informers. mamori just connects that signal to a typed, validated, redacted struct inside your Go process, so a rotation becomes a callback instead of a rollout.

```bash
go get github.com/xavidop/mamori/providers/k8s
```

- **Full introduction:** [Introducing mamori](/go/2026-07-21-introducing-mamori-config-secrets-go/)
- **Docs:** [mamorigo.dev/docs](https://mamorigo.dev/docs)
- **Source:** [github.com/xavidop/mamori](https://github.com/xavidop/mamori)

mamori is MIT-licensed and currently at `v0.1.0`, so issues and feedback are very welcome. Happy shipping!
