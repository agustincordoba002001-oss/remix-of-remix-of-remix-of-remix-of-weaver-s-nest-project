"""Rehace SOLO las frases aprobadas en el editor y rearma la narración.

Uso:
    python3 animacion-luna/rehacer_frases.py egipto_humor

Lee /mnt/documents/<id>/correcciones.json (lo que aprobó el usuario frase por
frase), vuelve a sintetizar únicamente esas frases con la MISMA voz, el mismo
masterizado y el mismo nivel que el resto de la narración, y vuelve a armar
full.wav reutilizando tal cual los audios ya masterizados de las demás frases.
Así el tono, el volumen y la entonación quedan idénticos y nada más se toca.
"""
import json
import os
import re
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voces_space import sintetizar  # noqa: E402
from mastering import masterizar  # noqa: E402

SR = 48000
ID = sys.argv[1] if len(sys.argv) > 1 else 'egipto_humor'
BASE = f'/mnt/documents/{ID}'
SEG = f'/mnt/documents/voces_{ID}'
GUION_PATH = f'{os.path.dirname(os.path.abspath(__file__))}/guion_{ID}.json'

GUION = json.load(open(GUION_PATH, encoding='utf-8'))['escenas']


def leer_wav(path):
    with wave.open(path, 'rb') as w:
        raw = w.readframes(w.getnframes())
        sr, ch = w.getframerate(), w.getnchannels()
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        m = int(len(a) * SR / sr)
        a = np.interp(np.linspace(0, len(a) - 1, m), np.arange(len(a)), a).astype(np.float32)
    return a


def recortar_silencio(a, umbral=0.012):
    idx = np.where(np.abs(a) > umbral)[0]
    if len(idx) == 0:
        return a
    ini = max(0, idx[0] - int(0.04 * SR))
    fin = min(len(a), idx[-1] + int(0.10 * SR))
    return a[ini:fin]


DRAMATICAS = ('muertos', 'murieron', 'miedo', 'tragedia', 'incendio', 'pálidos',
              'riesgoso', 'inalcanzable', 'silencio', 'solo', 'nunca', 'desastre',
              'guerra', 'batalla', 'derrotado', 'conquista', 'muerte', 'caos')
AGILES = ('porque', 'entonces', 'después', 'y todo', 'además', 'mientras', 'pero', 'para')
NOMBRES_LARGOS = ('Champollion', 'Tutankamón', 'Hatshepsut', 'Akenatón', 'Ptolomeo', 'Cleopatra')


def ritmo(txt):
    t = txt.lower()
    v = 1.08
    if any(k in t for k in DRAMATICAS):
        v += 0.04
    if any(t.startswith(k) for k in AGILES):
        v -= 0.015
    if any(k in txt for k in NOMBRES_LARGOS):
        v += 0.02
    if len(txt) > 140:
        v += 0.02
    if re.search(r'\d', t):
        v += 0.015
    return round(min(1.22, max(1.05, v)), 3)


def nivelar(a, objetivo=0.079, techo=0.68):
    activo = a[np.abs(a) > 0.01]
    rms = float(np.sqrt(np.mean(activo ** 2))) if len(activo) else 1e-6
    g = objetivo / max(1e-6, rms)
    pico = float(np.abs(a).max()) or 1e-6
    return a * min(g, techo / pico)


FONETICA = {
    'Champollion': 'Champolión', 'Hatshepsut': 'Hachepsut', 'Nefertiti': 'Nefertíti',
    'Amenofis': 'Amenófis', 'Tutmosis': 'Tutmósis', 'Imhotep': 'Imotep', 'Zoser': 'Yóser',
    'Saqqara': 'Sakara', 'Keops': 'Kéops', 'Esnofru': 'Esnofrú', 'Kemet': 'Kémet',
    'hicsos': 'ícsos', 'hititas': 'ititas', 'hitita': 'itita', 'Kadesh': 'Kádesh',
    'Rosetta': 'Roseta', 'Rashid': 'Rachid', 'Accio': 'Ácsio', 'kohl': 'col',
    'Ebers': 'Ébers', 'Octavio': 'Octávio', 'ADN': 'a de ene', 'Nubia': 'Núbia',
}


def pronunciar(txt):
    out = txt
    for k, v in FONETICA.items():
        out = re.sub(rf'\b{k}\b', v, out)
    return out


# --- 1. Frases aprobadas en el editor -------------------------------------
cambios = {}
try:
    datos = json.load(open(f'{BASE}/correcciones.json', encoding='utf-8'))
    for c in datos.get('correcciones', []):
        cambios[int(c['indice'])] = c['texto']
except FileNotFoundError:
    pass

if not cambios:
    print('No hay frases aprobadas: no hay nada que rehacer.')
    raise SystemExit(0)

print('frases a rehacer:', sorted(cambios))

for i, texto in sorted(cambios.items()):
    if i >= len(GUION):
        continue
    GUION[i]['txt'] = texto
    raw, dst = f'{SEG}/f_{i:03d}.wav', f'{SEG}/f_{i:03d}_master.wav'
    for p in (raw, dst):
        if os.path.exists(p):
            os.remove(p)
    ajustes = {
        'length_scale': ritmo(texto),
        'noise_scale': round(0.44 + (i % 3) * 0.01, 3),
        'noise_w': round(0.56 + (i % 2) * 0.02, 3),
    }
    sintetizar(pronunciar(texto), 'dark', raw, ajustes=ajustes)
    masterizar(raw, dst, 'dark')
    print('rehecha frase', i, flush=True)

json.dump({'escenas': GUION}, open(GUION_PATH, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# --- 2. Rearmar la narración completa ------------------------------------
parts = [np.zeros(int(0.5 * SR), np.float32)]
marks = []
tcur = 0.5
for i, s in enumerate(GUION):
    dst = f'{SEG}/f_{i:03d}_master.wav'
    a = nivelar(recortar_silencio(leer_wav(dst)))
    fade = int(0.05 * SR)
    a[:fade] *= np.linspace(0, 1, fade)
    a[-fade:] *= np.linspace(1, 0, fade)
    marks.append(dict(t0=tcur, t1=tcur + len(a) / SR, txt=s['txt']))
    tcur += len(a) / SR + s['gap']
    parts.append(a)
    parts.append(np.zeros(int(s['gap'] * SR), np.float32))

voz = np.concatenate(parts)
pico = float(np.abs(voz).max())
if pico > 0.80:
    voz *= 0.80 / pico
voz = np.clip(voz, -1, 1)

with wave.open(f'{BASE}/full.wav', 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((voz * 32767).astype(np.int16).tobytes())
json.dump(marks, open(f'{BASE}/marks_full.json', 'w'), ensure_ascii=False)
print('LISTO dur_min', round(len(voz) / SR / 60, 2), 'frases', len(GUION))
