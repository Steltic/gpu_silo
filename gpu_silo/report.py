"""Writes the structural design report and its figures from design/project.json.

The report is generated so that every number in it comes from the design file and the checks
in structure.py. Edit the inputs or this module, then run `python -m gpu_silo calcs`.
"""
import math
from pathlib import Path

from . import calcs, design_closeout
from . import design as cfg
from . import connection as cn
from . import foundation as fd
from . import logistics
from . import reinforcement as rf
from . import structure as st
from . import thermal as th
from . import walls

FOLDER = Path(__file__).resolve().parents[1] / "design"
FILE = FOLDER / "report.md"
FIGURES = FOLDER / "figures"
INK, MUTED, TENSION, COMPRESSION, PAPER = "#22303a", "#6b7780", "#1f6fa8", "#b4532a", "#ffffff"
KIP = 4448.2216


def kn(value, digits=1):
    return f"{value/1000:,.{digits}f}"


def signed(value):
    """A force in kN with its sign. A force that rounds to zero carries none, so the text does not depend on rounding noise."""
    return "0.0" if abs(value) < 50 else f"{value/1000:+.1f}"


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


def wall_figure():
    """Half section through the two walls of check 3 with carbon steel bars, with the walls as first drawn dashed."""
    c = walls.C
    inner = c["inner"]
    sx, sy, x0, base = 62., 12.2, 150., 482.
    X = lambda r: x0 + (r - walls.R_BORE) * sx
    Y = lambda z: base - z * sy
    out = [f'<text x="20" y="26" font-size="15" fill="{INK}" font-weight="bold">Figure 4. Half section through the walls of check 3, with carbon steel bars</text>',
           f'<text x="20" y="45" fill="{MUTED}">Horizontal scale five times the vertical. The walls as first drawn, {c["present"]["outer"]*1000:.0f} mm, are dashed.</text>',
           f'<text x="20" y="61" fill="{MUTED}">Hoop tension in kN/m at the lower edge of each lift, unfactored.</text>']
    top = Y(walls.HEIGHT)
    liquid = Y(walls.LIQUID)
    # Store
    points = [f"{X(walls.R_BORE+inner['t']):.1f},{base}"]
    for lift in c["lifts"]:
        points += [f"{X(lift['radius']):.1f},{Y(lift['z0']):.1f}", f"{X(lift['radius']):.1f},{max(liquid, Y(lift['z1'])):.1f}"]
    points.append(f"{X(walls.R_BORE+inner['t']):.1f},{liquid:.1f}")
    out.append(f'<polygon points="{" ".join(points)}" fill="#cfe6ee"/>')
    out.append(f'<rect x="{X(walls.R_BORE):.1f}" y="{top:.1f}" width="{inner["t"]*sx:.1f}" height="{base-top:.1f}" fill="#b9bdbd" stroke="{INK}" stroke-width="1"/>')
    for lift in c["lifts"]:
        out.append(f'<rect x="{X(lift["radius"]):.1f}" y="{Y(lift["z1"]):.1f}" width="{lift["t"]*sx:.1f}" height="{walls.LIFT*sy:.1f}" fill="#b9bdbd" stroke="{INK}" stroke-width="1"/>')
        bars = lift["bars"]
        out.append(f'<text x="{X(walls.R_OUT)+12:.1f}" y="{Y(lift["z0"]+walls.LIFT/2)+4:.1f}" fill="{INK}">{lift["t"]*1000:.0f} mm, {bars["layers"]} layers {bars["bar"]["name"]} at {bars["spacing"]*1000:.0f}</text>')
        out.append(f'<text x="{X(walls.R_OUT)+250:.1f}" y="{Y(lift["z0"]+walls.LIFT/2)+4:.1f}" fill="{TENSION}" text-anchor="end">{lift["tension"]/1000:,.0f}</text>')
        out.append(f'<text x="{X(walls.R_BORE)-10:.1f}" y="{Y(lift["z0"]+walls.LIFT/2)+4:.1f}" fill="{MUTED}" text-anchor="end">lift {lift["lift"]}</text>')
    out.append(f'<text x="{X(walls.R_OUT)+250:.1f}" y="{top-8:.1f}" fill="{TENSION}" text-anchor="end">hoop tension</text>')
    out.append(f'<text x="{X(walls.R_OUT)+12:.1f}" y="{top-8:.1f}" fill="{INK}">outer wall, hoop steel</text>')
    for r in (walls.R_BORE + c["present"]["inner"], walls.R_OUT - c["present"]["outer"]):
        out.append(f'<line x1="{X(r):.1f}" y1="{top:.1f}" x2="{X(r):.1f}" y2="{base}" stroke="{COMPRESSION}" stroke-width="1.2" stroke-dasharray="5 4"/>')
    out.append(f'<line x1="{X(walls.R_BORE+inner["t"]):.1f}" y1="{liquid:.1f}" x2="{X(c["lifts"][-1]["radius"]):.1f}" y2="{liquid:.1f}" stroke="{TENSION}" stroke-width="1.2"/>')
    middle = (X(walls.R_BORE + inner["t"]) + X(c["lifts"][0]["radius"])) / 2
    out.append(f'<text x="{middle:.1f}" y="{liquid+16:.1f}" fill="{TENSION}" text-anchor="middle">liquid to {walls.LIQUID:.2f} m</text>')
    out.append(f'<text x="{middle:.1f}" y="{Y(16):.1f}" fill="{INK}" text-anchor="middle">store</text>')
    out.append(f'<text x="{middle:.1f}" y="{base-10:.1f}" fill="{INK}" text-anchor="middle">{c["gap_base"]:.2f} m, {walls.pressure(0)/1000:.0f} kPa</text>')
    out.append(f'<text x="{middle:.1f}" y="{liquid+34:.1f}" fill="{INK}" text-anchor="middle">{c["gap_top"]:.2f} m</text>')
    out.append(f'<text x="{X(walls.R_BORE)+inner["t"]*sx/2:.1f}" y="{base+18:.1f}" fill="{INK}" text-anchor="middle">inner wall, {inner["t"]*1000:.0f} mm</text>')
    out.append(f'<text x="{X(walls.R_BORE)-10:.1f}" y="{top-8:.1f}" fill="{MUTED}" text-anchor="end">bore side</text>')
    out.append(f'<line x1="{X(walls.R_BORE)-70:.1f}" y1="{base}" x2="{X(walls.R_OUT)+260:.1f}" y2="{base}" stroke="{INK}" stroke-width="2"/>')
    return svg(760, 520, out)


def members_table(d):
    lines = ["| Member | Panel | Length, m | Docked, kN | Hoisted, kN | Factored tension, kN | Factored compression, kN | KL/r | Ratio |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for kind in ("Top chord", "Bottom chord", "Diagonal", "Vertical"):
        for row in d["rows"]:
            if row["kind"] != kind: continue
            lines.append(f"| {kind} | {row['panel']} | {row['length']:.3f} | {signed(row['docked'])} | {signed(row['hoisted'])} | "
                         f"{kn(row['tension'])} | {kn(row['compression'])} | {row['slenderness']:.0f} | {row['ratio']:.2f} |")
    return "\n".join(lines)


def section_row(s):
    inch = st.INCH
    return (f"| {s['name']} | {s['h']*1000:.0f} × {s['b']*1000:.0f} | {s['t_nominal']*1000:.2f} | {s['t']*1000:.2f} | {s['area']*1e6:,.0f} ({s['area']/inch**2:.2f}) | "
            f"{s['rx']*1000:.1f} | {s['ry']*1000:.1f} | {s['kg_m']:.1f} ({s['kg_m']/1.48816:.2f}) | {s['wall']:.1f} |")


def thermal_figure():
    """Heat the coolers reject against the outside air temperature, for a layered and a mixed store."""
    c = th.C
    x0, x1, y0, y1 = 80., 700., 372., 86.
    lo, hi, top = -20., 45., 70e6
    X = lambda t: x0 + (t - lo) / (hi - lo) * (x1 - x0)
    Y = lambda q: y0 - q / top * (y0 - y1)
    out = [f'<text x="20" y="26" font-size="15" fill="{INK}" font-weight="bold">Figure 5. Heat the dry coolers reject against the outside air temperature</text>',
           f'<text x="20" y="45" fill="{MUTED}">Supply to the pods held at {th.COLD:.0f} °C or below. A layered store lets the coolers draw the {th.HOT:.0f} °C return. A mixed store gives them {th.COLD:.0f} °C.</text>']
    for q in range(0, 71, 10):
        out.append(f'<line x1="{x0}" y1="{Y(q*1e6):.1f}" x2="{x1}" y2="{Y(q*1e6):.1f}" stroke="#e3e6e8" stroke-width="1"/>')
        out.append(f'<text x="{x0-8}" y="{Y(q*1e6)+4:.1f}" fill="{MUTED}" text-anchor="end">{q}</text>')
    for t in range(-20, 46, 5):
        out.append(f'<line x1="{X(t):.1f}" y1="{y0}" x2="{X(t):.1f}" y2="{y0+5}" stroke="{INK}" stroke-width="1"/>')
        out.append(f'<text x="{X(t):.1f}" y="{y0+19}" fill="{MUTED}" text-anchor="middle">{t}</text>')
    out.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{INK}" stroke-width="1.5"/>')
    out.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{INK}" stroke-width="1.5"/>')
    out.append(f'<text x="{(x0+x1)/2:.1f}" y="{y0+38}" fill="{INK}" text-anchor="middle">outside air, °C</text>')
    out.append(f'<text x="24" y="{(y0+y1)/2:.1f}" fill="{INK}" text-anchor="middle" transform="rotate(-90 24 {(y0+y1)/2:.1f})">heat rejected, MW</text>')
    steps = [lo + i * .25 for i in range(int((hi - lo) / .25) + 1)]
    each = th.cooler(1., 0.)[0]
    curves = [(lambda t: th.stratified_capacity(t), TENSION, 2.6, ""),
              (lambda t: th.stratified_capacity(t, th.DUTY), TENSION, 1.4, "5 3"),
              (lambda t: min(th.INSTALLED * th.Q_RATED, max(0., th.INSTALLED * each * (th.COLD - t))), COMPRESSION, 2.6, "")]
    for f, colour, width, dash in curves:
        points = " ".join(f"{X(t):.1f},{Y(f(t)):.1f}" for t in steps)
        out.append(f'<polyline points="{points}" fill="none" stroke="{colour}" stroke-width="{width}"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')
    out.append(f'<line x1="{x0}" y1="{Y(th.LOAD):.1f}" x2="{x1}" y2="{Y(th.LOAD):.1f}" stroke="{INK}" stroke-width="1.4" stroke-dasharray="7 4"/>')
    out.append(f'<text x="{x0+8}" y="{Y(th.LOAD)+16:.1f}" fill="{INK}">heat to reject, {th.LOAD/1e6:.2f} MW</text>')
    for key, label, anchor, shift in (("summer_design_c", "summer design", "end", -4), ("extreme_hot_c", "extreme", "start", 4)):
        t = th.AMBIENT[key]
        out.append(f'<line x1="{X(t):.1f}" y1="{y0}" x2="{X(t):.1f}" y2="{y1-10}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="2 4"/>')
        out.append(f'<text x="{X(t)+shift:.1f}" y="{y1-2}" fill="{MUTED}" text-anchor="{anchor}">{label}</text>')
    mixed, layered = c["limit"][th.INSTALLED, True], c["limit"][th.INSTALLED, False]
    for t, colour in ((mixed, COMPRESSION), (layered, TENSION)):
        out.append(f'<circle cx="{X(t):.1f}" cy="{Y(th.LOAD):.1f}" r="4.5" fill="{colour}"/>')
    out.append(f'<text x="{X(mixed)-10:.1f}" y="{Y(th.LOAD)+18:.1f}" fill="{COMPRESSION}" text-anchor="end">{mixed:.1f} °C</text>')
    out.append(f'<text x="{X(layered)+9:.1f}" y="{Y(th.LOAD)-9:.1f}" fill="{TENSION}">{layered:.1f} °C</text>')
    out.append(f'<text x="{X(8):.1f}" y="{Y(22e6):.1f}" fill="{COMPRESSION}" text-anchor="end">mixed store,</text>')
    out.append(f'<text x="{X(8):.1f}" y="{Y(22e6)+15:.1f}" fill="{COMPRESSION}" text-anchor="end">{th.INSTALLED} coolers</text>')
    out.append(f'<text x="{X(-18):.1f}" y="{Y(60e6)-8:.1f}" fill="{TENSION}">layered store, {th.INSTALLED} coolers</text>')
    out.append(f'<text x="{X(-18):.1f}" y="{Y(th.DUTY*th.Q_RATED)-7:.1f}" fill="{TENSION}">layered store, {th.DUTY} coolers</text>')
    return svg(760, 420, out)


def options_figure():
    """Plan section through one metre of the lowest lift of the outer wall, for each reinforcement scheme."""
    schemes = list(rf.C["schemes"].values())
    scale, pitch, left, top = .17, 183., 22., 96.
    out = [f'<text x="20" y="26" font-size="15" fill="{INK}" font-weight="bold">Figure 6. One metre of the lowest lift of the outer wall, for each reinforcement option</text>',
           f'<text x="20" y="45" fill="{MUTED}">Plan section, to scale. The store and its liner are at the top of each piece of wall and the outside air at the bottom.</text>',
           f'<text x="20" y="61" fill="{MUTED}">Hoop bars are drawn as dots. Vertical bars are left out.</text>']
    deepest = max(s["lifts"][0]["t"] for s in schemes) * 1000 * scale
    for i, s in enumerate(schemes):
        l = s["lifts"][0]
        bars, x = l["bars"], left + i * pitch
        t = l["t"] * 1000 * scale
        chosen = s is rf.C["proposed"]
        out.append(f'<rect x="{x:.1f}" y="{top}" width="{1000*scale:.1f}" height="{t:.1f}" fill="#d9dcdc" stroke="{INK}" stroke-width="{2 if chosen else 1}"/>')
        out.append(f'<line x1="{x:.1f}" y1="{top-2}" x2="{x+1000*scale:.1f}" y2="{top-2}" stroke="#4f8f86" stroke-width="3"/>')
        d = bars["bar"]["d"] * 1000
        colour = INK if s["scheme"]["ductile"] else COMPRESSION
        for layer in range(bars["per_face"]):
            depth = (walls.COVER * 1000 + d / 2 + layer * (d + walls.W["layer_gap_mm"])) * scale
            for y in (top + depth, top + t - depth):
                position = bars["spacing"] * 500
                while position < 1000:
                    out.append(f'<circle cx="{x+position*scale:.1f}" cy="{y:.1f}" r="{max(2.2, d/2*scale):.1f}" fill="{colour}"/>')
                    position += bars["spacing"] * 1000
        y = top + deepest + 24
        lines = [(s["scheme"]["name"], INK, "bold"), (f"{l['t']*1000:.0f} mm wall", INK, "normal"),
                 (f"{bars['layers']} layers of {bars['bar']['name']} at {bars['spacing']*1000:.0f} mm", INK, "normal"),
                 (f"bar stress {l['stress']/1e6:.0f} MPa", MUTED, "normal"),
                 (f"crack {l['crack']*1000:.2f} mm", MUTED if l["crack"] <= rf.CRACK + 1e-9 else COMPRESSION, "normal"),
                 (f"radius grows {l['growth']*1000:.0f} mm", MUTED, "normal")]
        for n, (text, fill, weight) in enumerate(lines):
            out.append(f'<text x="{x:.1f}" y="{y+n*17:.1f}" fill="{fill}" font-weight="{weight}">{text}</text>')
    out.append(f'<text x="20" y="{top+deepest+24+6*17+8:.1f}" fill="{MUTED}">The liner is taken to bridge a crack of {rf.CRACK*1000:.2f} mm. Wider cracks are in orange. The option adopted has the heavy outline.</text>')
    return svg(760, top + deepest + 24 + 6 * 17 + 22, out)


def foundation_figure():
    """Settlement of the base slab along a radius, before and after the store is filled."""
    c = fd.C
    d = c["grounds"][fd.F["design_ground"]]
    x0, x1, y0, y1 = 70., 700., 150., 370.
    deepest = math.ceil(d["settle"]["most"] * 1000 / 5) * 5
    X = lambda r: x0 + r / fd.RADIUS * (x1 - x0)
    Y = lambda w: y0 + w * 1000 / deepest * (y1 - y0)
    out = [f'<text x="20" y="26" font-size="15" fill="{INK}" font-weight="bold">Figure 7. Settlement of the base slab along a radius, on {fd.F["design_ground"]}</text>',
           f'<text x="20" y="45" fill="{MUTED}">Slab {d["thickness"]:.2f} m thick. The centre of the silo is at the left. Settlement is drawn downwards, to a much larger scale than the slab.</text>']
    for name, (a, b), colour in (("store", fd.WET, "#cfe6ee"),):
        out.append(f'<rect x="{X(a):.1f}" y="{y0-34}" width="{X(b)-X(a):.1f}" height="34" fill="{colour}"/>')
        out.append(f'<text x="{(X(a)+X(b))/2:.1f}" y="{y0-14}" fill="{TENSION}" text-anchor="middle">liquid, {fd.L["liquid"][2]/1000:.0f} kPa</text>')
    for label, r, half in (("inner wall", fd.R_INNER, fd.T_IN / 2), ("outer wall", fd.R_OUTER, fd.T_OUT / 2), ("shaft", fd.R_SHAFT, .03)):
        out.append(f'<rect x="{X(r-half):.1f}" y="{y0-58}" width="{max(3, X(r+half)-X(r-half)):.1f}" height="58" fill="#b9bdbd" stroke="{INK}" stroke-width="1"/>')
        out.append(f'<text x="{X(r):.1f}" y="{y0-64}" fill="{INK}" text-anchor="middle">{label}</text>')
    out.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{INK}" stroke-width="1.5"/>')
    for mm in range(0, deepest + 1, 5):
        out.append(f'<line x1="{x0}" y1="{Y(mm/1000):.1f}" x2="{x1}" y2="{Y(mm/1000):.1f}" stroke="#e3e6e8" stroke-width="1"/>')
        out.append(f'<text x="{x0-8}" y="{Y(mm/1000)+4:.1f}" fill="{MUTED}" text-anchor="end">{mm}</text>')
    out.append(f'<text x="24" y="{(y0+y1)/2:.1f}" fill="{INK}" text-anchor="middle" transform="rotate(-90 24 {(y0+y1)/2:.1f})">settlement, mm</text>')
    for r in range(0, int(fd.RADIUS) + 1, 2):
        out.append(f'<text x="{X(r):.1f}" y="{y1+18}" fill="{MUTED}" text-anchor="middle">{r}</text>')
    out.append(f'<text x="{(x0+x1)/2:.1f}" y="{y1+36}" fill="{INK}" text-anchor="middle">radius, m</text>')
    for values, colour, dash, width in ((d["w_empty"], MUTED, "6 4", 1.6), (d["w"], TENSION, "", 2.6)):
        points = " ".join(f"{X(r):.1f},{Y(w):.1f}" for r, w in zip(fd.NODES[::4], values[::4]))
        out.append(f'<polyline points="{points}" fill="none" stroke="{colour}" stroke-width="{width}"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')
    out.append(f'<text x="{X(3.2):.1f}" y="{Y(fd.at(d["w_empty"], 3.2))-8:.1f}" fill="{MUTED}">store empty</text>')
    out.append(f'<text x="{X(9.6):.1f}" y="{Y(fd.at(d["w"], 9.6))+26:.1f}" fill="{TENSION}" text-anchor="end">store full</text>')
    s = d["settle"]
    out.append(f'<text x="{x0}" y="{y1+62}" fill="{INK}">Filling the store lowers the inner wall by {s["fill_inner"]*1000:.1f} mm and {moved(s["fill_shaft"])}. '
               f'Ground pressure {d["pressure"]["least"]/1000:.0f} to {d["pressure"]["most"]/1000:.0f} kPa.</text>')
    return svg(760, y1 + 78, out)


def root_figure():
    """Section through the hub of one level and the root of one truss."""
    c = cn.C
    scale, x0, base = 200., 110., 600.
    X = lambda r: x0 + r * scale
    Y = lambda z: base - z * scale
    depth, shaft_r, ring_r, drum_r, root = cn.DEPTH, st.SHAFT_D / 2, cn.R["hub_ring_radius_m"], cn.HUB["drum_diameter_m"] / 2, st.ROOT
    wall = st.C["shaft"]["chosen"]["section"]["wall"]
    arm = c["arm"]["depth"]
    out = [f'<text x="20" y="26" font-size="15" fill="{INK}" font-weight="bold">Figure 8. The hub of one level and the root of one truss</text>',
           f'<text x="20" y="45" fill="{MUTED}">Section on one side of the shaft, as designed in check 6. Forces are for one truss, unfactored.</text>']
    lo, hi = -.45, depth + .45
    out.append(f'<rect x="{X(shaft_r-wall):.1f}" y="{Y(hi):.1f}" width="{wall*scale:.1f}" height="{(hi-lo)*scale:.1f}" fill="#8fa3a1" stroke="{INK}" stroke-width="1"/>')
    out.append(f'<line x1="{X(0):.1f}" y1="{Y(hi):.1f}" x2="{X(0):.1f}" y2="{Y(lo):.1f}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="10 4 2 4"/>')
    out.append(f'<text x="{X(0)+6:.1f}" y="{Y(hi)+14:.1f}" fill="{MUTED}">axis</text>')
    out.append(f'<text x="{X(shaft_r-wall)-6:.1f}" y="{Y(depth*.62):.1f}" fill="{INK}" text-anchor="end">shaft</text>')
    # Collar on the shaft and the slewing ring on it.
    out.append(f'<rect x="{X(shaft_r):.1f}" y="{Y(-.20):.1f}" width="{(ring_r-shaft_r)*scale:.1f}" height="{.06*scale:.1f}" fill="#8fa3a1" stroke="{INK}" stroke-width="1"/>')
    out.append(f'<rect x="{X(drum_r-.09):.1f}" y="{Y(-.04):.1f}" width="{.16*scale:.1f}" height="{.10*scale:.1f}" fill="#d7b46a" stroke="{INK}" stroke-width="1"/>')
    out.append(f'<text x="{X(shaft_r-wall)-6:.1f}" y="{Y(-.17)+4:.1f}" fill="{INK}" text-anchor="end">collar on the shaft</text>')
    out.append(f'<text x="{X(shaft_r-wall)-6:.1f}" y="{Y(.01)+4:.1f}" fill="#8a6a1c" text-anchor="end">slewing ring with gear</text>')
    # Hub: two rings and the drum between them.
    for z in (0., depth):
        out.append(f'<rect x="{X(drum_r-.15):.1f}" y="{Y(z+.02):.1f}" width="{(ring_r-drum_r+.15)*scale:.1f}" height="{.04*scale:.1f}" fill="#5f7a78" stroke="{INK}" stroke-width="1"/>')
    out.append(f'<rect x="{X(drum_r)-2:.1f}" y="{Y(depth):.1f}" width="4" height="{depth*scale:.1f}" fill="#5f7a78"/>')
    out.append(f'<text x="{X(drum_r)+10:.1f}" y="{Y(depth*.62):.1f}" fill="{INK}">hub drum</text>')
    out.append(f'<circle cx="{X(shaft_r)+9:.1f}" cy="{Y(depth):.1f}" r="8" fill="#d7b46a" stroke="{INK}" stroke-width="1"/>')
    out.append(f'<text x="{X(shaft_r-wall)-6:.1f}" y="{Y(depth)+4:.1f}" fill="#8a6a1c" text-anchor="end">guide rollers on the shaft</text>')
    # Arms and the truss.
    for z, label in ((depth, "top arm"), (0., "bottom arm")):
        top = z + arm / 2 if z else z + arm / 2
        out.append(f'<rect x="{X(ring_r):.1f}" y="{Y(z+arm/2):.1f}" width="{(root-ring_r)*scale:.1f}" height="{arm*scale:.1f}" fill="#c7cdca" stroke="{INK}" stroke-width="1"/>')
        out.append(f'<text x="{X((ring_r+root)/2):.1f}" y="{Y(z-arm/2)+15:.1f}" fill="{INK}" text-anchor="middle">{label}, {c["arm"]["name"]}</text>')
    out.append(f'<circle cx="{X(root):.1f}" cy="{Y(depth):.1f}" r="{max(5, c["pin"]["d"]*scale/2):.1f}" fill="{COMPRESSION}" stroke="{INK}" stroke-width="1"/>')
    out.append(f'<rect x="{X(root)-3:.1f}" y="{Y(.09):.1f}" width="10" height="{.18*scale:.1f}" fill="{COMPRESSION}"/>')
    chord = .15
    for z in (depth, 0.):
        out.append(f'<rect x="{X(root)+8:.1f}" y="{Y(z+chord/2):.1f}" width="{.62*scale:.1f}" height="{chord*scale:.1f}" fill="#e2e6e3" stroke="{INK}" stroke-width="1"/>')
    out.append(f'<line x1="{X(root)+12:.1f}" y1="{Y(depth-chord/2):.1f}" x2="{X(root)+12:.1f}" y2="{Y(chord/2):.1f}" stroke="{INK}" stroke-width="5"/>')
    out.append(f'<line x1="{X(root)+12:.1f}" y1="{Y(depth-chord/2):.1f}" x2="{X(root+.60):.1f}" y2="{Y(chord/2+.55):.1f}" stroke="{INK}" stroke-width="3" stroke-dasharray="1 0"/>')
    out.append(f'<text x="{X(root+.16):.1f}" y="{Y(depth*.22):.1f}" fill="{INK}">pod truss</text>')
    out.append(f'<text x="{X(root)+16:.1f}" y="{Y(depth+chord)-20:.1f}" fill="{COMPRESSION}">{c["pin"]["d"]*1000:.0f} mm pin: pull {kn(c["pull"])} kN, weight {kn(c["weight"])} kN</text>')
    out.append(f'<text x="{X(root)+16:.1f}" y="{Y(-chord)+32:.1f}" fill="{COMPRESSION}">bearing block: thrust {kn(c["thrust"])} kN</text>')
    # Dimensions.
    out.append(f'<line x1="{X(root+.72):.1f}" y1="{Y(depth):.1f}" x2="{X(root+.72):.1f}" y2="{Y(0):.1f}" stroke="{MUTED}" stroke-width="1"/>')
    out.append(f'<text x="{X(root+.72)+6:.1f}" y="{Y(depth/2)+34:.1f}" fill="{MUTED}">{depth:.3f} m</text>')
    out.append(f'<line x1="{X(shaft_r):.1f}" y1="{Y(depth*.3):.1f}" x2="{X(root):.1f}" y2="{Y(depth*.3):.1f}" stroke="{MUTED}" stroke-width="1"/>')
    out.append(f'<text x="{X((shaft_r+root)/2)+26:.1f}" y="{Y(depth*.3)-6:.1f}" fill="{MUTED}" text-anchor="middle">{st.ACCESS:.2f} m access</text>')
    return svg(760, base + 120, out)


ANCHORS = {"4": "4-check-2-pod-truss", "5": "5-check-1-central-shaft",
           "6": "6-check-6-root-connection-and-level-drive-design-loads",
           "7": "7-checks-7-to-10-support-rig-shaft-connector-and-wall-mounts-design-loads",
           "8": "8-check-3-silo-walls", "9": "9-check-5-heat-balance-of-the-store",
           "11": "11-check-4-foundation", "12": "12-check-6-root-connection-hub-and-level-drive"}

def foundation_section():
    c = fd.C
    d, b, F = c["chosen"], c["base"], fd.F
    ok = lambda o: o["shear_ok"] and o["punch"] <= o["punch_strength"]
    sand, rock = list(c["grounds"])[0], list(c["grounds"])[-1]
    differ = lambda o: (o["settle"]["fill_inner"] - o["settle"]["fill_shaft"]) * 1000
    thin = c["options"][0]
    middle = list(c["grounds"])[1]
    wt = c["weights"]
    weight_rows = "\n".join(f"| {name} | {wt[key]/1e6:,.1f} |" for key, name in (
        ("liquid", "Liquid in the store"), ("walls", "The two walls"), ("slab", f"Base slab, {d['thickness']:.2f} m"), ("shaft", "Shaft, hubs and 64 pods"),
        ("coolers", "Coolers and their frames"), ("power", "The two power levels"), ("lid", "Lid"), ("cage", "Cage posts and decks"), ("floor", "Load on the floor of the bore")))
    ground_rows = "\n".join(
        f"| {'**' if name == F['design_ground'] else ''}{name.capitalize()}{'**' if name == F['design_ground'] else ''} | {fd.MODULUS[name]/1e6:,.0f} | {fd.GROUND[name]/1e6:.1f} | {c['grounds'][name]['thickness']:.2f} | {g['pressure']['least']/1e3:.0f} to {g['pressure']['most']/1e3:.0f} | "
        f"{g['settle']['shaft']*1000:.0f} | {g['settle']['inner']*1000:.0f} | {g['settle']['outer']*1000:.0f} | **{differ(g):.1f}** | {max(abs(v['moment']) for v in g['faces'].values())/1e3:,.0f} |"
        for name, g in c["as_drawn"].items())
    option_rows = "\n".join(
        f"| {'**' if o is d else ''}{o['thickness']:.2f}{'**' if o is d else ''} | {o['faces']['radial','top']['moment']/1e3:,.0f} | {o['faces']['radial','bottom']['moment']/1e3:,.0f} | {o['vu']/1e3:,.0f} | {o['plain']/1e3:,.0f} | {o['tied']/1e3:,.0f} | "
        f"{'Yes' if o['stirrups'] else 'No'} | {o['punch']/1e6:.1f} against {o['punch_strength']/1e6:.1f} | {(o['settle']['fill_inner']-o['settle']['fill_shaft'])*1000:.1f} | {'Adopted' if o is d else '' if ok(o) else 'Not strong enough'} |"
        for o in c["options"])
    face_rows = "\n".join(
        f"| {way.capitalize()}, {face} | {v['moment']/1e3:+,.0f} | {v['area']*1e6:,.0f} | {v['bars']['layers']} layer of {v['bars']['bar']['name']} at {v['bars']['spacing']*1000:.0f} mm |"
        for (way, face), v in d["faces"].items())
    case_rows = "\n".join(
        f"| {case['group']} | {case['name'].split(':')[0]} | {kn(case['axial'],0)} | {kn(case['moment'],0)} | {case['factor']:g} | {kn(case['tension'],0)} | {kn(case['line'],0)} |" for case in b["cases"])
    s = d["settle"]
    fill = (s["fill_inner"] - s["fill_shaft"]) * 1000
    return f"""## 11. Check 4: foundation

### 11.1 Arrangement and basis

The silo stands on a round base slab, {2*fd.RADIUS:.2f} m across, which is the outside of the wall and {cfg.PROJECT['logistics']['concrete']['slab_overhang_m']:g} m more all round. It is {c['drawn']:.2f} m thick, by decision of the project in revision I. The two walls are built into it and the shaft is anchored to its centre.

The site is not fixed and there is no ground investigation. The project has said to assume {F['design_ground']}. This check gives the loads that the ground has to carry, checks the slab on that ground and on two stiffer ones, and designs the anchorage of the shaft, which does not depend on the ground. Every number is calculated by [foundation.py](../gpu_silo/foundation.py).

| Assumption | Value | Note |
| --- | ---: | --- |
| Ground | springs under the slab, each acting alone (Winkler) | the usual first model. Real ground spreads load sideways, so the differences in settlement found here are on the high side. |
| Stiffness of the ground | modulus of {', '.join(f"{v:,} MPa for {n}" for n, v in F['ground_modulus_mpa'].items())} | **assumption.** Typical values for each kind of ground. |
| Spring under the slab | 4 E ÷ (π D (1 − ν²)), with ν = {F['ground_poisson']:g} | the spring that gives a stiff round slab of diameter D its settlement on an elastic ground. It falls as the slab gets wider, so values from a plate test cannot be used for a slab {2*fd.RADIUS:.0f} m across. |
| Concrete | f'<sub>c</sub> = {F['concrete_fc_mpa']} MPa | |
| Reinforcement | Grade 60, {F['cover_mm']} mm cover | ordinary bar. The floor of the store is under the liner. |
| Load factor | {F['load_factor']:g} on everything | ACI 318-19 for dead load and liquid |

### 11.2 Loads

| Load | MN |
| --- | ---: |
{weight_rows}
| **Total** | **{c['total']/1e6:,.1f}** |

Spread evenly over the {c['area']:,.0f} m² of the slab this is **{c['total']/c['area']/1e3:.0f} kPa**. Nearly half of it is the liquid, and four fifths of it comes down on the ring between the bore and the outside, so the pressure on the ground is not even.

The feet of the two walls also bend the slab, by {kn(fd.L['moments'][0][2],0)} kN·m/m at the outer wall and {kn(abs(fd.L['moments'][1][2]),0)} kN·m/m at the inner wall, and pull it apart across the floor of the store with {kn(d['tie'],0)} kN/m.

### 11.3 Analysis

The slab is a round plate on springs, loaded round the lines of the walls and the shaft and over the floor of the store. It is solved by finite elements along a radius, {F['mesh_m']*1000:.0f} mm long, each with the settlement and the slope at its two ends. The loads are the same all the way round, so one radius describes the slab. Two states are solved: the store empty, and the store full.

### 11.4 Pressure on the ground and settlement

The slab is {c['drawn']:.2f} m thick and the store is full. The ground assumed is in bold.

| Ground | Modulus, MPa | Spring, MN/m³ | Thinnest slab that is strong enough, m | Pressure on the ground, kPa | Settlement of the shaft, mm | Inner wall, mm | Outer wall, mm | Filling lowers the inner wall more than the shaft by, mm | Largest moment, kN·m/m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{ground_rows}

![Settlement of the base slab](figures/foundation.svg)

- **On {F['design_ground']} the silo settles about {d['settle']['outer']*1000:.0f} mm**, as the load goes on. On {middle} it is about {c['as_drawn'][middle]['settle']['outer']*1000:.0f} mm and on {rock} about {c['as_drawn'][rock]['settle']['outer']*1000:.0f} mm. Clay goes on settling for years afterwards, which is not in these figures.
- **The pressure on the ground is about {c['total']/c['area']/1e3:.0f} kPa on average and {d['pressure']['least']/1e3:.0f} to {d['pressure']['most']/1e3:.0f} kPa across the slab.** A slab this wide is unlikely to fail the ground in sand or gravel. In clay the strength of the ground has to be checked as well. In either, it is the settlement that decides whether the silo can stand on a slab or needs piles. This is the first question for the site, and is open item 18.
- **The {c['drawn']:g} m slab goes down nearly level.** The walls and the store are heavy and the bore is light, so a thin slab lets the rim go down more than the centre. At {c['drawn']:g} m the difference across the slab is {(d['settle']['most']-d['settle']['least'])*1000:.0f} mm.

### 11.5 What settlement does to the pod tips

The pods hang from the shaft at the centre of the slab. Their wall connections are in the inner wall. When the store is filled the inner wall goes down more than the shaft, so every wall sleeve drops against its pod tip. The programme loads the pods on days {logistics.BY_KEY['pods']['start']} to {logistics.BY_KEY['pods']['end']} and fills the store from day {logistics.BY_KEY['water']['start']}, so this happens after the pods are docked.

Revision H proposed making the wall connections after the fill. The project decided against anything that constrains the build, and chose in revision I to deal with it in the structure:

1. **A {c['drawn']:g} m slab.** It is stiff enough to take the walls and the shaft down nearly together. The fill lowers the wall **{differ(d):.1f} mm** against the shaft on {F['design_ground']}, where the {thin['thickness']:g} m slab first drawn gave {differ(thin):.1f} mm.
2. **A flexible section in each wall connection**, which takes this movement and the others between a pod and the wall (section 3.8).

Settlement that goes on after the fill, as the ground consolidates under a load that never comes off, is given an allowance of {cfg.PROJECT['structure']['wall_connection']['settlement_over_time_mm']:g} mm in the flexible section. It depends on the ground and is open item 19.

### 11.6 Thickness, bending and shear

| Thickness, m | Largest radial moment, top in tension, kN·m/m | Bottom in tension, kN·m/m | Factored shear at the walls, kN/m | Shear strength with no ties, kN/m | With ties, kN/m | Ties needed | Factored punching at the shaft against strength, MN | Fill settlement, wall against shaft, mm | |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
{option_rows}

Moments are unfactored. The table is for {F['design_ground']}. The shear is taken at the effective depth from the face of each wall, and the largest is on the {d['worst']['side']} of the {d['worst']['wall']}.

**The slab is {c['drawn']:.2f} m thick.** On {F['design_ground']} the thinnest slab that is strong enough is {c['grounds'][F['design_ground']]['thickness']:.2f} m. The extra thickness is there for stiffness, to cut the settlement of the walls against the shaft. Shear ties are still needed in a band each side of each wall: no thickness in the list does without them, because a deep slab with little reinforcement is given a low shear strength (ACI 318-19 Section 22.5.5).

A stiff slab attracts moment. The top bars over the bore are heavy as a result.

Reinforcement of the {d['thickness']:.2f} m slab, by strength:

| Direction and face | Moment, kN·m/m | Steel needed, mm²/m | Bars |
| --- | ---: | ---: | --- |
{face_rows}
| Across the floor of the store, both faces together | tension {kn(d['tie'],0)} kN/m | {d['tie_area']*1e6:,.0f} | added to the radial bars between the walls |

The reinforcement is to be designed again once the ground is known.

### 11.7 Base of the shaft

The shaft carries {kn(wt['shaft'],0)} kN and stands on a ring plate bolted to anchors cast in the slab. Check 1 holds the top of the shaft with the support rig, which is set before the first pod. With the top held the base sees little moment and no bolt goes into tension.

The project asked for a heavy fixed base, because the out-of-balance loads are severe. The base is therefore also designed to stand alone, with the top free, under the worst out-of-balance load: as an accident, so that the pods never depend on the rig alone.

| Top of the shaft | State | Axial load, kN | Moment at the base, kN·m | Load factor | Tension in the worst bolt, kN | Bearing under the ring, kN/m |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{case_rows}

| Part | Design | Basis |
| --- | --- | --- |
| Anchors | **{b['n']} {b['bolt']}**, {F['shaft_base']['anchor']}, on a {b['circle']:.2f} m circle | design strength {kn(b['strength'],0)} kN each (ACI 318-19 Section 17.6.1). The worst bolt uses {b['use']*100:.0f}% of it in the accident, against a limit of {F['shaft_base']['most_use_in_accident']*100:.0f}% set here. |
| Ring plate | {F['shaft_base']['ring_inside_m']:.2f} m to {F['shaft_base']['ring_outside_m']:.2f} m across, about {math.ceil(b['plate']*200)*5} mm thick, with a gusset between every pair of bolts | bending between gussets, to be detailed |
| Bearing on the concrete | {kn(b['line'],0)} kN/m against {kn(b['bearing'],0)} kN/m | ACI 318-19 Section 22.8, over the {b['width']*1000:.0f} mm width of the ring |
| Anchor reinforcement | about {b['hairpins']*1e6:,.0f} mm² of vertical bar round each half of the bolt circle | carries the bolt tension into the slab in place of a concrete cone. The slab is to be thickened locally for the embedment. |
| Turning of the shaft | friction under the ring holds {kn(b['friction'],0)} kN·m | against {kn(cn.C['drive']['torque'],0)} kN·m with every level driven at once (section 12.8) |

### 11.8 Verification

| Check | Value | Independent value | Agreement |
| --- | ---: | ---: | --- |
| Upward push of the ground, summed over the slab | {d['reaction']/1e6:,.2f} MN | loads applied, {d['applied']/1e6:,.2f} MN | equal |
| Sum of the loads in section 11.2 | {c['total']/1e6:,.2f} MN | loads applied to the plate, {d['applied']/1e6:,.2f} MN | equal |
| A plate under even pressure alone | settles evenly, with no bending | exact result | equal |
| A very stiff plate on very soft ground | pressure even to within 0.2% | mean pressure | equal |
| Pressure on the ground | above zero everywhere | | the slab does not lift |

These are checked at every build by [foundation.py](../gpu_silo/foundation.py).

### 11.9 Conclusion

The slab is {c['drawn']:.2f} m thick, on ground taken as {F['design_ground']}. It is strong enough, with shear ties near the walls and heavy top bars. The silo weighs {c['total']/1e6:,.0f} MN full and settles about {d['settle']['outer']*1000:.0f} mm on that ground as it is loaded. Filling the store lowers the walls {differ(d):.1f} mm against the shaft, which the flexible section of each wall connection takes. The base of the shaft takes {b['n']} {b['bolt']} anchors and stands alone under the worst out-of-balance load.

The ground is an assumption. A ground investigation has to confirm it, and has to give the settlement over time, before the slab or the choice between a slab and piles is final.

**Correction in revision H.** Revision G took springs of 15, 40 and 100 MN/m³ and called them soft, medium and stiff ground. Those are values for a small test plate. Under a slab {2*fd.RADIUS:.0f} m across the spring is about a tenth of that, so revision G described rock while calling it soil, and its settlements were too small by about ten times for soil. The method is unchanged. The grounds are now set by their modulus.

### 11.10 Foundation interfaces and site verification

1. **The ground.** Its strength, its stiffness, how it varies across the site, groundwater, and settlement over time. A slab on ground that is softer on one side tilts, and the shaft tilts with it.
2. **Piles or ground improvement**, if the site needs them.
3. **Wind and earthquake**: overturning, sliding and the extra pressure at the rim. They wait for the site.
4. **The ground entry**, which crosses the slab at the door, and any pits or trenches in the floor of the bore.
5. **Heat.** The floor of the store is at {th.COLD:.0f} to {th.HOT:.0f} °C for life, on ground that it will warm and dry.
6. **The slab as a tie.** Hoop tension in the slab where it restrains the feet of the walls, and the detail of the wall feet.
7. **The anchor embedment** and the local thickening of the slab under the shaft.
"""


def connection_section():
    c = cn.C
    pin, arm, tip, hub, drive, budget = c["pin"], c["arm"], c["tip"], c["hub"], c["drive"], c["budget"]
    R, D = cn.R, cn.DRIVE
    check_rows = "\n".join(f"| {name.capitalize()} | {kn(c['factored']/2)} | {kn(value)} | {c['factored']/2/value:.2f} |" for name, value in pin["checks"].items())
    mass_rows = "\n".join(f"| {name} | {hub['masses'][key]:,.0f} |" for key, name in (
        ("drum", f"Drum, {cn.HUB['drum_diameter_m']:g} m across and {cn.HUB['drum_wall_mm']} mm thick"), ("rings", f"Two ring plates, {cn.HUB['ring_plate_mm']} mm"),
        ("arms", f"{4*cfg.BAYS} arms with their lugs and stiffeners"), ("floor", "Access floor"), ("bearing", "Slewing ring"), ("drive", "Drive, brake and lock")))
    bearing_rows = "\n".join(f"| {case['name']} | {kn(case['moment'],0)} | {kn(case['radial'],0)} | {kn(case['roller'],0)} |" for case in hub["cases"])
    budget_rows = "\n".join(
        f"| {'**' if r is budget['adopted'] else ''}{st.inches(r['wall']['section']['wall_in'])} in ({r['wall']['section']['wall']*1000:.1f} mm){'**' if r is budget['adopted'] else ''} | {budget['truss']*1000:.2f} | {r['shaft']*1000:.2f} | {budget['root']*1000:.1f} | {budget['hub']*1000:.1f} | "
        f"{'**' if r is budget['adopted'] else ''}{r['total']*1000:.2f}{'**' if r is budget['adopted'] else ''} | {'Yes' if r['ok'] else 'No'} | {'lightest' if r['extra'] < .01 else format(r['extra'], '.0f')} |"
        for r in budget["rows"])
    p = budget["adopted"]
    fx = c["flexible"]
    return f"""## 12. Check 6: root connection, hub and level drive

### 12.1 Arrangement

The shaft is fixed. At each level a hub turns on it and carries the {cfg.BAYS} pods of that level. Section 6 gives the loads. This section designs the parts, as a first pass, and every number is calculated by [connection.py](../gpu_silo/connection.py).

The arrangement is set in this report. It follows what the model shows: a bearing ring at the top and at the bottom of each level, an access walkway {st.ACCESS:.2f} m wide between the shaft and the pod roots, and an arm from the hub to each truss at the top and at the bottom.

- **Hub.** A top ring and a bottom ring, {cn.DEPTH:.3f} m apart, joined by a drum round the shaft, {cn.HUB['drum_diameter_m']:g} m across.
- **Arms.** Each truss has a top arm and a bottom arm, {cn.ARM*1000:.0f} mm long, standing out from the rings to the pod root at {st.ROOT:.2f} m radius. They cross above and below the walkway, so nothing blocks it.
- **Root of a truss.** The top chord hangs from a pin through two lug plates on the top arm. The pin takes the pull and the weight. The bottom chord bears on a block on the bottom arm, which takes the thrust and is shimmed to level the pod.
- **Bearings.** A slewing ring under the bottom ring sits on a collar on the shaft. It carries the weight of the level and has the gear teeth for the drive. A ring of guide rollers on the top ring runs on the shaft. The two together hold the hub upright.
- **Drive.** A geared motor on the collar turns a pinion in the gear. Each level has its own, so the levels index separately.

![The hub of one level and the root of one truss](figures/root.svg)

### 12.2 Loads at the root of one truss

| Load | Unfactored, kN | Factored, kN | Basis |
| --- | ---: | ---: | --- |
| Pull on the pin | {kn(c['pull'])} | {kn(cn.FACTOR*cn.IMPACT*c['pull'])} | {cn.FACTOR:g} D with {cn.IMPACT:g} for the pod being landed by the hoist |
| Weight on the pin | {kn(c['weight'])} | {kn(cn.FACTOR*cn.IMPACT*c['weight'])} | |
| **Resultant on the pin** | {kn(c['resultant'])} | **{kn(c['factored'])}** | |
| Thrust on the bearing block | {kn(c['thrust'])} | {kn(cn.FACTOR*cn.IMPACT*c['thrust'])} | |

### 12.3 Pin and lugs

The pin is {R['pin']['steel']} and the lugs are {R['lug']['steel']}. The pin is in double shear between two lugs.

| Check on the pin | Demand | Design strength | Ratio |
| --- | ---: | ---: | ---: |
| Shear on two planes | {kn(c['factored'])} kN | {kn(pin['shear'])} kN | {c['factored']/pin['shear']:.2f} |
| Bending between the lugs | {pin['moment']/1e3:.1f} kN·m | {pin['bending']/1e3:.1f} kN·m | {pin['moment']/pin['bending']:.2f} |

| Check on one lug, AISC 360-22 Sections D5 and J7 | Demand, kN | Design strength, kN | Ratio |
| --- | ---: | ---: | ---: |
{check_rows}

**A {pin['d']*1000:.0f} mm pin in two {pin['t']*1000:.0f} mm lugs**, each {pin['width']*1000:.0f} mm wide with {pin['a']*1000:.0f} mm of plate beyond the hole. These are the smallest in the lists and they are lightly used. Strength does not govern the root: stiffness does.

The hole is {R['lug']['hole_clearance_mm']:g} mm larger than the pin. The pull and the weight always act the same way, so the pin always seats on the same side of the hole, and the clearance is taken up once, when the pod is landed. It is set out with the shims under the bearing block and is not a movement of the tip in service.

### 12.4 Arms

The top arm carries the pull along its length and the weight across its end, as a cantilever. A flat plate, as now drawn, would let the pod drop about 2 mm. The arm has to be a beam.

| Quantity | Value | Basis |
| --- | ---: | --- |
| **Section** | **{arm['name']}** | lightest in the list within the limit below |
| Drop at the pin under the weight | {arm['drop']*1000:.2f} mm | limit {R['arm_deflection_limit_mm']:g} mm, set here. {arm['bend']*1000:.2f} mm in bending and {arm['shear_drop']*1000:.2f} mm in shear. |
| Stretch of the top arm with shortening of the bottom arm | {arm['stretch']*1000:.3f} mm | |
| Tension with bending, factored | ratio {arm['use']:.2f} | AISC 360-22 Section H1 |
| Shear, factored | ratio {arm['shear_use']:.2f} | |

### 12.5 Movement of the pod tip from the root connection

| Cause | At the root, mm | At the tip, mm | Note |
| --- | ---: | ---: | --- |
| Top arm bends under the weight | {arm['drop']*1000:.2f} | {tip['arm']*1000:.2f} | the whole pod drops |
| Arms, pin and lugs stretch | {c['horizontal']*1000:.3f} | {tip['stretch']*1000:.2f} | the tip drops {cn.RATIO:.1f} mm for each millimetre |
| Pin and lugs give under the weight | {tip['pin']*1000:.3f} | {tip['pin']*1000:.2f} | |
| **Total** | | **{tip['total']*1000:.2f}** | allowance {R['allowance_mm']['root']:g} mm |

The root connection moves the tip {tip['total']*1000:.2f} mm, well inside the {st.TIP['single_mm']:g} mm allowed to one part. An allowance of {R['allowance_mm']['root']:g} mm is carried, to cover the rings and welds of the hub, which are not modelled.

### 12.6 Hub

With a level full, the eight pulls on the top ring balance round it and put it in tension. The eight thrusts put the bottom ring in compression.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Force round each ring, level full | {kn(hub['ring_force'],0)} kN | pull of one pod ÷ 2 sin(180°/{cfg.BAYS}) |
| Ring section needed | {hub['ring_area']*1e6:,.0f} mm² | factored, in tension. A {cn.HUB['ring_plate_mm']} mm plate ring has many times this. |

| Part of one hub | kg |
| --- | ---: |
{mass_rows}
| **Total** | **{hub['mass']:,.0f}** |

Check 1 allowed 3 t a level for the hub and floor. This estimate is {hub['mass']/1e3:.1f} t, so the allowance is raised to {hub['allowance']/1e3:g} t in this revision. It adds {cfg.LEVELS*(hub['allowance']/1e3-3):.0f} t to the load on the shaft. The strength ratio of check 1 rises by 0.01 and the movement of the pod tips does not change.

### 12.7 Hub bearings

A level that is part filled or bunched is out of balance. The moment goes into the shaft as a pair of sideways forces, one at the slewing ring and one at the guide rollers, {cn.DEPTH:.3f} m apart.

| State of the level | Out-of-balance moment, kN·m | Sideways force at each bearing, kN | On one guide roller, kN |
| --- | ---: | ---: | ---: |
{bearing_rows}

| Requirement on the bearings | Value | Basis |
| --- | ---: | --- |
| Weight on the slewing ring | {kn(hub['axial'],0)} kN | pods and hub of one level |
| Sideways force on the slewing ring and on the guide rollers | {kn(hub['cases'][0]['radial'],0)} kN | unfactored |
| Tilt of the hub allowed | {hub['tilt']*1e3:.3f} mm in a metre | {R['allowance_mm']['hub_tilt']:g} mm at the pod tips, {st.TIP_R:.2f} m from the axis |
| **Sideways stiffness needed at each bearing, with its seating** | **{hub['radial_stiffness']/1e6:,.0f} kN/mm** | rotational stiffness {hub['rotational']/1e9:.1f} GN·m per radian |
| Clearance in the bearings | none | preloaded slewing ring, and guide rollers on adjustable mounts set to touch |

**The stiffness of the hub bearings matters more than their strength.** A sideways give of 0.1 mm at each bearing moves the pod tips {0.2e-3/cn.DEPTH*st.TIP_R*1000:.1f} mm. The value above is a requirement for the bearing supplier, like the stiffness of the top restraint in check 1.

Filling a level in opposite pairs would cut the moment to {hub['opposite']*100:.0f}% of this. The project decided in revision I not to constrain the order of filling, so the worst case stands.

### 12.8 Drive of one level

| Torque at the hub | kN·m | Basis |
| --- | ---: | --- |
| Friction of the slewing ring | {drive['friction']/1e3:.1f} | µ/2 × (weight + 3.81 × sideways force) × raceway diameter of {D['raceway_diameter_m']:g} m, with µ = {D['friction_coefficient']:g} and {D['start_factor']:g} for starting. The bearing maker's formula for a roller slewing ring. |
| Weight of an out-of-balance level on a leaning shaft | {drive['gravity']/1e3:.1f} | {kn(hub['cases'][0]['moment'],0)} kN·m × a lean of {drive['lean']*1000:.1f} mm in a metre: the shaft out of plumb by {D['plumb_tolerance']*1000:g} mm in a metre, its lean from check 1, and the tilt of the hub |
| Starting and stopping a full level | {drive['inertia']/1e3:.1f} | one bay in {D['index_seconds']} s (section 6.2) |
| **Running torque** | **{drive['running']/1e3:.1f}** | |
| **Design torque** | **{drive['design']/1e3:.0f}** | service factor {D['service_factor']:g} |

| Quantity | Value | Basis |
| --- | ---: | --- |
| Fastest speed of the hub | {drive['rpm']:.2f} rev/min | |
| **Motor power** | **{drive['power']/1e3:.1f} kW** | design torque at the fastest speed, drive efficiency {D['drive_efficiency']:g} |
| Force on the gear teeth | {kn(drive['tooth'],0)} kN | gear {D['gear_pitch_diameter_m']:g} m across |
| Torque at the pinion | {drive['pinion']/1e3:.1f} kN·m | {D['pinion_teeth_ratio']}:1 at the gear |
| Brake, to hold a level | at least {drive['hold']/1e3:.1f} kN·m at the hub | twice the torque from the lean |
| Lock at each bay position | {drive['lock']/1e3:.0f} kN·m, {kn(drive['lock_force'],0)} kN on a pin at the pod roots | {D['lock_factor']:g} times the design torque. A {max(40, math.ceil(drive['lock_pin']*200)*5)} mm pin is ample. |
| Torsion in the shaft, all {cfg.LEVELS} levels driven at once | {drive['torque']/1e3:,.0f} kN·m, {drive['shear_stress']/1e6:.1f} MPa | not significant |

**A motor of about {math.ceil(drive['power']/1e3*2)/2:g} kW on each level is enough.** The torque is small because the speed is very low and a roller slewing ring has little friction. Friction is {drive['friction']/drive['running']*100:.0f}% of it. A plain bearing in its place would need several times the torque.

The drive does not hold the level in position for docking. The lock does, with the brake as its backup.

### 12.9 The limit on accumulated movement

Section 3.7 left the choice of where to find room for the root connection to this check. Two allowances are needed, {budget['root']*1000:g} mm for the root connection and {budget['hub']*1000:g} mm for the tilt of the hub. The simplest place to find the room is the wall of the shaft:

| Shaft wall | Truss, mm | Shaft, mm | Root connection, mm | Hub tilt, mm | Total, mm | Within {st.TIP['accumulated_mm']:g} mm | Extra steel, t |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
{budget_rows}

**The project set the shaft wall at {st.inches(p['wall']['section']['wall_in'])} in, in revision I.** The lightest wall that meets the shaft's own limits is {st.inches(st.C['shaft']['lightest']['section']['wall_in'])} in, and the thinnest that keeps the total within {st.TIP['accumulated_mm']:g} mm is {st.inches(budget['least']['wall']['section']['wall_in'])} in. The wall adopted adds {p['extra']:.0f} t of plate and brings the total to **{p['total']*1000:.2f} mm**.

Settlement and temperature also move the wall sleeves against the pod tips. They are not in this total. The flexible section of each wall connection takes them (section 3.8).

### 12.10 Verification

| Check | Value | Independent value | Agreement |
| --- | ---: | ---: | --- |
| Force round the top ring, resolved at one pod | 2 × {kn(hub['ring_force'],1)} kN × sin(180°/{cfg.BAYS}) = {kn(2*hub['ring_force']*math.sin(math.pi/cfg.BAYS),1)} kN | pull of one pod, {kn(2*c['pull'],1)} kN | equal |
| Drop of the top arm in bending, by hand | {kn(c['weight'])} kN × ({cn.ARM*1000:.0f} mm)³ ÷ (3 E I) = {c['weight']*cn.ARM**3/(3*st.E*arm['inertia'])*1000:.3f} mm | {arm['bend']*1000:.3f} mm | equal |
| Sideways force at each bearing | {kn(hub['cases'][0]['moment'],0)} kN·m ÷ {cn.DEPTH:.3f} m = {kn(hub['cases'][0]['moment']/cn.DEPTH,0)} kN | {kn(hub['cases'][0]['radial'],0)} kN | equal |

### 12.11 Conclusion

The root of each truss is a {pin['d']*1000:.0f} mm pin in two {pin['t']*1000:.0f} mm lugs on a {arm['name']} arm, with a bearing block on a second arm below. It moves the pod tip {tip['total']*1000:.2f} mm. Each level turns on a slewing ring, steadied by guide rollers at the top of its hub, and is driven by a motor of about {math.ceil(drive['power']/1e3*2)/2:g} kW through a gear on the ring. The capacity of the drive is not a concern.

The thing to watch is the stiffness of the hub bearings: {hub['radial_stiffness']/1e6:,.0f} kN/mm each, or a part-filled level tilts its pods further than its allowance. With the shaft wall at {st.inches(p['wall']['section']['wall_in'])} in the accumulated movement of a pod tip is {p['total']*1000:.2f} mm against {st.TIP['accumulated_mm']:g} mm.

The arrangement of the hub was accepted by the project in revision I, and the model now draws the drum and the beam arms.

### 12.12 Connection interfaces and procurement verification

1. **Selection of the slewing ring and the guide rollers** from a supplier: static capacity, stiffness, life and sealing.
2. **The hub in detail**: the drum, the rings, their welds, and the arms where they join the rings.
3. **The shaft at each level**: the collar under the slewing ring, the track for the guide rollers, and the local stress in the shaft wall.
4. **Gear, gearbox, brake and lock** in detail, and their controls.
5. **Power and data to a turning level.** Revision J routes the main buses down the fixed shaft, feeds each indexed pod at a separate dry berth contact and uses an optical rotary joint for control data. See the R15/Q11 decision.
6. **The carriages that bunch the pods** on a level, and their actuators.
7. **Earthquake**, which may govern the lock and the guide rollers. The assumed 0.05g envelope is screened in section 7.8. Establish the actual site spectrum before release.
8. **Fatigue.** The levels turn seldom, so it is not expected to govern.
"""



def moved(settlement):
    """How far a part goes down, in words. A small rise is said as a rise."""
    return f"the shaft by {settlement*1000:.1f} mm" if settlement >= 0 else f"raises the shaft by {-settlement*1000:.1f} mm"


def hours(seconds):
    return "no limit" if seconds == float("inf") else f"{seconds/3600:.1f} h" if seconds >= 5400 else f"{seconds/60:.0f} min"


def thermal_section():
    c, a, t = th.C, th.AMBIENT, th.T
    rides = [("As first drawn, 250 mm", c["rides"]["drawn"]), ("Check 3, carbon steel bars", c["rides"]["proposed"]), ("Adopted: section 10, stainless steel bars", rf.C["proposed"]["ride"])]
    ride_rows = "\n".join(
        f"| {name} | {r['volume']:,.0f} | {r['energy']/1e9:.1f} | {r['per_k']/60:.1f} | **{r['layered']/60:.0f} min** | {r['mixed']['annual_mean_c']/60:.0f} min | {'none' if r['mixed']['summer_design_c'] <= 0 else format(r['mixed']['summer_design_c']/60, '.0f') + ' min'} |"
        for name, r in rides)
    air_rows = "\n".join(
        f"| {r['air']:g} | {r['each']/1e6:.2f} | {r['capacity']/1e6:.1f} | {r['needed'] if r['needed'] and r['needed'] <= th.INSTALLED else 'more than ' + str(th.INSTALLED)} | {r['mixed']:.1f} | {'within' if r['mixed'] <= th.COLD else f'{r["mixed"]-th.COLD:.1f} K too warm'} |"
        for r in c["rows"])
    wall_rows = "\n".join(
        f"| {l['lift']} | {l['t']*1000:.0f} | {l['bare']['flux']:.0f} | {l['bare']['wet']:.0f} | {l['bare']['dry']:.0f} | **{l['bare']['gradient']:.0f}** | {l['clad']['dry']:.0f} | **{l['clad']['gradient']:.0f}** |"
        for l in c["lifts"])
    p = rf.C["proposed"]["ride"]
    sw, lay, mv, sq, inner, cr, fz, ev = c["swell"], c["layering"], c["movement"], c["squeeze"], c["inner"], c["creep"], c["freeze"], c["evaporation"]
    lim = c["limit"]
    cool = c["cooler"]
    return f"""## 9. Check 5: heat balance of the store

### 9.1 What the store does

The store is the water-glycol between the two walls. Each pod has a CDU that takes the heat of its {cfg.CLUSTER['racks_per_pod']} racks and gives it to the store. Each dry cooler draws liquid from the store, cools it in the outside air and returns it. In a steady state the coolers take out what the pods put in. When they cannot, the store warms, and that reserve is what this check measures.

This is a first pass, with a simple model of each part. Its purpose is to find what governs the performance, to give the temperatures for the design of the walls, and to list what the detailed design has to settle. Every number is calculated by [thermal.py](../gpu_silo/thermal.py).

### 9.2 Inputs and assumptions

The site is not fixed. The outside air temperatures are therefore assumptions, and so is the rating condition of the coolers. They are marked.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Heat from the racks | {th.HEAT/1e6:.1f} MW | {cfg.RACKS} racks at {cfg.CLUSTER['liquid_heat_per_rack_kw']:.1f} kW |
| Heat from the pumps | {t['pump_heat_fraction']*100:g}%, {(th.LOAD-th.HEAT)/1e6:.2f} MW | allowance. The power of the CDU pumps and cooler pumps ends up in the liquid. |
| **Heat to reject** | **{th.LOAD/1e6:.2f} MW** | |
| Warmest coolant into a rack | {t['rack_supply_limit_c']:g} °C | NVIDIA, for the Vera Rubin generation |
| Rise across the racks | {th.RISE:g} K | input. NVIDIA gives about 55 °C leaving the rack. |
| Approach of the CDU | {t['cdu_approach_k']:g} K | **assumption.** The CDU has a plate heat exchanger between the rack loop and the store, so store liquid does not pass through the cold plates. |
| Dry coolers | {th.INSTALLED} of {cfg.COOL['cooler_capacity_mw']:g} MW | input |
| Rating condition of a cooler | liquid {t['cooler_rating']['liquid_in_c']:g} °C in and {t['cooler_rating']['liquid_in_c']-th.RISE:g} °C out, air {t['cooler_rating']['air_in_c']:g} °C in and {t['cooler_rating']['air_in_c']+cfg.COOL['air_rise_k']:g} °C out | **assumption** for the temperatures. The liquid drop and air rise are inputs. |
| Outside air, summer design | {a['summer_design_c']:g} °C | **assumption** |
| Outside air, extreme | {a['extreme_hot_c']:g} °C | **assumption** |
| Outside air, winter design | {a['winter_design_c']:g} °C | **assumption** |
| Outside air, yearly mean and daily range | {a['annual_mean_c']:g} °C and {a['daily_range_k']:g} K | **assumption** |
| Liquid | {cfg.FLUID['glycol_fraction']*100:g}% propylene glycol by volume | input, and the mixture NVIDIA designs for |
| Density of the liquid | {sw['density_fill']:,.0f} kg/m³ at {sw['fill']:g} °C, {th.density(th.COLD):,.0f} at {th.COLD:g} °C, {th.density(th.HOT):,.0f} at {th.HOT:g} °C | water tables and the density of glycol, mixed to a specific gravity of 1.022 at 15.6 °C. To be replaced with the supplier's table. |
| Freezing and bursting | slush forms at {fz['freeze']:g} °C, pipes burst below about {fz['burst']:g} °C | Dow data for inhibited propylene glycol at this strength |
| Heat held by the liquid | {th.CAPACITY/1e6:.2f} MJ/m³·K | {cfg.FLUID['density_kg_m3']:,.0f} kg/m³ × {cfg.FLUID['specific_heat_kj_kgk']:g} kJ/kg·K, as in the other calculations. Supplier data at {th.MEAN:.0f} °C gives {sw['capacity']/1e6:.2f}. |
| Concrete | conducts {th.CONCRETE['conductivity_w_mk']:g} W/m·K, expands {th.ALPHA*1e6:g} × 10⁻⁶ per K | typical values |
| Surface coefficients | liquid {th.FILMS['liquid']:g}, outside in wind {th.FILMS['outside_wind']:g}, outside in still air {th.FILMS['outside_still']:g}, bore {th.FILMS['bore']:g} W/m²·K | typical values |
| Liner | {cfg.PROJECT['coating']['thickness_mm']:g} mm, {t['liner_conductivity_w_mk']:g} W/m·K | input thickness |
| Insulation on the outer wall, if fitted | {t['insulation']['thickness_mm']} mm at {t['insulation']['conductivity_w_mk']:g} W/m·K | for comparison only |
| Air in the bore | {t['bore_air_c']:g} °C | **assumption.** The bore has to be ventilated to hold it. |
| Temperature at which the structure is built | {t['erection_temperature_c']:g} °C | assumption, for movements |

### 9.3 Temperatures the store has to run at

A rack may take coolant at {t['rack_supply_limit_c']:g} °C. The CDU needs {t['cdu_approach_k']:g} K to pass the heat on. So:

- the store may supply the CDUs at **{th.COLD:.0f} °C** at most;
- the liquid comes back from the CDUs at **{th.HOT:.0f} °C**;
- {c['flow']:,.0f} kg/s, {lay['flow']:.2f} m³/s, passes through the pods, and the same through the coolers.

Each kelvin of CDU approach moves both temperatures by one kelvin. If the store liquid went straight through the racks they would be {t['rack_supply_limit_c']:g} °C and {t['rack_supply_limit_c']+th.RISE:g} °C.

### 9.4 One dry cooler

From its rating, a cooler passes on {cool['eps']*100:.0f}% of the most heat that the air could take: an effectiveness of {cool['eps']:.2f}, {cool['ntu']:.2f} transfer units, a conductance of {cool['ua']/1e3:.0f} kW/K. With its fans at full speed and its rated flow, the heat it rejects is in proportion to the difference between the liquid entering and the air entering: **{th.cooler(1.,0.)[0]/1e3:.0f} kW for each kelvin.** At its rating that difference is {cool['itd']:g} K.

So the temperature of the liquid that the coolers draw is worth as much as the weather. Ten kelvin warmer liquid is the same as ten kelvin cooler air.

### 9.5 A mixed store against a layered store

The store can run in two ways.

- **Mixed.** The liquid is at one temperature throughout. The pods must be supplied at {th.COLD:.0f} °C or less, so the whole store is at {th.COLD:.0f} °C or less, and that is what the coolers draw.
- **Layered.** Warm liquid floats on cool liquid. The pods draw the cool layer at {th.COLD:.0f} °C and return to the warm layer at {th.HOT:.0f} °C. The coolers draw the warm layer and return to the cool one. The coolers work on liquid {th.RISE:g} K warmer.

| Outside air, °C | Layered: one cooler, MW | Layered: {th.INSTALLED} coolers, MW | Layered: coolers needed | Mixed: store settles at, °C | Mixed: supply against {th.COLD:.0f} °C |
| ---: | ---: | ---: | ---: | ---: | --- |
{air_rows}

![Heat rejected against outside air temperature](figures/heat_rejection.svg)

| | Mixed store | Layered store |
| --- | ---: | ---: |
| Warmest outside air at which {th.INSTALLED} coolers carry the load | {lim[th.INSTALLED, True]:.1f} °C | **{lim[th.INSTALLED, False]:.1f} °C** |
| The same with {th.DUTY} coolers | {lim[th.DUTY, True]:.1f} °C | {lim[th.DUTY, False]:.1f} °C |
| Coolers needed on the {a['summer_design_c']:g} °C design day | {c['mixed_coolers']} | {next(r['needed'] for r in c['rows'] if r['air']==a['summer_design_c'])}, see section 9.8 |

**The store has to be layered. This is the main finding of check 5.** A mixed store with the {th.INSTALLED} coolers holds its supply temperature only up to {lim[th.INSTALLED, True]:.0f} °C outside. On the design day it would settle about {next(r['mixed'] for r in c['rows'] if r['air']==a['summer_design_c'])-th.COLD:.0f} K too warm, and it would take {c['mixed_coolers']} coolers to prevent that.

With the pump heat included, {th.DUTY} coolers are needed at their rating, not {cfg.COOL['duty_coolers']}. That leaves {th.INSTALLED-th.DUTY} spare.

### 9.6 What layering needs

Each pod reaches the store through sleeves at its own level, and each cooler through conduits at its own level. Left like that, warm liquid would rise and cool liquid sink, so the store would layer partly by itself. But the pods on the upper levels would draw warmer liquid than those below, and the result could not be predicted. Layering has to be designed:

1. **Pods draw from the bottom of the store and return to the top.** One pair of vertical pipes in the store for each of the {cfg.BAYS} bays would serve the {cfg.LEVELS} pods above one another.
2. **Coolers draw from the top and return to the bottom.** One pair of vertical pipes for each of the {cfg.FRAMES} frames.
3. **Liquid enters slowly and sideways.** The warm and cool layers differ by {lay['difference']:.1f} kg/m³, about eight times the difference in a chilled-water store, where layered tanks are routine. Spread round the store, the whole flow can enter through an opening {lay['opening']*1000:.0f} mm high without stirring the layers (densimetric Froude number of 1).
4. **The two flows are kept equal.** The boundary between the layers then stays where it is. The coolers need variable flow, and the store needs temperature sensors up its height to show where the boundary is.
5. **The boundary is re-made often.** Conduction thickens it by about {round(lay['conduction']*100)*10} mm in a day. Running it to the top of the store each night, as section 9.8 describes, keeps it thin.

This check takes {th.FOM*100:.0f}% of the store as usable, which is in the usual range for a layered tank.

**The pipes are in the model from revision F.** They are drawn in [layering.py](../gpu_silo/layering.py) as follows.

| Quantity | Value | Note |
| --- | ---: | --- |
| Pairs of pipes | {c['pipes']['pairs']} | {cfg.BAYS} for the bays of pods, on the inner wall, and {cfg.FRAMES} for the cooler frames, on the outer wall |
| Pipe | {t['layering']['riser_diameter_m']*1000:.0f} mm | |
| Speed in a pod pipe | {c['pipes']['pod_speed']:.1f} m/s | {cfg.LEVELS} pods |
| Speed in a cooler pipe | {c['pipes']['cooler_speed']:.1f} m/s | {cfg.COOL['coolers_per_frame']} coolers, with all frames sharing the flow |
| Opening at each open end | a {t['layering']['diffuser_diameter_m']:g} m plate, {t['layering']['diffuser_gap_m']*1000:.0f} mm from the pipe | the liquid leaves sideways all round the plate |
| Froude number where warm liquid enters, at the top | {c['pipes']['warm_froude']:.2f} | {cfg.BAYS} pod returns. 1 or less does not stir the layers. |
| Froude number where cool liquid enters, at the bottom | {c['pipes']['cool_froude']:.2f} | {cfg.FRAMES} cooler returns |
| Top openings | {walls.LIQUID-sw['to_hot']-t['layering']['top_mouth_below_cold_fill_m']:.2f} m | {t['layering']['top_mouth_below_cold_fill_m']*1000:.0f} mm under the cold fill level of section 9.9, so they are covered before the store warms |
| Bottom openings | {t['layering']['mouth_above_floor_m']:.2f} m | above the floor |

The pipes hang from brackets on the walls and are fitted after the liner. Their sizes are a first estimate. The detail design is open item 1.

### 9.7 Ride-through

Ride-through is how long the pods keep their supply temperature after the coolers stop.

| Walls | Store, m³ | Heat held, GJ/K | Minutes to warm 1 K | Layered | Mixed, {a['annual_mean_c']:g} °C outside | Mixed, {a['summer_design_c']:g} °C outside |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{ride_rows}

- **Layered**, the ride-through is one pass of the store through the pods, less the part lost at the boundary. The supply stays at {th.COLD:.0f} °C the whole time, then rises by {th.RISE:g} K at once when the cool layer is used up. It does not depend on the weather, provided the store was full of cool liquid when the coolers stopped. In cool weather the coolers can hold the cool layer below {th.COLD:.0f} °C, which lengthens the ride-through. This check does not count on it.
- **Mixed**, the supply warms from the first minute, and the ride-through is the time to reach {th.COLD:.0f} °C from wherever the store sat. In mild weather that is long. On the design day there is none.

The {calcs.C['ride_min']:.0f} minutes in the [design calculations](calcs.md) is a {calcs.C['swing']:g} K swing of the store. It is the mixed case with the store held {calcs.C['swing']:g} K below its limit, which the coolers can do only below about {lim[th.INSTALLED, True]-calcs.C['swing']:.0f} °C outside.

The concrete is not counted. In an hour only the first 70 mm or so of each wet face follows the liquid, which adds 2 to 3%.

### 9.8 Hot afternoons and cool nights

The layered store also carries the plant through air that is too warm for the coolers. Figures are for the store as adopted.

| Outside air | {th.INSTALLED} coolers reject | Store makes up | For |
| --- | ---: | ---: | ---: |
| {a['summer_design_c']:g} °C, summer design | {p['day_capacity']/1e6:.1f} MW | {max(0, th.LOAD-p['day_capacity'])/1e6:.1f} MW | {hours(p['day'])} |
| {a['extreme_hot_c']:g} °C, extreme | {p['hot_capacity']/1e6:.1f} MW | {max(0, th.LOAD-p['hot_capacity'])/1e6:.1f} MW | {hours(p['hot'])} |
| {a['summer_design_c']-a['daily_range_k']:g} °C, the night after a design day | {p['night_capacity']/1e6:.1f} MW | {(p['night_capacity']-th.LOAD)/1e6:.1f} MW to spare | refills a spent store in {hours(p['recharge'])} |

Above {lim[th.INSTALLED, False]:.0f} °C the coolers fall behind and the cool layer is drawn down. At night they catch up. Whether {th.INSTALLED} coolers are enough therefore depends on how many hours a day the site spends above {lim[th.INSTALLED, False]:.0f} °C, which needs the site's weather record. A site hotter than the one assumed needs more coolers or a smaller CDU approach.

### 9.9 The liquid rises as it warms

| From | To | Rise of the surface |
| --- | --- | ---: |
| Filled at {sw['fill']:g} °C | all at {th.COLD:.0f} °C | {sw['to_cold']*1000:.0f} mm |
| Filled at {sw['fill']:g} °C | all at {th.HOT:.0f} °C | **{sw['to_hot']*1000:.0f} mm** |
| All at {th.COLD:.0f} °C | all at {th.HOT:.0f} °C, as at the end of a ride-through | {sw['cold_to_hot']*1000:.0f} mm |
| | each kelvin, near {th.MEAN:.0f} °C | {sw['per_k']*1000:.0f} mm |

The freeboard is {sw['freeboard']*1000:.0f} mm. A store filled cold to {walls.LIQUID:.2f} m would overflow by about {(sw['to_hot']-sw['freeboard'])*1000:.0f} mm of depth when it warmed. So:

- the {walls.LIQUID:.2f} m level is the level of a store that is warm throughout, and the cold fill stops at **{walls.LIQUID-sw['to_hot']:.2f} m**;
- an overflow to a catch tank is needed in any case, because the level cannot be relied on.

From revision F the model has an overflow standpipe inside the store, with its rim at {walls.LIQUID+t['overflow']['above_liquid_m']:.2f} m. It leaves through the outer wall beside the fill line and runs to a {t['overflow']['catch_tank_m3']:g} m³ catch tank by the pump skid. That tank holds {t['overflow']['catch_tank_m3']/ev['surface']*1000:.0f} mm of the depth of the store.

The liquid is {(1-sw['density']/cfg.FLUID['density_kg_m3'])*100:.0f}% lighter at {th.MEAN:.0f} °C than the {cfg.FLUID['density_kg_m3']:,.0f} kg/m³ used for the pressure on the walls in check 3, which is on the safe side. The rise is worked out for walls that do not move and a store of even width.

### 9.10 Cold weather

At {cfg.FLUID['glycol_fraction']*100:g}% glycol the liquid turns to slush at {fz['freeze']:g} °C and can burst a pipe below about {fz['burst']:g} °C. The winter design temperature assumed is {fz['winter']:g} °C.

A cooler that is running is full of warm liquid and is safe. A cooler that is stopped is not: the {th.INSTALLED-th.DUTY} spares in normal running, and all {th.INSTALLED} when the pods are off. Each stopped cooler needs a small flow from the store, or to be drained. More glycol is not a good answer, because {cfg.FLUID['glycol_fraction']*100:g}% is the mixture the racks are designed for.

The store itself is in no danger. With the pods off in the design winter it cools by about {c['idle']['rate']:.0f} K a day.

### 9.11 Heat through the walls and from the surface

| Path | Heat | Note |
| --- | ---: | --- |
| Outer wall to the outside air, winter design | {c['outer_loss']['winter']/1e3:,.0f} kW | {c['outer_loss']['winter']/th.LOAD*100:.1f}% of the load. It helps the coolers and is left out of the balance. |
| Outer wall, yearly mean | {c['outer_loss']['mean']/1e3:,.0f} kW | |
| Inner wall into the bore | {inner['heat']/1e3:,.0f} kW | with the bore at {t['bore_air_c']:g} °C. {inner['per_k']/1e3:.1f} kW for each kelvin between store and bore. |
| Surface of the store, if open | about {ev['heat']/1e3:,.0f} kW and {ev['rate']*86.4:.0f} t of water a day | pool formula for still air over {ev['surface']:.0f} m² at {th.HOT:.0f} °C |

Two requirements follow.

- **The bore needs ventilation** that removes about {inner['heat']/1e3:.0f} kW from the walls, as well as what the pods give to the air, to hold {t['bore_air_c']:g} °C.
- **The top of the store has to be closed**, with a breather. An open surface would lose water every day, which thickens the glycol, and would put that water into the power levels above. From revision F the model has a sealed deck over the store, {t['cover']['below_rim_m']*1000:.0f} mm below the rim, with a breather through the outer wall.

### 9.12 Temperatures for the design of the walls

The outer wall has the store on one face and the weather on the other. The severe case is the winter design day with wind, with warm liquid against the wall. The warm layer can stand anywhere up the wall, so {th.HOT:.0f} °C is used at every lift. The table uses the walls of check 3, to show the effect of thickness. The outer wall as adopted is {cfg.SILO['outer_wall_m']*1000:.0f} mm throughout, as lifts 6 to 10 here.

| Lift | Thickness, mm | Heat flow, W/m² | Wet face, °C | Outside face, °C | Difference across the wall, K | Outside face if insulated, °C | Difference if insulated, K |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{wall_rows}

- **Outer wall.** About {min(l['bare']['gradient'] for l in c['lifts']):.0f} to {max(l['bare']['gradient'] for l in c['lifts']):.0f} K across the wall in winter if it is not insulated, and {min(l['clad']['gradient'] for l in c['lifts']):.0f} to {max(l['clad']['gradient'] for l in c['lifts']):.0f} K if it is. The wall cannot curve to suit, so the outside face is stretched. Section 10.9 gives what this does to the hoop bars of each option.
- **Inner wall.** The store is at {th.MEAN:.0f} °C on average and the bore at {t['bore_air_c']:g} °C. The difference across the wall is {inner['wall']['gradient']:.0f} K and the concrete is at {inner['wall']['mean']:.0f} °C on average.
- **Both walls and the liner** are at {th.COLD:.0f} to {th.HOT:.0f} °C on the wet face for the life of the plant.

**The inner wall has to be thicker than check 3 found.** Concrete creeps faster when warm. Check 3 took a creep coefficient of {cr['cold']:g}. At {inner['wall']['mean']:.0f} °C it is about {cr['warm']:.1f}, by the rule for warm concrete in the fib Model Code 2010. Creep sets the buckling pressure of the inner wall: at {inner['t']*1000:.0f} mm the design buckling pressure falls to {cr['design']/1000:.0f} kPa against {cr['demand']/1000:.0f} kPa. **The inner wall becomes {cr['t']*1000:.0f} mm.** Section 10 uses this thickness.

### 9.13 Movement of the walls against the steel inside them

The walls warm with the store. The shaft and the pods stand in the bore air. From {t['erection_temperature_c']:g} °C:

| Movement | Value | Note |
| --- | ---: | --- |
| Inner wall rises at the top pod level, {mv['top_pod']:.1f} m | {mv['wall_pod']*1000:.1f} mm | wall at {mv['wall_mean']:.0f} °C on average |
| Shaft rises at the same level | {mv['shaft_pod']*1000:.1f} mm | bore at {t['bore_air_c']:g} °C |
| Difference at the top pod level | {(mv['wall_pod']-mv['shaft_pod'])*1000:.1f} mm, and up to {mv['wall_pod']*1000:.1f} mm while the store is warm and the bore is still cold | wall sleeve against pod tip |
| Inner wall and shaft at the support rig, {st.SHAFT_TOP:.1f} m | {mv['wall_rig']*1000:.1f} mm and {mv['shaft_rig']*1000:.1f} mm | the collar must let the shaft slide by the difference, as check 1 already asks |
| Bore radius grows with temperature | {mv['bore']*1000:.1f} mm | |
| Bore radius shrinks under the liquid, lowest pod level | {sq[1]['elastic']*1000:.1f} mm at once, {sq[1]['creep']*1000:.1f} mm with creep | inner wall of {cr['t']*1000:.0f} mm |
| Bore radius shrinks under the liquid, top pod level | {sq[cfg.LEVELS]['elastic']*1000:.1f} mm at once, {sq[cfg.LEVELS]['creep']*1000:.1f} mm with creep | |
| A pod grows in length | {mv['pod']*1000:.1f} mm | |

These are the same size as the {st.TIP['single_mm']:g} mm and {st.TIP['accumulated_mm']:g} mm limits on the movement of a pod tip. The flexible section of each wall connection is sized for them (section 3.8).

### 9.14 Verification

| Check | Value | Independent value | Agreement |
| --- | ---: | ---: | --- |
| Cooler model at its rating condition | {th.cooler(t['cooler_rating']['liquid_in_c'], t['cooler_rating']['air_in_c'])[0]/1e6:.3f} MW, liquid out at {th.cooler(t['cooler_rating']['liquid_in_c'], t['cooler_rating']['air_in_c'])[1]:.1f} °C | {cfg.COOL['cooler_capacity_mw']:.3f} MW, {t['cooler_rating']['liquid_in_c']-th.RISE:.1f} °C | equal |
| Heat rejected by {th.INSTALLED} coolers at the layered limit of {lim[th.INSTALLED, False]:.1f} °C | {th.stratified_capacity(lim[th.INSTALLED, False])/1e6:.2f} MW | heat to reject, {th.LOAD/1e6:.2f} MW | equal |
| Layered limit less mixed limit, {th.DUTY} coolers at rated flow | {lim[th.DUTY, False]-lim[th.DUTY, True]:.1f} K | rise across the pods, {th.RISE:g} K | close. The liquid flow of a cooler differs between the two cases. |
| Ride-through of the adopted store, by hand | {th.FOM:g} × {rf.C['proposed']['volume']:,.0f} m³ × {th.CAPACITY/1e6:.3f} MJ/m³·K × {th.RISE:g} K ÷ {th.LOAD/1e6:.2f} MW = {th.FOM*rf.C['proposed']['volume']*th.CAPACITY*th.RISE/th.LOAD/60:.1f} min | {p['layered']/60:.1f} min | equal |
| Heat flow through the lowest lift | {c['lifts'][0]['bare']['flux']:.1f} W/m² overall | {c['lifts'][0]['bare']['gradient']*th.CONCRETE['conductivity_w_mk']/c['lifts'][0]['t']:.1f} W/m² through the concrete alone | equal |

The first, second and fifth are checked at every build by [thermal.py](../gpu_silo/thermal.py).

### 9.15 Conclusion

The balance closes: {th.INSTALLED} coolers of {cfg.COOL['cooler_capacity_mw']:g} MW reject the {th.LOAD/1e6:.2f} MW in outside air up to {lim[th.INSTALLED, False]:.0f} °C, and the store carries the plant for {p['layered']/60:.0f} minutes with no coolers at all. Both statements hold only for a layered store, with the pods fed from the bottom and the coolers from the top. A mixed store falls short by {th.RISE:g} K, which the weather cannot be relied on to give back.

The check also finds that the fill level has to allow {sw['to_hot']*1000:.0f} mm for the liquid to swell, that the store has to be closed at the top, that stopped coolers need protecting below {fz['freeze']:g} °C, and that the inner wall has to be {cr['t']*1000:.0f} mm because warm concrete creeps more.

The confidence in these results is limited by the assumptions in section 9.2. The air temperatures, the CDU approach and the cooler rating each move the limit kelvin for kelvin.

### 9.16 Thermal interfaces and commissioning evidence

1. **The site's weather.** Hours above the limit, and the coldest and hottest days.
2. **The design of the layering.** The pipes, their openings and the control of the two flows. A flow model or a test should confirm the {th.FOM*100:.0f}%.
3. **Hydraulics.** Pump heads, pipe sizes, and priming of the coolers, which stand beside the store and partly above mid-height.
4. **Selection of the CDU and the cooler** from suppliers, including the high air speed through the coolers noted in the design calculations.
5. **Start-up and upsets.** Warming the store from cold, the loss of some pods or some coolers, and the supply of power to the coolers and pumps when the turbines stop.
6. **The liquid over time.** The life of the glycol and its inhibitors at {th.HOT:.0f} °C, and of the liner in it.
7. **Heat from the turbine level** into the top of the store and the bore.
"""


def reinforcement_section():
    r, t, W = rf.C, th.C, walls.W
    schemes = r["schemes"]
    carbon, stainless, gfrp, high = (schemes[k] for k in ("carbon", "stainless", "gfrp", "gfrp_high"))
    p = r["proposed"]
    first, last = p["lifts"][0], p["lifts"][-1]
    cf = r["cfrp"]
    def stress_basis(s):
        scheme, limits = s["scheme"], s["limits"]
        if limits["service"]: return f"{limits['service']/1e6:.0f}, the ACI 350 rule"
        if limits["sustained"]: return f"{limits['sustained']/1e6:.0f}, against creep rupture"
        return f"{min(l['stress'] for l in s['lifts'][:-1])/1e6:.0f} to {max(l['stress'] for l in s['lifts'])/1e6:.0f}, by the crack limit"
    option_rows = "\n".join(
        f"| {'**' if s is p else ''}{s['scheme']['name']}{'**' if s is p else ''} | {s['scheme']['bar']} | {stress_basis(s)} | {s['lifts'][0]['bars']['provided']*1e6:,.0f} | "
        f"{s['lifts'][0]['bars']['layers']} of {s['lifts'][0]['bars']['bar']['name']} at {s['lifts'][0]['bars']['spacing']*1000:.0f} | "
        f"{'**' if s is p else ''}{s['lifts'][0]['t']*1000:.0f}{'' if len(s['thicknesses'])==1 else ' to ' + format(s['lifts'][-1]['t']*1000, '.0f')}{'**' if s is p else ''} | "
        f"{min(l['crack'] for l in s['lifts'][:-1])*1000:.2f} to {s['crack']*1000:.2f} | {'Yes' if s['meets_crack'] else 'No'} | {s['growth']*1000:.0f} | {s['bar_mass']/1e3:,.0f} | {s['heaviest']/1e3:.0f} | {s['volume']:,.0f} |"
        for s in schemes.values())
    lift_rows = "\n".join(
        f"| {l['lift']} | {l['pressure']/1000:.0f} | {kn(l['tension'],0)} | **{l['t']*1000:.0f}** | {l['bars']['layers']} layers of {l['bars']['bar']['name']} at {l['bars']['spacing']*1000:.0f} mm | {l['bars']['provided']*1e6:,.0f} | "
        f"{l['ratio']*100:.1f}% | {l['stress']/1e6:.0f} | {l['use']:.2f} | {l['crack']*1000:.2f} | {l['growth']*1000:.0f} | {l['cage']/1e3:.1f} |"
        for l in p["lifts"])
    winter_rows = "\n".join(
        f"| {s['scheme']['name']} | {s['lifts'][0]['winter']['bare']['gradient']:.0f} | {s['lifts'][0]['stress']/1e6:.0f} | +{s['lifts'][0]['winter']['bare']['extra']/1e6:.0f} | "
        f"{s['lifts'][0]['winter']['bare']['stress']/1e6:.0f} | {s['lifts'][0]['winter']['bare']['crack']*1000:.2f} | +{s['lifts'][0]['winter']['clad']['extra']/1e6:.0f} | {s['vertical']['stress']/1e6:.0f} |"
        for s in schemes.values())
    foot = p["foot"]
    span = cfg.COOL["anchor_columns_m"][-1] - cfg.COOL["anchor_columns_m"][0]
    arc = 2 * math.pi * (walls.R_OUT - first["t"] / 2) / rf.SEGMENTS
    wc = walls.C
    return f"""## 10. Reinforcement of the outer wall: options

### 10.1 Purpose

Check 3 reinforced the outer wall with ordinary carbon steel bars and found a wall of {carbon['lifts'][0]['t']*1000:.0f} mm at the base with {carbon['lifts'][0]['bars']['layers']} layers of bars. The project asked whether a different bar would let the wall be thinner: stainless steel or a high-strength fibre-reinforced polymer (FRP), with cost not a consideration, and with cages made up off the wall and dropped in. This section compares the options, using the temperatures of check 5. Stainless steel was proposed in revision E and adopted by the project in revision F. Every number is calculated by [reinforcement.py](../gpu_silo/reinforcement.py).

### 10.2 What sets the thickness

The outer wall is a tie. The concrete cracks and the bars carry all of the hoop tension. The wall has to be thick enough to hold the bars and to be built, and no thicker. So the thickness follows the bar area, and the bar area follows the stress the bar is allowed in service. Four things can limit that stress:

1. **Strength.** Design strength of the bar against 1.4 times the tension.
2. **The durability rule of ACI 350**, which holds ordinary bars to {W['service_steel_stress_mpa']} MPa in direct tension so that cracks stay fine enough to protect them and to hold liquid.
3. **The crack that the liner can bridge.** The liner is the liquid barrier here, and it is sprayed before the store is filled, so every crack opens underneath it.
4. **For FRP, creep rupture.** A glass bar under load for years breaks at a fraction of its short-term strength.

The stiffness of the bar then decides how wide the cracks are and how far the wall stretches at a given stress. Steel, of either kind, is 200 GPa. Glass FRP is 45 to 60 GPa.

In check 3, rule 2 governed: {W['service_steel_stress_mpa']} MPa is a third of the strength of the bar. That is why the wall is thick. **The thickness comes from the reinforcement, so the reinforcement is worth changing.**

### 10.3 The limit common to every option

Rule 3 applies whatever the bar is made of. The crack width limit is taken as **{rf.CRACK*1000:.2f} mm**, the value ACI 224R-01 Table 4.1 gives as reasonable for a member with a protective membrane. Crack widths are estimated as in check 3, by ACI 224.2R, with the stress scaled to the stiffness of the bar and a bond factor of {gfrp['scheme']['bond']:g} for FRP.

The liner specification should ask for more than this, because crack widths scatter: bridging of a new crack of 1.25 mm (class A4 of EN 1062-7), shown at {th.HOT:.0f} °C and after ageing in warm glycol.

### 10.4 The options compared

| Option | Bar | Stress in service, MPa | Bar area at the base, mm²/m | Hoop bars at the base, mm | Wall, base to top, mm | Crack width, mm | Within {rf.CRACK*1000:.2f} mm | Radius grows, mm | Bars in the outer wall, t | Heaviest lift, t | Store, m³ |
| --- | --- | --- | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
{option_rows}

All four use the inner wall of {r['inner']*1000:.0f} mm from section 9.12. The masses are for hoop and vertical bars in the outer wall, without the foot, openings, laps or couplers. The growth of the radius is that of the bars alone, with no help from the concrete between cracks, so it is an upper estimate.

![One metre of the lowest lift for each option](figures/wall_options.svg)

### 10.5 Carbon steel

This is check 3. It is the only option that follows ACI 350 as written. It gives the thickest wall and the most layers.

Carbon steel could be designed to the crack limit of section 10.3 in place of rule 2, and the wall would come out the same as the stainless one. It is not adopted. The cracks pass through the wall, so they are open to rain on the outside face whatever the liner does on the inside, and ordinary bars crossing cracks of 0.4 mm in the weather will corrode. Rule 2 exists to prevent that.

### 10.6 Stainless steel: adopted

**Bar.** ASTM A955 Grade 75 (520 MPa yield) in a duplex alloy such as UNS S32304. It has the stiffness and ductility of ordinary bar, it is cut, bent and coupled in the same way, with tooling kept for stainless, and it is rolled in the same sizes up to #11.

**Design.** Strength to ACI 318-19: design strength 0.9 f<sub>y</sub> against {W['fluid_load_factor']:g} times the tension. Then the bar area is increased until the crack width is within {rf.CRACK*1000:.2f} mm. The crack limit governs at every lift but the top one, so the bars work at {min(l['use'] for l in p['lifts'][:-1])*100:.0f} to {max(l['use'] for l in p['lifts'])*100:.0f}% of their design strength.

| Lift | Pressure, kPa | Hoop tension, kN/m | Thickness, mm | Hoop bars | Provided, mm²/m | Ratio | Stress in service, MPa | Share of design strength used | Crack width, mm | Radius grows, mm | Bars in the lift, t |
| ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{lift_rows}

**Result.** The outer wall is **{first['t']*1000:.0f} mm for its whole height**, with **two layers of hoop bars**, one at each face. The thickness is set by the room the bars need: {W['cover_mm']} mm cover, a #11 hoop bar and a vertical bar at each face, and a {W['core_mm']} mm core. There are no steps, so the jumpform keeps one setting.

**Departure from ACI 350.** This design does not apply the durability factor of ACI 350 (rule 2). The reasons are that the liner, not the concrete, holds the liquid, and that the bars do not corrode. It is a departure from the standard named in the basis of design, and the checker and the authority have to agree to it. It is open item 4.

**Foot of the wall.**

| Quantity | Value | Basis |
| --- | ---: | --- |
| Moment at the foot | {kn(foot['moment'],0)} kN·m/m | long cylinder with a fixed foot, unfactored. A thinner wall attracts less than the {kn(wc['foot']['moment'],0)} kN·m/m of check 3. |
| Vertical bars on the store face | {foot['vertical']*1e6:,.0f} mm²/m: {foot['bars']['layers']} layer of {foot['bars']['bar']['name']} at {foot['bars']['spacing']*1000:.0f} mm | strength |
| Factored shear against the most the section can carry | {kn(foot['vu'],0)} kN/m against {kn(foot['most'],0)} kN/m | ACI 318-19 Section 22.5 |
| Shear ties | {foot['ties']*1e6:,.0f} mm² for each square metre of wall | the concrete alone carries {kn(foot['vc'],0)} kN/m |

The foot works, with heavy shear ties in the lowest part of the first lift. A local thickening of the wall at its foot would lighten them and is worth drawing.

### 10.7 Glass FRP

**Bars to the code.** ACI CODE-440.11-22 covers glass FRP bars to ASTM D7957, with a modulus of {gfrp['scheme']['modulus_gpa']:g} GPa. A guaranteed strength of {gfrp['scheme']['strength_mpa']} MPa is taken for the larger sizes. The stress under sustained load is limited to {gfrp['scheme']['sustained_fraction']:g} of the design strength, which is {gfrp['limits']['sustained']/1e6:.0f} MPa. The liquid load is sustained for the life of the store. So the code allows glass bars the same stress as rule 2 allows ordinary steel, and the bar area is the same. But the bar has less than a quarter of the stiffness:

- cracks of {min(l['crack'] for l in gfrp['lifts'])*1000:.1f} to {gfrp['crack']*1000:.1f} mm, against a limit of {rf.CRACK*1000:.2f} mm;
- the radius grows by {gfrp['growth']*1000:.0f} mm;
- the largest bar is #10, so the base needs {gfrp['lifts'][0]['bars']['layers']} layers, and the wall is {gfrp['lifts'][0]['t']*1000:.0f} mm;
- to meet the crack limit would take {gfrp['for_crack']*1e6:,.0f} mm² of bar a metre at the base, which cannot be placed.

**High-modulus bars.** Bars of {high['scheme']['modulus_gpa']:g} GPa and {high['scheme']['strength_mpa']:,} MPa are made, but ACI CODE-440.11-22 does not cover them. By the same method they could work at {high['limits']['sustained']/1e6:.0f} MPa. The wall comes down to {high['lifts'][0]['t']*1000:.0f} mm at the base and {high['lifts'][-1]['t']*1000:.0f} mm above, but the cracks are {min(l['crack'] for l in high['lifts'][:-1])*1000:.1f} to {high['crack']*1000:.1f} mm and the radius grows by {high['growth']*1000:.0f} mm.

**Other matters**, each of which counts against FRP in this wall:

1. **Temperature.** The wall is at {th.COLD:.0f} to {th.HOT:.0f} °C for life. ASTM D7957 qualifies a bar's resistance to alkali by 90 days at 60 °C and accepts the loss of a fifth of its strength. The store would hold the bars close to that test temperature permanently, under load. The limits in the code were not derived for that.
2. **Splices.** No coupler in general use develops the strength of a glass bar. The hoops would be closed by laps. For steel, ACI 318-19 Section 25.5.7.4 does not allow lap splices in a tension tie, which is what this wall is.
3. **No yield.** FRP is elastic until it breaks. Stresses from temperature and restraint add directly to the stress that breaks it. In steel they are shed by yielding.
4. **Fabrication.** The bars cannot be bent on site. Every hoop is made curved at the factory.
5. **Fire.** The resin softens at about 100 °C.

**Conclusion on glass FRP.** It does not suit the outer wall. Its strength cannot be used, because the load is permanent, and its low stiffness opens cracks three to four times wider than the liner limit. It could suit the **inner wall**, which is in compression and has only the least reinforcement, as light cages. That would need the fire case for the bore to be settled first.

### 10.8 Carbon FRP

Carbon FRP is strong and does not creep to rupture as glass does, but it is less stiff than steel, about {rf.R['cfrp']['modulus_gpa']:g} GPa. To hold the same crack width as the stainless design the bars could work at only {cf['stress']/1e6:.0f} MPa, {cf['ratio']*100:.0f}% of their strength, and the base would need {cf['area']*1e6:,.0f} mm² a metre. Bars are commonly made only up to about {cf['bar']}, of which four layers at {W['min_bar_spacing_mm']} mm give {cf['most']*1e6:,.0f} mm² a metre. The ACI code and the ASTM specification used here cover glass bars only. Carbon FRP is not readily available as bar and it does not make the wall thinner.

### 10.9 Temperature

On the winter design day the outside face is {t['lifts'][0]['bare']['gradient']:.0f} K or so colder than the wet face (section 9.12). A ring cannot curve, so the bars at the cold face are stretched further and those at the wet face are relieved. In a wall cracked through, the change in bar stress is E α ΔT times the distance of the bar from the middle of the wall over the thickness.

| Option | Difference across the lowest lift, K | Bar stress from the liquid, MPa | Change at the outside face, not insulated, MPa | Outside face in winter, MPa | Crack at the outside face, mm | Change if insulated, MPa | Vertical bars from the same cause, MPa |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{winter_rows}

- **Carbon steel** goes over its {W['service_steel_stress_mpa']} MPa limit by up to {max(l['winter']['bare']['stress'] for l in carbon['lifts'])/walls.FS*100-100:.0f}%. It would need that much more hoop steel at the outside face, or insulation.
- **Stainless steel** reaches {first['winter']['bare']['stress']/1e6:.0f} MPa at the outside face, {first['winter']['bare']['stress']/(p['scheme']['strength_mpa']*1e6)*100:.0f}% of yield, and the crack there opens to {max(l['winter']['bare']['crack'] for l in p['lifts'])*1000:.2f} mm. That face has no liner and the bars do not corrode, so this is accepted. The crack at the liner closes a little in winter.
- **The least vertical reinforcement** is enough for the bending up the wall from the same cause.

**The outer wall does not need insulating if its bars are stainless.** Insulation would remove most of the effect, but it is another trade working at height round the cooler frames, and the heat it would save is heat the coolers are there to reject. In summer the difference across the wall is small and can reverse in the sun, by a few kelvin.

### 10.10 Cages

Cages made up off the wall and lifted in help with any bar. They take the bar fixing off the critical path of the lift, which is where check 3 found the programme was exposed.

| | Carbon steel | Stainless steel | Glass FRP, to the code |
| --- | ---: | ---: | ---: |
| Layers of hoop bars in the lowest lift | {carbon['lifts'][0]['bars']['layers']} | {first['bars']['layers']} | {gfrp['lifts'][0]['bars']['layers']} |
| Bars in the lowest lift of the outer wall | {carbon['heaviest']/1e3:.0f} t | {p['heaviest']/1e3:.0f} t | {gfrp['heaviest']/1e3:.0f} t |
| One cage, with the lift in {rf.SEGMENTS} | {carbon['heaviest']/1e3/rf.SEGMENTS:.1f} t | **{p['heaviest']/1e3/rf.SEGMENTS:.1f} t** | {gfrp['heaviest']/1e3/rf.SEGMENTS:.1f} t |

An FRP cage is lighter, but lightness is not what limits a cage here. A stainless cage for one eighth of the lowest lift is {arc:.1f} m round the curve, {walls.LIFT:g} m high and {p['heaviest']/1e3/rf.SEGMENTS:.1f} t, with one layer of hoops at each face. That is an easy lift for the cranes on site and a simple cage to make. The hoop bars are joined between cages with couplers that can join two bars already in place, staggered. With carbon steel the same cage has four layers and twice the weight.

### 10.11 The walls with stainless reinforcement

| Quantity | As first drawn | Check 3, carbon steel | Adopted, stainless steel |
| --- | ---: | ---: | ---: |
| Outer wall | {wc['present']['outer']*1000:.0f} mm | {wc['lifts'][0]['t']*1000:.0f} mm to {wc['lifts'][-1]['t']*1000:.0f} mm, in {len(set(l['t'] for l in wc['lifts']))} steps | **{first['t']*1000:.0f} mm throughout** |
| Layers of hoop bars | | up to {max(l['bars']['layers'] for l in wc['lifts'])} | **{p['layers']}** |
| Inner wall | {wc['present']['inner']*1000:.0f} mm | {wc['inner']['t']*1000:.0f} mm, {r['inner']*1000:.0f} mm after check 5 | **{r['inner']*1000:.0f} mm** |
| Width of the store | {cfg.WALL_GAP:.2f} m | {carbon['lifts'][0]['radius']-walls.R_BORE-r['inner']:.2f} m to {carbon['lifts'][-1]['radius']-walls.R_BORE-r['inner']:.2f} m | {first['radius']-walls.R_BORE-r['inner']:.2f} m |
| Volume of the store | {wc['now_volume']:,.0f} m³ | {carbon['volume']:,.0f} m³ | **{p['volume']:,.0f} m³** against a target of {wc['target']:,.0f} m³ |
| Ride-through, layered | {t['rides']['drawn']['layered']/60:.0f} min | {carbon['ride']['layered']/60:.0f} min | **{p['ride']['layered']/60:.0f} min** |
| Concrete in the walls | {wc['now_concrete']:,.0f} m³ | {carbon['total_concrete']:,.0f} m³ | **{p['total_concrete']:,.0f} m³** |
| Bars in the outer wall | | {carbon['bar_mass']/1e3:,.0f} t | **{p['bar_mass']/1e3:,.0f} t** |
| Bars in the lowest lift of the outer wall | | {carbon['heaviest']/1e3:.0f} t | **{p['heaviest']/1e3:.0f} t** |
| Crack width under the liner | | {carbon['crack']*1000:.2f} mm | {p['crack']*1000:.2f} mm |

The carbon steel column uses the {r['inner']*1000:.0f} mm inner wall, so that the three can be compared. Its store is smaller than the {wc['volume']:,.0f} m³ in section 8.8 for that reason.

### 10.12 What the design depends on

1. **Agreement to the departure from ACI 350** (section 10.6).
2. **The liner.** It has to bridge new cracks of {p['crack']*1000:.1f} mm, and wider ones with a margin, at {th.HOT:.0f} °C in glycol, for life. If the supplier cannot show this, the crack limit comes down and the bars go up: at {W['min_bar_spacing_mm']} mm spacing two layers of #11 give a crack of about {r['tightest']*1000:.2f} mm in the same {first['t']*1000:.0f} mm wall. Below that the wall thickens again.
3. **The wall stretches when the store is first filled.** The radius grows by about {p['growth']*1000:.0f} mm, which is {first['strain']*1e3:.2f} mm in every metre round the wall. Whatever is fixed to the outer wall over a length has to allow for it or be fixed after the first fill. A cooler frame is anchored over {span:g} m, which stretches by {first['strain']*span*1000:.0f} mm. With carbon steel it would be {carbon['lifts'][0]['strain']*span*1000:.0f} mm.
4. **Anchors in cracked concrete.** The cast-in mounts and anchors of checks 9 and 10 and of the cooler frames sit in a wall with cracks of about 0.4 mm, and are to be designed for that.
5. **Supply.** Stainless #8 to #11 bar in Grade 75, and couplers for it, are standard products but are usually made to order. The lead time belongs in the programme.
6. **The first fill is the proof test.** The stretch of the wall and the cracks should be measured as the store is filled, in stages.

### 10.13 Conclusion

The thickness of the outer wall is set by its reinforcement, and by one rule: the {W['service_steel_stress_mpa']} MPa that ACI 350 allows an ordinary bar in direct tension. Stainless steel bars make it reasonable to set that rule aside, because they do not corrode at a crack and the liner holds the liquid. Designed for strength and for the crack the liner can bridge, **the outer wall is {first['t']*1000:.0f} mm for its whole height with two layers of bars, where carbon steel needs {carbon['lifts'][0]['t']*1000:.0f} mm and four layers at the base.**

FRP does not do the same. Glass is too flexible and cannot use its strength under a permanent load. Carbon is not stiff enough either and is not readily available.

Cages are worth having with stainless bars: eight to a lift, about {p['heaviest']/1e3/rf.SEGMENTS:.0f} t each at the base.

**These walls were adopted by the project in revision F.** The design file, the model and the calculations use an outer wall of {first['t']*1000:.0f} mm and an inner wall of {r['inner']*1000:.0f} mm.
"""


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
    plant_level = cfg.PROJECT["diesel"]["set_height_m"]
    W, wc = walls.W, walls.C
    first, last, inner, foot = wc["lifts"][0], wc["lifts"][-1], wc["inner"], wc["foot"]
    outer_rows = "\n".join(
        f"| {l['lift']} | {l['z0']:.1f} | {l['pressure']/1000:.0f} | **{l['t']*1000:.0f}** | {kn(l['tension'],0)} | {l['need']*1e6:,.0f} | "
        f"{l['bars']['layers']} layers of {l['bars']['bar']['name']} at {l['bars']['spacing']*1000:.0f} mm | {l['bars']['provided']*1e6:,.0f} | {l['ratio']*100:.1f}% | {l['stress']/1e6:.0f} | {l['crack']*1000:.2f} |"
        for l in wc["lifts"])
    options = []
    for limit, sizes in ((st.LIMIT, None), (st.LIMIT, (1.5,)), (st.LIMIT, (2,)), (.004, None), (.004, (2,))):
        truss = st.lightest(limit)
        wall = next(w for w in sh["walls"] if (w["section"]["wall_in"] in sizes if sizes else w is ch))
        total = truss["tip"] + wall["movement"]["total"]
        extra = (truss["steel"] - d["steel"]) * cfg.TOTAL / 1000 + (wall["mass"] - ch["mass"]) / 1000
        options.append(f"| {truss['chord']['name']} and {truss['web']['name']} | {st.inches(wall['section']['wall_in'])} | {truss['tip']*1000:.2f} | {wall['movement']['total']*1000:.2f} | "
                       f"{total*1000:.2f} | {(st.ACCUMULATED-total)*1000:.2f} | {'as designed' if extra < .01 else f'{extra:.0f}'} |")
    budget_rows = "\n".join(options)
    seq, unc, comp = cases["sequence"], cases["uncontrolled"], cases["complete"]
    fx = cn.C["flexible"]
    flex_rows = "\n".join(
        "\n".join([f"| *{title}* | | |"] + [f"| {name} | {value*1000:.1f} | {where} |" for name, value, where in fx[key]] + [f"| Sum | **{sum(v for _, v, _ in fx[key])*1000:.1f}** | |"])
        for key, title in (("down", "Tip lower than the sleeve"), ("up", "Tip higher than the sleeve"), ("closes", "Gap closes"), ("opens", "Gap opens")))
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
| C | 2026-11-22 | Limits on tip movement set by the project: {st.TIP['single_mm']:g} mm from any one part and {st.TIP['accumulated_mm']:g} mm accumulated. Support rig steel set straight after the cage, generator sets landed on it later. Turbine level given its own mounts and cast-in anchors, as check 10. |
| D | 2026-11-22 | Check 3 carried out for the liquid load: walls without post-tensioning, in {walls.W['concrete_fc_mpa']} MPa concrete, with the liner as the liquid barrier. Thicknesses proposed, not yet adopted in the model. |
| E | 2026-11-22 | Check 5 carried out, first pass: the store has to be layered. Inner wall raised to {th.C['creep']['t']*1000:.0f} mm for creep in warm concrete. Reinforcement of the outer wall compared: stainless steel proposed, which makes the outer wall {rf.C['proposed']['lifts'][0]['t']*1000:.0f} mm throughout. |
| F | 2026-11-22 | Decisions of the project adopted: outer wall {cfg.SILO['outer_wall_m']*1000:.0f} mm with stainless steel bars, inner wall {cfg.SILO['inner_wall_m']*1000:.0f} mm, the store layered, the CDU with a heat exchanger, and the assumed range of outside air. The store pipes, the cover and the overflow are in the model. |
| G | 2026-11-22 | Check 4 carried out on assumed ground: the slab as drawn is adequate, the shaft base is designed to stand alone, and the fill settles the walls against the shaft. Check 6 carried out, first pass: root connection, hub, bearings and drive. Allowance for the hub raised to {st.SHAFT['hub_and_floor_t_per_level']:g} t. A thicker shaft wall proposed for the accumulated limit. |
| H | 2026-11-22 | Check 4 corrected. The springs of revision G were values for a small test plate and were about ten times too stiff for soil under a slab this wide. The grounds are now set by modulus: settlement on soil is tens of millimetres, the fill lowers the walls {(fd.C['chosen']['settle']['fill_inner']-fd.C['chosen']['settle']['fill_shaft'])*1000:.0f} mm against the shaft on {fd.F['design_ground']}, and the slab as drawn is not strong enough on dense sand or stiff clay. |
| I | 2026-11-22 | Decisions of the project adopted: shaft wall {st.inches(st.C['shaft']['chosen']['section']['wall_in'])} in, base slab {fd.C['drawn']:g} m on ground taken as {fd.F['design_ground']}, a flexible section in each wall connection, and the hub arrangement of check 6. The build is not to be constrained: the wall connections are not left until after the fill, and the order of loading stays free. The model draws the hub drum, beam arms at the pod roots and the flexible sections. |
| J | 2026-11-22 | Crown floor girders, sliding shaft guide, separate anchor groups, reference lateral and services envelopes, recorded owner assumptions and the operating IFC. |
| K | 2026-11-23 | Checks 7–10 verified on the revision J loading basis. Added erection combinations, directional guide play, individual stud and closure weld checks, and revised the crown anchor bars for clearance and development. |

This report is generated from [project.json](project.json) by `python -m gpu_silo calcs`. Section 2 reads the numbered checks from `design_checks.register`. Sections 7.5–7.8 use the [coordination calculations](../gpu_silo/completion.py) and the [crown anchorage detail](../gpu_silo/crown_detail.py).

## Contents

1. [Purpose and scope](#1-purpose-and-scope)
2. [Register of design checks](#2-register-of-design-checks)
3. [Basis of design](#3-basis-of-design)
4. [Check 2: pod truss](#{ANCHORS['4']})
5. [Check 1: central shaft](#{ANCHORS['5']})
6. [Check 6: root connection and level drive, design loads](#{ANCHORS['6']})
7. [Checks 7 to 10: support rig, shaft connector and wall mounts, design loads](#{ANCHORS['7']})
8. [Check 3: silo walls](#{ANCHORS['8']})
9. [Check 5: heat balance of the store](#{ANCHORS['9']})
10. [Reinforcement of the outer wall: options](#10-reinforcement-of-the-outer-wall-options)
11. [Check 4: foundation](#{ANCHORS['11']})
12. [Check 6: root connection, hub and level drive](#{ANCHORS['12']})
13. [Assumptions and release conditions](#13-assumptions-and-release-conditions)
14. [Appendix A: member forces in the pod truss](#appendix-a-member-forces-in-the-pod-truss)
15. [Appendix B: section properties](#appendix-b-section-properties)

## 1. Purpose and scope

The GPU Silo stores {cfg.TOTAL} {cfg.NAME} pods on {cfg.LEVELS} levels round a central steel shaft, inside a double-walled concrete silo. Each pod holds {st.RACKS} GPU racks with its own coolant distribution unit (CDU) and pump. The purpose of this report is to give confidence in the predicted performance of the structure by working through a fixed list of design checks, one at a time, and recording the basis, the method and the result of each.

This revision covers:

- the register of design checks and the basis of design;
- check 2, the pod trusses, sized for gravity load;
- check 1, the central shaft, sized for gravity load;
- the loads at the pod root and the rotating mass of a level, for check 6;
- the loads on the support rig, the shaft connector and the wall mounts of both power levels, for checks 7 to 10;
- check 3, the silo walls, for the liquid load;
- check 5, the heat balance of the store, as a first pass;
- a comparison of reinforcement for the outer wall, using the temperatures from check 5;
- check 4, the base slab and the anchorage of the shaft, on assumed ground;
- check 6, the root connection of a pod, the hub of a level and its drive, as a first pass.

Section 7.8 screens lateral loading against a stated reference envelope. Site-specific dynamic and geotechnical verification requires an identified site.

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
| Liquid-containing concrete | ACI 350-06, *Code Requirements for Environmental Engineering Concrete Structures*, to be confirmed against ACI 350-20 |
| Structural concrete | ACI 318-19, *Building Code Requirements for Structural Concrete* |
| Reinforcing bar | ASTM A615/A615M, Grade 60 |
| Crack width | ACI 224.2R, *Cracking of Concrete Members in Direct Tension*, and ACI 224R-01, *Control of Cracking in Concrete Structures* |
| Stainless reinforcing bar | ASTM A955/A955M, Grade 75 |
| Glass FRP reinforcement | ACI CODE-440.11-22 with bars to ASTM D7957/D7957M |
| Creep of warm concrete | fib *Model Code for Concrete Structures 2010* |
| Crack bridging of the liner | EN 1062-7 |
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

The tip of each pod carries the coupling that connects its CDU to the water-glycol store through a sleeve in the inner wall, so the vertical position of the tip matters. The project set two limits on its movement for revision C.

| Criterion | Limit |
| --- | ---: |
| Movement of a pod tip caused by any one part of the structure on its own | {st.TIP['single_mm']:g} mm |
| Movement of a pod tip accumulated over all the parts | {st.TIP['accumulated_mm']:g} mm |

Where the accumulated limit stands with the parts designed so far:

| Part | Tip movement, mm | Single limit, mm | Where |
| --- | ---: | ---: | --- |
| Pod truss, deflection under dead load | {c['budget']['truss']*1000:.2f} | {st.TIP['single_mm']:g} | section 4.5 |
| Shaft, shortening as the store is filled plus lean in the worst filling state | {c['budget']['shaft']*1000:.2f} | {st.TIP['single_mm']:g} | section 5.7 |
| Root connection, as designed | {cn.C['tip']['total']*1000:.2f}, with an allowance of {cn.C['budget']['root']*1000:g} | {st.TIP['single_mm']:g} | section 12.5 |
| Tilt of the hub on its bearings | allowance of {cn.C['budget']['hub']*1000:g} | {st.TIP['single_mm']:g} | section 12.7 |

The truss is the lightest that meets its own {st.TIP['single_mm']:g} mm. The shaft wall was first the lightest that met the shaft's own {st.TIP['single_mm']:g} mm, {st.inches(sh['lightest']['section']['wall_in'])} in, which left {(st.ACCUMULATED-c['budget']['truss']-sh['lightest']['movement']['total'])*1000:.1f} mm of the accumulated limit for the root connection and the hub. Check 6 found that they need {cn.C['budget']['need']*1000:.1f} mm. The project therefore set the shaft wall at {st.inches(ch['section']['wall_in'])} in, in revision I. Section 12.9 has the comparison of shaft walls.

| | mm |
| --- | ---: |
| Truss, shaft, root connection and tilt of the hub | **{cn.C['budget']['adopted']['total']*1000:.2f}** |
| Limit | {st.TIP['accumulated_mm']:g} |

### 3.8 The wall connection

Each pod is joined to its sleeve in the inner wall through **a section of flexible material**, by decision of the project in revision I. It takes up the movement between the pod, which hangs from the shaft, and the wall. Nothing in the build has to wait for the store to be filled, and the order in which pods are loaded is free.

| Movement of the pod tip against its sleeve | mm | Where |
| --- | ---: | --- |
{flex_rows}

| Requirement on the flexible section | Value | Basis |
| --- | ---: | --- |
| **Movement across the connection, up or down** | **± {fx['across']*1000:.0f} mm** | the larger sum above, times {cfg.PROJECT['structure']['wall_connection']['margin']:g} |
| **Movement along the connection** | **± {fx['along']*1000:.0f} mm** | the same |
| Flexible length needed | about {round(fx['length']*100)*10} mm | hose makers' rule for a sideways offset, with a bending radius of {cfg.PROJECT['structure']['wall_connection']['hose_bend_radius_mm']} mm. To be confirmed by a supplier. |
| Gap between the pod tip and the wall | {cfg.POD['tip_clearance_m']*1000:.0f} mm | so the flexible length runs back into the end of the pod, behind the plug |
| Liquid | {fx['temperature']:.0f} °C, {fx['pressure']/1000:.0f} kPa of head at the lowest level, and the pressure of the pump | |

The limits of {st.TIP['single_mm']:g} mm and {st.TIP['accumulated_mm']:g} mm in section 3.7 still apply to the structure. Settlement and temperature are outside them and are taken by the flexible section. The power and data connections of a pod pass through the shaft, not the wall, and are not affected.

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
| 1 | Tip deflection under dead load | {c['limit']*1000:g} mm | section 3.7, limit for one part |
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

### 4.11 Interfaces beyond the plane truss check

Revision J dispositions and release evidence for these interfaces are in the [assumption register](assumptions.md).

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
- The top of the shaft is held sideways by a connector to the support rig that carries the diesel generator sets. The steel of the rig is set on its wall mounts and connected to the shaft straight after the cage is lifted in, before any pod is hung. The generator sets are landed on it later.
- The connector, the rig and the mounts were added in revision B. The rig passes the force to mounts cast into the inner wall. The connector takes sideways force only, so the shaft is free to shorten under load and the weight of the rig does not come onto the shaft.
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
| 1 | Movement of a pod tip caused by the shaft | {sh['limit']*1000:g} mm on its own, and {st.TIP['accumulated_mm']:g} mm accumulated with the truss | section 3.7. Shortening under the full store plus lean in the worst state of the filling sequence. |
| 2 | Strength under axial load and bending | interaction ≤ 1.0 in all three loading states | AISC 360-22 Sections E3, F8 and H1 |
| 3 | Wall slenderness | D/t ≤ 0.11 E/F<sub>y</sub> = {.11*e_fy:.1f} | AISC 360-22 Table B4.1a, case 9. No slender wall in compression. |
| 4 | Member slenderness | L<sub>c</sub>/r ≤ {T['max_slenderness']} | AISC 360-22 Section E2, user note |

Strength is checked for the uncontrolled fill as well as for the planned sequence. This is a decision made in this report so that a mistake in the fill order cannot overload the shaft. It costs nothing, because criterion 1 governs. The movement limit is checked for the planned sequence only.

The thinnest plate in the list in the design file that meets all four is chosen.

The shaft is treated as one part: its shortening and its lean are added before they are compared with the limit for one part.

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

**Selected: {st.SHAFT_D*1000:.0f} mm outside diameter × {st.inches(sec['wall_in'])} in ({sec['wall']*1000:.1f} mm) wall.** The lightest wall that meets the shaft's own limits is {st.inches(sh['lightest']['section']['wall_in'])} in, where the movement limit governs. The project set {st.inches(sec['wall_in'])} in after check 6, to keep the accumulated movement of a pod tip within {st.TIP['accumulated_mm']:g} mm (section 12.9). Strength would be met by the thinnest plate in the list.

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

### 5.10 Why the support rig is set before the pods

The worst out-of-balance state occurs while the pods are being loaded. If the top of the shaft were free then:

| Selected tube, top free, worst state of the filling sequence | Value |
| --- | ---: |
| Moment at the base | {kn(abs(free_cases['sequence']['result']['base']),0)} kN·m |
| Sideways movement of the top of the shaft | {abs(free_cases['sequence']['result']['top'])*1000:.0f} mm |
| Tip movement from lean | **{free['movement']['lean_drop']*1000:.0f} mm** |
| Strength interaction, planned sequence | {free_cases['sequence']['ratio']:.2f} |
| Strength interaction, uncontrolled fill | {free_cases['uncontrolled']['ratio']:.2f} |

The shaft would not collapse, but the pods would be {free['movement']['lean_drop']*1000:.0f} mm out of level at their tips and the top of the shaft would be {abs(free_cases['sequence']['result']['top'])*1000:.0f} mm off the axis.

The programme was changed in revision C to prevent this. The steel of the support rig is fabricated on site on days {logistics.span('rigfab')[0]} to {logistics.span('rigfab')[1]}, the cage is lifted in on day {logistics.span('cage')[0]}, and the rig is set on its wall mounts and connected to the shaft on days {logistics.span('rig')[0]} to {logistics.span('rig')[1]}. The first pod is hung on day {logistics.span('pods')[0]}. The generator sets are landed on the rig on days {logistics.span('power')[0]} to {logistics.span('power')[1]}, with the turbine level and the lid. The programme check in [logistics.py](../gpu_silo/logistics.py) fails if the rig is not in before the pods.

The construction sequence seats the bare rig on its wall mounts before pod loading. The diesel sets and day tanks are lifted onto the rig after the pods.

### 5.11 Verification

| Check | Analysis | Independent value | Agreement |
| --- | ---: | ---: | --- |
| Top reaction for a single couple M at height a, against 3Ma(2L − a)/(2L³) | numerical integration | closed form | within 0.1%, checked at every build |
| Base moment against the sum of the couples less the top reaction times L, each loading state | {kn(abs(seq['result']['base']),1)} kN·m | {kn(abs(sum(m for _, m in seq['couples'])-seq['result']['reaction']*st.SHAFT_TOP),1)} kN·m | equal |
| Sideways movement of the held top | {abs(seq['result']['top'])*1e6:.3f} µm | 0 | equal |

### 5.12 Conclusion

A {st.SHAFT_D*1000:.0f} mm tube with a {st.inches(sec['wall_in'])} in ({sec['wall']*1000:.1f} mm) wall of A572 Grade 50 plate, fixed at its base and held at its top, carries the {cfg.TOTAL} pods with a highest strength interaction of {ch['ratio']:.2f}. The pod tips move {mv['total']*1000:.1f} mm against the limit of {sh['limit']*1000:g} mm, and this governs the wall. The shaft weighs {ch['mass']/1000:.1f} t.

The result depends on the top restraint. It needs a stiffness of at least {sh['needed']/1e6 if sh['needed'] else 0:.0f} kN/mm, and it is in place before the first pod is hung.

### 5.13 Interfaces beyond the shaft gravity check

1. **Lateral load.** Earthquake load on {cfg.TOTAL*c['pod_t']:,.0f} t of pods is likely to govern the shaft, its base, the connector, the rig and the mounts. It waits for the site.
2. **Local loads at the hubs.** Each hub puts {kn(c['level_weight']+hub*1000*st.G,0)} kN of weight and the pull and thrust of eight pod roots into the wall of the tube. Ring stiffeners or thicker cans at the hubs are to be designed with the hub under check 6.
3. **Openings.** The revision J shaft carries continuous MV bus to grade. The sidewall has no intermediate power apertures. Provide local end-entry fittings and independent optical joints.
4. **Base connection.** Anchor rods, base plate and the foundation under them are part of check 4.
5. **Plumb.** A shaft that is out of plumb tilts every pod. One part in a thousand moves a pod tip {st.TIP_R:.1f} mm. The hubs will have to be set level independently of the shaft, or the erection tolerance set to suit.
6. **Torsion.** The drive of a level reacts on the shaft. The torque is small (section 6.2) and is not checked.
7. **Temperature.** The steel shaft and the concrete wall may warm by different amounts. The effect on the tip couplings is not checked.
8. **Field splices** and the welding of the seams.

## 6. Check 6: root connection and level drive, design loads

These are the loads from the pods as now designed, unfactored. The shaft is fixed and each level turns on it. Section 12 designs the connection, the hub and the drive for them.

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

The inertia torque is small. The drive is sized by the friction of the hub bearing under the weight and the out-of-balance moment, and by holding a level against the lean of the shaft. Section 12.8 does this.

## 7. Checks 7 to 10: support rig, shaft connector and wall mounts, design loads

Checks 7, 8 and 9 were added in revision B and check 10 in revision C. Holding the top of the shaft makes the rig, its connector and its mounts part of the structure that carries the pods. Sections 7.1–7.4 preserve the design brief. Sections 7.5–7.8 give the crown checks and site screening on the revision J reference loads. Revision K verifies the staged floors, shaft guide and two separate groups of wall seats.

### 7.1 Description

- **Support rig (check 7).** The steel deck that carries the diesel generator sets: girders under the sets and a ring beam inside the wall, {cfg.POWER['floor_structure_m']:g} m deep, at {cfg.CROWN:.2f} m to {cfg.CROWN+cfg.POWER['floor_structure_m']:.2f} m above the foundation. It is set on its mounts straight after the cage, and the generator sets are landed on it later.
- **Shaft connector (check 8).** A collar round the top of the shaft with {st.RIG['arms']} arms out to the ring beam, in the depth of the rig. The shaft runs up into the collar and can slide in it, so the connector passes sideways force and nothing else.
- **Rig mounts (check 9).** {rig['mounts']} steel plates, {st.RIG['mount_plate_m'][0]:g} m × {st.RIG['mount_plate_m'][1]:g} m, cast flush into the bore face of the inner wall with studs into the concrete, evenly spaced round the ring beam and clear of the access wedge. They are set in the forms of the wall lift that contains them. They have to be flush for the cage to pass, so the rig carries a shoe at each mount that is welded to the plate once the rig is down.
- **Turbine level mounts and cast-in anchors (check 10).** The turbine level does not bear on the support rig. It has {rig['turbine_mounts']} mounts of its own of the same kind, {cfg.POWER['floor_structure_m']+plant_level:.2f} m higher, cast into the next wall lift. The rig has to pass these on its way down, which is a second reason for them to be flush.

### 7.2 Loads from the shaft on the rig, its connector and its mounts

| Loading state | Shaft service force, kN | Factored shaft force, kN | Ideal full-ring service share per governing mount, kN |
| --- | ---: | ---: | ---: |
{rig_rows}

The direction of the force changes as the levels turn during a lift, so every mount is taken to see the largest share. The force on one mount assumes that the ring beam spreads the force round all {rig['mounts']} mounts as a cosine distribution, which gives 2/n of the total on the most heavily loaded mount. There are no mounts in the access wedge, so the true share is somewhat higher and is calculated in section 7.7.

The inner wall carries these forces in addition to the pressure of the store behind it. That is to be included in check 3.

### 7.3 Gravity loads

| Item | Mass, t | Basis |
| --- | ---: | --- |
| Diesel generator sets | {cfg.PROJECT['diesel']['sets']*cfg.PROJECT['diesel']['set_weight_t']:.1f} | {cfg.PROJECT['diesel']['sets']} × {cfg.PROJECT['diesel']['set_weight_t']:g} t |
| Day tanks, full | {cfg.PROJECT['diesel']['day_tanks']*rig['tank_t']:.1f} | fuel only |
| Rig steel | {rig['deck_t']:g} | allowance |
| **On the {rig['mounts']} rig mounts** | **{rig['diesel_t']:.0f}** | {kn(rig['vertical_mount'],0)} kN on each mount if shared equally |
| Turbine generator sets | {cfg.POWER['modules']*cfg.POWER['set_weight_t']:.1f} | {cfg.POWER['modules']} × {cfg.POWER['set_weight_t']:g} t |
| Turbine deck steel | {rig['deck_t']:g} | allowance |
| **On the {rig['turbine_mounts']} turbine level mounts** | **{rig['turbine_t']:.0f}** | {kn(rig['vertical_turbine_mount'],0)} kN on each mount if shared equally |

None of this weight comes onto the shaft. Before the generator sets are landed, the rig mounts carry the rig steel alone, {rig['deck_t']*st.G/rig['mounts']:.0f} kN each, together with the sideways force in section 7.2.

### 7.4 Requirements from check 1

1. Sideways stiffness at the top of the shaft of at least {sh['needed']/1e6 if sh['needed'] else 0:.0f} kN/mm, through the connector, the rig and the mounts together.
2. The rig set, welded to its mounts and connected to the shaft before the first pod is hung. It must be able to take the force in section 7.2 without the weight of the generator sets on it.
3. No vertical load from the rig onto the shaft, and freedom for the shaft to shorten by {mv['shortening']*1000:.0f} mm or more inside the collar.

{design_closeout.section()}
## 8. Check 3: silo walls

### 8.1 Arrangement

The store is the space between two concentric concrete walls, {walls.HEIGHT:g} m high, filled with water-glycol to {walls.LIQUID:.2f} m. The liquid pushes the outer wall outwards and puts it in hoop tension. It pushes the inner wall inwards and puts it in hoop compression. These decisions were made by the project for revision D.

- **No post-tensioning.** The outer wall is conventionally reinforced: thicker walls and more reinforcement.
- **Standards.** ACI 350 for liquid-containing structures, with ACI 318.
- **Concrete.** A high strength that is readily available, f'<sub>c</sub> = {W['concrete_fc_mpa']} MPa (7,250 psi), to keep the walls thin. Buildability comes before cost.
- **Liquid barrier.** The spray liner keeps the liquid in, not the concrete. The concrete may therefore crack under hoop tension, and the reinforcement limits the width of the cracks.
- **Thickness may change up the height.** Jumpform is adjusted between lifts, so a wall can step in thickness at a lift joint. Each wall keeps one face plumb and steps on the other: the outside face of the outer wall, which carries the cooler frames, and the bore face of the inner wall, which the cage and the pods pass. The steps are on the faces in the store.

The outside diameter of {2*walls.R_OUT:g} m and the bore of {2*walls.R_BORE:g} m do not change. The extra thickness comes out of the store. The two walls are not tied to each other. Section 8.9 looks at tying them.

Clause numbers in this section are those of ACI 350-06. ACI 350-20 has replaced it with a different arrangement, and the values used here are to be confirmed against it at the checking stage.

### 8.2 Loads

| Quantity | Value | Basis |
| --- | ---: | --- |
| Density of the water-glycol | {cfg.FLUID['density_kg_m3']:,.0f} kg/m³ | input |
| Depth of liquid | {walls.LIQUID:.2f} m | {walls.HEIGHT:g} m wall less {cfg.FLUID['freeboard_m']:g} m of freeboard |
| Pressure at the base | {walls.pressure(0)/1000:.0f} kPa | |
| Load factor on the liquid | {W['fluid_load_factor']:g} | ACI 350-06 Section 9.2.1, U = 1.4(D + F) |

Only the liquid load is in this section. Section 8.12 lists what is left out. Temperature is taken up in sections 9.12 and 10.9.

### 8.3 The walls as first drawn

Both walls were {wc['present']['outer']*1000:.0f} mm thick in the model until revision F. They did not work.

| Wall | Finding |
| --- | --- |
| Outer | Hoop tension at the base is {kn(wc['present_tension'],0)} kN/m. At the steel stress in section 8.4 that needs {wc['present_steel']*1e6:,.0f} mm² of steel a metre, which is {wc['present_ratio']*100:.0f}% of the section. It cannot be placed. |
| Inner | The design buckling pressure of a {wc['present']['inner']*1000:.0f} mm wall is {wc['present_buckling'][1]/1000:.0f} kPa against a factored pressure of {W['fluid_load_factor']*walls.pressure(0)/1000:.0f} kPa. |
| Both | ACI 350 asks for at least 300 mm in a wall over 3 m high that holds liquid. |

### 8.4 Design criteria

Outer wall, in hoop tension:

| No. | Criterion | Limit | Basis |
| ---: | --- | --- | --- |
| 1 | Hoop reinforcement carries all the tension | A<sub>s</sub> = T / f<sub>s</sub>, with f<sub>s</sub> = {W['service_steel_stress_mpa']} MPa (20,000 psi) | ACI 350-06 Section 9.2.6: the environmental durability factor for direct tension in normal exposure. It has the same effect as limiting the steel to this stress under unfactored load. |
| 2 | Bars | #8 to #11, Grade 60, in at most {W['max_layers_per_face']} layers at each face, {W['min_bar_spacing_mm']} mm to {W['max_bar_spacing_mm']} mm apart | readily available bar, and room to place and vibrate concrete |
| 3 | Hoop steel ratio | ≤ {W['max_hoop_steel_ratio']*100:g}% of the section | a buildability limit set in this report |
| 4 | Room for the layers | {W['cover_mm']} mm cover, the hoop layers, the vertical bars and a {W['core_mm']} mm core | ACI 350-06 Section 7.7.1 for the cover |
| 5 | Least thickness | {W['min_thickness_mm']} mm, in steps of {W['thickness_step_mm']} mm, never thicker above than below | ACI 350-06 Section 14.6.2 |
| 6 | Least steel each way | {W['min_steel_ratio']*100:g}% of the section | ACI 350-06 Section 7.12.2, Grade 60, no movement joints |

Inner wall, in hoop compression:

| No. | Criterion | Limit | Basis |
| ---: | --- | --- | --- |
| 7 | Buckling under the pressure of the store | factored pressure ≤ {W['inner_wall_buckling']['strength_reduction']:g} × {W['inner_wall_buckling']['imperfection_factor']:g} × elastic critical pressure, with the modulus divided by {1+W['inner_wall_buckling']['creep_coefficient']:g} for creep | a method set in this report. ACI 318-19 requires the stability of a shell to be examined with creep, cracking and imperfections allowed for, and gives no formula. |
| 8 | Crushing | factored hoop compression ≤ 0.65 × 0.80 × 0.85 f'<sub>c</sub> t | ACI 318-19 Section 22.4, concrete alone |
| 9 | Thickness | uniform, and at least {W['min_thickness_mm']} mm | one form setting for the whole height |

The thickness of the outer wall does not reduce its steel. All of the tension goes to the reinforcement whatever the thickness. The thickness is set by how much steel a wall can hold and still be built, which is why criterion 3 matters and why it is a judgement.

### 8.5 Outer wall

Each lift is designed for the pressure at its lower edge.

| Lift | From, m | Pressure, kPa | Thickness, mm | Hoop tension, kN/m | Steel needed, mm²/m | Hoop bars | Steel provided, mm²/m | Ratio | Steel stress, MPa | Crack width, mm |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
{outer_rows}

![Half section through the walls of check 3](figures/walls.svg)

The outer wall goes from **{first['t']*1000:.0f} mm at the base to {last['t']*1000:.0f} mm at the top**, in {len(set(l['t'] for l in wc['lifts']))} thicknesses. The lowest lift needs {first['bars']['layers']} layers of {first['bars']['bar']['name']} bars at {first['bars']['spacing']*1000:.0f} mm, two layers at each face.

Hoop bars in tension round a tank cannot rely on ordinary laps in one place. Mechanical couplers, staggered, are assumed for all hoop bars. This is to be detailed.

**Cracking.** The concrete will crack under the full store. If it did not, its tensile stress would be {first['uncracked']/1e6:.1f} MPa at the base, against a tensile strength of about {walls.FCT/1e6:.1f} MPa. Cracks are vertical and pass through the wall. Their width is estimated at about {max(l['crack'] for l in wc['lifts'])*1000:.1f} mm by ACI 224.2R, and they open and close each time the level in the store changes. **The liner has to bridge moving cracks of this width.** That is a requirement on the liner and is to go in its specification.

For comparison, a wall thick enough not to crack would have to be about {first['no_crack']:.1f} m at the base and {wc['lifts'][len(wc['lifts'])//2]['no_crack']:.1f} m at mid-height. That is the design if the concrete itself were the liquid barrier.

### 8.6 Foot of the outer wall

The wall is taken as built into the base slab. The slab holds the foot of the wall in, which bends the wall near its foot and puts shear into it.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Moment at the foot | {kn(foot['moment'],0)} kN·m/m | long cylinder with a fixed foot, unfactored |
| Shear at the foot | {kn(foot['shear'],0)} kN/m | the same, unfactored |
| Vertical steel on the store face | {foot['vertical']*1e6:,.0f} mm²/m: {foot['bars']['layers']} {'layers' if foot['bars']['layers']>1 else 'layer'} of {foot['bars']['bar']['name']} at {foot['bars']['spacing']*1000:.0f} mm | at {W['service_steel_stress_mpa']} MPa |
| Factored shear | {kn(foot['vu'],0)} kN/m | {W['fluid_load_factor']:g} F |
| Design shear strength of the concrete | {kn(foot['vc'],0)} kN/m | ACI 318-19 Section 22.5, with at least minimum shear reinforcement |
| Shear ties needed | {foot['ties']*1e6:,.0f} mm² for each square metre of wall | ACI 350-06 Section 9.2.6, durability factor {foot['sd']:.2f} on the shear carried by steel |

Shear ties are needed in the lowest part of the first lift. The bending and shear fall off quickly with height: {2*foot['reach']:.1f} m above the foot they are below 15% of these values.

### 8.7 Inner wall

| Quantity | Value | Basis |
| --- | ---: | --- |
| **Thickness** | **{inner['t']*1000:.0f} mm, uniform** | |
| Elastic critical pressure | {inner['critical']/1000:,.0f} kPa | cylinder {walls.HEIGHT:g} m long held round at both ends, modulus {inner['modulus']/1e9:.1f} GPa after creep |
| Design buckling pressure | {inner['design']/1000:.0f} kPa | criterion 7 |
| Factored pressure at the base | {W['fluid_load_factor']*inner['pressure']/1000:.0f} kPa | applied over the whole height, which is on the safe side |
| Hoop compression at the base | {kn(inner['compression'],0)} kN/m, {inner['stress']/1e6:.1f} MPa | unfactored |
| Factored hoop compression against design strength | {kn(inner['factored'],0)} kN/m against {kn(inner['strength'],0)} kN/m | criterion 8 |
| Reinforcement each way | {inner['bars']['layers']} layers of {inner['bars']['bar']['name']} at {inner['bars']['spacing']*1000:.0f} mm | {W['min_steel_ratio']*100:g}% |
| Moment and shear at the foot | {kn(inner['base']['moment'],0)} kN·m/m and {kn(inner['base']['shear'],0)} kN/m | unfactored. Needs {inner['base']['vertical']*1e6:,.0f} mm²/m of vertical steel and {inner['base']['ties']*1e6:,.0f} mm²/m² of shear ties at the foot. |

Buckling governs. The check relies on the wall being held round at the base by the slab and near the top by the support rig and the turbine level, which are welded to it at their mounts. A ring with no help from its ends would need {inner['ring']*1000:.0f} mm at the base. The method is the least certain part of this check, and a shell buckling analysis is to confirm it.

### 8.8 What the new walls change

| Quantity | As first drawn | Check 3 | Note |
| --- | ---: | ---: | --- |
| Outer wall | {wc['present']['outer']*1000:.0f} mm | {first['t']*1000:.0f} mm to {last['t']*1000:.0f} mm | |
| Inner wall | {wc['present']['inner']*1000:.0f} mm | {inner['t']*1000:.0f} mm | |
| Width of the store | {cfg.WALL_GAP:.2f} m | {wc['gap_base']:.2f} m at the base, {wc['gap_top']:.2f} m at the top | |
| Volume of the store | {wc['now_volume']:,.0f} m³ | **{wc['volume']:,.0f} m³** | target {wc['target']:,.0f} m³. {'Still above the target.' if wc['volume']>=wc['target'] else 'Below the target.'} |
| Concrete in the walls | {wc['now_concrete']:,.0f} m³ | **{wc['concrete']:,.0f} m³** | {wc['concrete']/wc['now_concrete']:.1f} times |
| Reinforcement in the walls | allowance | **about {wc['steel_t']:,.0f} t** | {wc['hoop_t']:,.0f} t of it is hoop steel in the outer wall. Excludes the feet, openings and couplers. |
| Reinforcement in the lowest lift | | about {wc['lift_steel'][0]:,.0f} t | |

**The jumpform programme is affected.** The programme has one lift a day with a crew that includes six ironworkers. The lowest lift now has about {wc['lift_steel'][0]:,.0f} t of bar and {wc['lifts'][0]['concrete']:,.0f} m³ of concrete. That is not a day's work for the present crew. Prefabricated cages lifted in by crane, a larger crew or a longer cycle for the lower lifts is needed. This is open item 9.

The heat that the store can absorb falls with its volume, by {(1-wc['volume']/wc['now_volume'])*100:.0f}%. Check 5 uses the new volume (section 9.7).

### 8.9 Alternative: tie the two walls together

The liquid stretches the outer wall and squeezes the inner wall. On a cut through the whole silo the liquid acts only on the width of the store, so the net hoop force is the pressure times that width: {kn(wc['tie_total'],0)} kN/m at the base with the walls as first drawn. That is {wc['tie_total']/wc['present_tension']*100:.0f}% of the tension that the outer wall takes when it works alone. If the walls were tied across the store, by radial concrete fins or by steel ties, the compression in the inner wall would cancel most of the tension in the outer wall, and the hoop steel would fall by about {(1-wc['tie_total']/wc['present_tension'])*100:.0f}%.

It is not adopted here. Ties or fins complicate the jumpform, divide the store into cells, pass through the liner and obstruct the spray stages, which goes against buildability. It is recorded because the saving is large. This is open item 10.

### 8.10 Verification

| Check | Value | Independent value | Agreement |
| --- | ---: | ---: | --- |
| Hoop tension in the outer wall less hoop compression in the inner wall, at the base | {kn(first['tension']-inner['compression'],1)} kN/m | pressure × width of the store = {kn(first['pressure']*first['gap'],1)} kN/m | equal |
| Steel stress in every lift | at most {max(l['stress'] for l in wc['lifts'])/1e6:.0f} MPa | limit {W['service_steel_stress_mpa']} MPa | within |
| Volume of the store against its target | {wc['volume']:,.0f} m³ | {wc['target']:,.0f} m³ | above |

These are checked at every build by [walls.py](../gpu_silo/walls.py).

### 8.11 Conclusion

Without post-tensioning, the outer wall needs to be {first['t']*1000:.0f} mm thick at the base, stepping to {last['t']*1000:.0f} mm, with up to {first['bars']['layers']} layers of {first['bars']['bar']['name']} hoop bars, and the inner wall {inner['t']*1000:.0f} mm throughout, in {W['concrete_fc_mpa']} MPa concrete. The store keeps {wc['volume']:,.0f} m³, which is above its target. The walls take {wc['concrete']/wc['now_concrete']:.1f} times the concrete now allowed for and about {wc['steel_t']:,.0f} t of reinforcement.

These thicknesses were the proposal of revision D, for the liquid load only. They were not adopted.

**Sections 9 and 10 take this further.** Check 5 raises the inner wall to {th.C['creep']['t']*1000:.0f} mm, because warm concrete creeps more. Section 10 then compares reinforcement and finds that stainless steel bars bring the outer wall down to {rf.C['proposed']['lifts'][0]['t']*1000:.0f} mm for its whole height.

### 8.12 Interfaces beyond the original wall calculation

1. **Temperature.** A warm store and cold outside air stretch the outside face of the outer wall. It is not in this section. Sections 9.12 and 10.9 cover it.
2. **The ground entry.** The entry passes through both walls and the store at the base, where the hoop forces are largest. It cuts the hoop steel of the outer wall and the compression ring of the inner wall. Framing it is a design task of its own.
3. **Other openings and fixings.** The {cfg.TOTAL} service sleeves in the inner wall, the cooler conduits in the outer wall, and the loads from the mounts of the support rig and the turbine level (checks 9 and 10) and from the cooler frames.
4. **Earthquake**, including the sloshing of the store. It waits for the site.
5. **Lift joints.** Nine horizontal joints in each wall, and the steps in thickness at them.
6. **Vertical load** from the lid, the power levels and the walls themselves, and wind on the empty silo. Both are small beside the liquid load.
7. **The base slab** and how firmly it holds the feet of the walls. Part of check 4.

{thermal_section()}
{reinforcement_section()}
{foundation_section()}
{connection_section()}
## 13. Assumptions and release conditions

The [revision J review register](assumptions.md) cross-references every previous structural open item (R1–R20) and calculation question (Q1–Q18) to an adopted decision and the evidence needed for release. The site spectrum, geotechnical investigation, authority acceptance of the lined-wall design, manufacturer submittals, lift plans and independent engineering sign-off remain external hold points.

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
            FIGURES / "shaft.svg": shaft_figure(), FIGURES / "walls.svg": wall_figure(),
            FIGURES / "heat_rejection.svg": thermal_figure(), FIGURES / "wall_options.svg": options_figure(),
            FIGURES / "foundation.svg": foundation_figure(), FIGURES / "root.svg": root_figure()}


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
