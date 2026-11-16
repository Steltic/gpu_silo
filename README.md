# GPU Silo

[![The finished GPU Silo with eight dry cooler frames on its concrete wall](docs/animation.jpg)](../../releases/latest/download/GPU_Silo.mp4)

**[Watch the animation · MP4](../../releases/latest/download/GPU_Silo.mp4)** · [Animated 3D model · GLB](../../releases/latest/download/GPU_Silo.glb) · [All versions](../../releases)

A 30 m concrete silo that houses, powers and liquid-cools 256 GPU racks. The racks sit four to a pod in 64 **4SU** pods on eight levels around a central shaft. Each pod carries its own CDU and pump and plugs into a water-glycol store held between the silo's two concrete walls. Thirty-two dry coolers on eight steel frames hang on the outside of the wall and reject the heat.

The animation is the working drawing for this project. Design decisions are made by looking at it, and every dimension in it comes from one file, [design/project.json](design/project.json). The repository holds that file, the [calculations](design/calcs.md) generated from it, the [decisions](design/README.md) and the code that turns them into the film. Anyone can propose a design idea and see it rendered.

| Design basis | Value |
| --- | ---: |
| GPU racks | 256 × NVIDIA NVL72 |
| 4SU pods | 64, eight per level on eight levels, 5.5 m long |
| CDUs and CDU pumps | 64 + 64, one of each per pod |
| Liquid heat load | 32 MW |
| Silo | 20 m outside, 13 m inside, 30 m high |
| Water-glycol store | 4,626 m³ (1.22 M US gal) between the walls, filled to the rim |
| Dry coolers | 32 × 1 MW in 8 steel frames, one pump each |

These figures are written by `python -m gpu_silo calcs` and also appear on screen throughout the film. The [calculations](design/calcs.md#6-open-questions-raised-by-these-numbers) list the open questions they raise. The first is that this geometry holds 1.22 M US gal against the 1.5 M target.

### Find it in the movie

| Scene | Time |
| --- | ---: |
| Jumpform the double-wall shell and cast the pod sleeves, frame anchors and conduits | 0:00 |
| Two crawlers lower the steel pod cage | 0:25 |
| The retained crawler tracks round the silo and hangs the eight dry cooler frames | 0:40 |
| Boom-lift crew connects the first frame | 0:45 |
| Water-glycol fills the wall gap to the rim | 1:12 |
| A flatbed delivers three 4SU pods with their light-grey CDU and pump sections | 1:19 |
| Lift the first 4SU, then run the lower six levels at 3× | 1:33 |
| Lower two power modules through the open top | 2:25 |
| Crews ride the wedge platforms to the pods | 2:47 |
| Exchange a faulty 4SU on Level 6 | 3:20 |
| Finished silo, design basis and a full exterior orbit | 4:11 |

[Scene guide](docs/sequence.md)

### Propose a design idea

1. **Describe it.** Open a [design idea](../../issues/new/choose) and say what a viewer should see and why.
2. **Or try it.** Edit a value in [design/project.json](design/project.json), run `python -m gpu_silo calcs` and open a pull request. The render check builds the MP4 and GLB for review.
3. **Record it.** An accepted change adds a line to the [decision log](design/history.md).

[Contributor quick start](CONTRIBUTING.md) · [Design decisions](design/README.md) · [Design calculations](design/calcs.md) · [Decision log](design/history.md)

### What is in the repository

| Path | Contents |
| --- | --- |
| [design/project.json](design/project.json) | Every design input: silo, pod, store, coolers, installation and film |
| [design/calcs.md](design/calcs.md) | Heat load, store volume, flows, cooler capacity and fit checks, generated from the inputs |
| [design/README.md](design/README.md) | The current decision for each part of the design and where to change it |
| [design/history.md](design/history.md) | Dated decision log, including what each decision replaced |
| [gpu_silo/](gpu_silo) | Parametric model, animation and checks |
| [renderer/](renderer) | Film renderer and the on-screen design panels |
| [docs/sequence.md](docs/sequence.md) | Scene-by-scene guide to the film |

This is a concept study. The model checks geometry and motion. It is not a structural, hydraulic, thermal or electrical design.
