"""Read the English song score against the 24 fps GPU Silo short."""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import re
import textwrap

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "audio" / "short_song" / "score.txt"
FPS = 24
PICTURE_FRAMES = 2917
FIRST_DOWNBEAT = Fraction(7, FPS)
BEAT = Fraction(1, 2)
DURATION = Fraction(PICTURE_FRAMES, FPS)
RECORDING_RATE = 48000
SINGER_RATE = 44100
SINGER_HOP = 512
# The voice takes a breath between these phrases. Each component study begins a new phrase.
PHRASE_STARTS = (0, 1, 3, 5, 6, 8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 26,
                 28, 30, 33, 35, 36, 38, 39, 40, 41, 43, 46, 49, 52, 55, 57, 59)


@dataclass(frozen=True)
class Bar:
    number: int
    chord: str
    lyric: str
    # Positions in sixteenths, pitches in MIDI semitones.
    notes: tuple
    release: float

    def seconds(self, position=0.0):
        return float(FIRST_DOWNBEAT) + self.number * 2.0 + position / 8.0

    @property
    def start(self):
        return self.seconds(self.notes[0][0])

    @property
    def end(self):
        return self.seconds(self.release)


def midi(note):
    match = re.fullmatch(r"([A-G])([#b]?)([0-8])", note)
    if not match:
        raise ValueError(f"Invalid note {note}")
    letter, accidental, octave = match.groups()
    return (int(octave) + 1) * 12 + {"C": 0, "D": 2, "E": 4, "F": 5,
           "G": 7, "A": 9, "B": 11}[letter] + {"#": 1, "b": -1, "": 0}[accidental]


def read(path=SCORE):
    bars = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        number, chord, lyric, notation = [part.strip() for part in line.split("|")]
        if int(number) != len(bars):
            raise ValueError(f"Nonconsecutive bar {number}")
        if notation == "-":
            bars.append(Bar(int(number), chord, "", (), 0))
            continue
        *events, end = notation.split()
        notes = []
        for event in events:
            onset, pitch = event.split(":")
            notes.append((float(onset), midi(pitch)))
        positions = [onset for onset, _ in notes] + [float(end)]
        if any(x >= y for x, y in zip(positions, positions[1:])):
            raise ValueError(f"Overlapping notes in bar {number}")
        bar = Bar(int(number), chord, lyric, tuple(notes), float(end))
        if bar.end > float(DURATION):
            raise ValueError(f"Lyric extends past the orbit in bar {number}")
        bars.append(bar)
    if len(bars) != 61:
        raise ValueError("The orbit ends in bar 60")
    sung = [b for b in bars if b.notes]
    if any(a.end > b.start for a, b in zip(sung, sung[1:])):
        raise ValueError("Overlapping vocal lines")
    return bars


def timestamp(seconds):
    millis = round(seconds * 1000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def captions(bars):
    # The 3-bar IFC studies have separate subtitle groups, as does the closing hook.
    entries = []
    for i, (first, stop) in enumerate(zip(PHRASE_STARTS, (*PHRASE_STARTS[1:], len(bars))), 1):
        part = [b for b in bars[first:stop] if b.notes]
        text = " ".join(b.lyric for b in part)
        # Keep numeric phrases and the letters GPU together.
        wrapped = "\n".join(textwrap.wrap(text, width=48, break_long_words=False, break_on_hyphens=False))
        entries.append(f"{i}\n{timestamp(part[0].start)} --> {timestamp(part[-1].end)}\n{wrapped}")
    return "\n\n".join(entries) + "\n"
