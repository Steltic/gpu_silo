# I Want a GPU Tower

The English song edition follows the construction film through the four IFC studies. The final camera orbit starts at 1:50.292. The last syllable of “tower” carries the song into D major. Brass, strings, harp and timpani resolve over the wide view. [Watch short_song.mp4](https://github.com/Steltic/gpu_silo/releases/download/short-technical-2026-11-24/short_song.mp4)

The original melody is in 4/4 at 120 BPM. The first downbeat is frame 7. Each six-second IFC study gets three complete bars, with a different instrument introducing its component. Frame numbers below start at zero. [English lyrics and note timings](score.txt)

| First frame | Time | Picture | Music cue |
| ---: | ---: | --- | --- |
| 2,071 | 1:26.292 | Shaft and indexing pod holder | Cello introduces the 45-degree turn |
| 2,215 | 1:32.292 | Four-rack pod | Harp introduces four racks per pod and 72 GPUs per rack |
| 2,359 | 1:38.292 | Dry cooler | Mandolin introduces 2 MW per cooler and 26 units on duty |
| 2,503 | 1:44.292 | Twin turbine deck | Horns introduce the four girders and the design exhaust temperature |
| 2,647 | 1:50.292 | Blue-hour orbit | The chorus returns over rising strings and brass |
| 2,887 | 2:00.292 | Final wide view | D-major resolution with a 1.25-second tail |

The lyrics use the project's 46 MW normal IT ceiling and 4 MW plant allowance. The 235 full-power racks and 21 spares in the closing verse are one operating choice. Each turbine is rated at 25 MW. The four 2.5 MW diesels cover emergencies, with up to 7 MW available for priority IT. [Design basis](../../design/technical_short.md) · [Operating assumptions](../../design/assumptions.md#operating-choice-after-revision-j)

## Make the movie

Place the narrated technical master at `renders/technical-short/silo_short.mp4` or pass its location with `--picture`. The command uses Python's standard library, FFmpeg, ffprobe and the stereo FLAC in this directory. [Source picture](https://github.com/Steltic/gpu_silo/releases/download/short-technical-2026-11-24/silo_short.mp4)

```sh
python -m gpu_silo short-song --output renders/short_song.mp4
```

The export copies frames 0 through 2,916 and keeps the timing of all 22 retained chapters. It encodes the stereo song at 48 kHz in AAC and adds selectable English lyrics. Before publishing the file it compares every H.264 packet and its timestamps with the source. The picture and the embedded song both end at 2:01.542.

| Released file | SHA-256 |
| --- | --- |
| `silo_short.mp4` (source picture) | `8899758bae8d92c07b44b29fd6176f53f2fcf87347c0d6a1ba494a91d025aafa` |
| `short_song.flac` (stereo master) | `d8255445b7c005a76f5a1186772b5b7c0919878f86e048fef4022b30a2e1bd1f` |
| `short_song.mp4` (song edition) | `f2682e518009ec16a7cfe88406b740e66feba10406eadc5532ca02434561c406` |

## Record another mix

The lead uses Kokoro v1.0's `am_michael` English voice. Each lyric syllable has a duration and a sung pitch in the score. Vocal: Chiaki (upper octave and chorus harmony). The instrumental arrangement uses S. Christian Collins's GeneralUser GS 2.0.3, including its Italian accordion and mandolin. [Kokoro ONNX and voices](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0) · [Chiaki voicebank](https://chiaki.ch/en/character/chiaki) · [GeneralUser GS](https://github.com/mrbumpy409/GeneralUser-GS)

To rebuild the audio, install the optional Python packages `cmudict`, `numpy`, `onnx`, `onnxruntime`, `PyYAML`, `scipy`, `soundfile` and `tinysoundfont`. Run from the repository root. Supply a soundfont, the unpacked Chiaki bank, and a folder containing `kokoro-v1.0.onnx` and `voices-v1.0.bin`. Use a fresh working directory when editing the score, models or pronunciation so cached vocal takes match the new performance.

```sh
python -m gpu_silo.song_band path/to/GeneralUser-GS.sf2 renders/song-work
python -m gpu_silo.song_vocal path/to/Chiaki renders/song-work
python -m gpu_silo.song_lead path/to/kokoro-models renders/song-work
python -m gpu_silo.song_mix renders/song-work audio/short_song/short_song.flac
python -m gpu_silo short-song --output renders/short_song.mp4
```
