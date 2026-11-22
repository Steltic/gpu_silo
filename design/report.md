# GPU Silo: structural design report

| | |
| --- | --- |
| Document | GS-STR-001 |
| Revision | B, 2026-11-22 |
| Status | Preliminary, issued for review. Not checked. Not for construction. |
| Prepared by | Claude (Anthropic), for Steltic |
| Checked by | Not yet checked |
| Approved by | Not yet approved |

| Revision | Date | Changes |
| --- | --- | --- |
| A | 2026-11-21 | First issue. Register of checks, basis of design, pod truss, loads on the shaft. |
| B | 2026-11-22 | Access round the shaft widened from 0.50 m to 0.62 m. Truss limit changed from span/1,000 to 5 mm. Shaft confirmed as fixed, with the levels turning on it, and held at its top by the support rig. Check 1 carried out. Checks 7, 8 and 9 added. |

This report is generated from [project.json](project.json) by `python -m gpu_silo calcs`. Every number in it is calculated by [structure.py](../gpu_silo/structure.py) from the inputs in that file. To change a result, change an input and run the command.

## Contents

1. [Purpose and scope](#1-purpose-and-scope)
2. [Register of design checks](#2-register-of-design-checks)
3. [Basis of design](#3-basis-of-design)
4. [Check 2: pod truss](#4-check-2-pod-truss)
5. [Check 1: central shaft](#5-check-1-central-shaft)
6. [Check 6: root connection and level drive, design loads](#6-check-6-root-connection-and-level-drive-design-loads)
7. [Checks 7, 8 and 9: support rig, shaft connector and wall mounts, design loads](#7-checks-7-8-and-9-support-rig-shaft-connector-and-wall-mounts-design-loads)
8. [Open items](#8-open-items)
9. [Appendix A: member forces in the pod truss](#appendix-a-member-forces-in-the-pod-truss)
10. [Appendix B: section properties](#appendix-b-section-properties)

## 1. Purpose and scope

The GPU Silo stores 64 4SU pods on 8 levels round a central steel shaft, inside a double-walled concrete silo. Each pod holds 4 GPU racks with its own coolant distribution unit (CDU) and pump. The purpose of this report is to give confidence in the predicted performance of the structure by working through a fixed list of design checks, one at a time, and recording the basis, the method and the result of each.

This revision covers:

- the register of design checks and the basis of design;
- check 2, the pod trusses, sized for gravity load;
- check 1, the central shaft, sized for gravity load;
- the loads at the pod root and the rotating mass of a level, for check 6;
- the loads on the support rig, the shaft connector and the wall mounts, for checks 7, 8 and 9.

Lateral load is not covered by any check yet, because the site is not fixed. It is the main limitation of this revision.

## 2. Register of design checks

| No. | Check | Scope | Status | Where |
| ---: | --- | --- | --- | --- |
| 1 | Steel shaft | Axial load, out-of-balance bending, shortening and lean of the central shaft, fixed at its base and held at its top | Wall thickness sized for gravity load. For review. | [Section 5](#5-check-1-central-shaft) |
| 2 | Pod trusses | The two welded side trusses that carry each 4SU pod as a cantilever | Sized for gravity load to a 5 mm tip deflection. For review. | [Section 4](#4-check-2-pod-truss) |
| 3 | Silo wall thickness | Hoop tension in the outer wall, external pressure on the inner wall, and wall thickness | Not started |  |
| 4 | Foundation | Base slab, bearing pressure, and the anchorage of the shaft base | Not started |  |
| 5 | Heat balance of the store | Water-glycol temperatures, mixing and ride-through in the store | Not started |  |
| 6 | Pod-to-shaft connection and level drive | Root connection of the pod, the hub at each level, and the capacity of the drive that turns a level on the fixed shaft | Design loads issued. Design not started. | [Section 6](#6-check-6-root-connection-and-level-drive-design-loads) |
| 7 | Top support rig | The steel rig at the crown that carries the diesel generator level and holds the top of the shaft | Design loads issued. Design not started. | [Section 7](#7-checks-7-8-and-9-support-rig-shaft-connector-and-wall-mounts-design-loads) |
| 8 | Shaft-top connector | The connector that puts the horizontal force from the top of the shaft into the support rig | Design loads issued. Design not started. | [Section 7](#7-checks-7-8-and-9-support-rig-shaft-connector-and-wall-mounts-design-loads) |
| 9 | Cast-in wall mounts | The mounts cast into the inner wall that carry the support rig, and the wall locally | Design loads issued. Design not started. | [Section 7](#7-checks-7-8-and-9-support-rig-shaft-connector-and-wall-mounts-design-loads) |

## 3. Basis of design

### 3.1 Codes and standards

| Subject | Document |
| --- | --- |
| Structural steel | ANSI/AISC 360-22, *Specification for Structural Steel Buildings*, load and resistance factor design (LRFD) |
| Loads and combinations | ASCE/SEI 7-22, *Minimum Design Loads and Associated Criteria for Buildings and Other Structures* |
| Hollow sections | ASTM A500/A500M, Grade C |
| Plate for the shaft | ASTM A572/A572M, Grade 50 |
| Section dimensions | AISC *Steel Construction Manual*, 16th edition, Table 1-11 and Table 1-12 |

The pods and the shaft are equipment supports inside a structure, and the specification is applied to them as it would be to a building frame. A crane or machinery standard may also apply to the hoisting and the rotation. That is to be settled under check 6.

### 3.2 Materials

| Property | Value | Source |
| --- | ---: | --- |
| Hollow structural sections | ASTM A500 Grade C | |
| Yield stress of hollow sections, F<sub>y</sub> | 345 MPa (50 ksi) | ASTM A500 Grade C, shaped sections |
| Tensile strength of hollow sections, F<sub>u</sub> | 427 MPa (62 ksi) | ASTM A500 Grade C |
| Design wall thickness of hollow sections | 0.93 × nominal | AISC 360-22 Section B4.2, for A500 sections |
| Shaft | ASTM A572 Grade 50 plate, rolled and seam welded | |
| Yield stress of the shaft plate, F<sub>y</sub> | 345 MPa (50 ksi) | ASTM A572 Grade 50 |
| Design wall thickness of the shaft | nominal | plate, submerged-arc welded |
| Modulus of elasticity, E | 200 GPa (29,000 ksi) | AISC 360-22 |
| Density | 7,850 kg/m³ | |

### 3.3 Units

Quantities are in SI units: metres, millimetres, kilonewtons and tonnes. Steel sections and plate keep their US sizes in inches. 1 kip = 4.448 kN and 1 in = 25.4 mm.

### 3.4 Geometry

| Quantity | Value | Basis |
| --- | ---: | --- |
| Clear bore of the silo | 17 m diameter | input |
| Shaft | 1.16 m outside diameter | input |
| Access round the shaft | 0.62 m | input, revision B |
| Pod root radius | 1.20 m | shaft radius + access |
| Rack housing | 5 m long, 0.6 m wide, 2.3 m high | input |
| CDU and pump section | 2.16 m long | fills the pod out to 140 mm from the wall |
| Pod length, the cantilever span L | 7.16 m | |
| Pod tip radius | 8.36 m | |
| Frame envelope | 0.76 m wide, 2.40 m high | 80 mm each side of the racks for a chord |
| Levels | 8 at 2.77 m, 8 pods a level | input |
| Storage pitch and packed pitch | 45° and 40° | input |
| Shaft, from the foundation to the support rig | 23.79 m | the connector is at mid-depth of the rig |

**Clearance at the pod roots.** The pods come closest to each other at their roots. With 0.62 m of access the frames are 107 mm apart there when a level is bunched at 40°, and a pod being lifted passes the pods either side of the lifting lane with 100 mm to spare. Stored at 45° the frames are 216 mm apart at the roots, so the space round the shaft is an inspection space and there is no way through at pod level to the wedge between two pods.

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
| Hub, bearing and access floor | 3 t a level | at each hub | allowance, to be replaced under check 6 |
| Shaft | calculated | uniform | from the design |
| Power and data services inside the shaft | 300 kg/m | uniform | allowance |

### 3.6 Load combinations

| Case | Combination | Basis |
| --- | --- | --- |
| Strength | 1.4 D | ASCE 7-22 Section 2.3.1, combination 1 |
| Strength, pod hoisted | 1.4 × 1.25 D | the same, with a 25% allowance for vertical impact, as ASCE 7-22 Section 4.9.3 gives for a powered bridge crane |
| Deflection and movement | 1.0 D | |

### 3.7 Serviceability

The tip of each pod carries the coupling that connects its CDU to the water-glycol store through a sleeve in the inner wall, so the vertical position of the tip matters. Two limits control it, and both are inputs. A deflection limit of 5 mm was set by the project for revision B. This report applies it twice, once to the truss and once to the shaft, and that reading is to be confirmed (open item 4).

| No. | Criterion | Limit | Checked in |
| ---: | --- | ---: | --- |
| 1 | Deflection of the pod truss at its tip under dead load | 5 mm | section 4.5 |
| 2 | Movement of a pod tip caused by the shaft: its shortening as the store is filled, plus its lean in the worst filling state | 5 mm | section 5.7 |

The first is a fixed amount that can be set out when a pod is built. The second develops after a pod has been docked, as other pods are added, and is what the coupling has to follow. The tolerance of the coupling is not yet known. The rotation of the root connection also moves the tip and belongs to check 6.

## 4. Check 2: pod truss

### 4.1 Description

Each pod is carried by two vertical trusses, one each side of the racks, 0.68 m apart centre to centre. They are joined top and bottom at every panel point by cross members and plan bracing, so the pair acts as a box. The trusses are 2.40 m deep overall and span 7.16 m as cantilevers from the hub on the shaft.

- **Chords.** Rectangular hollow sections with the long side vertical, no wider than 3 in (76 mm) so that they fit in the 80 mm beside the racks. An I-section was considered. No rolled W-shape has a flange narrower than about 100 mm, so an I-section chord would widen the pod, and a hollow section also gives a flat face to weld the web members to.
- **Web.** Square hollow sections. There is a vertical at every panel point and one diagonal in each panel. The diagonals fall towards the tip, so they are in tension when the pod is docked and the shorter verticals take the compression.
- **Panels.** One panel to each rack, 1.25 m long, so that each rack bears on panel points. The CDU and pump section has 2 panels of 1.08 m.
- **Joints.** Fully welded.
- **Support.** At the root the top chord is held by a clevis that takes the pull and the whole weight. The bottom chord bears on the hub and takes thrust only.

![Elevation of one side truss with member forces](figures/pod_truss.svg)

### 4.2 Design criteria

| No. | Criterion | Limit | Basis |
| ---: | --- | --- | --- |
| 1 | Tip deflection under dead load | 5 mm | section 3.7 |
| 2 | Member strength | required strength ≤ design strength | AISC 360-22 Chapters D and E |
| 3 | Member slenderness | L<sub>c</sub>/r ≤ 200 for every member | AISC 360-22 Section E2, user note. Applied to all members because the web forces reverse when the pod is hoisted. |
| 4 | Wall slenderness | (b − 3t)/t ≤ 1.40 √(E/F<sub>y</sub>) = 33.7 | AISC 360-22 Table B4.1a, case 6. No slender walls. |
| 5 | Joint geometry | web width between 0.25 and 1.0 of the chord width | AISC 360-22 Chapter K, limits of applicability |
| 6 | Chord width | ≤ 3 in | the frame envelope |

The lightest pair of sections from the lists in the design file that meets all six is chosen. The lists hold 11 chord sizes from HSS4×3×3/16 to HSS8×3×3/8 and 7 web sizes from HSS2×2×3/16 to HSS3×3×5/16, none with a wall thinner than 3/16 in.

### 4.3 Analysis

Each truss is analysed as a pin-jointed plane truss by the direct stiffness method, with half the pod's load applied at its panel points. Member lengths are taken between the centre lines of the chords, 2.248 m apart. The welded joints make the real truss slightly stiffer than the model, so the calculated deflection is an upper estimate for the truss alone.

Two support cases are analysed:

1. **Docked.** A cantilever from the root, as in Figure 1.
2. **Hoisted.** Hanging from the hoist's two pickups on the top chord, at panel points 1 and 4, which are 1.25 m and 5.00 m from the root. The pickups carry 47.2 kN and 40.4 kN for the whole pod, unfactored.

Compression members are checked for flexural buckling with an effective length equal to the distance between panel points.

### 4.4 Selected sections

| Member | Section | Size, mm | Steel |
| --- | --- | --- | --- |
| Top and bottom chords | **HSS6×3×3/16**, long side vertical | 152 deep × 76 wide × 4.8 wall | ASTM A500 Grade C |
| Verticals and diagonals | **HSS2×2×3/16** | 51 × 51 × 4.8 wall | ASTM A500 Grade C |
| Cross members and plan bracing | HSS2×2×3/16 | 51 × 51 × 4.8 wall | ASTM A500 Grade C |

### 4.5 Deflection

| Quantity | Value |
| --- | ---: |
| Tip deflection under dead load, stiffness analysis | **4.90 mm** |
| As a fraction of the span | span/1,463 |
| Limit | 5.00 mm |
| Tip deflection by statics and virtual work (section 4.7) | 4.90 mm |
| **Result** | **Satisfied**, 98% of the limit |

The 5 mm limit governs the chords. The lightest sections in the list, HSS4×3×3/16 chords with HSS2×2×3/16 web members, deflect 5.26 mm and do not pass. The verticals and diagonals contribute 3.3 mm of the deflection of the selected truss and the chords 1.6 mm, because the truss is 0.34 of its span deep.

### 4.6 Strength

Required strengths are the larger of the docked and hoisted cases with the factors in section 3.6. Design strengths are φ<sub>t</sub>F<sub>y</sub>A<sub>g</sub> in tension (Section D2, φ<sub>t</sub> = 0.90) and φ<sub>c</sub>F<sub>cr</sub>A<sub>g</sub> in compression (Section E3, φ<sub>c</sub> = 0.90). Tensile rupture does not govern for members welded all round, because 0.75 F<sub>u</sub> exceeds 0.90 F<sub>y</sub> for this steel.

| Member group | Section | Tension, kN | Design tension strength, kN | Compression, kN | Longest, m | L<sub>c</sub>/r | Design compression strength, kN | Highest ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Top chord | HSS6×3×3/16 | 50.9 | 588.7 | 4.4 | 1.25 | 40 | 525.1 | 0.09 |
| Bottom chord | HSS6×3×3/16 | 4.4 | 588.7 | 81.2 | 1.25 | 40 | 525.1 | 0.15 |
| Diagonal | HSS2×2×3/16 | 62.5 | 239.4 | 19.2 | 2.57 | 138 | 62.8 | 0.31 |
| Vertical | HSS2×2×3/16 | 26.9 | 239.4 | 41.9 | 2.25 | 121 | 82.3 | 0.51 |

The most heavily used member is the vertical at panel point 1, at 0.51. Strength does not govern. Forces in each member are in Appendix A.

### 4.7 Verification

The stiffness analysis is checked in three ways each time the report is generated. The checks are in [structure.py](../gpu_silo/structure.py) and the build fails if one does not hold.

| Check | Stiffness analysis | Independent value | Agreement |
| --- | ---: | ---: | --- |
| Tip deflection, by method of sections and virtual work | 4.895 mm | 4.895 mm | within 0.00% |
| Vertical reaction of one truss against half the pod weight | 43.79 kN | 43.79 kN | equal |
| Root couple of one truss against half the root moment | 130.4 kN·m | 130.4 kN·m | equal |

Section properties are calculated from the nominal size, the design wall thickness and an outside corner radius of twice the wall. For HSS6×3×1/4 this gives 3.83 in² and 13.92 lb/ft against 3.84 in² and 13.91 lb/ft in the AISC Manual. The properties of the selected sections are in Appendix B and should be compared with the Manual at the checking stage.

### 4.8 Weight of a pod

| Item | Mass, kg | Basis |
| --- | ---: | --- |
| Two trusses | 855 | HSS6×3×3/16 chords, HSS2×2×3/16 web |
| Cross members and plan bracing | 160 | 24.9 m of HSS2×2×3/16 |
| Connections | 101 | 10% of the steel |
| Housing | 415 | 10 kg/m² |
| **Frame and housing** | **1,531** | |
| Racks | 6,400 | allowance |
| CDU and pump | 600 | allowance |
| Coolant and piping | 400 | allowance |
| **One pod, operating** | **8,931** | 87.6 kN |

Steel is 11% of the weight of a pod. The racks are 72%, so the rack weight is the number that most needs confirming.

### 4.9 Sensitivity to the deflection limit

The table gives the lightest design in the list for other limits, with all the other criteria unchanged.

| Limit, mm | Chords | Web | Tip deflection, mm | As a fraction | Steel a pod, kg | Pod, t |
| ---: | --- | --- | ---: | --- | ---: | ---: |
| 10 | HSS4×3×3/16 | HSS2×2×3/16 | 5.3 | span/1,362 | 914 | 8.82 |
| 7.5 | HSS4×3×3/16 | HSS2×2×3/16 | 5.3 | span/1,362 | 914 | 8.82 |
| 5 | HSS6×3×3/16 | HSS2×2×3/16 | 4.9 | span/1,463 | 1,014 | 8.93 |
| 4 | HSS5×3×3/16 | HSS2-1/2×2-1/2×1/4 | 3.9 | span/1,821 | 1,224 | 9.16 |
| 3.5 | HSS6×3×1/4 | HSS2-1/2×2-1/2×1/4 | 3.4 | span/2,079 | 1,409 | 9.37 |
| 3 | HSS8×3×1/4 | HSS3×3×1/4 | 2.9 | span/2,440 | 1,695 | 9.68 |

### 4.10 Conclusion

HSS6×3×3/16 chords with HSS2×2×3/16 verticals and diagonals carry the pod with a tip deflection of 4.9 mm against the limit of 5 mm, and a highest strength ratio of 0.51. The deflection limit governs. A pod weighs 8.93 t in operation.

The result holds for gravity load only. The items in section 4.11 could change the section sizes, the lateral case most of all, and the design should not be treated as final until they are closed.

### 4.11 Not covered by this check

1. **Lateral load.** The pair of trusses is only 0.68 m wide and cantilevers 7.16 m sideways as well as downwards. Earthquake load and the starting and stopping of a level act sideways on it. The site and its seismic design category are not yet fixed. This case is likely to govern the chords and the plan bracing.
2. **Welded joints.** The connections between hollow sections are to be designed to AISC 360-22 Chapter K. Only the width ratio is checked here.
3. **Root connection.** The clevis, the bearing and their effect on the tip deflection are part of check 6.
4. **Local loads.** The racks are assumed to bear at panel points through the cross members. Rack feet that land between panel points would bend the bottom chord.
5. **Transport.** The pods travel upright, two side by side on a flatbed. Road loads and tie-down points are not checked.
6. **Fatigue.** The number of lifts and rotations in the life of a pod is small, so fatigue is not expected to govern. This is to be confirmed with the service plan.
7. **Temperature.** The bore is expected to sit near the temperature of the store. Differential movement between the pod and the wall sleeve is not checked.

## 5. Check 1: central shaft

### 5.1 Arrangement

These points were confirmed for revision B.

- The shaft is fixed to the foundation at its base and does not turn. Each level has a hub that turns on the shaft, and the eight pods of a level hang from the hub.
- The base is a heavy fixed connection to the foundation. It is designed with the foundation under check 4, for the reactions in section 5.8.
- The top of the shaft is held sideways by a connector to the support rig that carries the diesel generator level. The rig passes the force to mounts cast into the inner wall. The connector takes sideways force only, so the shaft is free to shorten under load and the weight of the rig does not come onto the shaft.
- The store is filled from the top level down. A pod is lifted up a lane at the ground entry by the hoist under the crown. While it is lifted, every level that is already full closes up from 45° to 40° between pods to open the lane.

The shaft is a round tube of 1160 mm outside diameter, rolled from plate, 23.79 m from the top of the foundation to the connector. Its wall thickness is the result of this check.

### 5.2 Dead load from the pods

| Quantity | Value | Basis |
| --- | ---: | --- |
| Weight of one pod, W | 87.6 kN (8.93 t) | section 4.8 |
| Centre of gravity from the root | 2.98 m | |
| Centre of gravity from the shaft axis | 4.18 m | root radius 1.20 m |
| Moment of one pod at its root | 261 kN·m | |
| Moment of one pod about the shaft axis, M<sub>pod</sub> | **366 kN·m** | |
| Weight of one level, 8 pods | 701 kN (71.4 t) | |
| Weight of 64 pods | **5,605 kN (572 t)** | |
| Hub, bearing and access floor | 29 kN a level | allowance |
| Shaft and the services inside it | 276 kN | 883 kg/m of steel and 300 kg/m of services |

All values are unfactored.

### 5.3 Out-of-balance moment

A complete level stored at 45° is balanced and puts no moment on the shaft. Moment arises while the store is being filled, and again whenever a pod is exchanged in service, because the levels above the working level bunch to open the lane.

| State | Moment on the shaft | In terms of M<sub>pod</sub> |
| --- | ---: | ---: |
| One complete level, stored at 45° | 0 | 0 |
| One complete level, bunched at 40° | 366 kN·m | 1.00 |
| One level part filled, worst number of pods | 956 kN·m | 2.61 |
| **Worst state in the filling sequence, total** | **3,247 kN·m** | **8.87** |
| Every level half filled on the same side, total | 7,651 kN·m | 20.9 |

The worst state in the sequence has 7 levels full and bunched and 5 pods on the level being filled. The moments of the bunched levels all point away from the lifting lane, so they add up the height of the shaft. Figure 2 shows this state. An exchange of a pod on the lowest level in service produces nearly the same state.

The last row is not part of the planned sequence. It is the moment that would arise if the fill order were not controlled.

![Plan of the worst out-of-balance state](figures/shaft_unbalance.svg)

### 5.4 Design criteria

| No. | Criterion | Limit | Basis |
| ---: | --- | --- | --- |
| 1 | Movement of a pod tip caused by the shaft | 5 mm | section 3.7. Shortening under the full store plus lean in the worst state of the filling sequence. |
| 2 | Strength under axial load and bending | interaction ≤ 1.0 in all three loading states | AISC 360-22 Sections E3, F8 and H1 |
| 3 | Wall slenderness | D/t ≤ 0.11 E/F<sub>y</sub> = 63.8 | AISC 360-22 Table B4.1a, case 9. No slender wall in compression. |
| 4 | Member slenderness | L<sub>c</sub>/r ≤ 200 | AISC 360-22 Section E2, user note |

Strength is checked for the uncontrolled fill as well as for the planned sequence. This is a decision made in this report so that a mistake in the fill order cannot overload the shaft. It costs nothing, because criterion 1 governs. The movement limit is checked for the planned sequence only.

The thinnest plate in the list in the design file that meets all four is chosen.

### 5.5 Analysis

The shaft is analysed as a beam, fixed at the foundation and held in position at the connector, 23.79 m above. The out-of-balance moment of each level is applied as a couple at the height of its hub. Couples are resolved onto the direction of their resultant. The weights of the pods, hubs, shaft and services give the axial force.

- **Shortening.** The drop of a hub is the shortening of the shaft below it under the weight of all 64 pods. The self-weight of the shaft and the hubs is left out, because it is in place before the hubs are set to level.
- **Lean.** The slope of the shaft at a hub tilts the pods of that level. The tip of a pod moves by the slope times the tip radius of 8.36 m. The largest slope at any hub is used.
- **Second-order effects.** Moments are multiplied by B<sub>1</sub> = 1/(1 − P<sub>u</sub>/P<sub>e1</sub>), with P<sub>e1</sub> = π²EI/L² and C<sub>m</sub> = 1.0, as AISC 360-22 Appendix 8 allows for a member held against sidesway.
- **Effective length.** K = 0.8, the value recommended for a column fixed at one end and held in position at the other.

![Elevation of the shaft with its loads and bending moment](figures/shaft.svg)

### 5.6 Selection of the wall thickness

| Wall, in (mm) | D/t | Mass, kg/m | Shortening, mm | Tip movement from lean, mm | Total, mm | Strength ratio | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 3/4 (19.0) | 60.9 | 536 | 4.55 | 3.16 | 7.72 | 0.58 | Tip movement too large |
| 7/8 (22.2) | 52.2 | 624 | 3.91 | 2.74 | 6.65 | 0.49 | Tip movement too large |
| 1 (25.4) | 45.7 | 711 | 3.43 | 2.41 | 5.85 | 0.43 | Tip movement too large |
| 1-1/8 (28.6) | 40.6 | 797 | 3.06 | 2.16 | 5.22 | 0.38 | Tip movement too large |
| **1-1/4 (31.8)** | 36.5 | 883 | 2.76 | 1.96 | **4.73** | 0.34 | Selected |
| 1-3/8 (34.9) | 33.2 | 969 | 2.52 | 1.80 | 4.32 | 0.31 | Passes |
| 1-1/2 (38.1) | 30.4 | 1,054 | 2.32 | 1.66 | 3.98 | 0.29 | Passes |
| 1-3/4 (44.4) | 26.1 | 1,223 | 2.00 | 1.45 | 3.45 | 0.25 | Passes |
| 2 (50.8) | 22.8 | 1,390 | 1.76 | 1.29 | 3.05 | 0.14 | Passes |

**Selected: 1160 mm outside diameter × 1-1/4 in (31.8 mm) wall.** The movement limit governs. Strength would be met by the thinnest plate in the list.

| Property of the selected tube | Value |
| --- | ---: |
| Area | 112,538 mm² |
| Second moment of area | 17.9 × 10⁹ mm⁴ |
| Flexural stiffness, EI | 3.58 GN·m² |
| Radius of gyration | 399 mm |
| Mass | 883 kg/m, 21.0 t in all |
| D/t | 36.5, compact in flexure (limit 0.07 E/F<sub>y</sub> = 40.6) |

### 5.7 Movement of the pod tips

| Quantity | Value |
| --- | ---: |
| Shortening at the top hub under the full store | 2.76 mm |
| Largest slope of the shaft at a hub, worst state of the filling sequence | 0.235 mrad |
| Tip movement from that slope | 1.96 mm |
| **Total** | **4.73 mm** |
| Limit | 5.00 mm |
| **Result** | **Satisfied**, 95% of the limit |

The two parts are added although they do not peak in exactly the same state, which is on the safe side. The shortening builds up from the bottom of the shaft, so it is largest at the top level, which is also the first to be filled:

| Level | Hub height, m | Drop of the hub under the full store, mm |
| ---: | ---: | ---: |
| 1 | 1.40 | 0.35 |
| 2 | 4.17 | 0.95 |
| 3 | 6.94 | 1.47 |
| 4 | 9.71 | 1.90 |
| 5 | 12.48 | 2.25 |
| 6 | 15.25 | 2.50 |
| 7 | 18.02 | 2.68 |
| 8 | 20.79 | 2.76 |

### 5.8 Strength

| Loading state | Pods | Axial at the base, kN | P<sub>u</sub>, kN | Largest moment, kN·m | B<sub>1</sub> | M<sub>u</sub>, kN·m | P<sub>u</sub>/φP<sub>n</sub> | M<sub>u</sub>/φM<sub>n</sub> | Interaction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Store complete, every level at the storage pitch | 64 | 6,117 | 8,564 | 0 | 1.16 | 0 | 0.29 | 0.00 | **0.29** |
| Worst state of the filling sequence: 7 levels full and bunched, 5 pods on the next | 61 | 5,854 | 8,196 | 574 | 1.15 | 925 | 0.28 | 0.07 | **0.34** |
| Uncontrolled fill: 4 pods on the same side of every level | 32 | 3,314 | 4,640 | 931 | 1.08 | 1,407 | 0.16 | 0.11 | **0.19** |

| Design strength of the selected tube | Value | Basis |
| --- | ---: | --- |
| Compression, φ<sub>c</sub>P<sub>n</sub> | 29,587 kN | Section E3, L<sub>c</sub>/r = 48, F<sub>cr</sub> = 292 MPa |
| Flexure, φ<sub>b</sub>M<sub>n</sub> | 12,553 kN·m | Section F8, plastic moment |
| Shear, φ<sub>v</sub>V<sub>n</sub> | 10,483 kN | Section G5, yielding |

Axial force and the largest moment are combined although they occur at different heights. The interaction is by Section H1.1. The largest shear is 435 kN, which is 4% of the design shear strength.

Reactions for the checks that follow:

| Loading state | Vertical at the base, kN | Moment at the base, kN·m | Sideways force at the top and at the base, kN | Factored vertical, kN | Factored base moment, kN·m | Factored sideways force, kN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Store complete, every level at the storage pitch | 6,117 | 0 | 0 | 8,564 | 0 | 0 |
| Worst state of the filling sequence: 7 levels full and bunched, 5 pods on the next | 5,854 | 408 | 119 | 8,196 | 657 | 167 |
| Uncontrolled fill: 4 pods on the same side of every level | 3,314 | 260 | 311 | 4,640 | 392 | 435 |

The sideways force at the base is equal and opposite to the force at the top. The base moment with the top held is 13% of what it would be with the top free in the worst state of the sequence, 3,247 kN·m. The base is still to be a heavy fixed connection: section 5.10 gives the case in which it has to work alone.

### 5.9 Stiffness of the top restraint

The results above assume that the top of the shaft does not move sideways. The support rig, its connector and the wall mounts will have some give. The table shows the effect in the worst state of the filling sequence.

| Stiffness of the restraint, kN/mm | Force at the top, kN | Sideways movement of the top, mm | Tip movement from lean, mm | Total with shortening, mm | Within 5 mm |
| ---: | ---: | ---: | ---: | ---: | --- |
| 25 | 116 | 4.6 | 2.76 | 5.53 | No |
| 50 | 117 | 2.3 | 2.12 | 4.89 | Yes |
| 100 | 118 | 1.2 | 1.84 | 4.61 | Yes |
| 250 | 119 | 0.5 | 1.72 | 4.49 | Yes |
| 1,000 | 119 | 0.1 | 1.90 | 4.66 | Yes |
| Rigid | 119 | 0.0 | 1.96 | 4.73 | Yes |

**The restraint needs a stiffness of at least 42 kN/mm** at the top of the shaft for the movement limit to be met with the selected wall. This is a design requirement for checks 7, 8 and 9. A moderately soft restraint gives slightly less lean than a rigid one, because the slope of the shaft changes sign up its height and the two ends balance better.

### 5.10 The shaft before the support rig is in place

In the present programme the pods are loaded on days 6 to 15 and the power levels, with the support rig, are lifted in on days 19 to 21. The worst out-of-balance state occurs during pod loading, so in the present programme it would occur with the top of the shaft free.

| Selected tube, top free, worst state of the filling sequence | Value |
| --- | ---: |
| Moment at the base | 3,247 kN·m |
| Sideways movement of the top of the shaft | 149 mm |
| Tip movement from lean | **76 mm** |
| Strength interaction, planned sequence | 0.65 |
| Strength interaction, uncontrolled fill | 1.00 |

The shaft would not collapse, but the pods would be 76 mm out of level at their tips and the top of the shaft would be 149 mm off the axis. An uncontrolled fill would use all of the strength of the tube.

**Requirement: the top of the shaft is to be held before the first pod is hung.** Either the steel of the support rig is set on its wall mounts and connected to the shaft straight after the cage is lifted in, and the generator sets are landed on it later, or the shaft is braced to the wall by temporary works until the rig arrives. The programme and the animation do not yet show either. This is open item 1.

### 5.11 Verification

| Check | Analysis | Independent value | Agreement |
| --- | ---: | ---: | --- |
| Top reaction for a single couple M at height a, against 3Ma(2L − a)/(2L³) | numerical integration | closed form | within 0.1%, checked at every build |
| Base moment against the sum of the couples less the top reaction times L, each loading state | 407.6 kN·m | 407.6 kN·m | equal |
| Sideways movement of the held top | 0.000 µm | 0 | equal |

### 5.12 Conclusion

A 1160 mm tube with a 1-1/4 in (31.8 mm) wall of A572 Grade 50 plate, fixed at its base and held at its top, carries the 64 pods with a highest strength interaction of 0.34. The pod tips move 4.7 mm against the limit of 5 mm, and this governs the wall. The shaft weighs 21.0 t.

The result depends on the top restraint. It needs a stiffness of at least 42 kN/mm, and it has to be in place before the first pod is hung.

### 5.13 Not covered by this check

1. **Lateral load.** Earthquake load on 572 t of pods is likely to govern the shaft, its base, the connector, the rig and the mounts. It waits for the site.
2. **Local loads at the hubs.** Each hub puts 730 kN of weight and the pull and thrust of eight pod roots into the wall of the tube. Ring stiffeners or thicker cans at the hubs are to be designed with the hub under check 6.
3. **Openings.** Power and data pass down the inside of the shaft and have to come out at every level. The openings reduce the section and are not yet sized.
4. **Base connection.** Anchor rods, base plate and the foundation under them are part of check 4.
5. **Plumb.** A shaft that is out of plumb tilts every pod. One part in a thousand moves a pod tip 8.4 mm. The hubs will have to be set level independently of the shaft, or the erection tolerance set to suit.
6. **Torsion.** The drive of a level reacts on the shaft. The torque is small (section 6.2) and is not checked.
7. **Temperature.** The steel shaft and the concrete wall may warm by different amounts. The effect on the tip couplings is not checked.
8. **Field splices** and the welding of the seams.

## 6. Check 6: root connection and level drive, design loads

The connection and the drive are not designed in this revision. These are the loads from the pods as now designed, unfactored. The shaft is fixed and each level turns on it.

### 6.1 At the root of one pod

| Load | One truss | One pod |
| --- | ---: | ---: |
| Pull on the upper clevis | 58.0 kN | 116.1 kN |
| Thrust on the lower bearing | 58.0 kN | 116.1 kN |
| Weight on the upper clevis | 43.8 kN | 87.6 kN |
| Lever arm between clevis and bearing | 2.248 m | |

The tip drops 3.2 mm for each millimetre of horizontal slack or stretch between the clevis and the bearing. The stiffness and fit of the root connection will therefore matter more to the position of the tip than the truss does.

### 6.2 For the drive of one level

| Quantity | Value | Basis |
| --- | ---: | --- |
| Rotating weight of a full level | 701 kN | pods only |
| Mass moment of inertia of one pod about the shaft axis | 188,296 kg·m² | |
| Mass moment of inertia of a full level | **1,506,367 kg·m²** | pods only |
| Out-of-balance moment on the hub bearing, level part filled | 956 kN·m | section 5.3 |
| Out-of-balance moment on the hub bearing, level bunched | 366 kN·m | section 5.3 |
| Torque to accelerate a full level, turning one bay in 60 s | 1.3 kN·m | accelerating for half the turn and braking for half |

The inertia torque is small. The drive will be sized by the friction of the hub bearing under the weight and the out-of-balance moment, and by holding a level against the lean of the shaft. Both depend on the bearing chosen under check 6.

## 7. Checks 7, 8 and 9: support rig, shaft connector and wall mounts, design loads

These three checks were added in revision B. Holding the top of the shaft makes the rig, its connector and its mounts part of the structure that carries the pods. They are not designed in this revision. This section describes them as modelled and gives their loads.

### 7.1 Description

- **Support rig (check 7).** The steel deck under the diesel generator level: girders under the sets and a ring beam inside the wall, 0.6 m deep, at 23.49 m to 24.09 m above the foundation.
- **Shaft connector (check 8).** A collar round the top of the shaft with 4 arms out to the ring beam, in the depth of the rig. The shaft runs up into the collar and can slide in it, so the connector passes sideways force and nothing else.
- **Wall mounts (check 9).** 16 steel plates, 0.6 m × 0.95 m, cast flush into the bore face of the inner wall with studs into the concrete, evenly spaced round the ring beam and clear of the access wedge. They are set in the forms of the wall lift that contains them. They have to be flush for the cage to pass, so the rig carries a shoe at each mount that is welded to the plate once the rig is down.

### 7.2 Loads from the shaft

| Loading state | Sideways force at the top of the shaft, kN | Factored, kN | Largest force on one mount, kN |
| --- | ---: | ---: | ---: |
| Store complete, every level at the storage pitch | 0 | 0 | 0 |
| Worst state of the filling sequence: 7 levels full and bunched, 5 pods on the next | 119 | 167 | 15 |
| Uncontrolled fill: 4 pods on the same side of every level | 311 | 435 | 39 |

The direction of the force changes as the levels turn during a lift, so every mount is taken to see the largest share. The force on one mount assumes that the ring beam spreads the force round all 16 mounts as a cosine distribution, which gives 2/n of the total on the most heavily loaded mount. There are no mounts in the access wedge, so the true share is somewhat higher and is to be worked out under check 9.

The inner wall carries these forces in addition to the pressure of the store behind it. That is to be included in check 3.

### 7.3 Gravity loads on the rig

| Item | Mass, t | Basis |
| --- | ---: | --- |
| Diesel generator sets | 94.0 | 4 × 23.5 t |
| Day tanks, full | 4.6 | fuel only |
| Deck steel | 38 | allowance |
| **Diesel generator level** | **137** | 84 kN on each mount if shared equally |
| Turbine level | 227 | 2 × 94.5 t and 38 t of deck steel |
| Both levels | 364 | 223 kN on each mount if the turbine level also bears on the rig |

The weight of the rig and its machines does not come onto the shaft.

### 7.4 Requirements from check 1

1. Sideways stiffness at the top of the shaft of at least 42 kN/mm, through the connector, the rig and the mounts together.
2. The restraint in place before the first pod is hung (section 5.10).
3. No vertical load from the rig onto the shaft, and freedom for the shaft to shorten by 3 mm or more inside the collar.

## 8. Open items

| No. | Item | Affects | Needed from |
| ---: | --- | --- | --- |
| 1 | The top of the shaft must be held before the pods are loaded: set the rig steel early, or brace the shaft temporarily | checks 1, 7, 8 and 9, the programme and the animation | project |
| 2 | Site and seismic design category, for the lateral case | all structural checks | project |
| 3 | Weight of a rack in operation, and of the CDU, pump and coolant | checks 1, 2, 4 and 6 | equipment supplier |
| 4 | Whether the 5 mm limit is meant for the truss and the shaft separately, as applied here, or for the two together. The tolerance of the wall coupling decides it. | checks 1, 2 and 6 | project and coupling supplier |
| 5 | Does the turbine level bear on the support rig or on mounts of its own? | checks 3, 7 and 9 | project |
| 6 | Weight of the hub, bearing and access floor at each level | checks 1 and 6 | check 6 |
| 7 | Comparison of section properties with the AISC Manual | check 2 | checker |

## Appendix A: member forces in the pod truss

One side truss. Forces are unfactored in the docked and hoisted columns, tension positive. Factored values use the combinations in section 3.6. Panels are numbered from 1 at the root. For a vertical the number is its panel point, from 0 at the root.

| Member | Panel | Length, m | Docked, kN | Hoisted, kN | Factored tension, kN | Factored compression, kN | KL/r | Ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Top chord | 1 | 1.250 | +36.4 | +2.7 | 50.9 | 0.0 | 40 | 0.09 |
| Top chord | 2 | 1.250 | +19.9 | -2.5 | 27.9 | 4.4 | 40 | 0.05 |
| Top chord | 3 | 1.250 | +8.8 | -2.5 | 12.3 | 4.3 | 40 | 0.02 |
| Top chord | 4 | 1.250 | +2.9 | +2.9 | 5.0 | 0.0 | 40 | 0.01 |
| Top chord | 5 | 1.080 | +0.7 | +0.7 | 1.3 | 0.0 | 34 | 0.00 |
| Top chord | 6 | 1.080 | -0.0 | -0.0 | 0.0 | 0.0 | 34 | 0.00 |
| Bottom chord | 1 | 1.250 | -58.0 | +0.0 | 0.0 | 81.2 | 40 | 0.15 |
| Bottom chord | 2 | 1.250 | -36.4 | -2.7 | 0.0 | 50.9 | 40 | 0.10 |
| Bottom chord | 3 | 1.250 | -19.9 | +2.5 | 4.4 | 27.9 | 40 | 0.05 |
| Bottom chord | 4 | 1.250 | -8.8 | +2.5 | 4.3 | 12.3 | 40 | 0.02 |
| Bottom chord | 5 | 1.080 | -2.9 | -2.9 | 0.0 | 5.0 | 34 | 0.01 |
| Bottom chord | 6 | 1.080 | -0.7 | -0.7 | 0.0 | 1.3 | 34 | 0.00 |
| Diagonal | 1 | 2.572 | +44.6 | -5.5 | 62.5 | 9.6 | 138 | 0.26 |
| Diagonal | 2 | 2.572 | +33.8 | +10.7 | 47.3 | 0.0 | 138 | 0.20 |
| Diagonal | 3 | 2.572 | +23.0 | -0.1 | 32.2 | 0.2 | 138 | 0.13 |
| Diagonal | 4 | 2.572 | +12.1 | -11.0 | 17.0 | 19.2 | 138 | 0.31 |
| Diagonal | 5 | 2.494 | +4.9 | +4.9 | 8.6 | 0.0 | 134 | 0.04 |
| Diagonal | 6 | 2.494 | +1.7 | +1.7 | 3.0 | 0.0 | 134 | 0.01 |
| Vertical | 0 | 2.248 | +4.5 | +4.5 | 7.9 | 0.0 | 121 | 0.03 |
| Vertical | 1 | 2.248 | -29.9 | +13.9 | 24.3 | 41.9 | 121 | 0.51 |
| Vertical | 2 | 2.248 | -20.5 | -0.3 | 0.0 | 28.6 | 121 | 0.35 |
| Vertical | 3 | 2.248 | -11.0 | +9.2 | 16.1 | 15.4 | 121 | 0.19 |
| Vertical | 4 | 2.248 | -4.8 | +15.4 | 26.9 | 6.7 | 121 | 0.11 |
| Vertical | 5 | 2.248 | -1.9 | -1.9 | 0.0 | 3.3 | 121 | 0.04 |
| Vertical | 6 | 2.248 | -0.2 | -0.2 | 0.0 | 0.3 | 121 | 0.00 |

## Appendix B: section properties

Hollow sections, calculated as described in section 4.7.

| Section | Depth × width, mm | Nominal wall, mm | Design wall, mm | Area, mm² (in²) | r<sub>x</sub>, mm | r<sub>y</sub>, mm | Mass, kg/m (lb/ft) | Wall slenderness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HSS6×3×3/16 | 152 × 76 | 4.76 | 4.43 | 1,896 (2.94) | 54.3 | 31.6 | 15.9 (10.70) | 31.4 |
| HSS2×2×3/16 | 51 × 51 | 4.76 | 4.43 | 771 (1.20) | 18.6 | 18.6 | 6.4 (4.32) | 8.5 |
