"""Cinco bandas nuevas, alegres y entretenidas para el documental del Titanic.

Estilos vivos, melódicos y con ritmo, pensados para sonar por debajo de la
narración sin competir con la voz.

Uso:  python3 musicas_fondo2.py <estilo> <duracion_seg> <salida.wav>
Estilos: swing, ukulele, jugueton, vals, marinero
"""
import sys
import wave

import numpy as np

SR = 44100
BLOCK_SEC = 10

ESTILOS = {
    # swing de orquesta de barco: alegre, con bombo y chasquidos
    "swing": dict(
        bpm=124,
        chords=[(261.63, 329.63, 392.00), (349.23, 440.00, 523.25),
                (220.00, 261.63, 329.63), (196.00, 246.94, 293.66)],
        melody=[523.25, 659.25, 587.33, 659.25, 523.25, 440.00, 392.00, 523.25],
        brillo=1.1, pulso=1.0, aire=1.0, arpegio=0.9, swing=0.62,
    ),
    # ukelele tropical: punteo rápido y liviano
    "ukulele": dict(
        bpm=132,
        chords=[(261.63, 329.63, 392.00), (392.00, 493.88, 587.33),
                (349.23, 440.00, 523.25), (293.66, 369.99, 440.00)],
        melody=[659.25, 783.99, 659.25, 587.33, 523.25, 587.33, 659.25, 523.25],
        brillo=1.3, pulso=0.7, aire=0.9, arpegio=1.2, swing=0.5,
    ),
    # juguetón: glockenspiel y pizzicato, bien curioso
    "jugueton": dict(
        bpm=112,
        chords=[(293.66, 369.99, 440.00), (261.63, 329.63, 392.00),
                (349.23, 440.00, 523.25), (220.00, 277.18, 329.63)],
        melody=[587.33, 739.99, 880.00, 739.99, 659.25, 587.33, 523.25, 587.33],
        brillo=1.25, pulso=0.8, aire=1.1, arpegio=1.1, swing=0.5,
    ),
    # vals alegre de salón: 3/4 orquestal
    "vals": dict(
        bpm=150,
        chords=[(261.63, 329.63, 392.00), (349.23, 440.00, 523.25),
                (196.00, 246.94, 293.66), (261.63, 329.63, 392.00)],
        melody=[659.25, 587.33, 523.25, 659.25, 783.99, 659.25, 523.25, 587.33],
        brillo=1.0, pulso=0.9, aire=1.0, arpegio=0.8, swing=0.5, vals=True,
    ),
    # marinero: ritmo de cubierta, palmas y melodía aventurera
    "marinero": dict(
        bpm=126,
        chords=[(196.00, 246.94, 293.66), (261.63, 329.63, 392.00),
                (293.66, 369.99, 440.00), (220.00, 261.63, 329.63)],
        melody=[587.33, 659.25, 783.99, 659.25, 587.33, 523.25, 587.33, 493.88],
        brillo=1.15, pulso=1.1, aire=0.95, arpegio=1.0, swing=0.58,
    ),
}


def render(nombre, dur, salida):
    cfg = ESTILOS[nombre]
    beat = 60 / cfg["bpm"]
    chords = cfg["chords"]
    melody = np.asarray(cfg["melody"])
    sw = cfg.get("swing", 0.5)
    es_vals = cfg.get("vals", False)
    rng = np.random.default_rng(2024 + len(nombre) * 7)

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
            if es_vals:
                bar = beat_i // 3
            else:
                bar = beat_i // 4
            chord_i = (bar // 2) % len(chords)

            ola = 0.74 + 0.26 * np.sin(2 * np.pi * t / 87.0)
            energia = ola * cfg["aire"]
            pulso = cfg["pulso"] * (0.65 + 0.35 * np.sin(2 * np.pi * t / 53.0 + 0.7))

            # pad de acompañamiento, más corto y vivo (staccato suave)
            pad_l = np.zeros_like(t)
            pad_r = np.zeros_like(t)
            for ci, chord in enumerate(chords):
                mask = chord_i == ci
                for j, f in enumerate(chord):
                    trem = .80 + .20 * np.sin(2 * np.pi * (.11 + j * .017) * t + j * 2)
                    tono = np.sin(2 * np.pi * f * t) + .30 * np.sin(2 * np.pi * f * 2 * t)
                    pan = .28 * np.sin(.07 * t + j * 1.9)
                    pad_l += mask * tono * trem * (1 - pan) / len(chord)
                    pad_r += mask * tono * trem * (1 + pan) / len(chord)
            pad_l *= .036 * energia
            pad_r *= .036 * energia

            # bajo en la raíz con patrón saltado
            fase_bajo = t % beat
            raiz = np.zeros_like(t)
            for ci, chord in enumerate(chords):
                mask = chord_i == ci
                raiz += mask * chord[0] / 2
            salta = np.where(np.isin(beat_i % 4, [0, 2]), 1.0, 0.55)
            env_b = np.exp(-fase_bajo / .30)
            bajo = (np.sin(2 * np.pi * raiz * t) + .25 * np.sin(2 * np.pi * raiz * 2 * t))
            bajo *= .055 * salta * env_b * pulso

            # arpegio en octavos con swing
            oct_len = beat / 2
            oct_pos = t / oct_len
            oct_i = oct_pos.astype(np.int64)
            # desplazar el segundo octavo para efecto swing
            fase_nota = (t % oct_len) - (oct_i % 2 == 1) * (sw - 0.5) * beat
            fase_nota = np.clip(fase_nota, 0, None)
            raices = np.zeros_like(t)
            for ci, chord in enumerate(chords):
                mask = chord_i == ci
                raices += mask * np.take(np.asarray(chord) * 2, oct_i % len(chord))
            env_a = np.where(fase_nota < .008, np.clip(fase_nota / .008, 0, 1),
                             np.exp(-(fase_nota - .008) / .15))
            arpegio = (np.sin(2 * np.pi * raices * t)
                       + .45 * np.sin(2 * np.pi * raices * 2.003 * t)
                       + .18 * np.sin(2 * np.pi * raices * 4.01 * t))
            arpegio *= .042 * cfg["arpegio"] * cfg["brillo"] * energia * env_a

            # melodía: motivo de 8 notas cada 2 compases, con campanita
            fase_motivo = t % (beat * 16)
            paso = (fase_motivo / beat).astype(np.int64)
            mf = np.take(melody, (bar + paso) % len(melody))
            mp = fase_motivo % beat
            me = np.where(mp < .015, np.clip(mp / .015, 0, 1), np.exp(-(mp - .015) / .28))
            campana = np.sin(2 * np.pi * mf * t) + .5 * np.sin(2 * np.pi * mf * 3.01 * t) * np.exp(-mp / .1)
            motivo = (paso < 8) * .030 * cfg["brillo"] * energia * me * campana

            # ritmo: bombo + caja/chasquido
            if es_vals:
                golpes = np.isin(beat_i % 3, [0])
                caja = np.isin(beat_i % 3, [1, 2])
            else:
                golpes = np.isin(beat_i % 4, [0, 2])
                caja = np.isin(beat_i % 4, [1, 3])
            bombo = golpes * np.sin(2 * np.pi * (55 + 50 * np.exp(-beat_phase / .03)) * t) \
                * np.exp(-beat_phase / .12) * .065 * pulso
            ruido = rng.uniform(-1, 1, len(t))
            caja_s = caja * ruido * np.exp(-beat_phase / .04) * .020 * pulso

            fi = np.clip(t / 2.5, 0, 1)
            fi = fi * fi * (3 - 2 * fi)
            fo = np.clip((dur - t) / 6.0, 0, 1)
            fo = fo * fo * (3 - 2 * fo)
            master = fi * fo

            izq = np.tanh((pad_l + bajo + arpegio * .92 + motivo * 1.05 + bombo + caja_s) * 1.5) * .70 * master
            der = np.tanh((pad_r + bajo + arpegio * 1.08 + motivo * .95 + bombo + caja_s * .8) * 1.5) * .70 * master
            estereo = np.column_stack((izq, der))
            wav.writeframesraw((np.clip(estereo, -1, 1) * 32767).astype("<i2").tobytes())
    print(salida)


if __name__ == "__main__":
    render(sys.argv[1], float(sys.argv[2]), sys.argv[3])
