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
LOGO = '/dev-server/public/demo/mano-lapiz.png'  # placeholder; la mano dibuja

RED = (198, 40, 44, 255)
BLUE = (25, 84, 143, 255)
GOLD = (198, 140, 32, 255)
INK = (28, 31, 35, 255)


def font(sz, bold=True):
    q = 'DejaVu Sans Condensed:bold' if bold else 'DejaVu Sans Condensed'
    p = subprocess.run(['fc-match', '-f', '%{file}', q],
                       capture_output=True, text=True, check=True).stdout
    return ImageFont.truetype(p, sz)


F_HERO, F_TITLE, F_SUB, F_TINY = font(150), font(96), font(58), font(24)

hand = Image.open(LOGO).convert('RGBA').resize((330, 330), Image.Resampling.LANCZOS)
TIPX, TIPY = int(.205 * 330), int(.664 * 330)


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
    ('a01-manana.png', (1500, 700), ['11 DE SEPTIEMBRE'], ['LA HISTORIA COMPLETA'], 'hero'),
    ('a05-torres.png', (620, 900), ['UN DÍA', 'LABORAL MÁS'], ['LA COSTA ESTE DESPIERTA'], 'izq'),
    ('a02-tren.png', (1000, 640), ['TRENES', 'REPLETOS'], ['CAFÉ, DIARIO Y OFICINA'], 'der'),
    ('a03-aeropuerto.png', (1080, 620), ['AEROPUERTOS'], ['UN VUELO DOMÉSTICO MÁS'], 'izq'),
    ('a04-control.png', (1150, 620), ['DIECINUEVE', 'HOMBRES'], ['ENTRE LA MULTITUD'], 'centro'),
    ('a06-boeing767.png', (1350, 560), ['AVIONES', 'COMO ARMAS'], ['NADIE LO IMAGINABA'], 'der'),
    ('a09-cutter.png', (900, 560), ['ARMAS BLANCAS', 'DE FILO CORTO'], ['NINGUNA ALARMA SONÓ'], 'izq'),
    ('a05-torres.png', (600, 880), ['BAJO', 'MANHATTAN'], ['WORLD TRADE CENTER'], 'der'),
    ('a01-manana.png', (1450, 680), ['LAS TORRES', 'GEMELAS'], ['EL CORAZÓN FINANCIERO'], 'centro'),
    ('a07-radar.png', (1080, 640), ['FUERA', 'DE RUTA'], ['EN CUESTIÓN DE MINUTOS'], 'izq'),
]

marks = json.load(open(MARKS))[:len(PLAN)]
DUR = marks[-1]['t1'] + 0.55
N = math.ceil(DUR * FPS)

IMG = {}
for name, box, *_ in PLAN:
    IMG[(name, box)] = load(name, box)


def text_layer(lines, color, f, spacing=14):
    tmp = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
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
    tt = text_layer(t1, RED if i % 2 == 0 else BLUE, F_HERO if layout == 'hero' else F_TITLE)
    ss = text_layer(t2, INK if i % 3 else GOLD, F_SUB)
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
