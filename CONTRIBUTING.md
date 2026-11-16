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
python -m gpu_silo stills 1100 2300 6300
```

The outputs are `renders/GPU_Silo.mp4` and `renders/GPU_Silo.glb`. `build --jobs N` sets the number of parallel render processes. `stills` writes single frames to `renders/stills` so you can look at a shot without rendering the film. Open the MP4 in a player with chapters, or import the GLB into Blender and play its animation. Generated files stay out of Git and are distributed with releases.

The panel text uses the first installed typeface from a short list (Georgia or Liberation Serif, Segoe UI or Inter, Consolas or DejaVu Sans Mono), so line breaks can differ slightly between systems.

### Try a one-value change

In `pod`, change `"cdu_pump_section_m": 0.5` to `0.4`. Every 4SU becomes 5.4 m long, with 0.4 m of light grey beyond the 5 m bronze housing. The gantry pick, footprint, service plug and installed copy follow. Run `python -m gpu_silo calcs` and look at section 5 of the calculations: the clearance to the bore grows by 100 mm. Then run the checks and inspect the terminal at 1:19.

To change one unit only, add it to `cdu_pump_section_m_by_unit`, for example `{"1": 0.25}`. A pod too long for the bore is rejected with a message that says so.

### What the checks cover

The checks read the exported animation, not the source. They cover pod dimensions and the colour of the CDU section, traffic through the doorway, clearance while the store rotates, docking strokes, the pod exchange and the crew decks. For the dry coolers they cover the size and count of the frames, their seats on the two tiers, clearance between neighbours, that every cast-in anchor and conduit is in the forms before its concrete is poured, that a frame never passes through the wall on its way to its seat, the crawler's reach and the boom lift's position at each frame. A failing check names the assertion to inspect when a change affects another part of the design.
