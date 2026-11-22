"""Writes the structural design report and its figures from design/project.json.

The report is generated so that every number in it comes from the design file and the checks
in structure.py. Edit the inputs or this module, then run `python -m gpu_silo calcs`.
"""
import math
from pathlib import Path

from . import calcs
from . import design as cfg
from . import logistics
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


def shaft_figure():
    """Elevation of the shaft with the couples of the worst filling state, and the bending moment in it when held at the top."""
    c = st.C
    chosen = c["shaft"]["chosen"]
    cases = {k["key"]: k for k in chosen["cases"]}
    scale, base, x0 = 14.5, 446., 250.
    y = lambda z: base - z * scale
    out = [f'<text x="20" y="26" font-size="15" fill="{INK}" font-weight="bold">Figure 3. The shaft: loads in the worst filling state, and bending moment</text>',
           f'<text x="20" y="45" fill="{MUTED}">Fixed at the foundation and held sideways at the support rig. Unfactored. Moments in kN·m.</text>']
    top = y(st.SHAFT_TOP)
    out.append(f'<rect x="{x0-8}" y="{top:.1f}" width="16" height="{base-top:.1f}" fill="#8fa3a8" stroke="{INK}" stroke-width="1.2"/>')
    out.append(f'<line x1="{x0-60}" y1="{base}" x2="{x0+60}" y2="{base}" stroke="{INK}" stroke-width="2.4"/>')
    for k in range(9):
        out.append(f'<line x1="{x0-56+k*14}" y1="{base}" x2="{x0-66+k*14}" y2="{base+10}" stroke="{INK}" stroke-width="1"/>')
    out.append(f'<text x="{x0}" y="{base+28}" fill="{INK}" text-anchor="middle">fixed base on the foundation</text>')
    out.append(f'<path d="M{x0+8},{top+6:.1f} l18,-9 v18 z" fill="{COMPRESSION}"/><line x1="{x0+26}" y1="{top+6:.1f}" x2="{x0+92}" y2="{top+6:.1f}" stroke="{COMPRESSION}" stroke-width="3"/>')
    out.append(f'<text x="{x0-42}" y="{top+4:.1f}" fill="{INK}" text-anchor="end">{st.SHAFT_TOP:.2f} m: connector to the support rig</text>')
    sequence = cases["sequence"]
    for (z, m), (_, load) in zip(sequence["couples"], sequence["loads"]):
        out.append(f'<line x1="{x0-34}" y1="{y(z):.1f}" x2="{x0+34}" y2="{y(z):.1f}" stroke="{INK}" stroke-width="2.2"/>')
        out.append(f'<text x="{x0-42}" y="{y(z)+4:.1f}" fill="{INK}" text-anchor="end">{z:.2f} m: {m/1000:,.0f} kN·m, {load/1000:,.0f} kN</text>')
    out.append(f'<text x="{x0-42}" y="{y(sequence["couples"][0][0])-18:.1f}" fill="{MUTED}" text-anchor="end">hub height: couple, weight</text>')
    peak = max(k["result"]["peak"] for k in chosen["cases"])
    for column, key, colour, title in ((470, "sequence", TENSION, "Worst state of the filling sequence"), (760, "uncontrolled", COMPRESSION, "Uncontrolled fill")):
        result = cases[key]["result"]
        out.append(f'<line x1="{column}" y1="{top:.1f}" x2="{column}" y2="{base}" stroke="{INK}" stroke-width="1.2"/>')
        points = " ".join(f"{column+m/peak*118:.1f},{y(z):.1f}" for z, m in zip(result["z"][::12], result["moment"][::12]))
        out.append(f'<polygon points="{column},{base} {points} {column},{top:.1f}" fill="{colour}" fill-opacity=".18" stroke="{colour}" stroke-width="1.6"/>')
        out.append(f'<text x="{column}" y="{top-26:.1f}" fill="{INK}" text-anchor="middle" font-weight="bold">{title}</text>')
        out.append(f'<text x="{column}" y="{top-10:.1f}" fill="{MUTED}" text-anchor="middle">top reaction {abs(result["reaction"])/1000:,.0f} kN</text>')
        out.append(f'<text x="{column}" y="{base+18}" fill="{INK}" text-anchor="middle">base {result["base"]/1000:+,.0f}</text>')
        index = int(abs(result["moment"]).argmax())
        zp, mp = result["z"][index], result["moment"][index]
        out.append(f'<text x="{column+mp/peak*118+(8 if mp>0 else -8):.1f}" y="{y(zp)-4:.1f}" fill="{INK}" text-anchor="{"start" if mp>0 else "end"}">{mp/1000:+,.0f} at {zp:.1f} m</text>')
    return svg(960, 496, out)


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


ANCHORS = {"4": "4-check-2-pod-truss", "5": "5-check-1-central-shaft",
           "6": "6-check-6-root-connection-and-level-drive-design-loads",
           "7": "7-checks-7-8-and-9-support-rig-shaft-connector-and-wall-mounts-design-loads"}


def markdown():
    c, k = st.C, calcs.C
    d = c["design"]
    doc = cfg.PROJECT["design_checks"]
    T, steel, pod, S = st.T, st.STEEL, cfg.POD, st.SHAFT
    u, sh, rig = c["unbalance"], c["shaft"], c["rig"]
    ch = sh["chosen"]
    sec, mv = ch["section"], ch["movement"]
    cases = {case["key"]: case for case in ch["cases"]}
    free = sh["free"]
    free_cases = {case["key"]: case for case in free["cases"]}
    groups = d["groups"]
    mass = d["mass"]
    e_fy = st.E / st.FY_SHAFT
    register = "\n".join(f"| {r['id']} | {r['title']} | {r['scope']} | {r['status']} | {('[Section '+r['section']+'](#'+ANCHORS[r['section']]+')') if r['section'] else ''} |"
                         for r in doc["register"])
    group_rows = "\n".join(
        f"| {kind} | {g['section']['name']} | {kn(g['tension'])} | {kn(st.PHI_T*st.FY*g['section']['area'])} | {kn(g['compression'])} | "
        f"{g['length']:.2f} | {g['slenderness']:.0f} | {kn(st.PHI_C*st.compression_stress(g['slenderness'])*g['section']['area'])} | {g['ratio']:.2f} |"
        for kind, g in groups.items())
    sens = "\n".join(
        f"| {limit*1000:g} | " + (f"{x['chord']['name']} | {x['web']['name']} | {x['tip']*1000:.1f} | span/{st.SPAN/x['tip']:,.0f} | {x['steel']:,.0f} | {x['pod']/1000:.2f} |" if x else "none in the list | | | | | |")
        for limit, x in st.sensitivity())
    drive = cfg.PROJECT["structure"]["level_drive"]
    worst = max(d["rows"], key=lambda r: r["ratio"])
    split = c["split"]
    lighter = st.analyse(st.CHORDS[0], st.WEBS[0])
    wall_rows = "\n".join(
        f"| {'**' if w is ch else ''}{st.inches(w['section']['wall_in'])} ({w['section']['wall']*1000:.1f}){'**' if w is ch else ''} | {w['section']['ratio']:.1f} | {w['section']['kg_m']:,.0f} | "
        f"{w['movement']['shortening']*1000:.2f} | {w['movement']['lean_drop']*1000:.2f} | {'**' if w is ch else ''}{w['movement']['total']*1000:.2f}{'**' if w is ch else ''} | {w['ratio']:.2f} | "
        f"{'Selected' if w is ch else 'Passes' if w['passes'] else 'Tip movement too large' if not w['ok']['movement'] else 'Fails'} |"
        for w in sh["walls"])
    case_rows = "\n".join(
        f"| {case['name']} | {case['pods']} | {kn(case['axial'],0)} | {kn(case['pu'],0)} | {kn(case['result']['peak'],0)} | {case['b1']:.2f} | {kn(case['mu'],0)} | {case['pu']/ch['pc']:.2f} | {case['mu']/ch['mc']:.2f} | **{case['ratio']:.2f}** |"
        for case in ch["cases"])
    reaction_rows = "\n".join(
        f"| {case['name']} | {kn(case['axial'],0)} | {kn(abs(case['result']['base']),0)} | {kn(abs(case['result']['reaction']),0)} | {kn(case['pu'],0)} | {kn(st.T['dead_load_factor']*case['b1']*abs(case['result']['base']),0)} | {kn(case['vu'],0)} |"
        for case in ch["cases"])
    spring_rows = "\n".join(
        f"| {stiff:,} | {kn(abs(next(x for x in w['cases'] if x['key']=='sequence')['result']['reaction']),0)} | {abs(next(x for x in w['cases'] if x['key']=='sequence')['result']['top'])*1000:.1f} | {w['movement']['lean_drop']*1000:.2f} | {w['movement']['total']*1000:.2f} | {'Yes' if w['ok']['movement'] else 'No'} |"
        for stiff, w in sh["springs"])
    rig_rows = "\n".join(
        f"| {case['name']} | {kn(case['reaction'],0)} | {kn(case['factored'],0)} | {kn(case['mount'],0)} |" for case in rig["cases"])
    level_rows = "\n".join(f"| {level} | {st.level_height(level):.2f} | {drop*1000:.2f} |" for level, drop in zip(range(1, cfg.LEVELS + 1), mv["by_level"]))
    hub = S["hub_and_floor_t_per_level"]
    seq, unc, comp = cases["sequence"], cases["uncontrolled"], cases["complete"]
    return f"""# GPU Silo: structural design report

| | |
| --- | --- |
| Document | {doc['document']} |
| Revision | {doc['revision']}, {doc['date']} |
| Status | {doc['status']} |
| Prepared by | {doc['prepared_by']} |
| Checked by | {doc['checked_by']} |
| Approved by | {doc['approved_by']} |

| Revision | Date | Changes |
| --- | --- | --- |
| A | 2026-11-21 | First issue. Register of checks, basis of design, pod truss, loads on the shaft. |
| B | 2026-11-22 | Access round the shaft widened from 0.50 m to {st.ACCESS:.2f} m. Truss limit changed from span/1,000 to {c['limit']*1000:g} mm. Shaft confirmed as fixed, with the levels turning on it, and held at its top by the support rig. Check 1 carried out. Checks 7, 8 and 9 added. |

This report is generated from [project.json](project.json) by `python -m gpu_silo calcs`. Every number in it is calculated by [structure.py](../gpu_silo/structure.py) from the inputs in that file. To change a result, change an input and run the command.

## Contents

1. [Purpose and scope](#1-purpose-and-scope)
2. [Register of design checks](#2-register-of-design-checks)
3. [Basis of design](#3-basis-of-design)
4. [Check 2: pod truss](#{ANCHORS['4']})
5. [Check 1: central shaft](#{ANCHORS['5']})
6. [Check 6: root connection and level drive, design loads](#{ANCHORS['6']})
7. [Checks 7, 8 and 9: support rig, shaft connector and wall mounts, design loads](#{ANCHORS['7']})
8. [Open items](#8-open-items)
9. [Appendix A: member forces in the pod truss](#appendix-a-member-forces-in-the-pod-truss)
10. [Appendix B: section properties](#appendix-b-section-properties)

## 1. Purpose and scope

The GPU Silo stores {cfg.TOTAL} {cfg.NAME} pods on {cfg.LEVELS} levels round a central steel shaft, inside a double-walled concrete silo. Each pod holds {st.RACKS} GPU racks with its own coolant distribution unit (CDU) and pump. The purpose of this report is to give confidence in the predicted performance of the structure by working through a fixed list of design checks, one at a time, and recording the basis, the method and the result of each.

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
{register}

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
| Hollow structural sections | {steel['hss']} | |
| Yield stress of hollow sections, F<sub>y</sub> | {steel['fy_mpa']} MPa (50 ksi) | ASTM A500 Grade C, shaped sections |
| Tensile strength of hollow sections, F<sub>u</sub> | {steel['fu_mpa']} MPa (62 ksi) | ASTM A500 Grade C |
| Design wall thickness of hollow sections | {steel['design_wall_factor']} × nominal | AISC 360-22 Section B4.2, for A500 sections |
| Shaft | {S['steel']} | |
| Yield stress of the shaft plate, F<sub>y</sub> | {S['fy_mpa']} MPa (50 ksi) | ASTM A572 Grade 50 |
| Design wall thickness of the shaft | nominal | plate, submerged-arc welded |
| Modulus of elasticity, E | {steel['e_gpa']:,} GPa (29,000 ksi) | AISC 360-22 |
| Density | {steel['density_kg_m3']:,} kg/m³ | |

### 3.3 Units

Quantities are in SI units: metres, millimetres, kilonewtons and tonnes. Steel sections and plate keep their US sizes in inches. 1 kip = 4.448 kN and 1 in = 25.4 mm.

### 3.4 Geometry

| Quantity | Value | Basis |
| --- | ---: | --- |
| Clear bore of the silo | {2*cfg.BORE_R:g} m diameter | input |
| Shaft | {st.SHAFT_D:.2f} m outside diameter | input |
| Access round the shaft | {st.ACCESS:.2f} m | input, revision B |
| Pod root radius | {st.ROOT:.2f} m | shaft radius + access |
| Rack housing | {cfg.BODY_LENGTH:g} m long, {cfg.BODY_WIDTH:g} m wide, {cfg.BODY_HEIGHT:g} m high | input |
| CDU and pump section | {cfg.SECTION:.2f} m long | fills the pod out to {pod['tip_clearance_m']*1000:.0f} mm from the wall |
| Pod length, the cantilever span L | {st.SPAN:.2f} m | |
| Pod tip radius | {st.TIP_R:.2f} m | |
| Frame envelope | {cfg.FRAME_WIDTH:.2f} m wide, {cfg.FRAME_HEIGHT:.2f} m high | {(cfg.FRAME_WIDTH-cfg.BODY_WIDTH)/2*1000:.0f} mm each side of the racks for a chord |
| Levels | {cfg.LEVELS} at {cfg.STORE['pitch_m']:g} m, {cfg.BAYS} pods a level | input |
| Storage pitch and packed pitch | {360/cfg.BAYS:g}° and {cfg.STORE['packed_pitch_degrees']:g}° | input |
| Shaft, from the foundation to the support rig | {st.SHAFT_TOP:.2f} m | the connector is at mid-depth of the rig |

**Clearance at the pod roots.** The pods come closest to each other at their roots. With {st.ACCESS:.2f} m of access the frames are {k['root_gap_packed']*1000:.0f} mm apart there when a level is bunched at {cfg.STORE['packed_pitch_degrees']:g}°, and a pod being lifted passes the pods either side of the lifting lane with {k['root_gap_lane']*1000:.0f} mm to spare. Stored at {360/cfg.BAYS:g}° the frames are {k['root_gap_stored']*1000:.0f} mm apart at the roots, so the space round the shaft is an inspection space and there is no way through at pod level to the wedge between two pods.

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
| Hub, bearing and access floor | {hub:g} t a level | at each hub | allowance, to be replaced under check 6 |
| Shaft | calculated | uniform | from the design |
| Power and data services inside the shaft | {S['services_kg_per_m']:g} kg/m | uniform | allowance |

### 3.6 Load combinations

| Case | Combination | Basis |
| --- | --- | --- |
| Strength | {T['dead_load_factor']:g} D | ASCE 7-22 Section 2.3.1, combination 1 |
| Strength, pod hoisted | {T['dead_load_factor']:g} × {T['hoist_impact_factor']:g} D | the same, with a {round((T['hoist_impact_factor']-1)*100)}% allowance for vertical impact, as ASCE 7-22 Section 4.9.3 gives for a powered bridge crane |
| Deflection and movement | 1.0 D | |

### 3.7 Serviceability

The tip of each pod carries the coupling that connects its CDU to the water-glycol store through a sleeve in the inner wall, so the vertical position of the tip matters. Two limits control it, and both are inputs. A deflection limit of 5 mm was set by the project for revision B. This report applies it twice, once to the truss and once to the shaft, and that reading is to be confirmed (open item 4).

| No. | Criterion | Limit | Checked in |
| ---: | --- | ---: | --- |
| 1 | Deflection of the pod truss at its tip under dead load | {c['limit']*1000:g} mm | section 4.5 |
| 2 | Movement of a pod tip caused by the shaft: its shortening as the store is filled, plus its lean in the worst filling state | {sh['limit']*1000:g} mm | section 5.7 |

The first is a fixed amount that can be set out when a pod is built. The second develops after a pod has been docked, as other pods are added, and is what the coupling has to follow. The tolerance of the coupling is not yet known. The rotation of the root connection also moves the tip and belongs to check 6.

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
| 1 | Tip deflection under dead load | {c['limit']*1000:g} mm | section 3.7 |
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
| Limit | {c['limit']*1000:.2f} mm |
| Tip deflection by statics and virtual work (section 4.7) | {c['hand']*1000:.2f} mm |
| **Result** | **{'Satisfied' if d['tip']<=c['limit'] else 'Not satisfied'}**, {d['tip']/c['limit']*100:.0f}% of the limit |

The {c['limit']*1000:g} mm limit governs the chords. The lightest sections in the list, {lighter['chord']['name']} chords with {lighter['web']['name']} web members, deflect {lighter['tip']*1000:.2f} mm and do not pass. The verticals and diagonals contribute {split['webs']*1000:.1f} mm of the deflection of the selected truss and the chords {split['chords']*1000:.1f} mm, because the truss is {cfg.FRAME_HEIGHT/st.SPAN:.2f} of its span deep.

### 4.6 Strength

Required strengths are the larger of the docked and hoisted cases with the factors in section 3.6. Design strengths are φ<sub>t</sub>F<sub>y</sub>A<sub>g</sub> in tension (Section D2, φ<sub>t</sub> = 0.90) and φ<sub>c</sub>F<sub>cr</sub>A<sub>g</sub> in compression (Section E3, φ<sub>c</sub> = 0.90). Tensile rupture does not govern for members welded all round, because 0.75 F<sub>u</sub> exceeds 0.90 F<sub>y</sub> for this steel.

| Member group | Section | Tension, kN | Design tension strength, kN | Compression, kN | Longest, m | L<sub>c</sub>/r | Design compression strength, kN | Highest ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{group_rows}

The most heavily used member is the {worst['kind'].lower()} at panel point {worst['panel']}, at {worst['ratio']:.2f}. Strength does not govern. Forces in each member are in Appendix A.

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
| **Frame and housing** | **{d['frame']:,.0f}** | |
| Racks | {mass['racks']:,.0f} | allowance |
| CDU and pump | {mass['cdu']:,.0f} | allowance |
| Coolant and piping | {mass['coolant']:,.0f} | allowance |
| **One pod, operating** | **{d['pod']:,.0f}** | {kn(d['weight'])} kN |

Steel is {d['steel']/d['pod']*100:.0f}% of the weight of a pod. The racks are {mass['racks']/d['pod']*100:.0f}%, so the rack weight is the number that most needs confirming.

### 4.9 Sensitivity to the deflection limit

The table gives the lightest design in the list for other limits, with all the other criteria unchanged.

| Limit, mm | Chords | Web | Tip deflection, mm | As a fraction | Steel a pod, kg | Pod, t |
| ---: | --- | --- | ---: | --- | ---: | ---: |
{sens}

### 4.10 Conclusion

{d['chord']['name']} chords with {d['web']['name']} verticals and diagonals carry the pod with a tip deflection of {d['tip']*1000:.1f} mm against the limit of {c['limit']*1000:g} mm, and a highest strength ratio of {worst['ratio']:.2f}. The deflection limit governs. A pod weighs {d['pod']/1000:.2f} t in operation.

The result holds for gravity load only. The items in section 4.11 could change the section sizes, the lateral case most of all, and the design should not be treated as final until they are closed.

### 4.11 Not covered by this check

1. **Lateral load.** The pair of trusses is only {st.TRUSS_SPACING:.2f} m wide and cantilevers {st.SPAN:.2f} m sideways as well as downwards. Earthquake load and the starting and stopping of a level act sideways on it. The site and its seismic design category are not yet fixed. This case is likely to govern the chords and the plan bracing.
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
- The store is filled from the top level down. A pod is lifted up a lane at the ground entry by the hoist under the crown. While it is lifted, every level that is already full closes up from {360/cfg.BAYS:g}° to {cfg.STORE['packed_pitch_degrees']:g}° between pods to open the lane.

The shaft is a round tube of {st.SHAFT_D*1000:.0f} mm outside diameter, rolled from plate, {st.SHAFT_TOP:.2f} m from the top of the foundation to the connector. Its wall thickness is the result of this check.

### 5.2 Dead load from the pods

| Quantity | Value | Basis |
| --- | ---: | --- |
| Weight of one pod, W | {kn(c['weight'])} kN ({c['pod_t']:.2f} t) | section 4.8 |
| Centre of gravity from the root | {d['centre']:.2f} m | |
| Centre of gravity from the shaft axis | {c['arm']:.2f} m | root radius {st.ROOT:.2f} m |
| Moment of one pod at its root | {kn(c['moment_root'],0)} kN·m | |
| Moment of one pod about the shaft axis, M<sub>pod</sub> | **{kn(c['moment_axis'],0)} kN·m** | |
| Weight of one level, {cfg.BAYS} pods | {kn(c['level_weight'],0)} kN ({cfg.BAYS*c['pod_t']:.1f} t) | |
| Weight of {cfg.TOTAL} pods | **{kn(c['store_weight'],0)} kN ({cfg.TOTAL*c['pod_t']:,.0f} t)** | |
| Hub, bearing and access floor | {hub*st.G:.0f} kN a level | allowance |
| Shaft and the services inside it | {kn(ch['line']*st.SHAFT_TOP,0)} kN | {sec['kg_m']:,.0f} kg/m of steel and {S['services_kg_per_m']:g} kg/m of services |

All values are unfactored.

### 5.3 Out-of-balance moment

A complete level stored at {360/cfg.BAYS:g}° is balanced and puts no moment on the shaft. Moment arises while the store is being filled, and again whenever a pod is exchanged in service, because the levels above the working level bunch to open the lane.

| State | Moment on the shaft | In terms of M<sub>pod</sub> |
| --- | ---: | ---: |
| One complete level, stored at {360/cfg.BAYS:g}° | 0 | 0 |
| One complete level, bunched at {cfg.STORE['packed_pitch_degrees']:g}° | {kn(u['bunched'],0)} kN·m | {u['bunched']/c['moment_axis']:.2f} |
| One level part filled, worst number of pods | {kn(u['partial_max'],0)} kN·m | {u['partial_max']/c['moment_axis']:.2f} |
| **Worst state in the filling sequence, total** | **{kn(u['base'],0)} kN·m** | **{u['base']/c['moment_axis']:.2f}** |
| Every level half filled on the same side, total | {kn(u['unrestricted'],0)} kN·m | {u['unrestricted']/c['moment_axis']:.1f} |

The worst state in the sequence has {u['full']} levels full and bunched and {u['placed']} pods on the level being filled. The moments of the bunched levels all point away from the lifting lane, so they add up the height of the shaft. Figure 2 shows this state. An exchange of a pod on the lowest level in service produces nearly the same state.

The last row is not part of the planned sequence. It is the moment that would arise if the fill order were not controlled.

![Plan of the worst out-of-balance state](figures/shaft_unbalance.svg)

### 5.4 Design criteria

| No. | Criterion | Limit | Basis |
| ---: | --- | --- | --- |
| 1 | Movement of a pod tip caused by the shaft | {sh['limit']*1000:g} mm | section 3.7. Shortening under the full store plus lean in the worst state of the filling sequence. |
| 2 | Strength under axial load and bending | interaction ≤ 1.0 in all three loading states | AISC 360-22 Sections E3, F8 and H1 |
| 3 | Wall slenderness | D/t ≤ 0.11 E/F<sub>y</sub> = {.11*e_fy:.1f} | AISC 360-22 Table B4.1a, case 9. No slender wall in compression. |
| 4 | Member slenderness | L<sub>c</sub>/r ≤ {T['max_slenderness']} | AISC 360-22 Section E2, user note |

Strength is checked for the uncontrolled fill as well as for the planned sequence. This is a decision made in this report so that a mistake in the fill order cannot overload the shaft. It costs nothing, because criterion 1 governs. The movement limit is checked for the planned sequence only.

The thinnest plate in the list in the design file that meets all four is chosen.

### 5.5 Analysis

The shaft is analysed as a beam, fixed at the foundation and held in position at the connector, {st.SHAFT_TOP:.2f} m above. The out-of-balance moment of each level is applied as a couple at the height of its hub. Couples are resolved onto the direction of their resultant. The weights of the pods, hubs, shaft and services give the axial force.

- **Shortening.** The drop of a hub is the shortening of the shaft below it under the weight of all {cfg.TOTAL} pods. The self-weight of the shaft and the hubs is left out, because it is in place before the hubs are set to level.
- **Lean.** The slope of the shaft at a hub tilts the pods of that level. The tip of a pod moves by the slope times the tip radius of {st.TIP_R:.2f} m. The largest slope at any hub is used.
- **Second-order effects.** Moments are multiplied by B<sub>1</sub> = 1/(1 − P<sub>u</sub>/P<sub>e1</sub>), with P<sub>e1</sub> = π²EI/L² and C<sub>m</sub> = 1.0, as AISC 360-22 Appendix 8 allows for a member held against sidesway.
- **Effective length.** K = {S['effective_length_factor']:g}, the value recommended for a column fixed at one end and held in position at the other.

![Elevation of the shaft with its loads and bending moment](figures/shaft.svg)

### 5.6 Selection of the wall thickness

| Wall, in (mm) | D/t | Mass, kg/m | Shortening, mm | Tip movement from lean, mm | Total, mm | Strength ratio | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{wall_rows}

**Selected: {st.SHAFT_D*1000:.0f} mm outside diameter × {st.inches(sec['wall_in'])} in ({sec['wall']*1000:.1f} mm) wall.** The movement limit governs. Strength would be met by the thinnest plate in the list.

| Property of the selected tube | Value |
| --- | ---: |
| Area | {sec['area']*1e6:,.0f} mm² |
| Second moment of area | {sec['i']*1e12/1e9:,.1f} × 10⁹ mm⁴ |
| Flexural stiffness, EI | {ch['ei']/1e9:.2f} GN·m² |
| Radius of gyration | {sec['r']*1000:.0f} mm |
| Mass | {sec['kg_m']:,.0f} kg/m, {ch['mass']/1000:.1f} t in all |
| D/t | {sec['ratio']:.1f}, {'compact' if ch['compact'] else 'noncompact'} in flexure (limit 0.07 E/F<sub>y</sub> = {.07*e_fy:.1f}) |

### 5.7 Movement of the pod tips

| Quantity | Value |
| --- | ---: |
| Shortening at the top hub under the full store | {mv['shortening']*1000:.2f} mm |
| Largest slope of the shaft at a hub, worst state of the filling sequence | {mv['lean']*1000:.3f} mrad |
| Tip movement from that slope | {mv['lean_drop']*1000:.2f} mm |
| **Total** | **{mv['total']*1000:.2f} mm** |
| Limit | {sh['limit']*1000:.2f} mm |
| **Result** | **{'Satisfied' if mv['total']<=sh['limit'] else 'Not satisfied'}**, {mv['total']/sh['limit']*100:.0f}% of the limit |

The two parts are added although they do not peak in exactly the same state, which is on the safe side. The shortening builds up from the bottom of the shaft, so it is largest at the top level, which is also the first to be filled:

| Level | Hub height, m | Drop of the hub under the full store, mm |
| ---: | ---: | ---: |
{level_rows}

### 5.8 Strength

| Loading state | Pods | Axial at the base, kN | P<sub>u</sub>, kN | Largest moment, kN·m | B<sub>1</sub> | M<sub>u</sub>, kN·m | P<sub>u</sub>/φP<sub>n</sub> | M<sub>u</sub>/φM<sub>n</sub> | Interaction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{case_rows}

| Design strength of the selected tube | Value | Basis |
| --- | ---: | --- |
| Compression, φ<sub>c</sub>P<sub>n</sub> | {kn(ch['pc'],0)} kN | Section E3, L<sub>c</sub>/r = {ch['slender']:.0f}, F<sub>cr</sub> = {ch['fcr']/1e6:.0f} MPa |
| Flexure, φ<sub>b</sub>M<sub>n</sub> | {kn(ch['mc'],0)} kN·m | Section F8, {'plastic moment' if ch['compact'] else 'noncompact wall'} |
| Shear, φ<sub>v</sub>V<sub>n</sub> | {kn(ch['vc'],0)} kN | Section G5, yielding |

Axial force and the largest moment are combined although they occur at different heights. The interaction is by Section H1.1. The largest shear is {kn(unc['vu'],0)} kN, which is {unc['shear']*100:.0f}% of the design shear strength.

Reactions for the checks that follow:

| Loading state | Vertical at the base, kN | Moment at the base, kN·m | Sideways force at the top and at the base, kN | Factored vertical, kN | Factored base moment, kN·m | Factored sideways force, kN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{reaction_rows}

The sideways force at the base is equal and opposite to the force at the top. The base moment with the top held is {abs(seq['result']['base'])/abs(free_cases['sequence']['result']['base'])*100:.0f}% of what it would be with the top free in the worst state of the sequence, {kn(abs(free_cases['sequence']['result']['base']),0)} kN·m. The base is still to be a heavy fixed connection: section 5.10 gives the case in which it has to work alone.

### 5.9 Stiffness of the top restraint

The results above assume that the top of the shaft does not move sideways. The support rig, its connector and the wall mounts will have some give. The table shows the effect in the worst state of the filling sequence.

| Stiffness of the restraint, kN/mm | Force at the top, kN | Sideways movement of the top, mm | Tip movement from lean, mm | Total with shortening, mm | Within {sh['limit']*1000:g} mm |
| ---: | ---: | ---: | ---: | ---: | --- |
{spring_rows}
| Rigid | {kn(abs(seq['result']['reaction']),0)} | 0.0 | {mv['lean_drop']*1000:.2f} | {mv['total']*1000:.2f} | Yes |

{f"**The restraint needs a stiffness of at least {sh['needed']/1e6:.0f} kN/mm** at the top of the shaft for the movement limit to be met with the selected wall. This is a design requirement for checks 7, 8 and 9. A moderately soft restraint gives slightly less lean than a rigid one, because the slope of the shaft changes sign up its height and the two ends balance better." if sh['needed'] else "The movement limit is met at every stiffness in the table."}

### 5.10 The shaft before the support rig is in place

In the present programme the pods are loaded on days {logistics.span('pods')[0]} to {logistics.span('pods')[1]} and the power levels, with the support rig, are lifted in on days {logistics.span('power')[0]} to {logistics.span('power')[1]}. The worst out-of-balance state occurs during pod loading, so in the present programme it would occur with the top of the shaft free.

| Selected tube, top free, worst state of the filling sequence | Value |
| --- | ---: |
| Moment at the base | {kn(abs(free_cases['sequence']['result']['base']),0)} kN·m |
| Sideways movement of the top of the shaft | {abs(free_cases['sequence']['result']['top'])*1000:.0f} mm |
| Tip movement from lean | **{free['movement']['lean_drop']*1000:.0f} mm** |
| Strength interaction, planned sequence | {free_cases['sequence']['ratio']:.2f} |
| Strength interaction, uncontrolled fill | {free_cases['uncontrolled']['ratio']:.2f} |

The shaft would not collapse, but the pods would be {free['movement']['lean_drop']*1000:.0f} mm out of level at their tips and the top of the shaft would be {abs(free_cases['sequence']['result']['top'])*1000:.0f} mm off the axis. An uncontrolled fill would use {'all' if free_cases['uncontrolled']['ratio']>=.995 else f"{free_cases['uncontrolled']['ratio']*100:.0f}%"} of the strength of the tube.

**Requirement: the top of the shaft is to be held before the first pod is hung.** Either the steel of the support rig is set on its wall mounts and connected to the shaft straight after the cage is lifted in, and the generator sets are landed on it later, or the shaft is braced to the wall by temporary works until the rig arrives. The programme and the animation do not yet show either. This is open item 1.

### 5.11 Verification

| Check | Analysis | Independent value | Agreement |
| --- | ---: | ---: | --- |
| Top reaction for a single couple M at height a, against 3Ma(2L − a)/(2L³) | numerical integration | closed form | within 0.1%, checked at every build |
| Base moment against the sum of the couples less the top reaction times L, each loading state | {kn(abs(seq['result']['base']),1)} kN·m | {kn(abs(sum(m for _, m in seq['couples'])-seq['result']['reaction']*st.SHAFT_TOP),1)} kN·m | equal |
| Sideways movement of the held top | {abs(seq['result']['top'])*1e6:.3f} µm | 0 | equal |

### 5.12 Conclusion

A {st.SHAFT_D*1000:.0f} mm tube with a {st.inches(sec['wall_in'])} in ({sec['wall']*1000:.1f} mm) wall of A572 Grade 50 plate, fixed at its base and held at its top, carries the {cfg.TOTAL} pods with a highest strength interaction of {ch['ratio']:.2f}. The pod tips move {mv['total']*1000:.1f} mm against the limit of {sh['limit']*1000:g} mm, and this governs the wall. The shaft weighs {ch['mass']/1000:.1f} t.

The result depends on the top restraint. It needs a stiffness of at least {sh['needed']/1e6 if sh['needed'] else 0:.0f} kN/mm, and it has to be in place before the first pod is hung.

### 5.13 Not covered by this check

1. **Lateral load.** Earthquake load on {cfg.TOTAL*c['pod_t']:,.0f} t of pods is likely to govern the shaft, its base, the connector, the rig and the mounts. It waits for the site.
2. **Local loads at the hubs.** Each hub puts {kn(c['level_weight']+hub*1000*st.G,0)} kN of weight and the pull and thrust of eight pod roots into the wall of the tube. Ring stiffeners or thicker cans at the hubs are to be designed with the hub under check 6.
3. **Openings.** Power and data pass down the inside of the shaft and have to come out at every level. The openings reduce the section and are not yet sized.
4. **Base connection.** Anchor rods, base plate and the foundation under them are part of check 4.
5. **Plumb.** A shaft that is out of plumb tilts every pod. One part in a thousand moves a pod tip {st.TIP_R:.1f} mm. The hubs will have to be set level independently of the shaft, or the erection tolerance set to suit.
6. **Torsion.** The drive of a level reacts on the shaft. The torque is small (section 6.2) and is not checked.
7. **Temperature.** The steel shaft and the concrete wall may warm by different amounts. The effect on the tip couplings is not checked.
8. **Field splices** and the welding of the seams.

## 6. Check 6: root connection and level drive, design loads

The connection and the drive are not designed in this revision. These are the loads from the pods as now designed, unfactored. The shaft is fixed and each level turns on it.

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

## 7. Checks 7, 8 and 9: support rig, shaft connector and wall mounts, design loads

These three checks were added in revision B. Holding the top of the shaft makes the rig, its connector and its mounts part of the structure that carries the pods. They are not designed in this revision. This section describes them as modelled and gives their loads.

### 7.1 Description

- **Support rig (check 7).** The steel deck under the diesel generator level: girders under the sets and a ring beam inside the wall, {cfg.POWER['floor_structure_m']:g} m deep, at {cfg.CROWN:.2f} m to {cfg.CROWN+cfg.POWER['floor_structure_m']:.2f} m above the foundation.
- **Shaft connector (check 8).** A collar round the top of the shaft with {st.RIG['arms']} arms out to the ring beam, in the depth of the rig. The shaft runs up into the collar and can slide in it, so the connector passes sideways force and nothing else.
- **Wall mounts (check 9).** {rig['mounts']} steel plates, {st.RIG['mount_plate_m'][0]:g} m × {st.RIG['mount_plate_m'][1]:g} m, cast flush into the bore face of the inner wall with studs into the concrete, evenly spaced round the ring beam and clear of the access wedge. They are set in the forms of the wall lift that contains them. They have to be flush for the cage to pass, so the rig carries a shoe at each mount that is welded to the plate once the rig is down.

### 7.2 Loads from the shaft

| Loading state | Sideways force at the top of the shaft, kN | Factored, kN | Largest force on one mount, kN |
| --- | ---: | ---: | ---: |
{rig_rows}

The direction of the force changes as the levels turn during a lift, so every mount is taken to see the largest share. The force on one mount assumes that the ring beam spreads the force round all {rig['mounts']} mounts as a cosine distribution, which gives 2/n of the total on the most heavily loaded mount. There are no mounts in the access wedge, so the true share is somewhat higher and is to be worked out under check 9.

The inner wall carries these forces in addition to the pressure of the store behind it. That is to be included in check 3.

### 7.3 Gravity loads on the rig

| Item | Mass, t | Basis |
| --- | ---: | --- |
| Diesel generator sets | {cfg.PROJECT['diesel']['sets']*cfg.PROJECT['diesel']['set_weight_t']:.1f} | {cfg.PROJECT['diesel']['sets']} × {cfg.PROJECT['diesel']['set_weight_t']:g} t |
| Day tanks, full | {cfg.PROJECT['diesel']['day_tanks']*rig['tank_t']:.1f} | fuel only |
| Deck steel | {rig['deck_t']:g} | allowance |
| **Diesel generator level** | **{rig['diesel_t']:.0f}** | {kn(rig['vertical_mount'],0)} kN on each mount if shared equally |
| Turbine level | {rig['turbine_t']:.0f} | {cfg.POWER['modules']} × {cfg.POWER['set_weight_t']:g} t and {rig['deck_t']:g} t of deck steel |
| Both levels | {rig['diesel_t']+rig['turbine_t']:.0f} | {kn(rig['vertical_mount_both'],0)} kN on each mount if the turbine level also bears on the rig |

The weight of the rig and its machines does not come onto the shaft.

### 7.4 Requirements from check 1

1. Sideways stiffness at the top of the shaft of at least {sh['needed']/1e6 if sh['needed'] else 0:.0f} kN/mm, through the connector, the rig and the mounts together.
2. The restraint in place before the first pod is hung (section 5.10).
3. No vertical load from the rig onto the shaft, and freedom for the shaft to shorten by {mv['shortening']*1000:.0f} mm or more inside the collar.

## 8. Open items

| No. | Item | Affects | Needed from |
| ---: | --- | --- | --- |
| 1 | The top of the shaft must be held before the pods are loaded: set the rig steel early, or brace the shaft temporarily | checks 1, 7, 8 and 9, the programme and the animation | project |
| 2 | Site and seismic design category, for the lateral case | all structural checks | project |
| 3 | Weight of a rack in operation, and of the CDU, pump and coolant | checks 1, 2, 4 and 6 | equipment supplier |
| 4 | Whether the {c['limit']*1000:g} mm limit is meant for the truss and the shaft separately, as applied here, or for the two together. The tolerance of the wall coupling decides it. | checks 1, 2 and 6 | project and coupling supplier |
| 5 | Does the turbine level bear on the support rig or on mounts of its own? | checks 3, 7 and 9 | project |
| 6 | Weight of the hub, bearing and access floor at each level | checks 1 and 6 | check 6 |
| 7 | Comparison of section properties with the AISC Manual | check 2 | checker |

## Appendix A: member forces in the pod truss

One side truss. Forces are unfactored in the docked and hoisted columns, tension positive. Factored values use the combinations in section 3.6. Panels are numbered from 1 at the root. For a vertical the number is its panel point, from 0 at the root.

{members_table(d)}

## Appendix B: section properties

Hollow sections, calculated as described in section 4.7.

| Section | Depth × width, mm | Nominal wall, mm | Design wall, mm | Area, mm² (in²) | r<sub>x</sub>, mm | r<sub>y</sub>, mm | Mass, kg/m (lb/ft) | Wall slenderness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{section_row(d['chord'])}
{section_row(d['web'])}
"""


def outputs():
    return {FILE: markdown(), FIGURES / "pod_truss.svg": truss_figure(), FIGURES / "shaft_unbalance.svg": balance_figure(),
            FIGURES / "shaft.svg": shaft_figure()}


def write():
    FIGURES.mkdir(exist_ok=True)
    for path, text in outputs().items():
        path.write_text(text, encoding="utf-8", newline="\n")
    return FILE


def current():
    return not differences()


def differences():
    """The first line that differs in each generated file that no longer matches the design file."""
    found = []
    for path, text in outputs().items():
        old = path.read_text(encoding="utf-8") if path.is_file() else ""
        if old == text: continue
        pairs = zip(old.split("\n") + [""] * 99999, text.split("\n"))
        line, (was, now) = next(((n, pair) for n, pair in enumerate(pairs, 1) if pair[0] != pair[1]), (0, ("", "")))
        found.append(f"{path.name} line {line}\n  committed: {was[:300]}\n  generated: {now[:300]}")
    return found
