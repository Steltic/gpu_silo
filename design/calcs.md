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
| Outer / inner skin | 400 / 500 mm | input |
| Liquid gap | 3.10 m | radius 9.00 to 12.10 m |
| Plan area of liquid | 205.5 m² | π (r₂² − r₁²) |
| **Volume** | **6,524 m³ = 1,723,553 US gal** | area × 31.75 m |
| Target | 5,678 m³ = 1,500,000 US gal | input |
| Volume against target | 115% | 846 m³ over |
| Envelope with no wall thickness, full height | 8,445 m³ = 2,230,828 US gal | upper bound for 25 / 17 / 32 m |
| Liquid mass | 6,655 t | 1020 kg/m³ |
| Heat capacity | 26.0 GJ/K = 7.21 MWh/K | cp 3.90 kJ/kg·K |
| Temperature rise with no heat rejection | 1 K every 8.7 min | at 50 MW |
| Ride-through on a 10 K swing | 87 min, 72 MWh | input swing. A mixed store can be held 10 K below its limit only in mild weather. |
| Ride-through with the store layered | 85 min | [check 5](report.md#9-check-5-heat-balance-of-the-store): one pass of the store, 90% usable, in any weather |
| Static pressure at the base | 318 kPa | ρ g h |
| Outer skin hoop tension at the base | 3,843 kN/m, 9.6 MPa on the gross section | p r, thin wall |
| Inner skin hoop compression at the base | 2,858 kN/m, 5.7 MPa | p r, thin wall |

**This geometry holds 1.72 million US gallons, 15% more than the 1.5 M target.**

### Does the store match the load?

The store's job is to carry the load while heat rejection is reduced. The measure is how long the full load takes to warm the store through the usable 10 K.

| Outside diameter | Bore | Height | Load | Store | Ride-through on 10 K |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20 m | 13 m | 30 m | 32 MW | 4,034 m³ | 84 min |
| 22 m | 13 m | 30 m | 50 MW | 5,922 m³ | 79 min |
| 25 m | 17 m | 32 m | 50 MW | 6,524 m³ | 87 min (this design) |

Widening the bore from 13 m to 17 m for the in-line turbine sets takes 3,192 m³ out of the store. The 25 m outer wall and the 32 m height more than give it back.

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
| Steel frames | 10 | 5 per tier, tiers based at 13.2 m and 22.2 m |
| Dry coolers installed | 30 × 2 MW | 3 stacked per frame |
| Dry coolers needed for the load | 26 | 51.25 MW including pump heat ÷ 2 MW |
| Spare coolers | 4 | N+4 |
| Cooler pumps | 30 | one per cooler |
| **Rejection capacity** | **60 MW** | |
| Margin over the heat load | 20% | 60 / 50 MW |
| One cooler out of service | 58 MW | still carries the full load |
| One whole frame out of service | 54 MW | still carries the full load |
| Two whole frames out of service | 48 MW | store warms 1 K every 3.6 h at full load |

26 coolers carry the load and ten frames of three give 30, so 4 are spare. A whole frame can be lowered at full load when the remaining coils have sufficient measured thermal duty.

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
| 4SU length | 7.16 m | 5 m rack housing + 2.16 m CDU and pump section, which fills the pod out to 140 mm from the wall |
| Access round the shaft | 0.62 m | input |
| Root radius | 1.20 m | 0.58 m shaft radius + access |
| Wall-end radius | 8.36 m | |
| Corner radius of the rotating frame | 8.369 m | 0.76 m wide frame |
| Clear bore radius | 8.50 m | |
| **Radial clearance** | **131 mm** | bore − corner |
| Storage height | 22.2 m | 8 levels × 2.77 m |

### Clearance at the pod roots

The pods come closest to each other at their roots, and a narrower access round the shaft brings the roots closer together.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Between frames, stored at 45° | 216 mm | at the root corners |
| Between frames, bunched at 40° | 107 mm | at the root corners |
| Between a pod being lifted and the pods either side of the lifting lane | 100 mm | lane 80° wide between centre lines |
| Access that would give 100 mm in both cases | 0.62 m | |

### Pod structure and weight

The side trusses are sized in the [design report](report.md#4-check-2-pod-truss). The numbers below come from that design.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Chords | HSS6×3×3/16 | long side vertical, ASTM A500 Grade C |
| Verticals and diagonals | HSS2×2×3/16 | |
| Tip deflection under dead load | 4.9 mm | span/1,463; limit 5 mm |
| Frame and housing | 1.53 t | 1.01 t of steel, 0.10 t of connections, 0.42 t of housing |
| **One pod, operating** | **8.93 t** | 4 racks × 1.6 t, 0.6 t of CDU and pump, 0.4 t of coolant and piping, frame and housing |
| Moment of one pod about the shaft axis | 366 kN·m | centre of gravity 4.18 m from the axis |
| Weight on the shaft, 64 pods | 5,605 kN | 572 t |
| Shaft | 1160 mm diameter, 50.8 mm wall | fixed at the base and held at the top by the support rig. [Design report](report.md#5-check-1-central-shaft) |
| Movement of a pod tip from the shaft | 3.0 mm | shortening and lean in the worst filling state; limit 5 mm |
| Sideways force at the top of the shaft | 119 kN | worst filling state, into the support rig and its 16 cast-in wall mounts |

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
| Height available | 9.26 m | crown at 23.49 m, raised lid seat at 32.75 m |
| Weight at the top of the silo | 283 t | 2 turbine sets and 4 diesel sets |

### Roof vents

The lid carries the machine intakes and exhausts. Two interlocked air handlers serve the bore through separate supply and return ducts at the raised curb.

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

## 8. Trucking

Road trucks are taken at the usual US limit of 36.3 t gross (80,000 lb), working 10 hours a day. Day numbers are days after the last wall pour. The film shows a sample of each kind of load, and its counters scale to the totals below.

| Load | Vehicle | Trucks | Days | Trucks a day |
| --- | --- | ---: | ---: | ---: |
| Concrete for the walls | 7.6 m³ mixer | 250 | -9 to 0 | 25.0 |
| Pod cage steel | flatbed, 3 a level | 27 | -8 to 0 | 3.0 |
| Dry coolers with their pump units | flatbed, one each | 30 | 3 to 12 | 3.0 |
| Cooler frame steel | flatbed, one frame each | 10 | 3 to 12 | 1.0 |
| Water-glycol | 24 t tanker | 278 | 15 to 28 | 19.9 |
| 4SU pods | flatbed, 2 each | 32 | 6 to 15 | 3.2 |
| Propane tanks and the diesel tank | oversize load, one each | 9 | 8 to 11 | 2.2 |
| Propane | 36 m³ transport | 26 | 16 to 22 | 3.7 |
| Diesel | 30 m³ tanker | 3 | 16 to 22 | 0.4 |
| Turbine generator sets | heavy haul, 94.5 t each | 2 | 9 to 18 | 0.2 |
| Diesel sets | lowboy, 23.5 t each | 4 | 9 to 18 | 0.4 |
| Deck steel for the power levels | flatbed | 12 | 9 to 18 | 1.2 |

After the last pour 406 loads arrive in 28 days. The busiest days are day 16: 26, day 17: 26, day 18: 26 loads.

### Pods: the heaviest legal load

| Quantity | Value | Basis |
| --- | ---: | --- |
| One 4SU pod | 8.9 t | 4 racks × 1.6 t, 1.53 t of frame and housing as designed, 0.6 t of CDU and pump, 0.4 t of coolant and piping |
| Flatbed | 14.6 × 2.59 m deck, 21.8 t payload | five-axle tractor and trailer |
| Pods that fit on the deck | 2 | 1 end to end × 2 across |
| Pods the payload allows | 2 | 2 × 8.9 t = 17.9 t |
| **Pods on each truck** | **2** | space and weight agree |
| Height on the road | 3.90 m | limit 4.11 m |
| **Trucks for 64 pods** | **32** | |

The deck has room for 2 pods and the weight limit allows 2. The rack weight is an allowance: NVIDIA has not published a shipping weight for the Vera Rubin NVL72.

### Receiving dock

| Quantity | Value | Basis |
| --- | ---: | --- |
| Pods to load each day | 6 | 64 pods in 10 days |
| Hoist capacity | 15 pods a day | 40 minutes a pod |
| Gantry capacity | 40 pods a day | 15 minutes a pod |
| Trucks each day | 3 | 2 pods each |
| One truck unloaded in | 30 min | |
| Dock capacity | 40 trucks a day | 2 back-in lanes under one gantry |
| Cradles on the rail | 2 | 1.3 hours of work for the hoist |

In real time one lane would be enough. The second lane lets one truck back in while another unloads, and the cradles keep the hoist working if a truck is late. The film runs 10 days in under a minute, so every truck appears to arrive at once.

### Water-glycol by tanker

| Quantity | Value | Basis |
| --- | ---: | --- |
| Store | 6,524 m³, 6,655 t | section 2 |
| Of which glycol | 1,631 m³ | 25% by volume |
| One tanker | 24 t, 23.5 m³ | 36.3 t gross |
| **Tanker loads** | **278** | |
| Loads a day | 20 | 14 days, one every 30 minutes |
| Time in a bay | 30 min | 10 minutes to connect, then 1.2 m³ a minute |
| One bay unloads | 20 loads a day | |
| Bays needed / provided | 1 / 3 | 2 spare |
| Level rises | 2.3 m a day | |
| Youngest concrete the water reaches | 24 days old | lifts poured one a day, fill from day 15 |
| Bottom lift at full head | 37 days old | day 28 |

The fill is left to the last 14 days so the concrete has as long as possible to dry and gain strength first. The tankers have their own drive off the public road, so 278 loads never enter the haul ring.

### Liner inside the store

The faces of the store are sprayed with a liner before the fill, to keep the water-glycol off the concrete and its reinforcement.

| Quantity | Value | Basis |
| --- | ---: | --- |
| System | Spray-applied polyurea liner | input, to be confirmed with a coating supplier for warm water-glycol |
| Wall faces | 4,242 m² | both faces of the gap, 32 m high |
| Floor of the gap | 205 m² | |
| **Area to coat** | **4,448 m²** | |
| Liner | 2 mm, 8.9 m³ | |
| Output | 1,120 m² a day | 4 sprayers at 28 m² an hour, from 4 stages hung in the gap |
| Time needed / allowed | 4.0 / 4 days | days 11 to 14 |
| Concrete age when coated | 11 days or more | the last lift is poured on day 0 |

### Coolers, fuel and concrete

| Quantity | Value | Basis |
| --- | ---: | --- |
| One cooler with its pump unit | 11.7 t, 13 m long | one to a 14.6 m deck, 4.00 m high on the road |
| Cooler trucks | 30 | plus 10 of frame steel |
| Assist crane | 13 lifts a day | 45 minutes a cooler, 3.0 a day needed |
| Propane to fill the tanks | 913 m³ | section 7 |
| One propane transport | 36 m³, 17.7 t | MC-331 trailer at 36.3 t gross |
| **Propane loads** | **26** | 4.1 a day with the diesel, 20 a day through 2 bays |
| Fuel tanks | 8 propane and 1 diesel | one oversize load each, 34 t a propane tank |
| Concrete in the walls | 1,869 m³ | 10 lifts of 187 m³ |
| **Mixers for one lift** | **25** | 7.6 m³ each, one every 10 minutes |
| Pour time for one lift | 4.2 h | 45 m³ an hour through one pump |
| Mixers for the walls | 250 | |
| Base slab, before the walls | 1,085 m³, 143 mixers | 2 m thick, set by the project and checked in [check 4](report.md#11-check-4-foundation) |
| Reinforcement | 477 t, 22 trucks | 314 t in the walls from the design report, with 15% for laps, feet, ties and openings. The slab at 150 kg per m³ is an allowance. |

### Crew on a typical lift

| Trade | People |
| --- | ---: |
| Foreman | 1 |
| Form carpenters | 6 |
| Ironworkers | 6 |
| Concrete placers | 4 |
| Finishers | 2 |
| Jack operators | 2 |
| Pump operator | 1 |
| **Total** | **22** |

Each lift is poured, left to set, stripped, jumped 3.2 m and reset. The crew rides the forms: placers and finishers on the pour deck, ironworkers on the starter bars, carpenters and jack operators on the working platform below.

### Roads and staging areas

| Area | Layout | Used by |
| --- | --- | --- |
| Public road | 116 m north of the silo. All site traffic arrives from the west and leaves to the east, so every turn is a right turn. | everything |
| Access road and gate | Two lanes from the public road to the ring at a bearing of 143° | all trucks except the water tankers |
| Holding lanes | 4 lanes beside the access road | pod trucks waiting to be called to the dock |
| Haul ring | One-way, anticlockwise. Running lane at 42.7 m radius and a stopping lane inside it at 39.1 m. The crane track is outside it. | every truck makes one lap |
| Receiving dock | 2 back-in lanes either side of the rail, under one gantry | pod trucks |
| Cooler laydown | 10 frame positions inside the ring. Trucks stop in the stopping lane and an assist crane lifts each cooler into its frame. | cooler and frame-steel trucks |
| Water drive | Its own entrance and exit on the public road, 3 drive-through bays, a pump and a buried fill line to the wall | water tankers |
| Fuel farm | Each tank truck drives through its slot and leaves by a road out of the back. Transports unload in a 2-bay lay-by on the ring beside the tank header. | tank deliveries, propane transports |
| Concrete bays | 2 back-in bays at the pump hopper by the ground opening, before the dock is built | truck mixers |

## 9. Programme

Day 0 is the last wall pour. The concrete reaches its 28-day strength on day 28, and the work is laid out to finish that day.

| Activity | First day | Last day | Days |
| --- | ---: | ---: | ---: |
| Jumpform the walls | -9 | 0 | 10 |
| Pod cage built, a level a day | -8 | 0 | 9 |
| Strip forms, rig the cranes | 1 | 2 | 2 |
| Support rig steel fabricated | -3 | 3 | 7 |
| Lift in the pod cage | 3 | 3 | 1 |
| Support rig set, shaft held | 4 | 5 | 2 |
| Build the receiving dock | 3 | 5 | 3 |
| Coolers into their frames | 3 | 12 | 10 |
| 4SU pods delivered and loaded | 6 | 15 | 10 |
| Cooler frames hung and piped | 8 | 17 | 10 |
| Fuel tanks set | 8 | 11 | 4 |
| Power sets made ready on site | 9 | 18 | 10 |
| Spray-coat the inside of the store | 11 | 14 | 4 |
| Water-glycol fill | 15 | 28 | 14 |
| Propane and diesel fill | 16 | 22 | 7 |
| Power sets and lid lifted in | 19 | 21 | 3 |
| Fuel lines and cabling | 22 | 26 | 5 |
| Dock enclosed as the control office | 24 | 27 | 4 |
| Full strength, handed over | 28 | 28 | 1 |

The walls take 10 days at 1 lift a day and are outside the 28 days. The pod cage is built beside the silo in those days, a level a day, so it is ready to lift in on day 3. One crawler crane does every heavy lift, so the cooler frames are hung before the power levels and the lid. The power levels are fabricated on the ground while the pods load. The store is coated on days 11 to 14 and filled over the last 14 days. Commissioning follows handover and is not part of this programme. The busiest day is day 16 with about 26 loads.

## 10. Operating limits and coordination decisions

The plant and thermal store are sized against 50 MW of installed racks. Normal metered IT is capped at 46 MW, subject to available turbine power after auxiliaries and available cooling. The operator chooses the rack mix. For example, 235 full-power racks and 21 spares at 2 kW each draw 45.940 MW. Normal operation requires zero grid import. The four diesels supply the essential bus only during emergencies, with 3 MW reserved for essential plant and up to 7 MW for priority IT.

The [revision J assumption register](assumptions.md) gives the disposition of all 18 questions previously listed here. [Structural checks 7–10](report.md#7-checks-7-to-10-support-rig-shaft-connector-and-wall-mounts-design-loads) include the independent upper floor, the guided shaft collar and the wall seats. The IFC includes the buried fuel crossing, conversion plant and the individual rack positions.

## Fluid properties used

Water + propylene glycol, 25% glycol by volume: density 1020 kg/m³, specific heat 3.90 kJ/kg·K. These are round values for a warm loop and should be replaced with supplier data at the design temperature. 1 US gal = 3.785 L.
