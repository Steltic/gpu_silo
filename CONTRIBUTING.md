# Contribute a design idea

The film is the project presentation and the place where design decisions are judged. Describe an idea by the shot and timestamp where a viewer would see it. The [design decisions](design/README.md) point to the input and the source behind each part of the film.

### Suggest an idea without touching code

Open a [design idea](../../issues/new/choose). Say what should change, what the viewer should see and why it is better. Ideas that affect capacity or dimensions are easier to discuss with a number from the [calculations](design/calcs.md).

### Make a change in GitHub

1. Open [design/project.json](design/project.json) and click the pencil. Edit the value, select **Create a new branch**, then open a pull request. You can also clone the repository and edit the same file locally.
2. Regenerate the calculations and the design report with `python -m gpu_silo calcs` and commit the files it writes with your change. The design check fails if they disagree with the design file.
3. Add a dated entry to the [decision log](design/history.md) with the reason, the affected shots and the decision it replaces. Put changes to geometry, motion or cameras in the subsystem listed in the [design index](design/README.md).
4. Open the pull request's **Check the design** check. It checks the calculations, the report and both models, and renders a few stills from each film. On the run page, download **gpu-silo-stills** under **Artifacts** to look at them.
5. Merge the reviewed change.
6. The films are not rendered for every change. When several changes are in and the films should catch up, run the **Render the animation** workflow on `main` from the Actions tab, or put `[render]` in the message of the merge commit. It renders and verifies both films and publishes them as a release, and the movie links in the README follow the latest release.

### Build locally

Use Python 3.12 from the repository root. Exporting and checking the GLB needs only Python and NumPy.

```shell
python -m pip install -r requirements.txt
python -m gpu_silo calcs
python -m gpu_silo build --scene-only
python -m gpu_silo check
```

The movie also needs FFmpeg with libx264 on PATH and a C# compiler:

| System | Renderer toolchain |
| --- | --- |
| Linux | `mono-mcs`, `libmono-system-drawing4.0-cil`, `libgdiplus` |
| macOS | Mono (`brew install mono mono-libgdiplus`) |
| Windows | 64-bit .NET Framework 4.x, which includes `csc.exe` |

```shell
python -m gpu_silo build
python -m gpu_silo.validation.verify_movie renders/GPU_Silo.mp4
python -m gpu_silo stills 60 1700 3800 4800 6100 7100
```

The outputs are `renders/GPU_Silo.mp4` and `renders/GPU_Silo.glb`.

The short film of the build is a second edition of the same model. Add `--film short` to `build`, `check` and `stills`, and set `GPU_SILO_FILM=short` for the movie check:

```shell
python -m gpu_silo build --film short
python -m gpu_silo check --film short
GPU_SILO_FILM=short python -m gpu_silo.validation.verify_movie renders/silo_short.mp4
python -m gpu_silo stills --film short 640 1900 2560 2800 3900 4700
```

Its outputs are `renders/silo_short.mp4` and `renders/silo_short.glb`. Scenes that only one film has are switched in [gpu_silo/film.py](gpu_silo/film.py), and the short film's scene order, cameras and tags are in [gpu_silo/shortfilm.py](gpu_silo/shortfilm.py). A change to the shared model shows in both films, so check both. `build --jobs N` sets the number of parallel render processes. `stills` writes single frames to `renders/stills` so you can look at a shot without rendering the film. Open the MP4 in a player with chapters, or import the GLB into Blender and play its animation. Generated files stay out of Git and are distributed with releases.

The panel text uses the first installed typeface from a short list (Georgia or Liberation Serif, Segoe UI or Inter, Consolas or DejaVu Sans Mono), so line breaks can differ slightly between systems.

### Try a one-value change

In `storage`, change `"shaft_access_m": 0.62` to `0.7`. Every 4SU starts 0.08 m further from the shaft and its light-grey CDU and pump section shortens to 2.08 m, so the wall end stays where it was. The trusses are sized again, and the pod weight, the loads on the shaft and the clearance at the pod roots follow in the calculations and the design report. The gantry pick, footprint, service plug and installed copy follow in the film. Run `python -m gpu_silo calcs` and look at section 5 of the calculations: the clearance at the pod roots grows from 100 mm to about 150 mm. Then run the checks and inspect the dock at 0:47.

To change one unit only, add it to `cdu_pump_section_m_by_unit`, for example `{"1": 0.25}`. A pod too long for the bore is rejected with a message that says so.

### The design report

[design/report.md](design/report.md) is the structural design report. It is generated with the calculations by `python -m gpu_silo calcs`, so do not edit it by hand. The register of checks and the document details are `design_checks` in the design file. The analysis is in [gpu_silo/structure.py](gpu_silo/structure.py) and the wording, tables and figures are in [gpu_silo/report.py](gpu_silo/report.py).

To add or revise a check, put the calculation and its own verification in its module, write it up in `report.py`, update the status in the register and raise the revision. The steel checks are in `structure.py`, the walls in `walls.py`, the heat balance of the store in `thermal.py` and the comparison of reinforcement in `reinforcement.py`. `python -m gpu_silo calcs --check` fails if the report, a figure or the calculations no longer match the design file, or if a verification in one of these modules does not hold.

### Narration

The plan view at 3:36 is narrated. The script is `plan_view` in [design/narration.json](design/narration.json): each line has the words to `say` and the caption to `show`. The recording and its caption timings are committed in [audio/](audio), so building the movie does not need the speech model. The scene is as long as the recording.

After editing the script, record it again and commit the two files in `audio/`:

```shell
python -m pip install kokoro-onnx soundfile
python -m gpu_silo narrate --models DIRECTORY
```

`DIRECTORY` holds `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the [kokoro-onnx model release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0). The voice is `am_eric`, the same Eric offered in the [Kokoro demo](https://huggingface.co/spaces/hexgrad/Kokoro-TTS). Spell abbreviations out in `say` (`four S U`, `C D U`) and keep the written form in `show`.

### What the checks cover

The checks read the exported animation, not the source. They cover pod dimensions and the colour of the CDU section, traffic through the doorway, clearance while the store rotates, docking strokes, the pod exchange and the crew decks. They check that every pod sleeve ends inside the store, that the inner wall is bored at each sleeve and that the outer wall is left solid. For the dry coolers they cover the size and count of the frames and screens, their seats on the two tiers, clearance between neighbours, that every cast-in anchor and conduit is in the forms before its concrete is poured, that a frame never passes through the wall on its way to its seat, the crawler's reach and the boom lift's position at each frame. They follow the cooler service from the wall to the ground and back to the same seat. They check that the lid seats on the rim, that the eight propane tanks and the diesel tank land on their pad and that every leg of the gas line reaches full length. They check that both power levels fit in the bore and under the lid, that the two turbine sets clear the wall, and that the diesel sets clear each other and the crew's access wedge. They check that the hinged side of turbine set A is closed outside the crew scene, stays inside the bore when folded, and carries the crew only while it is fully down. They check that nothing on the roof overlaps, that the exhaust stacks stand above the air inlets, and that the fuel drops land beside the turbine sets. They check that a walkway ring joins the shaft to the pod roots at every level. They check that every pod rides a truck to the dock two at a time, leaves it where the gantry picks it up, stays under the spreader to the rail and is handed to the hoist, and that no two trucks share a dock lane. They check that every cooler is lifted from its truck into its own bay before its frame is picked, that the water tankers stop in their bays and stay off the haul ring, that the mixers back up to the pump hopper, that the propane transports stop in the lay-by, and that the jumpform crew matches the listed crew and rides the forms. The movie check confirms the narration is present in the plan view and silent elsewhere. A failing check names the assertion to inspect when a change affects another part of the design. For the short film they also check that the nine cage modules stack into the cage that is lifted, that the liner is finished before any water is in the store, that the power levels are fabricated before their picks and carry no enclosure, and that the dock is enclosed after the last pod.
