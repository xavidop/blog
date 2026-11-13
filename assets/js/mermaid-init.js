/*
 * Mermaid diagrams for the blog.
 *
 * A fenced code block with the language "mermaid" is drawn as a diagram, in the colours of the
 * page: the palette is read from Hydejack's CSS variables, so it follows light and dark mode.
 * The library is only downloaded on pages that have such a block.
 *
 * Loaded as a file (see _includes/my-scripts.html), not inline: the production build compresses
 * the HTML into one line, which breaks inline scripts that hold line comments.
 */
const MERMAID = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
const ACCENT = '#4fb1ba';
let lib;

/* The page's real colours, whatever switched the theme: the toggle, the time of day or the OS. */
function palette() {
  const probe = document.createElement('span');
  probe.style.cssText = 'position:absolute;visibility:hidden;color:var(--body-color,#333);background-color:var(--body-bg,#fff);border:1px solid var(--border-color,#ddd)';
  document.body.appendChild(probe);
  const cs = getComputedStyle(probe);
  const colors = { text: cs.color, bg: cs.backgroundColor, border: cs.borderTopColor };
  probe.remove();
  const [r, g, b] = (colors.bg.match(/[\d.]+/g) || [255, 255, 255]).map(Number);
  colors.dark = 0.2126 * r + 0.7152 * g + 0.0722 * b < 128;
  return colors;
}

function config(c) {
  const node = c.dark ? '#313b41' : '#ffffff';
  const routeFill = c.dark ? '#24454a' : '#e6f4f5';
  const store = c.dark ? '#2b3438' : '#f4f6f7';
  const line = c.dark ? '#8fa3ab' : '#7b8a91';
  const muted = c.dark ? '#aab7bd' : '#5d6b72';
  return {
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'base',
    fontFamily: '"Noto Sans", Helvetica, Arial, sans-serif',
    flowchart: { curve: 'basis', nodeSpacing: 36, rankSpacing: 60, padding: 16, useMaxWidth: true },
    themeVariables: {
      darkMode: c.dark,
      background: 'transparent',
      fontFamily: '"Noto Sans", Helvetica, Arial, sans-serif',
      fontSize: '15px',
      primaryColor: node,
      primaryTextColor: c.text,
      primaryBorderColor: ACCENT,
      secondaryColor: store,
      tertiaryColor: store,
      lineColor: line,
      textColor: c.text,
      mainBkg: node,
      nodeBorder: ACCENT,
      clusterBkg: store,
      clusterBorder: c.border,
      edgeLabelBackground: c.bg,
      titleColor: c.text,
    },
    themeCSS: [
      '.node rect, .node polygon, .node path, .node circle, .node ellipse { stroke-width: 1.5px; }',
      '.node rect.basic { rx: 10px; ry: 10px; }',
      '.node polygon { fill: ' + routeFill + '; }',
      '.node path { fill: ' + store + '; stroke: ' + line + '; }',
      '.nodeLabel { font-weight: 600; line-height: 1.35; }',
      '.flowchart-link { stroke: ' + line + '; stroke-width: 1.6px; }',
      '.marker { fill: ' + line + '; stroke: ' + line + '; }',
      '.edgeLabel, .edgeLabel p, .edgeLabel span { color: ' + muted + '; font-size: 12px; font-weight: 400; background-color: ' + c.bg + '; }',
      '.edgeLabel p { padding: 0 6px; }',
    ].join(' '),
  };
}

async function draw(nodes) {
  if (!nodes.length) return;
  lib = lib || import(MERMAID).then((m) => m.default);
  const mermaid = await lib;
  const c = palette();
  mermaid.initialize(config(c));
  nodes.forEach((n) => {
    n.removeAttribute('data-processed');
    n.textContent = n.dataset.source;
    n.dataset.theme = c.dark ? 'dark' : 'light';
  });
  try {
    await mermaid.run({ nodes });
  } catch (err) {
    console.error('mermaid:', err);
  }
  /* A diagram that could not be drawn shows its source instead of an empty box. */
  nodes.forEach((n) => {
    if (n.querySelector('svg')) return;
    n.textContent = n.dataset.source;
    n.setAttribute('data-processed', 'failed');
    n.style.cssText = 'white-space:pre;text-align:left;font-family:monospace';
  });
}

/* Turn every rendered mermaid code block into a container that mermaid can draw into. */
function convert() {
  const made = [];
  document.querySelectorAll('.language-mermaid code, code.language-mermaid').forEach((code) => {
    const block = code.closest('.language-mermaid.highlighter-rouge') || code.closest('pre') || code;
    const div = document.createElement('div');
    div.className = 'mermaid mermaid-diagram';
    div.dataset.source = code.textContent.trim();
    block.replaceWith(div);
    made.push(div);
  });
  return made;
}

const drawNew = () => draw(convert());

let pending;
function redrawIfThemeChanged() {
  clearTimeout(pending);
  pending = setTimeout(() => {
    const now = palette().dark ? 'dark' : 'light';
    draw([...document.querySelectorAll('.mermaid-diagram')].filter((n) => n.dataset.theme && n.dataset.theme !== now));
  }, 150);
}

drawNew();
const pushState = document.getElementById('_pushState');
if (pushState) pushState.addEventListener('hy-push-state-load', drawNew);
new MutationObserver(redrawIfThemeChanged).observe(document.body, { attributes: true, attributeFilter: ['class'] });
document.addEventListener('hydejack-dark-mode-toggle', redrawIfThemeChanged);
if (window.matchMedia) matchMedia('(prefers-color-scheme: dark)').addEventListener('change', redrawIfThemeChanged);
