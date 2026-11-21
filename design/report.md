# GPU Silo: structural design report

| | |
| --- | --- |
| Document | GS-STR-001 |
| Revision | A, 2026-11-21 |
| Status | Preliminary, issued for review. Not checked. Not for construction. |
| Prepared by | Claude (Anthropic), for Steltic |
| Checked by | Not yet checked |
| Approved by | Not yet approved |

This report is generated from [project.json](project.json) by `python -m gpu_silo calcs`. Every number in it is calculated by [structure.py](../gpu_silo/structure.py) from the inputs in that file. To change a result, change an input and run the command.

## Contents

1. [Purpose and scope](#1-purpose-and-scope)
2. [Register of design checks](#2-register-of-design-checks)
3. [Basis of design](#3-basis-of-design)
4. [Check 2: pod truss](#4-check-2-pod-truss)
5. [Check 1: central shaft, design loads](#5-check-1-central-shaft-design-loads)
6. [Check 6: root connection and level drive, design loads](#6-check-6-root-connection-and-level-drive-design-loads)
7. [Open items](#7-open-items)
8. [Appendix A: member forces](#appendix-a-member-forces)
9. [Appendix B: section properties](#appendix-b-section-properties)

## 1. Purpose and scope

The GPU Silo stores 64 4SU pods on 8 levels round a central steel shaft, inside a double-walled concrete silo. Each pod holds 4 GPU racks with its own coolant distribution unit (CDU) and pump. The purpose of this report is to give confidence in the predicted performance of the structure by working through a fixed list of design checks, one at a time, and recording the basis, the method and the result of each.

This revision covers:

- the register of design checks and the basis of design;
- check 2, the pod trusses, sized for gravity load;
- the dead loads that the pods put on the shaft, for check 1;
- the loads at the pod root and the rotating mass of a level, for check 6.

The shaft, its base, the hub at each level and the drive are not designed in this revision. Section 5.5 looks ahead at the stiffness of the shaft because it affects decisions that are being made now.

## 2. Register of design checks

| No. | Check | Scope | Status | Where |
| ---: | --- | --- | --- | --- |
| 1 | Steel shaft | Axial load, out-of-balance bending and lean of the central shaft, and its fixed base on the foundation | Design loads issued. Design not started. | [Section 5](#5-check-1-central-shaft-design-loads) |
| 2 | Pod trusses | The two welded side trusses that carry each 4SU pod as a cantilever | Sized for gravity load. For review. | [Section 4](#4-check-2-pod-truss) |
| 3 | Silo wall thickness | Hoop tension in the outer wall, external pressure on the inner wall, and wall thickness | Not started |  |
| 4 | Foundation | Base slab, bearing pressure, and the anchorage of the shaft base | Not started |  |
| 5 | Heat balance of the store | Water-glycol temperatures, mixing and ride-through in the store | Not started |  |
| 6 | Pod-to-shaft connection and level drive | Root connection of the pod, the hub at each level, and the capacity of the drive that turns a level | Design loads issued. Design not started. | [Section 6](#6-check-6-root-connection-and-level-drive-design-loads) |

## 3. Basis of design

### 3.1 Codes and standards

| Subject | Document |
| --- | --- |
| Structural steel | ANSI/AISC 360-22, *Specification for Structural Steel Buildings*, load and resistance factor design (LRFD) |
| Loads and combinations | ASCE/SEI 7-22, *Minimum Design Loads and Associated Criteria for Buildings and Other Structures* |
| Hollow sections | ASTM A500/A500M, Grade C |
| Section dimensions | AISC *Steel Construction Manual*, 16th edition, Table 1-11 and Table 1-12 |

The pods are equipment supports inside a structure, and the specification is applied to them as it would be to a building frame. A crane or machinery standard may also apply to the hoisting and the rotation. That is to be settled under check 6.

### 3.2 Materials

| Property | Value | Source |
| --- | ---: | --- |
| Hollow structural sections | ASTM A500 Grade C | |
| Yield stress, F<sub>y</sub> | 345 MPa (50 ksi) | ASTM A500 Grade C, shaped sections |
| Tensile strength, F<sub>u</sub> | 427 MPa (62 ksi) | ASTM A500 Grade C |
| Modulus of elasticity, E | 200 GPa (29,000 ksi) | AISC 360-22 |
| Density | 7,850 kg/m³ | |
| Design wall thickness | 0.93 × nominal | AISC 360-22 Section B4.2, for A500 sections |

### 3.3 Units

Quantities are in SI units: metres, millimetres, kilonewtons and tonnes. Steel sections keep their US names, with dimensions in inches. 1 kip = 4.448 kN and 1 in = 25.4 mm.

### 3.4 Geometry

| Quantity | Value | Basis |
| --- | ---: | --- |
| Clear bore of the silo | 17 m diameter | input |
| Shaft | 1.16 m diameter | input |
| Access round the shaft | 0.50 m | input, reduced from 2.28 m in this revision |
| Pod root radius | 1.08 m | shaft radius + access |
| Rack housing | 5 m long, 0.6 m wide, 2.3 m high | input |
| CDU and pump section | 2.28 m long | fills the pod out to 140 mm from the wall; was 0.50 m |
| Pod length, the cantilever span L | 7.28 m | |
| Pod tip radius | 8.36 m | |
| Frame envelope | 0.76 m wide, 2.40 m high | 80 mm each side of the racks for a chord |
| Levels | 8 at 2.77 m, 8 pods a level | input |
| Storage pitch and packed pitch | 45° and 40° | input |

Narrowing the access round the shaft to 0.5 m moves every pod 1.78 m towards the axis. The racks stay at the shaft end and the CDU and pump section is lengthened to fill the pod out to the wall. Two consequences are recorded here because they affect later checks.

1. **Clearance at the roots.** The pods come closest to each other at their roots. When a level is bunched at 40° the frames are 25 mm apart there, and a pod being lifted passes the pods either side of the lifting lane with 23 mm to spare. Both were over 1 m before. An access of 0.62 m would give 100 mm in both cases.
2. **Use of the access.** At 0.5 m the space round the shaft is an inspection space, not a walkway. The frames of neighbouring pods are 124 mm apart at their roots when stored, so a person cannot pass from the shaft to the wedge between two pods at pod level.

### 3.5 Loads

Dead load, D, is the only load in this revision. Fixed equipment and its liquid contents are taken as dead load, as ASCE 7-22 Chapter 3 provides.

| Item | Mass | Distribution | Status |
| --- | ---: | --- | --- |
| GPU racks | 4 × 1.6 t = 6.4 t | each rack on the two panel points of its bay | allowance. No shipping or operating weight is published for the Vera Rubin NVL72. |
| CDU and pump | 0.6 t | uniform over the CDU and pump section | allowance |
| Coolant and piping | 0.4 t | uniform over the pod | allowance |
| Truss steel | calculated | at the nodes of each member | from the design |
| Cross members and plan bracing | calculated | uniform over the pod | HSS2×2×3/16, one top and one bottom at each panel point, and a plan diagonal in each panel, top and bottom |
| Connections | 10% of the steel | with the steel | allowance |
| Housing | 10 kg/m² of rack housing and CDU enclosure | uniform over the pod | allowance |

Loads that are not yet included are listed in section 4.11.

### 3.6 Load combinations

| Case | Combination | Basis |
| --- | --- | --- |
| Strength, docked | 1.4 D | ASCE 7-22 Section 2.3.1, combination 1 |
| Strength, hoisted | 1.4 × 1.25 D | the same, with a 25% allowance for vertical impact, as ASCE 7-22 Section 4.9.3 gives for a powered bridge crane |
| Deflection | 1.0 D | |

### 3.7 Serviceability

The tip of each pod carries the coupling that connects its CDU to the water-glycol store through a sleeve in the inner wall. The vertical position of the tip therefore matters, and it is controlled by a limit on the tip deflection of the truss under dead load.

**Criterion: tip deflection ≤ span/1,000 = 7.3 mm.**

This is a project criterion and not a code minimum. The tolerance of the coupling is not yet known. The limit is an input, and section 4.9 shows what other limits would require. The truss is only one of three contributions to the drop of the tip. The rotation of the root connection and the lean of the shaft are the others, and they belong to checks 6 and 1.

## 4. Check 2: pod truss

### 4.1 Description

Each pod is carried by two vertical trusses, one each side of the racks, 0.68 m apart centre to centre. They are joined top and bottom at every panel point by cross members and plan bracing, so the pair acts as a box. The trusses are 2.40 m deep overall and span 7.28 m as cantilevers from the hub on the shaft.

- **Chords.** Rectangular hollow sections with the long side vertical, no wider than 3 in (76 mm) so that they fit in the 80 mm beside the racks. An I-section was considered. No rolled W-shape has a flange narrower than about 100 mm, so an I-section chord would widen the pod, and a hollow section also gives a flat face to weld the web members to.
- **Web.** Square hollow sections. There is a vertical at every panel point and one diagonal in each panel. The diagonals fall towards the tip, so they are in tension when the pod is docked and the shorter verticals take the compression.
- **Panels.** One panel to each rack, 1.25 m long, so that each rack bears on panel points. The CDU and pump section has 2 panels of 1.14 m.
- **Joints.** Fully welded.
- **Support.** At the root the top chord is held by a clevis that takes the pull and the whole weight. The bottom chord bears on the hub and takes thrust only.

![Elevation of one side truss with member forces](figures/pod_truss.svg)

### 4.2 Design criteria

| No. | Criterion | Limit | Basis |
| ---: | --- | --- | --- |
| 1 | Tip deflection under dead load | span/1,000 = 7.3 mm | section 3.7 |
| 2 | Member strength | required strength ≤ design strength | AISC 360-22 Chapters D and E |
| 3 | Member slenderness | L<sub>c</sub>/r ≤ 200 for every member | AISC 360-22 Section E2, user note. Applied to all members because the web forces reverse when the pod is hoisted. |
| 4 | Wall slenderness | (b − 3t)/t ≤ 1.40 √(E/F<sub>y</sub>) = 33.7 | AISC 360-22 Table B4.1a, case 6. No slender walls. |
| 5 | Joint geometry | web width between 0.25 and 1.0 of the chord width | AISC 360-22 Chapter K, limits of applicability |
| 6 | Chord width | ≤ 3 in | the frame envelope |

The lightest pair of sections from the lists in the design file that meets all six is chosen. The lists hold 11 chord sizes from HSS4×3×3/16 to HSS8×3×3/8 and 7 web sizes from HSS2×2×3/16 to HSS3×3×5/16, none with a wall thinner than 3/16 in.

### 4.3 Analysis

Each truss is analysed as a pin-jointed plane truss by the direct stiffness method, with half the pod's load applied at its panel points. Member lengths are taken between the centre lines of the chords, 2.298 m apart. The welded joints make the real truss slightly stiffer than the model, so the calculated deflection is an upper estimate for the truss alone.

Two support cases are analysed:

1. **Docked.** A cantilever from the root, as in Figure 1.
2. **Hoisted.** Hanging from the hoist's two pickups on the top chord, at panel points 1 and 4, which are 1.25 m and 5.00 m from the root. The pickups carry 46.5 kN and 40.1 kN for the whole pod, unfactored.

Compression members are checked for flexural buckling with an effective length equal to the distance between panel points.

### 4.4 Selected sections

| Member | Section | Size, mm | Steel |
| --- | --- | --- | --- |
| Top and bottom chords | **HSS4×3×3/16**, long side vertical | 102 deep × 76 wide × 4.8 wall | ASTM A500 Grade C |
| Verticals and diagonals | **HSS2×2×3/16** | 51 × 51 × 4.8 wall | ASTM A500 Grade C |
| Cross members and plan bracing | HSS2×2×3/16 | 51 × 51 × 4.8 wall | ASTM A500 Grade C |

### 4.5 Deflection

| Quantity | Value |
| --- | ---: |
| Tip deflection under dead load, stiffness analysis | **5.34 mm** |
| As a fraction of the span | span/1,362 |
| Limit | 7.28 mm (span/1,000) |
| Tip deflection by statics and virtual work (section 4.7) | 5.34 mm |
| **Result** | **Satisfied**, 73% of the limit |

The truss is 0.33 of its span deep, which is very deep for a cantilever. Two things follow.

- The lightest sections in the list already meet span/1,000. Stiffness does not call for more steel than the minimum practical sizes at this limit.
- The verticals and diagonals contribute 3.3 mm of the deflection and the chords 2.1 mm. Heavier sections buy little either way. HSS6×3×1/4 chords with the same web give 4.7 mm for 242 kg more steel a pod, and HSS3×3×1/4 web members with the same chords give 3.9 mm for 424 kg more.

### 4.6 Strength

Required strengths are the larger of the docked and hoisted cases with the factors in section 3.6. Design strengths are φ<sub>t</sub>F<sub>y</sub>A<sub>g</sub> in tension (Section D2, φ<sub>t</sub> = 0.90) and φ<sub>c</sub>F<sub>cr</sub>A<sub>g</sub> in compression (Section E3, φ<sub>c</sub> = 0.90). Tensile rupture does not govern for members welded all round, because 0.75 F<sub>u</sub> exceeds 0.90 F<sub>y</sub> for this steel.

| Member group | Section | Tension, kN | Design tension strength, kN | Compression, kN | Longest, m | L<sub>c</sub>/r | Design compression strength, kN | Highest ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Top chord | HSS4×3×3/16 | 49.5 | 449.0 | 4.2 | 1.25 | 41 | 396.0 | 0.11 |
| Bottom chord | HSS4×3×3/16 | 4.2 | 449.0 | 78.8 | 1.25 | 41 | 396.0 | 0.20 |
| Diagonal | HSS2×2×3/16 | 61.5 | 239.4 | 19.1 | 2.62 | 141 | 60.7 | 0.31 |
| Vertical | HSS2×2×3/16 | 26.9 | 239.4 | 41.4 | 2.30 | 124 | 78.7 | 0.53 |

The most heavily used member is the vertical at panel point 1, at 0.53. Every member has a reserve of strength, and no member governs the design. Forces in each member are in Appendix A.

### 4.7 Verification

The stiffness analysis is checked in three ways each time the report is generated. The checks are in [structure.py](../gpu_silo/structure.py) and the build fails if one does not hold.

| Check | Stiffness analysis | Independent value | Agreement |
| --- | ---: | ---: | --- |
| Tip deflection, by method of sections and virtual work | 5.344 mm | 5.344 mm | within 0.00% |
| Vertical reaction of one truss against half the pod weight | 43.33 kN | 43.33 kN | equal |
| Root couple of one truss against half the root moment | 129.4 kN·m | 129.4 kN·m | equal |

Section properties are calculated from the nominal size, the design wall thickness and an outside corner radius of twice the wall. For HSS6×3×1/4 this gives 3.83 in² and 13.92 lb/ft against 3.84 in² and 13.91 lb/ft in the AISC Manual. The properties of the selected sections are in Appendix B and should be compared with the Manual at the checking stage.

### 4.8 Weight of a pod

| Item | Mass, kg | Basis |
| --- | ---: | --- |
| Two trusses | 760 | HSS4×3×3/16 chords, HSS2×2×3/16 web |
| Cross members and plan bracing | 161 | 25.1 m of HSS2×2×3/16 |
| Connections | 92 | 10% of the steel |
| Housing | 422 | 10 kg/m² |
| **Frame and housing** | **1,436** | the earlier allowance was 1,500 kg for a 5.5 m pod |
| Racks | 6,400 | allowance |
| CDU and pump | 600 | allowance |
| Coolant and piping | 400 | allowance |
| **One pod, operating** | **8,836** | 86.7 kN |

Steel is 10% of the weight of a pod. The racks are 72%, so the rack weight is the number that most needs confirming.

### 4.9 Sensitivity to the deflection limit

The table gives the lightest design in the list for other limits, with all the other criteria unchanged.

| Limit | Allowed, mm | Chords | Web | Tip deflection, mm | As a fraction | Steel a pod, kg | Pod, t |
| --- | ---: | --- | --- | ---: | --- | ---: | ---: |
| span/360 | 20.2 | HSS4×3×3/16 | HSS2×2×3/16 | 5.3 | span/1,362 | 922 | 8.84 |
| span/600 | 12.1 | HSS4×3×3/16 | HSS2×2×3/16 | 5.3 | span/1,362 | 922 | 8.84 |
| span/1,000 | 7.3 | HSS4×3×3/16 | HSS2×2×3/16 | 5.3 | span/1,362 | 922 | 8.84 |
| span/1,500 | 4.9 | HSS4×3×3/16 | HSS2×2×1/4 | 4.8 | span/1,532 | 1,024 | 8.95 |
| span/2,000 | 3.6 | HSS5×3×1/4 | HSS2-1/2×2-1/2×1/4 | 3.6 | span/2,003 | 1,354 | 9.31 |
| span/2,500 | 2.9 | HSS7×3×1/4 | HSS3×3×5/16 | 2.8 | span/2,565 | 1,806 | 9.81 |

### 4.10 Conclusion

HSS4×3×3/16 chords with HSS2×2×3/16 verticals and diagonals carry the pod with a tip deflection of 5.3 mm, which is span/1,362, and a highest strength ratio of 0.53. The design is governed by the minimum practical section sizes and not by stiffness or strength under gravity. A pod weighs 8.84 t in operation.

The result holds for gravity load only. The items in section 4.11 could change the section sizes, the lateral case most of all, and the design should not be treated as final until they are closed.

### 4.11 Not covered by this check

1. **Lateral load.** The pair of trusses is only 0.68 m wide and cantilevers 7.28 m sideways as well as downwards. Earthquake load and the starting and stopping of a level act sideways on it. The site and its seismic design category are not yet fixed. This case is likely to govern the chords and the plan bracing.
2. **Welded joints.** The connections between hollow sections are to be designed to AISC 360-22 Chapter K. Only the width ratio is checked here.
3. **Root connection.** The clevis, the bearing and their effect on the tip deflection are part of check 6.
4. **Local loads.** The racks are assumed to bear at panel points through the cross members. Rack feet that land between panel points would bend the bottom chord.
5. **Transport.** The pods travel upright, two side by side on a flatbed. Road loads and tie-down points are not checked.
6. **Fatigue.** The number of lifts and rotations in the life of a pod is small, so fatigue is not expected to govern. This is to be confirmed with the service plan.
7. **Temperature.** The bore is expected to sit near the temperature of the store. Differential movement between the pod and the wall sleeve is not checked.

## 5. Check 1: central shaft, design loads

The shaft itself is not designed in this revision. This section gives the loads that the pods, as now designed, put on it.

### 5.1 Arrangement assumed

The loads below assume the arrangement shown in the animation.

- The shaft is fixed to the foundation at its base and does not turn.
- Each level has a hub that turns on the shaft. The eight pods of a level hang from the hub.
- The store is filled from the top level down. A pod is lifted up a lane at the ground entry by the hoist under the crown.
- While a pod is being lifted, every level that is already full closes up from 45° to 40° between pods to open the lane.

The base of the shaft is to be a heavy fixed connection to the foundation, because of the out-of-balance loads in section 5.3. It is designed with the foundation under checks 1 and 4.

### 5.2 Dead load from the pods

| Quantity | Value | Basis |
| --- | ---: | --- |
| Weight of one pod, W | 86.7 kN (8.84 t) | section 4.8 |
| Centre of gravity from the root | 2.99 m | |
| Centre of gravity from the shaft axis | 4.07 m | root radius 1.08 m |
| Moment of one pod at its root | 259 kN·m | |
| Moment of one pod about the shaft axis, M<sub>pod</sub> | **352 kN·m** | |
| Weight of one level, 8 pods | 693 kN (70.7 t) | |
| Weight of 64 pods on the shaft | **5,546 kN (565 t)** | |

All values are unfactored. They exclude the hubs, the bearings, the access floors and the self-weight of the shaft, which are not yet designed. The earlier allowance was 8.5 t a pod with its centre of gravity about 5.6 m from the axis, which is about 467 kN·m. The pod is now +0.34 t and its centre of gravity is 1.5 m closer to the axis, because the racks have moved to the shaft end. The moment of a pod about the axis is 25% lower.

### 5.3 Out-of-balance moment

A complete level stored at 45° is balanced and puts no moment on the shaft. Moment arises in two ways while the store is being filled or a pod is being exchanged.

| State | Moment on the shaft | In terms of M<sub>pod</sub> |
| --- | ---: | ---: |
| One complete level, stored at 45° | 0 | 0 |
| One complete level, bunched at 40° | 352 kN·m | 1.00 |
| One level part filled, worst number of pods | 921 kN·m | 2.61 |
| **Worst state in the filling sequence, at the base** | **3,127 kN·m** | **8.87** |
| Every level half filled on the same side, at the base | 7,367 kN·m | 20.9 |

The worst state in the sequence has 7 levels full and bunched and 5 pods on the level being filled. The moments of the bunched levels all point away from the lifting lane, so they add up the height of the shaft. Figure 2 shows this state.

The last row is not part of the planned sequence. It is the moment that would arise if the fill order were not controlled, and it is 2.4 times the sequence value. Whether the shaft and its base are designed for the sequence value or for the uncontrolled value is a decision for check 1.

![Plan of the worst out-of-balance state](figures/shaft_unbalance.svg)

### 5.4 Loads at the base of the shaft

| Load | Value | Note |
| --- | ---: | --- |
| Vertical load from the pods | 5,546 kN | unfactored, excludes the shaft, hubs and floors |
| Moment, worst state in the filling sequence | 3,127 kN·m | unfactored, shaft free at the top |
| Moment, uncontrolled fill | 7,367 kN·m | unfactored, shaft free at the top |
| Shear | 0 | gravity produces couples, not shear, unless the shaft is restrained at the crown |

### 5.5 Look ahead: lean of the shaft

Check 1 has not started, but one result is given now because it bears on the layout. When the shaft leans, each pod tilts with it and its tip drops by the slope of the shaft times the tip radius of 8.36 m. A drop of 5 mm at the tip is used here as a trial limit.

| Case, worst state in the filling sequence | Slope of the shaft | Drop at a pod tip | Moment at the base |
| --- | ---: | ---: | ---: |
| Tube 1160 mm diameter × 50 mm wall, free at the top | 5.8 mrad | **48 mm** | 3,127 kN·m |
| The same tube, held in position at the crown | 0.13 mrad | **1.1 mm** | 373 kN·m |

| Stiffness | EI, GN·m² |
| --- | ---: |
| Needed for 5 mm at the tip, shaft free at the top | 52 |
| Trial tube, 1160 × 50 mm | 5.4 |
| Solid steel bar of 1160 mm diameter | 17.8 |

A free-standing shaft of the present diameter cannot hold the pods level during filling. A solid bar of that diameter has 34% of the stiffness needed. Three ways to deal with this are open.

1. **Hold the top of the shaft in position**, through the crown of the cage to the inner wall. This cuts the lean by a factor of about 43 and the base moment by a factor of about 8. It puts a horizontal force of 117 kN on the wall at the crown.
2. **A larger shaft.** A free-standing tube with a 50 mm wall would need to be about 2.4 m in diameter. That takes back space just given to the pods.
3. **A filling sequence that keeps the levels balanced**, which changes how the lifting lane is opened.

The trial tube and the trial limit are inputs for this comparison and are not design values.

### 5.6 Decisions needed for check 1

1. Is the shaft held at the crown, and by what: the crown of the cage, or the floors of the power levels?
2. Is the base designed for the filling sequence or for an uncontrolled fill?
3. What carries the two power levels and the lid, about 283 t of machinery: the shaft, the cage or the wall?
4. What drop at a pod tip can the wall coupling accept?

## 6. Check 6: root connection and level drive, design loads

The connection and the drive are not designed in this revision. These are the loads from the pods as now designed, unfactored.

### 6.1 At the root of one pod

| Load | One truss | One pod |
| --- | ---: | ---: |
| Pull on the upper clevis | 56.3 kN | 112.6 kN |
| Thrust on the lower bearing | 56.3 kN | 112.6 kN |
| Weight on the upper clevis | 43.3 kN | 86.7 kN |
| Lever arm between clevis and bearing | 2.298 m | |

The tip drops 3.2 mm for each millimetre of horizontal slack or stretch between the clevis and the bearing. The stiffness and fit of the root connection will therefore matter more to the position of the tip than the truss does.

### 6.2 For the drive of one level

| Quantity | Value | Basis |
| --- | ---: | --- |
| Rotating weight of a full level | 693 kN | pods only |
| Mass moment of inertia of one pod about the shaft axis | 178,712 kg·m² | |
| Mass moment of inertia of a full level | **1,429,696 kg·m²** | pods only |
| Out-of-balance moment on the hub bearing, level part filled | 921 kN·m | section 5.3 |
| Out-of-balance moment on the hub bearing, level bunched | 352 kN·m | section 5.3 |
| Torque to accelerate a full level, turning one bay in 60 s | 1.2 kN·m | accelerating for half the turn and braking for half |

The inertia torque is small. The drive will be sized by the friction of the hub bearing under the weight and the out-of-balance moment, and by holding a level against the lean of the shaft. Both depend on the bearing chosen under check 6.

Check 6 also needs one point settled. The animation shows each level turning on a fixed shaft, with the pods of a level able to close up. If instead the whole shaft is to turn, the base cannot be a fixed connection and the loads in section 5.4 pass through a slewing bearing.

## 7. Open items

| No. | Item | Affects | Needed from |
| ---: | --- | --- | --- |
| 1 | Weight of a rack in operation, and of the CDU, pump and coolant | checks 1, 2, 4 and 6 | equipment supplier |
| 2 | Tolerance of the wall coupling, to fix the limit on tip drop | checks 1, 2 and 6 | coupling supplier |
| 3 | Site and seismic design category, for the lateral case | checks 1 to 4 and 6 | project |
| 4 | Clearance of 23 mm between pod frames at the roots: accept, or widen the access to 0.62 m | layout | project |
| 5 | Restraint of the shaft at the crown | check 1 | project, section 5.6 |
| 6 | Fixed shaft with turning levels, or a turning shaft | checks 1 and 6 | project, section 6.2 |
| 7 | Load path of the power levels and the lid | checks 1, 3 and 4 | project |
| 8 | Comparison of section properties with the AISC Manual | check 2 | checker |

## Appendix A: member forces

One side truss. Forces are unfactored in the docked and hoisted columns, tension positive. Factored values use the combinations in section 3.6. Panels are numbered from 1 at the root. For a vertical the number is its panel point, from 0 at the root.

| Member | Panel | Length, m | Docked, kN | Hoisted, kN | Factored tension, kN | Factored compression, kN | KL/r | Ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Top chord | 1 | 1.250 | +35.3 | +2.6 | 49.5 | 0.0 | 41 | 0.11 |
| Top chord | 2 | 1.250 | +19.4 | -2.4 | 27.2 | 4.2 | 41 | 0.06 |
| Top chord | 3 | 1.250 | +8.6 | -2.3 | 12.1 | 4.0 | 41 | 0.03 |
| Top chord | 4 | 1.250 | +2.9 | +2.9 | 5.1 | 0.0 | 41 | 0.01 |
| Top chord | 5 | 1.140 | +0.8 | +0.8 | 1.3 | 0.0 | 38 | 0.00 |
| Top chord | 6 | 1.140 | -0.0 | +0.0 | 0.0 | 0.0 | 38 | 0.00 |
| Bottom chord | 1 | 1.250 | -56.3 | +0.0 | 0.0 | 78.8 | 41 | 0.20 |
| Bottom chord | 2 | 1.250 | -35.3 | -2.6 | 0.0 | 49.5 | 41 | 0.12 |
| Bottom chord | 3 | 1.250 | -19.4 | +2.4 | 4.2 | 27.2 | 41 | 0.07 |
| Bottom chord | 4 | 1.250 | -8.6 | +2.3 | 4.0 | 12.1 | 41 | 0.03 |
| Bottom chord | 5 | 1.140 | -2.9 | -2.9 | 0.0 | 5.1 | 38 | 0.01 |
| Bottom chord | 6 | 1.140 | -0.8 | -0.8 | 0.0 | 1.3 | 38 | 0.00 |
| Diagonal | 1 | 2.616 | +43.9 | -5.4 | 61.5 | 9.5 | 141 | 0.26 |
| Diagonal | 2 | 2.616 | +33.3 | +10.4 | 46.6 | 0.0 | 141 | 0.19 |
| Diagonal | 3 | 2.616 | +22.6 | -0.2 | 31.6 | 0.4 | 141 | 0.13 |
| Diagonal | 4 | 2.616 | +12.0 | -10.9 | 16.7 | 19.1 | 141 | 0.31 |
| Diagonal | 5 | 2.566 | +4.9 | +4.9 | 8.6 | 0.0 | 138 | 0.04 |
| Diagonal | 6 | 2.566 | +1.7 | +1.7 | 3.0 | 0.0 | 138 | 0.01 |
| Vertical | 0 | 2.298 | +4.5 | +4.5 | 7.9 | 0.0 | 124 | 0.03 |
| Vertical | 1 | 2.298 | -29.5 | +13.8 | 24.1 | 41.4 | 124 | 0.53 |
| Vertical | 2 | 2.298 | -20.2 | -0.1 | 0.0 | 28.3 | 124 | 0.36 |
| Vertical | 3 | 2.298 | -10.8 | +9.2 | 16.2 | 15.2 | 124 | 0.19 |
| Vertical | 4 | 2.298 | -4.7 | +15.4 | 26.9 | 6.6 | 124 | 0.11 |
| Vertical | 5 | 2.298 | -1.8 | -1.8 | 0.0 | 3.2 | 124 | 0.04 |
| Vertical | 6 | 2.298 | -0.2 | -0.2 | 0.0 | 0.3 | 124 | 0.00 |

## Appendix B: section properties

Calculated as described in section 4.7.

| Section | Depth × width, mm | Nominal wall, mm | Design wall, mm | Area, mm² (in²) | r<sub>x</sub>, mm | r<sub>y</sub>, mm | Mass, kg/m (lb/ft) | Wall slenderness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HSS4×3×3/16 | 102 × 76 | 4.76 | 4.43 | 1,446 (2.24) | 37.7 | 30.2 | 12.1 (8.15) | 19.9 |
| HSS2×2×3/16 | 51 × 51 | 4.76 | 4.43 | 771 (1.20) | 18.6 | 18.6 | 6.4 (4.32) | 8.5 |
