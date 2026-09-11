---
layout: page
title: Open Source
description: >
  The projects I build and maintain in the open, grouped by what they are for:
  Genkit and AI tooling, Go libraries and CLIs, full products, templates, and
  the voice back catalogue.
---

Everything here is public, most of it on [github.com/xavidop](https://github.com/xavidop) and the rest under the [genkit-ai](https://github.com/genkit-ai) org. This page is the curated version, grouped by what each thing is actually for. Star counts are a snapshot from September 2026.

<div class="oss">
{% for group in site.data.projects %}
  <section class="oss-group">
    <h2 id="{{ group.category | slugify }}">{{ group.category }}</h2>
    {% if group.blurb %}<p class="oss-blurb">{{ group.blurb }}</p>{% endif %}
    <div class="oss-grid">
      {% for p in group.projects %}
        <div class="oss-card">
          <h3 class="oss-name"><a href="{{ p.url }}">{{ p.name }}</a></h3>
          <p class="oss-meta">
            {% if p.lang %}<span class="oss-lang">{{ p.lang }}</span>{% endif %}
            {% if p.stars and p.stars > 0 %}<span class="oss-stars">&#9733; {{ p.stars }}</span>{% endif %}
          </p>
          <p class="oss-desc">{{ p.desc }}</p>
          <p class="oss-links">
            <a href="{{ p.url }}">Source</a>
            {% if p.homepage %}<a href="{{ p.homepage }}">Website</a>{% endif %}
          </p>
        </div>
      {% endfor %}
    </div>
  </section>
{% endfor %}
</div>

<style>
.oss-group { margin-bottom: 2.5rem; }
.oss-blurb { opacity: .75; margin-top: -.4rem; }
.oss-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}
.oss-card {
  border: 1px solid rgba(128,128,128,.3);
  border-radius: .4rem;
  padding: .9rem 1rem 1rem;
  display: flex;
  flex-direction: column;
}
.oss-card:hover { border-color: rgb(79,177,186); }
.oss-name { margin: 0 0 .25rem; font-size: 1.05rem; line-height: 1.25; word-break: break-word; }
.oss-name a { border-bottom: none; }
.oss-meta { margin: 0 0 .5rem; font-size: .78rem; opacity: .7; }
.oss-lang { margin-right: .6rem; }
.oss-stars { white-space: nowrap; }
.oss-desc { margin: 0 0 .75rem; font-size: .88rem; line-height: 1.45; flex: 1 1 auto; }
.oss-links { margin: 0; font-size: .8rem; }
.oss-links a { margin-right: .8rem; }
@media (max-width: 30rem) { .oss-grid { grid-template-columns: 1fr; } }
</style>
