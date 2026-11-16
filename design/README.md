# Design decisions

The movie shows the current design. [Project inputs](project.json) are versioned with the geometry, animation and checks, and the [calculations](calcs.md) are generated from the same file. A contributor can change one pod, the shared design or the way a scene is filmed. Each change has a reviewable diff, a recalculated design basis and a movie preview.

## System

256 NVIDIA Vera Rubin NVL72 racks in 64 pods of four, 195 kW of liquid heat each. Liquid heat load 50 MW.

| Side | Equipment | Path |
| --- | --- | --- |
| Heat collection | 64 CDUs, one per pod, each with its own VFD pump | Pod cold plates → CDU → wall coupling → store |
| Thermal store | Closed-loop water and propylene glycol between the two concrete walls | Decouples the two sides, buffers load and steadies cooler staging |
| Heat rejection | 30 dry coolers of 2 MW, each with its own pump, in 10 steel frames. 25 carry the load. | Store → cast-in conduit → pump → cooler → cast-in conduit → store |

Central control manages CDU pump speed, dry cooler fan speed and staging, and cooler pump staging against store temperature and total heat load.

## Current decisions

| Design choice | Current decision | Where to change it |
| --- | --- | --- |
| Application | House and power Vera Rubin GPU racks, cooled by liquid. 50 MW. | [Cluster inputs](project.json) · [Calculations](calcs.md) |
| Concrete and jumpforming | 22 m outside diameter, 13 m inside diameter, 30 m high, ten 3 m lifts. Two 250 mm skins enclose a 4.0 m liquid gap. | [Silo inputs](project.json) · [Forms, wall lifts and farm](../gpu_silo/silo_model.py) |
| Thermal store | Water-glycol fills the gap between the skins to 29.75 m. There is no upper tank. The gap holds 6,542 m³, 1.73 M US gal, which is 87 minutes of full load on a 10 K swing. A steel lid closes the store and the bore. | [Store inputs](project.json) · [Liquid, sleeves and doorway](../gpu_silo/services.py) · [Volume](calcs.md#2-thermal-store-between-the-concrete-walls) |
| Ground entry | 0.60 × 2.30 m body inside a 0.76 × 2.40 m steel frame. Allow 50 mm each side and 100 mm overhead, giving a 0.86 × 2.50 m opening. Blocked jambs and a lintel keep the entry dry. | [Pod and opening inputs](project.json) · [Door and seals](../gpu_silo/services.py) |
| 4SU pod | Named 4SU. 5.5 m long: the 5 m bronze housing with dark side trusses holds four racks, and a solid light-grey 0.5 m section at the wall end holds the CDU and pump. All 64 are the same. | [Pod inputs and per-unit overrides](project.json) · [Body, frame, material and CDU section](../gpu_silo/cargo.py) |
| Storage and ground feed | Eight berths on each of eight levels, 2.8 m apart, which leaves 0.4 m between pods. A steel central shaft carries radial cantilevers. The hole through both walls is the only ground entry. Every pod rises from grade. | [Storage inputs](project.json) · [Cage, pickup and radial motion](../gpu_silo/pod_scene.py) |
| Parking and sequence | Berths sit 45° apart. Occupied levels rotate and bunch at 40° pitch to free the lifting lane. Fill from the top down. After the top two levels, run the remaining installation at 3×. | [Pitch and speed](project.json) · [Lift clock](../gpu_silo/pod_scene.py) |
| Pod services | A cast-in sleeve at each berth passes through the inner wall only and opens into the store. The CDU pump draws from and returns to the store through a self-sealing coupling. The outer wall is not penetrated for the pods. Sleeves stop at the top pod level, 20.95 m. Power and data reach each pod down the steel shaft. | [Berth elevations](project.json) · [Sleeves and docking](../gpu_silo/services.py) |
| Dry coolers | 30 coolers of 2 MW. Each is 12 × 2.5 × 2.5 m with outward fans and has its own 1 m pump unit at one end. 25 carry the 50 MW load and 5 are spare. | [Cooler inputs](project.json) · [Cooler, pump and frame](../gpu_silo/cooler_frames.py) |
| Cooler frames | Ten steel frames, 13 m across, 8.4 m high and 2.9 m off the wall, each holding three coolers stacked vertically behind a concrete-grey steel mesh screen. Ten frames are wider than the circumference, so they sit in two tiers of five, turned 36° from each other, at RL 12.3 to 20.7 m and RL 21.2 to 29.6 m. | [Frame size and tiers](project.json) · [Arrangement](calcs.md#frame-arrangement) |
| Frame fixings | 16 cast-in anchors per frame for the supports and 6 cast-in conduits per frame through the outer skin, a supply and a return for each cooler. All are set in the forms before their lift is poured. | [Anchor columns and conduits](project.json) · [Anchors, seats, sleeves and spools](../gpu_silo/cooler_frames.py) |
| Frame installation | The frames are hung while the pods are being loaded. The south crawler stays after the tandem cage lift, tracks anticlockwise round the silo from frame 01, picks each frame from laydown, hoists it and sets it on its seats. Two fitters in a boom lift follow and connect the pipework. | [Track, laydown, order and cycle times](project.json) · [Crawler, boom lift and crew](../gpu_silo/cooler_frames.py) · [Shared clock](../gpu_silo/clock.py) |
| Cooler service | During the pod exchange the crawler returns and lowers frame 09 to the ground, one 2 MW cooler is drawn out and replaced, and the frame is hung back on its seats. With five spare coolers a whole frame can come down at full load. | [Frame and cooler selection](project.json) · [Service choreography](../gpu_silo/service.py) · [Crawler route](../gpu_silo/crane.py) |
| Terminal and delivery | One flatbed brings three pods. The travelling gantry unloads them onto receiving cradles and the intake rail feeds the silo. | [Truck, cradles, gantry and handoff](../gpu_silo/yard.py) |
| Power modules | Two 25 MW modules, each a container section holding an aeroderivative gas turbine and generator of the GE LM2500 class. After pod loading they are lowered through the open top onto coaxial stubs above the pods. They turn 90° between levels and four exhaust vents telescope to 0.9 m above the rim. Their output goes down the steel shaft to each 4SU. The package is drawn far smaller than a real one. | [Power inputs](project.json) · [Power picks, stubs and vents](../gpu_silo/plant.py) · [Air and exhaust](calcs.md#6-power-and-fuel) |
| Turbine access | The side of the lower module facing the crew wedge is hinged at floor level. It folds down to a work floor at 24.1 m, the crew step onto it from their deck and work on the turbine, and it closes when they leave. | [Hinged side and turbine](../gpu_silo/plant.py) · [Crew moves](../gpu_silo/crew.py) |
| Bore ventilation | A panel with two fans plugs the ground door and four air vents sit in the lid. Air warmed by the pods rises and leaves at the roof, drawing cool air in at the door. The plug is set aside for a pod exchange. Natural convection carries about 28 kW. | [Ventilation inputs](project.json) · [Plug and vents](../gpu_silo/vents.py) · [Air flow](calcs.md#7-air-in-the-bore) |
| Lid | A steel lid covers the bore and the store at the rim, with the four vents standing through it. It is the crawler's last lift of the build. | [Lid and vents](../gpu_silo/plant.py) |
| Fuel | Eight propane tanks, 20 m long and 3 m in diameter, stand 64 m from the silo. One gas line runs along the ground, up the outside wall behind frame 07, across the lid and down to the power modules. 913 m³ runs the site for about 43 hours. | [Fuel inputs](project.json) · [Tanks and gas line](../gpu_silo/fuel.py) · [Run time](calcs.md#6-fuel-storage) |
| People and access | Eight solid wedge platforms board 19 technicians at grade. Seven service different pod levels. One rises to the lower power module and works on its turbine. | [Crew and destination by wedge](project.json) · [Decks, guides and poses](../gpu_silo/crew.py) |
| Pod exchange | The last scene. Level 6, bay 5, 4SU 021. Set the door plug aside, disconnect the two berths above and five below, rotate clear, lower the faulty pod, feed the spare from grade, reconnect and refit the plug. | [Fault selection](project.json) · [Exchange choreography](../gpu_silo/maintenance.py) |
| Design information on the film | A design basis strip stays on screen. The cooler, store, fuel and closing panels show figures from the calculations. | [Figures](../gpu_silo/calcs.py) · [Panels](../renderer/DesignRender.cs) |
| Flow drawings | The film closes with two drawings to scale: a plan of the cooling loop and a section showing power, water-glycol and gas. Moving dashes show direction. Hot water-glycol enters the store from the CDUs at the inner wall and cold water-glycol enters from the coolers at the outer wall. Both streams disperse into the stored liquid and nothing is piped from a cooler to a pod. The section also shows air entering at the door plug and leaving at the roof vents. | [Scene clock](../gpu_silo/closing.py) · [Drawings](../renderer/FlowRender.cs) |
| Narration | The plan view is narrated by the Kokoro voice Eric (`am_eric`). The script is an input, the recording is committed and the scene lasts as long as the recording. | [Script](narration.json) · [Recorder](../gpu_silo/narrate.py) · [Audio](../audio) |
| Camera, timing and finish | Low-poly agricultural setting at 24 fps and 1280 × 720. The concrete is solid while it is cast and in the finished views. In the cutaway views, from the cage lift to the end of the crew scene and again for the pod exchange, it is fully see-through and only its edges are drawn. | [Movie inputs](project.json) · [Cameras](../gpu_silo/pod_scene.py) · [Renderer](../renderer) · [Chapters and encoding](../gpu_silo/render_project.py) |

## How dimensions propagate

The liquid gap is `(outside diameter − inside diameter) / 2 − outer skin − inner skin`. At 22 m and 13 m with 250 mm skins it is **4.00 m**. The shaft end of a pod is at radius **0.86 m** and its wall end at **6.36 m**. The corner of the 0.76 m wide frame sweeps a radius of **6.371 m**, which leaves **129 mm** to the 6.50 m bore.

A cooler frame is flat and the wall is curved. Its back plane stands 0.20 m off the wall at its centre and 2.33 m off at each end. The anchor struts bridge that gap.

Unit numbers follow the installation order, starting at 001 on the top level, then round a level before moving down. The exchange spare has the next number. Cooler frames are numbered anticlockwise from the ground entry. Dimensions are in metres, angles in degrees and colours in sRGB hexadecimal.

[Design calculations](calcs.md) · [Decision log](history.md) · [How to preview and merge a design change](../CONTRIBUTING.md)
