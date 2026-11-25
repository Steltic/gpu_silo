"""Sing the notated English tenor line with Kokoro's open duration and harmonic-source controls."""
import argparse
import json
from pathlib import Path
import re

import numpy as np
import onnx
from onnx import TensorProto, helper
import onnxruntime as ort
import soundfile as sf

from .song_diction import prepare, score_phrase
from .song_score import DURATION, PHRASE_STARTS, ROOT, SINGER_HOP, SINGER_RATE, read

RATE = 24000
UNIT = 600  # Kokoro duration frames; its F0 control runs twice as fast.
PREROLL = .60
VOWELS = set("aeiouɑɐɒæɔəɚɛɜɪʊʌᵻ")
LEXICON = ROOT/"audio"/"short_song"/"english_diction.json"


def token_times(chars, native, frames):
    # Preserve the model's English articulation. Held notes stretch mostly across the vowels.
    values = np.array(native, dtype=float)
    minimum = np.ones(len(chars), dtype=int)
    for i in sorted(range(len(chars)), key=lambda j: chars[j] not in " ˈˌː"):
        if minimum.sum() <= frames:
            break
        minimum[i] = 0
    if frames > values.sum():
        hold = np.array([float(c in VOWELS) for c in chars])
        hold /= max(hold.sum(), 1)
        values += (frames-values.sum()) * (.48*values/values.sum() + .52*hold)
    ideal = values * frames / values.sum()
    counts = np.maximum(np.floor(ideal).astype(int), minimum)
    while counts.sum() < frames:
        counts[np.argmax(ideal-counts)] += 1
    while counts.sum() > frames:
        counts[np.argmax(np.where(counts > minimum, counts-ideal, -np.inf))] -= 1
    return counts.tolist()


def score_graph(path, cache):
    if cache.is_file():
        return
    model = onnx.load(str(path))
    graph = model.graph
    nodes = {n.name:n for n in graph.node}
    durations = nodes["/encoder/Cast"].output[0]
    f0 = nodes["/encoder/Reshape"].output[0]
    align = nodes["/encoder/Gather"]
    excite = nodes["/decoder/decoder/Unsqueeze"]
    if align.input[0] != durations or excite.input[0] != f0:
        raise ValueError("Expected the published Kokoro v1.0 ONNX graph")
    graph.input.extend([helper.make_tensor_value_info("note_durations",TensorProto.INT64,[1,"phones"]),
                        helper.make_tensor_value_info("note_f0",TensorProto.FLOAT,[1,"pitch_frames"])])
    graph.output.extend([helper.make_tensor_value_info(durations,TensorProto.INT64,[1,"phones"]),
                         helper.make_tensor_value_info(f0,TensorProto.FLOAT,[1,"pitch_frames"])])
    # Only the score alignment and pitch going into the decoder change. Learned weights are untouched.
    align.input[0] = "note_durations"
    excite.input[0] = "note_f0"
    onnx.save(model, str(cache))


class EnglishTenor:
    def __init__(self, models, work):
        export = work/"kokoro-scored.onnx"
        score_graph(models/"kokoro-v1.0.onnx", export)
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        opts.inter_op_num_threads = 1
        opts.log_severity_level = 3
        opts.add_session_config_entry("session.intra_op.allow_spinning","0")
        self.engine = ort.InferenceSession(str(export),sess_options=opts,providers=["CPUExecutionProvider"])
        self.fetch = ort.RunOptions()
        self.fetch.only_execute_path_to_fetches = True
        self.styles = np.load(models/"voices-v1.0.bin")["am_michael"]
        lexicon = json.loads(LEXICON.read_text(encoding="utf-8"))
        self.words, self.vocab = lexicon["words"], lexicon["tokens"]

    def perform(self, bars):
        scored = score_phrase(bars)
        units = []
        for bar in bars:
            for word in re.findall(r"[a-z]+",bar.lyric.lower().replace("i.t.","itletters")):
                for j, syl in enumerate(self.words[word]):
                    units.append((" " if j == 0 and units else "")+syl)
        if len(units) != len(scored):
            raise ValueError(f"English underlay differs in bar {bars[0].number}")
        offset = scored[0].begin-PREROLL
        def at(seconds):
            return round((seconds-offset)*RATE/UNIT)
        # Give the decoder a vowel to establish its voice before the first lyric pickup.
        # It is removed from the isolated vocal take before the take enters the mix.
        ids = [0, self.vocab["ə"], self.vocab[","], self.vocab[" "]]
        plan = [(0,1,5,None), (1,2,8,None), (2,3,8,None), (3,4,3,None)]
        pos = sum(row[2] for row in plan)
        for i, (note, chars) in enumerate(zip(scored, units)):
            start = at(note.begin)
            if start > pos:
                ids.append(self.vocab[","])
                plan.append((len(ids)-1,len(ids),start-pos,None))
            end = note.finish if i+1==len(scored) else min(note.finish,scored[i+1].begin)
            pos = at(end)
            first = len(ids)
            ids.extend(self.vocab[c] for c in chars)
            plan.append((first,len(ids),pos-start,chars))
        ids.append(0)
        plan.append((len(ids)-1,len(ids),8,None))
        ids = np.array([ids],np.int64)
        inputs = {"tokens":ids, "style":self.styles[min(ids.shape[1]-2,509)], "speed":np.array([1],np.float32),
                  "note_durations":np.ones_like(ids), "note_f0":np.zeros((1,2*ids.size),np.float32)}
        natural, = self.engine.run(["/encoder/Cast_output_0"],inputs,self.fetch)
        durations = []
        for lo, hi, count, chars in plan:
            durations.extend([int(count)] if chars is None else token_times(chars,natural[0,lo:hi],count))
        inputs["note_durations"] = np.array([durations],np.int64)
        frames = sum(durations)*2
        inputs["note_f0"] = np.zeros((1,frames),np.float32)
        original, = self.engine.run(["/encoder/Reshape_output_0"],inputs,self.fetch)
        if original.size != frames:
            raise ValueError(f"Unexpected F0 frame rate {original.shape}, expected {frames}")
        # Give the native English formants a tenor melody one octave below the written treble line.
        ds_offset, _, _, treble = prepare(bars)
        seconds = offset + (np.arange(frames)+.5)*UNIT/(RATE*2)
        ds_seconds = ds_offset + (np.arange(treble.size)+.5)*SINGER_HOP/SINGER_RATE
        midi = np.interp(seconds,ds_seconds,treble[0])-12
        hz = 440*np.exp2((midi-69)/12)
        voicing = np.clip((original-10)/50,0,1)
        inputs["note_f0"] = (voicing*hz[None,:]+(1-voicing)*original).astype(np.float32)
        audio, = self.engine.run(["audio"],inputs,self.fetch)
        wave = audio.ravel()
        if abs(len(wave)-sum(durations)*UNIT)>UNIT or not np.isfinite(wave).all():
            raise ValueError(f"Unexpected tenor waveform of {len(wave)} samples")
        taper = np.linspace(0,1,240)
        gate = round((PREROLL-.035)*RATE)
        wave[:gate] = 0
        wave[gate:gate+240] *= taper
        wave[-240:] *= taper[::-1]
        return offset, wave


def render(models, work, selected=None):
    bars = read()
    parts = work / "tenor-parts"
    parts.mkdir(exist_ok=True, parents=True)
    voice = EnglishTenor(models, work)
    track = np.zeros(int(DURATION * RATE), np.float32)
    for start, stop in zip(PHRASE_STARTS, (*PHRASE_STARTS[1:], len(bars))):
        if selected is not None and start not in selected:
            continue
        part = [b for b in bars[start:stop] if b.notes]
        path = parts / f"tenor-{start:02}.wav"
        offset = score_phrase(part)[0].begin - PREROLL
        if path.is_file():
            wave, rate = sf.read(path, dtype="float32")
            if rate != RATE:
                raise ValueError(f"Unexpected sample rate in {path}")
        else:
            ort.set_seed(901+start)
            offset, wave = voice.perform(part)
            tmp = path.with_suffix(".partial.wav")
            sf.write(tmp, wave, RATE, subtype="FLOAT")
            tmp.replace(path)
            print(f"Tenor bar {start:02}  {part[0].lyric}", flush=True)
        index = round(offset * RATE)
        left, right = max(0, index), min(len(track), index+len(wave))
        track[left:right] += wave[left-index:right-index]
    if selected is None:
        sf.write(work / "tenor.wav", track, RATE, subtype="FLOAT")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", type=Path)
    parser.add_argument("work", type=Path)
    parser.add_argument("--phrases", nargs="+", type=int)
    args = parser.parse_args()
    render(args.models, args.work, set(args.phrases) if args.phrases else None)
