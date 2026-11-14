#!/usr/bin/env python3
"""Famous-trainer pages: add intrinsic width/height to local <img>, lazy-load below-the-fold photos (not the hero), and
keep inline photos' height:auto so the new attributes cannot distort them. YouTube hqdefault thumbs get 480x360. Idempotent."""
import re, glob, os
from PIL import Image
n = 0
for p in sorted(glob.glob('famous-trainers/*.html')):
    s = open(p, encoding='utf-8').read(); o = s
    def fix(m):
        t = m.group(0)
        src = re.search(r'src="([^"]+)"', t)
        if not src: return t
        src = src.group(1); hero = 'hero-photo' in s[max(0, m.start() - 400):m.start()]
        if src.startswith('/famous-trainers/images/') and os.path.exists(src[1:]):
            if not re.search(r'\bwidth=', t):
                w, h = Image.open(src[1:]).size
                t = t.replace('<img', f'<img width="{w}" height="{h}"', 1)
            if not hero:
                if 'loading=' not in t: t = t.replace('<img', '<img loading="lazy" decoding="async"', 1)
                if 'style="' in t:
                    if 'height:auto' not in t: t = t.replace('style="', 'style="height:auto;', 1)
                else: t = t.replace('<img', '<img style="height:auto"', 1)
        elif 'i.ytimg.com/vi/' in src and 'hqdefault' in src and not re.search(r'\bwidth=', t):
            t = t.replace('<img', '<img width="480" height="360"', 1)
        return t
    s = re.sub(r'<img\b[^>]*>', fix, s)
    if s != o: open(p, 'w', encoding='utf-8').write(s); n += 1
print('updated', n)
