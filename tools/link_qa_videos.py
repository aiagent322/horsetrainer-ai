#!/usr/bin/env python3
"""Add an 'About this video' link to every Q&A video block, pointing at that video's own page
(videos/watch/<slug>/, from data/video_slugs.json). Idempotent. Run after build_video_pages.py,
then run tools/qa_videos.py extract so data/qa_videos.json keeps the link for future rebuilds."""
import re, glob, json
slugs = json.load(open('data/video_slugs.json'))
INFO = re.compile(r'(<div class="qa-vid-info">\s*<div class="qa-vid-title">.*?</div>(?:\s*<div class="qa-vid-ch">.*?</div>)?)(\s*</div>)', re.S)
YT = re.compile(r'(<div class="yt-facade" data-vid="([\w-]+)".*?<div class="yt-label">.*?</div>\s*</div>)', re.S)
STYLE = 'margin-top:6px;font-size:.78rem;'
def link(slug, cls): return '<div class="%s" style="%s"><a href="/videos/watch/%s/">About this video ›</a></div>' % (cls, STYLE, slug)
n = 0
for p in sorted(glob.glob('qa/*/*/index.html')):
    s = open(p, encoding='utf-8').read()
    if 'About this video' in s: continue
    m = re.search(r'data-vid="([\w-]+)"', s)
    if not m or m.group(1) not in slugs: continue
    slug = slugs[m.group(1)]
    if 'class="qa-vid-info"' in s:
        s2, k = INFO.subn(lambda x: x.group(1) + link(slug, 'qa-vid-more') + x.group(2), s, count=1)
    else:
        s2, k = YT.subn(lambda x: x.group(1) + '\n' + link(slugs.get(x.group(2), slug), 'yt-more'), s, count=1)
    if k: open(p, 'w', encoding='utf-8').write(s2); n += 1
print('linked', n, 'pages')
