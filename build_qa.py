#!/usr/bin/env python3
"""
HorseTrainer.ai — Q&A Section Builder
Generates static HTML pages under /qa/ matching the existing site design.
Run locally, then commit the qa/ folder to GitHub.

Usage: python3 build_qa.py
Output: ./qa/ directory (push this to the repo root)
"""

import json, os, re, ssl, sys, urllib.request
from collections import defaultdict
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://ptuuuishzwwgmaexneul.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
BASE_URL     = "https://horsetrainer-ai.pages.dev"
OUT          = "qa"   # output folder — push this to repo root

# ── Helpers ────────────────────────────────────────────────────────────────
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-")

def first_n_words(text, n=50):
    words = text.split()
    snippet = " ".join(words[:n])
    return snippet + ("…" if len(words) > n else "")

def first_n_chars(text, n=155):
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0] + "…"

def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ qa/{path}")

def fetch_all_qa():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    all_rows = []
    offset = 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/qa?select=id,category,question,answer&order=category,id&limit=1000&offset={offset}"
        req = urllib.request.Request(
            url,
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        )
        with urllib.request.urlopen(req, context=ctx) as r:
            batch = json.loads(r.read())
        if not batch:
            break
        all_rows.extend(batch)
        offset += len(batch)
        if len(batch) < 1000:
            break
    return all_rows

# ── Shared CSS (matches existing horsetrainer.ai design) ───────────────────
SHARED_CSS = """
:root {
  --primary:#0b3c5d;--primary-light:#144e78;--secondary:#1d6fa5;
  --accent:#2a8fd4;--gold:#b8860b;--gold-light:#d4a017;
  --bg:#ffffff;--bg-alt:#f4f6f8;--bg-warm:#faf9f7;
  --text:#1f2933;--text-mid:#4a5568;--text-light:#6b7280;
  --border:#e5e7eb;--border-light:#f0f1f3;
  --radius:6px;--max-w:1100px;--transition:0.2s ease;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%;}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color:var(--text);background:var(--bg);line-height:1.65;font-size:16px;
  -webkit-font-smoothing:antialiased;overflow-x:hidden;}
a{color:var(--secondary);text-decoration:none;transition:color var(--transition);}
a:hover{color:var(--primary);text-decoration:underline;}
.container{max-width:var(--max-w);margin:0 auto;padding:0 16px;}
:focus-visible{outline:2px solid var(--secondary);outline-offset:2px;border-radius:2px;}
:focus:not(:focus-visible){outline:none;}

/* Header */
.site-header{position:sticky;top:0;z-index:100;
  background:rgba(255,255,255,0.97);border-bottom:1px solid var(--border);
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);}
.header-top{display:flex;justify-content:space-between;align-items:center;
  max-width:var(--max-w);margin:0 auto;padding:10px 16px;}
.site-logo{font-weight:800;font-size:1.05rem;color:var(--primary);letter-spacing:-0.02em;}
.site-logo span{color:var(--secondary);}
.nav-toggle{display:flex;align-items:center;justify-content:center;
  background:none;border:none;cursor:pointer;padding:8px;min-width:44px;min-height:44px;}
.nav-toggle svg{width:24px;height:24px;stroke:var(--text);}
.main-nav{display:none;flex-direction:column;padding:4px 16px 12px;gap:2px;
  border-top:1px solid var(--border-light);}
.main-nav.open{display:flex;}
.main-nav a{padding:10px 16px;border-radius:var(--radius);font-size:0.92rem;
  font-weight:500;color:var(--text-mid);min-height:44px;display:flex;align-items:center;
  transition:background var(--transition),color var(--transition);}
.main-nav a:hover{background:var(--bg-alt);color:var(--primary);text-decoration:none;}
.main-nav a.active{background:var(--primary);color:#fff;}
@media(min-width:768px){
  .nav-toggle{display:none;}
  .main-nav{display:flex!important;flex-direction:row;padding:0;gap:4px;
    border-top:none;align-items:center;}
  .main-nav a{padding:7px 14px;font-size:0.88rem;min-height:auto;}
}

/* Page hero */
.qa-hero{background:#003D79;color:#fff;padding:32px 16px 24px;}
.qa-hero .container{max-width:var(--max-w);margin:0 auto;}
.qa-eyebrow{display:inline-block;background:rgba(255,255,255,0.12);
  color:rgba(255,255,255,0.9);font-size:0.75rem;font-weight:600;
  letter-spacing:0.08em;text-transform:uppercase;
  padding:4px 12px;border-radius:20px;margin-bottom:12px;}
.qa-hero h1{font-size:1.6rem;font-weight:800;line-height:1.2;
  letter-spacing:-0.02em;margin-bottom:10px;}
.qa-hero h1 em{font-style:normal;color:#7ec8f0;}
.qa-hero p{font-size:0.95rem;color:rgba(255,255,255,0.8);max-width:560px;line-height:1.55;}
.hero-stats{display:flex;gap:0;border-top:1px solid rgba(255,255,255,0.12);
  margin-top:20px;padding-top:16px;}
.stat-item{flex:1;text-align:center;padding:0 8px;
  border-right:1px solid rgba(255,255,255,0.12);}
.stat-item:last-child{border-right:none;}
.stat-num{font-size:1.4rem;font-weight:800;color:#fff;}
.stat-label{font-size:0.72rem;color:rgba(255,255,255,0.65);text-transform:uppercase;
  letter-spacing:0.06em;margin-top:2px;}

/* Breadcrumb */
.breadcrumb{font-size:0.82rem;color:var(--text-light);
  padding:12px 0;border-bottom:1px solid var(--border-light);}
.breadcrumb a{color:var(--text-light);}
.breadcrumb a:hover{color:var(--primary);}
.breadcrumb span{margin:0 6px;opacity:.5;}

/* Search */
.qa-search{padding:20px 0;}
.qa-search .search-wrap{position:relative;max-width:560px;}
.qa-search input{width:100%;border:1.5px solid var(--border);border-radius:8px;
  padding:11px 16px 11px 42px;font-size:0.95rem;background:var(--bg-alt);
  color:var(--text);transition:border-color var(--transition);}
.qa-search input:focus{outline:none;border-color:var(--secondary);background:#fff;}
.qa-search .search-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);
  color:var(--text-light);font-size:1rem;pointer-events:none;}

/* Category grid */
.cat-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;
  background:var(--border);border:1px solid var(--border);
  border-radius:var(--radius);overflow:hidden;margin:8px 0 24px;}
@media(min-width:600px){.cat-grid{grid-template-columns:repeat(3,1fr);}}
@media(min-width:900px){.cat-grid{grid-template-columns:repeat(4,1fr);}}
.cat-cell{background:var(--bg);padding:16px;text-decoration:none;display:block;
  transition:background var(--transition);}
.cat-cell:hover{background:var(--bg-alt);text-decoration:none;}
.cat-name{font-size:0.9rem;font-weight:600;color:var(--primary);margin-bottom:3px;}
.cat-count{font-size:0.78rem;color:var(--text-light);}

/* Q&A cards */
.qa-list{display:flex;flex-direction:column;gap:0;}
.qa-card{border:1px solid var(--border);border-radius:var(--radius);
  padding:18px 20px;margin-bottom:10px;background:var(--bg);
  transition:box-shadow var(--transition),border-color var(--transition);}
.qa-card:hover{border-color:var(--secondary);box-shadow:0 2px 8px rgba(11,60,93,0.08);}
.qa-card .q-num{font-size:0.72rem;font-weight:700;text-transform:uppercase;
  letter-spacing:0.08em;color:var(--gold);margin-bottom:6px;}
.qa-card h2{font-size:1rem;font-weight:700;color:var(--primary);
  line-height:1.35;margin-bottom:10px;}
.qa-card h2 a{color:var(--primary);}
.qa-card h2 a:hover{color:var(--secondary);text-decoration:none;}
.qa-card .preview{font-size:0.88rem;color:var(--text-mid);line-height:1.6;margin-bottom:12px;}
.qa-card .read-btn{display:inline-flex;align-items:center;gap:5px;
  font-size:0.82rem;font-weight:600;color:var(--secondary);
  border:1.5px solid var(--secondary);border-radius:var(--radius);
  padding:6px 14px;transition:all var(--transition);}
.qa-card .read-btn:hover{background:var(--secondary);color:#fff;text-decoration:none;}

/* Section heading */
.section-head{display:flex;align-items:center;justify-content:space-between;
  margin:24px 0 14px;}
.section-head h2{font-size:1rem;font-weight:700;color:var(--primary);}
.section-head .count{font-size:0.82rem;color:var(--text-light);}

/* Full answer page */
.answer-wrap{max-width:800px;}
.answer-meta{margin-bottom:20px;}
.answer-meta .cat-badge{display:inline-block;background:var(--bg-alt);
  color:var(--secondary);font-size:0.75rem;font-weight:600;
  letter-spacing:0.06em;text-transform:uppercase;
  padding:4px 10px;border-radius:20px;margin-bottom:12px;
  border:1px solid var(--border);}
.answer-wrap h1{font-size:1.4rem;font-weight:800;color:var(--primary);
  line-height:1.3;margin-bottom:20px;}
@media(min-width:600px){.answer-wrap h1{font-size:1.65rem;}}
.full-answer{font-size:1rem;line-height:1.8;color:var(--text);
  border-left:4px solid var(--secondary);padding-left:20px;
  background:var(--bg-warm);padding:20px 20px 20px 24px;
  border-radius:0 var(--radius) var(--radius) 0;}

/* Related */
.related-section{border-top:1px solid var(--border);padding-top:24px;margin-top:32px;}
.related-section h3{font-size:0.78rem;font-weight:700;text-transform:uppercase;
  letter-spacing:0.08em;color:var(--text-light);margin-bottom:14px;}
.related-link{display:flex;align-items:flex-start;gap:10px;
  padding:12px 0;border-bottom:1px solid var(--border-light);text-decoration:none;}
.related-link:last-child{border-bottom:none;}
.related-link:hover{text-decoration:none;}
.related-link .rel-q{font-size:0.9rem;font-weight:600;color:var(--primary);
  transition:color var(--transition);}
.related-link:hover .rel-q{color:var(--secondary);}
.related-link .rel-arrow{color:var(--text-light);flex-shrink:0;margin-top:2px;}

/* Find trainer CTA */
.trainer-cta{background:var(--bg-alt);border:1px solid var(--border);
  border-radius:var(--radius);padding:20px;margin:28px 0;
  display:flex;align-items:center;gap:16px;flex-wrap:wrap;}
.trainer-cta .cta-text strong{display:block;font-size:0.95rem;color:var(--primary);margin-bottom:4px;}
.trainer-cta .cta-text span{font-size:0.82rem;color:var(--text-mid);}
.trainer-cta .cta-btn{display:inline-flex;align-items:center;gap:6px;
  background:var(--gold);color:#fff;font-weight:700;font-size:0.88rem;
  border-radius:var(--radius);padding:10px 20px;white-space:nowrap;
  transition:background var(--transition);}
.trainer-cta .cta-btn:hover{background:var(--gold-light);color:#fff;text-decoration:none;}

/* Category chips for search filter */
.chip-row{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 16px;}
.chip{font-size:0.78rem;padding:4px 12px;border:1px solid var(--border);
  border-radius:20px;color:var(--text-mid);background:var(--bg);
  cursor:pointer;transition:all var(--transition);}
.chip:hover,.chip.active{background:var(--primary);color:#fff;border-color:var(--primary);}

/* Footer */
.site-footer{background:var(--primary);color:rgba(255,255,255,0.75);padding:32px 16px 20px;}
.footer-inner{max-width:var(--max-w);margin:0 auto;}
.footer-top{display:grid;gap:24px;grid-template-columns:1fr;margin-bottom:24px;}
@media(min-width:600px){.footer-top{grid-template-columns:2fr 1fr 1fr;}}
.footer-brand-name{font-weight:800;font-size:1.05rem;color:#fff;margin-bottom:6px;}
.footer-brand-name span{color:#7ec8f0;}
.footer-brand-desc{font-size:0.82rem;line-height:1.6;}
.footer-heading{font-size:0.75rem;font-weight:700;text-transform:uppercase;
  letter-spacing:0.08em;color:rgba(255,255,255,0.5);margin-bottom:10px;}
.footer-links{list-style:none;display:flex;flex-direction:column;gap:6px;}
.footer-links a{font-size:0.85rem;color:rgba(255,255,255,0.7);}
.footer-links a:hover{color:#fff;text-decoration:none;}
.footer-bottom{border-top:1px solid rgba(255,255,255,0.1);padding-top:16px;
  display:flex;flex-wrap:wrap;gap:8px;justify-content:space-between;font-size:0.78rem;}
.footer-bottom a{color:rgba(255,255,255,0.5);}
.footer-bottom a:hover{color:rgba(255,255,255,0.85);text-decoration:none;}
.bb-badge{display:inline-flex;align-items:center;gap:6px;
  font-size:0.75rem;color:rgba(255,255,255,0.5);}
"""

# ── Shared HTML Fragments ──────────────────────────────────────────────────
def html_head(title, desc, canonical, extra_meta=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
{extra_meta}
<style>{SHARED_CSS}</style>
</head>
<body>"""

def html_header(active_page="qa"):
    return f"""<header class="site-header">
  <div class="header-top">
    <a href="/" class="site-logo">Horse<span>Trainer</span>.AI</a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false" aria-controls="main-nav">
      <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>
    <nav class="main-nav" id="main-nav">
      <a href="/#find-a-trainer">Find a Trainer</a>
      <a href="/reining/">Reining</a>
      <a href="/barrel-racing/">Barrel Racing</a>
      <a href="/colt-starting/">Colt Starting</a>
      <a href="/videos/">Videos</a>
      <a href="/famous-trainers/">Famous Trainers</a>
      <a href="/qa/" class="active">Training Q&amp;A</a>
      <a href="/list-your-training/">List Your Training</a>
    </nav>
  </div>
</header>
<script>
document.getElementById('nav-toggle').addEventListener('click',function(){{
  var nav=document.getElementById('main-nav');
  var open=nav.classList.toggle('open');
  this.setAttribute('aria-expanded',open);
}});
</script>"""

def html_footer():
    return f"""<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-top">
      <div>
        <div class="footer-brand-name">Horse<span>Trainer</span>.AI</div>
        <div class="footer-brand-desc">Expert horse training Q&amp;A and AI-powered trainer matching across all 50 states.</div>
        <div class="bb-badge" style="margin-top:14px;">
          <span>A</span>
          <a href="https://www.bridleandbit.com" style="color:rgba(255,255,255,0.5);font-size:0.75rem;" target="_blank" rel="noopener">Bridle &amp; Bit Magazine</a>
          <span>service</span>
        </div>
      </div>
      <div>
        <div class="footer-heading">Training Q&amp;A</div>
        <ul class="footer-links">
          <li><a href="/qa/">All Categories</a></li>
          <li><a href="/qa/horsemanship/">Horsemanship</a></li>
          <li><a href="/qa/reining/">Reining</a></li>
          <li><a href="/qa/training-principles/">Training Principles</a></li>
          <li><a href="/qa/cutting/">Cutting</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-heading">Directory</div>
        <ul class="footer-links">
          <li><a href="/#find-a-trainer">Find a Trainer</a></li>
          <li><a href="/list-your-training/">List Your Training</a></li>
          <li><a href="/famous-trainers/">Famous Trainers</a></li>
          <li><a href="https://www.bridleandbit.com" target="_blank" rel="noopener">Bridle &amp; Bit</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; {datetime.now().year} Bridle &amp; Bit Magazine &middot; HorseTrainer.AI</span>
      <a href="/qa/sitemap.xml">Sitemap</a>
    </div>
  </div>
</footer>
</body>
</html>"""

def html_trainer_cta():
    return """<div class="trainer-cta">
  <div class="cta-text">
    <strong>Find the Right Trainer</strong>
    <span>1,700+ verified trainers across Arizona and the Southwest</span>
  </div>
  <a href="/#find-a-trainer" class="cta-btn">Find My Trainer →</a>
</div>"""

# ── Q&A Landing Page ───────────────────────────────────────────────────────
def build_landing(categories, total):
    print("\nBuilding qa/index.html…")

    cat_cells = ""
    for cat, info in sorted(categories.items()):
        cat_cells += f"""<a class="cat-cell" href="/qa/{slugify(cat)}/">
  <div class="cat-name">{cat}</div>
  <div class="cat-count">{info['count']} answers</div>
</a>
"""
    title = f"Horse Training Q&A — {total} Expert Answers | HorseTrainer.AI"
    desc  = f"Expert answers to {total} horse training questions across {len(categories)} disciplines — horsemanship, reining, cutting, barrel racing, trail, and more."
    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": desc,
        "url": f"{BASE_URL}/qa/"
    })

    html = html_head(title, desc, f"{BASE_URL}/qa/",
                     f'<script type="application/ld+json">{schema}</script>') + \
           html_header() + f"""
<section class="qa-hero">
  <div class="container">
    <div class="qa-eyebrow">Expert Horse Training</div>
    <h1>Training Q&amp;A — <em>{total} Answers</em></h1>
    <p>Professional answers across {len(categories)} disciplines, from horsemanship fundamentals to advanced competition training.</p>
    <div class="hero-stats">
      <div class="stat-item"><div class="stat-num">{total}</div><div class="stat-label">Answers</div></div>
      <div class="stat-item"><div class="stat-num">{len(categories)}</div><div class="stat-label">Disciplines</div></div>
      <div class="stat-item"><div class="stat-num">1,700+</div><div class="stat-label">Trainers</div></div>
    </div>
  </div>
</section>

<main class="container" style="padding:24px 16px 40px;">
  <nav class="breadcrumb"><a href="/">Home</a><span>›</span>Training Q&amp;A</nav>

  <div class="qa-search">
    <div class="search-wrap">
      <span class="search-icon">🔍</span>
      <input type="text" id="cat-search" placeholder="Search categories…" autocomplete="off">
    </div>
  </div>

  <div class="section-head">
    <h2>Browse by Discipline</h2>
    <span class="count">{len(categories)} categories</span>
  </div>

  <div class="cat-grid" id="cat-grid">
{cat_cells}
  </div>

  {html_trainer_cta()}
</main>

<script>
var inp=document.getElementById('cat-search');
if(inp){{
  inp.addEventListener('input',function(){{
    var q=this.value.toLowerCase();
    document.querySelectorAll('.cat-cell').forEach(function(c){{
      c.style.display=c.textContent.toLowerCase().includes(q)?'':'none';
    }});
  }});
}}
</script>
""" + html_footer()

    write("index.html", html)

# ── Category Page ──────────────────────────────────────────────────────────
def build_category(category, qa_list):
    print(f"  {category} ({len(qa_list)} Qs)")
    cat_slug = slugify(category)

    cards = ""
    for i, qa in enumerate(qa_list, 1):
        q_slug = slugify(qa["question"])
        preview = first_n_words(qa["answer"], 50)
        cards += f"""<div class="qa-card">
  <p class="q-num">Q {i:02d} of {len(qa_list)}</p>
  <h2><a href="/qa/{cat_slug}/{q_slug}/">{qa['question']}</a></h2>
  <p class="preview">{preview}</p>
  <a class="read-btn" href="/qa/{cat_slug}/{q_slug}/">Read full answer →</a>
</div>
"""

    title = f"{category} Training Q&A — {len(qa_list)} Expert Answers | HorseTrainer.AI"
    desc  = f"Expert answers to {len(qa_list)} horse training questions about {category}. Learn from professional trainers."
    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": qa["question"],
             "acceptedAnswer": {"@type": "Answer", "text": qa["answer"][:300]}}
            for qa in qa_list[:10]
        ]
    })

    html = html_head(title, desc, f"{BASE_URL}/qa/{cat_slug}/",
                     f'<script type="application/ld+json">{schema}</script>') + \
           html_header() + f"""
<section class="qa-hero">
  <div class="container">
    <div class="qa-eyebrow">Horse Training Q&amp;A</div>
    <h1>{category}</h1>
    <p>{len(qa_list)} expert questions &amp; answers from professional trainers</p>
  </div>
</section>

<main class="container" style="padding:24px 16px 40px;">
  <nav class="breadcrumb">
    <a href="/">Home</a><span>›</span>
    <a href="/qa/">Training Q&amp;A</a><span>›</span>
    {category}
  </nav>

  <div class="qa-search">
    <div class="search-wrap">
      <span class="search-icon">🔍</span>
      <input type="text" id="qa-search" placeholder="Search {category} questions…" autocomplete="off">
    </div>
  </div>

  <div class="section-head">
    <h2>All Questions</h2>
    <span class="count">{len(qa_list)} answers</span>
  </div>

  <div class="qa-list" id="qa-list">
{cards}
  </div>

  {html_trainer_cta()}
</main>

<script>
var inp=document.getElementById('qa-search');
if(inp){{
  inp.addEventListener('input',function(){{
    var q=this.value.toLowerCase();
    document.querySelectorAll('.qa-card').forEach(function(c){{
      c.style.display=c.textContent.toLowerCase().includes(q)?'':'none';
    }});
  }});
}}
</script>
""" + html_footer()

    write(f"{cat_slug}/index.html", html)

# ── Individual Answer Page ─────────────────────────────────────────────────
def build_answer(qa, cat_qa_list):
    cat_slug = slugify(qa["category"])
    q_slug   = slugify(qa["question"])
    url      = f"{BASE_URL}/qa/{cat_slug}/{q_slug}/"

    related = [q for q in cat_qa_list if q["id"] != qa["id"]][:4]
    related_html = ""
    for r in related:
        r_slug = slugify(r["question"])
        related_html += f"""<a class="related-link" href="/qa/{cat_slug}/{r_slug}/">
  <span class="rel-arrow">›</span>
  <span class="rel-q">{r['question']}</span>
</a>
"""

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": qa["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": qa["answer"]}}]
    })

    title = f"{qa['question']} | {qa['category']} | HorseTrainer.AI"
    desc  = first_n_chars(qa["answer"], 155)

    html = html_head(title, desc, url,
                     f'<script type="application/ld+json">{schema}</script>') + \
           html_header() + f"""
<main class="container" style="padding:24px 16px 48px;">
  <nav class="breadcrumb">
    <a href="/">Home</a><span>›</span>
    <a href="/qa/">Training Q&amp;A</a><span>›</span>
    <a href="/qa/{cat_slug}/">{qa['category']}</a><span>›</span>
    Answer
  </nav>

  <article class="answer-wrap">
    <div class="answer-meta">
      <span class="cat-badge">{qa['category']}</span>
      <h1>{qa['question']}</h1>
    </div>
    <div class="full-answer">
      <p>{qa['answer']}</p>
    </div>
  </article>

  {html_trainer_cta()}
"""
    if related_html:
        html += f"""
  <section class="related-section">
    <h3>More {qa['category']} Questions</h3>
    {related_html}
    <a href="/qa/{cat_slug}/" style="display:block;margin-top:14px;font-size:0.85rem;color:var(--text-light);">
      View all {qa['category']} questions →
    </a>
  </section>
"""
    html += "\n</main>\n" + html_footer()
    write(f"{cat_slug}/{q_slug}/index.html", html)

# ── Sitemap ────────────────────────────────────────────────────────────────
def build_sitemap(all_urls):
    today = datetime.now().strftime("%Y-%m-%d")
    urls  = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>"
        for u in all_urls
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>"""
    write("sitemap.xml", xml)
    print(f"\n  Sitemap: {len(all_urls)} URLs")

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    if not SUPABASE_KEY:
        sys.exit("ERROR: Set SUPABASE_KEY environment variable before running.")
    print("=" * 52)
    print("HorseTrainer.ai — Q&A Section Builder")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 52)

    print("\nFetching Q&A from Supabase…")
    qa_data = fetch_all_qa()
    print(f"  {len(qa_data)} entries")

    categories = defaultdict(lambda: {"count": 0, "items": []})
    for qa in qa_data:
        categories[qa["category"]]["count"] += 1
        categories[qa["category"]]["items"].append(qa)

    os.makedirs(OUT, exist_ok=True)
    all_urls = [f"{BASE_URL}/qa/"]

    # Landing page
    build_landing(categories, len(qa_data))

    # Category + answer pages
    print("\nBuilding category and answer pages…")
    for cat, info in sorted(categories.items()):
        build_category(cat, info["items"])
        cat_slug = slugify(cat)
        all_urls.append(f"{BASE_URL}/qa/{cat_slug}/")
        for qa in info["items"]:
            q_slug = slugify(qa["question"])
            build_answer(qa, info["items"])
            all_urls.append(f"{BASE_URL}/qa/{cat_slug}/{q_slug}/")

    build_sitemap(all_urls)

    print("\n" + "=" * 52)
    print(f"Done: {len(all_urls)} pages → ./{OUT}/")
    print(f"Next: commit the qa/ folder to aiagent322/horsetrainer-ai")
    print("=" * 52)

if __name__ == "__main__":
    main()
