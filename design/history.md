# Decision log

Add a dated entry when a choice changes. Say what the viewer should see, the dimensions or timing affected, the reason, what it replaces and a shot where it can be checked. Timestamps refer to the film released with that change. Git keeps the full source and design file behind each release.

## Decisions

| Date | Decision | Change and reason | Replaces | Where to see it |
| --- | --- | --- | --- | --- |
| 2026-11-16 | Application | The silo houses and powers GPU racks: 256 NVL72 racks in 64 pods of four, about 32 MW of liquid heat. | The earlier storage study this model was adapted from | Design basis strip, whole film |
| 2026-11-16 | Pod name and length | A pod is a **4SU**. It is 5.5 m long. The existing 5 m housing is kept as drawn. A solid light-grey 0.5 m section is added at the end that meets the wall, so the CDU and pump can be told apart from the rack housing. | 5 m pods | Terminal at 1:19, first lift at 1:33 |
| 2026-11-16 | Silo dimensions | 30 m high, 13 m inside diameter, 20 m outside diameter, sized for a 1.5 M US gal store. | 17 m clear bore with a 1 m liquid gap | Wall plan at 0:05, closing orbit at 4:11 |
| 2026-11-16 | Thermal store | Delete the upper tank. Water-glycol fills the gap between the walls to the top. | Annular steel tank above a part-filled gap, and its tanker top-up | Fill to the rim at 1:12 |
| 2026-11-16 | Dry coolers | 32 coolers of 1 MW, one pump each, in 8 steel frames spread round the silo and reaching RL 30 m. Each frame is 10 m across, 10 m high and 2.5 m off the wall and holds 4 coolers of 9 m and 4 pump units of 1 m, stacked vertically. Cast-in anchors carry the supports and several cast-in conduits serve each frame. | 16 coolers of 2.0 to 2.2 MW (32 to 35 MW) on common headers with 8 headered pumps at N+1 or N+2 | Cooler frames from 0:40 |
| 2026-11-16 | Frame installation | The crane stays after it lowers the steel pod cage and positions the 8 frames. Workers on a boom lift connect each one. | Complete cooling rings lowered over the silo | 0:40 to 1:12 |
| 2026-11-16 | Design information on the film | The film carries key design figures, starting now: a design basis strip on every scene, figures on the cooler and store panels, and a closing design basis. | Scene panels without design figures | Whole film, closing panel at 4:11 |

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

## Open questions

The [calculations](calcs.md#6-open-questions-raised-by-these-numbers) list the questions these decisions raise. The first is that the 20 m, 13 m and 30 m geometry holds 1.22 M US gal against the 1.5 M target.
