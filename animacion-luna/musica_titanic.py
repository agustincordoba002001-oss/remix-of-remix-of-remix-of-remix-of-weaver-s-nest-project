"""Banda instrumental original para el documental del Titanic.

Genera una base estéreo dinámica y discreta, pensada para mezclarse debajo de
la narración. No usa melodías ni grabaciones externas.
"""
import math
import os
import wave

import numpy as np

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
rng = np.random.default_rng(1912)


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


with wave.open(OUT, "wb") as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(SR)
    total = int(DUR * SR)
    for start in range(0, total, SR * 10):
        end = min(total, start + BLOCK)
        end = min(total, start + SR * 10)
        t = np.arange(start, end, dtype=np.float64) / SR
        beat_pos = t / BEAT
        beat_i = beat_pos.astype(np.int64)
        beat_phase = (beat_pos - beat_i) * BEAT
        bar = beat_i // 4
        chord_i = (bar // 2) % len(CHORDS)
        energy = np.select([t < 24, t < 250, t < 520, t < 780, t < 995],
                           [1.0, .72, .78, .88, 1.0], default=.65)
        drums = np.select([t < 24, t < 250, t < 520, t < 780, t < 995],
                          [1.0, .55, .68, .82, 1.0], default=.38)
        sparkle = np.select([t < 24, t < 250, t < 520, t < 780, t < 995],
                            [.65, .42, .50, .58, .72], default=.34)

        pad_l = np.zeros_like(t)
        pad_r = np.zeros_like(t)
        for ci, chord in enumerate(CHORDS):
            mask = chord_i == ci
            for j, f in enumerate(chord):
                trem = .80 + .20 * np.sin(2 * np.pi * (.10 + j * .017) * t + j)
                tone = np.sin(2 * np.pi * f * t) + .28 * np.sin(2 * np.pi * f * 2 * t)
                pan = .24 * np.sin(.07 * t + j * 1.7)
                pad_l += mask * tone * trem * (1 - pan) / len(chord)
                pad_r += mask * tone * trem * (1 + pan) / len(chord)
        pad_l *= .035 * energy
        pad_r *= .035 * energy

        eighth = (t / (BEAT / 2)).astype(np.int64)
        note_phase = t % (BEAT / 2)
        roots = np.zeros_like(t)
        for ci, chord in enumerate(CHORDS):
            mask = chord_i == ci
            choices = np.take(np.asarray(chord), eighth % len(chord))
            roots += mask * choices
        roots *= np.where(np.isin(eighth % 8, [2, 6]), 2, 1)
        pe = np.where(note_phase < .012, np.clip(note_phase / .012, 0, 1),
                      np.exp(-(note_phase - .012) / .19))
        pluck = (np.sin(2*np.pi*roots*t) + .42*np.sin(2*np.pi*roots*2.01*t) +
                 .16*np.sin(2*np.pi*roots*3.99*t)) * .042 * sparkle * pe

        motif_phase = t % (BEAT * 16)
        motif_step = (motif_phase / BEAT).astype(np.int64)
        mf = np.take(np.asarray(MELODY), (bar + motif_step) % len(MELODY))
        mp = motif_phase % BEAT
        me = np.where(mp < .03, np.clip(mp/.03, 0, 1), np.exp(-(mp-.03)/.32))
        motif = (motif_step < 6) * .024 * sparkle * me * np.sin(2*np.pi*mf*t)

        kick_mask = np.isin(beat_i % 4, [0, 2])
        kick = kick_mask * np.sin(2*np.pi*(54 + 42*np.exp(-beat_phase/.04))*t) * np.exp(-beat_phase/.12) * .075 * drums
        tick_mask = beat_i % 2 == 1
        tick = tick_mask * rng.uniform(-1, 1, len(t)) * np.exp(-beat_phase/.045) * .018 * drums

        swell = np.zeros_like(t)
        for marker in (24, 250, 520, 780, 995):
            dt = t - marker
            x = np.clip((dt + 2.5) / 2.5, 0, 1)
            se = x*x*(3-2*x)
            swell += ((dt > -2.5) & (dt < 0)) * np.sin(2*np.pi*98*t) * se * .018

        fi = np.clip(t / 2.2, 0, 1); fi = fi*fi*(3-2*fi)
        fo = np.clip((DUR-t) / 5, 0, 1); fo = fo*fo*(3-2*fo)
        master = fi * fo
        left = np.tanh((pad_l + pluck*.92 + motif*1.06 + kick + tick + swell)*1.5)*.72*master
        right = np.tanh((pad_r + pluck*1.08 + motif*.94 + kick + tick*.72 + swell)*1.5)*.72*master
        stereo = np.column_stack((left, right))
        wav.writeframesraw((np.clip(stereo, -1, 1) * 32767).astype('<i2').tobytes())
print(OUT)
