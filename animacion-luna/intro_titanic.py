"""Nuevo comienzo del video del Titanic (primeros ~23 segundos).

Estilo: dibujo a tinta y acuarela bien colorido sobre papel claro, entrando con
rebote y balanceo suave; los títulos aparecen palabra por palabra con rebote,
subrayado rojo que barre y una palabra en rojo por frase.

Uso:  START=0 END=23.1 OUT=/tmp/intro.mp4 python3 intro_titanic.py
"""
import math
import os
import random
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
AUDIO = os.environ.get('AUDIO', '/mnt/documents/titanic_editado.mp4')
OUT = os.environ.get('OUT', '/tmp/intro.mp4')
REF = '/mnt/documents/intro_tt/'
FONT = '/tmp/Anton-Regular.ttf'

INK = (24, 24, 26)
RED = (206, 38, 38)
PAPER = (250, 246, 238)
GREY = (92, 92, 96)

# frase: t0, t1, imagen, líneas del título (palabra roja marcada con *), bajada
ESCENAS = [
    dict(t0=0.60, t1=5.41, im='e1.png',
         lines=[['2', 'HORAS'], ['Y', '*40', '*MINUTOS']],
         sub='y el barco ya no estaba'),
    dict(t0=6.07, t1=9.99, im='e2.png',
         lines=[['*1500'], ['MUERTOS']],
         sub='y casi nadie por el choque'),
    dict(t0=10.65, t1=16.26, im='e3.png',
         lines=[['MURIERON', 'POR'], ['*DECISIONES']],
         sub='tomadas en una oficina'),
    dict(t0=16.93, t1=23.10, im='e4.png',
         lines=[['TITANIC'], ['LA', 'HISTORIA'], ['*COMPLETA']],
         sub='la historia completa'),
]

START = float(os.environ.get('START', 0))
END = float(os.environ.get('END', ESCENAS[-1]['t1']))

_F = {}


def font(sz, path=FONT):
    if (path, sz) not in _F:
        _F[(path, sz)] = ImageFont.truetype(path, sz)
    return _F[(path, sz)]


SUB_FONT = subprocess.run(['fc-match', '-f', '%{file}', 'DejaVu Sans:italic'],
                          capture_output=True, text=True, check=True).stdout


def papel():
    """Hoja clara con grano y una mancha de acuarela muy suave."""
    base = Image.new('RGB', (W, H), PAPER)
    rnd = random.Random(7)
    grano = Image.new('L', (W // 3, H // 3))
    grano.putdata([rnd.randint(238, 255) for _ in range((W // 3) * (H // 3))])
    grano = grano.resize((W, H), Image.Resampling.BILINEAR)
    base = Image.composite(base, Image.new('RGB', (W, H), (236, 231, 221)),
                           grano.point(lambda v: 255 if v > 247 else 0))
    wash = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(wash)
    d.ellipse((820, -260, 2200, 900), fill=(233, 240, 244))
    d.ellipse((-200, 620, 900, 1400), fill=(247, 240, 230))
    wash = wash.filter(ImageFilter.GaussianBlur(140))
    return Image.blend(base, wash, 0.55)


FONDO = papel()

_IM = {}


def dibujo(name, maxw, maxh):
    ck = (name, maxw, maxh)
    if ck in _IM:
        return _IM[ck]
    im = Image.open(REF + name).convert('RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    im.thumbnail((maxw, maxh), Image.Resampling.LANCZOS)
    _IM[ck] = im
    return im


def rebote(p):
    """0 -> 1 con un pequeño sobrepaso (entrada viva)."""
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    return 1 - math.exp(-7 * p) * math.cos(9 * p)


def suave(p):
    p = max(0.0, min(1.0, p))
    return p * p * (3 - 2 * p)


def medir(word, f):
    b = font(f).getbbox(word)
    return b[2] - b[0], b[3] - b[1]


def armar(esc):
    """Posiciona palabras del título en la mitad izquierda y calcula tiempos."""
    dur = esc['t1'] - esc['t0']
    size = 150 if max(len(' '.join(l)) for l in esc['lines']) <= 10 else 118
    if len(esc['lines']) >= 3:
        size = min(size, 122)
    maxw = 830
    while True:
        anchos = [medir(' '.join(w.lstrip('*') for w in l), size)[0]
                  for l in esc['lines']]
        if max(anchos) <= maxw or size <= 70:
            break
        size -= 6
    lh = int(size * 1.02)
    total = lh * len(esc['lines'])
    y0 = (H - total) // 2 - 40
    palabras, orden = [], 0
    for li, line in enumerate(esc['lines']):
        limpio = [w.lstrip('*') for w in line]
        espacio = medir(' ', size)[0]
        anchos = [medir(w, size)[0] for w in limpio]
        x = 130
        for w, raw, aw in zip(limpio, line, anchos):
            palabras.append(dict(txt=w, x=x, y=y0 + li * lh, size=size,
                                 color=RED if raw.startswith('*') else INK,
                                 i=orden))
            orden += 1
            x += aw + espacio
        palabras[-1]['ancho_linea'] = x - espacio - 130
    paso = min(0.17, dur * 0.4 / max(1, orden))
    for p in palabras:
        p['t'] = esc['t0'] + 0.10 + p['i'] * paso
    fin_txt = palabras[-1]['t'] + 0.35
    return palabras, y0 + total, fin_txt, size


PRE = []
for esc in ESCENAS:
    palabras, ybase, fin_txt, size = armar(esc)
    im = dibujo(esc['im'], 900, 830)
    PRE.append(dict(esc=esc, palabras=palabras, ybase=ybase, fin=fin_txt,
                    im=im, size=size,
                    ancho=max(p.get('ancho_linea', 0) for p in palabras)))

DUR = END - START
cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
       '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
       '-i', '-', '-ss', str(START), '-t', str(DUR), '-i', AUDIO,
       '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium',
       '-crf', '19', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.1',
       '-c:a', 'aac', '-b:a', '168k', '-ar', '48000', '-ac', '2',
       '-movflags', '+faststart', '-shortest', OUT]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
assert proc.stdin is not None

for frame in range(int(START * FPS), int(END * FPS)):
    t = frame / FPS
    idx = 0
    for i, p in enumerate(PRE):
        if t >= p['esc']['t0'] - 0.25:
            idx = i
    cur = PRE[idx]
    esc = cur['esc']
    canvas = FONDO.copy()
    local = t - esc['t0']

    # ---- dibujo (derecha): entra con rebote y después se balancea ----
    im = cur['im']
    ent = rebote(local / 0.75)
    if ent > 0.001:
        vaiven = math.sin((local + idx) * 1.1)
        esc_f = (0.80 + 0.20 * ent) * (1 + 0.012 * vaiven)
        ang = (1 - ent) * -7 + 1.4 * math.sin((local + idx) * 0.9)
        sw, sh = max(2, int(im.width * esc_f)), max(2, int(im.height * esc_f))
        art = im.resize((sw, sh), Image.Resampling.LANCZOS).rotate(
            ang, expand=True, resample=Image.Resampling.BICUBIC)
        cx = 1440 + int(14 * math.sin((local + idx) * 0.7))
        cy = 540 + int(16 * math.sin((local + idx) * 1.3 + 1)) - int((1 - ent) * 30)
        sombra = Image.new('RGBA', art.size, (0, 0, 0, 0))
        sombra.paste((40, 44, 50, 70), (0, 0), art)
        sombra = sombra.filter(ImageFilter.GaussianBlur(18))
        canvas.paste(sombra, (cx - art.width // 2 + 12, cy - art.height // 2 + 16), sombra)
        art_a = art.copy()
        art_a.putalpha(art.getchannel('A').point(lambda v: int(v * min(1, ent * 1.3))))
        canvas.paste(art_a, (cx - art.width // 2, cy - art.height // 2), art_a)

    d = ImageDraw.Draw(canvas)

    # ---- título (izquierda): palabra por palabra con rebote ----
    for p in cur['palabras']:
        pr = (t - p['t']) / 0.42
        if pr <= 0:
            continue
        e = rebote(pr)
        f = font(p['size'])
        sub = Image.new('RGBA', (medir(p['txt'], p['size'])[0] + 30,
                                 int(p['size'] * 1.6)), (0, 0, 0, 0))
        ImageDraw.Draw(sub).text((14, 6), p['txt'], font=f, fill=p['color'] + (255,))
        k = 0.7 + 0.3 * e
        sw, sh = max(2, int(sub.width * k)), max(2, int(sub.height * k))
        sub2 = sub.resize((sw, sh), Image.Resampling.LANCZOS)
        if e < 0.999:
            sub2 = sub2.rotate((1 - e) * 6, expand=True,
                               resample=Image.Resampling.BICUBIC)
            a = sub2.getchannel('A').point(lambda v: int(v * min(1, pr * 2)))
            sub2.putalpha(a)
        px = p['x'] - 14 - (sub2.width - sub.width) // 2
        py = p['y'] - 6 - (sub2.height - sub.height) // 2 + int((1 - e) * 26)
        canvas.paste(sub2, (px, py), sub2)

    # ---- subrayado rojo que barre y bajada ----
    barrido = suave((t - cur['fin']) / 0.5)
    if barrido > 0:
        y = cur['ybase'] + 18
        d.rounded_rectangle((130, y, 130 + int(cur['ancho'] * barrido), y + 12),
                            radius=6, fill=RED)
        if barrido > 0.55:
            sf = ImageFont.truetype(SUB_FONT, 44)
            op = suave((barrido - 0.55) / 0.45)
            tmp = Image.new('RGBA', (900, 90), (0, 0, 0, 0))
            ImageDraw.Draw(tmp).text((0, 0), esc['sub'], font=sf,
                                     fill=GREY + (int(255 * op),))
            canvas.paste(tmp, (132, y + 34 - int(12 * (1 - op))), tmp)

    proc.stdin.write(canvas.tobytes())

proc.stdin.close()
if proc.wait():
    raise SystemExit(1)
print(OUT)
