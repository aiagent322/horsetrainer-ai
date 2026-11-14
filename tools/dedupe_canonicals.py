#!/usr/bin/env python3
"""Same question+identical answer in several Q&A categories -> canonical/og:url of every copy points at ONE primary copy
(the category with the fewest answers = most specific; ties alphabetical). Copies stay live and linked. Run after build_qa.py, then build_sitemaps.py."""
import re, glob, os, collections, hashlib
BASE = 'https://horsetrainer.ai'
size = collections.Counter(p.split('/')[1] for p in glob.glob('qa/*/*/index.html'))
by = collections.defaultdict(list)
for p in glob.glob('qa/*/*/index.html'):
    s = open(p, encoding='utf-8').read()
    a = re.search(r'"acceptedAnswer": \{"@type": "Answer", "text": "(.*?)"\}', s)
    by[(p.split('/')[2], hashlib.md5((a.group(1) if a else p).encode()).hexdigest())].append(p)
n = 0
for (slug, _), ps in by.items():
    prim = min(ps, key=lambda p: (size[p.split('/')[1]], p.split('/')[1])) if len(ps) > 1 else ps[0]
    url = f'{BASE}/qa/{prim.split("/")[1]}/{slug}/'
    for p in ps:
        s = open(p, encoding='utf-8').read()
        new = re.sub(r'(<link rel="canonical" href=")[^"]*(")', r'\g<1>' + url + r'\2', s, 1)
        new = re.sub(r'(<meta property="og:url" content=")[^"]*(")', r'\g<1>' + url + r'\2', new, 1)
        if new != s: open(p, 'w', encoding='utf-8').write(new); n += 1
print('canonicals changed on', n, 'pages')
