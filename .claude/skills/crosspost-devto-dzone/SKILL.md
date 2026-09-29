---
name: crosspost-devto-dzone
description: Cross-post (syndicate) articles from Xavi's Jekyll blog xavidop.me to dev.to (https://dev.to/xavidop) and DZone (https://dzone.com/authors/xavidop), with canonical links back to the blog. Covers finding which posts are not published yet, converting kramdown/Jekyll markdown for each platform, publishing on dev.to, and submitting to DZone moderation through the logged-in browser. Use this whenever the user asks to publish, republish, share, cross-post or syndicate blog posts or "my articles" on dev.to, DEV Community, Forem or DZone, asks which posts are still missing on those sites, or wants to fix a cross-posted article there, even if they only name one of the two platforms.
---

# Cross-post blog posts to dev.to and DZone

Posts live in `<category>/_posts/YYYY-MM-DD-slug.md` and are canonical on `https://xavidop.me/<category>/<name>/`.
dev.to publishes immediately; DZone only takes submissions to its editorial moderation queue. Both copies point
back to xavidop.me (dev.to `canonical_url`, DZone "Original Source") so search credit stays with the blog.

Neither site gets an API key here: everything goes through the **user's logged-in sessions in the Playwright MCP
browser**. dev.to's editor endpoints and DZone's editor form are driven with `browser_run_code_unsafe`.

## Ground rules

- **Publishing is public and outward-facing.** The user's request to cross-post authorizes it, but list the exact
  posts you are about to publish first. Never publish anything already on the platform (check both published and
  drafts), and never create a second copy when a run is retried: the snippets are written to skip existing items.
- **Keep executed code visible.** Paste the snippets from the reference files inline into
  `browser_run_code_unsafe`. Only data (JSON payloads, JPEGs) is read from disk, through `page.route`. Loading a
  JS file via the tool's `filename` parameter was blocked by the auto-mode permission check as unreviewable code;
  do not route around such a denial, ask the user instead.
- **Content stays the blog's content.** Do not rewrite articles. The only new text is the short description and
  the tags. Short descriptions follow Xavi's style: no em dashes, plain and direct, his voice (see the
  `writing-style-preferences` memory).
- Verify each step with real output (API state, reloaded forms, screenshots) before claiming it worked.

## Workflow

Paths below are relative to the repo root. `SK=.claude/skills/crosspost-devto-dzone`.

### 1. Pick the posts and check what already exists

```bash
python3 $SK/scripts/crosspost.py status --since YYYY-MM-DD      # or: status <post-name> ...
```

This lists posts in the range and whether dev.to already has them (matched by canonical URL, then title). It sees
only public dev.to articles, and it cannot see DZone (Cloudflare blocks scripts). So also run the browser checks:
the dev.to session check (`references/devto.md` §1, which includes drafts) and the DZone status check
(`references/dzone.md` §2), after the build in step 3 produces the manifest. Skip non-English posts
(`lang=es`) unless the user asks for them.

Before any browser step, make sure the user is logged in to both sites in the Playwright browser. If not, ask them
to log in there and wait.

### 2. Write the overrides (short descriptions, tags, series, type, order)

```bash
python3 $SK/scripts/crosspost.py init-overrides <names...> --out <scratchpad>/overrides.json
```

Then edit that file (keep it outside the repo). For each post:

- `short_description`: **120-175 characters** (DZone's TL;DR limit), no em dashes. It becomes the dev.to
  description, DZone's TL;DR and DZone's meta description. Condense the post's own `_full_description`; keep its
  hook and its concrete numbers ("73 lines in Genkit Go against 272 in LangChainGo").
- `tags`: 1-4 lowercase alphanumeric dev.to tags, most relevant first. Prefer tags people follow (`go`, `ai`,
  `devops`, `kubernetes`, `aws`, `azure`, `googlecloud`, `security`, `opensource`, `tutorial`, `llm`) plus one
  specific one (`genkit`, `langchain`, `cicd`).
- `series`: a dev.to series name for launch sets that read in order (existing: `mamori`, `senro`), else `null`.
- `dzone_type`: `analysis` for comparisons, `tutorial` for guides (also `opinion`, `news`, `review`).
- `order`: publish order. Oldest first; inside a series, the introduction first and then the natural reading order.

### 3. Build the payloads

```bash
python3 $SK/scripts/crosspost.py build --overrides <scratchpad>/overrides.json
```

Writes `.playwright-mcp/crosspost/<name>.json`, `img/<name>.jpg` and `manifest.json` (that folder is where the
Playwright MCP server is allowed to read from). The build strips the frontmatter and Hydejack TOC seed, resolves
`{% post_url %}` and root-relative links to absolute xavidop.me URLs, re-fences code blocks that contain ```
(dev.to breaks on them), renders DZone HTML with pandoc in DZone's code-block format, and makes a JPEG cover under
350 KB. It refuses to build when a short description or tags break the rules, and prints warnings for anything
it could not map. Needs `pandoc`, and `sips` (macOS) for the covers.

### 4. dev.to

Follow `references/devto.md`: session check → preview validation of every post (no side effects) → first post as
a draft, check its fields and a screenshot of the preview → publish all in manifest order → verify.

### 5. DZone

Follow `references/dzone.md`: status check → submit `new` posts in batches of up to five → verify that every post
reads `MODERATION`.

### 6. Clean up and report

- `rm -rf .playwright-mcp` (build output, screenshots and console logs from the browser tool; never commit it)
  and confirm `git status` is as clean as it was before.
- Update the `crossposting-devto-dzone` memory with the date of the newest post cross-posted.
- Report to the user:
  - dev.to: one link per published article, grouped by series or topic.
  - DZone: count submitted and "In Moderation"; editors publish later and may retitle.
  - Anything that differs from the blog version (new short descriptions, JPEG covers on DZone, dev.to's tab
    expansion in code) and anything skipped or left as a draft, with the reason.
  - Anything odd you noticed on the accounts (e.g. a broken title on an older post), without fixing it unasked.

## Files

- `scripts/crosspost.py`: `status`, `init-overrides`, `build`. Constants at the top hold the dev.to username,
  DZone's TL;DR limits, the JPEG size cap and the code-language → DZone MIME map.
- `references/devto.md`: dev.to snippets (session check, preview validation, draft, publish, verify) and fixes.
- `references/dzone.md`: DZone editor model, snippets (status, batch submit, verify) and fixes.
