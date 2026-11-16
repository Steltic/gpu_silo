# Design calculations

This file is generated from [project.json](project.json) by `python -m gpu_silo calcs`. Change an input, run the command and commit both files. The same numbers appear on the design panels in the animation.

These are concept-stage sizing checks to steer design decisions. They are not a structural, hydraulic or thermal design and have not been reviewed by an engineer.

## 1. Cluster and heat load

| Quantity | Value | Basis |
| --- | ---: | --- |
| 4SU pods | 64 | 8 per level × 8 levels |
| GPU racks | 256 | 4 × NVIDIA NVL72 per pod |
| CDUs | 64 | one per pod, in the light-grey wall-end section |
| CDU pumps | 64 | one per CDU, VFD controlled |
| Liquid heat per rack | 125 kW | input |
| Liquid heat per pod | 500 kW | 4 racks |
| **Liquid heat load** | **32.0 MW** | 256 × 125 kW |

## 2. Thermal store between the concrete walls

The water-glycol fills the gap between the two concrete skins to 29.75 m, 0.25 m below the 30 m rim. There is no separate upper tank.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Outside / inside diameter | 20 / 13 m | input |
| Outer / inner skin | 250 / 250 mm | input |
| Liquid gap | 3.00 m | radius 6.75 to 9.75 m |
| Plan area of liquid | 155.5 m² | π (r₂² − r₁²) |
| **Volume** | **4,626 m³ = 1,222,162 US gal** | area × 29.75 m |
| Target | 5,678 m³ = 1,500,000 US gal | input |
| Volume against target | 81% | 1,052 m³ short |
| Envelope with no wall thickness, full height | 5,443 m³ = 1,437,838 US gal | upper bound for 20 / 13 / 30 m |
| Liquid mass | 4,719 t | 1020 kg/m³ |
| Heat capacity | 18.4 GJ/K = 5.11 MWh/K | cp 3.90 kJ/kg·K |
| Temperature rise with no heat rejection | 1 K every 9.6 min | at 32 MW |
| Ride-through on a 10 K swing | 96 min, 51 MWh | input swing |
| Static pressure at the base | 298 kPa | ρ g h |
| Outer skin hoop tension at the base | 2,901 kN/m, 11.6 MPa on the gross section | p r, thin wall |
| Inner skin hoop compression at the base | 2,009 kN/m, 8.0 MPa | p r, thin wall |

**The 20 m / 13 m / 30 m geometry does not hold 1.5 million US gallons.** Even with zero wall thickness the annulus holds 1.44 M gal. With two 250 mm skins it holds 1.22 M gal. Keeping the other inputs, the target needs one of:

| Change | Required value |
| --- | ---: |
| Taller silo | 36.8 m |
| Larger outside diameter | 21.12 m |
| Smaller inside diameter | 11.21 m, which no longer fits a 5.5 m pod |

## 3. Loop flows

Based on a 10 K rise across the load and the same 10 K drop across the coolers.

| Loop | Heat | Mass flow | Volume flow |
| --- | ---: | ---: | ---: |
| Whole cluster | 32 MW | 821 kg/s | 48,265 L/min, 12,750 US gpm |
| One 4SU pod (one CDU pump) | 500 kW | 12.8 kg/s | 754 L/min, 199 US gpm |
| One dry cooler (one pump) | 1000 kW | 25.6 kg/s | 1,508 L/min, 398 US gpm |

At full flow the store turns over once every 96 minutes.

## 4. Heat rejection

| Quantity | Value | Basis |
| --- | ---: | --- |
| Steel frames | 8 | 4 per tier, tiers based at 9.5 m and 20 m |
| Dry coolers | 32 × 1 MW | 4 stacked per frame |
| Cooler pumps | 32 | one per cooler |
| **Rejection capacity** | **32 MW** | |
| Margin over the heat load | 0% | 32 / 32 MW |
| One cooler out of service | 31 MW | store warms 1 K every 5.1 h at full load |
| One whole frame out of service | 28 MW | store warms 1 K every 77 min at full load |

The coolers match the load with no spare unit. The thermal store carries a single cooler outage for hours, but there is no installed N+1.

### Frame arrangement

| Quantity | Value | Basis |
| --- | ---: | --- |
| Frame | 10 m across × 10 m high × 2.5 m off the wall | input |
| Each row | 9 m cooler + 1 m pump unit | 2.50 m row height |
| Total frame width | 80 m | 8 × 10 m |
| Silo circumference | 62.8 m | π × 20 m |
| Angle taken by one frame | 58.7° | flat frame 0.20 m off the wall at its centre |
| Gap from frame back to the curved wall at each end | 1.54 m | bridged by the anchor struts |
| Cast-in anchors | 20 per frame, 160 in total | 4 columns × 5 rows |
| Cast-in conduits to the store | 8 per frame, 64 in total | supply and return for each cooler |

Eight 10 m frames need 80 m of wall and the silo has 62.8 m, so they cannot share one level. They sit in two tiers of four, each tier turned 45° from the other. The upper tier finishes at RL 30 m.

## 5. Pod fit in the bore

| Quantity | Value | Basis |
| --- | ---: | --- |
| 4SU length | 5.50 m | 5 m rack housing + 0.5 m CDU and pump section |
| Root radius on the shaft | 0.86 m | input |
| Wall-end radius | 6.36 m | |
| Corner radius of the rotating frame | 6.371 m | 0.76 m wide frame |
| Clear bore radius | 6.50 m | |
| **Radial clearance** | **129 mm** | bore − corner |
| Storage height | 20.0 m | 8 levels × 2.5 m |

## 6. Open questions raised by these numbers

1. **Tank volume.** The geometry gives 1.22 M US gal against a 1.5 M target. See the three options in section 2.
2. **Rack generation.** 125 kW per rack matches a GB200-class NVL72 (about 120 to 132 kW). Published figures for the Vera Rubin NVL72 are about 190 to 230 kW per rack, which would put 256 racks at 49 to 59 MW. Confirm the rack generation before fixing the cooler count.
3. **Cooling redundancy.** 32 MW of coolers for a 32 MW load has no spare. The earlier concept allowed 32 to 35 MW with N+1 pumps.
4. **Wall design.** 298 kPa at the base puts about 12 MPa of hoop tension in a 250 mm outer skin. That needs post-tensioning or a thicker wall, and the inner skin needs a buckling check under external pressure.
5. **Pod clearance.** 129 mm between the rotating pod and the bore is tight for a 5.5 m cantilever.
6. **Air path.** Four coolers stacked vertically discharge outward. Recirculation between rows and between the two tiers has not been checked.
7. **Electrical supply.** The two power modules in the film are placeholders. Supplying about 32 MW of IT load is not yet sized.

## Fluid properties used

Water + propylene glycol, 25% glycol by volume: density 1020 kg/m³, specific heat 3.90 kJ/kg·K. These are round values for a warm loop and should be replaced with supplier data at the design temperature. 1 US gal = 3.785 L.
