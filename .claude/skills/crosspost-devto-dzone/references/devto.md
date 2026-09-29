# dev.to: validate, draft, publish, verify

All snippets run through `browser_run_code_unsafe` with the code pasted **inline** (not via its `filename`
parameter). Replace `<REPO>` with the absolute repo path. Each snippet serves the build output to the page with
`page.route('https://dev.to/__xp/**')`, so the page can `fetch('/__xp/<name>.json')` and `fetch('/__xp/manifest.json')`.

Everything goes through the logged-in web session: `POST /articles` (create), `PUT /articles/:id` (update),
`POST /articles/preview` (render only, no side effects), with the CSRF token from `meta[name="csrf-token"]`. No
API key is needed. The article body is the markdown with a front matter block, which is how Forem reads title,
tags, canonical, cover and series.

## Contents
1. Session + existing-article check
2. Preview validation (no side effects)
3. First article as a draft
4. Publish everything
5. Verify
6. Troubleshooting

## 1. Session + existing-article check

`/api/articles/me/all` includes drafts, which the public API and `crosspost.py status` cannot see.

```js
async (page) => {
  const DATA = '<REPO>/.playwright-mcp/crosspost/';
  await page.goto('https://dev.to/dashboard');
  await page.route('https://dev.to/__xp/**', r => r.fulfill({ path: DATA + r.request().url().split('/__xp/')[1] }));
  const res = await page.evaluate(async () => {
    const user = document.body.dataset.user ? JSON.parse(document.body.dataset.user).username : null;
    if (!user) return { loggedIn: false };
    const man = await (await fetch('/__xp/manifest.json')).json();
    let mine = [], pg = 1;
    while (true) { const b = await (await fetch('/api/articles/me/all?per_page=100&page=' + pg, { credentials: 'include' })).json(); mine = mine.concat(b); if (b.length < 100) break; pg++; }
    const norm = s => (s || '').replace(/\/$/, '');
    return { loggedIn: true, user, total: mine.length, posts: man.posts.map(p => { const a = mine.find(x => norm(x.canonical_url) === norm(p.canonical) || x.title === p.title); return p.name + ' -> ' + (a ? (a.published ? 'PUBLISHED ' : 'DRAFT ') + a.id + ' ' + a.url : 'new'); }) };
  });
  await page.unroute('https://dev.to/__xp/**');
  return JSON.stringify(res, null, 1);
}
```

If `loggedIn` is false, ask the user to log in to dev.to in the Playwright browser window and wait.

## 2. Preview validation (no side effects)

Renders every post with dev.to's own pipeline and compares each rendered `<pre>` with the source code block.
Expected, harmless differences: dev.to expands tabs (the check normalizes tabs to 4 spaces, so tab-aligned
`go test` output can still show a whitespace-only diff), and a fence indented inside a list item keeps its
indentation. Anything else, or `liquidErr=true`, needs fixing before publishing.

```js
async (page) => {
  const DATA = '<REPO>/.playwright-mcp/crosspost/';
  await page.goto('https://dev.to/new');
  await page.route('https://dev.to/__xp/**', r => r.fulfill({ path: DATA + r.request().url().split('/__xp/')[1] }));
  const out = await page.evaluate(async () => {
    const man = await (await fetch('/__xp/manifest.json')).json();
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
    const lines = [];
    for (const m of man.posts) {
      const p = await (await fetch('/__xp/' + m.name + '.json')).json();
      const r = await fetch('/articles/preview', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf, 'Accept': 'application/json' }, body: JSON.stringify({ article_body: p.devto_md }) });
      const j = await r.json().catch(() => ({}));
      const d = document.createElement('div'); d.innerHTML = j.processed_html || '';
      const norm = s => s.replace(/\t/g, '    ').split('\n').map(l => l.replace(/\s+$/, '')).join('\n').replace(/^\n+|\n+$/g, '');
      const src = [...p.devto_md.matchAll(/^([ \t]*)(`{3}|~{3})(\S*)\n([\s\S]*?)\n\1\2[ \t]*$/gm)].map(x => norm(x[4].split('\n').map(l => l.startsWith(x[1]) ? l.slice(x[1].length) : l).join('\n')));
      const pres = [...d.querySelectorAll('pre')].map(e => norm(e.textContent));
      const bad = [];
      src.forEach((s, i) => { if (pres[i] !== s) { const a = s.split('\n'), b = (pres[i] || '').split('\n'); let k = 0; while (k < a.length && a[k] === b[k]) k++; bad.push('blk' + i + ' line ' + k + ': ' + JSON.stringify(a[k]) + ' vs ' + JSON.stringify(b[k])); } });
      const noCode = p.devto_md.replace(/^([ \t]*)(`{3}|~{3})[\s\S]*?\n\1\2[ \t]*$/gm, '');
      const tables = (noCode.match(/^\|[\s:|-]+\|\s*$/gm) || []).length;
      lines.push(m.name + ' status=' + r.status + ' pre=' + pres.length + '/' + src.length + ' tables=' + d.querySelectorAll('table').length + '/' + tables + ' liquidErr=' + /Liquid (syntax )?error/i.test(d.textContent) + (bad.length ? '\n   ' + bad.slice(0, 3).join('\n   ') : ''));
    }
    return lines.join('\n');
  });
  await page.unroute('https://dev.to/__xp/**');
  return out;
}
```

If one post fails as a whole, bisect it: split `devto_md` on `\n(?=#{2,3} )`, preview each section, and find the
first failing one. That is how the ``` inside a Go string literal was found.

## 3. First article as a draft

Create the first post unpublished, then check the stored fields and look at the preview page (screenshot)
before publishing anything. `published: false` in the front matter keeps it private.

```js
async (page) => {
  const DATA = '<REPO>/.playwright-mcp/crosspost/';
  await page.goto('https://dev.to/dashboard');
  await page.route('https://dev.to/__xp/**', r => r.fulfill({ path: DATA + r.request().url().split('/__xp/')[1] }));
  const res = await page.evaluate(async () => {
    const man = await (await fetch('/__xp/manifest.json')).json();
    const p = await (await fetch('/__xp/' + man.posts[0].name + '.json')).json();
    const q = s => '"' + s.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
    const fm = ['---', 'title: ' + q(p.title), 'published: false', 'description: ' + q(p.short_description), 'tags: ' + p.tags.join(', '), 'canonical_url: ' + p.canonical, 'cover_image: ' + p.cover_url, p.series ? 'series: ' + p.series : null, '---', '', ''].filter(l => l !== null).join('\n');
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
    const r = await fetch('/articles', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf, 'Accept': 'application/json' }, body: JSON.stringify({ article: { body_markdown: fm + p.devto_md } }) });
    const created = await r.json().catch(() => ({}));
    const all = await (await fetch('/api/articles/me/unpublished?per_page=100', { credentials: 'include' })).json();
    const a = all.find(x => x.id === created.id) || {};
    return { status: r.status, id: created.id, preview: created.current_state_path, title: a.title, description: a.description, tags: a.tag_list, canonical: a.canonical_url, cover: !!a.cover_image };
  });
  await page.unroute('https://dev.to/__xp/**');
  return JSON.stringify(res, null, 1);
}
```

Then `page.goto('https://dev.to' + preview)` and take a screenshot to eyeball the cover and first screen. Keep the
returned `id`: step 4 publishes that draft instead of creating a duplicate.

## 4. Publish everything

Publishes in manifest order (oldest first, so the newest ends up on top and series read in order). It is
idempotent: an article already published with the same canonical URL is skipped, and an existing draft is
updated in place. Requests are spaced 6 s apart; a 429 waits 35 s and retries.

```js
async (page) => {
  const DATA = '<REPO>/.playwright-mcp/crosspost/';
  await page.goto('https://dev.to/dashboard');
  await page.route('https://dev.to/__xp/**', r => r.fulfill({ path: DATA + r.request().url().split('/__xp/')[1] }));
  const man = await page.evaluate(async () => (await fetch('/__xp/manifest.json')).json());
  const out = [];
  for (const m of man.posts) {
    let res, attempt = 0;
    do {
      res = await page.evaluate(async (name) => {
        const p = await (await fetch('/__xp/' + name + '.json')).json();
        let mine = [], pg = 1;
        while (true) { const b = await (await fetch('/api/articles/me/all?per_page=100&page=' + pg, { credentials: 'include' })).json(); mine = mine.concat(b); if (b.length < 100) break; pg++; }
        const norm = s => (s || '').replace(/\/$/, '');
        const existing = mine.find(x => norm(x.canonical_url) === norm(p.canonical));
        if (existing && existing.published) return { status: 'skip', body: 'already published ' + existing.url };
        const q = s => '"' + s.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
        const fm = ['---', 'title: ' + q(p.title), 'published: true', 'description: ' + q(p.short_description), 'tags: ' + p.tags.join(', '), 'canonical_url: ' + p.canonical, 'cover_image: ' + p.cover_url, p.series ? 'series: ' + p.series : null, '---', '', ''].filter(l => l !== null).join('\n');
        const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
        const r = await fetch(existing ? '/articles/' + existing.id : '/articles', { method: existing ? 'PUT' : 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf, 'Accept': 'application/json' }, body: JSON.stringify({ article: { body_markdown: fm + p.devto_md } }) });
        return { status: r.status, body: (await r.text()).slice(0, 250) };
      }, m.name);
      if (res.status === 429) await page.waitForTimeout(35000);
    } while (res.status === 429 && ++attempt < 3);
    out.push(m.name + ' -> ' + res.status + ' ' + res.body);
    if (res.status !== 'skip' && res.status >= 300) break;
    if (res.status !== 'skip') await page.waitForTimeout(6000);
  }
  await page.unroute('https://dev.to/__xp/**');
  return out.join('\n');
}
```

## 5. Verify

Use the logged-in endpoint; the public `/api/articles?username=...` can serve an hour-old cached list.

```js
async (page) => {
  const DATA = '<REPO>/.playwright-mcp/crosspost/';
  await page.goto('https://dev.to/dashboard');
  await page.route('https://dev.to/__xp/**', r => r.fulfill({ path: DATA + r.request().url().split('/__xp/')[1] }));
  const res = await page.evaluate(async () => {
    const man = await (await fetch('/__xp/manifest.json')).json();
    let mine = [], pg = 1;
    while (true) { const b = await (await fetch('/api/articles/me/all?per_page=100&page=' + pg, { credentials: 'include' })).json(); mine = mine.concat(b); if (b.length < 100) break; pg++; }
    const norm = s => (s || '').replace(/\/$/, '');
    return man.posts.map(p => { const a = mine.filter(x => norm(x.canonical_url) === norm(p.canonical)); return (a.length === 1 && a[0].published ? 'OK  ' : 'CHECK ') + p.name + ' copies=' + a.length + (a[0] ? ' ' + a[0].url + ' tags=' + a[0].tag_list + ' cover=' + !!a[0].cover_image : ''); }).join('\n');
  });
  await page.unroute('https://dev.to/__xp/**');
  return res;
}
```

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Preview body is `Liquid syntax error: Unknown tag 'endraw'` | A code block contains ``` (e.g. `"```json"` in Go); dev.to pairs backticks before escaping Liquid | `crosspost.py build` re-fences those blocks with `~~~`; if it still happens, bisect by section (step 2) |
| `{{ }}` or `{% %}` vanish in the rendered code | Liquid inside code that dev.to did not escape | dev.to auto-escapes fenced and inline code; if a case slips through, wrap the fenced block in `{% raw %}` ... `{% endraw %}` outside the fence |
| Public API misses articles you just published | dev.to edge-caches each list URL (keyed on `per_page`, not on extra params) for up to an hour | Use `/api/articles/me/all` in the browser; `crosspost.py status` varies `per_page` per run to dodge the cache |
| 429 on create | dev.to rate limit | Wait 35 s and retry (the publish snippet does this) |
| Series box missing on the first article | A series only shows once it has 2+ articles | Expected |
