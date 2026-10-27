"""Build the website's main page (docs/index.html) from PROJECT_EXPLAINED.md, so the two never drift apart.

Keeps the site's look (the <style> block of the current docs/index.html), adds a contents rail from the
numbered sections, turns ```mermaid blocks into rendered diagrams and images into captioned figures.
Usage: python scripts/17_build_site.py
"""

import html
import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "PROJECT_EXPLAINED.md"
OUT = ROOT / "docs" / "index.html"


def main() -> None:
    style = re.search(r"<style>.*?</style>", OUT.read_text(), re.S).group(0)
    style = style.replace("</style>", "figure { margin: 8px 0 22px; }\nfigure img { display: block; width: 100%; height: auto; border-radius: 6px; border: 1px solid var(--rule); background: #fff; }\nfigcaption { font-size: 14px; color: var(--muted); margin-top: 6px; }\ncode { font-family: var(--mono); font-size: .88em; background: var(--code-bg); padding: 1px 4px; border-radius: 3px; }\nhr { border: 0; border-top: 1px solid var(--rule); margin: 8px 0; }\n</style>")
    md = SRC.read_text()
    title = re.match(r"# (.+)\n", md).group(1)
    body_md = md.split("\n", 1)[1]
    body = markdown.markdown(body_md, extensions=["tables", "fenced_code"])

    # Diagrams, tables and figures.
    body = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>',
                  lambda m: f'<div class="diagram"><pre class="mermaid">{m.group(1)}</pre></div>', body, flags=re.S)
    body = re.sub(r"<table>(.*?)</table>", r'<div class="tablebox"><table>\1</table></div>', body, flags=re.S)
    body = re.sub(r'<p><img alt="([^"]*)" src="docs/([^"]+)" ?/?></p>',
                  lambda m: f'<figure><img src="{m.group(2)}" alt="{m.group(1)}" loading="lazy"><figcaption>{m.group(1)}</figcaption></figure>', body)
    body = body.replace("<hr />", "")

    # Split into numbered sections with a contents rail.
    parts = re.split(r"<h2>(.*?)</h2>", body)
    intro, sections, toc = parts[0], [], []
    for i in range(1, len(parts), 2):
        heading = html.unescape(parts[i])
        m = re.match(r"(\d+)\.\s+(.*)", heading)
        num, name = (m.group(1), m.group(2)) if m else ("", heading)
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
        toc.append(f'<li><a href="#{slug}">{html.escape(name)}</a></li>')
        sections.append(f'<section id="{slug}">\n<h2><span class="n">{int(num):02d}</span>{html.escape(name)}</h2>\n{parts[i + 1]}</section>')

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Plain-language explanation of the ToolLife Policy project: what we built, the data, the models, the results.">
<title>ToolLife Policy</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
{style}
</head>
<body>
<div class="wrap">
<nav class="toc" aria-label="Contents">
  <div class="label">Contents</div>
  <ol>
    {chr(10).join(toc)}
  </ol>
</nav>
<main>
<header class="hero">
  <div class="eyebrow">AI in Manufacturing · course project · what we built</div>
  <h1>ToolLife <span>Policy</span></h1>
  <p class="lede">Predicting when a CNC milling cutter will break, from its motor current and vibration, and deciding when to change it.</p>
</header>
{intro}
{chr(10).join(sections)}
<footer>Generated from <span class="mono">PROJECT_EXPLAINED.md</span> by <span class="mono">scripts/17_build_site.py</span>. Code and data: <a href="https://github.com/Aadityakshatriya/AI-in-manufacturing">github.com/Aadityakshatriya/AI-in-manufacturing</a>.</footer>
</main>
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>
  var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  mermaid.initialize({{ startOnLoad: true, theme: dark ? 'dark' : 'neutral', flowchart: {{ useMaxWidth: true }} }});
</script>
</body>
</html>
"""
    OUT.write_text(page)
    print(f"{OUT}: {len(sections)} sections, title {title!r}")


if __name__ == "__main__":
    sys.exit(main())
