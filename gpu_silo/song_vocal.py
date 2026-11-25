"""Perform the English upper octave and chorus harmonies with Chiaki's DiffSinger models."""
import argparse
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import soundfile as sf
import yaml

from .song_diction import prepare
from .song_score import DURATION, PHRASE_STARTS, SINGER_HOP, SINGER_RATE, read
HARMONIES = (8, 9, 39, 40, 59)


def config(directory, name="dsconfig.yaml"):
    return yaml.safe_load((directory/name).read_text(encoding="utf-8-sig"))


def bank_parameters(directory, settings):
    table = json.loads((directory/settings["phonemes"]).read_text(encoding="utf-8-sig"))
    languages = json.loads((directory/settings["languages"]).read_text(encoding="utf-8-sig"))
    embed = np.fromfile(directory/(settings["speakers"][0]+".emb"), dtype="<f4")
    if len(embed) != settings["hidden_size"]:
        raise ValueError("Speaker embedding dimensions differ from the bank configuration")
    return table, languages["en"], embed


def tokens(phones, table, english):
    ids = [table["en/"+p] if "en/"+p in table else table[p] for p in phones]
    langs = [0 if p in ("SP", "AP") else english for p in phones]
    return np.array([ids], np.int64), np.array([langs], np.int64)


class Singer:
    def __init__(self, bank):
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        opts.inter_op_num_threads = 1
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        opts.log_severity_level = 3

        def session(path):
            return ort.InferenceSession(str(path), sess_options=opts, providers=["CPUExecutionProvider"])

        acoustic = config(bank)
        varn = bank/"dsvariance"
        variance = config(varn)
        voc = bank/acoustic["vocoder"]
        vocoder = config(voc, "vocoder.yaml")
        if any(c["sample_rate"] != SINGER_RATE or c["hop_size"] != SINGER_HOP for c in (acoustic, variance, vocoder)):
            raise ValueError("The score uses the 44.1 kHz / 512-hop Chiaki voicebank")
        self.acoustic_bank = bank_parameters(bank, acoustic)
        self.variance_bank = bank_parameters(varn, variance)
        self.linguistic = session(varn/variance["linguistic"])
        self.variance = session(varn/variance["variance"])
        self.acoustic = session(bank/acoustic["acoustic"])
        self.vocoder = session(voc/vocoder["model"])
        self.depth = np.array(acoustic["max_depth"], np.float32)

    def sing(self, phones, durations, pitch):
        n = pitch.shape[1]
        def speaker(embed):
            return np.broadcast_to(embed, (1, n, len(embed))).copy()
        table, en, embed = self.variance_bank
        ids, langs = tokens(phones, table, en)
        encoder, = self.linguistic.run(["encoder_out"], {"tokens":ids, "languages":langs, "ph_dur":durations})
        blank = np.zeros_like(pitch)
        breath, tension = self.variance.run(["breathiness_pred", "tension_pred"], {
            "encoder_out":encoder, "ph_dur":durations, "pitch":pitch, "breathiness":blank, "tension":blank,
            "retake":np.ones((1,n,2), dtype=bool), "spk_embed":speaker(embed), "steps":np.array(40,np.int64)})
        table, en, embed = self.acoustic_bank
        ids, langs = tokens(phones, table, en)
        pitch_hz = (440*np.exp2((pitch-69)/12)).astype(np.float32)
        mel, = self.acoustic.run(["mel"], {
            "tokens":ids, "languages":langs, "durations":durations, "f0":pitch_hz, "tension":tension,
            "breathiness":breath, "velocity":np.ones_like(pitch), "gender":blank, "spk_embed":speaker(embed),
            "depth":self.depth, "steps":np.array(20,np.int64)})
        wav, = self.vocoder.run(["waveform"], {"mel":mel, "f0":pitch_hz})
        mono = np.asarray(wav, np.float32).reshape(-1)
        if len(mono) != n*SINGER_HOP or not np.isfinite(mono).all() or np.max(np.abs(mono)) < .001:
            raise ValueError("The singing model returned an invalid waveform")
        # The surrounding silence is only inference context. Taper its outer edge before assembly.
        count = min(480, len(mono)//4)
        mono[:count] *= np.linspace(0,1,count)
        mono[-count:] *= np.linspace(1,0,count)
        return mono


def render(bank, work, selected=None):
    bars = read()
    work.mkdir(parents=True, exist_ok=True)
    parts = work/"vocal-parts"
    parts.mkdir(exist_ok=True)
    voice = None
    size = round(float(DURATION)*SINGER_RATE)
    for harmony in (False, True):
        role = "harmony" if harmony else "lead"
        output = np.zeros(size, np.float32)
        for first, last in zip(PHRASE_STARTS, (*PHRASE_STARTS[1:], len(bars))):
            if harmony and first not in HARMONIES or selected is not None and first not in selected:
                continue
            part = [b for b in bars[first:last] if b.notes]
            offset, phones, durations, pitch = prepare(part, harmony)
            path = parts/f"{role}-{first:02}.wav"
            if not path.is_file():
                if voice is None:
                    voice = Singer(bank)
                ort.set_seed(1776+first+100*int(harmony))
                mono = voice.sing(phones, durations, pitch)
                temp = path.with_suffix(".partial.wav")
                sf.write(temp, mono, SINGER_RATE, subtype="FLOAT")
                temp.replace(path)
                print(f"{role} bar {first:02}  {part[0].lyric}", flush=True)
            mono, rate = sf.read(path, dtype="float32")
            if rate != SINGER_RATE or len(mono) != int(durations.sum())*SINGER_HOP:
                raise ValueError(f"Stale vocal part {path}; use a fresh work directory")
            start = round(offset*SINGER_RATE)
            left, right = max(0,start), min(size,start+len(mono))
            output[left:right] += mono[left-start:right-start]
        if selected is None:
            sf.write(work/f"{role}.wav", output, SINGER_RATE, subtype="FLOAT")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bank", type=Path)
    parser.add_argument("work", type=Path)
    parser.add_argument("--phrases", nargs="+", type=int)
    args = parser.parse_args()
    render(args.bank, args.work, set(args.phrases) if args.phrases else None)
