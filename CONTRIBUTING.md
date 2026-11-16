# Contribute a design idea

The film is the project presentation and the place where design decisions are judged. Describe an idea by the shot and timestamp where a viewer would see it. The [design decisions](design/README.md) point to the input and the source behind each part of the film.

### Suggest an idea without touching code

Open a [design idea](../../issues/new/choose). Say what should change, what the viewer should see and why it is better. Ideas that affect capacity or dimensions are easier to discuss with a number from the [calculations](design/calcs.md).

### Make a change in GitHub

1. Open [design/project.json](design/project.json) and click the pencil. Edit the value, select **Create a new branch**, then open a pull request. You can also clone the repository and edit the same file locally.
2. Regenerate the calculations with `python -m gpu_silo calcs` and commit `design/calcs.md` with your change. The render check fails if the two disagree.
3. Add a dated entry to the [decision log](design/history.md) with the reason, the affected shots and the decision it replaces. Put changes to geometry, motion or cameras in the subsystem listed in the [design index](design/README.md).
4. Open the pull request's **Render the animation** check. On the run page, download the artifact beginning with **gpu-silo-animation-** under **Artifacts**. It contains the MP4 and the animated GLB built together. Watch the changed chapter and the scenes on either side of it.
5. Merge the reviewed change. On `main` the workflow publishes the verified files as a release, and the movie link in the README follows the latest release.

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
python -m gpu_silo stills 1700 3900 5400 6300 7250
```

The outputs are `renders/GPU_Silo.mp4` and `renders/GPU_Silo.glb`. `build --jobs N` sets the number of parallel render processes. `stills` writes single frames to `renders/stills` so you can look at a shot without rendering the film. Open the MP4 in a player with chapters, or import the GLB into Blender and play its animation. Generated files stay out of Git and are distributed with releases.

The panel text uses the first installed typeface from a short list (Georgia or Liberation Serif, Segoe UI or Inter, Consolas or DejaVu Sans Mono), so line breaks can differ slightly between systems.

### Try a one-value change

In `pod`, change `"cdu_pump_section_m": 0.5` to `0.4`. Every 4SU becomes 5.4 m long, with 0.4 m of light grey beyond the 5 m bronze housing. The gantry pick, footprint, service plug and installed copy follow. Run `python -m gpu_silo calcs` and look at section 5 of the calculations: the clearance to the bore grows by 100 mm. Then run the checks and inspect the terminal at 0:47.

To change one unit only, add it to `cdu_pump_section_m_by_unit`, for example `{"1": 0.25}`. A pod too long for the bore is rejected with a message that says so.

### Narration

The plan view at 3:40 is narrated. The script is `plan_view` in [design/narration.json](design/narration.json): each line has the words to `say` and the caption to `show`. The recording and its caption timings are committed in [audio/](audio), so building the movie does not need the speech model. The scene is as long as the recording.

After editing the script, record it again and commit the two files in `audio/`:

```shell
python -m pip install kokoro-onnx soundfile
python -m gpu_silo narrate --models DIRECTORY
```

`DIRECTORY` holds `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the [kokoro-onnx model release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0). The voice is `am_eric`, the same Eric offered in the [Kokoro demo](https://huggingface.co/spaces/hexgrad/Kokoro-TTS). Spell abbreviations out in `say` (`four S U`, `C D U`) and keep the written form in `show`.

### What the checks cover

The checks read the exported animation, not the source. They cover pod dimensions and the colour of the CDU section, traffic through the doorway, clearance while the store rotates, docking strokes, the pod exchange and the crew decks. They check that every pod sleeve ends inside the store, that the inner wall is bored at each sleeve and that the outer wall is left solid. For the dry coolers they cover the size and count of the frames and screens, their seats on the two tiers, clearance between neighbours, that every cast-in anchor and conduit is in the forms before its concrete is poured, that a frame never passes through the wall on its way to its seat, the crawler's reach and the boom lift's position at each frame. They follow the cooler service from the wall to the ground and back to the same seat. They check that the lid seats on the rim below the vent tops, that the eight tanks land on their pad and that every leg of the gas line reaches full length. They check that the hinged side of the lower power module is closed outside the crew scene, that the crew stand on it only while it is fully down, and that the turbine fits inside the module. They check that the door plug is in the door for the orbit, clear of the doorway while pods pass through, and back at the end, and that the roof vents sit on the lid clear of the exhaust vents. The movie check confirms the narration is present in the plan view and silent elsewhere. A failing check names the assertion to inspect when a change affects another part of the design.
