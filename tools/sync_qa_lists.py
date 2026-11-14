#!/usr/bin/env python3
"""Make each qa/<cat>/index.html list every answer page that exists, and make every stated count match.
Run from repo root. Idempotent. (Offline stand-in for build_qa.py when SUPABASE_KEY is unavailable.)"""
import re, glob, html, json, os
def attr(s, pat):
    m = re.search(pat, s, re.S); return html.unescape(m.group(1)).strip() if m else ''
cats = {}
for p in sorted(glob.glob('qa/*/index.html')):
    cat = p.split('/')[1]; s = open(p, encoding='utf-8').read()
    linked = set(re.findall(r'href="/qa/%s/([^"/]+)/?"' % re.escape(cat), s))
    dirs = sorted(os.path.basename(os.path.dirname(x)) for x in glob.glob(f'qa/{cat}/*/index.html'))
    n_old = len(re.findall(r'class="qa-card"', s)); n = len(dirs)
    add = ''
    i = n_old
    for d in dirs:
        if d in linked: continue
        a = open(f'qa/{cat}/{d}/index.html', encoding='utf-8').read()
        q = attr(a, r'"@type": "Question", "name": ("(?:[^"\\]|\\.)*")')
        q = json.loads(f'"{q}"') if False else (json.loads(re.search(r'"@type": "Question", "name": ("(?:[^"\\]|\\.)*")', a).group(1)) if re.search(r'"@type": "Question", "name": ("(?:[^"\\]|\\.)*")', a) else attr(a, r'<h1[^>]*>(.*?)</h1>'))
        pv = attr(a, r'<meta name="description" content="([^"]*)"')
        i += 1; u = f'/qa/{cat}/{d}/'
        add += (f'<div class="qa-card">\n  <p class="q-num">Q {i:02d} of {n}</p>\n  <h2><a href="{u}">{html.escape(q, quote=False)}</a></h2>\n'
                f'  <p class="preview">{html.escape(pv, quote=False)}</p>\n  <a class="read-btn" href="{u}">Read full answer →</a>\n</div>\n')
    if add:
        k = s.index('</div>\n', s.rindex('<a class="read-btn"')) + len('</div>\n')
        s = s[:k] + add + s[k:]
    if n_old != n or add:
        s = re.sub(r'(Q \d+ of )%d\b' % n_old, lambda m: m.group(1) + str(n), s)
    # stated counts: any "<old> Expert Answers|answers|horse training questions" -> n
    m = re.search(r'([\d,]+) Expert Answers', s)
    old = int(m.group(1).replace(',', '')) if m else n_old
    if old != n:
        fmt = lambda x: f'{x:,}'
        s = re.sub(r'\b%s (Expert Answers|answers|horse training questions)' % re.escape(fmt(old)), lambda m: f'{fmt(n)} {m.group(1)}', s)
        s = re.sub(r'\b%d (Expert Answers|answers|horse training questions)' % old, lambda m: f'{n} {m.group(1)}', s)
    open(p, 'w', encoding='utf-8').write(s); cats[cat] = n
# hub counts
tot = sum(cats.values()); t = f'{tot:,}'
q = open('qa/index.html', encoding='utf-8').read()
for cat, n in cats.items():
    q = re.sub(r'(<a[^>]*href="/qa/%s/"[^>]*>.*?<div class="cat-count">)[\d,]+ answers' % re.escape(cat), lambda m: f'{m.group(1)}{n} answers', q, flags=re.S, count=1)
q = re.sub(r'[\d,]+( Expert Answers| horse training questions)', lambda m: t + m.group(1), q)
q = re.sub(r'\b\d+ (disciplines|categories)', lambda m: f'{len(cats)} {m.group(1)}', q)
open('qa/index.html', 'w', encoding='utf-8').write(q)
h = open('index.html', encoding='utf-8').read()
h = h.replace('3,570 expert answers', f'{t} expert answers')
open('index.html', 'w', encoding='utf-8').write(h)
print('total', tot, 'categories', len(cats))
