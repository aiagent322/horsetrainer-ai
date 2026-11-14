#!/usr/bin/env python3
"""Build the scrolling subject bar inside the sticky home-page header.

Reads every category cell (name, slug, answer count) from qa/index.html and
writes a horizontally scrollable chip strip into index.html between the
<!-- subject-bar --> markers (and the CSS between /* subject-bar */ markers).
Order: most answers first. Run after any Q&A rebuild:
    python3 -I tools/build_subject_bar.py
"""
import html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cells = re.findall(
    r'<a class="cat-cell" href="/qa/([a-z0-9-]+)/">\s*<div class="cat-name">(.*?)</div>\s*<div class="cat-count">([\d,]+) answers?</div>',
    open(os.path.join(ROOT, "qa", "index.html"), encoding="utf-8").read(), re.S)
seen, rows = set(), []
for slug, name, cnt in cells:
    if slug in seen:
        continue
    seen.add(slug)
    rows.append((int(cnt.replace(",", "")), html.unescape(name).strip(), slug))
rows.sort(key=lambda r: (-r[0], r[1]))

chips = "\n".join(
    f'      <a href="/qa/{slug}/">{html.escape(name, quote=False)}</a>' for _, name, slug in rows)
BAR = (
    "<!-- subject-bar -->\n"
    '  <div class="subject-bar" role="navigation" aria-label="Browse all training subjects">\n'
    '    <div class="subject-scroll">\n'
    '      <a href="/qa/" class="all">All subjects</a>\n'
    f"{chips}\n"
    "    </div>\n"
    "  </div>\n"
    "  <!-- /subject-bar -->"
)
CSS = """/* subject-bar */
.subject-bar { border-top:1px solid var(--border-light); }
.subject-scroll {
  display:flex; gap:6px; align-items:center; max-width:var(--max-w); margin:0 auto;
  padding:6px 16px 8px; overflow-x:auto; overflow-y:hidden; white-space:nowrap;
  -webkit-overflow-scrolling:touch; scrollbar-width:none; overscroll-behavior-x:contain;
}
.subject-scroll::-webkit-scrollbar { display:none; }
.subject-scroll a {
  flex:0 0 auto; display:inline-flex; align-items:center; min-height:40px;
  padding:0 14px; border:1px solid var(--border); border-radius:999px;
  font-size:0.85rem; font-weight:500; color:var(--text-mid); text-decoration:none; background:#fff;
}
.subject-scroll a:hover { background:var(--bg-alt); color:var(--primary); }
.subject-scroll a.all { background:var(--primary); border-color:var(--primary); color:#fff; font-weight:600; }
@media(min-width:900px){ .subject-scroll a { min-height:32px; font-size:0.82rem; } .subject-scroll { scrollbar-width:thin; } }
/* /subject-bar */"""

p = os.path.join(ROOT, "index.html")
s = open(p, encoding="utf-8").read()
if "<!-- subject-bar -->" in s:
    s = re.sub(r"<!-- subject-bar -->.*?<!-- /subject-bar -->", lambda m: BAR, s, flags=re.S)
else:
    s = s.replace("  </div>\n</header>", "  </div>\n  " + BAR + "\n</header>", 1)
if "/* subject-bar */" in s:
    s = re.sub(r"/\* subject-bar \*/.*?/\* /subject-bar \*/", lambda m: CSS, s, flags=re.S)
else:
    s = s.replace("/* ═══════════════════════════════════════\n   HERO", CSS + "\n\n/* ═══════════════════════════════════════\n   HERO", 1)
s = s.replace("scroll-padding-top:100px", "scroll-padding-top:150px", 1)
open(p, "w", encoding="utf-8").write(s)
print(len(rows), "subjects in bar")
