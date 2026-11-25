"""Mix the English vocal, Italian dance band and the orchestral orbit, then master to stereo FLAC."""
import argparse
import json
from pathlib import Path
import re
import subprocess

import numpy as np
from scipy import signal
import soundfile as sf

from .song_score import DURATION, FIRST_DOWNBEAT, RECORDING_RATE, read

RATE = RECORDING_RATE
LENGTH = int(DURATION * RATE)


def load_track(path, stereo=True):
    wave, rate = sf.read(path, dtype="float32", always_2d=True)
    if rate != RATE:
        from math import gcd
        divisor = gcd(rate, RATE)
        wave = signal.resample_poly(wave, RATE//divisor, rate//divisor, axis=0).astype("float32")
    if abs(len(wave)-LENGTH) > 2:
        raise ValueError(f"Unexpected length for {path}")
    wave = np.pad(wave[:LENGTH], ((0, max(0, LENGTH-len(wave))), (0, 0)))
    if stereo and wave.shape[1] != 2:
        raise ValueError(f"Expected a stereo stem for {path}")
    return wave


def highpass(wave, hz):
    filt = signal.butter(2, hz, "highpass", fs=RATE, output="sos").astype("float32")
    return signal.sosfilt(filt, wave, axis=0)


def meter(wave, block=240):
    pad = (-len(wave)) % block
    frames = np.pad(wave, ((0, pad), (0, 0))).reshape(-1, block, wave.shape[1])
    return np.maximum(1.e-8, np.mean(frames*frames, axis=(1,2))**.5)


def smoothed(values, attack=.016, release=.12, block=240):
    fast = np.exp(-block/(attack*RATE))
    slow = np.exp(-block/(release*RATE))
    current = 0.
    result = []
    for target in values:
        coefficient = fast if target > current else slow
        current = coefficient*current+(1-coefficient)*target
        result.append(current)
    samples = np.arange(LENGTH, dtype=np.float32)
    return np.interp(samples, np.arange(len(result))*block+block/2, result).astype("float32")


def compress(wave, threshold, ratio):
    excess = np.maximum(20*np.log10(meter(wave))-threshold, 0.)*(1-1/ratio)
    return wave * (10**(-smoothed(excess)/20))[:, None]


def room_ir(seconds, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(int(RATE*seconds))/RATE
    noise = rng.normal(size=len(t))
    noise = signal.sosfilt(signal.butter(2, (170, 6100), fs=RATE, btype="bandpass", output="sos"), noise)
    tail = noise*np.minimum(t/.06, 1.)**2*np.exp(-6.91*t/seconds)
    tail *= .73 / np.linalg.norm(tail)
    for delay, level in ((.027,.39),(.047,-.28),(.069,.20),(.102,.18),(.149,-.14)):
        tail[int(RATE*(delay+rng.uniform(-.004,.004)))] += level
    tail[:round(.014*RATE)] = 0
    return tail.astype("float32")


def reverb(wave, seconds, seed):
    mono = wave.mean(axis=1)
    return np.column_stack([signal.oaconvolve(mono, room_ir(seconds, seed+ch), mode="full")[:LENGTH]
                            for ch in range(2)]).astype("float32")


def electronic_kick(bars):
    t = np.arange(round(.38*RATE))/RATE
    # Pitched kick with a short click and a longer sub tail.
    phase = 2*np.pi*(49*t + 2.1*(1-np.exp(-t/.025)) + .25*(1-np.exp(-t/.004)))
    hit = np.sin(phase)*np.exp(-t/.105)*(1-np.exp(-t/.0018))
    hit += .12*np.sin(2*np.pi*1310*t)*np.exp(-t/.0032)
    out = np.zeros(LENGTH, "float32")
    for bar in bars:
        if bar.number in (59, 60):
            continue
        ticks = (0,8) if bar.number in (10,24,30,41,43,49,54) else (0,4,8,12)
        for tick in ticks:
            index = round(bar.seconds(tick)*RATE)
            out[index:index+len(hit)] += hit*(.235 if tick == 0 else .195)
    return out[:, None]


def mix(work):
    bars = read()
    lead = highpass(load_track(work/"tenor.wav", False), 65)
    lead = compress(lead*2.95, -16.5, 2.1)*1.06
    upper = highpass(load_track(work/"lead.wav", False), 135)
    upper = compress(upper, -19, 2.2)
    harmony = highpass(load_track(work/"harmony.wav", False), 100)
    harmony = compress(harmony, -20, 2.2)
    rhythm = highpass(load_track(work/"rhythm.wav"), 29)*3.10
    band = highpass(load_track(work/"band.wav"), 105)*7.8
    orch = highpass(load_track(work/"orchestra.wav"), 36)*3.8
    rhythm = compress(rhythm, -18.5, 1.9) + electronic_kick(bars)
    band = compress(band, -18.0, 2.)
    orch = compress(orch, -13, 1.7)
    t = np.arange(LENGTH, dtype=np.float32)/RATE
    orbit = float(FIRST_DOWNBEAT)+110
    swell = np.clip((t-orbit)/8, 0, 1)
    # A little space around consonants without removing the energy of the groove.
    singing = smoothed(np.clip((20*np.log10(meter(lead))+42)/22, 0, 1), .012, .14)
    band *= (1-.13*singing)[:,None]
    orch *= ((1-.08*singing)*(1+.26*swell))[:,None]
    chorus = np.zeros(LENGTH, np.float32)
    for index in (0, 8, 9, 39, 40, 59):
        bar = bars[index]
        attack = np.clip((t-bar.start+.055)/.070, 0, 1)
        release = np.clip((bar.end+.055-t)/.090, 0, 1)
        chorus = np.maximum(chorus, attack*release)
    upper *= (chorus*(.23+.11*swell))[:,None]
    harmony *= (.19+.08*swell)[:,None]
    # Keep the low melody in the centre, with the sung octave and third on its flanks.
    doubles = np.column_stack((.65*upper[:,0]+harmony[:,0], upper[:,0]+.62*harmony[:,0]))
    # Different rooms for the small band and the broad orchestral finish.
    wet = .090*reverb(lead, .79, 137) + .15*reverb(band, .68, 273)
    wet += .27*reverb(orch, 1.65, 189) + .27*reverb(doubles, 1.24, 423)
    stereo = lead + doubles + rhythm + band + orch + wet
    # Let the resolving chord decay into the last wide frame.
    length = round(.37*RATE)
    stereo[-length:] *= (.5+.5*np.cos(np.linspace(0, np.pi, length, dtype=np.float32)))[:,None]
    stereo *= .94 / np.max(np.abs(stereo))
    if not np.isfinite(stereo).all():
        raise ValueError("Non-finite samples in the mix")
    raw = work/"mix.wav"
    sf.write(raw, stereo, RATE, subtype="PCM_24")
    return raw


def master(raw, output):
    base = ["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(raw), "-map", "0:a:0"]
    target = "loudnorm=I=-14:TP=-1.3:LRA=9"
    measure = subprocess.run([*base, "-af", target+":print_format=json", "-f", "null", "-"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    data = json.loads(re.findall(r"\{[^{}]*input_i[^{}]*\}", measure.stderr)[-1])
    norm = (target+f":measured_I={data['input_i']}:measured_TP={data['input_tp']}"
            f":measured_LRA={data['input_lra']}:measured_thresh={data['input_thresh']}"
            f":offset={data['target_offset']}:linear=true")
    audio = f"{norm},aresample={RATE},apad=whole_len={LENGTH},atrim=end_sample={LENGTH}"
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([*base,"-loglevel","error","-af",audio,"-ar",str(RATE),"-c:a","flac","-compression_level","8",
                    "-sample_fmt","s16","-metadata","title=I Want a GPU Tower",
                    "-metadata","artist=English tenor: Kokoro (am_michael). Vocal: Chiaki.",
                    "-metadata","comment=Original music for the GPU Silo short. Instruments: GeneralUser GS by S. Christian Collins.",
                    str(output)],check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    master(mix(args.work), args.output)
