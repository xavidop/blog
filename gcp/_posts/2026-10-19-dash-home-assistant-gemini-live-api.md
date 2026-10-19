---
layout: post
title: "Dash: An Open-Source Home Assistant Built on the Gemini 3.8 Live API (English)"
description: >
  Dash is my open-source ambient display for a wall tablet, in the spirit of a Nest Hub, with a "Hey Dash" voice assistant on top. This article is about that assistant: how the Gemini Live API works under the hood (ephemeral tokens, the WebSocket protocol, PCM audio, tool calls, Google Search grounding), what Gemini 3.8 Live changes, what it costs per question, and the design decisions that keep the API key on the server and the microphone off Gemini until you say the wake word.
image: /assets/img/blog/post-headers/dash-gemini-live.png
noindex: false
comments: true
author: xavi
kate: hl markdown;
categories: [gcp]
tags:
  - gemini
  - gemini-live
  - voice-assistant
  - nodejs
  - typescript
keywords:
  - dash
  - gemini
  - gemini-live-api
  - gemini-3.8-live
  - live-api
  - realtime-api
  - voice-assistant
  - home-assistant
  - smart-display
  - nest-hub
  - ephemeral-tokens
  - websocket
  - function-calling
  - google-search-grounding
  - nodejs
  - typescript
  - open-source

lang: en
---
{:.no_toc}
1. this unordered seed list will be replaced by toc as unordered list
{:toc}

## Introduction

I wanted a Nest Hub that I could actually program. Something on the kitchen wall that shows the time, the weather, my teams, what's cooking and what's playing, and that answers when I talk to it. That is [Dash](https://github.com/xavidop/dash): an open-source ambient display for any tablet or screen in kiosk mode, one `config.json`, six languages, free data sources, MIT.

Most of Dash needs no account at all. The part that does is the one I want to talk about here: the **"Hey Dash" voice assistant**, which runs on Google's realtime voice model, **Gemini 3.8 Live**, through the **Gemini Live API**. If you have ever wanted to build a voice assistant without stitching speech-to-text, an LLM and text-to-speech together yourself, this is the article. You will see how the Live API works at the protocol level, how Dash keeps the API key off the device, how tool calls turn speech into shopping list items and timers, and what a question costs.

Everything below is the real code from the repository, as of **October 2026**, against `gemini-3.8-live`.

![Full-width image](/assets/img/blog/dash/assistant.png){:.lead data-width="800" data-height="100"}

---

## What Dash Is

Dash is an Express server plus a Vite and vanilla TypeScript front end, built to be left alone on a wall for weeks. Panels rotate every minute: Home with a "Today" strip (weather warnings, holidays, your teams playing today, reminders, bin day, the cheapest electricity hour in Spain, the moon), Agenda from any iCal link, news, markets with sparklines, Spotify with synced lyrics, a kitchen that suggests six recipes a day and walks you through them one step at a time, and live sports boards that take over the screen when one of your teams plays, with a celebration when they score.

![Full-width image](/assets/img/blog/dash/home.png){:.lead data-width="800" data-height="100"}

![Full-width image](/assets/img/blog/dash/cooking.png){:.lead data-width="800" data-height="100"}

Everything on screen also has an HTTP endpoint, so an iOS Shortcut or Home Assistant can add to the shopping list or start a timer. And then there is the voice layer, which is where Gemini comes in.

---

## Why the Live API and Not a Pipeline

The classic way to build a voice assistant is a pipeline: a wake word engine, a speech-to-text service, an LLM call, a text-to-speech service, and a lot of glue to make the whole thing feel responsive. You can build Dash that way. You will spend most of your time on the glue, and it will still feel like a walkie-talkie.

The Gemini Live API collapses that pipeline into one stateful WebSocket. You stream raw microphone audio in, and the model streams spoken audio back, with transcripts of both sides, tool calls in the middle, and Google Search when it needs a current fact. This is what that buys you:

| Concern | Pipeline (STT + LLM + TTS) | Gemini Live API |
|---|---|---|
| Latency | Three sequential network calls per turn | One bidirectional stream, audio starts before the sentence is finished |
| Interruptions | Hand-rolled: detect speech, cancel TTS, re-prompt | Built in: barge-in, `interrupted` event, playback stops |
| Language | Configure STT and TTS per language, detect yourself | Reply in whatever language the user spoke, 70+ languages |
| Transcripts | Two separate services, two formats | `inputTranscription` and `outputTranscription` on the same socket |
| Tools | Parse LLM output, dispatch, re-prompt, re-synthesize | `toolCall` and `toolResponse` messages inside the session |
| Current facts | Your own search integration | `googleSearch` tool with grounding |
| Voice | Pick a TTS vendor and voice | `voiceName` in the session config (Dash ships with `Kore`) |

The trade-off is control: you do not get to inspect the text between STT and TTS, because there is no text in between. For a kitchen assistant that is the right deal.

---

## How "Hey Dash" Works

Here is the whole shape of it. Three parties: the browser running the display, the Dash server on the same machine, and the Gemini Live API.

![Full-width image](/assets/img/blog/dash/architecture.png){:.lead data-width="800" data-height="100"}

The two rules that drive the design:

1. **The API key never leaves the server.** The browser never sees it. For each conversation the server mints a single-use ephemeral token with the entire session setup locked in (model, voice, system instructions, tools), and the browser connects to Gemini with that token.
2. **Audio never touches the server.** The browser talks to Gemini directly over WebSocket: 16 kHz PCM up, 24 kHz PCM down. The server's only job during a conversation is to run the tools Gemini asks for.

Dash is on the kitchen wall, so a third rule follows from the first two: **Gemini is only on the line while you are talking to it.** Waiting for the wake word is free and runs in the browser.

![Full-width image](/assets/img/blog/dash/lifecycle.png){:.lead data-width="800" data-height="100"}

---

## What You Need

- **Node.js 22+** (Dash uses `node --test`, native `fetch`, and the `WebSocket` global)
- A **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey), in a `.env` file next to `config.json`
- A browser with the **Web Speech API** for the wake word (Edge or Chrome; Firefox has no speech recognition, so there you tap the microphone button)
- A tablet or screen in kiosk mode, with microphone access allowed for `http://localhost:3000`

```bash
git clone https://github.com/xavidop/dash && cd dash
npm install
cp config.example.json config.json
echo "GEMINI_API_KEY=your-key" > .env
npm run build && npm start      # http://localhost:3000
```

Then switch on Settings → General → Voice assistant (or set `features.assistant` to `true` in `config.json`). The rest of this article walks through what happens from the moment you say "Dash".

---

## Step 1: Wait for the Wake Word Without Paying for It

A Live session is billed per minute of audio, so you do not want it open all day. Dash uses the browser's own speech recognition to wait for the wake word, and only opens a Gemini session once it hears it. This is the relevant part of `web/src/assistant.ts`:

```ts
function startWake() {
  if (!cfg() || wakeBlocked || phase !== 'off' || wakeOn) return;
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SR) return;
  startMic(); // keeps the pre-roll buffer filling
  rec = new SR() as Recognition;
  rec.lang = getState().config?.locale || defaultLocale();
  rec.continuous = true;
  rec.interimResults = true;
  const re = wakeRegex();
  rec.onresult = (e: any) => {
    for (let i = e.resultIndex; i < e.results.length; i++) {
      // Cooking: short commands ("next", "siguiente paso") act at once, without Gemini.
      if (e.results[i].isFinal && cookingCommand(norm(e.results[i][0].transcript))) return;
      if (re.test(` ${norm(e.results[i][0].transcript)} `)) {
        restartDelay = 300;
        open(true);
        return;
      }
    }
  };
  // ...
}
```

Two details matter here.

**The wake regex is forgiving.** A recognizer set to Spanish or German hears "Dash" as "das", "dach" or "dasch". Exact wake words match anywhere; sound-alikes only count after "hey", "oye", "ok" and friends, because "das" is just a word in German:

```ts
function wakeRegex() {
  const words = (cfg()?.wakeWords || ['dash']).map(norm).map((w) => w.trim()).filter(Boolean);
  const alike = words.flatMap((w) => (w === 'dash' ? ['dasch', 'dach', 'dache', 'dass', 'dahs', ...(getState().config?.language === 'de' ? [] : ['das'])] : []));
  const exact = words.map(esc).join('|');
  const loose = alike.map(esc).join('|');
  return new RegExp(`(?:^|\\s)(?:${exact})(?:\\s|$)${loose ? `|(?:^|\\s)(?:hey|hei|ei|ey|oye|ok|okay|hola|hallo|ehi|eh)\\s+(?:${loose})(?:\\s|$)` : ''}`);
}
```

**The microphone keeps a 2.5-second ring buffer in memory.** People say "Hey Dash, what's the weather?" in one breath. By the time the recognizer fires, the question is already half spoken. An `AudioWorklet` converts the mic to 16-bit PCM at 16 kHz in 100 ms chunks, and the last 25 chunks are kept so the whole sentence reaches Gemini when the session opens:

```ts
const IN_RATE = 16000;
const CHUNK = 1600;         // 100 ms
const PREROLL_CHUNKS = 25;  // 2.5 s of audio before the wake word fired

node.port.onmessage = (e) => {
  ring.push(e.data);
  if (ring.length > PREROLL_CHUNKS) ring.shift();
  onChunk?.(e.data);
};
```

Nothing in that buffer leaves the device before the wake word. What the browser's own speech service hears while waiting is a different matter, and Dash is explicit about it in [docs/voice-assistant.md](https://github.com/xavidop/dash/blob/main/docs/voice-assistant.md): in Edge and Chrome, recognition runs on the browser vendor's online service, not on Gemini, and Dash stores none of it.

Cooking mode adds a shortcut: while a recipe is open, "next", "back", "repeat", "start the timer" and "stop cooking" (in each of the six languages) are matched locally and act instantly, without opening a Gemini session at all.

---

## Step 2: Mint an Ephemeral Token on the Server

This is the part of the Live API that most examples skip, and the one that makes a client-side connection safe. Instead of handing the browser your API key, your backend calls the token endpoint and gets back a short-lived credential that is **locked to a full session setup**. The browser can connect with it, but it cannot change the model, the voice, the instructions or the tools.

`server/services/assistant.js`:

```js
const API = 'https://generativelanguage.googleapis.com/v1beta';
export const LIVE_WS = 'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContentConstrained';

/** Mints a single-use token valid for 30 min (a new session must start within 1 min). */
async session() {
  if (!this.enabled) throw Object.assign(new Error('assistant disabled'), { status: 404 });
  if (Date.now() - this.lastSession < 2000) throw Object.assign(new Error('too many sessions'), { status: 429 });
  this.lastSession = Date.now();
  const iso = (min) => new Date(Date.now() + min * 60e3).toISOString();
  const res = await fetch(`${API}/auth_tokens`, {
    method: 'POST',
    headers: { 'x-goog-api-key': this.key, 'content-type': 'application/json' },
    body: JSON.stringify({ uses: 1, expireTime: iso(30), newSessionExpireTime: iso(1), bidiGenerateContentSetup: this.setup() }),
    signal: AbortSignal.timeout(10000),
  });
  const d = await res.json().catch(() => ({}));
  if (!res.ok || !d.name) throw Object.assign(new Error(d.error?.message || `token request failed (HTTP ${res.status})`), { status: 502 });
  return { url: `${LIVE_WS}?access_token=${encodeURIComponent(d.name)}`, idleSeconds: this.config.assistant.idleSeconds };
}
```

The fields, one by one:

- `uses: 1`: the token starts exactly one session.
- `expireTime`: how long messages can flow over a connection opened with it (30 minutes here; the API's default is also 30).
- `newSessionExpireTime`: how long you have to open that session (1 minute; again the default). The browser requests a token and connects immediately, so a minute is plenty.
- `bidiGenerateContentSetup`: the whole `setup` message the client would normally send on the WebSocket, baked into the token. In the SDKs this is called `liveConnectConstraints`; on the REST endpoint it is `bidiGenerateContentSetup`.

The response is tiny, and it is all the browser ever gets from the server:

```json
{
  "name": "auth_tokens/<redacted>"
}
```

Two things follow from this. First, the browser connects to the **constrained** WebSocket endpoint, `BidiGenerateContentConstrained`, with the token as `access_token`. That endpoint ignores any setup the client sends, so the browser cannot repurpose the token for something else. Second, the token endpoint is the only place that sees the API key, and Dash puts a guard in front of it: only the display itself (requests from `localhost`) may ask for a token unless `assistant.allowRemote` is set, so other devices on your Wi-Fi cannot spend your quota.

The setup locked into the token is where the assistant gets its personality:

```js
setup() {
  const a = this.config.assistant;
  return {
    model: `models/${a.model}`,                                  // gemini-3.8-live
    generationConfig: {
      responseModalities: ['AUDIO'],
      speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: a.voice } } },   // Kore
    },
    systemInstruction: { parts: [{ text: [ /* persona, rules, and this.context() */ ].join('\n') }] },
    tools: this.spotify?.enabled && this.spotify.connected
      ? [TOOLS[0], { functionDeclarations: [...TOOLS[1].functionDeclarations, ...SPOTIFY_TOOLS] }]
      : TOOLS,
    inputAudioTranscription: {},
    outputAudioTranscription: {},
  };
}
```

`responseModalities: ['AUDIO']` is the only modality Gemini 3.8 Live speaks on this path; the two empty transcription objects ask for text transcripts of both sides, which is what the on-screen chat is built from. Note how the Spotify tools are only declared when Spotify is actually connected: fewer tools means fewer wrong tool picks.

---

## Step 3: Open the WebSocket and Stream Audio

Back in the browser, the session is one `WebSocket` and a handful of message types. This is the core of `open()` in `web/src/assistant.ts`:

```ts
const res = await fetch('/api/assistant/session', { method: 'POST' });
const d = await res.json();
ws = new WebSocket(d.url);

ws.onopen = () => ws?.send(JSON.stringify({ setup: {} }));
```

The `setup` message is empty on purpose: everything is already in the token. Gemini answers with `setupComplete`, and from then on the browser pushes audio:

```ts
const sendAudio = (pcm: ArrayBuffer) =>
  ws?.readyState === WebSocket.OPEN &&
  ws.send(JSON.stringify({ realtimeInput: { audio: { data: b64(pcm), mimeType: `audio/pcm;rate=${IN_RATE}` } } }));

if (m.setupComplete) {
  setPhase('listening');
  if (prompt) ws?.send(JSON.stringify({ realtimeInput: { text: prompt } }));   // "[briefing]"
  for (const c of pending) sendAudio(c);          // the 2.5 s pre-roll
  onChunk = (pcm) => { if (!isSpeaking()) sendAudio(pcm); };
  maxTimer = window.setTimeout(close, MAX_SESSION_MS);
  armIdle();
  return;
}
```

Three things worth noticing:

- **The pre-roll goes first.** Those 25 buffered chunks are flushed before live audio starts, so the question you began before the wake word fired arrives intact.
- **A text prompt can open the conversation.** The scheduled morning briefing sends `[briefing]` as `realtimeInput.text`, and the system instruction tells the model what a briefing is. Same session, same voice, no audio needed to start it.
- **Half-duplex.** `onChunk` drops microphone audio while Dash is speaking. A wall tablet plays through speakers, and without reliable echo cancellation the model would hear itself. You can still interrupt: tap the card and playback stops.

The server's side of the conversation is a few message shapes, all handled in one `onmessage`:

```ts
if (m.toolCall) return runTools(m.toolCall.functionCalls || []);
if (m.goAway) return close();
const sc = m.serverContent;
if (!sc) return;
if (sc.inputTranscription?.text) say('user', sc.inputTranscription.text);   // what you said
for (const p of sc.modelTurn?.parts || []) {
  if (p.inlineData?.data) play(p.inlineData.data);                           // 24 kHz PCM, base64
}
if (sc.outputTranscription?.text) say('dash', sc.outputTranscription.text);  // what Dash said
if (sc.interrupted) stopPlayback();
if (sc.turnComplete) { /* arm the idle timer, or close if the model said goodbye */ }
```

| Message | Meaning |
|---|---|
| `setupComplete` | Session is ready; start sending `realtimeInput` |
| `serverContent.inputTranscription` | Streaming transcript of the user's speech |
| `serverContent.modelTurn.parts[].inlineData` | Chunks of 16-bit PCM audio at 24 kHz, base64 |
| `serverContent.outputTranscription` | Streaming transcript of what the model is saying |
| `serverContent.interrupted` | The user barged in; stop playing what you have queued |
| `serverContent.turnComplete` | The model finished its turn |
| `toolCall.functionCalls[]` | The model wants you to run functions and reply with `toolResponse` |
| `goAway` | The server is about to close the connection |

Playback is plain Web Audio: decode the base64 into `Int16`, scale to floats, schedule each buffer right after the previous one on a 24 kHz `AudioContext`. The `playHead` bookkeeping is what lets Dash know how long it will still be speaking, which drives both the half-duplex gate and the idle timer.

```ts
function play(b64: string) {
  outCtx ??= new AudioContext({ sampleRate: OUT_RATE });
  const bin = atob(b64);
  const pcm = new Int16Array(bin.length / 2);
  for (let i = 0; i < pcm.length; i++) pcm[i] = (bin.charCodeAt(i * 2) | (bin.charCodeAt(i * 2 + 1) << 8)) << 16 >> 16;
  const buf = outCtx.createBuffer(1, pcm.length, OUT_RATE);
  const ch = buf.getChannelData(0);
  for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 0x8000;
  const src = outCtx.createBufferSource();
  src.buffer = buf;
  src.connect(outCtx.destination);
  playHead = Math.max(playHead, outCtx.currentTime + 0.05);
  src.start(playHead);
  playHead += buf.duration;
  speakingUntil = Date.now() + (playHead - outCtx.currentTime) * 1000;
}
```

---

## Step 4: Let Gemini Act Through Tools

A voice assistant that can only talk is a radio. The useful part is that Gemini can change what is on the screen. Dash declares its tools once, in the setup locked into the token, and runs them on the server.

![Full-width image](/assets/img/blog/dash/tools.png){:.lead data-width="800" data-height="100"}

The declarations are plain function schemas, plus Google Search as a built-in tool:

```js
const S = (description) => ({ type: 'STRING', description });

export const TOOLS = [
  { googleSearch: {} },
  {
    functionDeclarations: [
      {
        name: 'add_to_shopping_list',
        description: 'Add one or more items to the household shopping list shown on the display.',
        parameters: { type: 'OBJECT', properties: { items: { type: 'ARRAY', items: S('One item, short, e.g. "milk" or "2 kg of oranges"') } }, required: ['items'] },
      },
      {
        name: 'start_timer',
        description: 'Start a kitchen timer on the display: for a duration ("10 minutes") or until a clock time ("at 18:30", an alarm). Up to 6 at once.',
        parameters: {
          type: 'OBJECT',
          properties: {
            minutes: { type: 'NUMBER', description: 'Duration in minutes (may be fractional). Omit when `at` is given.' },
            at: S('Local clock time "HH:MM" to ring at (today, or tomorrow if already past). Omit when `minutes` is given.'),
            label: S('Optional label, e.g. "pasta"'),
          },
        },
      },
      {
        name: 'remember',
        description: 'Save a fact the household wants Dash to remember (people, phone numbers, codes, preferences, where things are). Store it as one self-contained sentence.',
        parameters: { type: 'OBJECT', properties: { fact: S('E.g. "The plumber is Juan, phone 600 123 456"') }, required: ['fact'] },
      },
      {
        name: 'start_recipe',
        description: 'Open cooking mode on the display with a recipe: big step-by-step instructions the user follows while cooking. ... Every step that takes time must say how long in minutes, with a number ("cook the spaghetti for 9 minutes"): the display turns those into one-tap timers. Never write "until al dente" without a time.',
        parameters: {
          type: 'OBJECT',
          properties: {
            title: S('Dish name'),
            servings: S('E.g. "4 servings"'),
            ingredients: { type: 'ARRAY', items: S('One ingredient with quantity') },
            steps: { type: 'ARRAY', items: S('One short step, with its time in minutes when it takes time') },
          },
          required: ['title', 'ingredients', 'steps'],
        },
      },
      { name: 'end_conversation', description: 'Close the assistant when the user is done (e.g. "thanks", "that is all"). Say a short goodbye first.' },
      // ... remove_from_shopping_list, get_shopping_list, add_note, list_timers, add_time_to_timer,
      //     cancel_timer, forget, open_saved_recipe, recipe_step, start_step_timer, stop_cooking
    ],
  },
];
```

The full list is eighteen functions, plus three Spotify ones when it is connected. The `start_recipe` description is my favourite: it is a prompt disguised as a schema. Telling the model that every timed step needs a number of minutes is what makes the "Timer 8 min" button in cooking mode appear by itself.

When the model decides to act, the browser receives `toolCall`, forwards each call to the server, and sends the results back as `toolResponse`:

```ts
async function runTools(calls: { id: string; name: string; args?: Record<string, unknown> }[]) {
  setPhase('thinking');
  const functionResponses = [];
  for (const c of calls) {
    let response: unknown;
    try {
      response = await (await fetch('/api/assistant/tool', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: c.name, args: c.args || {} }),
      })).json();
    } catch {
      response = { error: 'tool failed' };
    }
    if (c.name === 'end_conversation') ending = true;
    const done = actionText(c.name, c.args || {}, response as Record<string, unknown>);
    if (done) log.push({ role: 'action', text: done });   // the green receipt on screen
    functionResponses.push({ id: c.id, name: c.name, response });
  }
  ws?.send(JSON.stringify({ toolResponse: { functionResponses } }));
}
```

On the server, `tool()` is a switch over the names, working against the local JSON database and the timers service. The responses are deliberately rich: `add_to_shopping_list` returns both what was added and the full list afterwards, so the model can say "milk is already on it" instead of pretending it added a duplicate:

```js
case 'add_to_shopping_list': {
  const added = this.db.addShopping(args.items);
  this.onChange('shopping');
  return { added: added.map((x) => x.text), list: this.db.shopping().filter((x) => !x.done).map((x) => x.text) };
}
case 'start_timer': {
  let seconds = Math.round(Number(args.minutes) * 60);
  const at = String(args.at || '').match(/^(\d{1,2}):(\d{2})$/);
  if (at) {
    const today = new Date().toLocaleDateString('en-CA', { timeZone: this.config.timezone });
    let when = localToEpoch(`${today}T${at[1].padStart(2, '0')}:${at[2]}`, this.config.timezone);
    if (when != null && when <= Date.now()) when += 864e5;
    seconds = when == null ? NaN : Math.ceil((when - Date.now()) / 1000); // ring on the minute, never early
  }
  if (!(seconds >= 5 && seconds <= 24 * 3600)) return { error: 'give minutes (up to 1440) or a clock time "HH:MM"' };
  const tm = this.timers.add(seconds, String(args.label || '').slice(0, 40));
  return { started: true, minutes: Math.round(seconds / 6) / 10, endsAt: tm.endsAt, label: tm.label || null };
}
```

Errors go back to the model as data, not as exceptions. "Which timer? say its label" is a tool response, and the model turns it into a question.

One Gemini 3.8 Live detail you should know: **function calls are asynchronous by default** (`NON_BLOCKING`). The model can keep talking while a tool runs, and schedule the result for when it is idle or interrupt itself with it. For Dash's tools, which take milliseconds, the difference is invisible; for a slow tool you would set `BLOCKING` on the declaration.

---

## Step 5: Give Gemini the Household Context

The system instruction is rebuilt for every session, and the second half of it is a snapshot of what Dash already knows. That is why "when do Arsenal play next?" is answered from the display's own data instead of a web search, and why "add it to the list" works when there is only one list.

```js
/** What Dash knows right now, so "when do Valencia play?" doesn't need a web search. */
context() {
  const tz = this.config.timezone;
  const lines = [`Now: ${now.toLocaleString('en-GB', { timeZone: tz, dateStyle: 'full', timeStyle: 'short' })} (${tz}).`];
  const w = this.store.get('weather')?.data;
  if (w) lines.push(`Weather now: ${w.current.temp}°C, ${w.current.desc}; today ${w.today.min}–${w.today.max}°C, rain chance ${w.today.precip}%.`);
  for (const c of teams.slice(0, 10)) { /* last result and next game per followed team */ }
  if (events.length) lines.push(`Calendar: ${events.map((e) => `${e.title || 'event'} (${e.allDay ? e.start : fmt(e.start)})`).join('; ')}.`);
  if (alerts.length) lines.push(`Weather warnings: ...`);
  if (hol?.today) lines.push(`Today is a public holiday: ${hol.today.name}.`);
  if (reminders.length) lines.push(`Reminders today: ...`);
  if (bins.length) lines.push(`Bins: ${bins.join('; ')}.`);
  if (news.length) lines.push(`Top headlines: ${news.map((n) => n.title).join(' | ')}.`);
  const cook = this.cooking?.current();
  if (cook) {
    lines.push(`COOKING MODE is open: "${cook.title}" (${cook.servings || 'servings not given'}), on step ${cook.step + 1} of ${cook.steps.length}: "${cook.steps[cook.step].text}".`);
    lines.push(`Ingredients: ${cook.ingredients.join('; ')}.`);
  }
  if (music?.item) lines.push(`Spotify: ${music.playing ? 'playing' : 'paused'} "${music.item.name}" by ${music.item.by}...`);
  const memories = this.db.memories();
  if (memories.length) lines.push(`Things the household asked you to remember:\n${memories.map((m) => `- ${m.text}`).join('\n')}`);
  lines.push(shopping.length ? `Shopping list: ${shopping.map((x) => x.text).join(', ')}.` : 'The shopping list is empty.');
  if (timers.length) lines.push(`Running timers: ...`);
  return lines.join('\n');
}
```

The memories deserve a word. "Remember that the plumber is Juan, 600 123 456" calls the `remember` tool, which stores one sentence locally. Every later session gets those sentences in the context, and the instruction tells the model to quote numbers and codes exactly. They live in Dash's own `data/db.json`, and Settings lists them so you can delete any. It is a simple mechanism, and it is enough: a kitchen does not need a vector database.

The persona rules are short and shaped by the fact that the output is spoken: no lists, no markdown, no URLs, one or two sentences, answer first and then maybe a follow-up, never claim a tool ran without calling it, and reply in the language the user is speaking.

---

## Step 6: End the Conversation on Purpose

A per-minute API needs a clear end. Dash closes a session in four ways:

- **Silence.** After the model finishes a turn, an idle timer waits for Dash to finish speaking plus `idleSeconds` (8 by default). If nothing was heard since, the session closes.
- **"Thanks."** The `end_conversation` tool exists so the model can hang up gracefully: say goodbye, call the tool, and the browser closes once the goodbye has played.
- **Five minutes.** A hard cap, `MAX_SESSION_MS`, so a kitchen full of chatter cannot keep the meter running.
- **`goAway`.** When Gemini announces it is about to drop the connection, Dash closes cleanly instead of waiting for the error.

```ts
function armIdle() {
  clearTimeout(idleTimer);
  // Wait for Dash to finish talking, then give the user a few seconds to follow up.
  const wait = Math.max(0, speakingUntil - Date.now()) + (cfg()?.idleSeconds ?? 8) * 1000;
  idleTimer = window.setTimeout(() => (ending || !heardSinceTurn ? close() : armIdle()), wait);
}
```

Closing plays a short down-chime (two oscillators, no audio file), stops playback, restarts the wake-word recognizer a second and a half later, and tells the server to restore the Spotify volume. While the assistant is open, Dash lowers the music ("ducking") so the model does not have to shout over it.

---

## What Gemini 3.8 Live Changes

Dash ships pinned to `gemini-3.8-live`, the stable Live model Google updated in September 2026. If you are coming from `gemini-3.1-flash-live-preview`, these are the differences that affect a voice assistant:

| | Gemini 3.8 Live |
|---|---|
| Inputs / outputs | Text, image, audio, video in; text and audio out |
| Context | 131,072 input tokens, 65,536 output tokens |
| Function calling | Supported, **asynchronous by default** (`NON_BLOCKING`); `BLOCKING`, `SILENT`, `WHEN_IDLE`, `INTERRUPTED` scheduling available |
| Google Search grounding | Supported, 5,000 free requests a month shared across Gemini 3+ models |
| Thinking | Interleaved reasoning built in; `thinking_level` is **not** a setup option any more |
| Proactive audio | Always on (the model decides when a sound is addressed to it); setting it to `false` is an error |
| Affective dialog | Removed from the API |
| Transcription | Input and output transcription, opt in per session |
| Variant | `gemini-3.8-live-extended-thinking` for multi-step reasoning alongside speech |

Two of those matter for Dash's design. Proactive audio being always on is why the pre-roll buffer and the half-duplex gate are enough: the model is already good at ignoring background noise and its own echo. And asynchronous function calling is why the "thinking" phase on screen is so short: the model does not stall while a tool runs.

---

## What It Costs and Where Your Audio Goes

Gemini is on the line only during a conversation, and this is what each state costs:

| State | What runs | Gemini cost |
|---|---|---|
| Waiting for "Dash" | The browser's speech recognition | none |
| Talking | A live Gemini session | per minute |
| Closed | After 8 s of silence, on "thanks" or ✕, or after 5 minutes at most | none |

On the paid tier, `gemini-3.8-live` audio is priced at $0.005 per minute in and $0.018 per minute out, with the first 5,000 Google searches a month included. A typical question is a few seconds each way, around half a cent. Twenty questions a day comes to roughly $3 a month. The free tier costs nothing, with rate limits, and Google may use free-tier data to improve its products, which is the main reason to pay.

On privacy, the three facts you need are the three design rules from the architecture section: the key stays on the server, audio goes from the browser straight to Gemini only during a session, and the wake word runs on the browser's speech service. Memories are stored locally and sent to Gemini as context in each conversation, so do not store anything you would not say to it.

---

## Gemini Beyond the Voice: Recipes and Translation

The Live API is the headline, but Dash uses plain `generateContent` on `gemini-3.8-flash` in two quieter places, both in the kitchen.

![Full-width image](/assets/img/blog/dash/recipes.png){:.lead data-width="800" data-height="100"}

**Any recipe link, turned into steps.** Most recipe sites embed a schema.org `Recipe` card, and that is what Dash parses first. For pages without one, Gemini reads the page text and returns the same shape, with structured output enforced by a response schema:

```js
async function recipeWithGemini(text, url, { key, model, language }) {
  const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
    method: 'POST',
    headers: { 'x-goog-api-key': key, 'content-type': 'application/json' },
    signal: AbortSignal.timeout(40000),
    body: JSON.stringify({
      contents: [{ parts: [{ text: `Extract the recipe from this web page. Keep the original language (${language} if unclear). Steps are short and in order. If there is no recipe, return an empty title.\n\nURL: ${url}\n\n${text.slice(0, 30000)}` }] }],
      generationConfig: {
        responseMimeType: 'application/json',
        responseSchema: {
          type: 'OBJECT',
          properties: {
            title: { type: 'STRING' },
            servings: { type: 'STRING' },
            ingredients: { type: 'ARRAY', items: { type: 'STRING' } },
            steps: { type: 'ARRAY', items: { type: 'STRING' } },
          },
          required: ['title', 'ingredients', 'steps'],
        },
      },
    }),
  });
  const d = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(d.error?.message || `Gemini HTTP ${res.status}`);
  return normalizeRecipe(JSON.parse(d.candidates?.[0]?.content?.parts?.[0]?.text || '{}'), url);
}
```

**"What to cook" in your language.** The daily ideas come from TheMealDB, which is English only. With a key set and the display in another language, titles and full recipes are translated in one structured call, with the same `responseSchema` trick.

No SDK in either case. Dash's whole Gemini integration is `fetch` against the REST API and one `WebSocket`, which is a good reminder of how small the surface actually is.

---

## Turning It On

The assistant is a few lines of configuration on top of a running Dash:

```json
"features": { "assistant": true },
"assistant": {
  "model": "gemini-3.8-live",
  "voice": "Kore",
  "wakeWords": ["dash"],
  "idleSeconds": 8,
  "allowRemote": false
},
"briefing": { "time": "07:30", "weekdays": [1, 2, 3, 4, 5] }
```

Any Gemini prebuilt voice works in `voice` (`Kore`, `Puck`, `Charon`, and the rest). `wakeWords` can be anything the browser's recognizer can hear reliably. `briefing.time` opens a session by itself at that time and asks for the morning summary: weather, calendar, your teams, bins, one headline. On a Windows kiosk, `windows/edge-kiosk-policy.reg` allows the microphone for `http://localhost:3000` without a prompt.

Then say "Dash", or "Hey Dash, what's the weather?" in one breath, or tap the microphone button at the bottom left. A blue dot on that button means the wake word is listening.

![Full-width image](/assets/img/blog/dash/shopping.png){:.lead data-width="800" data-height="100"}

---

## Conclusion

The Gemini Live API turns a voice assistant from a systems-integration project into an application project. The protocol is small: one token request on your server, one WebSocket in the client, PCM in, PCM out, and `toolCall` and `toolResponse` for everything that changes the world. Gemini 3.8 Live adds the pieces that used to be the hard part, interruptions, language detection, asynchronous tools and search grounding, and leaves you with the decisions that are actually yours: when to open a session, what the model is allowed to do, and what it knows about your house.

Dash makes those decisions one way: free wake word in the browser, ephemeral tokens with the setup locked in, tools on the server, memories on disk, and a session that ends when you say thanks. The code is at [github.com/xavidop/dash](https://github.com/xavidop/dash). Put it on a tablet, add your teams, and talk to your kitchen.

---

## Further reading

- [Dash on GitHub](https://github.com/xavidop/dash), and the [voice assistant doc](https://github.com/xavidop/dash/blob/main/docs/voice-assistant.md) with everything it can do
- [Gemini Live API overview](https://ai.google.dev/gemini-api/docs/live)
- [Ephemeral tokens for the Live API](https://ai.google.dev/gemini-api/docs/ephemeral-tokens)
- [Gemini 3.8 Live model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-live), including the migration notes from the 3.1 preview
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Dash architecture](https://github.com/xavidop/dash/blob/main/docs/architecture.md) and [HTTP API](https://github.com/xavidop/dash/blob/main/docs/api.md)

---

*Last updated: October 2026. Model versions referenced: gemini-3.8-live for the assistant, gemini-3.8-flash for recipes. Dash at commit `60e909f`.*
