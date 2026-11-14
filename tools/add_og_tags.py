#!/usr/bin/env python3
"""Add/refresh og:image + twitter:card tags on every HTML page. Idempotent. Run from repo root."""
import os, re, html, glob
BASE = 'https://horsetrainer.ai'
SECTIONS = {'groundwork','reining','colt-starting','barrel-racing','problem-horse','dressage','mustang','trail','tack','videos'}
have = lambda n: os.path.exists(f'images/og/{n}.jpg')
def pick(rel):
    parts = rel.replace('\\', '/').split('/')
    if parts == ['index.html']: return 'og-home'
    top = parts[0]
    if top == 'qa':
        if len(parts) >= 3 and have(f'og-qa-{parts[1]}'): return f'og-qa-{parts[1]}'
        return 'og-qa'
    if top == 'famous-trainers':
        if parts[-1] == 'index.html' and len(parts) == 2: return 'og-famous-trainers'
        slug = parts[1][:-5] if parts[1].endswith('.html') else parts[1]
        return f'og-famous-{slug}' if have(f'og-famous-{slug}') else 'og-famous-trainers'
    if top in SECTIONS: return f'og-{top}'
    if top == 'find-a-trainer': return 'og-find-a-trainer'
    if top == 'training' or rel == 'training-guide.html': return 'og-training'
    return 'og-default'
STRIP = re.compile(r'[ \t]*<meta\s+(?:property="og:image[^"]*"|name="twitter:(?:image|card)")[^>]*>\n?')
n = 0
for p in glob.glob('**/*.html', recursive=True):
    if p.startswith(('.git/', 'node_modules/')) or os.path.basename(p).startswith('google'): continue
    s = open(p, encoding='utf-8').read()
    if '</head>' not in s: continue
    t = re.search(r'<meta property="og:title" content="([^"]*)"', s) or re.search(r'<title>(.*?)</title>', s, re.S)
    alt = html.escape(html.unescape(t.group(1)).strip(), quote=True) if t else 'HorseTrainer.ai'
    img = f'{BASE}/images/og/{pick(p)}.jpg?v=1'
    block = (f'<meta property="og:image" content="{img}">\n<meta property="og:image:width" content="1200">\n'
             f'<meta property="og:image:height" content="630">\n<meta property="og:image:alt" content="{alt}">\n'
             f'<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:image" content="{img}">\n')
    new = STRIP.sub('', s).replace('</head>', block + '</head>', 1)
    if new != s: open(p, 'w', encoding='utf-8').write(new); n += 1
print('updated', n)
