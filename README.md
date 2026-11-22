# GPU Silo

[![The finished GPU Silo with its roof stacks, ten screened dry cooler frames, the haul ring and the fuel farm](docs/animation.jpg)](../../releases/latest/download/GPU_Silo.mp4)

**[Watch the build · silo_short.mp4](../../releases/latest/download/silo_short.mp4)** (3:26) · **[Watch the full presentation · GPU_Silo.mp4](../../releases/latest/download/GPU_Silo.mp4)** (5:33) · Animated 3D models: [silo_short.glb](../../releases/latest/download/silo_short.glb), [GPU_Silo.glb](../../releases/latest/download/GPU_Silo.glb) · [All versions](../../releases)

A 32 m concrete silo that houses, powers and liquid-cools 256 NVIDIA Vera Rubin GPU racks, a 50 MW cluster. The racks sit four to a pod in 64 **4SU** pods on eight levels around a central shaft. Each pod carries its own CDU and pump and plugs into a water-glycol store held between the silo's two concrete walls. Thirty 2 MW dry coolers on ten screened steel frames hang on the outside of the wall and reject the heat. Two in-line 25 MW gas turbine sets sit side by side above the pods under the lid, burn propane from eight tanks beside the silo and feed the pods down the central shaft. Four backup diesel sets sit on the level below them. Everything arrives by truck on a one-way haul ring, and the build is laid out to finish 28 days after the last concrete is poured.

There are two films. **silo_short** shows the build in programme order and nothing else: the pod cage built beside the walls, the pods and coolers, the fuel tanks, the store liner, the power levels fabricated on site, the water fill over the last two weeks and the dock closed in as a control office. It ends on a plan and a section side by side. **GPU_Silo** is the longer presentation, with the narrated cooling loop, personnel access and the pod and cooler replacement. The two are built from the same model and are not kept in step: the long film still shows the earlier build order, with the store filled before the pods.

The animation is the working drawing for this project. Design decisions are made by looking at it, and every dimension in it comes from one file, [design/project.json](design/project.json). The repository holds that file, the [calculations](design/calcs.md) generated from it, the [decisions](design/README.md) and the code that turns them into the film. Anyone can propose a design idea and see it rendered.

| Design basis | Value |
| --- | ---: |
| GPU racks | 256 × NVIDIA Vera Rubin NVL72, 195 kW each |
| 4SU pods | 64, eight per level on eight levels, 2.77 m apart vertically. Each is 7.16 m long and 8.93 t: 5 m of racks at the shaft end and a 2.16 m CDU and pump section out to the wall. |
| Pod structure | Two welded side trusses, HSS6×3×3/16 chords and HSS2×2×3/16 web, cantilevering from the shaft. Tip deflection 4.9 mm against a 5 mm limit. [Design report](design/report.md) |
| Central shaft | 1.16 m diameter steel tube with a 1-1/4 in (31.8 mm) wall, fixed to the foundation and held at its top by the support rig under the diesel level, through 16 plates cast into the inner wall. The levels turn on it. 0.62 m of access round it. |
| CDUs and CDU pumps | 64 + 64, one of each per pod |
| Liquid heat load | 50 MW |
| Silo | 25 m outside, 17 m inside, 32 m high |
| Water-glycol store | 7,331 m³ (1.94 M US gal) between the walls, 97 minutes of full load on a 10 K swing |
| Dry coolers | 30 × 2 MW in 10 screened steel frames, one pump each. 25 carry the load, 5 are spare. |
| Power | 2 × 25 MW in-line gas turbine generator sets, side by side on the top level |
| Backup | 4 × 2.5 MW diesel sets on the level below, day tanks inside, 64 m³ bulk tank outside |
| Fuel | 8 propane tanks of 20 m, 913 m³, about 43 h at full load, one 200 mm line |
| Roof | 2 turbine exhaust stacks, 2 air inlet houses, diesel exhausts and room vents |
| Trucking | 32 pod trucks at 2 pods each, 312 water tankers, 30 cooler trucks, 26 propane transports, 140 mixers for the walls |
| Store liner | 2 mm spray-applied polyurea on both faces of the store, 4,453 m², sprayed from four stages on days 11 to 14 |
| Programme | Walls in 10 daily lifts by a crew of 22 while the pod cage is built beside them a level a day, then 28 days to handover. Water goes in last, on days 15 to 28. Commissioning is by others after day 28. |

These figures are written by `python -m gpu_silo calcs` and also appear on screen throughout the film. The [calculations](design/calcs.md#10-open-questions-raised-by-these-numbers) list the open questions they raise. The largest are the wall design, no spare turbine, heat from the turbines next to the pods and the store, and air for people working in the bore.

### Find it in the short film (silo_short)

| Scene | Programme | Time |
| --- | --- | ---: |
| Jumpform the walls with a crew of 22. The pod cage is built beside the silo: each day three trucks bring a level, it is welded on the pad, lifted onto the stack and welded on. | Days -9 to 0 | 0:00 |
| Two crawlers lift the finished cage into the silo | Day 3 | 0:42 |
| Receiving dock: two pods a truck, lifted onto the rail by the gantry | Day 6 | 0:58 |
| Pods load and the cooler frames are hung. Everything in or on the walls is cleared from the cutaway. | Days 6 to 17 | 1:13 |
| Fuel tanks arrive and are set on the pad | Days 8 to 11 | 1:28 |
| The inside of the store is spray-coated from four rising stages | Days 11 to 14 | 1:44 |
| Power levels fabricated on site: deck steel welded, diesel and turbine sets landed from their trucks | Days 9 to 18 | 1:52 |
| Open diesel level, open turbine level and the lid lifted in. Water tankers start and the store begins to fill. | Days 19 to 21 | 2:04 |
| Propane transports fill the tanks and the fuel lines run to the power levels | Days 16 to 26 | 2:30 |
| The receiving dock is walled and given a flat roof as the control office | Days 24 to 27 | 2:38 |
| Finished silo, design basis, the 28-day programme and a full exterior orbit | Day 28 | 2:44 |
| Plan and section side by side, silent | | 3:07 |

### Find it in the long film (GPU_Silo)

| Scene | Time |
| --- | ---: |
| Jumpform the double-wall shell: the form system, a crew of 22 and truck mixers at the pump | 0:00 |
| Two crawlers lower the steel pod cage while water tankers and cooler trucks start arriving | 0:25 |
| Water-glycol fills the wall gap to the top from three tanker bays | 0:40 |
| Receiving dock: trucks back in with two 4SU pods each and the gantry lifts them onto the rail | 0:47 |
| Lift the first 4SU | 1:01 |
| The retained crawler hangs the ten screened cooler frames while the pods load and the trucks keep coming | 1:09 |
| Run the lower six levels at 3× | 1:30 |
| Lower the backup diesel level | 1:52 |
| Lower the turbine level: two in-line 25 MW sets side by side | 2:04 |
| Close the lid with its exhaust stacks and air inlet houses | 2:12 |
| Crews ride the wedge platforms to the pods | 2:19 |
| The side of turbine set A folds down to show its 25 MW gas turbine | 2:36 |
| Finished silo on day 28, design basis, the 28-day programme and a full exterior orbit | 2:50 |
| Trucks bring eight propane tanks and the diesel tank | 3:12 |
| Propane transports fill the tanks and the fuel lines run to the power levels | 3:27 |
| Plan view of the cooling loop, with narration | 3:36 |
| Section showing power, water-glycol, gas and diesel | 4:11 |
| Replace a faulty 4SU on Level 6 | 4:37 |
| Wide shot: the crawler lowers cooler frame 09, swaps one cooler and hangs it back | 4:50 |

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
| [design/report.md](design/report.md) | Structural design report: the register of design checks, the basis of design and each check as it is completed. Generated from the inputs. |
| [design/narration.json](design/narration.json) · [audio/](audio) | The narration script and its recording |
| [design/README.md](design/README.md) | The current decision for each part of the design and where to change it |
| [design/history.md](design/history.md) | Dated decision log, including what each decision replaced |
| [gpu_silo/](gpu_silo) | Parametric model, animation and checks |
| [renderer/](renderer) | Film renderer and the on-screen design panels |
| [docs/sequence.md](docs/sequence.md) | Scene-by-scene guides to both films |

This is a concept study. The model checks geometry and motion. It is not a structural, hydraulic, thermal or electrical design.
