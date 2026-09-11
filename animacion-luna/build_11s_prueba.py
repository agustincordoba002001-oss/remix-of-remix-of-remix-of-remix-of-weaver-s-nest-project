"""11-S — prueba de estilo de un minuto (Full HD nativo).

Novedades respecto a las animaciones anteriores:
- Se dibuja directo a 1920x1080 (letras y dibujos nítidos, sin reescalado).
- Los dibujos rotan de lugar: derecha, izquierda, centro, arriba.
- Cada escena tiene su dibujo específico y exacto (torres, Boeing 767, cutter).
"""
import json
import math
import os
import subprocess
from PIL import Image, ImageChops, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
REF = '/mnt/documents/ref_11s/'
AUDIO = '/mnt/documents/11s/narracion_completa.mp3'
MARKS = '/mnt/documents/11s/marcas_completas.json'
OUT = os.environ.get('OUT', '/mnt/documents/11s/prueba_estilo_1min.mp4')
LOGO = '/dev-server/public/demo/mano-a-realista.png'  # la mano de siempre

RED = (198, 40, 44, 255)
BLUE = (25, 84, 143, 255)
GOLD = (198, 140, 32, 255)
INK = (28, 31, 35, 255)


FONTS = '/dev-server/public/fonts/'
F_DISPLAY = FONTS + 'Anton.ttf'        # titulares
F_STRONG = FONTS + 'Oswald-Bold.ttf'   # subtítulos
F_UI = FONTS + 'Inter-SemiBold.ttf'    # datos y pie


def font(sz, path=F_DISPLAY):
    return ImageFont.truetype(path, sz)


F_HERO, F_TITLE = font(158), font(104)
F_SUB, F_TINY = font(66, F_STRONG), font(26, F_UI)


HAND_SIZE = 300
hand = Image.open(LOGO).convert('RGBA').resize((HAND_SIZE, HAND_SIZE), Image.Resampling.LANCZOS)
TIPX, TIPY = int(.26 * HAND_SIZE), int(.70 * HAND_SIZE)


def load(name, box):
    im = Image.open(REF + name).convert('RGBA')
    if im.mode == 'RGBA':
        # recorta el blanco/transparente sobrante
        bb = im.getchannel('A').point(lambda a: 255 if a > 12 else 0).getbbox()
        if bb:
            im = im.crop(bb)
    im.thumbnail(box, Image.Resampling.LANCZOS)
    return im


# escena -> (dibujo, tamaño máximo, líneas de título, colores, layout)
PLAN = [
    ('a01-manana.png', (1500, 700), ['11 DE SEPTIEMBRE'], ['LA HISTORIA COMPLETA, MINUTO A MINUTO'], 'hero'),
    ('a05-torres.png', (620, 900), ['UNA MAÑANA', 'CUALQUIERA'], ['MARTES, 6:00 A.M. · COSTA ESTE'], 'izq'),
    ('a02-tren.png', (1000, 640), ['LA CIUDAD', 'SE PONE EN MARCHA'], ['CAFÉ, DIARIO Y TRENES REPLETOS'], 'der'),
    ('a03-aeropuerto.png', (1080, 620), ['CUATRO VUELOS', 'DE RUTINA'], ['BOSTON · NEWARK · WASHINGTON'], 'izq'),
    ('a04-control.png', (1150, 620), ['DIECINUEVE', 'PASAJEROS'], ['NADIE LOS MIRA DOS VECES'], 'centro'),
    ('a06-boeing767.png', (1350, 560), ['UN AVIÓN', 'CONVERTIDO EN ARMA'], ['BOEING 767 · 90.000 LITROS DE COMBUSTIBLE'], 'der'),
    ('a09-cutter.png', (900, 560), ['CÚTERS', 'Y FILOS CORTOS'], ['PERMITIDOS EN 2001'], 'izq'),
    ('a05-torres.png', (600, 880), ['110 PISOS', 'SOBRE MANHATTAN'], ['WORLD TRADE CENTER · 50.000 PERSONAS'], 'der'),
    ('a01-manana.png', (1450, 680), ['EL CORAZÓN', 'DEL MUNDO'], ['DONDE LATE EL DINERO DEL PLANETA'], 'centro'),
    ('a07-radar.png', (1080, 640), ['8:14 A.M.', 'FUERA DE RUTA'], ['EL RADAR PIERDE AL VUELO 11'], 'izq'),
]

marks = json.load(open(MARKS))[:len(PLAN)]
DUR = marks[-1]['t1'] + 0.55
N = math.ceil(DUR * FPS)

IMG = {}
for name, box, *_ in PLAN:
    IMG[(name, box)] = load(name, box)


def text_layer(lines, color, f, spacing=14, maxw=1080):
    tmp = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    size = f.size
    while size > 24 and max(tmp.textlength(x, font=ImageFont.truetype(f.path, size)) for x in lines) > maxw:
        size -= 4
    f = ImageFont.truetype(f.path, size)
    boxes = [tmp.textbbox((0, 0), x, font=f) for x in lines]
    ws = [b[2] - b[0] for b in boxes]
    hs = [b[3] - b[1] + spacing for b in boxes]
    lay = Image.new('RGBA', (max(ws) + 24, sum(hs) + 22), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y = 6
    for line, w, h in zip(lines, ws, hs):
        d.text((10, y), line, font=f, fill=color)
        y += h
    return lay



def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mask_reveal(im, rows, p):
    p = max(0.0, min(1.0, p))
    m = Image.new('L', im.size, 0)
    d = ImageDraw.Draw(m)
    rh = im.height / rows
    pos = p * rows
    row, frac = int(pos), pos - int(pos)
    for r in range(min(row, rows)):
        d.rectangle((0, int(r * rh) - 3, im.width, int((r + 1) * rh) + 3), fill=255)
    tx, ty = im.width, im.height
    if row < rows:
        ww = int(im.width * frac)
        d.rectangle((0, int(row * rh) - 3, ww, int((row + 1) * rh) + 3), fill=255)
        tx, ty = ww, row * rh + rh * .55
    out = im.copy()
    out.putalpha(ImageChops.multiply(im.getchannel('A'), m))
    return out, tx, ty


def compose(i):
    """Devuelve la lista de elementos (imagen, posición, filas) de la escena i."""
    name, box, t1, t2, layout = PLAN[i]
    im = IMG[(name, box)]
    if layout == 'hero':
        mw = 1700
    elif layout == 'centro':
        mw = 1600
    else:
        mw = max(620, W - im.width - 300)
    tt = text_layer(t1, RED if i % 2 == 0 else BLUE,
                    F_HERO if layout == 'hero' else F_TITLE, maxw=mw)
    ss = text_layer(t2, INK if i % 3 else GOLD, F_SUB, maxw=mw)

    els = []
    if layout == 'hero':
        els.append(('t', tt, ((W - tt.width) // 2, 90)))
        els.append(('t', ss, ((W - ss.width) // 2, 90 + tt.height + 4)))
        els.append(('i', im, ((W - im.width) // 2, H - im.height - 60)))
    elif layout == 'izq':
        els.append(('i', im, (110, (H - im.height) // 2 + 20)))
        x = 110 + im.width + 90
        els.append(('t', tt, (x, 250)))
        els.append(('t', ss, (x, 250 + tt.height + 16)))
    elif layout == 'der':
        els.append(('t', tt, (120, 260)))
        els.append(('t', ss, (120, 260 + tt.height + 16)))
        els.append(('i', im, (W - im.width - 110, (H - im.height) // 2 + 20)))
    else:  # centro
        els.append(('t', tt, (130, 110)))
        els.append(('t', ss, (130, 110 + tt.height + 12)))
        els.append(('i', im, ((W - im.width) // 2, H - im.height - 70)))
    return els


SC = []
for i, mk in enumerate(marks):
    t0 = mk['t0'] - 0.45 if i else 0.0
    t1 = marks[i + 1]['t0'] - 0.45 if i + 1 < len(marks) else DUR
    els = compose(i)
    span = max(1.0, min((t1 - t0) * .62, 3.1))
    per = span / len(els)
    cur = t0
    out = []
    for kind, im, xy in els:
        rows = max(4, min(10, im.height // 88)) if kind == 'i' else max(1, im.height // 110)
        out.append(dict(im=im, xy=xy, t0=cur, t1=cur + per, rows=rows))
        cur += per * .82
    SC.append(dict(t0=t0, els=out))

cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
       '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
       '-i', AUDIO, '-t', f'{DUR:.2f}',
       '-map', '0:v', '-map', '1:a',
       '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
       '-profile:v', 'high', '-level', '4.2', '-c:a', 'aac', '-b:a', '192k',
       '-movflags', '+faststart', '-shortest', OUT]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
assert proc.stdin

for frame in range(N):
    t = frame / FPS
    idx = max(i for i, s in enumerate(SC) if t >= s['t0'])
    s = SC[idx]
    canvas = Image.new('RGB', (W, H), (255, 255, 255))
    tip = None
    for el in s['els']:
        if t < el['t0']:
            continue
        p = (t - el['t0']) / max(.05, el['t1'] - el['t0'])
        if p < 1:
            im, tx, ty = mask_reveal(el['im'], el['rows'], ease(p))
            canvas.paste(im, el['xy'], im)
            tip = (el['xy'][0] + tx, el['xy'][1] + ty)
        else:
            canvas.paste(el['im'], el['xy'], el['im'])
    if tip:
        hx = int(max(-220, min(W - 60, tip[0] - TIPX)))
        hy = int(max(-220, min(H - 60, tip[1] - TIPY)))
        canvas.paste(hand, (hx, hy), hand)
    d = ImageDraw.Draw(canvas)
    d.text((100, 1022), '11 DE SEPTIEMBRE  ·  LA HISTORIA COMPLETA', font=F_TINY, fill=(150, 152, 156))
    proc.stdin.write(canvas.tobytes())

proc.stdin.close()
code = proc.wait()
if code:
    raise SystemExit(code)
print(OUT, round(DUR, 2))
