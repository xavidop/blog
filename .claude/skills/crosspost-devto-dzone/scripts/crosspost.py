#!/usr/bin/env python3
"""Cross-post helper for the xavidop.me Jekyll blog: find posts, check dev.to, build dev.to + DZone payloads.

Subcommands:
  status          List posts in a date range and whether dev.to already has them (by canonical URL / title).
  init-overrides  Write a per-post overrides skeleton (short description, tags, series, DZone type, order).
  build           Convert posts listed in an overrides file into payload JSON + upload-safe JPEG covers.

The build output goes to <repo>/.playwright-mcp/crosspost/ by default, because the Playwright MCP server may only
read files inside the repo, and page.route() serves these files to the dev.to / DZone pages from there.
"""
import argparse
import datetime
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

DEVTO_USER = 'xavidop'
DZONE_TLDR_MIN, DZONE_TLDR_MAX = 120, 175  # DZone rejects a TL;DR outside this range.
JPEG_MAX_BYTES = 350_000                   # DZone's uploader returns HTTP 500 on larger covers despite its "1MB" label.

# DZone code-block language name + CodeMirror MIME. go/bash/json/yaml/text/Dockerfile/PowerShell were read from
# DZone's language picker; the rest come from CodeMirror's mode list, which is what DZone's picker is built on.
DZ_LANG = {
    'go': ('Go', 'text/x-go'), 'golang': ('Go', 'text/x-go'),
    'bash': ('Shell', 'text/x-sh'), 'sh': ('Shell', 'text/x-sh'), 'shell': ('Shell', 'text/x-sh'),
    'zsh': ('Shell', 'text/x-sh'), 'console': ('Shell', 'text/x-sh'),
    'json': ('JSON', 'application/json'), 'yaml': ('YAML', 'text/x-yaml'), 'yml': ('YAML', 'text/x-yaml'),
    'dockerfile': ('Dockerfile', 'text/x-dockerfile'), 'powershell': ('PowerShell', 'application/x-powershell'),
    'javascript': ('JavaScript', 'text/javascript'), 'js': ('JavaScript', 'text/javascript'),
    'typescript': ('TypeScript', 'application/typescript'), 'ts': ('TypeScript', 'application/typescript'),
    'python': ('Python', 'text/x-python'), 'py': ('Python', 'text/x-python'),
    'java': ('Java', 'text/x-java'), 'kotlin': ('Kotlin', 'text/x-kotlin'), 'csharp': ('C#', 'text/x-csharp'),
    'rust': ('Rust', 'text/x-rustsrc'), 'sql': ('SQL', 'text/x-sql'), 'xml': ('XML', 'application/xml'),
    'html': ('HTML', 'text/html'), 'toml': ('TOML', 'text/x-toml'), 'diff': ('Diff', 'text/x-diff'),
    'protobuf': ('ProtoBuf', 'text/x-protobuf'), 'proto': ('ProtoBuf', 'text/x-protobuf'),
    'text': ('Plain Text', 'text/plain'), 'txt': ('Plain Text', 'text/plain'), 'plaintext': ('Plain Text', 'text/plain'),
    '': ('Plain Text', 'text/plain'),
}

TAG_ALIASES = {'golang': 'go', 'gcp': 'googlecloud', 'k8s': 'kubernetes', 'ci-cd': 'cicd', 'genai': 'ai',
               'generative-ai': 'ai', 'llms': 'llm', 'typescript': 'typescript', 'nodejs': 'node'}
DZONE_TYPES = {'tutorial', 'analysis', 'opinion', 'news', 'review'}


def fail(msg):
    sys.exit(f'error: {msg}')


def repo_root():
    try:
        root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, check=True).stdout.strip()
        if os.path.exists(os.path.join(root, '_config.yml')):
            return root
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    # <repo>/.claude/skills/crosspost-devto-dzone/scripts/crosspost.py
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


def site_url(root):
    m = re.search(r'^url:\s*(\S+)', open(os.path.join(root, '_config.yml')).read(), re.M)
    return (m.group(1) if m else 'https://xavidop.me').rstrip('/')


def split_post(path):
    raw = open(path).read()
    if not raw.startswith('---\n'):
        fail(f'{path}: no frontmatter')
    fm, body = raw[4:].split('\n---\n', 1)
    return fm, body


def fm_field(fm, key):
    m = re.search(rf'^{key}:\s*(.*)$', fm, re.M)
    return m.group(1).strip() if m else None


def fm_list(fm, key):
    inline = fm_field(fm, key)
    if inline and inline.startswith('['):
        return [x.strip().strip('"\'') for x in inline.strip('[]').split(',') if x.strip()]
    m = re.search(rf'^{key}:\s*\n((?:\s+- .*\n?)+)', fm + '\n', re.M)
    return [x.strip().strip('"\'') for x in re.findall(r'^\s+- (.*)$', m.group(1), re.M)] if m else []


def fm_description(fm):
    m = re.search(r'^description:\s*[>|]-?\s*\n((?:[ \t]+.*\n?)+)', fm + '\n', re.M)
    text = ' '.join(l.strip() for l in m.group(1).splitlines()) if m else (fm_field(fm, 'description') or '').strip('"\'')
    return strip_lang_suffix(text)


def strip_lang_suffix(s):
    return re.sub(r'\s*\((English|Spanish|Español)\)\s*$', '', s.strip())


class Post:
    def __init__(self, root, path):
        self.path = path
        self.name = os.path.basename(path)[:-3]
        self.date = self.name[:10]
        self.fm, self.body = split_post(path)
        title = fm_field(self.fm, 'title') or ''
        self.title = strip_lang_suffix(title.strip('"\'').replace('\\"', '"'))
        self.description = fm_description(self.fm)
        self.categories = fm_list(self.fm, 'categories')
        self.tags = fm_list(self.fm, 'tags')
        self.lang = fm_field(self.fm, 'lang') or 'en'
        self.image = fm_field(self.fm, 'image')
        site = site_url(root)
        self.canonical = f"{site}/{'/'.join(self.categories)}/{self.name}/"
        self.cover_url = site + self.image if self.image else None
        self.cover_path = os.path.join(root, self.image.lstrip('/')) if self.image else None


def all_posts(root):
    paths = [p for p in glob.glob(os.path.join(root, '*', '_posts', '*.md')) if '/_site/' not in p]
    return sorted((Post(root, p) for p in paths), key=lambda p: p.name)


def select(posts, since=None, until=None, names=None):
    out = posts
    if names:
        wanted = {os.path.basename(n)[:-3] if n.endswith('.md') else os.path.basename(n) for n in names}
        out = [p for p in out if p.name in wanted]
        missing = wanted - {p.name for p in out}
        if missing:
            fail(f'unknown posts: {sorted(missing)}')
    if since:
        out = [p for p in out if p.date >= since]
    if until:
        out = [p for p in out if p.date <= until]
    return out


# ---------------------------------------------------------------- status

def devto_articles():
    """Public, published articles only. dev.to's edge caches each list URL for up to an hour (a cache-buster
    param is ignored, but per_page is part of the key), so vary the page size per run to get a fresh list.
    The logged-in /api/articles/me/all check in the browser stays authoritative and also sees drafts."""
    size = 70 + int(time.time()) % 30
    arts, page = [], 1
    while True:
        req = urllib.request.Request(f'https://dev.to/api/articles?username={DEVTO_USER}&per_page={size}&page={page}',
                                     headers={'User-Agent': 'crosspost-skill'})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.load(r)
        arts += batch
        if len(batch) < size:
            return arts
        page += 1


def norm_title(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def cmd_status(args):
    root = repo_root()
    posts = select(all_posts(root), args.since, args.until, args.posts)
    arts = devto_articles()
    by_canon = {(a.get('canonical_url') or '').rstrip('/'): a for a in arts}
    by_title = {norm_title(a['title']): a for a in arts}
    rows = []
    for p in posts:
        a = by_canon.get(p.canonical.rstrip('/')) or by_title.get(norm_title(p.title))
        rows.append({'name': p.name, 'title': p.title, 'lang': p.lang, 'canonical': p.canonical,
                     'devto': a['url'] if a else None})
    if args.json:
        print(json.dumps(rows, indent=1))
        return
    print(f'{len(rows)} post(s); dev.to public articles checked: {len(arts)} (drafts are not visible here)')
    for r in rows:
        flag = 'on dev.to ' if r['devto'] else 'NOT on dev.to'
        lang = '' if r['lang'] == 'en' else f' [lang={r["lang"]}]'
        print(f"{flag:13} {r['name']}{lang}\n{'':13}   {r['title']}" + (f"\n{'':13}   {r['devto']}" if r['devto'] else ''))
    print('\nDZone cannot be checked from here (Cloudflare blocks scripts); check it in the browser.')


# ---------------------------------------------------------------- init-overrides

def suggest_tags(p):
    tags = []
    for t in p.categories + p.tags:
        t = TAG_ALIASES.get(t.lower(), t.lower())
        t = re.sub(r'[^a-z0-9]', '', t)
        if t and t not in tags:
            tags.append(t)
    return tags[:4]


def cmd_init_overrides(args):
    root = repo_root()
    posts = select(all_posts(root), args.since, args.until, args.posts)
    if not posts:
        fail('no posts selected')
    if os.path.exists(args.out) and not args.force:
        fail(f'{args.out} exists (use --force to overwrite)')
    skeleton = {}
    for i, p in enumerate(posts):
        fits = DZONE_TLDR_MIN <= len(p.description) <= DZONE_TLDR_MAX and '—' not in p.description
        comparison = re.search(r'\bvs\.?\b|comparison|compared', p.title + ' ' + ' '.join(p.tags), re.I)
        skeleton[p.name] = {
            'order': i + 1,
            'short_description': p.description if fits else '',
            '_full_description': p.description,
            'tags': suggest_tags(p),
            'series': None,
            'dzone_type': 'analysis' if comparison else 'tutorial',
        }
    json.dump(skeleton, open(args.out, 'w'), indent=2, ensure_ascii=False)
    todo = [n for n, v in skeleton.items() if not v['short_description']]
    print(f'wrote {args.out} for {len(skeleton)} post(s)')
    if todo:
        print(f'short_description needed ({DZONE_TLDR_MIN}-{DZONE_TLDR_MAX} chars, no em dashes) for:')
        for n in todo:
            print(f'  {n} (full description is {len(skeleton[n]["_full_description"])} chars)')


# ---------------------------------------------------------------- build

def resolve_post_url(root, site, target):
    d, name = target.split('/', 1)
    path = os.path.join(root, d, '_posts', name + '.md')
    if not os.path.exists(path):
        fail(f'post_url target not found: {target}')
    fm, _ = split_post(path)
    return f"{site}/{'/'.join(fm_list(fm, 'categories'))}/{name}/"


FENCED_BLOCK = re.compile(r'(^([ \t]*)(```|~~~).*?^\2\3[ \t]*$)', re.S | re.M)


def map_prose(md, fn):
    """Apply fn to everything outside fenced code blocks, leaving code untouched."""
    parts, last = [], 0
    for m in FENCED_BLOCK.finditer(md):
        parts += [fn(md[last:m.start()]), m.group(1)]
        last = m.end()
    return ''.join(parts + [fn(md[last:])])


def clean_body(root, site, p):
    body = re.sub(r'^\{:\.no_toc\}\n1\. this unordered seed list.*\n\{:toc\}\n', '', p.body, flags=re.M)
    body = re.sub(r'\{%\s*post_url\s+(\S+)\s*%\}', lambda m: resolve_post_url(root, site, m.group(1)), body)

    def absolutize(text):
        text = re.sub(r'\]\((/[^)\s]*)\)', lambda m: f']({site}{m.group(1)})', text)                 # md links/images
        return re.sub(r'(src|href)="(/[^"]*)"', lambda m: f'{m.group(1)}="{site}{m.group(2)}"', text)  # raw HTML
    body = map_prose(body, absolutize)
    outside_code = FENCED_BLOCK.sub('', body)
    if re.search(r'\{:[^}]*\}', outside_code):
        fail(f'{p.name}: leftover kramdown attribute ({re.search(r"{:[^}]*}", outside_code).group(0)}); handle it first')
    if '{%' in outside_code:
        fail(f'{p.name}: Liquid tag outside code blocks ({re.search(r"{%.{0,40}", outside_code).group(0)}); resolve it first')
    return body.lstrip('\n')


def tilde_fence_nested_backticks(md):
    """dev.to pairs ``` before its Liquid pass, so a code block containing ``` (e.g. a Go "```json" literal) gets
    split and the article fails with "Unknown tag 'endraw'". Re-fence those blocks with ~~~ (renders the same)."""
    def refence(m):
        return m.group(0) if '```' not in m.group(3) else f'{m.group(1)}~~~{m.group(2)}\n{m.group(3)}\n{m.group(1)}~~~'
    return re.sub(r'^([ \t]*)```(\S*)\n(.*?)\n\1```[ \t]*$', refence, md, flags=re.S | re.M)


def to_dzone_html(md, name, warnings):
    out = subprocess.run(['pandoc', '-f', 'gfm-gfm_auto_identifiers', '-t', 'html', '--wrap=none',
                          '--syntax-highlighting=none'], input=md, capture_output=True, text=True, check=True).stdout

    def code(m):
        lang = (m.group(1) or '').lower()
        if lang not in DZ_LANG:
            warnings.append(f'{name}: code language "{lang}" not mapped, using Plain Text')
        label, mime = DZ_LANG.get(lang, DZ_LANG[''])
        text = html.unescape(m.group(2))
        esc = html.escape(text, quote=True)
        return (f'<div class="codeMirror-wrapper" contenteditable="false"><div contenteditable="false">'
                f'<div class="codeHeader"><div class="nameLanguage">{label}</div>'
                f'<i class="icon-cancel-circled-1 cm-remove">&nbsp;</i></div>'
                f'<div class="codeMirror-code--wrapper" data-code="{esc}" data-lang="{mime}">'
                f'<pre><code lang="{mime}">{esc}</code></pre></div></div></div>')

    out, n = re.subn(r'<pre(?: class="([\w+#-]+)")?><code>(.*?)</code></pre>', code, out, flags=re.S)
    if '<pre' in out.replace('<pre><code lang=', ''):
        fail(f'{name}: pandoc produced a <pre> block the DZone converter did not recognise')
    return out, n


def jpeg_cover(src, dst):
    """DZone-safe cover: JPEG under JPEG_MAX_BYTES (macOS sips)."""
    if not shutil.which('sips'):
        return None
    for q in (88, 80, 72, 65, 58, 50, 42):
        subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', str(q), src, '--out', dst],
                       capture_output=True, check=True)
        if os.path.getsize(dst) < JPEG_MAX_BYTES:
            return dst
    return None


def validate_override(name, o):
    errs = []
    sd = o.get('short_description') or ''
    if not DZONE_TLDR_MIN <= len(sd) <= DZONE_TLDR_MAX:
        errs.append(f'short_description is {len(sd)} chars, needs {DZONE_TLDR_MIN}-{DZONE_TLDR_MAX}')
    if '—' in sd:
        errs.append('short_description contains an em dash')
    tags = o.get('tags') or []
    if not 1 <= len(tags) <= 4 or any(not re.fullmatch(r'[a-z0-9]+', t) for t in tags):
        errs.append(f'tags must be 1-4 lowercase alphanumeric words, got {tags}')
    if o.get('dzone_type') not in DZONE_TYPES:
        errs.append(f'dzone_type must be one of {sorted(DZONE_TYPES)}')
    return [f'{name}: {e}' for e in errs]


def cmd_build(args):
    if not shutil.which('pandoc'):
        fail('pandoc is required (brew install pandoc)')
    root = repo_root()
    site = site_url(root)
    overrides = json.load(open(args.overrides))
    posts = {p.name: p for p in select(all_posts(root), names=list(overrides))}
    errs = [e for n, o in overrides.items() for e in validate_override(n, o)]
    if errs:
        fail('fix the overrides file:\n  ' + '\n  '.join(errs))
    out_dir = args.out or os.path.join(root, '.playwright-mcp', 'crosspost')
    os.makedirs(os.path.join(out_dir, 'img'), exist_ok=True)
    warnings, manifest = [], []
    ordered = sorted(overrides.items(), key=lambda kv: (kv[1].get('order', 999), kv[0]))
    for name, o in ordered:
        p = posts[name]
        md = clean_body(root, site, p)
        dz_html, ncode = to_dzone_html(md, name, warnings)
        n_fences = len(re.findall(r'^\s*```', md, re.M)) // 2
        if ncode != n_fences:
            fail(f'{name}: converted {ncode} code blocks but found {n_fences} fences')
        cover_jpg = None
        if p.cover_path and os.path.exists(p.cover_path):
            if jpeg_cover(p.cover_path, os.path.join(out_dir, 'img', name + '.jpg')):
                cover_jpg = name + '.jpg'
            else:
                warnings.append(f'{name}: could not make a JPEG cover under {JPEG_MAX_BYTES} bytes')
        else:
            warnings.append(f'{name}: no cover image in frontmatter or file missing ({p.image})')
        if p.lang != 'en':
            warnings.append(f'{name}: lang is {p.lang}')
        payload = {
            'name': name, 'title': p.title, 'description': p.description,
            'short_description': o['short_description'], 'canonical': p.canonical,
            'cover_url': p.cover_url, 'cover_jpg': cover_jpg, 'tags': o['tags'], 'series': o.get('series'),
            'dzone_type': o['dzone_type'], 'devto_md': tilde_fence_nested_backticks(md), 'dzone_html': dz_html,
            'code_blocks': ncode,
        }
        json.dump(payload, open(os.path.join(out_dir, name + '.json'), 'w'))
        manifest.append({k: payload[k] for k in ('name', 'title', 'canonical', 'series', 'dzone_type', 'code_blocks', 'cover_jpg')})
    json.dump({'generated': datetime.datetime.now().isoformat(timespec='seconds'), 'site': site, 'posts': manifest},
              open(os.path.join(out_dir, 'manifest.json'), 'w'), indent=1)
    print(f'built {len(manifest)} payload(s) in {out_dir} (publish order below)')
    for i, m in enumerate(manifest, 1):
        print(f"{i:2}. {m['name']}  code={m['code_blocks']} cover={'ok' if m['cover_jpg'] else 'MISSING'}"
              f"{'  series=' + m['series'] if m['series'] else ''}")
    for w in warnings:
        print('warning:', w)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('status', 'init-overrides'):
        s = sub.add_parser(name)
        s.add_argument('posts', nargs='*', help='post names or paths (default: all in range)')
        s.add_argument('--since', help='YYYY-MM-DD, inclusive')
        s.add_argument('--until', help='YYYY-MM-DD, inclusive')
        if name == 'status':
            s.add_argument('--json', action='store_true')
        else:
            s.add_argument('--out', required=True, help='overrides JSON to write (keep it outside the repo)')
            s.add_argument('--force', action='store_true')
    b = sub.add_parser('build')
    b.add_argument('--overrides', required=True)
    b.add_argument('--out', help='output dir (default: <repo>/.playwright-mcp/crosspost)')
    args = ap.parse_args()
    {'status': cmd_status, 'init-overrides': cmd_init_overrides, 'build': cmd_build}[args.cmd](args)


if __name__ == '__main__':
    main()
