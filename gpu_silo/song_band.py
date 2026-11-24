"""Play the original dance-band and orchestral arrangement from the short-song score."""
import argparse
from pathlib import Path
import random

import numpy as np
import soundfile as sf
import tinysoundfont

from .song_score import DURATION, FIRST_DOWNBEAT, RECORDING_RATE, read

# GM bank, preset, pan and volume. The mandolin and Italian accordion are GeneralUser variations.
PATCHES = {
    "bass": (0, 33, 64, 112), "sub": (0, 38, 64, 85),
    "guitar": (0, 24, 43, 103), "mandolin": (16, 25, 86, 107),
    "accordion": (8, 21, 75, 98), "piano": (0, 0, 38, 94),
    "strings": (0, 49, 48, 112), "horns": (0, 60, 75, 111),
    "cello": (0, 42, 52, 104), "kit": (128, 0, 64, 115),
    "brass": (0, 61, 67, 106), "harp": (0, 46, 88, 100),
    "timpani": (0, 47, 55, 115), "violins": (0, 48, 40, 107),
}
CHANNEL = {name: i for i, name in enumerate(PATCHES)}
HARMONY = {
    "Dm": (38, (53, 57, 62, 65)), "Bb": (34, (53, 58, 62, 65)),
    "F": (41, (53, 57, 60, 65)), "A7": (33, (52, 55, 57, 61)),
    "Gm": (31, (50, 55, 58, 62)), "C": (36, (52, 55, 60, 64)),
    "D": (38, (54, 57, 62, 66)),
}
RHYTHM = {"bass", "sub", "kit"}
BAND = {"guitar", "mandolin", "accordion", "piano"}


def arrangement(bars):
    rng = random.Random(1746)
    events = []

    def note(inst, beat, length, key, velocity, scatter=0):
        # Express the score in quarter notes. Only the players drift a few milliseconds.
        time = float(FIRST_DOWNBEAT) + beat * .5 + rng.uniform(-scatter, scatter)
        onset = max(0, round(RECORDING_RATE * time))
        release = max(onset + 1, round(RECORDING_RATE * (time + length * .5)))
        vel = int(np.clip(velocity + rng.randint(-3, 3), 8, 123))
        events.extend(((onset, 1, inst, key, vel), (release, 0, inst, key, 0)))

    def strum(inst, beat, length, keys, velocity, up=False):
        for j, key in enumerate(reversed(keys) if up else keys):
            note(inst, beat + .013*j, length, key, velocity - 2*j, .002)

    def drum(beat, key, velocity, length=.15):
        note("kit", beat, length, key, velocity, .002 if key != 36 else 0)

    # A mandolin pickup answers the first sung word.
    note("mandolin", -.53, .18, 69, 87)
    note("mandolin", -.28, .22, 72, 92)
    for b in bars:
        i = b.number
        root, keys = HARMONY[b.chord]
        beat = i * 4
        if i == 60:
            # Picardy third. Leave 1.25 seconds of picture for the chord and room decay.
            for inst, pitches, velocity, hold in (
                ("strings", (57, 62, 66, 74), 102, 1.55), ("violins", (78, 81), 81, 1.35),
                ("horns", (50, 57, 62), 109, 1.45), ("brass", (62, 66, 69), 99, 1.3),
                ("cello", (38, 50), 111, 1.55), ("timpani", (38,), 119, 1.4),
                ("piano", (38, 50, 57, 62, 66, 74), 98, 1.1),
            ):
                strum(inst, beat, hold, pitches, velocity)
            drum(beat, 49, 107, 1.65)
            note("bass", beat, 1.6, 38, 111)
            for j, p in enumerate((50, 57, 62, 66, 69, 74, 78, 81)):
                note("harp", beat + j*.091, .67, p, 82 - j)
            continue

        hook = i in (0, 8, 9, 39, 40, 59)
        studio = 43 <= i < 55
        finale = i >= 55
        sparse = i in (10, 24, 30, 41, 43, 49, 54)
        lift = i in (7, 15, 23, 32, 35, 42, 54, 58, 59)
        # Drum kit and a walking electric bass over a four-on-the-floor foundation.
        if i != 59:
            for j in ((0, 2) if sparse else (0, 1, 2, 3)):
                drum(beat + j, 36, 109 if j == 0 else 99)
            for j in (1, 3):
                drum(beat + j + .014, 38, 72 if sparse else 87)
                if hook or i >= 32:
                    drum(beat + j + .027, 39, 79 if not finale else 87)
            for j in range(8):
                if sparse and j % 2 == 0:
                    continue
                drum(beat + j*.5 + (.025 if j % 2 else 0), 42 if j != 7 or sparse else 46,
                     (47 if j % 2 == 0 else 69) + (5 if finale else 0), .12 if j != 7 else .22)
            if 8 <= i < 24 or 33 <= i < 43 or finale:
                for j in (.51, 1.53, 2.53, 3.54):
                    drum(beat + j, 54, 62)
        if lift:
            for j in range(4 if not finale else 8):
                inc = .25 if not finale else .125
                drum(beat + 3 + j*inc, 38, 43 + j*(8 if not finale else 7), .10)
        if i in (8, 16, 22, 33, 36, 43, 52, 55):
            drum(beat, 49 if i in (36, 55) else 51, 82, .8)
        steps = ((0, root, .68), (.76, root+12, .20), (1.47, root+7, .42),
                 (2, root, .60), (2.78, root+12, .17), (3.49, root+7, .39))
        if sparse:
            steps = ((0, root, 1.35), (2.5, root+7, .72))
        if i == 59:
            steps = ((0, root, 1.45), (2, root+12, .44), (3, root+12, .42))
        for j, (offset, pitch, hold) in enumerate(steps):
            note("bass", beat+offset, hold, pitch, 106 if j == 0 else 85, .003)
        for off in ((0, 2) if not sparse else (0,)):
            sub = root if root < 35 else root - 12
            note("sub", beat+off, .68 if not finale else 1.25, sub, 82)

        # Chopped guitar and piano leave the centre free for the sung numbers.
        for j, off in enumerate((.5, 1.5, 2.5, 3.5)):
            if sparse and j not in (1, 3) or i == 59 and j > 0:
                continue
            strum("guitar", beat+off+.016, .23 if j % 2 else .32, keys[:3], 88, j % 2 == 0)
        if hook or 16 <= i <= 23 or 36 <= i <= 40 or finale:
            for j in (0, 1.5, 3):
                strum("piano", beat+j, .38, (keys[0], keys[2], keys[1]+12), 62 if not finale else 75)
        if not finale and not studio:
            for j in ((.51, 2.52) if not hook else (.50, 1.50, 2.50, 3.50)):
                strum("accordion", beat+j, .32, (keys[1]+12, keys[2]+12), 59)
        # Single-note mandolin responses and paired-course tremolos between vocal phrases.
        if i % 2 == 1 or sparse:
            picks = (keys[3]+12, keys[2]+12, keys[1]+12, keys[2]+12)
            for j, pitch in enumerate(picks):
                if not finale:
                    note("mandolin", beat+2.53+j*.33, .25, pitch, 68+4*j, .004)
        if i in (5, 7, 9, 15, 19, 23, 27, 32, 35, 40, 45, 48, 51, 54):
            for j, (off, p) in enumerate(((2.48, keys[1]+12), (2.82, keys[2]+12),
                                          (3.11, keys[3]+12), (3.65, keys[2]+12))):
                note("accordion", beat+off, .27 if j != 3 else .32, p, 78 + 3*j, .004)

        # A distinct colour for each of the four three-bar IFC reveals.
        if studio and (i-43) % 3 == 0:
            inst = ("cello", "harp", "mandolin", "horns")[(i-43)//3]
            for j, p in enumerate((keys[0], keys[1], keys[2], keys[3])):
                note(inst, beat+j*.33, .74, p+(12 if inst in ("harp", "mandolin") else 0), 77-j*2)
        if i in (36, 37, 38, 39, 40, 52, 53, 54):
            strum("strings", beat+.04, 3.65, (keys[0]+12, keys[2]+12), 55 + (i % 3)*4)
        if not finale:
            continue

        # The orbit grows from cello ostinato to full strings, horns, brass and timpani.
        strength = i - 55
        strum("strings", beat, 3.94, (keys[0]+12, keys[1]+12, keys[3]+12), 78+4*strength)
        for j in range(8):
            pitch = (keys[0], keys[1], keys[2], keys[1])[j % 4]
            note("cello", beat+j*.5, .34, pitch-12, 77+3*strength + (10 if j % 2 == 0 else 0))
        if strength >= 1:
            for off, pitch, length in ((0, keys[1], 1.40), (1.5, keys[2], .43), (2, keys[3], 1.84)):
                note("horns", beat+off, length, pitch, 86+4*strength)
        if strength >= 2:
            for j in range(8):
                p = (keys[1]+12, keys[2]+12, keys[3]+12, keys[2]+12)[j % 4]
                note("violins", beat+j*.5, .37, p + (12 if i == 59 and j > 3 else 0), 74+3*strength)
            for off in (0, 2.5):
                strum("brass", beat+off, .56, (keys[0], keys[2], keys[3]), 77+3*strength)
        if i in (55, 57, 58):
            for off in (0, 2):
                note("timpani", beat+off, .61, root, 95+strength)
        if i == 59:
            for j in range(12):
                note("timpani", beat+1+j*.25, .19, 45, 50+j*5)
            # Sweep into the bright D-major downbeat with a harp glissando.
            for j, p in enumerate((45, 49, 52, 55, 57, 61, 64, 67, 69, 73, 76, 79)):
                note("harp", beat+2.51+j*.125, .42, p, 65+j*2)
    return sorted(events)


def render_stem(events, selected, font, path):
    synth = tinysoundfont.Synth(gain=-8, samplerate=RECORDING_RATE)
    sfid = synth.sfload(str(font), max_voices=256)
    for name in selected:
        bank, preset, pan, level = PATCHES[name]
        channel = CHANNEL[name]
        synth.program_select(channel, sfid, bank, preset, is_drums=name == "kit")
        synth.control_change(channel, 10, pan)
        synth.control_change(channel, 7, level)
    total = int(DURATION * RECORDING_RATE)
    position = 0
    with sf.SoundFile(path, "w", RECORDING_RATE, 2, subtype="FLOAT") as out:
        def render_to(stop):
            nonlocal position
            while position < stop:
                count = min(16384, stop-position)
                samples = np.frombuffer(synth.generate_simple(count), np.float32).reshape(-1, 2)
                out.write(samples)
                position += count
        for sample, attack, inst, pitch, velocity in events:
            if inst not in selected or sample >= total:
                continue
            render_to(sample)
            if attack:
                synth.noteon(CHANNEL[inst], pitch, velocity)
            else:
                synth.noteoff(CHANNEL[inst], pitch)
        render_to(total)


def render(font, work):
    work.mkdir(parents=True, exist_ok=True)
    events = arrangement(read())
    for name, instruments in (("rhythm", RHYTHM), ("band", BAND), ("orchestra", set(PATCHES)-BAND-RHYTHM)):
        render_stem(events, instruments, font, work/f"{name}.wav")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("soundfont", type=Path)
    parser.add_argument("work", type=Path)
    args = parser.parse_args()
    render(args.soundfont, args.work)
