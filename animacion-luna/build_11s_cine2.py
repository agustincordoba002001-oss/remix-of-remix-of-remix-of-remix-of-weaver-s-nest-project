"""11-S — prueba de 30 s con edicion profesional (v2).

Mezcla clips con movimiento real + fotos fijas, cortes rapidos, cinematica
letterbox, titulos cineticos (Anton), chips de hora, grano/viñeta y
subtitulo palabra por palabra.
"""
import json
import math
import os
import random
import subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
REF = '/mnt/documents/ref_cine_11s/'
CLIPS = '/tmp/f11s/'
AUDIO = '/mnt/documents/11s/narracion_completa.mp3'
MARKS = '/mnt/documents/11s/marcas_completas.json'
OUT = os.environ.get('OUT', '/mnt/documents/11s/prueba_cine_v2_30s.mp4')
DUR = 30.5

FONTS = '/dev-server/public/fonts/'
F_DISPLAY = FONTS + 'Anton.ttf'
F_STRONG = FONTS + 'Oswald-Bold.ttf'
F_UI = FONTS + 'Inter-SemiBold.ttf'

AMBER = (255, 186, 66)
WHITE = (245, 246, 248)
BAR = 92  # letterbox

f_sub = ImageFont.truetype(F_STRONG, 54)
f_tag = ImageFont.truetype(F_UI, 23)
f_chip = ImageFont.truetype(F_STRONG, 34)
f_chip2 = ImageFont.truetype(F_UI, 20)

# ------------------------------------------------------------------ material
# (tipo, fuente, t0, t1, movimiento, velocidad)
SHOTS = [
    ('clip', 'v1', 0.0, 4.8, 'in', 0.72),
    ('clip', 'v2', 4.6, 8.4, 'left', 0.8),
    ('foto', 'c1-skyline.jpg', 8.2, 11.2, 'up', 1),
    ('clip', 'v6', 11.0, 14.8, 'in', 0.75),
    ('clip', 'v3', 14.6, 18.4, 'right', 0.8),
    ('foto', 'c4-multitud.jpg', 18.2, 20.8, 'in', 1),
    ('clip', 'v5', 20.6, 24.6, 'right', 0.75),
    ('foto', 'c5-boeing.jpg', 24.4, 27.2, 'in', 1),
    ('clip', 'v4', 27.0, 30.5, 'in', 0.8),
]

# palabras-golpe: (t0, t1, texto, bajada)
HITS = [
    (24.6, 27.0, '19 HOMBRES', 'CUATRO AVIONES'),
]

# chips de hora: (t0, t1, hora, lugar)
CHIPS = [
    (5.0, 8.2, '07:59', 'BOSTON · LOGAN'),
    (15.0, 18.2, '08:14', 'TORRE DE CONTROL'),
    (21.0, 24.4, '08:19', 'VUELO AA 11'),
]

TITULO = (0.5, 4.2, '11 · 09 · 2001', 'MINUTO A MINUTO')

fotos = {}
for _, s, *_ in SHOTS:
    if s.endswith('.jpg') and s not in fotos:
        im = Image.open(REF + s).convert('RGB')
        r = max(2304 / im.width, 1296 / im.height)
        fotos[s] = im.resize((int(im.width * r), int(im.height * r)), Image.Resampling.LANCZOS)

nclip = {d: len(os.listdir(CLIPS + d)) for d in os.listdir(CLIPS)}

# capas fijas
vig = Image.new('L', (W, H), 0)
ImageDraw.Draw(vig).ellipse((-W * 0.30, -H * 0.40, W * 1.30, H * 1.40), fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(180))
sombra_inf = Image.new('L', (W, H), 0)
dsi = ImageDraw.Draw(sombra_inf)
for i in range(360):
    dsi.line([(0, H - i), (W, H - i)], fill=int(210 * (i / 360) ** 1.5))
negro = Image.new('RGB', (W, H), (6, 9, 14))
blanco = Image.new('RGB', (W, H), (255, 255, 255))

GRANOS = []
rnd = random.Random(11)
for _ in range(9):
    g = Image.new('L', (W // 4, H // 4))
    g.putdata([rnd.randint(112, 143) for _ in range(g.width * g.height)])
    GRANOS.append(g.resize((W, H), Image.Resampling.BILINEAR))


def fuente_frame(tipo, s, k, vel):
    if tipo == 'foto':
        return fotos[s]
    n = nclip[s]
    idx = int(k * (n - 1) * min(1.0, vel))
    return Image.open(f'{CLIPS}{s}/{idx + 1:04d}.jpg').convert('RGB')


def encuadre(tipo, s, k, modo, vel, t):
    im = fuente_frame(tipo, s, k, vel)
    z = 1.14 - 0.10 * k if modo == 'in' else 1.09
    cw, ch = min(int(W * z), im.width), min(int(H * z), im.height)
    maxx, maxy = im.width - cw, im.height - ch
    cx, cy = maxx / 2, maxy / 2
    if modo == 'left':
        cx = maxx * (0.80 - 0.60 * k)
    elif modo == 'right':
        cx = maxx * (0.20 + 0.60 * k)
    elif modo == 'up':
        cy = maxy * (0.85 - 0.60 * k)
    # micro temblor de camara
    cx += math.sin(t * 2.3) * 5
    cy += math.cos(t * 1.7) * 4
    cx = max(0, min(maxx, cx))
    cy = max(0, min(maxy, cy))
    caja = (int(cx), int(cy), int(cx) + cw, int(cy) + ch)
    return im.crop(caja).resize((W, H), Image.Resampling.BILINEAR)


# ------------------------------------------------------------------ subtitulo
marcas = [m for m in json.load(open(MARKS)) if m['t0'] < DUR]
frases = []
for m in marcas:
    pal = m['txt'].replace('—', '-').split()
    total = sum(len(p) + 1 for p in pal)
    t, tramos = m['t0'], []
    for p in pal:
        d = (m['t1'] - m['t0']) * (len(p) + 1) / total
        tramos.append((p, t, t + d))
        t += d
    frases.append({'t0': m['t0'], 't1': m['t1'], 'pal': tramos})

tmpd = ImageDraw.Draw(Image.new('RGB', (10, 10)))


def lineas_sub(pal, i):
    ini = max(0, i - 4)
    trozo = pal[ini:ini + 9]
    lin, cur = [], []
    for idx, (p, _, _) in enumerate(trozo):
        prueba = cur + [(p, ini + idx)]
        if tmpd.textlength(' '.join(x[0] for x in prueba).upper(), font=f_sub) > 1360 and cur:
            lin.append(cur)
            cur = [(p, ini + idx)]
        else:
            cur = prueba
    if cur:
        lin.append(cur)
    return lin[:2]


def dibujar_sub(base, t):
    fr = next((f for f in frases if f['t0'] - 0.15 <= t <= f['t1'] + 0.25), None)
    if not fr:
        return
    act = 0
    for k, (_, a, b) in enumerate(fr['pal']):
        if t >= a:
            act = k
    lin = lineas_sub(fr['pal'], act)
    d = ImageDraw.Draw(base)
    y = H - BAR - 78 - (len(lin) - 1) * 68
    for fila in lin:
        texto = ' '.join(p.upper() for p, _ in fila)
        x = (W - d.textlength(texto, font=f_sub)) / 2
        for p, idx in fila:
            s = p.upper()
            activo = idx == act
            col = AMBER if activo else WHITE
            dy = -3 if activo else 0
            d.text((x + 2, y + 3 + dy), s, font=f_sub, fill=(0, 0, 0))
            d.text((x, y + dy), s, font=f_sub, fill=col)
            x += d.textlength(s + ' ', font=f_sub)
        y += 68


def ease(k):
    return 1 - (1 - k) ** 3


def dibujar_titulo(base, t):
    t0, t1, txt, sub = TITULO
    if not (t0 <= t <= t1):
        return
    k = (t - t0) / (t1 - t0)
    ent = ease(min(1, (t - t0) / 0.7))
    sal = min(1, (t1 - t) / 0.5)
    a = min(ent, sal)
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    f = ImageFont.truetype(F_DISPLAY, 168)
    anc = d.textlength(txt, font=f)
    x = 150
    y = H * 0.36 + (1 - ent) * 60
    # barra que se abre
    d.rectangle([x, y - 34, x + 620 * ent, y - 22], fill=(*AMBER, int(255 * a)))
    d.text((x + 5, y + 7), txt, font=f, fill=(0, 0, 0, int(150 * a)))
    d.text((x, y), txt, font=f, fill=(255, 255, 255, int(255 * a)))
    f2 = ImageFont.truetype(F_UI, 34)
    corte = int(len(sub) * min(1, max(0, (k - 0.18) * 3.2)))
    d.text((x + 4, y + 226), sub[:corte], font=f2, fill=(220, 224, 230, int(235 * a)))
    base.paste(Image.alpha_composite(base.convert('RGBA'), capa).convert('RGB'), (0, 0))


def dibujar_hit(base, t):
    for t0, t1, txt, sub in HITS:
        if not (t0 <= t <= t1):
            continue
        k = (t - t0) / (t1 - t0)
        a = min(1.0, min(k * 5, (1 - k) * 5))
        capa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(capa)
        esc = 1.0 + 0.04 * (1 - ease(min(1, k * 3)))
        f = ImageFont.truetype(F_DISPLAY, int(172 * esc))
        anc = d.textlength(txt, font=f)
        x, y = (W - anc) / 2, H * 0.32
        d.text((x + 6, y + 8), txt, font=f, fill=(0, 0, 0, int(150 * a)))
        d.text((x, y), txt, font=f, fill=(255, 255, 255, int(255 * a)))
        d.rectangle([x, y + 214, x + anc * min(1, k * 2.4), y + 224],
                    fill=(*AMBER, int(255 * a)))
        f2 = ImageFont.truetype(F_UI, 36)
        a2 = d.textlength(sub, font=f2)
        d.text(((W - a2) / 2, y + 250), sub, font=f2, fill=(225, 228, 233, int(235 * a)))
        base.paste(Image.alpha_composite(base.convert('RGBA'), capa).convert('RGB'), (0, 0))


def dibujar_chip(base, t):
    for t0, t1, hora, lugar in CHIPS:
        if not (t0 <= t <= t1):
            continue
        ent = ease(min(1, (t - t0) / 0.4))
        a = min(ent, min(1, (t1 - t) / 0.3))
        capa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(capa)
        x = 96
        y = H - BAR - 250
        anc = max(d.textlength(hora, font=f_chip), d.textlength(lugar, font=f_chip2)) + 46
        anc *= ent
        d.rectangle([x, y, x + anc, y + 96], fill=(10, 13, 18, int(180 * a)))
        d.rectangle([x, y, x + 6, y + 96], fill=(*AMBER, int(255 * a)))
        if ent > 0.6:
            d.text((x + 26, y + 12), hora, font=f_chip, fill=(255, 255, 255, int(255 * a)))
            d.text((x + 26, y + 58), lugar, font=f_chip2, fill=(198, 202, 208, int(240 * a)))
        base.paste(Image.alpha_composite(base.convert('RGBA'), capa).convert('RGB'), (0, 0))


N = int(DUR * FPS)
cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
       '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
       '-i', AUDIO, '-t', str(DUR),
       '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
       '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

cortes = [s[2] for s in SHOTS[1:]]

for n in range(N):
    t = n / FPS
    activos = [s for s in SHOTS if s[2] <= t < s[3]] or [SHOTS[-1]]
    tipo, s, t0, t1, modo, vel = activos[0]
    frame = encuadre(tipo, s, (t - t0) / (t1 - t0), modo, vel, t)
    if len(activos) > 1:
        tp2, s2, a0, a1, m2, v2 = activos[1]
        mez = min(1.0, (t - a0) / 0.28)
        frame = Image.blend(frame, encuadre(tp2, s2, (t - a0) / (a1 - a0), m2, v2, t), mez)

    # grade
    frame = Image.blend(frame, negro, 0.15)
    frame = Image.composite(frame, Image.blend(frame, negro, 0.58), vig)
    frame.paste(Image.blend(frame, negro, 0.72), (0, 0), sombra_inf)
    frame = Image.blend(frame, Image.merge('RGB', (GRANOS[n % 9],) * 3), 0.05)

    for c in cortes:
        if 0 <= t - c < 0.14:
            frame = Image.blend(frame, blanco, 0.16 * (1 - (t - c) / 0.14))

    dibujar_titulo(frame, t)
    dibujar_hit(frame, t)
    dibujar_chip(frame, t)
    dibujar_sub(frame, t)

    d = ImageDraw.Draw(frame)
    # letterbox cinematografico
    ab = BAR * ease(min(1, t / 0.8))
    d.rectangle([0, 0, W, ab], fill=(0, 0, 0))
    d.rectangle([0, H - ab, W, H], fill=(0, 0, 0))
    if t > 0.9:
        d.text((96, BAR / 2 - 13), '11 DE SEPTIEMBRE  ·  MINUTO A MINUTO',
               font=f_tag, fill=(196, 200, 206))
        d.rectangle([96, H - BAR / 2 - 2, 96 + 380 * min(1, t / DUR), H - BAR / 2 + 2],
                    fill=AMBER)
        d.rectangle([96, H - BAR / 2 - 2, 96 + 380, H - BAR / 2 + 2],
                    outline=(70, 74, 80))

    p.stdin.write(frame.tobytes())

p.stdin.close()
p.wait()
print('listo', OUT)
