"""11-S — prueba de 30 s con edición cinematográfica dinámica.

Estilo aprendido del canal de referencia:
- imagen fotorrealista a pantalla completa, sin marcos ni fondo blanco
- movimiento constante de cámara (zoom / paneo tipo Ken Burns)
- cortes frecuentes con fundido corto
- grano de película, viñeta y grade oscuro
- subtítulo palabra por palabra, con la palabra hablada resaltada
- palabras-golpe grandes en momentos clave
"""
import json
import math
import os
import subprocess
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
REF = '/mnt/documents/ref_cine_11s/'
AUDIO = '/mnt/documents/11s/narracion_completa.mp3'
MARKS = '/mnt/documents/11s/marcas_completas.json'
OUT = os.environ.get('OUT', '/mnt/documents/11s/prueba_cine_30s.mp4')
DUR = 30.5

FONTS = '/dev-server/public/fonts/'
F_DISPLAY = FONTS + 'Anton.ttf'
F_STRONG = FONTS + 'Oswald-Bold.ttf'
F_UI = FONTS + 'Inter-SemiBold.ttf'

AMBER = (255, 186, 66)
WHITE = (245, 246, 248)

f_sub = ImageFont.truetype(F_STRONG, 58)
f_hit = ImageFont.truetype(F_DISPLAY, 190)
f_tag = ImageFont.truetype(F_UI, 24)

# ---------------------------------------------------------------- material
# (archivo, t0, t1, tipo de movimiento)
SHOTS = [
    ('c1-skyline.jpg', 0.0, 6.6, 'in'),
    ('c2-tren.jpg', 6.4, 12.6, 'left'),
    ('c1-skyline.jpg', 12.4, 17.9, 'up'),
    ('c3-aeropuerto.jpg', 17.7, 22.4, 'in'),
    ('c5-boeing.jpg', 22.2, 25.6, 'right'),
    ('c4-multitud.jpg', 25.4, 28.6, 'in'),
    ('c6-radar.jpg', 28.4, 30.5, 'in'),
]

# palabras-golpe: (t0, t1, texto)
HITS = [
    (0.6, 2.6, '11 · 09 · 2001'),
    (25.6, 28.2, '19 HOMBRES'),
]

src = {}
for name in {s[0] for s in SHOTS}:
    im = Image.open(REF + name).convert('RGB')
    # encuadre 16:9 exacto
    r = max(W * 1.25 / im.width, H * 1.25 / im.height)
    im = im.resize((int(im.width * r), int(im.height * r)), Image.Resampling.LANCZOS)
    src[name] = im

# viñeta + grade (capas fijas)
vig = Image.new('L', (W, H), 0)
ImageDraw.Draw(vig).ellipse((-W * 0.32, -H * 0.42, W * 1.32, H * 1.42), fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(190))
sombra_inf = Image.new('L', (W, H), 0)
dsi = ImageDraw.Draw(sombra_inf)
for i in range(340):
    dsi.line([(0, H - i), (W, H - i)], fill=int(215 * (i / 340) ** 1.5))
negro = Image.new('RGB', (W, H), (6, 9, 14))

GRANOS = []
rnd = random.Random(11)
for _ in range(9):
    g = Image.new('L', (W // 4, H // 4))
    g.putdata([rnd.randint(112, 143) for _ in range(g.width * g.height)])
    GRANOS.append(g.resize((W, H), Image.Resampling.BILINEAR))


def encuadre(name, k, modo):
    """Devuelve el fotograma con movimiento de cámara continuo."""
    im = src[name]
    z = 1.16 - 0.12 * k if modo == 'in' else 1.10
    cw, ch = int(W * z), int(H * z)
    cw = min(cw, im.width)
    ch = min(ch, im.height)
    maxx, maxy = im.width - cw, im.height - ch
    cx, cy = maxx / 2, maxy / 2
    if modo == 'left':
        cx = maxx * (0.78 - 0.56 * k)
    elif modo == 'right':
        cx = maxx * (0.22 + 0.56 * k)
    elif modo == 'up':
        cy = maxy * (0.85 - 0.6 * k)
    caja = (int(cx), int(cy), int(cx) + cw, int(cy) + ch)
    return im.crop(caja).resize((W, H), Image.Resampling.BILINEAR)


# ---------------------------------------------------------------- subtítulo
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


def lineas_sub(pal, i):
    """Ventana de palabras alrededor de la que se está diciendo."""
    ini = max(0, i - 4)
    trozo = pal[ini:ini + 9]
    lin, cur = [], []
    tmp = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    for idx, (p, _, _) in enumerate(trozo):
        prueba = cur + [(p, ini + idx)]
        if tmp.textlength(' '.join(x[0] for x in prueba).upper(), font=f_sub) > 1420 and cur:
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
    y = H - 108 - (len(lin) - 1) * 74
    for fila in lin:
        texto = ' '.join(p.upper() for p, _ in fila)
        x = (W - d.textlength(texto, font=f_sub)) / 2
        for p, idx in fila:
            s = p.upper()
            col = AMBER if idx == act else WHITE
            d.text((x + 2, y + 3), s, font=f_sub, fill=(0, 0, 0))
            d.text((x, y), s, font=f_sub, fill=col)
            x += d.textlength(s + ' ', font=f_sub)
        y += 74


def dibujar_hit(base, t):
    for t0, t1, txt in HITS:
        if not (t0 <= t <= t1):
            continue
        k = (t - t0) / (t1 - t0)
        alpha = min(1.0, min(k, 1 - k) * 6)
        capa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(capa)
        esc = 1.0 + 0.05 * (1 - k)
        f = ImageFont.truetype(F_DISPLAY, int(190 * esc))
        ancho = d.textlength(txt, font=f)
        x, y = (W - ancho) / 2, H * 0.34
        d.text((x + 6, y + 8), txt, font=f, fill=(0, 0, 0, int(150 * alpha)))
        d.text((x, y), txt, font=f, fill=(255, 255, 255, int(255 * alpha)))
        d.rectangle([x, y + 236, x + ancho * min(1, k * 2.2), y + 246],
                    fill=(255, 186, 66, int(255 * alpha)))
        base.alpha_composite(capa) if base.mode == 'RGBA' else base.paste(
            Image.alpha_composite(base.convert('RGBA'), capa).convert('RGB'), (0, 0))


N = int(DUR * FPS)
cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
       '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
       '-i', AUDIO, '-t', str(DUR),
       '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
       '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

for n in range(N):
    t = n / FPS
    activos = [s for s in SHOTS if s[1] <= t < s[2]]
    if not activos:
        activos = [SHOTS[-1]]
    name, t0, t1, modo = activos[0]
    frame = encuadre(name, (t - t0) / (t1 - t0), modo)
    if len(activos) > 1:  # fundido corto entre planos
        n2, a0, a1, m2 = activos[1]
        mez = min(1.0, (t - a0) / 0.35)
        frame = Image.blend(frame, encuadre(n2, (t - a0) / (a1 - a0), m2), mez)

    # grade cinematográfico
    frame = Image.blend(frame, negro, 0.16)
    frame = Image.composite(frame, Image.blend(frame, negro, 0.6), vig)
    frame.paste(Image.blend(frame, negro, 0.75), (0, 0), sombra_inf)
    frame = Image.blend(frame, Image.merge('RGB', (GRANOS[n % 9],) * 3), 0.055)

    # flash blanco en cada corte
    for _, a0, _, _ in SHOTS[1:]:
        if 0 <= t - a0 < 0.12:
            frame = Image.blend(frame, Image.new('RGB', (W, H), (255, 255, 255)),
                                0.20 * (1 - (t - a0) / 0.12))

    dibujar_hit(frame, t)
    dibujar_sub(frame, t)
    d = ImageDraw.Draw(frame)
    d.text((72, 62), '11 DE SEPTIEMBRE  ·  MINUTO A MINUTO', font=f_tag, fill=(186, 190, 196))
    d.rectangle([72, 100, 72 + 300 * min(1, t / DUR), 104], fill=AMBER)

    p.stdin.write(frame.tobytes())

p.stdin.close()
p.wait()
print('listo', OUT)
