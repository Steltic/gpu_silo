# Design decisions

The movie shows the current design. [Project inputs](project.json) are versioned with the geometry, animation and checks, and the [calculations](calcs.md) are generated from the same file. A contributor can change one pod, the shared design or the way a scene is filmed. Each change has a reviewable diff, a recalculated design basis and a movie preview.

## System

256 NVL72 racks in 64 pods of four. Estimated liquid heat load 32 MW.

| Side | Equipment | Path |
| --- | --- | --- |
| Heat collection | 64 CDUs, one per pod, each with its own VFD pump | Pod cold plates → CDU → wall coupling → store |
| Thermal store | Closed-loop water and propylene glycol between the two concrete walls | Decouples the two sides, buffers load and steadies cooler staging |
| Heat rejection | 32 dry coolers of 1 MW, each with its own pump, in 8 steel frames | Store → cast-in conduit → pump → cooler → cast-in conduit → store |

Central control manages CDU pump speed, dry cooler fan speed and staging, and cooler pump staging against store temperature and total heat load.

## Current decisions

| Design choice | Current decision | Where to change it |
| --- | --- | --- |
| Application | House and power GPU racks, cooled by liquid. | [Cluster inputs](project.json) · [Calculations](calcs.md) |
| Concrete and jumpforming | 20 m outside diameter, 13 m inside diameter, 30 m high, ten 3 m lifts. Two 250 mm skins enclose a 3.0 m liquid gap. | [Silo inputs](project.json) · [Forms, wall lifts and farm](../gpu_silo/silo_model.py) |
| Thermal store | Water-glycol fills the gap between the skins to 29.75 m. There is no upper tank. The gap holds 4,626 m³, 1.22 M US gal. | [Store inputs](project.json) · [Liquid, sleeves and doorway](../gpu_silo/services.py) · [Volume](calcs.md#2-thermal-store-between-the-concrete-walls) |
| Ground entry | 0.60 × 2.30 m body inside a 0.76 × 2.40 m steel frame. Allow 50 mm each side and 100 mm overhead, giving a 0.86 × 2.50 m opening. Blocked jambs and a lintel keep the entry dry. | [Pod and opening inputs](project.json) · [Door and seals](../gpu_silo/services.py) |
| 4SU pod | Named 4SU. 5.5 m long: the 5 m bronze housing with dark side trusses holds four racks, and a solid light-grey 0.5 m section at the wall end holds the CDU and pump. All 64 are the same. | [Pod inputs and per-unit overrides](project.json) · [Body, frame, material and CDU section](../gpu_silo/cargo.py) |
| Storage and ground feed | Eight berths on each of eight 2.5 m levels. A steel central shaft carries radial cantilevers. The hole through both walls is the only ground entry. Every pod rises from grade. | [Storage inputs](project.json) · [Cage, pickup and radial motion](../gpu_silo/pod_scene.py) |
| Parking and sequence | Berths sit 45° apart. Occupied levels rotate and bunch at 40° pitch to free the lifting lane. Fill from the top down. After the top two levels, run the remaining installation at 3×. | [Pitch and speed](project.json) · [Lift clock](../gpu_silo/pod_scene.py) |
| Pod services | A cast-in sleeve at each berth passes through both walls. The CDU pump draws from and returns to the store through a self-sealing coupling. Power and data enter through a dry duct in the same sleeve. | [Berth elevations](project.json) · [Sleeves and docking](../gpu_silo/services.py) |
| Dry coolers | 32 coolers of 1 MW. Each is 9 m long with outward fans and has its own 1 m pump unit beside it. | [Cooler inputs](project.json) · [Cooler, pump and frame](../gpu_silo/cooler_frames.py) |
| Cooler frames | Eight steel frames, 10 m across, 10 m high and 2.5 m off the wall, each holding four coolers stacked vertically. Eight frames are wider than the circumference, so they sit in two tiers of four, turned 45° from each other, at RL 9.5 to 19.5 m and RL 20 to 30 m. | [Frame size and tiers](project.json) · [Arrangement](calcs.md#frame-arrangement) |
| Frame fixings | 20 cast-in anchors per frame for the supports and 8 cast-in conduits per frame through the outer skin, a supply and a return for each cooler. All are set in the forms before their lift is poured. | [Anchor columns and conduits](project.json) · [Anchors, seats, sleeves and spools](../gpu_silo/cooler_frames.py) |
| Frame installation | The south crawler stays after the tandem cage lift. It tracks round the silo, picks each frame from laydown, hoists it and sets it on its seats. Two fitters in a boom lift follow and connect the pipework. | [Track, laydown, order and cycle times](project.json) · [Crawler, boom lift and crew](../gpu_silo/cooler_frames.py) |
| Terminal and delivery | One flatbed brings three pods. The travelling gantry unloads them onto receiving cradles and the intake rail feeds the silo. | [Truck, cradles, gantry and handoff](../gpu_silo/yard.py) |
| Power modules | After pod loading, lower two 2.5 × 2.5 m container sections through the open top onto coaxial stubs above the store. They turn 90° between levels and four end ducts telescope to the rim. These are placeholders. The electrical supply is not yet sized. | [Power inputs](project.json) · [Power picks, stubs and exhausts](../gpu_silo/plant.py) |
| People and access | Eight solid wedge platforms board 19 technicians at grade. Seven service different pod levels. One rises to the underside of the lower power module. | [Crew and destination by wedge](project.json) · [Decks, guides and poses](../gpu_silo/crew.py) |
| Pod exchange | Level 6, bay 5, 4SU 021. Disconnect the two berths above and five below, rotate clear, lower the faulty pod, feed the spare from grade, then reconnect. | [Fault selection](project.json) · [Exchange choreography](../gpu_silo/maintenance.py) |
| Design information on the film | A design basis strip stays on screen. The cooler, store and closing panels show figures from the calculations. | [Figures](../gpu_silo/calcs.py) · [Panels](../renderer/DesignRender.cs) |
| Camera, timing and finish | Low-poly agricultural setting at 24 fps and 1280 × 720. The concrete is solid while it is cast and while the cooler frames are hung, and drawn as glass while the cage and pods are loaded. | [Movie inputs](project.json) · [Cameras](../gpu_silo/pod_scene.py) · [Renderer](../renderer) · [Chapters and encoding](../gpu_silo/render_project.py) |

## How dimensions propagate

The liquid gap is `(outside diameter − inside diameter) / 2 − outer skin − inner skin`. At 20 m and 13 m with 250 mm skins it is **3.00 m**. The shaft end of a pod is at radius **0.86 m** and its wall end at **6.36 m**. The corner of the 0.76 m wide frame sweeps a radius of **6.371 m**, which leaves **129 mm** to the 6.50 m bore.

A cooler frame is flat and the wall is curved. Its back plane stands 0.20 m off the wall at its centre and 1.54 m off at each end. The anchor struts bridge that gap.

Unit numbers follow the installation order, starting at 001 on the top level, then round a level before moving down. The exchange spare has the next number. Cooler frames are numbered anticlockwise from the ground entry. Dimensions are in metres, angles in degrees and colours in sRGB hexadecimal.

[Design calculations](calcs.md) · [Decision log](history.md) · [How to preview and merge a design change](../CONTRIBUTING.md)
