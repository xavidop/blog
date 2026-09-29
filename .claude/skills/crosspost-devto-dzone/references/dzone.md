# DZone: check, submit to moderation, verify

DZone has no public API and sits behind Cloudflare, so everything runs in the logged-in Playwright browser. Paste
the snippets **inline** into `browser_run_code_unsafe` and replace `<REPO>` with the absolute repo path. Build
output is served to the page through `page.route('https://dzone.com/__xp/**')`.

Account: user id `4278252` (profile `/authors/xavidop`). The contributor search returns two "Xavier Portilla Edo"
accounts; the right one is the **Voiceflow / CORE** one (the other is an old IVIRMA profile).

A regular author cannot publish on DZone. "Submit to Moderation" is the final step; DZone editors review and
publish, sometimes with a new title or permalink (e.g. "Stop Using Python for Your GenAI Apps" went live as "Why You
Should Use Go and Genkit for Your GenAI Apps").

## Contents
1. What the editor needs (form model)
2. Status: already on DZone?
3. Submit a batch
4. Verify
5. Troubleshooting

## 1. What the editor needs

The editor at `/content/article/post.html` is AngularJS + Froala. Scope of `[ng-model="article.title"]` holds
`article` and helpers. Fields and how each one is set:

| Field | How | Rule |
|---|---|---|
| Title | `page.fill('textarea[name=title]')` | Strip the blog's ` (English)` suffix (build does) |
| TL;DR | `page.fill('textarea[name=subtitle]')` | **120-175 chars**, else "TL;DR is too short/long" |
| Body | `FroalaEditor.INSTANCES[0].html.set(html)` + `events.trigger('contentChanged')` | Code blocks must be DZone's `codeMirror-wrapper` markup (build emits it) |
| Type | click `Not set`, then link `Tutorial` / `Analysis` | Comparisons are Analysis |
| Meta description | `page.fill('#meta-description-textarea')` | up to 255 chars; reuse the short description |
| Contributors | search box `.select-users`, type `Xavier Portilla`, pick the row containing `Voiceflow` | Without an `author` entry the save fails: "Please add an author in the contributors field" |
| Featured image | `angular.element(input[ng-file-change]).scope().upload([File])` | JPEG under ~350 KB (build makes it); larger PNGs return HTTP 500 |
| Original Source | `page.fill('[ng-model="article.originalSource"]')` | The xavidop.me canonical URL |

"Save draft" creates `/content/<id>/edit.html`. On that page the Save split button's caret opens a menu whose
item `li.dropdown-actions` "Submit to Moderation" (`s.save(true, false, false, true)`) submits it. After that,
`article.state === 'moderation'` and the sidebar shows "Status: In Moderation".

## 2. Status: already on DZone?

Lists drafts / in-moderation items (from the drafts page's Alpine state) and checks the canonical URL of the most
recent published articles on the profile (editors retitle, so titles alone are not reliable).

```js
async (page) => {
  const DATA = '<REPO>/.playwright-mcp/crosspost/';
  await page.goto('https://dzone.com/users/4278252/drafts.html');
  await page.waitForTimeout(2500);
  await page.route('https://dzone.com/__xp/**', r => r.fulfill({ path: DATA + r.request().url().split('/__xp/')[1] }));
  const pending = await page.evaluate(async () => {
    const auth = await (await fetch('/services/internal/data/articles-getAuthenticationStatus', { credentials: 'include' })).json();
    if (!auth.result?.data?.authenticated) return { loggedIn: false };
    const host = [...document.querySelectorAll('[x-data]')].find(e => e.getAttribute('x-data') === 'draftModel');
    const nodes = host && window.Alpine ? Alpine.$data(host).sortedNodes : [];
    const man = await (await fetch('/__xp/manifest.json')).json();
    return { loggedIn: true, user: auth.result.data.username, man, nodes: nodes.map(n => ({ id: n.id, title: n.title, visibility: n.visibility })) };
  });
  await page.unroute('https://dzone.com/__xp/**');
  if (!pending.loggedIn) return 'NOT LOGGED IN to DZone';
  await page.goto('https://dzone.com/authors/xavidop');
  await page.waitForTimeout(2500);
  const published = await page.evaluate(async () => {
    const links = [...new Set([...document.querySelectorAll('a[href^="/articles/"]')].map(a => a.getAttribute('href').split('?')[0]))].filter(h => !/how-to-submit|submission-guidelines/.test(h)).slice(0, 25);
    const out = [];
    for (const h of links) { const t = await (await fetch(h)).text(); const m = t.match(/<link[^>]+rel="canonical"[^>]+href="([^"]+)"/) || t.match(/<link[^>]+href="([^"]+)"[^>]+rel="canonical"/); out.push({ url: 'https://dzone.com' + h, canonical: m ? m[1] : null }); }
    return out;
  });
  const norm = s => (s || '').replace(/\/$/, '');
  // The drafts list HTML-escapes titles (&amp;) and cuts long ones to about 70 chars + "...".
  const decode = s => s.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;|&#x27;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>');
  const sameTitle = (dz, blog) => { const t = decode(dz).trim(); return t.endsWith('...') ? blog.startsWith(t.slice(0, -3).trim()) : t === blog; };
  return pending.man.posts.map(p => {
    const pub = published.find(x => norm(x.canonical) === norm(p.canonical));
    const node = pending.nodes.find(n => sameTitle(n.title, p.title));
    return (pub ? 'PUBLISHED ' + pub.url : node ? node.visibility.toUpperCase() + ' ' + node.id : 'new') + '  ' + p.name;
  }).join('\n');
}
```

Only `new` posts go into the next step. A leftover `DRAFT` (from a run that halted) should be opened, checked and
submitted by hand rather than re-created.

## 3. Submit a batch

Set `NAMES` to at most five `new` posts per call (each takes 30-60 s). For every post it fills the form, checks
everything **before** saving (no validation errors, author present, image uploaded, all code blocks in the body),
saves a draft, reloads it to confirm what DZone stored, and only then submits to moderation. It stops at the first
problem and says whether a draft was left behind.

```js
async (page) => {
  const NAMES = ['<post-name-1>', '<post-name-2>'];
  const DATA = '<REPO>/.playwright-mcp/crosspost/';
  const onDialog = d => d.accept().catch(() => {});
  page.on('dialog', onDialog);
  const go = async (url) => { await page.evaluate(() => { window.onbeforeunload = null; }).catch(() => {}); await page.goto(url); };
  const scope = () => page.evaluate(() => { const s = angular.element(document.querySelector('[ng-model="article.title"]')).scope(); return { errors: s.errors.map(e => e.value), authorErr: s.validation && s.validation.author, authors: s.authors.filter(a => !a.removed).map(a => a.id + ':' + a.type), a: { title: s.article.title, src: s.article.originalSource, type: s.article.articleType, hasImage: s.article.hasImage, state: s.article.state } }; });
  const results = [];
  try {
    for (const file of NAMES) {
      await go('https://dzone.com/content/article/post.html');
      await page.waitForSelector('.fr-element');
      await page.waitForTimeout(1500);
      await page.route('https://dzone.com/__xp/**', r => r.fulfill({ path: DATA + r.request().url().split('/__xp/')[1], contentType: r.request().url().endsWith('.jpg') ? 'image/jpeg' : 'application/json' }));
      const p = await page.evaluate(async (f) => { const p = await (await fetch('/__xp/' + f + '.json')).json(); window.__p = p; return { title: p.title, short: p.short_description, canonical: p.canonical, type: p.dzone_type, cover: p.cover_jpg, code: p.code_blocks }; }, file);
      if (!p.cover) { results.push(file + ' HALT: no cover_jpg in payload'); break; }
      await page.fill('textarea[name=title]', p.title);
      await page.fill('textarea[name=subtitle]', p.short);
      await page.fill('#meta-description-textarea', p.short);
      await page.fill('[ng-model="article.originalSource"]', p.canonical);
      await page.evaluate(() => { const ed = FroalaEditor.INSTANCES[0]; ed.html.set(window.__p.dzone_html); ed.undo.saveStep(); ed.events.trigger('contentChanged'); });
      await page.getByText('Not set', { exact: true }).click();
      await page.getByRole('link', { name: p.type.charAt(0).toUpperCase() + p.type.slice(1), exact: true }).click();
      await page.locator('.select-users .ui-select-match').click();
      await page.locator('.select-users input.ui-select-search').fill('Xavier Portilla');
      await page.locator('.select-users .ui-select-choices-row').filter({ hasText: 'Voiceflow' }).first().click({ timeout: 15000 });
      let upStatus = null;
      const onResp = r => { if (/uploadFile/.test(r.url())) upStatus = r.status(); };
      page.on('response', onResp);
      await page.evaluate(async (name) => { const blob = await (await fetch('/__xp/img/' + name)).blob(); const sc = angular.element(document.querySelector('input[type=file][ng-file-change]')).scope(); sc.$apply(() => sc.upload([new File([blob], name, { type: 'image/jpeg' })])); }, p.cover);
      for (let k = 0; k < 40; k++) { await page.waitForTimeout(1000); if (upStatus && await page.evaluate(() => !angular.element(document.querySelector('input[type=file][ng-file-change]')).scope().uploading)) break; }
      page.off('response', onResp);
      await page.unroute('https://dzone.com/__xp/**');
      await page.locator('textarea[name=title]').click();
      await page.waitForTimeout(500);
      const pre = await scope();
      const bodyCode = await page.evaluate(() => (FroalaEditor.INSTANCES[0].html.get().match(/codeMirror-code--wrapper/g) || []).length);
      const problems = [];
      if (pre.errors.length) problems.push('errors: ' + pre.errors.join('/'));
      if (pre.authorErr) problems.push('author: ' + pre.authorErr);
      if (!pre.a.hasImage) problems.push('no image (upload HTTP ' + upStatus + ')');
      if (bodyCode !== p.code) problems.push('code blocks ' + bodyCode + '/' + p.code);
      if (!pre.authors.includes('4278252:author')) problems.push('author missing ' + pre.authors);
      if (problems.length) { results.push(file + ' HALT before save (nothing saved): ' + problems.join('; ')); break; }
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.getByRole('button', { name: 'Save draft' }).first().click();
      await page.waitForURL(/\/content\/\d+\/edit\.html/, { timeout: 30000 });
      const id = page.url().match(/content\/(\d+)\//)[1];
      await go('https://dzone.com/content/' + id + '/edit.html');
      await page.waitForSelector('.fr-element');
      await page.waitForTimeout(2500);
      const saved = await scope();
      const savedCode = await page.evaluate(() => { const d = document.createElement('div'); d.innerHTML = angular.element(document.querySelector('[ng-model="article.title"]')).scope().article.body || ''; return d.querySelectorAll('.codeMirror-code--wrapper').length; });
      const ok = saved.a.title === p.title && saved.a.src === p.canonical && saved.a.hasImage && savedCode === p.code && saved.authors.includes('4278252:author') && !saved.errors.length;
      if (!ok) { results.push(file + ' HALT after save (draft ' + id + ' left, not submitted): ' + JSON.stringify({ saved, savedCode })); break; }
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.waitForTimeout(500);
      const item = () => page.locator('li.dropdown-actions:has-text("Submit to Moderation")').locator('visible=true');
      for (let attempt = 0; attempt < 3 && !(await item().count()); attempt++) { const b = await page.getByRole('button', { name: 'Save', exact: true }).first().boundingBox(); await page.mouse.click(b.x + b.width + 12, b.y + b.height / 2); await page.waitForTimeout(700); }
      if (!(await item().count())) { results.push(file + ' draft ' + id + ' saved but the Submit menu did not open; retry the submit alone'); break; }
      await item().first().click();
      let state = null;
      for (let k = 0; k < 25; k++) { await page.waitForTimeout(1000); state = await page.evaluate(() => { const el = document.querySelector('[ng-model="article.title"]'); return el ? angular.element(el).scope().article.state : null; }); if (state === 'moderation') break; }
      results.push(file + ' -> draft ' + id + ', state=' + state + ', type=' + saved.a.type + ', code=' + savedCode + '/' + p.code + ', image=' + saved.a.hasImage);
      if (state !== 'moderation') break;
    }
  } catch (e) { results.push('ERROR: ' + e.message.slice(0, 300)); }
  page.off('dialog', onDialog);
  return results.join('\n');
}
```

To submit a saved draft on its own (e.g. after "Submit menu did not open"): `go` to its `edit.html`, then run the
last block of the loop (open the caret up to three times, click the visible item, wait for `state === 'moderation'`).

## 4. Verify

Run the status snippet (step 2) again: every post should read `MODERATION <id>` (or `PUBLISHED` later on). Also
count the drafts-page entries per post (two entries with the same title prefix means a duplicate submission).

## 5. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `run_code` returns nothing and the tool reports a `beforeunload` dialog | Navigating away from an unsaved form | `browser_handle_dialog` with `accept: true`; the snippet sets `window.onbeforeunload = null` and auto-accepts to avoid it |
| "TL;DR is too short" / "too long" | TL;DR outside 120-175 chars | Fix `short_description` in the overrides and rebuild |
| "Please add an author in the contributors field" | The original poster (`op`) does not count as author | Add yourself through the contributor search (Voiceflow account) |
| Image stays "No image selected", upload HTTP 500 | Cover too large for DZone's uploader | Use the build's JPEG (< 350 KB); lower quality further if needed |
| Image stays "No image selected", no upload request | `setInputFiles` does not reach the old ng-file-upload handler (and Chromium skips `change` for the same file) | Call the widget scope's `upload([File])` as the snippet does |
| Submit click times out | The split-button menu closed or never opened | Re-open the caret and click the visible `li.dropdown-actions`; retry up to three times |
| Wrong code highlighting | Language not in the build's `DZ_LANG` map | Add the language (name + CodeMirror MIME) to `scripts/crosspost.py` |
