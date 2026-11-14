#!/usr/bin/env python3
"""Bring <title> and meta descriptions inside Google's display guidelines (title <= ~60, description ~120-160) by REMOVAL only
(or by quoting the page's own question titles). Never rewrites meaning. Idempotent. Run from repo root, after build_qa.py."""
import re, glob, html
def trim(d, lim=160):
    if len(d) <= lim: return d
    cut = d[:lim]
    ends = [m.end() for m in re.finditer(r'[.!?](?=\s|$)', cut)]
    if ends and ends[-1] >= 90: return cut[:ends[-1]].strip()
    for sep in (' — ', '; ', ', '):
        i = cut.rfind(sep)
        if i >= 90: return cut[:i].rstrip(' ,;—') + '.'
    return cut[:cut.rfind(' ', 0, lim - 1)].rstrip(' ,;—.') + '…'
nt = nd = 0
for p in glob.glob('**/*.html', recursive=True):
    if p.startswith('.git') or p.split('/')[-1].startswith('google'): continue
    s = o = open(p, encoding='utf-8').read()
    if 'noindex' in s[:3000]: continue
    t = re.search(r'<title([^>]*)>(.*?)</title>', s, re.S)
    if t:
        cur = html.unescape(t.group(2)).strip()
        if len(cur) > 60:
            new = re.sub(r'\s*\|\s*HorseTrainer\.(?:ai|AI)$', '', cur)
            if new != cur and p != 'index.html':
                s = s.replace(t.group(0), f'<title{t.group(1)}>{html.escape(new, quote=False)}</title>', 1); nt += 1
    d = re.search(r'<meta name="description"([^>]*)content="([^"]*)"', s)
    if d:
        cur = html.unescape(d.group(2)); new = cur
        if len(cur) > 160: new = trim(cur)
        elif len(cur) < 120 and re.fullmatch(r'Expert answers to \d+ horse training questions about .*? Learn from professional trainers\.', cur) and re.fullmatch(r'qa/[^/]+/index\.html', p):
            qs = [html.unescape(x).strip() for x in re.findall(r'<h2><a href="[^"]+">(.*?)</a></h2>', s)]
            base = cur.replace(' Learn from professional trainers.', '')
            base = base[:-1] if base.endswith('.') else base
            out = base
            for k in range(min(3, len(qs)), 0, -1):
                inc = ' and '.join(f'“{q}”' for q in qs[:k]) if k < 3 else f'“{qs[0]}”, “{qs[1]}” and “{qs[2]}”'
                cand = f'{base}, including {inc}'
                if 120 <= len(cand) <= 160: out = cand; break
            new = out + ('' if out.endswith(('.', '…')) else '.') if out != base else cur
        if new != cur:
            e = lambda x: html.escape(x, quote=True)
            s = s.replace(d.group(2), e(new)).replace(f'og:description" content="{d.group(2)}"', f'og:description" content="{e(new)}"')
            nd += 1
    if s != o: open(p, 'w', encoding='utf-8').write(s)
print('titles', nt, 'descriptions', nd)
