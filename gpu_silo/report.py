"""Writes the structural design report and its figures from design/project.json.

The report is generated so that every number in it comes from the design file and the checks
in structure.py. Edit the inputs or this module, then run `python -m gpu_silo calcs`.
"""
import math
from pathlib import Path

from . import calcs
from . import design as cfg
from . import structure as st

FOLDER = Path(__file__).resolve().parents[1] / "design"
FILE = FOLDER / "report.md"
FIGURES = FOLDER / "figures"
INK, MUTED, TENSION, COMPRESSION, PAPER = "#22303a", "#6b7780", "#1f6fa8", "#b4532a", "#ffffff"
KIP = 4448.2216


def kn(value, digits=1):
    return f"{value/1000:,.{digits}f}"


def svg(width, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'font-family="Helvetica, Arial, sans-serif" font-size="12">\n<rect width="{width}" height="{height}" fill="{PAPER}"/>\n'
            + "\n".join(body) + "\n</svg>\n")


def truss_figure():
    """Elevation of one side truss with the docked member forces."""
    d = st.C["design"]
    model = d["model"]
    scale, left, base = 96., 150., 344.
    def at(node):
        x, z = model["nodes"][node]
        return left + x * scale, base - z * scale
    out = [f'<text x="20" y="26" font-size="15" fill="{INK}" font-weight="bold">Figure 1. One side truss of a {cfg.NAME} pod, docked</text>',
           f'<text x="20" y="45" fill="{MUTED}">Unfactored dead load on one truss. Member forces in kN: tension blue, compression orange. Two trusses carry each pod.</text>']
    for row in d["rows"]:
        (x0, y0), (x1, y1) = at(row["a"]), at(row["b"])
        force = row["docked"]
        colour = TENSION if force > 50 else COMPRESSION if force < -50 else MUTED
        width = 5 if row["kind"].endswith("chord") else 3
        out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{colour}" stroke-width="{width}" stroke-linecap="round"/>')
    for row in d["rows"]:
        (x0, y0), (x1, y1) = at(row["a"]), at(row["b"])
        force = row["docked"] / 1000
        if abs(force) < .05: continue
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        colour = TENSION if force > 0 else COMPRESSION
        if row["kind"] == "Top chord": my -= 9
        elif row["kind"] == "Bottom chord": my += 19
        elif row["kind"] == "Vertical": mx += 6; my += 34
        else: mx += 8; my -= 4
        anchor = "middle" if row["kind"].endswith("chord") else "start"
        out.append(f'<text x="{mx:.1f}" y="{my:.1f}" fill="{colour}" text-anchor="{anchor}" font-size="11.5">{force:+.1f}</text>')
    n = model["n"]
    for i in range(2 * n):
        x, y = at(i)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{PAPER}" stroke="{INK}" stroke-width="1.4"/>')
    # Supports on the hub.
    x, y = at(n)
    out.append(f'<path d="M{x-4:.1f},{y:.1f} l-16,-10 v20 z" fill="{INK}"/><text x="{x-26:.1f}" y="{y-16:.1f}" fill="{INK}" text-anchor="end">Upper clevis</text>')
    out.append(f'<text x="{x-26:.1f}" y="{y-2:.1f}" fill="{MUTED}" text-anchor="end">pull {kn(d["root_pull"])} kN</text>')
    out.append(f'<text x="{x-26:.1f}" y="{y+12:.1f}" fill="{MUTED}" text-anchor="end">weight {kn(d["root_shear"])} kN</text>')
    x, y = at(0)
    out.append(f'<path d="M{x-4:.1f},{y:.1f} l-16,-10 v20 z" fill="{PAPER}" stroke="{INK}" stroke-width="1.4"/><circle cx="{x-24:.1f}" cy="{y-6:.1f}" r="3" fill="{INK}"/><circle cx="{x-24:.1f}" cy="{y+6:.1f}" r="3" fill="{INK}"/>')
    out.append(f'<text x="{x-34:.1f}" y="{y-2:.1f}" fill="{INK}" text-anchor="end">Lower bearing</text>')
    out.append(f'<text x="{x-34:.1f}" y="{y+12:.1f}" fill="{MUTED}" text-anchor="end">thrust {kn(d["root_thrust"])} kN</text>')
    out.append(f'<line x1="{left-112}" y1="{base-model["depth"]*scale-52}" x2="{left-112}" y2="{base+30}" stroke="{INK}" stroke-width="2"/>')
    out.append(f'<text x="8" y="{base+46}" fill="{MUTED}" text-anchor="start">hub on the shaft</text>')
    # Loads on the bottom chord and dimensions.
    for i in range(n):
        x, y = at(i)
        load = (d["load"][i] + d["load"][n + i]) / 1000
        out.append(f'<line x1="{x:.1f}" y1="{y+30:.1f}" x2="{x:.1f}" y2="{y+52:.1f}" stroke="{INK}" stroke-width="1.3"/><path d="M{x-4:.1f},{y+47:.1f} L{x:.1f},{y+56:.1f} L{x+4:.1f},{y+47:.1f} z" fill="{INK}"/>')
        out.append(f'<text x="{x:.1f}" y="{y+70:.1f}" fill="{INK}" text-anchor="middle">{load:.1f}</text>')
    out.append(f'<text x="{left-14:.1f}" y="{base+70:.1f}" fill="{MUTED}" text-anchor="end">Load at panel point, kN</text>')
    y = base + 96
    xs = model["xs"]
    for a, b in zip(xs, xs[1:]):
        xa, xb = left + a * scale, left + b * scale
        out.append(f'<line x1="{xa:.1f}" y1="{y}" x2="{xb:.1f}" y2="{y}" stroke="{MUTED}"/><line x1="{xa:.1f}" y1="{y-5}" x2="{xa:.1f}" y2="{y+5}" stroke="{MUTED}"/><line x1="{xb:.1f}" y1="{y-5}" x2="{xb:.1f}" y2="{y+5}" stroke="{MUTED}"/>')
        out.append(f'<text x="{(xa+xb)/2:.1f}" y="{y+16}" fill="{MUTED}" text-anchor="middle">{b-a:.2f}</text>')
    xr = left + cfg.BODY_LENGTH * scale
    out.append(f'<text x="{(left+xr)/2:.1f}" y="{y+36}" fill="{INK}" text-anchor="middle">{cfg.BODY_LENGTH:g} m rack housing, {st.RACKS} racks</text>')
    out.append(f'<text x="{(xr+left+xs[-1]*scale)/2:.1f}" y="{y+36}" fill="{INK}" text-anchor="middle">{cfg.SECTION:.2f} m CDU and pump</text>')
    xe = left + xs[-1] * scale
    top = base - model["depth"] * scale
    out.append(f'<line x1="{xe+44:.1f}" y1="{top:.1f}" x2="{xe+44:.1f}" y2="{base:.1f}" stroke="{MUTED}"/><text x="{xe+50:.1f}" y="{(top+base)/2-14:.1f}" fill="{MUTED}">{model["depth"]:.3f} m between</text><text x="{xe+50:.1f}" y="{(top+base)/2+2:.1f}" fill="{MUTED}">chord centres</text>')
    out.append(f'<text x="{xe+14:.1f}" y="{base+22:.1f}" fill="{INK}">tip deflection {d["tip"]*1000:.1f} mm</text>')
    out.append(f'<text x="{left+60:.1f}" y="{top-30:.1f}" fill="{INK}">Chords {d["chord"]["name"]}, long side vertical. Verticals and diagonals {d["web"]["name"]}.</text>')
    return svg(1010, 494, out)


def balance_figure():
    """Plan of the worst loading state, with the out-of-balance moment each level puts on the shaft."""
    c = st.C
    u = c["unbalance"]
    packed = math.radians(cfg.STORE["packed_pitch_degrees"])
    uniform = 2 * math.pi / cfg.BAYS
    out = [f'<text x="20" y="26" font-size="15" fill="{INK}" font-weight="bold">Figure 2. Worst out-of-balance state while the store is filled from the top down</text>',
           f'<text x="20" y="45" fill="{MUTED}">Plan views. The lifting lane is at the ground entry, drawn to the right. Arrows show the out-of-balance moment on the shaft as the direction of the heavy side.</text>']
    scale = 15.
    def plan(cx, cy, angles, title, note, resultant):
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{cfg.BORE_R*scale:.1f}" fill="none" stroke="{MUTED}" stroke-width="1.2"/>')
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{st.SHAFT_R*scale:.1f}" fill="{INK}"/>')
        out.append(f'<path d="M{cx+cfg.BORE_R*scale+4:.1f},{cy-9} v18" stroke="{INK}" stroke-width="3"/>')
        half = cfg.FRAME_WIDTH / 2 * scale
        for a in angles:
            deg = -math.degrees(a)
            out.append(f'<rect x="{cx+st.ROOT*scale:.1f}" y="{cy-half:.1f}" width="{st.SPAN*scale:.1f}" height="{2*half:.1f}" fill="#c9b27c" stroke="{INK}" stroke-width=".8" transform="rotate({deg:.2f} {cx} {cy})"/>')
        if abs(resultant) > 1:
            size = abs(resultant) / c["moment_axis"]
            ux, uy = resultant.real / abs(resultant), -resultant.imag / abs(resultant)
            length = 28 + 16 * size
            x1, y1 = cx + ux * length, cy + uy * length
            out.append(f'<line x1="{cx}" y1="{cy}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{COMPRESSION}" stroke-width="3.2"/>')
            out.append(f'<path d="M{x1+ux*9:.1f},{y1+uy*9:.1f} L{x1-uy*5:.1f},{y1+ux*5:.1f} L{x1+uy*5:.1f},{y1-ux*5:.1f} z" fill="{COMPRESSION}"/>')
        out.append(f'<text x="{cx}" y="{cy+cfg.BORE_R*scale+24:.1f}" fill="{INK}" text-anchor="middle" font-weight="bold">{title}</text>')
        out.append(f'<text x="{cx}" y="{cy+cfg.BORE_R*scale+41:.1f}" fill="{MUTED}" text-anchor="middle">{note}</text>')
    full = [math.pi + (j - (cfg.BAYS - 1) / 2) * packed for j in range(cfg.BAYS)]
    part = [-uniform * (k + 1) for k in range(u["placed"])]
    plan(190, 215, full, f"Each of the {u['full']} full levels, bunched at {cfg.STORE['packed_pitch_degrees']:g}°",
         f"{kn(u['bunched'],0)} kN·m each, away from the lane", complex(-u["bunched"], 0))
    plan(520, 215, part, f"Level being filled, {u['placed']} pods placed",
         f"{kn(u['partial'],0)} kN·m", u["parts"][-1] if u["placed"] else 0j)
    plan(850, 215, [], "Resultant at the base of the shaft", f"{kn(u['base'],0)} kN·m, unfactored", u["vector"] / 3.2)
    return svg(1040, 410, out)


def members_table(d):
    lines = ["| Member | Panel | Length, m | Docked, kN | Hoisted, kN | Factored tension, kN | Factored compression, kN | KL/r | Ratio |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for kind in ("Top chord", "Bottom chord", "Diagonal", "Vertical"):
        for row in d["rows"]:
            if row["kind"] != kind: continue
            lines.append(f"| {kind} | {row['panel']} | {row['length']:.3f} | {row['docked']/1000:+.1f} | {row['hoisted']/1000:+.1f} | "
                         f"{kn(row['tension'])} | {kn(row['compression'])} | {row['slenderness']:.0f} | {row['ratio']:.2f} |")
    return "\n".join(lines)


def section_row(s):
    inch = st.INCH
    return (f"| {s['name']} | {s['h']*1000:.0f} × {s['b']*1000:.0f} | {s['t_nominal']*1000:.2f} | {s['t']*1000:.2f} | {s['area']*1e6:,.0f} ({s['area']/inch**2:.2f}) | "
            f"{s['rx']*1000:.1f} | {s['ry']*1000:.1f} | {s['kg_m']:.1f} ({s['kg_m']/1.48816:.2f}) | {s['wall']:.1f} |")


def markdown():
    c, k = st.C, calcs.C
    d = c["design"]
    doc = cfg.PROJECT["design_checks"]
    T, steel, pod = st.T, st.STEEL, cfg.POD
    u, sh = c["unbalance"], c["shaft"]
    groups = d["groups"]
    mass = d["mass"]
    limit_ratio = T["tip_deflection_span_over"]
    register = "\n".join(f"| {r['id']} | {r['title']} | {r['scope']} | {r['status']} | {('[Section '+r['section']+'](#'+anchor(r['section'])+')') if r['section'] else ''} |"
                         for r in doc["register"])
    group_rows = "\n".join(
        f"| {kind} | {g['section']['name']} | {kn(g['tension'])} | {kn(st.PHI_T*st.FY*g['section']['area'])} | {kn(g['compression'])} | "
        f"{g['length']:.2f} | {g['slenderness']:.0f} | {kn(st.PHI_C*st.compression_stress(g['slenderness'])*g['section']['area'])} | {g['ratio']:.2f} |"
        for kind, g in groups.items())
    sens = "\n".join(
        f"| span/{ratio:,} | {limit*1000:.1f} | " + (f"{x['chord']['name']} | {x['web']['name']} | {x['tip']*1000:.1f} | span/{st.SPAN/x['tip']:,.0f} | {x['steel']:,.0f} | {x['pod']/1000:.2f} |" if x else "none in the list | | | | | |")
        for ratio, limit, x in st.sensitivity())
    drive = cfg.PROJECT["structure"]["level_drive"]
    worst = max(d["rows"], key=lambda r: r["ratio"])
    split = c["split"]
    more_chord = st.analyse(st.hss(6, 3, .25), d["web"])
    more_web = st.analyse(d["chord"], st.hss(3, 3, .25))
    return f"""# GPU Silo: structural design report

| | |
| --- | --- |
| Document | {doc['document']} |
| Revision | {doc['revision']}, {doc['date']} |
| Status | {doc['status']} |
| Prepared by | {doc['prepared_by']} |
| Checked by | {doc['checked_by']} |
| Approved by | {doc['approved_by']} |

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

The GPU Silo stores {cfg.TOTAL} {cfg.NAME} pods on {cfg.LEVELS} levels round a central steel shaft, inside a double-walled concrete silo. Each pod holds {st.RACKS} GPU racks with its own coolant distribution unit (CDU) and pump. The purpose of this report is to give confidence in the predicted performance of the structure by working through a fixed list of design checks, one at a time, and recording the basis, the method and the result of each.

This revision covers:

- the register of design checks and the basis of design;
- check 2, the pod trusses, sized for gravity load;
- the dead loads that the pods put on the shaft, for check 1;
- the loads at the pod root and the rotating mass of a level, for check 6.

The shaft, its base, the hub at each level and the drive are not designed in this revision. Section 5.5 looks ahead at the stiffness of the shaft because it affects decisions that are being made now.

## 2. Register of design checks

| No. | Check | Scope | Status | Where |
| ---: | --- | --- | --- | --- |
{register}

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
| Hollow structural sections | {steel['hss']} | |
| Yield stress, F<sub>y</sub> | {steel['fy_mpa']} MPa (50 ksi) | ASTM A500 Grade C, shaped sections |
| Tensile strength, F<sub>u</sub> | {steel['fu_mpa']} MPa (62 ksi) | ASTM A500 Grade C |
| Modulus of elasticity, E | {steel['e_gpa']:,} GPa (29,000 ksi) | AISC 360-22 |
| Density | {steel['density_kg_m3']:,} kg/m³ | |
| Design wall thickness | {steel['design_wall_factor']} × nominal | AISC 360-22 Section B4.2, for A500 sections |

### 3.3 Units

Quantities are in SI units: metres, millimetres, kilonewtons and tonnes. Steel sections keep their US names, with dimensions in inches. 1 kip = 4.448 kN and 1 in = 25.4 mm.

### 3.4 Geometry

| Quantity | Value | Basis |
| --- | ---: | --- |
| Clear bore of the silo | {2*cfg.BORE_R:g} m diameter | input |
| Shaft | {2*st.SHAFT_R:.2f} m diameter | input |
| Access round the shaft | {st.ACCESS:.2f} m | input, reduced from 2.28 m in this revision |
| Pod root radius | {st.ROOT:.2f} m | shaft radius + access |
| Rack housing | {cfg.BODY_LENGTH:g} m long, {cfg.BODY_WIDTH:g} m wide, {cfg.BODY_HEIGHT:g} m high | input |
| CDU and pump section | {cfg.SECTION:.2f} m long | fills the pod out to {pod['tip_clearance_m']*1000:.0f} mm from the wall; was 0.50 m |
| Pod length, the cantilever span L | {st.SPAN:.2f} m | |
| Pod tip radius | {st.TIP_R:.2f} m | |
| Frame envelope | {cfg.FRAME_WIDTH:.2f} m wide, {cfg.FRAME_HEIGHT:.2f} m high | {(cfg.FRAME_WIDTH-cfg.BODY_WIDTH)/2*1000:.0f} mm each side of the racks for a chord |
| Levels | {cfg.LEVELS} at {cfg.STORE['pitch_m']:g} m, {cfg.BAYS} pods a level | input |
| Storage pitch and packed pitch | {360/cfg.BAYS:g}° and {cfg.STORE['packed_pitch_degrees']:g}° | input |

Narrowing the access round the shaft to {st.ACCESS:g} m moves every pod {2.86-st.ROOT:.2f} m towards the axis. The racks stay at the shaft end and the CDU and pump section is lengthened to fill the pod out to the wall. Two consequences are recorded here because they affect later checks.

1. **Clearance at the roots.** The pods come closest to each other at their roots. When a level is bunched at {cfg.STORE['packed_pitch_degrees']:g}° the frames are {k['root_gap_packed']*1000:.0f} mm apart there, and a pod being lifted passes the pods either side of the lifting lane with {k['root_gap_lane']*1000:.0f} mm to spare. Both were over 1 m before. An access of {k['access_for_100']:.2f} m would give 100 mm in both cases.
2. **Use of the access.** At {st.ACCESS:g} m the space round the shaft is an inspection space, not a walkway. The frames of neighbouring pods are {k['root_gap_stored']*1000:.0f} mm apart at their roots when stored, so a person cannot pass from the shaft to the wedge between two pods at pod level.

### 3.5 Loads

Dead load, D, is the only load in this revision. Fixed equipment and its liquid contents are taken as dead load, as ASCE 7-22 Chapter 3 provides.

| Item | Mass | Distribution | Status |
| --- | ---: | --- | --- |
| GPU racks | {st.RACKS} × {pod['rack_mass_t']:g} t = {mass['racks']/1000:.1f} t | each rack on the two panel points of its bay | allowance. No shipping or operating weight is published for the {cfg.CLUSTER['rack_model'].replace('NVIDIA ','')}. |
| CDU and pump | {mass['cdu']/1000:.1f} t | uniform over the CDU and pump section | allowance |
| Coolant and piping | {mass['coolant']/1000:.1f} t | uniform over the pod | allowance |
| Truss steel | calculated | at the nodes of each member | from the design |
| Cross members and plan bracing | calculated | uniform over the pod | {st.CROSS['name']}, one top and one bottom at each panel point, and a plan diagonal in each panel, top and bottom |
| Connections | {T['connection_allowance']*100:.0f}% of the steel | with the steel | allowance |
| Housing | {T['housing_kg_per_m2']:g} kg/m² of rack housing and CDU enclosure | uniform over the pod | allowance |

Loads that are not yet included are listed in section 4.11.

### 3.6 Load combinations

| Case | Combination | Basis |
| --- | --- | --- |
| Strength, docked | {T['dead_load_factor']:g} D | ASCE 7-22 Section 2.3.1, combination 1 |
| Strength, hoisted | {T['dead_load_factor']:g} × {T['hoist_impact_factor']:g} D | the same, with a {round((T['hoist_impact_factor']-1)*100)}% allowance for vertical impact, as ASCE 7-22 Section 4.9.3 gives for a powered bridge crane |
| Deflection | 1.0 D | |

### 3.7 Serviceability

The tip of each pod carries the coupling that connects its CDU to the water-glycol store through a sleeve in the inner wall. The vertical position of the tip therefore matters, and it is controlled by a limit on the tip deflection of the truss under dead load.

**Criterion: tip deflection ≤ span/{limit_ratio:,} = {c['limit']*1000:.1f} mm.**

This is a project criterion and not a code minimum. The tolerance of the coupling is not yet known. The limit is an input, and section 4.9 shows what other limits would require. The truss is only one of three contributions to the drop of the tip. The rotation of the root connection and the lean of the shaft are the others, and they belong to checks 6 and 1.

## 4. Check 2: pod truss

### 4.1 Description

Each pod is carried by two vertical trusses, one each side of the racks, {st.TRUSS_SPACING:.2f} m apart centre to centre. They are joined top and bottom at every panel point by cross members and plan bracing, so the pair acts as a box. The trusses are {cfg.FRAME_HEIGHT:.2f} m deep overall and span {st.SPAN:.2f} m as cantilevers from the hub on the shaft.

- **Chords.** Rectangular hollow sections with the long side vertical, no wider than {T['chord_max_width_in']:g} in ({T['chord_max_width_in']*25.4:.0f} mm) so that they fit in the {(cfg.FRAME_WIDTH-cfg.BODY_WIDTH)/2*1000:.0f} mm beside the racks. An I-section was considered. No rolled W-shape has a flange narrower than about 100 mm, so an I-section chord would widen the pod, and a hollow section also gives a flat face to weld the web members to.
- **Web.** Square hollow sections. There is a vertical at every panel point and one diagonal in each panel. The diagonals fall towards the tip, so they are in tension when the pod is docked and the shorter verticals take the compression.
- **Panels.** One panel to each rack, {cfg.BODY_LENGTH/st.RACKS:.2f} m long, so that each rack bears on panel points. The CDU and pump section has {T['cdu_panels']} panels of {cfg.SECTION/T['cdu_panels']:.2f} m.
- **Joints.** Fully welded.
- **Support.** At the root the top chord is held by a clevis that takes the pull and the whole weight. The bottom chord bears on the hub and takes thrust only.

![Elevation of one side truss with member forces](figures/pod_truss.svg)

### 4.2 Design criteria

| No. | Criterion | Limit | Basis |
| ---: | --- | --- | --- |
| 1 | Tip deflection under dead load | span/{limit_ratio:,} = {c['limit']*1000:.1f} mm | section 3.7 |
| 2 | Member strength | required strength ≤ design strength | AISC 360-22 Chapters D and E |
| 3 | Member slenderness | L<sub>c</sub>/r ≤ {T['max_slenderness']} for every member | AISC 360-22 Section E2, user note. Applied to all members because the web forces reverse when the pod is hoisted. |
| 4 | Wall slenderness | (b − 3t)/t ≤ 1.40 √(E/F<sub>y</sub>) = {st.WALL_LIMIT:.1f} | AISC 360-22 Table B4.1a, case 6. No slender walls. |
| 5 | Joint geometry | web width between {T['min_web_to_chord_width']:g} and 1.0 of the chord width | AISC 360-22 Chapter K, limits of applicability |
| 6 | Chord width | ≤ {T['chord_max_width_in']:g} in | the frame envelope |

The lightest pair of sections from the lists in the design file that meets all six is chosen. The lists hold {len(st.CHORDS)} chord sizes from {st.CHORDS[0]['name']} to {st.CHORDS[-1]['name']} and {len(st.WEBS)} web sizes from {st.WEBS[0]['name']} to {st.WEBS[-1]['name']}, none with a wall thinner than 3/16 in.

### 4.3 Analysis

Each truss is analysed as a pin-jointed plane truss by the direct stiffness method, with half the pod's load applied at its panel points. Member lengths are taken between the centre lines of the chords, {d['model']['depth']:.3f} m apart. The welded joints make the real truss slightly stiffer than the model, so the calculated deflection is an upper estimate for the truss alone.

Two support cases are analysed:

1. **Docked.** A cantilever from the root, as in Figure 1.
2. **Hoisted.** Hanging from the hoist's two pickups on the top chord, at panel points {T['pickup_panel_points'][0]} and {T['pickup_panel_points'][1]}, which are {d['model']['xs'][T['pickup_panel_points'][0]]:.2f} m and {d['model']['xs'][T['pickup_panel_points'][1]]:.2f} m from the root. The pickups carry {kn(2*d['lifting'][0])} kN and {kn(2*d['lifting'][1])} kN for the whole pod, unfactored.

Compression members are checked for flexural buckling with an effective length equal to the distance between panel points.

### 4.4 Selected sections

| Member | Section | Size, mm | Steel |
| --- | --- | --- | --- |
| Top and bottom chords | **{d['chord']['name']}**, long side vertical | {d['chord']['h']*1000:.0f} deep × {d['chord']['b']*1000:.0f} wide × {d['chord']['t_nominal']*1000:.1f} wall | {steel['hss']} |
| Verticals and diagonals | **{d['web']['name']}** | {d['web']['h']*1000:.0f} × {d['web']['b']*1000:.0f} × {d['web']['t_nominal']*1000:.1f} wall | {steel['hss']} |
| Cross members and plan bracing | {st.CROSS['name']} | {st.CROSS['h']*1000:.0f} × {st.CROSS['b']*1000:.0f} × {st.CROSS['t_nominal']*1000:.1f} wall | {steel['hss']} |

### 4.5 Deflection

| Quantity | Value |
| --- | ---: |
| Tip deflection under dead load, stiffness analysis | **{d['tip']*1000:.2f} mm** |
| As a fraction of the span | span/{st.SPAN/d['tip']:,.0f} |
| Limit | {c['limit']*1000:.2f} mm (span/{limit_ratio:,}) |
| Tip deflection by statics and virtual work (section 4.7) | {c['hand']*1000:.2f} mm |
| **Result** | **{'Satisfied' if d['tip']<=c['limit'] else 'Not satisfied'}**, {d['tip']/c['limit']*100:.0f}% of the limit |

The truss is {cfg.FRAME_HEIGHT/st.SPAN:.2f} of its span deep, which is very deep for a cantilever. Two things follow.

- The lightest sections in the list already meet span/{limit_ratio:,}. Stiffness does not call for more steel than the minimum practical sizes at this limit.
- The verticals and diagonals contribute {split['webs']*1000:.1f} mm of the deflection and the chords {split['chords']*1000:.1f} mm. Heavier sections buy little either way. {more_chord['chord']['name']} chords with the same web give {more_chord['tip']*1000:.1f} mm for {more_chord['steel']-d['steel']:,.0f} kg more steel a pod, and {more_web['web']['name']} web members with the same chords give {more_web['tip']*1000:.1f} mm for {more_web['steel']-d['steel']:,.0f} kg more.

### 4.6 Strength

Required strengths are the larger of the docked and hoisted cases with the factors in section 3.6. Design strengths are φ<sub>t</sub>F<sub>y</sub>A<sub>g</sub> in tension (Section D2, φ<sub>t</sub> = 0.90) and φ<sub>c</sub>F<sub>cr</sub>A<sub>g</sub> in compression (Section E3, φ<sub>c</sub> = 0.90). Tensile rupture does not govern for members welded all round, because 0.75 F<sub>u</sub> exceeds 0.90 F<sub>y</sub> for this steel.

| Member group | Section | Tension, kN | Design tension strength, kN | Compression, kN | Longest, m | L<sub>c</sub>/r | Design compression strength, kN | Highest ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{group_rows}

The most heavily used member is the {worst['kind'].lower()} at panel point {worst['panel']}, at {worst['ratio']:.2f}. Every member has a reserve of strength, and no member governs the design. Forces in each member are in Appendix A.

### 4.7 Verification

The stiffness analysis is checked in three ways each time the report is generated. The checks are in [structure.py](../gpu_silo/structure.py) and the build fails if one does not hold.

| Check | Stiffness analysis | Independent value | Agreement |
| --- | ---: | ---: | --- |
| Tip deflection, by method of sections and virtual work | {d['tip']*1000:.3f} mm | {c['hand']*1000:.3f} mm | within {abs(c['hand']-d['tip'])/d['tip']*100:.2f}% |
| Vertical reaction of one truss against half the pod weight | {kn(d['root_shear'],2)} kN | {kn(d['weight']/2,2)} kN | equal |
| Root couple of one truss against half the root moment | {kn(d['root_pull']*d['model']['depth'],1)} kN·m | {kn(c['moment_root']/2,1)} kN·m | equal |

Section properties are calculated from the nominal size, the design wall thickness and an outside corner radius of twice the wall. For {st.hss(6,3,.25)['name']} this gives {st.hss(6,3,.25)['area']/st.INCH**2:.2f} in² and {st.hss(6,3,.25)['kg_m']/1.48816:.2f} lb/ft against 3.84 in² and 13.91 lb/ft in the AISC Manual. The properties of the selected sections are in Appendix B and should be compared with the Manual at the checking stage.

### 4.8 Weight of a pod

| Item | Mass, kg | Basis |
| --- | ---: | --- |
| Two trusses | {d['truss_steel']:,.0f} | {d['chord']['name']} chords, {d['web']['name']} web |
| Cross members and plan bracing | {d['cross']:,.0f} | {d['cross_m']:.1f} m of {st.CROSS['name']} |
| Connections | {d['connections']:,.0f} | {T['connection_allowance']*100:.0f}% of the steel |
| Housing | {d['housing']:,.0f} | {T['housing_kg_per_m2']:g} kg/m² |
| **Frame and housing** | **{d['frame']:,.0f}** | the earlier allowance was 1,500 kg for a 5.5 m pod |
| Racks | {mass['racks']:,.0f} | allowance |
| CDU and pump | {mass['cdu']:,.0f} | allowance |
| Coolant and piping | {mass['coolant']:,.0f} | allowance |
| **One pod, operating** | **{d['pod']:,.0f}** | {kn(d['weight'])} kN |

Steel is {d['steel']/d['pod']*100:.0f}% of the weight of a pod. The racks are {mass['racks']/d['pod']*100:.0f}%, so the rack weight is the number that most needs confirming.

### 4.9 Sensitivity to the deflection limit

The table gives the lightest design in the list for other limits, with all the other criteria unchanged.

| Limit | Allowed, mm | Chords | Web | Tip deflection, mm | As a fraction | Steel a pod, kg | Pod, t |
| --- | ---: | --- | --- | ---: | --- | ---: | ---: |
{sens}

### 4.10 Conclusion

{d['chord']['name']} chords with {d['web']['name']} verticals and diagonals carry the pod with a tip deflection of {d['tip']*1000:.1f} mm, which is span/{st.SPAN/d['tip']:,.0f}, and a highest strength ratio of {worst['ratio']:.2f}. The design is governed by the minimum practical section sizes and not by stiffness or strength under gravity. A pod weighs {d['pod']/1000:.2f} t in operation.

The result holds for gravity load only. The items in section 4.11 could change the section sizes, the lateral case most of all, and the design should not be treated as final until they are closed.

### 4.11 Not covered by this check

1. **Lateral load.** The pair of trusses is only {st.TRUSS_SPACING:.2f} m wide and cantilevers {st.SPAN:.2f} m sideways as well as downwards. Earthquake load and the starting and stopping of a level act sideways on it. The site and its seismic design category are not yet fixed. This case is likely to govern the chords and the plan bracing.
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
- While a pod is being lifted, every level that is already full closes up from {360/cfg.BAYS:g}° to {cfg.STORE['packed_pitch_degrees']:g}° between pods to open the lane.

The base of the shaft is to be a heavy fixed connection to the foundation, because of the out-of-balance loads in section 5.3. It is designed with the foundation under checks 1 and 4.

### 5.2 Dead load from the pods

| Quantity | Value | Basis |
| --- | ---: | --- |
| Weight of one pod, W | {kn(c['weight'])} kN ({c['pod_t']:.2f} t) | section 4.8 |
| Centre of gravity from the root | {d['centre']:.2f} m | |
| Centre of gravity from the shaft axis | {c['arm']:.2f} m | root radius {st.ROOT:.2f} m |
| Moment of one pod at its root | {kn(c['moment_root'],0)} kN·m | |
| Moment of one pod about the shaft axis, M<sub>pod</sub> | **{kn(c['moment_axis'],0)} kN·m** | |
| Weight of one level, {cfg.BAYS} pods | {kn(c['level_weight'],0)} kN ({cfg.BAYS*c['pod_t']:.1f} t) | |
| Weight of {cfg.TOTAL} pods on the shaft | **{kn(c['store_weight'],0)} kN ({cfg.TOTAL*c['pod_t']:,.0f} t)** | |

All values are unfactored. They exclude the hubs, the bearings, the access floors and the self-weight of the shaft, which are not yet designed. The earlier allowance was 8.5 t a pod with its centre of gravity about 5.6 m from the axis, which is about 467 kN·m. The pod is now {c['pod_t']-8.5:+.2f} t and its centre of gravity is {5.6-c['arm']:.1f} m closer to the axis, because the racks have moved to the shaft end. The moment of a pod about the axis is {(1-c['moment_axis']/467e3)*100:.0f}% lower.

### 5.3 Out-of-balance moment

A complete level stored at {360/cfg.BAYS:g}° is balanced and puts no moment on the shaft. Moment arises in two ways while the store is being filled or a pod is being exchanged.

| State | Moment on the shaft | In terms of M<sub>pod</sub> |
| --- | ---: | ---: |
| One complete level, stored at {360/cfg.BAYS:g}° | 0 | 0 |
| One complete level, bunched at {cfg.STORE['packed_pitch_degrees']:g}° | {kn(u['bunched'],0)} kN·m | {u['bunched']/c['moment_axis']:.2f} |
| One level part filled, worst number of pods | {kn(u['partial_max'],0)} kN·m | {u['partial_max']/c['moment_axis']:.2f} |
| **Worst state in the filling sequence, at the base** | **{kn(u['base'],0)} kN·m** | **{u['base']/c['moment_axis']:.2f}** |
| Every level half filled on the same side, at the base | {kn(u['unrestricted'],0)} kN·m | {u['unrestricted']/c['moment_axis']:.1f} |

The worst state in the sequence has {u['full']} levels full and bunched and {u['placed']} pods on the level being filled. The moments of the bunched levels all point away from the lifting lane, so they add up the height of the shaft. Figure 2 shows this state.

The last row is not part of the planned sequence. It is the moment that would arise if the fill order were not controlled, and it is {u['unrestricted']/u['base']:.1f} times the sequence value. Whether the shaft and its base are designed for the sequence value or for the uncontrolled value is a decision for check 1.

![Plan of the worst out-of-balance state](figures/shaft_unbalance.svg)

### 5.4 Loads at the base of the shaft

| Load | Value | Note |
| --- | ---: | --- |
| Vertical load from the pods | {kn(c['store_weight'],0)} kN | unfactored, excludes the shaft, hubs and floors |
| Moment, worst state in the filling sequence | {kn(u['base'],0)} kN·m | unfactored, shaft free at the top |
| Moment, uncontrolled fill | {kn(u['unrestricted'],0)} kN·m | unfactored, shaft free at the top |
| Shear | 0 | gravity produces couples, not shear, unless the shaft is restrained at the crown |

### 5.5 Look ahead: lean of the shaft

Check 1 has not started, but one result is given now because it bears on the layout. When the shaft leans, each pod tilts with it and its tip drops by the slope of the shaft times the tip radius of {st.TIP_R:.2f} m. A drop of {sh['allowed']*1000:.0f} mm at the tip is used here as a trial limit.

| Case, worst state in the filling sequence | Slope of the shaft | Drop at a pod tip | Moment at the base |
| --- | ---: | ---: | ---: |
| Tube {sh['diameter']*1000:.0f} mm diameter × {sh['wall']*1000:.0f} mm wall, free at the top | {sh['free']['slope']*1000:.1f} mrad | **{sh['drop_free']*1000:.0f} mm** | {kn(sh['free']['base'],0)} kN·m |
| The same tube, held in position at the crown | {sh['held']['slope']*1000:.2f} mrad | **{sh['drop_held']*1000:.1f} mm** | {kn(sh['held']['base'],0)} kN·m |

| Stiffness | EI, GN·m² |
| --- | ---: |
| Needed for {sh['allowed']*1000:.0f} mm at the tip, shaft free at the top | {sh['ei_free']/1e9:.0f} |
| Trial tube, {sh['diameter']*1000:.0f} × {sh['wall']*1000:.0f} mm | {sh['ei']/1e9:.1f} |
| Solid steel bar of {sh['diameter']*1000:.0f} mm diameter | {sh['ei_solid']/1e9:.1f} |

A free-standing shaft of the present diameter cannot hold the pods level during filling. A solid bar of that diameter has {sh['ei_solid']/sh['ei_free']*100:.0f}% of the stiffness needed. Three ways to deal with this are open.

1. **Hold the top of the shaft in position**, through the crown of the cage to the inner wall. This cuts the lean by a factor of about {sh['free']['slope']/sh['held']['slope']:.0f} and the base moment by a factor of about {sh['free']['base']/sh['held']['base']:.0f}. It puts a horizontal force of {kn(sh['held']['reaction'],0)} kN on the wall at the crown.
2. **A larger shaft.** A free-standing tube with a {sh['wall']*1000:.0f} mm wall would need to be about {sh['diameter_free']:.1f} m in diameter. That takes back space just given to the pods.
3. **A filling sequence that keeps the levels balanced**, which changes how the lifting lane is opened.

The trial tube and the trial limit are inputs for this comparison and are not design values.

### 5.6 Decisions needed for check 1

1. Is the shaft held at the crown, and by what: the crown of the cage, or the floors of the power levels?
2. Is the base designed for the filling sequence or for an uncontrolled fill?
3. What carries the two power levels and the lid, about {k['top_weight_t']:.0f} t of machinery: the shaft, the cage or the wall?
4. What drop at a pod tip can the wall coupling accept?

## 6. Check 6: root connection and level drive, design loads

The connection and the drive are not designed in this revision. These are the loads from the pods as now designed, unfactored.

### 6.1 At the root of one pod

| Load | One truss | One pod |
| --- | ---: | ---: |
| Pull on the upper clevis | {kn(d['root_pull'])} kN | {kn(2*d['root_pull'])} kN |
| Thrust on the lower bearing | {kn(d['root_thrust'])} kN | {kn(2*d['root_thrust'])} kN |
| Weight on the upper clevis | {kn(d['root_shear'])} kN | {kn(2*d['root_shear'])} kN |
| Lever arm between clevis and bearing | {d['model']['depth']:.3f} m | |

The tip drops {st.SPAN/d['model']['depth']:.1f} mm for each millimetre of horizontal slack or stretch between the clevis and the bearing. The stiffness and fit of the root connection will therefore matter more to the position of the tip than the truss does.

### 6.2 For the drive of one level

| Quantity | Value | Basis |
| --- | ---: | --- |
| Rotating weight of a full level | {kn(c['level_weight'],0)} kN | pods only |
| Mass moment of inertia of one pod about the shaft axis | {c['inertia_pod']:,.0f} kg·m² | |
| Mass moment of inertia of a full level | **{c['inertia_level']:,.0f} kg·m²** | pods only |
| Out-of-balance moment on the hub bearing, level part filled | {kn(u['partial_max'],0)} kN·m | section 5.3 |
| Out-of-balance moment on the hub bearing, level bunched | {kn(u['bunched'],0)} kN·m | section 5.3 |
| Torque to accelerate a full level, turning one bay in {drive['index_seconds']:g} s | {c['index_torque']/1000:.1f} kN·m | accelerating for half the turn and braking for half |

The inertia torque is small. The drive will be sized by the friction of the hub bearing under the weight and the out-of-balance moment, and by holding a level against the lean of the shaft. Both depend on the bearing chosen under check 6.

Check 6 also needs one point settled. The animation shows each level turning on a fixed shaft, with the pods of a level able to close up. If instead the whole shaft is to turn, the base cannot be a fixed connection and the loads in section 5.4 pass through a slewing bearing.

## 7. Open items

| No. | Item | Affects | Needed from |
| ---: | --- | --- | --- |
| 1 | Weight of a rack in operation, and of the CDU, pump and coolant | checks 1, 2, 4 and 6 | equipment supplier |
| 2 | Tolerance of the wall coupling, to fix the limit on tip drop | checks 1, 2 and 6 | coupling supplier |
| 3 | Site and seismic design category, for the lateral case | checks 1 to 4 and 6 | project |
| 4 | Clearance of {min(k['root_gap_packed'],k['root_gap_lane'])*1000:.0f} mm between pod frames at the roots: accept, or widen the access to {k['access_for_100']:.2f} m | layout | project |
| 5 | Restraint of the shaft at the crown | check 1 | project, section 5.6 |
| 6 | Fixed shaft with turning levels, or a turning shaft | checks 1 and 6 | project, section 6.2 |
| 7 | Load path of the power levels and the lid | checks 1, 3 and 4 | project |
| 8 | Comparison of section properties with the AISC Manual | check 2 | checker |

## Appendix A: member forces

One side truss. Forces are unfactored in the docked and hoisted columns, tension positive. Factored values use the combinations in section 3.6. Panels are numbered from 1 at the root. For a vertical the number is its panel point, from 0 at the root.

{members_table(d)}

## Appendix B: section properties

Calculated as described in section 4.7.

| Section | Depth × width, mm | Nominal wall, mm | Design wall, mm | Area, mm² (in²) | r<sub>x</sub>, mm | r<sub>y</sub>, mm | Mass, kg/m (lb/ft) | Wall slenderness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{section_row(d['chord'])}
{section_row(d['web'])}
"""


def anchor(section):
    return {"4": "4-check-2-pod-truss", "5": "5-check-1-central-shaft-design-loads",
            "6": "6-check-6-root-connection-and-level-drive-design-loads"}[section]


def outputs():
    return {FILE: markdown(), FIGURES / "pod_truss.svg": truss_figure(), FIGURES / "shaft_unbalance.svg": balance_figure()}


def write():
    FIGURES.mkdir(exist_ok=True)
    for path, text in outputs().items():
        path.write_text(text, encoding="utf-8", newline="\n")
    return FILE


def current():
    return all(path.is_file() and path.read_text(encoding="utf-8") == text for path, text in outputs().items())
