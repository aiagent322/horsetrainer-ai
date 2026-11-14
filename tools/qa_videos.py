#!/usr/bin/env python3
"""Persist the Q&A 'Watch:' video blocks, which build_qa.py does NOT generate (a rebuild would erase them).
  python3 tools/qa_videos.py extract   # read blocks out of current qa/*/*/index.html -> data/qa_videos.json
  python3 tools/qa_videos.py inject    # after build_qa.py: put blocks (+ CSS + click-to-play script) back. Idempotent.
Run order after a rebuild: build_qa.py -> qa_videos.py inject -> dedupe_canonicals.py -> fix_meta_lengths.py -> build_sitemaps.py"""
import re, glob, json, os, sys
DB = 'data/qa_videos.json'
BLOCK = re.compile(r'[ \t]*<div class="qa-vid-wrap">.*?(?=\n\s*<section class="related-section">)', re.S)
SCRIPT = re.compile(r'<script>\ndocument\.querySelectorAll\(\'\.qa-vid-facade\'\).*?</script>\n?', re.S)
CSS = re.compile(r'\.qa-vid-wrap\{.*?\.qa-vid-ch\{[^}]*\}\n', re.S)
def key(p): return '/'.join(p.split('/')[1:3])
def extract():
    db = {}; meta = {}
    for p in sorted(glob.glob('qa/*/*/index.html')):
        s = open(p, encoding='utf-8').read(); b = BLOCK.search(s)
        if not b: continue
        db[key(p)] = b.group(0).rstrip()
        if 'css' not in meta:
            c, j = CSS.search(s), SCRIPT.search(s)
            if c and j: meta = {'css': c.group(0), 'script': j.group(0).rstrip('\n')}
    os.makedirs('data', exist_ok=True)
    json.dump({'meta': meta, 'blocks': db}, open(DB, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('extracted', len(db), 'blocks')
def inject():
    d = json.load(open(DB, encoding='utf-8')); meta = d['meta']; n = 0
    for p in sorted(glob.glob('qa/*/*/index.html')):
        b = d['blocks'].get(key(p))
        if not b: continue
        s = o = open(p, encoding='utf-8').read()
        if '<div class="qa-vid-wrap">' not in s and '<section class="related-section">' in s:
            s = s.replace('<section class="related-section">', b + '\n\n<section class="related-section">', 1)
        if '.qa-vid-wrap{' not in s: s = s.replace('</style>', meta['css'] + '</style>', 1)
        if "querySelectorAll('.qa-vid-facade')" not in s: s = s.replace('\n</body>', '\n' + meta['script'] + '\n</body>', 1)
        if s != o: open(p, 'w', encoding='utf-8').write(s); n += 1
    print('injected into', n, 'pages')
{'extract': extract, 'inject': inject}[sys.argv[1]]()
