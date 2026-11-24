"""Place each English syllable and consonant on the notated melody."""
from dataclasses import dataclass
from functools import lru_cache
import re

import cmudict
import numpy as np

from .song_score import SINGER_HOP, SINGER_RATE


# Letter names and the sung two-syllable pronunciation of "every".
OVERRIDES = {
    "gpu": "JH IY1 P IY1 Y UW1", "gpus": "JH IY1 P IY1 Y UW1 Z",
    "itletters": "AY1 T IY1", "every": "EH1 V R IY0", "concrete": "K AA1 N K R IY0 T",
    "consoles": "K AA1 N S OW2 L Z",
}
ONSET_PAIRS = set("br bl dr dw fl fr gl gr kl kr kw pl pr sk sl sm sn sp st sw tr tw thr shr".split())
SIBILANTS = {"s", "z", "sh", "zh", "f", "v", "th", "dh"}
STOPS = {"k", "t", "p", "g", "d", "b", "ch", "jh"}


@lru_cache(maxsize=1)
def dictionary():
    return cmudict.dict()


def syllables(text):
    result = []
    for word in re.findall(r"[a-z]+", text.lower().replace("i.t.", "itletters")):
        raw = OVERRIDES.get(word)
        if raw:
            phones = raw.split()
        else:
            try:
                phones = dictionary()[word][0]
            except KeyError as exc:
                raise ValueError(f"Missing pronunciation for {word}") from exc
        vowels = [i for i, p in enumerate(phones) if p[-1].isdigit()]
        starts = [0]
        for first, second in zip(vowels, vowels[1:]):
            gap = [p.lower() for p in phones[first+1:second]]
            onset = min(1, len(gap))
            if len(gap) >= 2 and "".join(gap[-2:]) in ONSET_PAIRS:
                onset = 2
            if len(gap) >= 3 and gap[-3] == "s" and "".join(gap[-2:]) in ONSET_PAIRS:
                onset = 3
            starts.append(second-onset)
        for start, end in zip(starts, (*starts[1:], len(phones))):
            unit = phones[start:end]
            nucleus = next(i for i, p in enumerate(unit) if p[-1].isdigit())
            normal = [("ax" if p == "AH0" else re.sub(r"[012]$", "", p).lower()) for p in unit]
            result.append((normal, nucleus))
    return result


def consonant_time(phone):
    if phone in SIBILANTS:
        return .063
    if phone in STOPS:
        return .042
    return .048


@dataclass
class Syllable:
    phones: list
    nucleus: int
    beat: float
    begin: float
    finish: float
    pitch: int


def lower_harmony(pitch, chord):
    # Sing a diatonic lower third, with a leading tone over the dominant.
    pcs = (0, 2, 4, 5, 7, 9, 10) if chord != "A7" else (1, 2, 4, 5, 7, 9, 10)
    lower = [key for key in range(pitch-7, pitch) if key % 12 in pcs]
    return lower[-2]


def score_phrase(bars, harmony=False):
    notes = []
    for bar in bars:
        units = syllables(bar.lyric)
        if len(units) != len(bar.notes):
            raise ValueError(f"Bar {bar.number}, {bar.lyric!r}: {len(units)} syllables, {len(bar.notes)} notes")
        for i, ((phones, nucleus), (tick, pitch)) in enumerate(zip(units, bar.notes)):
            beat = bar.seconds(tick)
            end = bar.seconds(bar.notes[i+1][0] if i+1 < len(units) else bar.release)
            lead = min(.100, sum(consonant_time(p) for p in phones[:nucleus]), (end-beat)*.33)
            if harmony:
                pitch = lower_harmony(pitch, bar.chord)
            notes.append(Syllable(phones, nucleus, beat, max(.003, beat-lead), end, pitch))
    return notes


def apportion(seconds, frames):
    values = np.asarray(seconds, dtype=float) / sum(seconds) * frames
    lengths = np.maximum(1, np.floor(values).astype(int))
    if frames < len(lengths):
        raise ValueError("Too little time to pronounce this syllable")
    while lengths.sum() < frames:
        lengths[np.argmax(values-lengths)] += 1
    while lengths.sum() > frames:
        lengths[np.argmax(np.where(lengths > 1, lengths-values, -np.inf))] -= 1
    return lengths.tolist()


def prepare(bars, harmony=False):
    notes = score_phrase(bars, harmony)
    frame = SINGER_HOP / SINGER_RATE
    offset = notes[0].begin - .17
    tick = lambda t: round((t-offset)/frame)
    phones, durations = ["SP"], [tick(notes[0].begin)]
    for i, n in enumerate(notes):
        end = min(n.finish, notes[i+1].begin) if i+1 < len(notes) else n.finish
        beginning = tick(n.begin)
        gap = beginning - sum(durations)
        if gap > 0:
            phones.append("SP")
            durations.append(gap)
        lead = n.beat - n.begin
        attack = np.array([consonant_time(p) for p in n.phones[:n.nucleus]])
        if len(attack):
            attack = attack / attack.sum() * lead
        coda = np.array([consonant_time(p) for p in n.phones[n.nucleus+1:]])
        if len(coda):
            coda *= min(1., (end-n.beat)*.42 / coda.sum())
        vowel = max(frame, end-n.begin - attack.sum()-coda.sum())
        weights = [*attack, vowel, *coda]
        lengths = apportion(weights, tick(end)-beginning)
        phones.extend(n.phones)
        durations.extend(lengths)
    phones.append("SP")
    durations.append(17)
    t = offset + (np.arange(sum(durations))+.5)*frame
    pitches = np.full_like(t, notes[0].pitch, dtype=float)
    for i, n in enumerate(notes):
        if i == 0:
            start = n.beat-.06
            window = np.clip((t-start)/.10, 0., 1.)
            pitches += -.32*(1-window)
        else:
            previous = notes[i-1]
            slide = min(.092, .29*(n.finish-n.beat), .35*(previous.finish-previous.beat))
            u = np.clip((t-(n.beat-.62*slide))/slide, 0., 1.)
            pitches += (n.pitch-previous.pitch) * (u*u*(3-2*u))
        hold = t-n.beat
        active = (hold > 0) & (t < n.finish)
        depth = np.clip((hold-.105)*.54, 0., .17) * active
        pitches += depth*np.sin(2*np.pi*(5.35 if not harmony else 5.08)*hold+.61*i)
    return offset, phones, np.array(durations, dtype=np.int64)[None], pitches.astype(np.float32)[None]
