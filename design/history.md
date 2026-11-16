# Decision log

Add a dated entry when a choice changes. Say what the viewer should see, the dimensions or timing affected, the reason, what it replaces and a shot where it can be checked. Timestamps refer to the film released with that change. Git keeps the full source and design file behind each release.

## Decisions

| Date | Decision | Change and reason | Replaces | Where to see it |
| --- | --- | --- | --- | --- |
| 2026-11-16 | Application | The silo houses and powers GPU racks: 256 NVL72 racks in 64 pods of four, about 32 MW of liquid heat. | The earlier storage study this model was adapted from | Design basis strip, whole film |
| 2026-11-16 | Pod name and length | A pod is a **4SU**. It is 5.5 m long. The existing 5 m housing is kept as drawn. A solid light-grey 0.5 m section is added at the end that meets the wall, so the CDU and pump can be told apart from the rack housing. | 5 m pods | Terminal at 0:47, first lift at 1:01 |
| 2026-11-16 | Silo dimensions | 30 m high, 13 m inside diameter, 20 m outside diameter, sized for a 1.5 M US gal store. | 17 m clear bore with a 1 m liquid gap | Wall plan at 0:05, closing orbit at 3:45 |
| 2026-11-16 | Thermal store | Delete the upper tank. Water-glycol fills the gap between the walls to the top. | Annular steel tank above a part-filled gap, and its tanker top-up | Fill to the top at 0:40 |
| 2026-11-16 | Dry coolers | 32 coolers of 1 MW, one pump each, in 8 steel frames spread round the silo and reaching RL 30 m. Each frame is 10 m across, 10 m high and 2.5 m off the wall and holds 4 coolers of 9 m and 4 pump units of 1 m, stacked vertically. Cast-in anchors carry the supports and several cast-in conduits serve each frame. | 16 coolers of 2.0 to 2.2 MW (32 to 35 MW) on common headers with 8 headered pumps at N+1 or N+2 | Cooler frames from 1:09 |
| 2026-11-16 | Frame installation | The crane stays after it lowers the steel pod cage and positions the 8 frames. Workers on a boom lift connect each one. | Complete cooling rings lowered over the silo | 1:09 to 1:52 |
| 2026-11-16 | Design information on the film | The film carries key design figures, starting now: a design basis strip on every scene, figures on the cooler and store panels, and a closing design basis. | Scene panels without design figures | Whole film, closing panel at 3:45 |
| 2026-11-16 | Pod sleeves | A 4SU sleeve passes through the inner wall only and opens into the store. Sleeves are fitted up to the top pod level. The outer wall has no pod penetrations. Power and data reach the pods down the shaft. | Sleeves through both walls with an exterior flange, a blind cover and a dry power and data duct | Shell at 0:00, coupling inset at 1:07 |
| 2026-11-16 | Lid and vents | A lid closes the top of the silo. The four power-module vents come out through it. | Open top with exhausts ending at the rim | 2:12 to 2:20 |
| 2026-11-16 | Cooler screens | Each of the 8 cooler frames carries a steel mesh screen in concrete grey. | Open frames | From 1:09, closing orbit at 3:45 |
| 2026-11-16 | Cooler frames hung during pod loading | The frames are mounted while the 4SUs are being loaded. | Frames hung before the store was filled and before pod delivery | 1:09 to 1:52 |
| 2026-11-16 | Cooler service | The pod exchange is filmed wide. In the same shot a crane lowers a cooler frame to the ground, one cooler is pulled out and replaced, and the frame goes back up on the silo. | Close shots of the pod exchange only | 3:08 to 3:32 |
| 2026-11-16 | Cutaways | In cutaway views the concrete is 100% see-through. | Tinted translucent concrete | 0:28 to 3:45 |
| 2026-11-16 | Fuel | Eight large, long propane tanks stand near the silo. Their gas line runs up the outside wall and down to the power modules. | No fuel supply shown | 4:06 |
| 2026-11-16 | Cooling loop in plan | A plan view shows hot water entering the store from the CDUs and cold water entering it at the coolers, explained by a voice-over in the Kokoro voice Eric. | — | 4:23 |
| 2026-11-16 | Section | A section through the silo shows generated power moving down from the power modules through the steel shaft into each 4SU, water flowing over the 4SUs to cool them, and gas going from the tanks to the power modules. | — | 4:56 |

## Assumptions made while applying these decisions

These were needed to draw the decisions. Each one is an input in [project.json](project.json) and is open to change.

| Date | Assumption | Reason | Input |
| --- | --- | --- | --- |
| 2026-11-16 | Every pod is 5.5 m, not one pod only. | The design has one CDU and pump per pod, so each pod needs the section. | `pod.cdu_pump_section_m`, with `cdu_pump_section_m_by_unit` for exceptions |
| 2026-11-16 | 13 m is the clear bore and 20 m is the outside face of the outer skin, with two 250 mm skins. | Keeps the skins of the earlier model. Gives a 3.0 m liquid gap. | `silo` |
| 2026-11-16 | The store fills to 29.75 m, 0.25 m below the rim. | "To the top" with a small freeboard. | `thermal_store.freeboard_m` |
| 2026-11-16 | The eight frames sit in two tiers of four, at RL 9.5 to 19.5 m and RL 20 to 30 m, alternating round the silo. | Eight 10 m frames need 80 m and the circumference is 62.8 m. Two tiers also keep the ground entry and the terminal clear. | `dry_coolers.tier_base_m` |
| 2026-11-16 | Each frame has 20 anchors and 8 conduits. | Four anchor columns at five levels, and a supply and return for each cooler. | `dry_coolers.anchor_columns_m`, `conduits_per_cooler` |
| 2026-11-16 | 125 kW of liquid heat per rack. | 32 MW over 256 racks. | `cluster.liquid_heat_per_rack_kw` |
| 2026-11-16 | The crawler travels round the silo on a 38 m radius track, with the frames stood in laydown at 22.5 m. One boom lift carries two fitters. | A crawler standing in one place cannot reach the far side of the silo past the wall. | `installation` |
| 2026-11-16 | The two power modules stay as placeholders and are lowered through the open top. | The silo must power the racks. The supply is not yet sized. | `power` |
| 2026-11-16 | The film ends with the finished silo. The regional network and tanker scenes were left out. | They belonged to the earlier study. | [Sequence](../docs/sequence.md) |
| 2026-11-16 | The frames go up anticlockwise from frame 01, the first pick 8 seconds after the first pod lift. Frames 01 and 08 stand a few degrees aside in laydown. | Keeps the crawler and the laydown clear of the rail terminal while pods are arriving. | `installation.direction`, `laydown_offset_degrees_by_frame` |
| 2026-11-16 | The lid sits on the rim at 30.03 m and the vents rise to 30.9 m. | The vents have to clear the lid. | [plant.py](../gpu_silo/plant.py) |
| 2026-11-16 | The cooler service is on frame 07, fourth cooler, and uses the retained crawler standing 7 m back from its track. | Frame 07 is a lower-tier frame near the ground entry, so it shares a shot with the pod exchange. Standing back keeps the coolers on the ground outside the crane's minimum radius. | `service.cooler_service_frame`, `cooler_service_row` |
| 2026-11-16 | Each tank is 20 m long and 3 m in diameter, filled to 85%, 60 m from the silo axis. The riser is behind frame 07. | "Large long" tanks of a size made as standard bullets. The distance is a placeholder for the separation a code check would set. | `fuel` |
| 2026-11-16 | 40% generation efficiency and 23.5 MJ per litre of propane. | Needed for a run time. Typical of gas engines, lower heating value. | `fuel.generation_efficiency`, `energy_mj_per_litre` |
| 2026-11-16 | The plan and section are drawings to scale, not 3D views. In the section the tank farm is drawn closer and smaller than scale and both sides show a lower-tier cooler frame. | Flows through a wall and inside a pod cannot be seen in the 3D model. | [FlowRender.cs](../renderer/FlowRender.cs) |
| 2026-11-16 | Only the plan view is narrated. | The voice-over was asked for on that scene. | [narration.json](narration.json) |
| 2026-11-16 | In the section, cold water-glycol enters each pod, passes the racks and returns hot. This stands for the CDU exchanging heat with the rack loop. | The split between the store loop and the rack loop inside a CDU is not designed. | [FlowRender.cs](../renderer/FlowRender.cs) |

## Open questions

The [calculations](calcs.md#7-open-questions-raised-by-these-numbers) list the questions these decisions raise. The first is that the 20 m, 13 m and 30 m geometry holds 1.22 M US gal against the 1.5 M target.
