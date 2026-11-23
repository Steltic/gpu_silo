# GPU Silo

[![The finished GPU Silo with its roof stacks, ten screened dry cooler frames, the haul ring and the fuel farm](docs/animation.jpg)](../../releases/latest/download/GPU_Silo.mp4)

**[Watch the build · silo_short.mp4](../../releases/download/short-film-2026-11-23/silo_short.mp4)** (4:22, narrated) · **[Watch the full presentation · GPU_Silo.mp4](../../releases/latest/download/GPU_Silo.mp4)** (5:43) · Animated 3D models: [silo_short.glb](../../releases/download/short-film-2026-11-23/silo_short.glb), [GPU_Silo.glb](../../releases/latest/download/GPU_Silo.glb) · **[Complete BIM model · GPU_Silo.ifc](../../releases/latest/download/GPU_Silo.ifc)** · [All versions](../../releases)

A 32 m concrete silo that houses, powers and liquid-cools 256 NVIDIA Vera Rubin GPU racks with 50 MW of installed rack capacity. The racks sit four to a pod in 64 **4SU** pods on eight levels around a central shaft. Each pod carries its own CDU and pump and plugs into a water-glycol store held between the silo's two concrete walls. Thirty 2 MW dry coolers on ten screened steel frames hang on the outside of the wall and reject the heat. Two in-line 25 MW gas turbine sets sit side by side above the pods under the lid, burn propane from eight tanks beside the silo and feed the grade-level transformers down the central shaft. Fixed bay risers supply each docked pod. Four backup diesel sets sit on the level below them. Everything arrives by truck on a one-way haul ring, and the build is laid out to finish 28 days after the last concrete is poured.

**silo_short** follows the build from jumpforming to the conversion of one receiving lane into a control room. Four narrated IFC cutaways isolate the shaft, a four-rack pod, a dry cooler and the turbine deck before a blue-hour orbit. **GPU_Silo** is the longer presentation, with the narrated cooling loop, personnel access and the pod and cooler replacement. It shows the earlier build order with the store filled before the pods.

The animation is the working drawing for this project. Design decisions are made by looking at it, and every dimension in it comes from one file, [design/project.json](design/project.json). The repository holds that file, the [calculations](design/calcs.md) generated from it, the [decisions](design/README.md) and the code that turns them into the film. Anyone can propose a design idea and see it rendered.

The normal operating brief is 46 MW IT on the turbines, with diesels reserved for emergencies. One reference case runs 235 racks at full power and holds 21 spare. Operators can choose another mix within the available power and cooling. Revision K uses the 50 MW installed capacity to size the physical cooling plant. [Operating choice](design/assumptions.md#operating-choice-after-revision-j)

| Revision K design basis | Value |
| --- | ---: |
| GPU racks | 256 × NVIDIA Vera Rubin NVL72, 195 kW each |
| 4SU pods | 64, eight per level on eight levels, 2.77 m apart vertically. Each is 7.16 m long and 8.93 t: 5 m of racks at the shaft end and a 2.16 m CDU and pump section out to the wall. |
| Pod structure | Two welded side trusses, HSS6×3×3/16 chords and HSS2×2×3/16 web, cantilevering from the shaft. Tip deflection 4.9 mm against a 5 mm limit. [Design report](design/report.md) |
| Central shaft | 1.16 m diameter steel tube with a 2 in (50.8 mm) wall, fixed to the foundation and held at its top by the support rig under the diesel level, through 16 plates cast into the inner wall. The levels turn on it. 0.62 m of access round it. |
| CDUs and CDU pumps | 64 + 64, one of each per pod |
| Installed rack heat / normal IT ceiling | 50 MW / 46 MW |
| Silo | 25 m outside, 17 m inside, 32 m high. Outer wall 400 mm with stainless steel hoop bars, inner wall 500 mm, no post-tensioning. |
| Water-glycol store | 6,524 m³ (1.72 M US gal) between the walls. It runs layered, cool below warm, through a pair of vertical pipes for each bay of pods and each cooler frame: about 76 minutes from a fully charged store at the 51.25 MW thermal design load. [Check 5](design/report.md#9-check-5-heat-balance-of-the-store) |
| Dry coolers | 30 × 2 MW in 10 screened steel frames, one pump each. The full cluster and pumps require at least 26 at rated conditions. Inlet temperature determines the available duty. |
| Power | 2 × 25 MW turbines supply normal operations, with a 4 MW plant allowance. The modeled 6 MW intertie is optional for normal operation. Emergency transfer can supply up to 7 MW of priority IT after essential services. |
| Backup | 4 × 2.5 MW diesel sets on the level below, day tanks inside, 64 m³ bulk tank outside |
| Fuel | 8 propane tanks of 20 m, 913 m³, about 43 h at full load, one 200 mm line |
| Roof | 2 turbine exhaust stacks, 2 air inlet houses, diesel exhausts and room vents |
| Trucking | 32 pod trucks at 2 pods each, 278 water tankers, 30 cooler trucks, 26 propane transports, 250 mixers for the walls |
| Store liner | 2 mm spray-applied polyurea on both faces of the store, 4,448 m², sprayed from four stages on days 11 to 14 |
| Programme | Walls in 10 daily lifts by a crew of 22 while the pod cage is built beside them a level a day, then 28 days to handover. The support rig is set on days 4 and 5 to hold the top of the shaft before the first pod. Water goes in last, on days 15 to 28. Commissioning is by others after day 28. |

Section 2 of the design report lists each numbered check and its status. Revision K checks the support rig, sliding shaft guide and both sets of wall mounts, including the revised anchor bars in the IFC. Edit `design_checks.register` in the project inputs to add a check or change its status, then regenerate the report. [Register of design checks](design/report.md#2-register-of-design-checks) · [Project inputs](design/project.json) · [Assumptions and release evidence](design/assumptions.md)

### Find it in the short film (silo_short)

| Scene | Programme | Time |
| --- | --- | ---: |
| Jumpform the walls with a crew of 22. The pod cage is built beside the silo: each day three trucks bring a level, it is welded on the pad, lifted onto the stack and welded on. | Days -9 to 0 | 0:00 |
| Two crawlers lift the finished cage into the silo | Day 3 | 0:42 |
| Bare support rig lowered onto its wall mounts to brace the shaft | Days 4 to 5 | 0:56 |
| Receiving dock: two pods a truck, lifted onto the rail by the gantry | Day 6 | 1:07 |
| Pods load and the cooler frames are hung. Everything in or on the walls is cleared from the cutaway. | Days 6 to 17 | 1:21 |
| Fuel tanks arrive and are set on the pad | Days 8 to 11 | 1:37 |
| A tinted liner rises along both faces of the store | Days 11 to 14 | 1:52 |
| Diesel sets staged and the turbine deck welded and fitted out on site | Days 9 to 18 | 2:00 |
| Diesel sets and day tanks land on the rig, then the turbine level and the lid are lifted in. Water tankers start and the store begins to fill. | Days 19 to 21 | 2:12 |
| Propane transports fill the tanks and the fuel lines run to the power levels | Days 16 to 26 | 2:38 |
| A glazed control room occupies one dock lane. The adjacent lane and the pod rail remain available for exchanges. | Days 24 to 27 | 2:46 |
| IFC studies of the shaft, four-rack pod, dry cooler and turbine deck | | 2:53 / 3:05 / 3:17 / 3:29 |
| Roof antenna and complete blue-hour orbit | Day 28 | 3:41 |
| Narrated cooling plan and section | | 4:03 |

### Find it in the long film (GPU_Silo)

| Scene | Time |
| --- | ---: |
| Jumpform the double-wall shell: the form system, a crew of 22 and truck mixers at the pump | 0:00 |
| Two crawlers lower the steel pod cage while water tankers and cooler trucks start arriving | 0:25 |
| Bare support rig lowered onto its wall mounts to brace the shaft | 0:40 |
| Water-glycol fills the wall gap to the top from three tanker bays | 0:49 |
| Receiving dock: trucks back in with two 4SU pods each and the gantry lifts them onto the rail | 0:55 |
| Lift the first 4SU | 1:09 |
| The retained crawler hangs the ten screened cooler frames while the pods load and the trucks keep coming | 1:17 |
| Run the lower six levels at 3× | 1:38 |
| Land the diesel sets and day tanks on the support rig | 2:01 |
| Lower the turbine level: two in-line 25 MW sets side by side | 2:13 |
| Close the lid with its exhaust stacks and air inlet houses | 2:21 |
| Crews ride the wedge platforms to the pods | 2:27 |
| The side of turbine set A folds down to show its 25 MW gas turbine | 2:44 |
| Finished silo on day 28, design basis, the 28-day programme and a full exterior orbit | 2:58 |
| Trucks bring eight propane tanks and the diesel tank | 3:21 |
| Propane transports fill the tanks and the fuel lines run to the power levels | 3:36 |
| Plan view of the cooling loop, with narration | 3:44 |
| Section showing power, water-glycol, gas and diesel | 4:20 |
| Replace a faulty 4SU on Level 6 | 4:46 |
| Wide shot: the crawler lowers cooler frame 09, swaps one cooler and hangs it back | 5:00 |

[Scene guide](docs/sequence.md)

### Propose a design idea

1. **Describe it.** Open a [design idea](../../issues/new/choose) and say what a viewer should see and why.
2. **Or try it.** Edit a value in [design/project.json](design/project.json), run `python -m gpu_silo calcs` and open a pull request. The design check verifies the calculations, the report and both models, and renders stills for review. The films are rendered on request, so they can be a few changes behind the design.
3. **Record it.** An accepted change adds a line to the [decision log](design/history.md).

[Contributor quick start](CONTRIBUTING.md) · [Design decisions](design/README.md) · [Design calculations](design/calcs.md) · [Structural design report](design/report.md) · [Decision log](design/history.md)

### What is in the repository

| Path | Contents |
| --- | --- |
| [design/project.json](design/project.json) | Every design input: cluster, silo, pod, store, coolers, power, diesel, fuel, installation, trucking, site roads, jumpform crew, programme and film |
| [design/calcs.md](design/calcs.md) | Heat load, store, flows, coolers and spares, the fit of the power levels, roof vents, propane line size, fuel run times, truck loads, the store liner, the roads and staging areas, and the 28-day programme. Generated from the inputs. |
| [design/report.md](design/report.md) | Ten design checks, the site screening envelope, thermal limits and owner review assumptions. |
| [design/narration.json](design/narration.json) · [audio/](audio) | The narration script and its recording |
| [design/README.md](design/README.md) | The current decision for each part of the design and where to change it |
| [design/history.md](design/history.md) | Dated decision log, including what each decision replaced |
| [gpu_silo/](gpu_silo) | Parametric model, animation and checks |
| [renderer/](renderer) | Film renderer and the on-screen design panels |
| [docs/sequence.md](docs/sequence.md) | Scene-by-scene guides to both films |

This is a concept study. The model checks geometry and motion. It is not a structural, hydraulic, thermal or electrical design.
