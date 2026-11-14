#!/usr/bin/env python3
"""Generate 1200x630 social-share (Open Graph / Twitter) images into images/og/.
Text-only branded cards (no photos). Run from the repo root: python3 tools/build_og_images.py
Naming: og-default, og-home, og-qa, og-qa-<category>, og-<section>, og-famous-trainers, og-famous-<slug>."""
import os, re, html, glob
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 630
FD = '/usr/share/fonts/truetype/google-fonts/'
def font(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f
BLUE = ((9, 48, 76), (20, 78, 120)); BROWN = ((52, 30, 18), (96, 60, 34))
GOLD = (212, 160, 23); WHITE = (255, 255, 255); SOFT = (214, 226, 236); CREAM = (245, 237, 224)

def gradient(c1, c2):
    img = Image.new('RGB', (W, H)); px = img.load()
    for y in range(H):
        for x in range(W):
            t = (x / W * 0.45 + y / H * 0.55)
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return img

def horseshoe(img, color_alpha):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    cx, cy, r = 925, 335, 205
    d.arc((cx - r, cy - r, cx + r, cy + r), start=125, end=415, fill=color_alpha, width=62)
    for a in range(0, 1):
        pass
    import math
    for ang in (150, 180, 210, 330, 0, 30, 245, 295):
        x = cx + (r) * math.cos(math.radians(ang)); y = cy + (r) * math.sin(math.radians(ang))
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(0, 0, 0, 55))
    return Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')

def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def card(path, title, sub, brown=False, kicker=None):
    bg = BROWN if brown else BLUE
    img = horseshoe(gradient(*bg), (212, 160, 23, 38)); d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 14, H), fill=GOLD)                      # accent bar
    brand = font('Poppins-Bold.ttf', 34); x = 70
    for part, col in (('Horse', WHITE), ('Trainer', GOLD), ('.ai', WHITE)):
        d.text((x, 54), part, font=brand, fill=col); x += d.textlength(part, font=brand)
    if kicker: d.text((70, 140), kicker.upper(), font=font('Poppins-Medium.ttf', 26), fill=GOLD, spacing=4)
    for size in range(92, 51, -4):
        tf = font('Lora-Variable.ttf', size, 700); lines = wrap(d, title, tf, 780)
        if len(lines) <= 2: break
    else:
        size = 52; tf = font('Lora-Variable.ttf', size, 700); lines = wrap(d, title, tf, 780)
    sf = font('Poppins-Regular.ttf', 32); sl = wrap(d, sub, sf, 760)[:(1 if len(lines) >= 3 else 2)]
    lh = int(size * 1.15); block = lh * len(lines[:3]) + 12 + 44 * len(sl)
    y = 190 + max(0, (290 - block) // 2)
    for ln in lines[:3]:
        d.text((70, y), ln, font=tf, fill=WHITE); y += lh
    y += 12
    for ln in sl:
        d.text((70, y), ln, font=sf, fill=CREAM if brown else SOFT); y += 44
    d.rectangle((70, H - 92, 150, H - 88), fill=GOLD)
    d.text((70, H - 70), 'horsetrainer.ai', font=font('Poppins-Medium.ttf', 28), fill=WHITE)
    img.save(path, 'JPEG', quality=86, optimize=True, progressive=True)

OUT = 'images/og'; os.makedirs(OUT, exist_ok=True)
def out(n): return f'{OUT}/{n}.jpg'
n = 0
def make(name, *a, **k):
    global n; card(out(name), *a, **k); n += 1

make('og-default', 'Horse Training, Explained', 'Guides, expert Q&A and trainers from HorseTrainer.ai')
make('og-home', 'Find a Horse Trainer', 'Training guides, 3,500+ expert Q&A answers and trainer profiles', kicker='HorseTrainer.ai')
make('og-qa', 'Horse Training Q&A', 'Expert answers across 60+ disciplines and topics', kicker='Questions & Answers')
make('og-find-a-trainer', 'Find a Horse Trainer', 'Match with trainers by discipline and training need', kicker='Trainer Match')
make('og-training', 'Horse Training Guides', 'Gaits, collection, safety, speed, competition and more', kicker='Training Guides')
make('og-famous-trainers', 'Famous Horse Trainers', 'Biographies of the horsemen and horsewomen who shaped training', brown=True, kicker='Published Biographies')
SECTIONS = {'groundwork': ('Groundwork', 'Lunging, yielding, sacking out, leading and foundation work'),
            'reining': ('Reining', 'Stops, spins, lead changes and NRHA competition'),
            'colt-starting': ('Colt Starting', 'First saddling to the first 60 days under saddle'),
            'barrel-racing': ('Barrel Racing', 'Pattern, rate, fitness and starting a barrel prospect'),
            'problem-horse': ('Problem Horse Solutions', 'Rearing, bolting, bucking, biting and barn sour fixes'),
            'dressage': ('Dressage', 'Training scale, lateral work and first-level movements'),
            'mustang': ('Mustang Training', 'Gentling, halter training and the first 30 days'),
            'trail': ('Trail Horse Training', 'Desensitizing, water crossings and obstacles'),
            'tack': ('Tack & Equipment Guides', 'Saddle fit, bridle fit, bits and protective boots'),
            'videos': ('Horse Training Videos', 'Trainer videos organized by discipline')}
for k, (t, s) in SECTIONS.items(): make(f'og-{k}', t, s, kicker='HorseTrainer.ai Guides')
# Q&A categories
for p in sorted(glob.glob('qa/*/index.html')):
    cat = p.split('/')[1]
    ti = re.search(r'<title>(.*?)</title>', open(p, encoding='utf-8').read(), re.S)
    name = html.unescape(ti.group(1)).split(' — ')[0] if ti else cat.replace('-', ' ').title()
    name = re.sub(r'\s+(Training\s+)?Q&A$', '', name).strip()
    make(f'og-qa-{cat}', name, 'Horse training questions and expert answers', kicker='Training Q&A')
# Famous trainer profiles
idx = open('famous-trainers/index.html', encoding='utf-8').read()
disc = {}
for m in re.finditer(r'<a href="/famous-trainers/([a-z0-9-]+)" class="trainer-card".*?card-discipline">([^<]*)<', idx, re.S): disc[m.group(1)] = html.unescape(m.group(2))
for p in sorted(glob.glob('famous-trainers/*.html')):
    slug = os.path.basename(p)[:-5]
    if slug == 'index': continue
    t = open(p, encoding='utf-8').read()
    hs = re.findall(r'<h1[^>]*>(.*?)</h1>', t, re.S); name = re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', ' '.join(hs)))).strip() if hs else slug.replace('-', ' ').title()
    make(f'og-famous-{slug}', name, (disc.get(slug, 'Horse trainer') + ' · Famous Horse Trainers'), brown=True, kicker='Trainer Biography')
print('generated', n, 'images')
