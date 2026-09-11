"""Narración completa del documental 11-S — voz Dark, sin música.

Genera /mnt/documents/11s/full.wav y /mnt/documents/11s/marks_full.json.
Cada frase se sintetiza y masteriza una sola vez; si el proceso se corta,
al volver a ejecutarlo continúa donde quedó.
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
TMP = '/mnt/documents/11s'
SEG = '/mnt/documents/voces_11s'
os.makedirs(TMP, exist_ok=True)
os.makedirs(SEG, exist_ok=True)

GUION = json.load(open('animacion-luna/guion_11s.json', encoding='utf-8'))['escenas']


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
              'guerra', 'batalla', 'derrotado', 'conquista', 'muerte', 'caos',
              'catástrofe', 'terrorista', 'secuestrador', 'impacto', 'desplomó',
              'colapsó', 'devastador', 'sacrificaron', 'víctima', 'fatal')
AGILES = ('porque', 'entonces', 'después', 'y todo', 'además', 'mientras', 'pero', 'para')
NOMBRES_LARGOS = ('Mohamed', 'Atta', 'Champollion', 'Tutankamón')


def ritmo(txt):
    """Ritmo claro y conversacional, con aire extra en frases dramáticas."""
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


# Pronunciación: nombres propios y términos que Piper lee mal en español.
FONETICA = {
    'Betty Ong': 'Beti Ong',
    'Mohamed Atta': 'Mojamed Ata',
    'Atta': 'Ata',
    'Daniel Lewin': 'Daniel Levin',
    'Lewin': 'Levin',
    'George Bush': 'Yor Bush',
    'Bush': 'Bush',
    'World Trade Center': 'Uorld Treid Center',
    'Newark': 'Niúark',
    'New Jersey': 'Niú Yersei',
    'Manhattan': 'Manjatán',
    'Pensilvania': 'Pensilvania',
    'Sarasota': 'Sarasota',
    'Florida': 'Florida',
    'Ohio': 'Ohio',
    'Pentágono': 'Pentágono',
    'Torre Norte': 'Torre Norte',
    'Torre Sur': 'Torre Sur',
    'Capitolio': 'Capitolio',
    'Fuerza Aérea': 'Fuerza Aérea',
    'American Airlines': 'American Airlines',
    'United Airlines': 'United Airlines',
    'Boeing': 'Boing',
    'transpondedor': 'transpondedor',
    'radares': 'radares',
    'controladores': 'controladores',
    'secuestradores': 'secuestradores',
    'terroristas': 'terroristas',
    'combustible': 'combustible',
    'ascensores': 'ascensores',
    'emergencia': 'emergencia',
}


def pronunciar(txt):
    out = txt
    # ordenar de más específico a más general para evitar reemplazos parciales
    for k, v in sorted(FONETICA.items(), key=lambda x: -len(x[0])):
        out = re.sub(rf'\b{re.escape(k)}\b', v, out, flags=re.IGNORECASE)
    return out


parts = [np.zeros(int(0.5 * SR), np.float32)]
marks = []
tcur = 0.5

for i, s in enumerate(GUION):
    txt, gap = s['txt'], s['gap']
    ajustes = {
        'length_scale': ritmo(txt),
        'noise_scale': round(0.44 + (i % 3) * 0.01, 3),
        'noise_w': round(0.56 + (i % 2) * 0.02, 3),
    }
    raw = f'{SEG}/f_{i:03d}.wav'
    dst = f'{SEG}/f_{i:03d}_master.wav'
    if not os.path.exists(raw):
        sintetizar(pronunciar(txt), 'dark', raw, ajustes=ajustes)
    if not os.path.exists(dst):
        masterizar(raw, dst, 'dark')
    a = recortar_silencio(leer_wav(dst))
    a = nivelar(a)
    fade = int(0.05 * SR)
    a[:fade] *= np.linspace(0, 1, fade)
    a[-fade:] *= np.linspace(1, 0, fade)
    marks.append(dict(t0=tcur, t1=tcur + len(a) / SR, txt=txt))
    tcur += len(a) / SR + gap
    parts.append(a)
    parts.append(np.zeros(int(gap * SR), np.float32))
    if i % 5 == 0:
        print('frase', i, 'de', len(GUION), 'min', round(tcur / 60, 2), flush=True)

voz = np.concatenate(parts)
pico = float(np.abs(voz).max())
if pico > 0.80:
    voz *= 0.80 / pico
voz = np.clip(voz, -1, 1)

with wave.open(f'{TMP}/full.wav', 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((voz * 32767).astype(np.int16).tobytes())
json.dump(marks, open(f'{TMP}/marks_full.json', 'w'), ensure_ascii=False)

palabras = sum(len(s['txt'].split()) for s in GUION)
minutos = round(palabras / 140, 1)
print('LISTO dur_min', round(len(voz) / SR / 60, 2), 'palabras', palabras, 'min_est', minutos)
