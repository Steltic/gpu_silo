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

The water-glycol fills the gap between the two concrete skins to 31.75 m, 0.25 m below the 32 m rim. There is no separate upper tank.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Outside / inside diameter | 25 / 17 m | input |
| Outer / inner skin | 250 / 250 mm | input |
| Liquid gap | 3.50 m | radius 8.75 to 12.25 m |
| Plan area of liquid | 230.9 m² | π (r₂² − r₁²) |
| **Volume** | **7,331 m³ = 1,936,724 US gal** | area × 31.75 m |
| Target | 5,678 m³ = 1,500,000 US gal | input |
| Volume against target | 129% | 1,653 m³ over |
| Envelope with no wall thickness, full height | 8,445 m³ = 2,230,828 US gal | upper bound for 25 / 17 / 32 m |
| Liquid mass | 7,478 t | 1020 kg/m³ |
| Heat capacity | 29.2 GJ/K = 8.10 MWh/K | cp 3.90 kJ/kg·K |
| Temperature rise with no heat rejection | 1 K every 9.7 min | at 50 MW |
| Ride-through on a 10 K swing | 97 min, 81 MWh | input swing |
| Static pressure at the base | 318 kPa | ρ g h |
| Outer skin hoop tension at the base | 3,890 kN/m, 15.6 MPa on the gross section | p r, thin wall |
| Inner skin hoop compression at the base | 2,779 kN/m, 11.1 MPa | p r, thin wall |

**This geometry holds 1.94 million US gallons, 29% more than the 1.5 M target.**

### Does the store match the load?

The store's job is to carry the load while heat rejection is reduced. The measure is how long the full load takes to warm the store through the usable 10 K.

| Outside diameter | Bore | Height | Load | Store | Ride-through on 10 K |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20 m | 13 m | 30 m | 32 MW | 4,626 m³ | 96 min |
| 22 m | 13 m | 30 m | 50 MW | 6,542 m³ | 87 min |
| 25 m | 17 m | 32 m | 50 MW | 7,331 m³ | 97 min (this design) |

Widening the bore from 13 m to 17 m for the in-line turbine sets takes 3,092 m³ out of the store. The 25 m outer wall and the 32 m height more than give it back.

## 3. Loop flows

Based on a 10 K rise across the load and the same 10 K drop across the coolers.

| Loop | Heat | Mass flow | Volume flow |
| --- | ---: | ---: | ---: |
| Whole cluster | 50 MW | 1282 kg/s | 75,415 L/min, 19,922 US gpm |
| One 4SU pod (one CDU pump) | 781 kW | 20.0 kg/s | 1,178 L/min, 311 US gpm |
| One dry cooler (one pump) | 2000 kW | 51.3 kg/s | 3,017 L/min, 797 US gpm |

At full flow the store turns over once every 97 minutes.

## 4. Heat rejection

| Quantity | Value | Basis |
| --- | ---: | --- |
| Steel frames | 10 | 5 per tier, tiers based at 13.2 m and 22.2 m |
| Dry coolers installed | 30 × 2 MW | 3 stacked per frame |
| Dry coolers needed for the load | 25 | 50 MW ÷ 2 MW |
| Spare coolers | 5 | N+5 |
| Cooler pumps | 30 | one per cooler |
| **Rejection capacity** | **60 MW** | |
| Margin over the heat load | 20% | 60 / 50 MW |
| One cooler out of service | 58 MW | still carries the full load |
| One whole frame out of service | 54 MW | still carries the full load |
| Two whole frames out of service | 48 MW | store warms 1 K every 4.1 h at full load |

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
| Silo circumference | 78.5 m | π × 25 m |
| Angle taken by one frame | 61.6° | flat frame 0.20 m off the wall at its centre |
| Gap from frame back to the curved wall at each end | 2.02 m | bridged by the anchor struts |
| Cast-in anchors | 16 per frame, 160 in total | 4 columns × 4 rows |
| Cast-in conduits to the store | 6 per frame, 60 in total | supply and return for each cooler |

Ten 13 m frames need 130 m of wall and the silo has 78.5 m, so they cannot share one level. They sit in two tiers of 5, each tier turned 36° from the other. The upper tier finishes at RL 30.6 m.

## 5. Pod fit in the bore

| Quantity | Value | Basis |
| --- | ---: | --- |
| 4SU length | 5.50 m | 5 m rack housing + 0.5 m CDU and pump section |
| Root radius on the shaft | 2.86 m | input |
| Wall-end radius | 8.36 m | |
| Corner radius of the rotating frame | 8.369 m | 0.76 m wide frame |
| Clear bore radius | 8.50 m | |
| **Radial clearance** | **131 mm** | bore − corner |
| Storage height | 22.2 m | 8 levels × 2.77 m |

## 6. Power

Two in-line gas turbine generator sets stand side by side on the top level, under the lid. The backup diesel sets are on the level below.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Turbine sets | 2 × 25 MW | Aeroderivative gas turbine, GE LM2500 class |
| **Generating capacity** | **50 MW** | |
| Margin over the load | 0% | no spare turbine |
| One set | 14.38 × 3.12 × 3.98 m, 94.5 t | published figures for an LM2500+ generator set |
| Diagonal of one set | 14.71 m | the bore is 17 m |
| Two sets side by side | 0.33 m clear of the wall | 1.5 m aisle between them |
| Height needed above the pods | 8.48 m | diesel level and turbine level, each with 0.6 m of floor structure |
| Height available | 8.51 m | crown at 23.49 m, lid at 32 m |
| Weight at the top of the silo | 283 t | 2 turbine sets and 4 diesel sets |

### Roof vents

The lid carries everything that breathes. There is no general ventilation of the bore.

| Vent | Flow | Size on the roof | Speed |
| --- | ---: | --- | ---: |
| Turbine exhaust, each of 2 | 70.3 kg/s at 566 °C, 167 m³/s | stack 2.4 m in diameter, 4.5 m high | 37 m/s |
| Turbine air inlet, each of 2 | 69.4 kg/s, 58 m³/s | filter house 5 × 2.6 × 2.5 m, 25 m² of filter on two faces | 2.3 m/s |
| Diesel exhaust, each of 4 | 8.5 m³/s | stack 0.6 m in diameter, 3 m high | 30 m/s |
| Diesel room air, in and out | 49 m³/s | 2 cowls of 2.5 × 2 m | 9.8 m/s |

The turbine filter face needed at 2.5 m/s is 23 m². GE's nominal ducts for this engine are 4.5 m² for the inlet and 2.8 m² for the exhaust, so the 4.5 m² stack is larger than nominal. The diesel room air removes 1180 kW radiated by the running sets at a 20 K rise. The diesel flows are typical figures for a 2.5 MW set, not datasheet values.

## 7. Fuel

### Propane for the turbines

| Quantity | Value | Basis |
| --- | ---: | --- |
| Tanks | 8 | 20 m long × 3 m diameter, 66 m from the silo axis |
| Stored liquid | 913 m³ = 241,258 US gal | 85% fill |
| Stored energy | 5,962 MWh thermal | 23.5 MJ per litre, lower heating value |
| Electricity generated | 2,146 MWh | 36% generation efficiency |
| **Run time at full load** | **43 h (1.8 days)** | 50 MW |
| Burn rate at full load | 21.3 m³/h | one tank every 5.4 h |

### Is one propane line big enough?

Yes. Both turbines at full load burn 139 MW of fuel, which is 3.00 kg/s of propane.

| How the propane travels | Density | Flow | Speed in the 200 mm line | Bore needed |
| --- | ---: | ---: | ---: | ---: |
| Liquid, pumped | 493 kg/m³ | 6.1 L/s | 0.19 m/s | 72 mm for 1.5 m/s |
| Vapour at tank pressure, 9.5 bar, 25 °C | 21 kg/m³ | 142 L/s | 4.5 m/s | 95 mm for 20 m/s |
| Vapour at turbine pressure, 30 bar, 90 °C | 55 kg/m³ | 55 L/s | 1.7 m/s | 59 mm for 20 m/s |

One 200 mm line carries the full flow in any of the three ways with room to spare. A 100 mm line would also do. The turbines need gas at about 30 bar, and propane at that pressure is liquid below about 70 °C. The practical arrangement is to pump liquid up the line and vaporise it beside the turbines. Vaporising takes 1.3 MW of heat. The store at 45 to 55 °C is too cool to do it at that pressure, so the vaporiser needs a hotter source such as turbine exhaust heat. The supply pressure is a typical figure for this class of turbine, not a datasheet value.

### Diesel for the backup sets

| Quantity | Value | Basis |
| --- | ---: | --- |
| Backup sets | 4 × 2.5 MW | 6.87 × 2.92 × 3.3 m, 23.5 t each |
| **Backup capacity** | **10 MW** | 20% of the load |
| Fuel burn, all sets at full load | 2.62 m³/h | 654 L/h per set |
| Day tanks inside | 2 × 2.7 m³ | 2.1 h at full load |
| Bulk tank outside | 64 m³ | 10 m × 3 m at the propane tanks, 90% fill |
| **Run time on the bulk tank** | **24 h** | all sets at full load |
| Diesel line | 50 mm | 0.37 m/s at full burn |

The backup covers black start, controls, the cooling plant and about a fifth of the racks. It does not cover the loss of a turbine.

## 8. Open questions raised by these numbers

1. **Store size.** 1.94 M US gal gives 97 minutes of ride-through at 50 MW. Decide the ride-through the site needs. See section 2.
2. **Rack heat.** 195 kW per rack is 50 MW over 256 racks. Published figures for the Vera Rubin NVL72 run from about 190 to 230 kW, so the upper end would be 59 MW.
3. **Generation.** Two 25 MW sets match the 50 MW load with no spare, and pumps, fans and conversion losses add to that load. The diesels cover 20%.
4. **Fit of the power levels.** The two levels need 8.48 m and have 8.51 m, so the turbine sets stand 30 mm under the lid. The floor structure for 283 t is an allowance, not a design.
5. **Wall design.** 318 kPa at the base puts about 16 MPa of hoop tension in a 250 mm outer skin. That needs post-tensioning or a thicker wall, and the inner skin needs a buckling check under external pressure.
6. **Air in the bore.** There is no general ventilation. The bore is surrounded by a store at 45 to 55 °C, so it will sit near that temperature. Work inside needs cooled air or short shifts, and this is not designed.
7. **Heat next to the pods.** Each turbine rejects about 44 MW, mostly up the stack at 566 °C. Insulation of the stacks and the turbine level above the pods and the store is not designed.
8. **Cooler air path.** Three coolers stacked vertically discharge outward at 4.6 m/s. Recirculation between rows and between the two tiers has not been checked.
9. **Lifts.** Each power level is shown lowered as one assembly. The crane, the lifting sequence and the removal route for a turbine or generator are not designed.
10. **Fuel.** 913 m³ of propane runs the site for about 43 hours. Separation distances, bunding, the vaporiser and the resupply rate have not been checked. Fuel stored inside is limited to the day tanks, and the limit that applies has not been checked.
11. **Power in the shaft.** 50 MW passes down the steel shaft to 64 pods, 781 kW each. The busbar, its cooling and the connection at each level are not designed.
12. **Pod support.** The pods now hang 2.3 m out from the shaft with a walkway ring between. The carrier ring and its arms are not designed.

## Fluid properties used

Water + propylene glycol, 25% glycol by volume: density 1020 kg/m³, specific heat 3.90 kJ/kg·K. These are round values for a warm loop and should be replaced with supplier data at the design temperature. 1 US gal = 3.785 L.
