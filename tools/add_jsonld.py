#!/usr/bin/env python3
"""Add minimal schema.org JSON-LD (from each page's own title/description/canonical) to indexable pages that have none. Idempotent."""
import re, glob, html, json
n = 0
for p in sorted(glob.glob('**/*.html', recursive=True)):
    if p.startswith('.git') or p.split('/')[-1].startswith('google'): continue
    s = open(p, encoding='utf-8').read()
    if 'noindex' in s[:3000] or '</head>' not in s: continue
    if '"@type"' in ' '.join(re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)): continue
    g = lambda pat: html.unescape(re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', m.group(1)))).strip() if (m := re.search(pat, s, re.S)) else ''
    canon = g(r'<link rel="canonical" href="([^"]*)"') or 'https://horsetrainer.ai/' + re.sub(r'(index)?\.html$', '', p)
    desc = g(r'<meta name="description"[^>]*content="([^"]*)"')
    title = g(r'<title[^>]*>(.*?)</title>')
    h1 = ' '.join(html.unescape(re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', x))).strip() for x in re.findall(r'<h1[^>]*>(.*?)</h1>', s, re.S)) or title
    top = p.split('/')[0]; leaf = p.endswith('index.html') is False or p.count('/') >= 2
    d = {'@context': 'https://schema.org'}
    if top == 'famous-trainers' and p != 'famous-trainers/index.html':
        d.update({'@type': 'Article', 'headline': h1, 'about': {'@type': 'Person', 'name': h1}})
    elif top == 'about': d['@type'] = 'AboutPage'; d['name'] = h1
    elif p.count('/') >= 2 and top not in ('trainers',) and p.endswith('index.html') and top in ('reining','groundwork','barrel-racing','trail','tack','mustang','dressage','colt-starting','problem-horse'):
        d.update({'@type': 'Article', 'headline': h1})
    elif p.endswith('index.html') and p.count('/') == 1 or p.endswith('index.html') and p == 'index.html':
        d.update({'@type': 'CollectionPage', 'name': h1})
    else: d.update({'@type': 'WebPage', 'name': h1})
    d['url'] = canon
    if desc: d['description'] = desc
    d['publisher'] = {'@type': 'Organization', 'name': 'HorseTrainer.ai', 'url': 'https://horsetrainer.ai/'}
    block = '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + '</script>\n'
    open(p, 'w', encoding='utf-8').write(s.replace('</head>', block + '</head>', 1)); n += 1
print('added', n)
