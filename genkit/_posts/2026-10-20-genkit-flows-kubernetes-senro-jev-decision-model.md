---
layout: post
title: "Genkit Flows on Kubernetes, Routed by a Decision Model: senro + jev in Go (English)"
description: >
  Run every step of an AI pipeline as a Genkit flow inside a Kubernetes pod, and let jev, a decision model reached through Genkit's System One plugin, decide which steps run next. senro's Kubernetes executor does the pods, the workspaces and the secrets; a 200 ms typed decision does the routing and the guardrail. A practical guide with a local kind cluster, real Gemini and jev calls, and every output pasted from the run.
image: /assets/img/blog/post-headers/genkit-k8s-senro-jev.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [genkit]
tags:
  - genkit
  - senro
  - kubernetes
  - golang
  - ai
  - pipelines
keywords:
  - genkit
  - genkit-go
  - senro
  - kubernetes
  - kind
  - jev
  - system-one
  - decision-model
  - typesafe
  - golang
  - go
  - ai-pipelines
  - flows
  - orchestration
  - gemini
  - guardrails
  - routing
  - generative-ai
  - llm

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

[Genkit flows as senro steps]({% post_url genkit/2026-09-11-genkit-flows-senro-ai-pipelines-go %}) showed how to put a Genkit flow inside a [senro](https://github.com/xavidop/senro) step and get retries, caching and an event stream for every model call. Every step in that article ran on your own machine.

This one moves the steps into Kubernetes and adds a second kind of model. **Gemini writes. jev decides.** [jev](https://typesafe.ai) is a decision model: it does not generate text, it evaluates a state against typed questions and answers each one with a probability, in a few hundred milliseconds. Genkit Go 1.14 reaches it through the [System One plugin](https://genkit.dev/docs/go/integrations/system-one/), and a decision is one `genkit.GenerateData` call whose output type is the question set.

That makes jev the right model to sit at the switch points of a pipeline. In this guide it decides twice: which department's workflow runs for a support ticket, and whether the reply Gemini drafted is safe to send.

Everything below runs against the real Gemini API (`gemini-3.8-flash`) and the real TypeSafe API (`jev-latest`), on Genkit Go v1.14.0, senro v1.4.5 and a local [kind](https://kind.sigs.k8s.io) cluster on Kubernetes 1.37. The code is in [genkit-k8s-flows-jev](https://github.com/xavidop/genkit-k8s-flows-jev).

## Why a decision model decides and a chat model writes

Asking a chat model "which team should own this ticket, answer with one word" works until it does not: you get prose around the word, a department that is not on the list, no idea how sure the model was, and a second or two of latency for a decision that should take milliseconds. A decision model is built for exactly that call.

| | Chat model as router | Decision model as router |
|---|---|---|
| Answer | Text you parse | A typed field: `Choice[Dept]`, `Noul`, `Score[L]` |
| Options | In the prompt, hoped for in the output | In the Go type, enforced by the schema |
| Confidence | None, or whatever the model says about itself | A probability per option, calibrated per model version |
| Tools | Can be called by accident | Refused by the protocol |
| Latency | Seconds | A few hundred milliseconds |
| Cost per decision | Tokens for the state and the prose | Tokens for the state |

![Full-width image](/assets/img/blog/genkit-k8s-jev/two-models.png){:.lead data-width="800" data-height="100"}

And the reverse is just as true. jev cannot write the reply to the customer, explain an outage or summarise a brief. That is what `gemini-3.8-flash` is for. The pipeline needs both, and senro is what puts each call in its own step, on its own pod, with its own log, retry policy and secret.

## What we are building

A support-ticket pipeline. A raw email comes in; a reply goes out, or a brief goes to a human, or both.

![Full-width image](/assets/img/blog/genkit-k8s-jev/two-runs.png){:.lead data-width="800" data-height="100"}

Two runs, because of one rule in senro: **a `When` condition is evaluated once, at run start, against facts the run already has, never against something a step produces.** So the first run understands the ticket and decides, and the decision becomes the **run parameters** of the second run, where `senro.When(senro.ParamIs(...))` prunes every branch the verdict did not pick before anything starts. Pruned steps settle as `skipped_condition` and the run stays green.

| Run | Step | Where | Model | Writes |
|---|---|---|---|---|
| `triage` | `seed` | coordinator | none | puts the raw email into the run's workspace |
| `triage` | `ingest` | pod | Gemini | `ticket.json`, a structured ticket |
| `triage` | `triage` | pod | jev | `decision.json`: department, urgency, frustration, needs a human |
| `triage` | `collect` | coordinator | none | copies both files out of the run |
| `resolve` | `<dept>/draft` | pod | Gemini | `reply.md`, following that department's playbook |
| `resolve` | `<dept>/verify` | pod | jev | `verdict.json`; a rejection fails the step |
| `resolve` | `<dept>/send` | coordinator | none | the reply, only if `verify` passed |
| `resolve` | `escalate/brief` | pod | Gemini | `brief.md` for a human, when jev said so |

Inside a branch, jev is a guardrail: `verify` reads the draft against the playbook, and if it rejects the draft, the step fails and senro skips `send`. The second decision also determines the next step, this time without leaving the run.

## What you need

- Go 1.27 or newer, Docker, [kind](https://kind.sigs.k8s.io) and `kubectl`
- `GEMINI_API_KEY` and `TYPESAFE_API_KEY` in your environment
- the [senro CLI](https://xavidop.github.io/senro/docs/install/) if you want the terminal UI (optional)

```bash
go get github.com/firebase/genkit/go@v1.14.0
go get github.com/xavidop/senro@v1.4.5
go get github.com/xavidop/mamori
```

[mamori](https://github.com/xavidop/mamori) is the library senro uses to resolve secrets. It is how the two API keys reach the pods without ever being in a pod spec.

## Step 1: a cluster senro can reach

senro's Kubernetes executor **never reads `KUBECONFIG`, `~/.kube/config` or your current context.** A kubeconfig typically holds a dozen contexts, most of them production, with whichever one you last used selected; a pipeline that inherited that would eventually deploy into the wrong cluster. Instead, the cluster comes from three environment variables, read at run start:

| Variable | What it is |
|---|---|
| `SENRO_K8S_SERVER` | The apiserver URL |
| `SENRO_K8S_CA_FILE` | The cluster CA, as a PEM file. senro will not skip verification |
| `SENRO_K8S_TOKEN_FILE` | A bearer token in a file (or a client certificate and key) |

So a local cluster needs four things: kind, a namespace, an identity with the permissions the executor documents, and those three files. The repo's `scripts/cluster-up.sh` does all of it; this is what it runs.

```bash
kind create cluster --name senro-ai --kubeconfig .kind/kubeconfig
export KUBECONFIG=$PWD/.kind/kubeconfig
kubectl apply -f k8s/rbac.yaml
```

The RBAC is the exact set senro needs and nothing more: in the namespace, `create`, `get` and `delete` on pods, `get` on `pods/log`, `create` **and `get`** on `pods/exec`, and `create`, `patch`, `delete` on secrets. At cluster scope, `list` and `get` on nodes, which is how senro reads the platform it has to compile for.

The `get` on `pods/exec` is the one to remember. Workspaces, the pipeline binary and `senro shell` all cross over the exec subresource, and senro speaks the WebSocket exec protocol (`v5.channel.k8s.io`, Kubernetes 1.29 or newer), which is a `GET` on that subresource. A Role with only `create`, the verb the SPDY protocol uses, fails every step with a 403 that surfaces as `reading workspace "case" to send it to pod ...: EOF`.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: senro-steps
  namespace: support
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["create", "get", "delete"]
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get"]
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create", "get"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["create", "patch", "delete"]
```

Then the three files, pulled out of the kubeconfig kind wrote and a short-lived ServiceAccount token:

```bash
kubectl config view --minify --raw -o jsonpath='{.clusters[0].cluster.server}' > .kind/server
kubectl config view --minify --raw \
  -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 -d > .kind/ca.crt
kubectl -n support create token senro --duration=4h > .kind/token

export SENRO_K8S_SERVER=$(cat .kind/server)
export SENRO_K8S_CA_FILE=$PWD/.kind/ca.crt
export SENRO_K8S_TOKEN_FILE=$PWD/.kind/token
```

A file rather than `SENRO_K8S_TOKEN` inline, because an environment variable is visible in `/proc/<pid>/environ` and inherited by every child process the coordinator spawns.

## Step 2: the flows

Five flows, in one file. Nothing here knows about senro or Kubernetes.

### Gemini turns an email into a ticket

```go
type Ticket struct {
	Customer string   `json:"customer"`
	Company  string   `json:"company,omitempty"`
	Summary  string   `json:"summary"`
	Ask      string   `json:"ask"`
	Facts    []string `json:"facts"`
}

f.Ingest = genkit.DefineFlow(g, "ingestTicket", func(ctx context.Context, raw string) (Ticket, error) {
	t, _, err := genkit.GenerateData[Ticket](ctx, g,
		ai.WithModelName("googleai/gemini-3.8-flash"),
		ai.WithSystem("You turn raw support emails into a structured ticket. "+
			"Facts are identifiers, amounts, dates and error codes quoted from the email, nothing inferred."),
		ai.WithPrompt("Email:\n\n%s", raw))
	if err != nil {
		return Ticket{}, err
	}
	if t == nil {
		return Ticket{}, fmt.Errorf("ingest: the model returned no ticket")
	}
	return *t, nil
})
```

### jev decides what the ticket is

With the System One plugin, **the output type is the question set.** Each field is one question, its `jsonschema_description` tag is the instruction, and the options, levels and criteria belong to Go types, so the same question means the same thing wherever it is asked.

```go
import systemonex "github.com/firebase/genkit/go/plugins/systemone/exp"

type Dept string

func (Dept) Criteria() map[Dept]string {
	return map[Dept]string{
		"billing":   "Charges, invoices, refunds, subscriptions, plan changes",
		"technical": "Bugs, errors, outages, latency, integrations, webhooks, API",
		"account":   "Login, password, permissions, data export or deletion, privacy",
		"other":     "None of the above",
	}
}

type Frustration int

func (Frustration) Levels() []string { return []string{"Calm", "Annoyed", "Angry", "Furious"} }

type Urgent struct{}

func (Urgent) Criteria() (yes, no string) {
	return "Names a deadline, says now or today, or describes an outage in progress",
		"No time pressure is expressed, or the customer says there is no rush"
}

type Triage struct {
	Department  systemonex.Choice[Dept]       `json:"department" jsonschema_description:"Which team should own this ticket?"`
	IsUrgent    systemonex.NoulOf[Urgent]     `json:"is_urgent" jsonschema_description:"Does the ticket communicate time pressure?"`
	Frustration systemonex.Score[Frustration] `json:"frustration" jsonschema_description:"How frustrated is the customer?"`
	NeedsHuman  systemonex.Noul               `json:"needs_human" jsonschema_description:"Does resolving this need a human: a legal threat, a contract or SLA dispute, data loss, or a refund outside the playbook?"`
}
```

Four question kinds cover the protocol. `Choice[T]` picks one of `T.Criteria()` and gives a probability per option plus a `Confidence`. `Score[L]` rates on `L.Levels()` and answers `Level()` and `Label()`. `Noul` is "is this true?" as a probability, where 0.5 means the model could not tell. `NoulOf[C]` is the same with `C.Criteria()` saying what yes and no mean.

![Full-width image](/assets/img/blog/genkit-k8s-jev/question-types.png){:.lead data-width="800" data-height="100"}

The flow sends the ticket as a **data part**, so the state is a JSON object and a question can refer to a field by name. It then turns the four answers into a flat verdict, with thresholds that belong to the caller:

```go
type Decision struct {
	Department  string  `json:"department"`
	Confidence  float64 `json:"confidence"`
	Urgent      bool    `json:"urgent"`
	Frustration string  `json:"frustration"`
	Escalate    bool    `json:"escalate"`
	Model       string  `json:"model"`
}

f.Triage = genkit.DefineFlow(g, "triageTicket", func(ctx context.Context, t Ticket) (Decision, error) {
	out, resp, err := genkit.GenerateData[Triage](ctx, g,
		ai.WithModelName("typesafe/jev-latest"),
		ai.WithPromptParts(ai.NewDataPart(t)))
	if err != nil {
		return Decision{}, err
	}
	d := Decision{
		Department:  string(out.Department.Choice),
		Confidence:  out.Department.Confidence,
		Urgent:      out.IsUrgent.Probability >= 0.5,
		Frustration: out.Frustration.Label(),
		Model:       systemonex.ResponseInfo(resp).Model,
	}
	// A low-confidence routing decision is not a routing decision.
	if d.Confidence < 0.5 {
		d.Department = "other"
	}
	d.Escalate = d.Department == "other" ||
		out.NeedsHuman.Probability >= 0.6 ||
		out.Frustration.Level() >= 3
	return d, nil
})
```

`ResponseInfo(resp).Model` records which jev version answered. Confidence thresholds are calibrated per version, so a verdict that does not say who produced it is a threshold waiting to drift.

### Gemini drafts, jev reviews

The draft flow is an ordinary `GenerateData[Reply]` call with the playbook and the ticket in the prompt. One difference from the triage flow: the ticket goes to Gemini as JSON **text**, not as a data part. `ai.NewDataPart` is how a decision model takes an object state; the Gemini plugin refuses it in a user message with `could not convert media part to genai part: missing file data`.

```go
f.Draft = genkit.DefineFlow(g, "draftReply", func(ctx context.Context, in DraftInput) (Reply, error) {
	r, _, err := genkit.GenerateData[Reply](ctx, g,
		ai.WithModelName("googleai/gemini-3.8-flash"),
		ai.WithSystem("You are a support agent for Acme Cloud. Write the reply the customer will receive. "+
			"Follow the playbook strictly. Never state amounts, dates or identifiers that are not in the ticket. "+
			"Plain text, under 180 words, sign as 'Acme Cloud Support'."),
		ai.WithPrompt("Playbook:\n%s\n\n%s\n\nTicket:\n%s", in.Playbook, urgency, asJSON(in.Ticket)))
	// ...
})
``` The review flow is the second decision, and it asks different questions of a different state: the ticket, the draft and the playbook, together.

```go
type Overpromise struct{}

func (Overpromise) Criteria() (yes, no string) {
	return "Commits to a refund amount, a credit, a release date, a deadline, or a deletion the playbook does not allow",
		"Every commitment in the reply is one the playbook permits"
}

type Tone int

func (Tone) Levels() []string { return []string{"Cold or dismissive", "Neutral", "Warm and specific"} }

type Review struct {
	Addresses    systemonex.Noul                `json:"addresses" jsonschema_description:"Does the reply address what the customer actually asked for?"`
	Overpromises systemonex.NoulOf[Overpromise] `json:"overpromises" jsonschema_description:"Does the reply promise something the playbook forbids?"`
	Invents      systemonex.Noul                `json:"invents" jsonschema_description:"Does the reply state amounts, dates, identifiers or causes that appear in neither the ticket nor the playbook?"`
	Tone         systemonex.Score[Tone]         `json:"tone" jsonschema_description:"How does the reply read to the customer?"`
}

f.Verify = genkit.DefineFlow(g, "verifyReply", func(ctx context.Context, in VerifyInput) (Verdict, error) {
	out, _, err := genkit.GenerateData[Review](ctx, g,
		ai.WithModelName("typesafe/jev-latest"),
		ai.WithSystem("The state has the customer's ticket, the reply an agent drafted, and the playbook the agent had to follow."),
		ai.WithPromptParts(ai.NewDataPart(in)))
	if err != nil {
		return Verdict{}, err
	}
	v := Verdict{Addresses: out.Addresses.Probability, Overpromises: out.Overpromises.Probability,
		Invents: out.Invents.Probability, Tone: out.Tone.Label()}
	if v.Addresses < 0.6 {
		v.Reasons = append(v.Reasons, "the reply does not address the customer's ask")
	}
	if v.Overpromises >= 0.5 {
		v.Reasons = append(v.Reasons, "the reply promises something the playbook forbids")
	}
	if v.Invents >= 0.5 {
		v.Reasons = append(v.Reasons, "the reply invents facts")
	}
	if out.Tone.Level() == 0 {
		v.Reasons = append(v.Reasons, "the tone is cold")
	}
	v.Approved = len(v.Reasons) == 0
	return v, nil
})
```

A system message is never part of the state with this plugin. It goes in front of every question's instructions, which is the right place to say what the state is.

## Step 3: flows as steps that can run in a pod

A senro func step is a registered Go function. In the local-only article the flow lived in a package variable that `main` filled in. **In a pod that does not work**, because senro runs a func step by sending your pipeline binary into the pod and re-entering it as a fresh process; `main` never gets to the line that initialised Genkit. So Genkit is initialised lazily, inside the step, from the secrets senro delivered to that pod:

```go
var (
	engineOnce sync.Once
	engine     *Flows
	engineErr  error
)

func flows(ctx senro.Ctx) (*Flows, error) {
	engineOnce.Do(func() {
		var plugins []api.Plugin
		gemini, err := readSecret(ctx, "Gemini")
		if err != nil {
			engineErr = err
			return
		}
		if gemini != "" {
			plugins = append(plugins, &googlegenai.GoogleAI{APIKey: gemini})
		}
		typesafe, err := readSecret(ctx, "TypeSafe")
		if err != nil {
			engineErr = err
			return
		}
		if typesafe != "" {
			ts := systemonex.TypeSafe()
			ts.APIKey = typesafe
			plugins = append(plugins, ts)
		}
		g := genkit.Init(ctx, genkit.WithPlugins(plugins...))
		engine = defineFlows(g)
	})
	return engine, engineErr
}

// ctx.Secret hands back a file path, never the value.
func readSecret(ctx senro.Ctx, name string) (string, error) {
	path := ctx.Secret(name)
	if path == "" {
		return "", nil
	}
	b, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("reading secret %s: %w", name, err)
	}
	return strings.TrimSpace(string(b)), nil
}
```

Two details matter here. `senro.Ctx` embeds `context.Context`, so it goes straight into `genkit.Init` and into `flow.Run`. And `ctx.Secret(name)` is a **path**: in the pod it points at a `0400` file under `/run/senro/secrets`, projected from a short-lived, immutable Kubernetes `Secret` with an owner reference to the pod. The key is never in the pod spec, never in `env`, never in the plan, never in a log. That is also why the plugin fields are set explicitly: the Gemini plugin would otherwise read `GEMINI_API_KEY` from the environment, and in the pod that variable holds the file's path.

![Full-width image](/assets/img/blog/genkit-k8s-jev/secrets-path.png){:.lead data-width="800" data-height="100"}

The steps themselves are short. Each one reads from the `case` workspace, runs a flow, and writes back:

```go
const workspace = "case"

func init() {
	senro.RegisterFunc("ai/ingest", Ingest)
	senro.RegisterFunc("ai/triage", TriageStep)
	senro.RegisterFunc("ai/draft", Draft)
	senro.RegisterFunc("ai/verify", Verify)
	senro.RegisterFunc("ai/brief", Brief)
	senro.RegisterFunc("ai/collect", Collect)
	senro.RegisterFunc("ai/seed", Seed)
	senro.RegisterFunc("ai/send", Send)
}

func Ingest(ctx senro.Ctx, p IngestParams) error {
	f, err := flows(ctx)
	if err != nil {
		return err
	}
	raw, err := os.ReadFile(wsPath(ctx, p.File))
	if err != nil {
		return err
	}
	t, err := f.Ingest.Run(ctx, string(raw))
	if err != nil {
		return err
	}
	fmt.Fprintf(ctx.Stdout(), "ticket from %s: %s\n", t.Customer, t.Summary)
	return writeJSON(ctx, "ticket.json", t)
}

func TriageStep(ctx senro.Ctx, _ NoParams) error {
	f, err := flows(ctx)
	if err != nil {
		return err
	}
	var t Ticket
	if err := readJSON(ctx, "ticket.json", &t); err != nil {
		return err
	}
	d, err := f.Triage.Run(ctx, t)
	if err != nil {
		return err
	}
	fmt.Fprintf(ctx.Stdout(), "%s decided: department=%s (confidence %.2f) urgent=%v frustration=%q escalate=%v\n",
		d.Model, d.Department, d.Confidence, d.Urgent, d.Frustration, d.Escalate)
	return writeJSON(ctx, "decision.json", d)
}

func Verify(ctx senro.Ctx, p PlaybookParams) error {
	// ...read ticket.json and reply.json, run f.Verify...
	if err := writeJSON(ctx, "verdict.json", v); err != nil {
		return err
	}
	if !v.Approved {
		return fmt.Errorf("reply rejected: %v", v.Reasons)
	}
	return nil
}
```

`Verify` returning an error is the guardrail. A func step that returns an error is a `failed` step, and senro settles every dependent of a failed step as `skipped_upstream_failed`.

The last thing a pod needs from `main` is one line before flag parsing, so that senro's re-entry does not hit your flags:

```go
func main() {
	ctx := context.Background()
	if handled, err := senro.StepChild(ctx); handled {
		if err != nil {
			log.Fatal(err)
		}
		return
	}
	ticketPath := flag.String("ticket", "tickets/double-charge.txt", "raw ticket to process")
	// ...
}
```

## Step 4: the Kubernetes target

One target, used by every AI workflow:

```go
import "github.com/xavidop/senro/executor/k8s"

const stepImage = "docker.io/library/alpine:3.22@sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8"

func pods() senro.ExecutorTarget {
	return k8s.Pod(stepImage,
		k8s.Namespace("support"),
		k8s.Resources(
			map[string]string{"cpu": "250m", "memory": "128Mi"},
			map[string]string{"cpu": "1", "memory": "512Mi"},
		))
}
```

Three rules of this executor show up in those six lines:

- **The image must be pinned to a digest** and the namespace must be stated, or `Build()` refuses the pipeline. There is no fallback to `default`.
- **The image needs `sh` and `tar`, and nothing else.** Alpine is 3 MB. Your pipeline binary is not in the image; senro cross-compiles it with `CGO_ENABLED=0`, sends it in as a tar over the apiserver's `exec` subresource, and re-enters it. No registry, no Dockerfile, no build step for your code.
- **Requests and limits apply to the step's container only.** senro adds two containers of its own when a step mounts a workspace: an init container that fills the `emptyDir`, and an idle container that keeps the pod alive so the result can be read back out.

![Full-width image](/assets/img/blog/genkit-k8s-jev/pod-anatomy.png){:.lead data-width="800" data-height="100"}

Every workspace byte crosses the apiserver twice per attempt, in and out. For a few JSON files that is nothing. For a gigabyte of inputs, fetch them inside the pod under `NoSnapshot()` instead.

## Step 5: run one, the triage

```go
func triagePipeline(ticketPath, outDir string) *senro.Pipeline {
	p := senro.New("triage")
	ws := senro.Workspace(workspace)

	// The raw email enters the workspace from the coordinator, so the ingest
	// step can declare it as an input and be cached on it.
	intake := p.Workflow("intake", senro.On(senro.Local()))
	intake.Step("seed", senro.Func("ai/seed", DirParams{
		Dir:   filepath.Dir(ticketPath),
		Files: []string{filepath.Base(ticketPath)},
	})).Mount(ws.At("/case", senro.RW))

	understand := p.Workflow("understand", senro.Needs("intake"), senro.On(pods()))

	understand.Step("ingest", senro.Func("ai/ingest", IngestParams{File: filepath.Base(ticketPath)})).
		Mount(ws.At("/case", senro.RW)).
		SecretEnv("GEMINI_API_KEY", "Gemini").
		Timeout(stepTimeout).
		Retry(3, retry.OnInfra()).
		Pure().
		Inputs(artifact.File(filepath.Base(ticketPath))).
		Outputs(artifact.File("ticket.json"))

	understand.Step("triage", senro.Func("ai/triage", NoParams{})).
		Needs("ingest").
		Mount(ws.At("/case", senro.RW)).
		SecretEnv("TYPESAFE_API_KEY", "TypeSafe").
		Timeout(stepTimeout).
		Retry(3, retry.OnInfra()).
		Pure().
		Inputs(artifact.File("ticket.json")).
		Outputs(artifact.File("decision.json"))

	handoff := p.Workflow("handoff", senro.Needs("understand"), senro.On(senro.Local()))
	handoff.Step("collect", senro.Func("ai/collect", DirParams{
		Dir:   outDir,
		Files: []string{"ticket.json", "decision.json"},
	})).Mount(ws.At("/case", senro.RO))

	return p
}
```

Each step names only the secret it needs: the Gemini step never sees the TypeSafe key and the jev step never sees the Gemini key. `Timeout` is not decoration on a remote func step; the function has a process of its own in the pod, and the deadline is what ends it if the coordinator dies. The two pod steps are `Pure()` with explicit `Inputs` and `Outputs`, which `Build()` insists on: a `Pure()` step with no `Inputs` is refused, because its cache key could never change when its sources do. `seed` and `collect` run on the coordinator with the workspace mounted, and `collect` copies the two files to disk, which is how the verdict crosses into the second run.

The keys are declared once, as a struct mamori resolves from the environment:

```go
type Secrets struct {
	Gemini   secret.String `source:"env:GEMINI_API_KEY"`
	TypeSafe secret.String `source:"env:TYPESAFE_API_KEY"`
}

secrets, err := mamori.Load[Secrets](ctx)

run := func(p *senro.Pipeline, extra ...senro.Option) error {
	att, err := attach.Listen(ctx, attach.Options{Bind: attach.AutoUnixSocket, Pipeline: p.Name()})
	if err != nil {
		return err
	}
	defer func() { _ = att.Close() }()
	opts := append([]senro.Option{
		senro.WithAttach(att),
		senro.WithSecrets(secrets),
		senro.WithFuncBuild("."),
	}, extra...)
	return senro.Run(ctx, p, opts...)
}

err = run(triagePipeline(ticket, out))
```

`WithFuncBuild(".")` names the package senro cross-compiles for the pods. On a macOS coordinator every func step in a pod needs it, because the pod is Linux. `WithAttach` is what lets `senro run` and `senro attach` render the run live; without it the run still works, it just cannot be watched.

Run it against the first sample ticket, a double charge with a deadline. The senro CLI builds the package, runs it and attaches; on a TTY you get the terminal UI, and with `--ui=plain` the same events as lines:

```bash
senro run . --ui=plain -- -ticket tickets/double-charge.txt
```

```
seed started
seed succeeded
ingest started
ingest stderr | 2026/10/20 22:14:40 INFO Genkit initialized env=prod plugins=[googleai] duration=2ms
ingest stdout | ticket from Marta Ruiz: Card charged twice for invoice INV-2291
ingest succeeded
triage started
triage stderr | 2026/10/20 22:14:48 INFO Genkit initialized env=prod plugins=[typesafe] duration=1ms
triage stdout | jev-1.13.0 decided: department=billing (confidence 1.00) urgent=true frustration="Annoyed" escalate=false
triage succeeded
collect started
collect stdout | collected ticket.json
collect stdout | collected decision.json
collect succeeded
run succeeded
```

That is a Gemini call and a jev call, each in its own pod, each initialising Genkit with exactly one plugin, with its own log under `runs/<id>/`. The `ingest` step took about seven seconds and the `triage` step about three, pod creation, the 34 MB pipeline binary crossing the apiserver and the model call included. `jev-latest` resolved to `jev-1.13.0`, and the decision says so. The verdict lands in `out/decision.json`:

```json
{
  "department": "billing",
  "confidence": 1,
  "urgent": true,
  "frustration": "Annoyed",
  "escalate": false,
  "model": "jev-1.13.0"
}
```

And `out/ticket.json` is what Gemini extracted, facts quoted rather than inferred:

```json
{
  "customer": "Marta Ruiz",
  "company": "Lumen Logistics",
  "summary": "Customer was charged twice for invoice INV-2291 on March 3rd",
  "ask": "Refund the duplicate charge today",
  "facts": ["INV-2291", "59.00 EUR", "March 3rd"]
}
```

## Step 6: let the verdict choose the next steps

The second pipeline declares every branch. The parameters decide which ones run.

```go
func resolvePipeline(outDir string, reckless bool) *senro.Pipeline {
	p := senro.New("resolve")
	ws := senro.Workspace(workspace)

	intake := p.Workflow("intake", senro.On(senro.Local()))
	intake.Step("seed", senro.Func("ai/seed", DirParams{
		Dir:   outDir,
		Files: []string{"ticket.json", "decision.json"},
	})).Mount(ws.At("/case", senro.RW))

	for _, d := range departments {
		draftPlaybook := d.Playbook
		if reckless {
			draftPlaybook = recklessPlaybook // see Step 7
		}
		w := p.Workflow(d.Name,
			senro.Needs("intake"),
			senro.On(pods()),
			senro.When(senro.ParamIs("department", d.Name)))

		w.Step(d.Name+"/draft", senro.Func("ai/draft", PlaybookParams{Playbook: draftPlaybook})).
			Mount(ws.At("/case", senro.RW)).
			SecretEnv("GEMINI_API_KEY", "Gemini").
			Timeout(stepTimeout).
			Retry(3, retry.OnInfra())

		w.Step(d.Name+"/verify", senro.Func("ai/verify", PlaybookParams{Playbook: d.Playbook})).
			Needs(d.Name + "/draft").
			Mount(ws.At("/case", senro.RW)).
			SecretEnv("TYPESAFE_API_KEY", "TypeSafe").
			Timeout(stepTimeout).
			Retry(3, retry.OnInfra())

		send := p.Workflow(d.Name+"-send",
			senro.Needs(d.Name),
			senro.On(senro.Local()),
			senro.When(senro.ParamIs("department", d.Name)))
		send.Step(d.Name+"/send", senro.Func("ai/send", DirParams{Dir: outDir})).
			Mount(ws.At("/case", senro.RO))
	}

	esc := p.Workflow("escalate",
		senro.Needs("intake"),
		senro.On(pods()),
		senro.When(senro.ParamIs("escalate", "true")))
	esc.Step("escalate/brief", senro.Func("ai/brief", NoParams{})).
		Mount(ws.At("/case", senro.RW)).
		SecretEnv("GEMINI_API_KEY", "Gemini").
		Timeout(stepTimeout).
		Retry(3, retry.OnInfra())

	// ...and an escalate-notify workflow on the coordinator that collects brief.md
	return p
}
```

The pipeline is a Go program, so the three departments are a `for` loop over a slice of playbooks, and each playbook is a step **parameter**. A func step's cache key includes the parameter digest, so editing the billing playbook changes the identity of the billing steps and nothing else.

`main` glues the two runs together with the verdict as parameters:

```go
var decision Decision
b, _ := os.ReadFile(filepath.Join(out, "decision.json"))
json.Unmarshal(b, &decision)

err = run(resolvePipeline(out, *reckless), senro.WithParams(decision.Params()))
```

```go
func (d Decision) Params() senro.Params {
	return senro.Params{
		"department": d.Department,
		"urgent":     fmt.Sprint(d.Urgent),
		"escalate":   fmt.Sprint(d.Escalate),
	}
}
```

Parameters are never recorded in an event or a cache key; they exist to be read by conditions. And this is what the second run looks like for the double-charge ticket, read back from disk with `senro attach --run <id> --ui=plain`:

```
seed succeeded
billing/draft stdout | drafted: Duplicate charge for invoice INV-2291
billing/draft succeeded
billing/verify stdout | review: addresses=0.81 overpromises=0.44 invents=0.25 tone="Warm and specific"
billing/verify stdout | approved
billing/verify succeeded
billing/send stdout | sent to customer:
billing/send succeeded
technical/draft skipped_condition
technical/verify skipped_condition
technical/send skipped_condition
account/draft skipped_condition
account/verify skipped_condition
account/send skipped_condition
escalate/brief skipped_condition
escalate/notify skipped_condition
run succeeded
```

Twelve steps declared, four executed. `technical`, `account` and `escalate` settled as `skipped_condition` before a single pod was created, and the run is `succeeded`, not `partial`: a pruned branch is not a failed one. The reply that went out, in `out/reply.md`:

```
# Update regarding duplicate charge for invoice INV-2291

Hello Marta, I understand you are under time pressure and need this resolved
urgently. Over the next few hours, our billing team will process the reversal
on your account. We can confirm that the duplicate charge of 59.00 EUR for
invoice INV-2291 from March 3rd will be refunded to your original payment
method within 5 to 10 business days. Acme Cloud Support
```

Every number in it is in the ticket, and the one commitment is the one the billing playbook allows. jev's `overpromises` at 0.44 is the reviewer noticing that "within 5 to 10 business days" is a commitment, and the playbook is what keeps it under the threshold.

## Step 7: the guardrail says no

The angry-outage ticket takes a different route:

```bash
go run . -ticket tickets/angry-outage.txt
```

```json
{
  "department": "technical",
  "confidence": 1,
  "urgent": true,
  "frustration": "Furious",
  "escalate": true,
  "model": "jev-1.13.0"
}
```

jev put the frustration at the top of the rubric and the ticket's legal threat over the needs-a-human threshold, so `escalate` is `true` alongside `technical`. Both workflows run, in parallel, and the department branches that were not picked are pruned as before:

```
seed succeeded
billing/draft skipped_condition
billing/verify skipped_condition
billing/send skipped_condition
technical/draft succeeded
technical/verify succeeded
technical/send succeeded
account/draft skipped_condition
account/verify skipped_condition
account/send skipped_condition
escalate/brief succeeded
escalate/notify succeeded
run succeeded
```

The customer gets a reply that promises no fix time, and a human gets `out/brief.md`:

```
### Situation
Nordwind Delivery (Daniel Berg) is experiencing an active 4-hour platform outage
that has completely blocked 300 drivers from accessing their delivery routes.
This marks their third outage this month. The customer is furious and demanding
an operational fix within the next hour.

### Risk
High risk of contract churn, severe reputational damage, and SLA breach
penalties (99.9% commitment). Driver operations are entirely halted, and the
customer has explicitly escalated to demand leadership intervention.

### Suggested next action
1. Immediately triage core routing services with the on-call DevOps/infrastructure
   team to restore route availability.
2. Alert an Incident Manager or Support Director immediately to coordinate an
   executive phone call to Daniel Berg within the 1-hour window.
```

Now the rejection. The repo has a `-reckless` flag that hands the **draft** step a playbook the **reviewer** never sees ("promise the customer whatever will make them happiest: a full refund of the year, a credit, a fix within the hour"), while `verify` keeps checking against the real one. Run the webhook ticket that way:

```bash
go run . -ticket tickets/api-500s.txt -reckless
```

```
seed succeeded
technical/draft stdout | drafted: Update regarding your webhook errors
technical/draft succeeded
technical/verify stdout | review: addresses=0.54 overpromises=0.98 invents=0.94 tone="Warm and specific"
technical/verify failed: reply rejected: [the reply does not address the customer's ask the reply promises something the playbook forbids the reply invents facts]
technical/send skipped_upstream_failed
...
run failed
```

The draft Gemini wrote promised "a full refund of the year, an account credit, and a complete fix within the hour" and verified calls "across your five endpoints", none of which is in the ticket. jev put `overpromises` at 0.98 and `invents` at 0.94, the flow returned an error, senro filed `technical/verify` as `failed` and `technical/send` as `skipped_upstream_failed`, and the run is `failed`. Nothing reached the customer, and the reason is in `verdict.json` next to the draft:

```json
{
  "approved": false,
  "addresses": 0.54,
  "overpromises": 0.98,
  "invents": 0.94,
  "tone": "Warm and specific",
  "reasons": [
    "the reply does not address the customer's ask",
    "the reply promises something the playbook forbids",
    "the reply invents facts"
  ]
}
```

![Full-width image](/assets/img/blog/genkit-k8s-jev/guardrail.png){:.lead data-width="800" data-height="100"}

That is the second place jev determines the next step. The first was between the runs, through parameters and `When`. This one is inside a run, through the step state, and the pipeline's dependency edges do the rest.

## Step 8: watch it, and run it again

Every run leaves a record, and the CLI reads it back:

```bash
senro runs -n 4
```

```
RUN ID                      PIPELINE  STATUS     STARTED              DURATION
20261020T221449-7a7f7bd960  resolve   succeeded  2026-10-21 00:14:49  14s
20261020T221435-c6a8ed3850  triage    succeeded  2026-10-21 00:14:38  11s
20261020T221243-8040620785  resolve   failed     2026-10-21 00:12:43  17s
20261020T221229-d56d7f7f3a  triage    succeeded  2026-10-21 00:12:29  11s
```

Every pod senro creates is labelled, so if a coordinator dies mid-run you can still find and clean up what it left:

```bash
kubectl -n support get pods,secrets -l senro.dev/managed=true
```

And the two triage steps are `Pure()`, so a second run of the same ticket does not call either model:

```
seed succeeded
ingest cached
triage cached
collect stdout | collected ticket.json
collect stdout | collected decision.json
collect succeeded
run succeeded
```

`cached` is a step state, not a label: no pod, no model call, no tokens. The recorded outputs were restored from the content store and `collect` read the same two files.

## What the combination gives you

| Concern | Who handles it |
|---|---|
| Reading and writing | Gemini, through `genkit.GenerateData` and `GenerateText` |
| Routing, scoring, guardrails | jev, through the same `GenerateData` call with a decision type |
| Where a step runs | `senro.On(k8s.Pod(...))`, one pod per step, platform read from the cluster |
| Which steps run | `senro.When(senro.ParamIs(...))`, fed by jev's verdict |
| What a rejection does | The step fails, dependents are `skipped_upstream_failed` |
| Credentials | mamori resolves, senro delivers a file per pod, per step, per attempt |
| Retries | `retry.OnInfra()`: an image pull or an evicted pod, never a model answer you did not like |
| Repeat work | `Pure()` steps with `Inputs` and `Outputs` are replayed, not re-run |
| Evidence | One `runs/<id>/` per run, with the plan, the events, and one log per step |

## Conclusion

The pattern fits in four lines:

1. Define the flows with `genkit.DefineFlow`. Make the routing and review flows return a decision type from the System One plugin.
2. Register each flow as a `senro.Func` step that initialises Genkit lazily from `ctx.Secret(...)`.
3. Point the workflows at `k8s.Pod(image@digest, k8s.Namespace(...))`, and give every remote step a `Timeout`.
4. Turn the decision into run parameters, gate workflows with `senro.When`, and let a rejected guardrail fail its step.

A decision model is cheap enough and fast enough to sit at every switch point of a pipeline, and typed enough that the switch is a Go field, not a parsed string. senro makes the switch points visible: a branch jev did not pick is a `skipped_condition` step in the event stream, with the reason one `senro cache explain` away.

- The code: [genkit-k8s-flows-jev](https://github.com/xavidop/genkit-k8s-flows-jev)
- [Decision models in Genkit Go](https://genkit.dev/docs/go/integrations/system-one/) and [Flows](https://genkit.dev/docs/go/flows/)
- [senro's Kubernetes executor](https://xavidop.github.io/senro/docs/executors/kubernetes/) and [Func steps off the coordinator](https://xavidop.github.io/senro/docs/executors/func-remote/)
- The previous article: [Genkit flows as senro steps]({% post_url genkit/2026-09-11-genkit-flows-senro-ai-pipelines-go %})
