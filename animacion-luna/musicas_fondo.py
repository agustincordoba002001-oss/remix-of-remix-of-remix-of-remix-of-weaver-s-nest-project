"""Cinco bandas instrumentales originales para el documental del Titanic.

Cada estilo dura exactamente lo que dura el video y está pensado para sonar
por debajo de la narración: sin melodías invasivas, con dinámica propia.

Uso:  python3 musicas_fondo.py <estilo> <duracion_seg> <salida.wav>
Estilos: cuerdas, aventura, misterio, epica, nostalgia
"""
import sys
import wave

import numpy as np

SR = 44100
BLOCK_SEC = 10

ESTILOS = {
    # nombre: (bpm, progresion (Hz de la triada), melodia, brillo, pulso, aire)
    "cuerdas": dict(
        bpm=96,
        chords=[(146.83, 174.61, 220.00), (116.54, 146.83, 174.61),
                (130.81, 164.81, 196.00), (98.00, 146.83, 196.00)],
        melody=[293.66, 349.23, 440.00, 392.00, 349.23, 293.66, 261.63, 293.66],
        brillo=0.9, pulso=0.55, aire=1.0, arpegio=0.6,
    ),
    "aventura": dict(
        bpm=118,
        chords=[(130.81, 164.81, 196.00), (146.83, 185.00, 220.00),
                (110.00, 138.59, 164.81), (123.47, 155.56, 185.00)],
        melody=[392.00, 440.00, 523.25, 440.00, 392.00, 329.63, 349.23, 392.00],
        brillo=1.15, pulso=1.0, aire=0.7, arpegio=1.0,
    ),
    "misterio": dict(
        bpm=84,
        chords=[(110.00, 130.81, 164.81), (98.00, 116.54, 146.83),
                (103.83, 123.47, 155.56), (87.31, 110.00, 130.81)],
        melody=[261.63, 311.13, 293.66, 261.63, 233.08, 261.63, 207.65, 233.08],
        brillo=0.6, pulso=0.35, aire=1.3, arpegio=0.45,
    ),
    "epica": dict(
        bpm=104,
        chords=[(146.83, 220.00, 293.66), (116.54, 174.61, 233.08),
                (130.81, 196.00, 261.63), (98.00, 146.83, 196.00)],
        melody=[440.00, 523.25, 587.33, 523.25, 440.00, 392.00, 349.23, 440.00],
        brillo=1.0, pulso=0.9, aire=1.1, arpegio=0.8,
    ),
    "nostalgia": dict(
        bpm=72,
        chords=[(174.61, 220.00, 261.63), (155.56, 196.00, 233.08),
                (130.81, 164.81, 196.00), (146.83, 185.00, 220.00)],
        melody=[349.23, 392.00, 440.00, 392.00, 349.23, 329.63, 293.66, 261.63],
        brillo=0.75, pulso=0.25, aire=1.4, arpegio=0.5,
    ),
}


def render(nombre, dur, salida):
    cfg = ESTILOS[nombre]
    beat = 60 / cfg["bpm"]
    chords = cfg["chords"]
    melody = np.asarray(cfg["melody"])
    rng = np.random.default_rng(1912 + len(nombre))

    with wave.open(salida, "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        total = int(dur * SR)
        for start in range(0, total, SR * BLOCK_SEC):
            end = min(total, start + SR * BLOCK_SEC)
            t = np.arange(start, end, dtype=np.float64) / SR
            beat_pos = t / beat
            beat_i = beat_pos.astype(np.int64)
            beat_phase = (beat_pos - beat_i) * beat
            bar = beat_i // 4
            chord_i = (bar // 2) % len(chords)

            # dinámica: sube y baja lentamente para que no canse
            ola = 0.72 + 0.28 * np.sin(2 * np.pi * t / 95.0)
            energia = ola * cfg["aire"]
            pulso = cfg["pulso"] * (0.6 + 0.4 * np.sin(2 * np.pi * t / 61.0 + 1.3))

            pad_l = np.zeros_like(t)
            pad_r = np.zeros_like(t)
            for ci, chord in enumerate(chords):
                mask = chord_i == ci
                for j, f in enumerate(chord):
                    trem = .82 + .18 * np.sin(2 * np.pi * (.09 + j * .019) * t + j)
                    tono = np.sin(2 * np.pi * f * t) + .26 * np.sin(2 * np.pi * f * 2 * t)
                    pan = .26 * np.sin(.06 * t + j * 1.7)
                    pad_l += mask * tono * trem * (1 - pan) / len(chord)
                    pad_r += mask * tono * trem * (1 + pan) / len(chord)
            pad_l *= .040 * energia
            pad_r *= .040 * energia

            octavo = (t / (beat / 2)).astype(np.int64)
            fase_nota = t % (beat / 2)
            raices = np.zeros_like(t)
            for ci, chord in enumerate(chords):
                mask = chord_i == ci
                raices += mask * np.take(np.asarray(chord), octavo % len(chord))
            raices *= np.where(np.isin(octavo % 8, [2, 6]), 2, 1)
            env = np.where(fase_nota < .012, np.clip(fase_nota / .012, 0, 1),
                           np.exp(-(fase_nota - .012) / .18))
            arpegio = (np.sin(2 * np.pi * raices * t)
                       + .40 * np.sin(2 * np.pi * raices * 2.01 * t)
                       + .14 * np.sin(2 * np.pi * raices * 3.99 * t))
            arpegio *= .040 * cfg["arpegio"] * cfg["brillo"] * energia * env

            fase_motivo = t % (beat * 16)
            paso = (fase_motivo / beat).astype(np.int64)
            mf = np.take(melody, (bar + paso) % len(melody))
            mp = fase_motivo % beat
            me = np.where(mp < .03, np.clip(mp / .03, 0, 1), np.exp(-(mp - .03) / .30))
            motivo = (paso < 6) * .026 * cfg["brillo"] * energia * me * np.sin(2 * np.pi * mf * t)

            bombo = np.isin(beat_i % 4, [0, 2]) * np.sin(
                2 * np.pi * (52 + 44 * np.exp(-beat_phase / .04)) * t
            ) * np.exp(-beat_phase / .13) * .070 * pulso
            tic = (beat_i % 2 == 1) * rng.uniform(-1, 1, len(t)) * np.exp(
                -beat_phase / .045) * .016 * pulso

            fi = np.clip(t / 3.0, 0, 1)
            fi = fi * fi * (3 - 2 * fi)
            fo = np.clip((dur - t) / 6.0, 0, 1)
            fo = fo * fo * (3 - 2 * fo)
            master = fi * fo

            izq = np.tanh((pad_l + arpegio * .92 + motivo * 1.06 + bombo + tic) * 1.5) * .70 * master
            der = np.tanh((pad_r + arpegio * 1.08 + motivo * .94 + bombo + tic * .7) * 1.5) * .70 * master
            estereo = np.column_stack((izq, der))
            wav.writeframesraw((np.clip(estereo, -1, 1) * 32767).astype("<i2").tobytes())
    print(salida)


if __name__ == "__main__":
    render(sys.argv[1], float(sys.argv[2]), sys.argv[3])
