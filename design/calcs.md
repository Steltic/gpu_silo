# Design calculations

This file is generated from [project.json](project.json) by `python -m gpu_silo calcs`. Change an input, run the command and commit both files. The same numbers appear on the design panels in the animation.

These are concept-stage sizing checks to steer design decisions. They are not a structural, hydraulic or thermal design and have not been reviewed by an engineer.

## 1. Cluster and heat load

| Quantity | Value | Basis |
| --- | ---: | --- |
| 4SU pods | 64 | 8 per level × 8 levels |
| GPU racks | 256 | 4 × NVIDIA Vera Rubin NVL72 per pod |
| CDUs | 64 | one per pod, in the light-grey wall-end section |
| CDU pumps | 64 | one per CDU, VFD controlled |
| Liquid heat per rack | 195 kW | input |
| Liquid heat per pod | 781 kW | 4 racks |
| **Liquid heat load** | **50.0 MW** | 256 × 195 kW |

## 2. Thermal store between the concrete walls

The water-glycol fills the gap between the two concrete skins to 29.75 m, 0.25 m below the 30 m rim. There is no separate upper tank.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Outside / inside diameter | 22 / 13 m | input |
| Outer / inner skin | 250 / 250 mm | input |
| Liquid gap | 4.00 m | radius 6.75 to 10.75 m |
| Plan area of liquid | 219.9 m² | π (r₂² − r₁²) |
| **Volume** | **6,542 m³ = 1,728,310 US gal** | area × 29.75 m |
| Target | 5,678 m³ = 1,500,000 US gal | input |
| Volume against target | 115% | 864 m³ over |
| Envelope with no wall thickness, full height | 7,422 m³ = 1,960,688 US gal | upper bound for 22 / 13 / 30 m |
| Liquid mass | 6,673 t | 1020 kg/m³ |
| Heat capacity | 26.0 GJ/K = 7.23 MWh/K | cp 3.90 kJ/kg·K |
| Temperature rise with no heat rejection | 1 K every 8.7 min | at 50 MW |
| Ride-through on a 10 K swing | 87 min, 72 MWh | input swing |
| Static pressure at the base | 298 kPa | ρ g h |
| Outer skin hoop tension at the base | 3,199 kN/m, 12.8 MPa on the gross section | p r, thin wall |
| Inner skin hoop compression at the base | 2,009 kN/m, 8.0 MPa | p r, thin wall |

**This geometry holds 1.73 million US gallons, 15% more than the 1.5 M target.**

### Does the store match the load?

The store's job is to carry the load while heat rejection is reduced. The measure is how long the full load takes to warm the store through the usable 10 K.

| Silo outside diameter | Load | Store | Ride-through on 10 K |
| --- | ---: | ---: | ---: |
| 20 m (earlier design) | 32 MW | 4,626 m³ | 96 min |
| 20 m | 50 MW | 4,626 m³ | 61 min |
| 22 m (this design) | 50 MW | 6,542 m³ | 87 min |

Going from 20 m to 22 m adds 1,916 m³ and brings the ride-through at 50 MW from 61 to 87 minutes. The earlier 32 MW design had 96 minutes. Matching that at 50 MW needs an outside diameter of 22.7 m, or a silo 33.1 m high at 22 m.

## 3. Loop flows

Based on a 10 K rise across the load and the same 10 K drop across the coolers.

| Loop | Heat | Mass flow | Volume flow |
| --- | ---: | ---: | ---: |
| Whole cluster | 50 MW | 1282 kg/s | 75,415 L/min, 19,922 US gpm |
| One 4SU pod (one CDU pump) | 781 kW | 20.0 kg/s | 1,178 L/min, 311 US gpm |
| One dry cooler (one pump) | 2000 kW | 51.3 kg/s | 3,017 L/min, 797 US gpm |

At full flow the store turns over once every 87 minutes.

## 4. Heat rejection

| Quantity | Value | Basis |
| --- | ---: | --- |
| Steel frames | 10 | 5 per tier, tiers based at 12.3 m and 21.2 m |
| Dry coolers installed | 30 × 2 MW | 3 stacked per frame |
| Dry coolers needed for the load | 25 | 50 MW ÷ 2 MW |
| Spare coolers | 5 | N+5 |
| Cooler pumps | 30 | one per cooler |
| **Rejection capacity** | **60 MW** | |
| Margin over the heat load | 20% | 60 / 50 MW |
| One cooler out of service | 58 MW | still carries the full load |
| One whole frame out of service | 54 MW | still carries the full load |
| Two whole frames out of service | 48 MW | store warms 1 K every 3.6 h at full load |

25 coolers carry the load and ten frames of three give 30, so 5 are spare. A whole frame can be lowered for service at full load.

### One 2 MW cooler

| Quantity | Value | Basis |
| --- | ---: | --- |
| Casing | 12 × 2.5 × 2.5 m | input |
| Water-glycol flow | 51.3 kg/s, 3,017 L/min | 10 K drop |
| Pipe bore for 2 m/s | 179 mm | supply and return conduits are drawn at 300 mm |
| Air flow | 138 m³/s | 12 K air rise |
| Face velocity | 4.6 m/s | over the 30 m² outward face |
| Fans drawn | 5 | one per 2.25 m of length |

A face velocity of 4.6 m/s is high for a dry cooler, where 2 to 4 m/s is usual. A 2 MW unit in this casing needs a larger air rise, a deeper coil or more face area. Confirm against a supplier selection.

### Frame arrangement

| Quantity | Value | Basis |
| --- | ---: | --- |
| Frame | 13 m across × 8.4 m high × 2.9 m off the wall | input |
| Each row | 12 m cooler + 1 m pump unit | 2.80 m row height |
| Total frame width | 130 m | 10 × 13 m |
| Silo circumference | 69.1 m | π × 22 m |
| Angle taken by one frame | 71.0° | flat frame 0.20 m off the wall at its centre |
| Gap from frame back to the curved wall at each end | 2.33 m | bridged by the anchor struts |
| Cast-in anchors | 16 per frame, 160 in total | 4 columns × 4 rows |
| Cast-in conduits to the store | 6 per frame, 60 in total | supply and return for each cooler |

Ten 13 m frames need 130 m of wall and the silo has 69.1 m, so they cannot share one level. They sit in two tiers of 5, each tier turned 36° from the other. The upper tier finishes at RL 29.6 m.

## 5. Pod fit in the bore

| Quantity | Value | Basis |
| --- | ---: | --- |
| 4SU length | 5.50 m | 5 m rack housing + 0.5 m CDU and pump section |
| Root radius on the shaft | 0.86 m | input |
| Wall-end radius | 6.36 m | |
| Corner radius of the rotating frame | 6.371 m | 0.76 m wide frame |
| Clear bore radius | 6.50 m | |
| **Radial clearance** | **129 mm** | bore − corner |
| Storage height | 22.4 m | 8 levels × 2.8 m |

## 6. Power and fuel

| Quantity | Value | Basis |
| --- | ---: | --- |
| Power modules | 2 × 25 MW | Aeroderivative gas turbine, GE LM2500 class |
| **Generating capacity** | **50 MW** | |
| Margin over the load | 0% | no spare module |
| Combustion air, one turbine | 69.4 kg/s, 58 m³/s | published figure for a 25 MW LM2500 |
| Exhaust, one turbine | 70.3 kg/s at 566 °C, 167 m³/s | published figure |
| Exhaust vents as drawn | 2 × 0.89 m per module | 134 m/s in the vent |
| Vent diameter for 30 m/s | 1.9 m | each of 2 per module |
| Heat rejected by one turbine | 44 MW | at 36% efficiency, mostly in the exhaust |

The modules burn propane from tanks beside the silo. One gas line runs along the ground, up the outside wall, over the lid and down to the modules.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Tanks | 8 | 20 m long × 3 m diameter, 64 m from the silo axis |
| Volume of one tank | 134 m³ | cylinder with hemispherical ends |
| Stored liquid | 913 m³ = 241,258 US gal | 85% fill |
| Stored energy | 5,962 MWh thermal | 23.5 MJ per litre, lower heating value |
| Electricity generated | 2,146 MWh | 36% generation efficiency |
| **Run time at full load** | **43 h (1.8 days)** | 50 MW |
| Burn rate at full load | 21.3 m³/h | one 20 m tank every 5.4 h |

## 7. Air in the bore

A panel with 2 fans plugs the ground door and 4 vents sit in the lid. Air warmed by the pods rises, leaves through the roof and draws cool air in at the bottom.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Height of the air column | 28.8 m | door centre to the lid |
| Driving pressure | 11.3 Pa | 10 K warmer inside, ρ g h ΔT / T |
| Inlet area | 0.77 m² | 2 fans of 0.7 m in the door plug |
| Outlet area | 4.5 m² | 4 roof vents of 1.2 m |
| Air speed at the inlet | 3.1 m/s | loss coefficient 2 |
| Air flow by natural convection | 2.4 m³/s | |
| **Heat carried away** | **28 kW** | 0.06% of the 50 MW load |
| Combustion air for both turbines | 116 m³/s | 49 times the convection flow |

Natural convection through a door-sized inlet moves tens of kilowatts. That suits pods that put all of their heat into the liquid. It cannot supply the turbines, which need their own air inlets.

## 8. Open questions raised by these numbers

1. **Store size.** 1.73 M US gal gives 87 minutes of ride-through at 50 MW. Decide the ride-through the site needs. See section 2.
2. **Rack heat.** 195 kW per rack is 50 MW over 256 racks. Published figures for the Vera Rubin NVL72 run from about 190 to 230 kW, so the upper end would be 59 MW.
3. **Generation.** Two 25 MW modules match the 50 MW load with no spare, and pumps, fans and conversion losses add to that load. A 25 MW aeroderivative package with its generator, inlet filter and exhaust silencer is far larger than the 2.5 × 2.5 m section drawn.
4. **Turbine air and exhaust.** Each turbine needs about 58 m³/s of air and discharges about 167 m³/s of exhaust at 566 °C. The vents as drawn would run at 134 m/s. Inlets, vent sizes and the heat next to the pods and the store are not designed.
5. **Wall design.** 298 kPa at the base puts about 13 MPa of hoop tension in a 250 mm outer skin. That needs post-tensioning or a thicker wall, and the inner skin needs a buckling check under external pressure.
6. **Pod clearance.** 129 mm between the rotating pod and the bore is tight for a 5.5 m cantilever.
7. **Cooler air path.** Three coolers stacked vertically discharge outward at 4.6 m/s. Recirculation between rows and between the two tiers has not been checked.
8. **Frame weight.** A frame of three 12 m coolers is a heavy pick at 33 m radius. The crane and the cast-in anchors are not sized.
9. **Fuel.** 913 m³ of propane runs the site for about 43 hours. Separation distances, bunding and the resupply rate have not been checked.
10. **Power in the shaft.** 50 MW passes down the steel shaft to 64 pods, 781 kW each. The busbar, its cooling and the connection at each level are not designed.
11. **Pod spacing.** The levels are 2.8 m apart, which leaves 400 mm between pods. A full 0.5 m needs 0.7 m more height than the two power modules leave under the lid.

## Fluid properties used

Water + propylene glycol, 25% glycol by volume: density 1020 kg/m³, specific heat 3.90 kJ/kg·K. These are round values for a warm loop and should be replaced with supplier data at the design temperature. 1 US gal = 3.785 L.
