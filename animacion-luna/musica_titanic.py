"""Banda instrumental original para el documental del Titanic.

Genera una base estéreo dinámica y discreta, pensada para mezclarse debajo de
la narración. No usa melodías ni grabaciones externas.
"""
import math
import os
import random
import struct
import wave

SR = 48000
DUR = float(os.environ.get("DUR", "1137.81"))
OUT = os.environ.get("OUT", "/tmp/musica_titanic.wav")
BLOCK = 4096
BPM = 108
BEAT = 60 / BPM

# Progresión cinematográfica en re menor: Dm, Bb, F, C, con variaciones.
CHORDS = [
    (146.83, 174.61, 220.00),
    (116.54, 146.83, 174.61),
    (130.81, 164.81, 196.00),
    (130.81, 164.81, 196.00, 233.08),
]
MELODY = [293.66, 349.23, 440.00, 392.00, 349.23, 293.66, 261.63, 293.66]
random.seed(1912)


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def section(t):
    if t < 24:
        return 1.0, 1.0, 0.65
    if t < 250:
        return 0.72, 0.55, 0.42
    if t < 520:
        return 0.78, 0.68, 0.50
    if t < 780:
        return 0.88, 0.82, 0.58
    if t < 995:
        return 1.00, 1.00, 0.72
    return 0.65, 0.38, 0.34


def envelope(phase, attack=0.06, decay=0.9):
    if phase < attack:
        return smoothstep(phase / attack)
    return math.exp(-(phase - attack) / decay)


with wave.open(OUT, "wb") as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(SR)
    total = int(DUR * SR)
    for start in range(0, total, BLOCK):
        frames = bytearray()
        end = min(total, start + BLOCK)
        for n in range(start, end):
            t = n / SR
            energy, drums, sparkle = section(t)
            beat_pos = t / BEAT
            beat_i = int(beat_pos)
            beat_phase = (beat_pos - beat_i) * BEAT
            bar = beat_i // 4
            chord = CHORDS[(bar // 2) % len(CHORDS)]

            # Cuerdas/pad con movimiento estéreo lento.
            pad_l = pad_r = 0.0
            for j, f in enumerate(chord):
                trem = 0.80 + 0.20 * math.sin(2 * math.pi * (0.10 + j * 0.017) * t + j)
                tone = math.sin(2 * math.pi * f * t) + 0.28 * math.sin(2 * math.pi * f * 2 * t)
                pan = 0.24 * math.sin(0.07 * t + j * 1.7)
                pad_l += tone * trem * (1 - pan)
                pad_r += tone * trem * (1 + pan)
            pad_l *= 0.035 * energy / len(chord)
            pad_r *= 0.035 * energy / len(chord)

            # Ostinato de piano/celesta: una nota cada medio pulso.
            eighth = int(t / (BEAT / 2))
            note_phase = t % (BEAT / 2)
            root = chord[eighth % len(chord)] * (2 if eighth % 8 in (2, 6) else 1)
            pluck_env = envelope(note_phase, 0.012, 0.19)
            pluck = (math.sin(2 * math.pi * root * t) +
                     0.42 * math.sin(2 * math.pi * root * 2.01 * t) +
                     0.16 * math.sin(2 * math.pi * root * 3.99 * t))
            pluck *= 0.042 * sparkle * pluck_env

            # Motivo breve cada cuatro compases, deja aire a la voz.
            motif_phase = t % (BEAT * 16)
            motif_step = int(motif_phase / BEAT)
            motif = 0.0
            if motif_step < 6:
                mf = MELODY[(bar + motif_step) % len(MELODY)]
                me = envelope(motif_phase % BEAT, 0.03, 0.32)
                motif = 0.024 * sparkle * me * math.sin(2 * math.pi * mf * t)

            # Pulso grave y percusión suave, más intensa en el tramo del hundimiento.
            kick = 0.0
            if beat_i % 4 in (0, 2):
                ke = math.exp(-beat_phase / 0.12)
                kick = math.sin(2 * math.pi * (54 + 42 * math.exp(-beat_phase / 0.04)) * t) * ke * 0.075 * drums
            tick = 0.0
            if beat_i % 2 == 1:
                te = math.exp(-beat_phase / 0.045)
                noise = random.random() * 2 - 1
                tick = noise * te * 0.018 * drums

            # Crescendos breves al cambiar de bloque narrativo.
            swell = 0.0
            for marker in (24, 250, 520, 780, 995):
                dt = t - marker
                if -2.5 < dt < 0:
                    se = smoothstep((dt + 2.5) / 2.5)
                    swell += math.sin(2 * math.pi * 98 * t) * se * 0.018

            fade_in = smoothstep(t / 2.2)
            fade_out = smoothstep((DUR - t) / 5.0)
            master = fade_in * fade_out
            left = (pad_l + pluck * 0.92 + motif * 1.06 + kick + tick + swell) * master
            right = (pad_r + pluck * 1.08 + motif * 0.94 + kick + tick * 0.72 + swell) * master
            left = math.tanh(left * 1.5) * 0.72
            right = math.tanh(right * 1.5) * 0.72
            frames.extend(struct.pack('<hh', int(left * 32767), int(right * 32767)))
        wav.writeframesraw(frames)
print(OUT)
