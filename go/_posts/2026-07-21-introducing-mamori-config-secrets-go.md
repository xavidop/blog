---
layout: post
title: "Introducing mamori: Typed, Watchable Config & Secrets for Go (English)"
description: >
  Every Go service ends up hand-rolling the same thing: a config loader, a secrets fetcher, a ticker to refresh them, a mutex, and a prayer that nothing leaks into the logs. mamori is a new open-source Go library that loads configuration and secrets from more than 30 sources into typed, validated structs, and keeps them reconciled at runtime, without a restart.
image: /assets/img/blog/post-headers/mamori.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [go]
tags:
  - go
  - golang
  - mamori
  - secrets
  - configuration
  - reconciliation
  - kubernetes
keywords:
  - go
  - golang
  - mamori
  - secrets-management
  - configuration
  - config
  - hot-reload
  - secret-rotation
  - kubernetes
  - vault
  - aws-secrets-manager
  - gcp-secret-manager
  - cloud-native
  - reconciliation

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

Every Go service I have ever shipped ends up growing the same organ. It starts small: a couple of `os.Getenv` calls. Then a secret needs to come from AWS Secrets Manager, so you add the SDK. Then someone wants that secret to rotate without a deploy, so you add a `time.Ticker`. Then the ticker needs a mutex because two goroutines read the config while it is being replaced. Then a bad value slips in and takes down production, so you add validation. Then a secret shows up in a log line during an incident, and now you are adding a redaction wrapper too.

By the end you have a bespoke `ConfigManager` in every repo: a loader, a fetcher, a refresh loop, a mutex, and a prayer. It is never quite the same twice, it is rarely tested well, and it is exactly the kind of code nobody wants to own.

I got tired of writing it, so I built a library that does it once, properly. It is called **[mamori](https://mamorigo.dev)**, it is open source, and this article is the full tour: what it is, why it exists, how to use it end to end, and when you should (and shouldn't) reach for it.

## The restart-to-rotate problem

Here is the assumption baked into most Go config code: **configuration is static**. You read it at boot, decode it into a struct, and treat that struct as immutable for the lifetime of the process. If something changes, you redeploy.

That assumption was fine when "config" meant a log level and a port. It is not fine anymore. In a modern service, a meaningful amount of your config is *dynamic by nature*:

- Database passwords and API tokens rotate on a schedule (and increasingly, automatically).
- Vault hands you **dynamic credentials** with a lease that expires in an hour.
- Feature flags flip in the middle of the day, on purpose.
- TLS certificates get reissued.

The industry answer to "config is dynamic" has mostly been to push the problem into the platform. On Kubernetes, the [External Secrets Operator](https://external-secrets.io/) syncs your cloud secret into a `Secret`, and then... you still restart the pod to pick it up, or you mount it as a file and hope your app re-reads it. The dynamic part gets flattened back into a static one at the worst possible layer.

mamori takes the opposite position: **your process should be able to observe a change at the source and react to it, in memory, without bouncing.** Rotating a password should rotate a connection pool, not recycle a pod.

## What is mamori?

**mamori** (守り, Japanese for *"protection"* or *"safeguard"*) is an embedded Go library — not an operator, not a server, not a sidecar. It lives inside your process. Its tagline says it plainly:

> **Typed, watchable config & secrets for Go.** Load configuration and secrets from anywhere into validated Go structs — and keep them reconciled at runtime, without a restart.

There are three concepts you actually touch, and they map cleanly onto three types:

1. **Refs.** Struct fields carry a `source` tag containing a URL-like reference to where the value lives — `env:LOG_LEVEL`, `aws-sm://prod/db#password`, `vault://secret/app#token`. A ref names *what* you want, not *how* to fetch it.

2. **Providers.** A provider resolves one scheme (`aws-sm`, `vault`, `k8s-secret`, …) into a value. Providers register themselves using the same pattern as `database/sql` drivers, so the core module carries **zero cloud-SDK dependencies** — you only pull in the providers you use.

3. **The Reconciler.** This is the interesting part. `Watch` resolves every ref once (fail-fast at startup), then keeps watching each source. When a value changes, it **re-validates the entire struct**, and only if the new snapshot is valid does it **atomically swap it in** and hand you a diff-aware callback. Your app never sees a half-updated, invalid config.

If you have used `IOptionsMonitor<T>` in .NET, `w.Get()` is the direct analogue: always the latest *valid* configuration, lock-free.

## How mamori compares

I want to be honest about prior art, because none of these primitives are new — mamori's contribution is composing them.

- **`gocloud.dev/runtimevar`** is the closest primitive. It watches a single variable beautifully, but it is one variable at a time, with no struct composition, no tags, no validation, no secret hygiene. mamori adds all of that on top of the same idea.
- **Viper / koanf** are excellent, but they are *config-first with secrets bolted on*. mamori is deliberately *secrets-first, with config included*: secret types redact by default, and there is a `go vet` analyzer that yells at you if you store a secret in a plain `string`.
- **envconfig / caarlos0/env** are load-once. No watching, env only.
- **The External Secrets Operator** is complementary, not competitive. mamori is for apps that want to skip the Kubernetes `Secret` hop entirely, or that do not run on Kubernetes at all. It keeps no persistent external state, so there is no finalizer lifecycle to babysit.

And to be equally clear about what mamori is **not**: it is not a secrets store (no encryption at rest, no server), not a sync engine between stores, not a general feature-flag platform, and not cross-language. It is a Go-idiomatic library and it stays in its lane.

## Getting started

The core module has built-in `env:`, `file://`, and `dotenv:` providers, so you can do something useful with zero extra dependencies:

```bash
go get github.com/xavidop/mamori
```

> **Heads up:** mamori requires **Go 1.26 or newer**. It leans on modern generics ergonomics, so this is a hard floor, not a suggestion.

The whole API is driven by a struct and its tags. You describe *what* you want; mamori figures out *how*:

```go
package main

import (
	"context"
	"log"

	"github.com/xavidop/mamori"
	"github.com/xavidop/mamori/secret"
)

type Config struct {
	DBPassword secret.String `source:"aws-sm://prod/db#password"`
	LogLevel   string        `source:"env:LOG_LEVEL" default:"info" validate:"oneof=debug info warn error"`
	Workers    int           `source:"env:WORKERS" default:"4" validate:"gte=1,lte=256"`
	TLSCert    []byte        `source:"file:///etc/tls/tls.crt"`
}

func main() {
	cfg, err := mamori.Load[Config](context.Background())
	if err != nil {
		log.Fatal(err)
	}
	// cfg is fully resolved, defaulted, and validated.
}
```

The signature is exactly what you'd hope for:

```go
func Load[T any](ctx context.Context, opts ...Option) (T, error)
```

`Load` resolves every ref once, applies defaults, validates, and returns your typed config. It **fails fast**: on any resolve or validation error it returns the zero value and a non-nil error. It never returns a partially-populated struct — you either get a complete, valid config or an error.

A few things worth knowing about the tags:

| Tag | Meaning |
| --- | --- |
| `source:"..."` | The ref: where the value comes from. |
| `default:"..."` | Used only when the ref resolves to **not-found** — *never* on an error. |
| `validate:"..."` | [go-playground/validator/v10](https://github.com/go-playground/validator) syntax, run on load and on every update. |
| `flatten:"json\|yaml\|env"` | Decode one payload into a nested struct. |
| `optional:"true"` | Tolerate not-found with no default (field keeps its zero value). |

That `default`-only-on-not-found rule is deliberate and important: if AWS Secrets Manager is having a bad day, you want an error, not a silent fallback to a default password.

## Watching and reconciliation

This is why mamori exists. Swap `Load` for `Watch` and your config becomes a living thing:

```go
func Watch[T any](ctx context.Context, opts ...Option) (*Watcher[T], error)
```

You read the current config with a lock-free `w.Get()`, and you react to changes with an `OnChange` callback:

```go
w, err := mamori.Watch[Config](ctx,
	mamori.WithPollInterval(30*time.Second),
	mamori.OnChange(func(ev mamori.Change[Config]) {
		if ev.Changed("DBPassword") {
			pool.Rotate(ev.New.DBPassword.Reveal())
		}
		for _, f := range ev.Fields {
			log.Printf("%s changed: %s -> %s", f.Path, f.OldVersion, f.NewVersion)
		}
	}),
	mamori.OnError(func(err error) { metrics.Inc("config_error") }),
)
if err != nil {
	log.Fatal(err)
}
defer w.Close()

cfg := w.Get() // always the last VALID config, no lock needed
```

The `Change[T]` you get in the callback carries the old value, the new value, and a per-field diff, plus a `Changed(path)` helper so you only do expensive work (like rebuilding a connection pool) when the field you care about actually moved.

The guarantees are the whole point, so let me spell them out:

- **Atomicity.** `OnChange` only ever fires with a fully re-validated snapshot. If an incoming value fails validation, the update is *rejected*: `Get()` keeps returning the last good config and `OnError` receives a `*ValidationError`. Your config never transitions into a broken state mid-flight.
- **Push where possible, poll where not.** Providers whose backend can push changes (Kubernetes informers, Vault lease watchers, Consul blocking queries, `fsnotify` for files) push natively. Everything else is polled on `WithPollInterval`, **jittered by ±20% by default** so a fleet of pods doesn't stampede your secrets backend on the same tick. If a native watch fails to start, mamori quietly falls back to polling.
- **Coalescing.** Rapid-fire changes within a debounce window (500ms default, overridable per-field with `?debounce=`) collapse into a single event.
- **Lease-aware.** If a provider reports an expiry (Vault dynamic creds), mamori schedules a refresh *before* the lease dies, rather than waiting for the next poll.
- **First event.** `Watch` resolves the initial config before it returns, so `OnChange` fires only on *subsequent* changes. Read the initial state from `w.Get()`.

There's a nice operational escape hatch too. Transient backend outages shouldn't page anyone — but *prolonged* staleness should. `WithStale` draws that line for you:

```go
w, err := mamori.Watch[Config](ctx,
	mamori.WithStale(10*time.Minute),
	mamori.OnError(func(err error) {
		var stale *mamori.StaleError
		if errors.As(err, &stale) {
			alert.Page("config stale", stale)
			return
		}
		metrics.Inc("config_transient_error")
	}),
)
```

A blip retries with exponential backoff and keeps the last good value. Ten minutes of failure escalates to a hard `*StaleError` you can actually page on.

## Secrets that behave like secrets

Configuration and secrets are treated differently, on purpose. Any field that holds a secret should be a `secret.String` or `secret.Bytes` instead of a plain `string` or `[]byte`. These types redact themselves *everywhere* a value normally leaks:

```go
s := secret.NewString("hunter2")

fmt.Println(s)              // [REDACTED]
fmt.Sprintf("%v", s)        // [REDACTED]
fmt.Sprintf("%#v", s)       // [REDACTED]
json.Marshal(s)             // "[REDACTED]"
slog.Info("login", "pw", s) // pw=[REDACTED]

s.Reveal()                  // "hunter2"  <- the only way to read the plaintext
```

It works because the type implements `fmt.Stringer`, `fmt.GoStringer`, `json.Marshaler`, and `slog.LogValuer`. The single, greppable access point is `Reveal()`. That is a feature: in code review or an audit, `grep Reveal` shows you every place a secret is actually unwrapped. (`secret.Bytes.Reveal()` returns `[]byte` rather than a string, for keys and certificates.)

And because "just remember to use `secret.String`" is exactly the kind of discipline that erodes under deadline pressure, mamori ships a `go vet` analyzer that enforces it:

```bash
go install github.com/xavidop/mamori/tools/reconcilevet/cmd/reconcilevet@latest
go vet -vettool=$(which reconcilevet) ./...
```

`reconcilevet` flags any field whose `source` points at a secret-bearing scheme (`aws-sm`, `gcp-sm`, `azure-kv`, `vault`, `op`, `sops`, `k8s-secret`) but is stored in a plain `string` or `[]byte`. The leak becomes a build failure, not a postmortem.

## Providers: more than 30 sources

The core stays dependency-free; each cloud backend is its own module you opt into. A ref's scheme picks the provider:

```bash
go get github.com/xavidop/mamori/providers/aws         # aws-sm://  aws-ps://
go get github.com/xavidop/mamori/providers/vault       # vault://
go get github.com/xavidop/mamori/providers/gcp         # gcp-sm://
go get github.com/xavidop/mamori/providers/azure       # azure-kv://
go get github.com/xavidop/mamori/providers/k8s         # k8s-secret://  k8s-cm://
go get github.com/xavidop/mamori/providers/consul      # consul://
go get github.com/xavidop/mamori/providers/doppler     # doppler://
go get github.com/xavidop/mamori/providers/onepassword # op://
go get github.com/xavidop/mamori/providers/sops        # sops://
```

That is a small slice. All in, there are **more than 30 providers**: secret managers (AWS Secrets Manager, AWS Parameter Store, Vault, GCP, Azure Key Vault, Doppler, 1Password, SOPS), databases (Postgres, MySQL, SQLite, MongoDB, DynamoDB, Cosmos DB, Redis), KV stores (Consul, etcd), Kubernetes Secrets and ConfigMaps, Firebase/Firestore/Remote Config, object storage (S3, GCS, Azure Blob), and a whole shelf of feature-flag platforms (LaunchDarkly, Unleash, Flagsmith, ConfigCat, Split, GrowthBook, Flipt, GO Feature Flag).

Registration follows the `database/sql` convention — a blank import runs the provider's `init()`, which calls `mamori.Register(...)`:

```go
import _ "github.com/xavidop/mamori/providers/vault"
```

When you need explicit configuration (a region, a custom client), construct the provider and pass it with `WithProvider`. That takes precedence over the registry for that call:

```go
import awsprov "github.com/xavidop/mamori/providers/aws"

cfg, err := mamori.Load[Config](ctx,
	mamori.WithProvider(awsprov.NewSecretsManager(awsprov.WithRegion("eu-west-1"))),
)
```

The ref grammar is compact — `scheme://path[#key][?opts]` — with a couple of quirks worth internalizing:

- The `#key` fragment selects one field out of a JSON payload: `aws-sm://prod/db#password`.
- AWS Parameter Store, `etcd`, `sops`, and `file` preserve absolute paths, so they use a **triple slash**: `aws-ps:///myapp/log-level`, `file:///etc/tls/tls.crt`.
- Doppler is the one provider where the `#` fragment is **required**: `doppler://backend/prd#STRIPE_API_KEY`.

When a payload is a structured blob, you can decode it straight into a nested struct with `flatten`:

```go
type Config struct {
	Redis RedisConfig `source:"aws-sm://prod/redis" flatten:"json"`
}

type RedisConfig struct {
	Addr     string        `mapstructure:"addr"`
	Password secret.String `mapstructure:"password"`
	DB       int           `mapstructure:"db"`
}
```

One AWS Secrets Manager call, one JSON blob, cleanly typed — with the password still redacting itself.

## Writing your own provider

If your source of truth is homegrown — an internal config service, a weird legacy database table — you can teach mamori about it. The interface is intentionally tiny:

```go
type Provider interface {
	Scheme() string
	Resolve(ctx context.Context, ref Ref) (Value, error)
}
```

A minimal implementation looks like this:

```go
func (p *Provider) Resolve(ctx context.Context, ref mamori.Ref) (mamori.Value, error) {
	raw, err := p.fetch(ctx, ref.Path)
	if isNotFound(err) {
		return mamori.Value{}, mamori.ErrNotFound // MUST satisfy errors.Is
	}
	if err != nil {
		return mamori.Value{}, err
	}
	if ref.Key != "" {
		raw, err = mamori.SelectKey(raw, ref.Key) // implements #key against a JSON payload
		if err != nil {
			return mamori.Value{}, err
		}
	}
	return mamori.Value{
		Bytes:     raw,
		Version:   mamori.VersionHash(raw), // change detection; use a native revision if you have one
		Sensitive: true,                    // true for secret-bearing sources
	}, nil
}

func init() { mamori.Register(New()) } // database/sql pattern; panics on a duplicate scheme
```

The `Version` field is what powers cheap change detection: if your backend exposes a revision (a `VersionId`, a Vault version, an mtime hash), return it; otherwise `mamori.VersionHash(bytes)` gives you a stable FNV hash for free. Two optional interfaces let you do better when the backend supports it:

```go
type WatchableProvider interface {
	Provider
	Watch(ctx context.Context, ref Ref) (<-chan Update, error)
}

type BatchProvider interface {
	Provider
	ResolveBatch(ctx context.Context, refs []Ref) (map[string]Value, error)
}
```

Implement `Watch` **only** if your backend can genuinely push — otherwise let mamori's poller do the work, so behavior stays consistent across providers. Implement `ResolveBatch` if you can fetch many refs in one round trip (the AWS provider does this automatically).

Best of all, you don't have to trust yourself to get the contract right. There's a conformance kit — `github.com/xavidop/mamori/providertest` — that exercises resolution, not-found typing, version monotonicity, concurrency, context cancellation, native watching, goroutine hygiene, and even asserts you never accidentally log the payload. Point it at your provider and it tells you if you've broken the rules.

## Middleware: cache, failover, audit, rate-limit

Because every provider is just a `Provider`, you can wrap one in another. The `middleware` package ships the decorators you'd otherwise reinvent:

| Middleware | What it does |
| --- | --- |
| `Cache(ttl, inner)` | Memoize successful resolves. Errors and not-found are **not** cached. |
| `Failover(primary, replicas...)` | Try the primary, fall back to replicas on transport errors. Not-found is authoritative. |
| `RateLimit(rps, inner)` | Cap resolves per second so you don't trip your secrets backend's throttle. |
| `Audit(logger, inner)` | Log scheme, ref, latency, and outcome — never the value. |
| `Prefix(prefix, inner)` | Namespace every ref path — handy for multi-tenant setups. |

They compose by nesting, so you can read the stack top-down:

```go
import "github.com/xavidop/mamori/middleware"

mamori.WithProvider(
	middleware.Cache(5*time.Minute,
		middleware.Audit(logger,
			middleware.RateLimit(10,
				middleware.Failover(primarySM, replicaSM),
			),
		),
	),
)
```

Crucially, the shipped middleware preserves the `WatchableProvider` and `BatchProvider` capabilities of whatever they wrap — decorating a provider never silently downgrades it from push to poll.

## Observability out of the box

The core takes no OpenTelemetry dependency (keeping it lean), but there's a bridge module when you want metrics and traces:

```bash
go get github.com/xavidop/mamori/x/otel
```

```go
import (
	"go.opentelemetry.io/otel"
	mamoriotel "github.com/xavidop/mamori/x/otel"
	"github.com/xavidop/mamori"
)

meter, _ := mamoriotel.NewMeter(otel.Meter("mamori"))
tracer := mamoriotel.NewTracer(otel.Tracer("mamori"))

w, err := mamori.Watch[Config](ctx,
	mamori.WithMeter(meter),
	mamori.WithTracer(tracer),
)
```

You get a `mamori.resolve.duration` histogram, `mamori.refresh.count` and `mamori.watch.errors` counters (all tagged by `scheme`), and a span per resolve. And because `WithMeter`/`WithTracer` take tiny internal interfaces, you can implement them against Prometheus, statsd, or a test recorder without pulling OTel into your binary at all.

## A complete, runnable example

Here is the whole loop — load, watch, react — in one file you can run today (it's the `examples/basic` program from the repo):

```go
package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"time"

	"github.com/xavidop/mamori"
	"github.com/xavidop/mamori/secret"
)

const tokenPath = "/tmp/mamori-example-token"

type Config struct {
	LogLevel string        `source:"env:LOG_LEVEL" default:"info" validate:"oneof=debug info warn error"`
	Workers  int           `source:"env:WORKERS" default:"4" validate:"gte=1,lte=256"`
	APIToken secret.String `source:"file:///tmp/mamori-example-token"`
}

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))
	_ = os.WriteFile(tokenPath, []byte("initial-token"), 0o600)
	defer func() { _ = os.Remove(tokenPath) }()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	w, err := mamori.Watch[Config](ctx,
		mamori.WithPollInterval(2*time.Second),
		mamori.OnChange(func(ev mamori.Change[Config]) {
			for _, f := range ev.Fields {
				logger.Info("config changed", "field", f.Path, "from", f.OldVersion, "to", f.NewVersion)
			}
			if ev.Changed("APIToken") {
				logger.Info("rotating clients with the new API token", "token", ev.New.APIToken)
			}
		}),
		mamori.OnError(func(err error) { logger.Warn("reconcile error", "err", err) }),
	)
	if err != nil {
		logger.Error("watch failed", "err", err)
		os.Exit(1)
	}
	defer func() { _ = w.Close() }()

	cfg := w.Get()
	logger.Info("loaded config", "logLevel", cfg.LogLevel, "workers", cfg.Workers, "apiToken", cfg.APIToken)

	// Simulate a rotation a few seconds in.
	go func() {
		time.Sleep(3 * time.Second)
		_ = os.WriteFile(tokenPath, []byte("rotated-token"), 0o600)
	}()

	time.Sleep(8 * time.Second)
	logger.Info("final config", "apiToken", w.Get().APIToken)
}
```

```bash
LOG_LEVEL=debug WORKERS=8 go run ./examples/basic
```

Notice the `token` field in the log output: it prints `[REDACTED]` every time, even though the program is actively rotating it. That's the whole philosophy in one demo — live rotation, no restart, and nothing leaks.

## When to reach for mamori (and when not)

**Reach for it when:**

- Your config or secrets genuinely change while the process runs, and you want to react in memory instead of bouncing pods.
- You pull from more than one source and are tired of a different SDK and refresh strategy for each.
- Secret hygiene matters and you want redaction and a `go vet` guardrail for free.
- You run outside Kubernetes, or you're on Kubernetes but want to skip the `Secret`-sync hop.

**Probably skip it when:**

- Your config is a log level and a port from the environment, read once at boot. `os.Getenv` is fine — don't add a dependency.
- You need a secrets *store* (encryption at rest, a server component) — that's Vault's job, not mamori's.
- You're syncing secrets *between* stores — that's what ESO, `vals`, and `teller` are for.

## Wrapping up

mamori is the library I wish I'd had every time I typed `type ConfigManager struct` for the fifth time. It takes the boring, error-prone, security-sensitive plumbing — load, validate, watch, redact, reconcile — and makes it a typed struct and one function call.

It's **open source under the MIT license** and currently at `v0.1.0` — early, pre-1.0, and moving fast, so feedback and issues are genuinely welcome. Give it a spin:

```bash
go get github.com/xavidop/mamori
```

- **Docs:** [mamorigo.dev/docs](https://mamorigo.dev/docs)
- **Homepage:** [mamorigo.dev](https://mamorigo.dev)
- **Source:** [github.com/xavidop/mamori](https://github.com/xavidop/mamori)

### Provider deep-dives

If you live on a particular platform, I've written focused, hands-on companions:

- [Hot-reloading Kubernetes Secrets and ConfigMaps in Go — no pod restarts](/kubernetes/2026-07-22-mamori-hot-reload-kubernetes-secrets-configmaps-go/)
- [Rotating AWS Secrets Manager secrets without restarting your Go service](/aws/2026-07-22-mamori-rotate-aws-secrets-manager-go/)
- [GCP Secret Manager, live-reloaded in Go](/gcp/2026-07-22-mamori-gcp-secret-manager-live-reload-go/)
- [Azure Key Vault secrets that reconcile themselves in Go](/azure/2026-07-22-mamori-azure-key-vault-go/)

If you build something with it, or write a provider for a backend I haven't covered yet, I'd love to hear about it. Happy coding!
