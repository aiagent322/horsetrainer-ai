#!/usr/bin/env python3
"""Rebuild sitemap.xml (site pages) and qa/sitemap.xml (Q&A pages) from the files actually in the repo.
URL = the page's own <link rel="canonical"> (falls back to the file path). Skips noindex pages,
the Google verification file and the trainer-profile template stubs. Existing <lastmod> values in
sitemap.xml are kept; new URLs get today's date. Run from the repo root: python3 tools/build_sitemaps.py"""
import os, re, sys, datetime
HOST = 'https://horsetrainer.ai'
SKIP_PREFIX = ('trainers/template/', 'trainers/wade-callahan/')   # retired-directory stubs, not indexable content
today = datetime.date.today().isoformat()

def url_for(path, text):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', text)
    if m and m.group(1).startswith(HOST + '/'):
        return m.group(1)
    if path == 'index.html': return HOST + '/'
    if path.endswith('/index.html'): return HOST + '/' + path[:-len('index.html')]
    return HOST + '/' + path[:-len('.html')]

site, qa = {}, {}
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules')]
    for f in files:
        if not f.endswith('.html') or f.startswith('google'): continue
        p = os.path.join(root, f)[2:]
        if p.startswith(SKIP_PREFIX): continue
        t = open(p, encoding='utf-8', errors='ignore').read()
        if re.search(r'<meta[^>]+name="robots"[^>]+noindex', t, re.I): continue
        (qa if p.startswith('qa/') else site)[url_for(p, t)] = p

old = open('sitemap.xml', encoding='utf-8').read() if os.path.exists('sitemap.xml') else ''
lastmod = dict(re.findall(r'<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>', old))

def key(u): return (u != HOST + '/', u)
out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in sorted(site, key=key):
    out.append(f'  <url>\n    <loc>{u}</loc>\n    <lastmod>{lastmod.get(u, today)}</lastmod>\n    <changefreq>weekly</changefreq>\n  </url>')
out.append('</urlset>')
open('sitemap.xml', 'w', encoding='utf-8').write('\n'.join(out) + '\n')

out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in sorted(qa, key=lambda u: (u != HOST + '/qa/', u)):
    out.append(f'  <url><loc>{u}</loc></url>')
out.append('</urlset>')
open('qa/sitemap.xml', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(f'sitemap.xml: {len(site)} URLs; qa/sitemap.xml: {len(qa)} URLs')
