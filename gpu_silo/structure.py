"""Structural design checks, worked out from design/project.json.

SI units throughout: metres, newtons, kilograms. Sections carry their US names.
Steel design follows AISC 360-22 (LRFD) with loads from ASCE 7-22.

The pod is carried by two vertical side trusses, one each side of the racks. Each is
analysed as a pin-jointed plane truss by the direct stiffness method. The joints are
fully welded, so the real truss is a little stiffer than the model.
"""
import math
from fractions import Fraction

import numpy as np

from . import design as cfg

P = cfg.PROJECT["structure"]
STEEL = P["steel"]
T = P["pod_truss"]
G = 9.80665
INCH = .0254
E = STEEL["e_gpa"] * 1e9
FY = STEEL["fy_mpa"] * 1e6
FU = STEEL["fu_mpa"] * 1e6
RHO = STEEL["density_kg_m3"]
PHI_C = PHI_T = .90
ROOT = cfg.STORE["root_radius_m"]
SHAFT_R = cfg.STORE["shaft_radius_m"]
ACCESS = round(ROOT - SHAFT_R, 6)
RACKS = cfg.CLUSTER["racks_per_pod"]
RACK_ZONE = cfg.BODY_LENGTH
CDU_ZONE = cfg.SECTION
SPAN = RACK_ZONE + CDU_ZONE
TIP_R = ROOT + SPAN
TRUSS_SPACING = round(cfg.BODY_WIDTH + (cfg.FRAME_WIDTH - cfg.BODY_WIDTH) / 2, 6)
# No one part may move a pod tip by more than the single limit, and all the parts together by no more than the accumulated limit.
TIP = P["tip_movement"]
LIMIT = TIP["single_mm"] / 1000
ACCUMULATED = TIP["accumulated_mm"] / 1000
SHAFT = P["shaft"]
RIG = P["top_rig"]
SHAFT_D = 2 * SHAFT_R
FY_SHAFT = SHAFT["fy_mpa"] * 1e6
# The shaft is fixed at the top of the foundation and held sideways at mid-depth of the support rig.
SHAFT_TOP = cfg.CROWN + cfg.POWER["floor_structure_m"] / 2


def inches(value):
    whole, part = divmod(Fraction(value).limit_denominator(16), 1)
    if not part: return str(whole)
    return f"{whole}-{part}" if whole else str(part)


def rounded_rectangle(h, b, r):
    """Area and second moments of a rectangle h high and b wide with corner radius r."""
    area = h * b - (4 - math.pi) * r * r
    def second(depth, width):
        square = r**4 / 12 + r * r * (depth / 2 - r / 2)**2
        arm = depth / 2 - r + 4 * r / (3 * math.pi)
        quarter = (math.pi / 16 - 4 / (9 * math.pi)) * r**4 + math.pi * r * r / 4 * arm * arm
        return width * depth**3 / 12 - 4 * square + 4 * quarter
    return area, second(h, b), second(b, h)


def hss(h_in, b_in, t_in):
    """A rectangular HSS, long side h. Properties use the design wall thickness and an outside corner radius of twice the wall."""
    nominal = t_in * INCH
    t = STEEL["design_wall_factor"] * nominal
    h, b = h_in * INCH, b_in * INCH
    outer = rounded_rectangle(h, b, 2 * t)
    inner = rounded_rectangle(h - 2 * t, b - 2 * t, t)
    area, ix, iy = (o - i for o, i in zip(outer, inner))
    weight = rounded_rectangle(h, b, 2 * nominal)[0] - rounded_rectangle(h - 2 * nominal, b - 2 * nominal, nominal)[0]
    return dict(name=f"HSS{inches(h_in)}×{inches(b_in)}×{inches(t_in)}", h=h, b=b, t=t, t_nominal=nominal,
                h_in=h_in, b_in=b_in, t_in=t_in, area=area, ix=ix, iy=iy, rx=math.sqrt(ix / area), ry=math.sqrt(iy / area),
                kg_m=weight * RHO, wall=max((h - 3 * t) / t, (b - 3 * t) / t))


def compression_stress(slenderness):
    """Critical stress for flexural buckling, AISC 360-22 E3."""
    fe = math.pi**2 * E / slenderness**2
    return .658**(FY / fe) * FY if slenderness <= 4.71 * math.sqrt(E / FY) else .877 * fe


WALL_LIMIT = 1.40 * math.sqrt(E / FY)       # AISC 360-22 Table B4.1a, case 6
CHORDS = [hss(*size) for size in T["chord_sizes_in"]]
WEBS = [hss(*size) for size in T["web_sizes_in"]]
CROSS = hss(*T["cross_member_in"])


def masses():
    pod = cfg.POD
    return dict(racks=RACKS * pod["rack_mass_t"] * 1000, cdu=pod["cdu_pump_mass_t"] * 1000,
                coolant=pod["coolant_and_piping_t"] * 1000)


def stations():
    """Panel points along the pod, measured from its root. One panel to a rack, then the CDU and pump section."""
    rack = [i * RACK_ZONE / RACKS for i in range(RACKS + 1)]
    return rack + [RACK_ZONE + (i + 1) * CDU_ZONE / T["cdu_panels"] for i in range(T["cdu_panels"])]


def secondary(chord, web):
    """Steel and housing that the two trusses carry but that is not part of them, in kilograms."""
    xs = stations()
    clear = cfg.BODY_WIDTH
    cross = 2 * len(xs) * clear + 2 * sum(math.hypot(b - a, TRUSS_SPACING) for a, b in zip(xs, xs[1:]))
    housing = T["housing_kg_per_m2"] * 2 * (cfg.BODY_HEIGHT + cfg.BODY_WIDTH) * SPAN
    return dict(cross_m=cross, cross=cross * CROSS["kg_m"], housing=housing)


def truss(chord, web):
    """Nodes and members of one side truss. Diagonals fall towards the tip, so they are in tension when the pod is docked."""
    xs = stations()
    depth = cfg.FRAME_HEIGHT - chord["h"]
    n = len(xs)
    nodes = [(x, 0.) for x in xs] + [(x, depth) for x in xs]
    members = []
    for i in range(n - 1):
        members.append(dict(a=i, b=i + 1, section=chord, kind="Bottom chord", panel=i + 1))
        members.append(dict(a=n + i, b=n + i + 1, section=chord, kind="Top chord", panel=i + 1))
        members.append(dict(a=n + i, b=i + 1, section=web, kind="Diagonal", panel=i + 1))
    for i in range(n):
        members.append(dict(a=i, b=n + i, section=web, kind="Vertical", panel=i))
    for m in members:
        (x0, z0), (x1, z1) = nodes[m["a"]], nodes[m["b"]]
        m["length"] = math.hypot(x1 - x0, z1 - z0)
        m["cos"], m["sin"] = (x1 - x0) / m["length"], (z1 - z0) / m["length"]
    return dict(xs=xs, n=n, depth=depth, nodes=nodes, members=members, chord=chord, web=web)


def node_loads(model):
    """Unfactored dead load at each node of one truss, in newtons downwards, and the mass that makes it up."""
    xs, n = model["xs"], model["n"]
    load = np.zeros(2 * n)
    parts = dict(truss=0., connections=0.)
    for m in model["members"]:
        kg = m["section"]["kg_m"] * m["length"]
        parts["truss"] += kg
        load[m["a"]] += kg / 2
        load[m["b"]] += kg / 2
    extra = secondary(model["chord"], model["web"])
    mass = masses()
    line = (mass["coolant"] + extra["cross"] + extra["housing"]) / SPAN / 2      # kg/m on one truss
    connections = T["connection_allowance"] * (parts["truss"] + extra["cross"] / 2)
    load[:] *= 1 + T["connection_allowance"]
    line += T["connection_allowance"] * extra["cross"] / SPAN / 2
    for i in range(n - 1):
        panel = xs[i + 1] - xs[i]
        kg = line * panel
        if i < RACKS: kg += mass["racks"] / RACKS / 2
        else: kg += mass["cdu"] / T["cdu_panels"] / 2
        load[i] += kg / 2
        load[i + 1] += kg / 2
    parts["connections"] = connections
    return load * G, parts, extra


def solve(model, load, supports):
    """Node displacements and member forces (tension positive) for vertical node loads and the given restraints."""
    n, nodes = model["n"], model["nodes"]
    size = 4 * n
    k = np.zeros((size, size))
    for m in model["members"]:
        c, s = m["cos"], m["sin"]
        ea = E * m["section"]["area"] / m["length"]
        block = ea * np.array([[c * c, c * s, -c * c, -c * s], [c * s, s * s, -c * s, -s * s],
                               [-c * c, -c * s, c * c, c * s], [-c * s, -s * s, c * s, s * s]])
        dof = [2 * m["a"], 2 * m["a"] + 1, 2 * m["b"], 2 * m["b"] + 1]
        k[np.ix_(dof, dof)] += block
    force = np.zeros(size)
    force[1::2] = -load
    free = [i for i in range(size) if i not in supports]
    u = np.zeros(size)
    u[free] = np.linalg.solve(k[np.ix_(free, free)], force[free])
    axial = []
    for m in model["members"]:
        a, b = m["a"], m["b"]
        stretch = (u[2 * b] - u[2 * a]) * m["cos"] + (u[2 * b + 1] - u[2 * a + 1]) * m["sin"]
        axial.append(E * m["section"]["area"] / m["length"] * stretch)
    reactions = k @ u - force
    return u, axial, {dof: reactions[dof] for dof in supports}


def pickup_panels():
    """Panel points at which the hoist's two pickups take the pod, one each side of its centre of gravity."""
    return tuple(T["pickup_panel_points"])


def analyse(chord, web):
    """One candidate: docked as a cantilever and hanging from the hoist. Returns deflection, forces, checks and mass."""
    model = truss(chord, web)
    n = model["n"]
    load, parts, extra = node_loads(model)
    # Docked: the upper clevis holds the top chord in both directions and the lower bearing takes thrust only.
    u, docked, reactions = solve(model, load, [2 * n, 2 * n + 1, 0])
    tip = -u[2 * (n - 1) + 1]          # bottom chord, at the wall end
    first, second = pickup_panels()
    _, hoisted, lifting = solve(model, load, [2 * (n + first), 2 * (n + first) + 1, 2 * (n + second) + 1])
    limit = T["max_slenderness"]
    rows = []
    for m, a, b in zip(model["members"], docked, hoisted):
        section = m["section"]
        cases = (T["dead_load_factor"] * a, T["dead_load_factor"] * T["hoist_impact_factor"] * b)
        tension = max(0., *cases)
        compression = max(0., *(-v for v in cases))
        slender = m["length"] / min(section["rx"], section["ry"])
        strength_t = PHI_T * FY * section["area"]
        strength_c = PHI_C * compression_stress(slender) * section["area"]
        rows.append(dict(m, docked=a, hoisted=b, tension=tension, compression=compression, slenderness=slender,
                         strength_t=strength_t, strength_c=strength_c,
                         ratio=max(tension / strength_t, compression / strength_c)))
    mass = masses()
    steel = 2 * parts["truss"] + extra["cross"]
    connections = T["connection_allowance"] * steel
    frame = steel + connections + extra["housing"]
    weight = 2 * load.sum()
    xs = np.array(model["xs"] * 2)
    centre = float((load * xs).sum() / load.sum())
    radius = ROOT + xs
    inertia = float(2 * (load / G * radius**2).sum())
    groups = {}
    for kind in ("Top chord", "Bottom chord", "Diagonal", "Vertical"):
        chosen = [r for r in rows if r["kind"] == kind]
        groups[kind] = dict(section=chosen[0]["section"], tension=max(r["tension"] for r in chosen),
                            compression=max(r["compression"] for r in chosen), ratio=max(r["ratio"] for r in chosen),
                            slenderness=max(r["slenderness"] for r in chosen), length=max(r["length"] for r in chosen),
                            docked_max=max(r["docked"] for r in chosen), docked_min=min(r["docked"] for r in chosen))
    ok = dict(deflection=tip <= LIMIT + 1e-12,
              strength=max(r["ratio"] for r in rows) <= 1,
              slenderness=max(r["slenderness"] for r in rows) <= limit,
              walls=max(chord["wall"], web["wall"]) <= WALL_LIMIT,
              joint=T["min_web_to_chord_width"] <= web["b"] / chord["b"] <= 1 and chord["b_in"] <= T["chord_max_width_in"])
    return dict(model=model, chord=chord, web=web, tip=tip, rows=rows, groups=groups, ok=ok, passes=all(ok.values()),
                load=load, steel=steel, truss_steel=2 * parts["truss"], cross=extra["cross"], cross_m=extra["cross_m"],
                connections=connections, housing=extra["housing"], frame=frame,
                mass=dict(mass, frame=frame), pod=weight / G, weight=weight, centre=centre, inertia=inertia,
                root_pull=abs(reactions[2 * n]), root_thrust=abs(reactions[0]), root_shear=abs(reactions[2 * n + 1]),
                lifting=(abs(lifting[2 * (n + first) + 1]), abs(lifting[2 * (n + second) + 1])))


def candidates():
    found = [analyse(chord, web) for chord in CHORDS for web in WEBS]
    return sorted(found, key=lambda c: (round(c["steel"], 3), c["tip"]))


def lightest(limit=None):
    """Lightest pair of sections that passes every criterion, for a tip deflection limit in metres."""
    limit = LIMIT if limit is None else limit
    for c in candidates():
        ok = dict(c["ok"], deflection=c["tip"] <= limit + 1e-12)
        if all(ok.values()): return c
    return None


def hand_check(design):
    """Tip deflection by statics and virtual work, independent of the stiffness solution."""
    model, load = design["model"], design["load"]
    xs, n, depth = model["xs"], model["n"], model["depth"]
    chord, web = design["chord"], design["web"]
    point = [load[i] + load[n + i] for i in range(n)]
    chords = webs = 0.
    for i in range(n - 1):
        panel = xs[i + 1] - xs[i]
        diagonal = math.hypot(panel, depth)
        shear = sum(point[i + 1:])
        moment = lambda x: sum(p * (xs[j] - x) for j, p in enumerate(point) if xs[j] > x)
        # Real forces, then the forces from a unit load at the tip.
        pairs = [(moment(xs[i + 1]) / depth, (xs[-1] - xs[i + 1]) / depth, panel, chord),
                 (-moment(xs[i]) / depth, -(xs[-1] - xs[i]) / depth, panel, chord),
                 (shear * diagonal / depth, diagonal / depth, diagonal, web)]
        chords += sum(f * unit * length / (E * s["area"]) for f, unit, length, s in pairs[:2])
        webs += sum(f * unit * length / (E * s["area"]) for f, unit, length, s in pairs[2:])
    for i in range(1, n - 1):
        real = -(sum(point[i + 1:]) + load[n + i])
        webs += real * -1 * depth / (E * web["area"])
    return dict(total=chords + webs, chords=chords, webs=webs)


def sensitivity():
    return [(mm / 1000, lightest(mm / 1000)) for mm in T["sensitivity_limits_mm"]]


def unbalance(moment):
    """Out-of-balance moment on the shaft as the store is filled from the top down.

    Levels already full bunch to the packed pitch while a pod is lifted past them. The level being
    filled holds its pods at the storage pitch. Returns the worst state and the moment at each level.
    """
    bays, levels = cfg.BAYS, cfg.LEVELS
    uniform, packed = 2 * math.pi / bays, math.radians(cfg.STORE["packed_pitch_degrees"])
    bunched = sum(complex(math.cos(a), math.sin(a)) for a in ((j - (bays - 1) / 2) * packed for j in range(bays)))
    full = abs(bunched)
    worst = dict(base=0.)
    for done in range(levels):                      # levels already full, counted from the top
        for placed in range(bays):                  # pods already on the level being filled
            # Full levels: resultant opposite the lifting lane. Partial level: its pods trail back from the lane.
            above = done * full * complex(-1, 0)
            partial = sum(complex(math.cos(-uniform * (k + 1)), math.sin(-uniform * (k + 1))) for k in range(placed))
            base = abs(above + partial) * moment
            if base > worst["base"]:
                worst = dict(base=base, full=done, placed=placed, partial=abs(partial) * moment, above=abs(above) * moment,
                             vector=(above + partial) * moment, parts=[above * moment / max(done, 1)] * done + [partial * moment])
    partial_max = max(abs(sum(complex(math.cos(uniform * k), math.sin(uniform * k)) for k in range(count)))
                      for count in range(bays + 1))
    return dict(worst, bunched=full * moment, partial_max=partial_max * moment,
                unrestricted=levels * partial_max * moment)


def level_height(level):
    return cfg.STORE["lowest_berth_m"] + (level - 1) * cfg.STORE["pitch_m"] + cfg.FRAME_HEIGHT / 2


def tube(wall_in):
    """A round tube of the shaft diameter, rolled from plate. The design wall is the nominal thickness."""
    wall = wall_in * INCH
    d, inner = SHAFT_D, SHAFT_D - 2 * wall
    area = math.pi / 4 * (d * d - inner * inner)
    i = math.pi / 64 * (d**4 - inner**4)
    return dict(name=f"{d*1000:.0f} mm OD × {inches(wall_in)} in", wall_in=wall_in, wall=wall, d=d, area=area, i=i, s=i / (d / 2),
                z=(d**3 - inner**3) / 6, r=math.sqrt(i / area), kg_m=area * RHO, ratio=d / wall)


def beam(couples, ei, stiffness=None):
    """The shaft as a beam: fixed at the base, couples applied at given heights, held at the top.

    stiffness is that of the top restraint in N/m: None for a rigid hold, 0 for a free top.
    """
    height = SHAFT_TOP
    z = np.linspace(0, height, 4759)
    moment = np.zeros_like(z)
    for elevation, m in couples:
        moment[z <= elevation] += m
    step = z[1] - z[0]
    integrate = lambda y: np.concatenate([[0], np.cumsum((y[1:] + y[:-1]) / 2) * step])
    slope = integrate(moment) / ei
    sway = integrate(slope)
    flexibility = height**3 / (3 * ei)
    reaction = 0. if stiffness == 0 else sway[-1] / (flexibility + (0 if stiffness is None else 1 / stiffness))
    moment = moment - reaction * (height - z)
    slope = slope - reaction * (height * z - z * z / 2) / ei
    sway = sway - reaction * (height * z * z / 2 - z**3 / 6) / ei
    hubs = np.interp([level_height(level) for level in range(1, cfg.LEVELS + 1)], z, slope)
    return dict(z=z, moment=moment, slope=slope, sway=sway, reaction=float(reaction), base=float(moment[0]),
                peak=float(np.abs(moment).max()), lean=float(np.abs(hubs).max()), top=float(sway[-1]))


def states(c):
    """Loading states of the shaft: couples and vertical loads at each level, from the pods as designed."""
    weight, moment, u = c["weight"], c["moment_axis"], c["unbalance"]
    levels = list(range(cfg.LEVELS, 0, -1))                       # from the top down
    hub = SHAFT["hub_and_floor_t_per_level"] * 1000 * G
    along = u["vector"] / abs(u["vector"])
    full = [(level_height(level), cfg.BAYS * weight + hub) for level in levels]
    sequence_couples = [(level_height(level), (m * along.conjugate()).real) for level, m in zip(levels, u["parts"])]
    sequence_loads = [(level_height(level), hub + weight * (cfg.BAYS if k < u["full"] else u["placed"] if k == u["full"] else 0))
                      for k, level in enumerate(levels)]
    half = max(range(cfg.BAYS + 1), key=lambda n: abs(sum(complex(math.cos(2 * math.pi / cfg.BAYS * k), math.sin(2 * math.pi / cfg.BAYS * k)) for k in range(n))))
    return [dict(key="complete", name="Store complete, every level at the storage pitch", couples=[], loads=full, pods=cfg.TOTAL),
            dict(key="sequence", name=f"Worst state of the filling sequence: {u['full']} levels full and bunched, {u['placed']} pods on the next",
                 couples=sequence_couples, loads=sequence_loads, pods=u["full"] * cfg.BAYS + u["placed"]),
            dict(key="uncontrolled", name=f"Uncontrolled fill: {half} pods on the same side of every level",
                 couples=[(level_height(level), u["partial_max"]) for level in levels],
                 loads=[(level_height(level), half * weight + hub) for level in levels], pods=half * cfg.LEVELS)]


def shortening(section, c):
    """Drop of each hub as the pods are hung, from the shortening of the shaft below it. Top level last."""
    heights = [level_height(level) for level in range(1, cfg.LEVELS + 1)]
    load = cfg.BAYS * c["weight"]
    return [sum(load * min(a, b) for b in heights) / (E * section["area"]) for a in heights]


def shaft_check(section, c, stiffness=None):
    """Strength to AISC 360-22 and the movement of the pod tips, for one wall thickness."""
    ei = E * section["i"]
    length = SHAFT_TOP
    line = (section["kg_m"] + SHAFT["services_kg_per_m"]) * G
    slender = SHAFT["effective_length_factor"] * length / section["r"]
    fe = math.pi**2 * E / slender**2
    fcr = .658**(FY_SHAFT / fe) * FY_SHAFT if slender <= 4.71 * math.sqrt(E / FY_SHAFT) else .877 * fe
    pc = PHI_C * fcr * section["area"]
    lam, compact, limit = section["ratio"], .07 * E / FY_SHAFT, .31 * E / FY_SHAFT
    mn = FY_SHAFT * section["z"] if lam <= compact else (.021 * E / lam + FY_SHAFT) * section["s"]
    mc = .90 * mn
    vc = .90 * .6 * FY_SHAFT * section["area"] / 2
    euler = math.pi**2 * ei / length**2
    factor = T["dead_load_factor"]
    cases = []
    for state in states(c):
        result = beam(state["couples"], ei, stiffness)
        axial = sum(p for _, p in state["loads"]) + line * length
        pu = factor * axial
        b1 = 1 / (1 - pu / euler)
        mu = factor * b1 * result["peak"]
        ratio = pu / pc + 8 / 9 * mu / mc if pu / pc >= .2 else pu / (2 * pc) + mu / mc
        cases.append(dict(state, result=result, axial=axial, pu=pu, mu=mu, b1=b1, ratio=ratio, vu=factor * abs(result["reaction"]),
                          shear=factor * abs(result["reaction"]) / vc))
    drops = shortening(section, c)
    lean = next(k for k in cases if k["key"] == "sequence")["result"]["lean"]
    movement = dict(shortening=max(drops), lean=lean, lean_drop=lean * TIP_R, total=max(drops) + lean * TIP_R, by_level=drops)
    ok = dict(wall=lam <= .11 * E / FY_SHAFT, flexure=lam < .45 * E / FY_SHAFT, strength=max(k["ratio"] for k in cases) <= 1,
              slenderness=slender <= T["max_slenderness"], movement=movement["total"] <= LIMIT + 1e-12,
              accumulated=c["design"]["tip"] + movement["total"] <= ACCUMULATED + 1e-12)
    return dict(section=section, ei=ei, line=line, slender=slender, fcr=fcr, pc=pc, mc=mc, vc=vc, compact=lam <= compact, cases=cases,
                movement=movement, ok=ok, passes=all(ok.values()), ratio=max(k["ratio"] for k in cases),
                mass=section["kg_m"] * length)


def shaft_design(c):
    walls = [shaft_check(tube(size), c) for size in SHAFT["wall_sizes_in"]]
    lightest = next((w for w in walls if w["passes"]), None)
    if lightest is None:
        raise ValueError("No wall thickness in structure.shaft meets the criteria. Add thicker plate, a larger shaft or relax the limit.")
    chosen = lightest
    if SHAFT.get("adopted_wall_in"):
        # The project may set a thicker wall than the lightest that meets the shaft's own limits.
        chosen = next(w for w in walls if w["section"]["wall_in"] == SHAFT["adopted_wall_in"])
        if not chosen["passes"]:
            raise ValueError("The wall thickness adopted in structure.shaft does not meet the criteria.")
    section = chosen["section"]
    limit = LIMIT
    free = shaft_check(section, c, 0)
    springs = [(k, shaft_check(section, c, k * 1e6)) for k in SHAFT["rig_stiffness_kn_per_mm"]]
    # Stiffness of the top restraint at which the movement just meets the limit.
    lo, hi = 1e3, 1e12
    needed = None
    if free["movement"]["total"] > limit >= chosen["movement"]["total"]:
        for _ in range(80):
            mid = math.sqrt(lo * hi)
            lo, hi = (mid, hi) if shaft_check(section, c, mid)["movement"]["total"] > limit else (lo, mid)
        needed = hi
    return dict(walls=walls, chosen=chosen, lightest=lightest, free=free, springs=springs, needed=needed, limit=limit, length=SHAFT_TOP)


def rig_loads(c):
    """Design loads for the support rig, the shaft-top connector and the cast-in wall mounts."""
    shaft = c["shaft"]
    mounts = RIG["wall_mounts"]
    power, diesel = cfg.POWER, cfg.PROJECT["diesel"]
    deck = cfg.PROJECT["logistics"]["power_fabrication"]["deck_steel_t"]
    tank = math.pi / 4 * diesel["day_tank_diameter_m"]**2 * diesel["day_tank_length_m"] * 850 / 1000
    diesel_level = diesel["sets"] * diesel["set_weight_t"] + diesel["day_tanks"] * tank + deck
    turbine_level = power["modules"] * power["set_weight_t"] + deck
    out = dict(mounts=mounts, diesel_t=diesel_level, turbine_t=turbine_level, tank_t=tank, deck_t=deck, cases=[])
    for case in shaft["chosen"]["cases"]:
        r = abs(case["result"]["reaction"])
        out["cases"].append(dict(key=case["key"], name=case["name"], reaction=r, factored=T["dead_load_factor"] * r,
                                 mount=2 * r / mounts))
    out["vertical_mount"] = diesel_level * 1000 * G / mounts
    out["turbine_mounts"] = P["turbine_mounts"]["wall_mounts"]
    out["vertical_turbine_mount"] = turbine_level * 1000 * G / out["turbine_mounts"]
    return out


def compute():
    design = lightest()
    if design is None:
        raise ValueError("No pair of sections in structure.pod_truss meets the criteria. Add heavier sections or relax the limit.")
    split = hand_check(design)
    c = dict(design=design, limit=LIMIT, hand=split["total"], split=split)
    pod = design["pod"]
    weight = design["weight"]
    arm = ROOT + design["centre"]
    c.update(pod_t=pod / 1000, weight=weight, arm=arm, moment_root=weight * design["centre"], moment_axis=weight * arm,
             level_weight=cfg.BAYS * weight, store_weight=cfg.TOTAL * weight,
             inertia_pod=design["inertia"], inertia_level=cfg.BAYS * design["inertia"])
    c["unbalance"] = unbalance(c["moment_axis"])
    c["shaft"] = shaft_design(c)
    c["rig"] = rig_loads(c)
    moved = c["shaft"]["chosen"]["movement"]["total"]
    c["budget"] = dict(truss=design["tip"], shaft=moved, total=design["tip"] + moved, limit=ACCUMULATED,
                       reserve=ACCUMULATED - design["tip"] - moved)
    drive = P["level_drive"]
    c["index_alpha"] = 4 * (2 * math.pi / cfg.BAYS) / drive["index_seconds"]**2
    c["index_torque"] = c["inertia_level"] * c["index_alpha"]
    return c


C = compute()


def check():
    d = C["design"]
    assert abs(ACCESS - cfg.STORE["shaft_access_m"]) < 1e-6 and abs(TIP_R + cfg.POD["tip_clearance_m"] - cfg.BORE_R) < 1e-6
    assert CDU_ZONE > 0, "the rack housing is longer than the space between the access and the wall"
    assert d["passes"] and d["tip"] <= C["limit"]
    assert abs(C["hand"] - d["tip"]) < .02 * d["tip"], "the stiffness solution and the hand check disagree"
    assert abs(d["root_shear"] - d["weight"] / 2) < 1e-6 * d["weight"] and abs(d["root_pull"] - d["root_thrust"]) < 1e-6 * d["weight"]
    assert abs(d["root_pull"] * d["model"]["depth"] - C["moment_root"] / 2) < 1e-6 * C["moment_root"]
    assert abs(sum(d["lifting"]) - d["weight"] / 2) < 1e-6 * d["weight"] and min(d["lifting"]) > .25 * d["weight"] / 2
    reference = hss(6, 3, .25)       # AISC Manual Table 1-11 lists A = 3.84 in² and 13.91 lb/ft for HSS6×3×1/4
    assert abs(reference["area"] / INCH**2 - 3.84) < .04 and abs(reference["kg_m"] / 1.48816 - 13.91) < .14
    # The shaft: a single couple on a propped cantilever has a closed-form reaction, and the held top does not move.
    shaft = C["shaft"]
    ei, height, a = shaft["chosen"]["ei"], SHAFT_TOP, level_height(cfg.LEVELS)
    one = beam([(a, 1e6)], ei)
    assert abs(one["reaction"] - 3 * 1e6 * a * (2 * height - a) / (2 * height**3)) < 1e-3 * one["reaction"] and abs(one["top"]) < 1e-9
    for case in shaft["chosen"]["cases"]:
        total = sum(m for _, m in case["couples"])
        assert abs(case["result"]["base"] - (total - case["result"]["reaction"] * height)) < 1e-6 * max(1., abs(total))
    assert shaft["chosen"]["passes"] and shaft["chosen"]["movement"]["total"] <= shaft["limit"]
    assert C["budget"]["total"] <= ACCUMULATED and C["budget"]["reserve"] >= 0


def summary():
    d = C["design"]
    s = C["shaft"]["chosen"]
    return (f"Pod truss: {d['chord']['name']} chords and {d['web']['name']} web, tip deflection {d['tip']*1000:.1f} mm "
            f"against {C['limit']*1000:.1f} mm, highest strength ratio {max(r['ratio'] for r in d['rows']):.2f}. "
            f"A pod weighs {C['pod_t']:.2f} t. The hand check agrees to {abs(C['hand']-d['tip'])/d['tip']*100:.2f}%.\n"
            f"Shaft: {s['section']['name']} wall, held at the top. Pod tips move {s['movement']['total']*1000:.1f} mm "
            f"against {C['shaft']['limit']*1000:.1f} mm, highest strength ratio {s['ratio']:.2f}.")
