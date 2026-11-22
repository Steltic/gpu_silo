"""Check 4: the base slab under the silo and the anchorage of the shaft.

The slab is a round plate on the ground, loaded by the two walls, the liquid between them and the shaft
at its centre. It is analysed as an axisymmetric plate on springs (Winkler ground) by finite elements.
The site is not fixed, so the stiffness of the ground is an assumption and three values are carried through.

SI units: metres, newtons, pascals.
"""
import math

import numpy as np

from . import design as cfg
from . import logistics
from . import reinforcement
from . import structure
from . import walls

F = cfg.PROJECT["structure"]["foundation"]
BASE = F["shaft_base"]
FC = F["concrete_fc_mpa"]
EC = 4700 * math.sqrt(FC) * 1e6
NU = walls.NU
FY = F["fy_mpa"] * 1e6
GAMMA_C = F["unit_weight_kn_m3"] * 1e3
LOAD = F["load_factor"]
RADIUS = cfg.OUTSIDE_R + cfg.PROJECT["logistics"]["concrete"]["slab_overhang_m"]
# The spring under a slab is not a property of the ground alone: it falls as the slab gets wider. For a stiff round
# slab on an elastic ground of modulus E the settlement is q D (1 - v²) π / (4 E), so the spring is 4 E / (π D (1 - v²)).
MODULUS = {name: value * 1e6 for name, value in F["ground_modulus_mpa"].items()}
GROUND = {name: 4 * e / (math.pi * 2 * RADIUS * (1 - F["ground_poisson"]**2)) for name, e in MODULUS.items()}
T_OUT, T_IN = cfg.SILO["outer_wall_m"], cfg.SILO["inner_wall_m"]
R_OUTER = cfg.OUTSIDE_R - T_OUT / 2                    # centre of the outer wall
R_INNER = cfg.BORE_R + T_IN / 2
WET = (cfg.BORE_R + T_IN, cfg.OUTSIDE_R - T_OUT)       # the floor of the store
R_SHAFT = structure.SHAFT_D / 2
G = 9.80665
PHI_SHEAR, PHI_FLEXURE, PHI_ANCHOR, PHI_BEARING = .75, .9, .75, .65


def loads():
    """Unfactored loads on the slab: ring loads in N/m at a radius, ring moments in N·m/m and pressures in Pa over a band."""
    extra = F["loads"]
    rig = structure.C["rig"]
    lid = extra["lid_kg_per_m2"] * G * math.pi * cfg.OUTSIDE_R**2
    coolers = (cfg.COOLERS * logistics.C["cooler_load_t"] + cfg.FRAMES * extra["cooler_frame_steel_t"]) * 1e3 * G
    power = (rig["diesel_t"] + rig["turbine_t"]) * 1e3 * G
    outer = T_OUT * walls.HEIGHT * GAMMA_C + (coolers + lid / 2) / (2 * math.pi * R_OUTER)
    inner = T_IN * walls.HEIGHT * GAMMA_C + (power + lid / 2) / (2 * math.pi * R_INNER)
    shaft = next(case["axial"] for case in structure.C["shaft"]["chosen"]["cases"] if case["key"] == "complete")
    cage = extra["cage_posts_and_decks_t"] * 1e3 * G
    foot_outer = reinforcement.C["proposed"]["foot"]
    foot_inner = walls.base(T_IN, R_INNER, walls.pressure(0))
    return dict(
        rings=[("Outer wall, with the coolers and half the lid", R_OUTER, outer), ("Inner wall, with the power levels and half the lid", R_INNER, inner),
               ("Shaft, store complete", R_SHAFT, shaft / (2 * math.pi * R_SHAFT)), ("Cage posts and decks", cfg.BORE_R - .07, cage / (2 * math.pi * (cfg.BORE_R - .07)))],
        liquid=("Liquid on the floor of the store", WET, walls.pressure(0)),
        floor=("Load on the floor of the bore", (0., cfg.BORE_R), extra["bore_floor_kpa"] * 1e3),
        moments=[("Foot of the outer wall", R_OUTER, foot_outer["moment"]), ("Foot of the inner wall", R_INNER, -foot_inner["moment"])],
        tie=(foot_outer["shear"], foot_inner["shear"]), totals=dict(coolers=coolers, lid=lid, power=power, shaft=shaft, cage=cage))


L = loads()


def mesh():
    """Node radii, with a node at every load line and band edge."""
    marks = sorted({0., RADIUS, *WET, cfg.BORE_R, *(r for _, r, _ in L["rings"]), BASE["ring_outside_m"] / 2})
    nodes = []
    for a, b in zip(marks, marks[1:]):
        n = max(1, round((b - a) / F["mesh_m"]))
        nodes += [a + (b - a) * i / n for i in range(n)]
    return np.array(nodes + [RADIUS])


NODES = mesh()
GAUSS = [(.5 - math.sqrt(3 / 7 + 2 / 7 * math.sqrt(6 / 5)) / 2, (18 - math.sqrt(30)) / 72), (.5 - math.sqrt(3 / 7 - 2 / 7 * math.sqrt(6 / 5)) / 2, (18 + math.sqrt(30)) / 72),
         (.5 + math.sqrt(3 / 7 - 2 / 7 * math.sqrt(6 / 5)) / 2, (18 + math.sqrt(30)) / 72), (.5 + math.sqrt(3 / 7 + 2 / 7 * math.sqrt(6 / 5)) / 2, (18 - math.sqrt(30)) / 72)]


def shapes(x, length):
    """Hermite cubic shape functions, and their first and second derivatives with respect to radius."""
    n = np.array([1 - 3 * x**2 + 2 * x**3, length * (x - 2 * x**2 + x**3), 3 * x**2 - 2 * x**3, length * (-x**2 + x**3)])
    d1 = np.array([-6 * x + 6 * x**2, length * (1 - 4 * x + 3 * x**2), 6 * x - 6 * x**2, length * (-2 * x + 3 * x**2)]) / length
    d2 = np.array([-6 + 12 * x, length * (-4 + 6 * x), 6 - 12 * x, length * (-2 + 6 * x)]) / length**2
    return n, d1, d2


def solve(thickness, ground, liquid=True, weight=True, others=True):
    """Settlement and slope at every node for a slab of this thickness on ground of this stiffness."""
    rigidity = EC * thickness**3 / (12 * (1 - NU**2))
    size = 2 * len(NODES)
    k = np.zeros((size, size)); f = np.zeros(size)
    def pressure(r):
        q = thickness * GAMMA_C if weight else 0.
        for (_, (a, b), p), on in ((L["liquid"], liquid), (L["floor"], others)):
            if on and a <= r <= b: q += p
        return q
    for e, (a, b) in enumerate(zip(NODES, NODES[1:])):
        length = b - a
        ke = np.zeros((4, 4)); fe = np.zeros(4)
        for x, weight_ in GAUSS:
            r = a + x * length
            n, d1, d2 = shapes(x, length)
            bend = np.outer(d2, d2) + np.outer(d1, d1) / r**2 + NU * (np.outer(d2, d1) + np.outer(d1, d2)) / r
            ke += weight_ * length * 2 * math.pi * r * (rigidity * bend + ground * np.outer(n, n))
            fe += weight_ * length * 2 * math.pi * r * pressure(r) * n
        dofs = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        k[np.ix_(dofs, dofs)] += ke; f[dofs] += fe
    if others:
        for _, r, line in L["rings"]:
            f[2 * int(np.argmin(abs(NODES - r)))] += 2 * math.pi * r * line
    if liquid:
        for _, r, moment in L["moments"]:
            f[2 * int(np.argmin(abs(NODES - r))) + 1] += 2 * math.pi * r * moment
    free = [i for i in range(size) if i != 1]                 # no slope at the centre
    u = np.zeros(size)
    u[free] = np.linalg.solve(k[np.ix_(free, free)], f[free])
    return dict(u=u, rigidity=rigidity, ground=ground, thickness=thickness, applied=f[::2].sum(), pressure=pressure)


def results(s):
    """Settlement, contact pressure, moments and shear along the radius, from a solution."""
    u, rigidity, ground = s["u"], s["rigidity"], s["ground"]
    r_out, w, mr, mt, q = [], [], [], [], []
    inside = 0.                                               # net downward force inside the radius
    rings = sorted((r, line) for _, r, line in L["rings"]) if s.get("others", True) else []
    for e, (a, b) in enumerate(zip(NODES, NODES[1:])):
        length = b - a
        ue = u[2 * e:2 * e + 4]
        for x in (0., 1.):
            n, d1, d2 = shapes(x, length)
            r = a + x * length
            curvature, slope = d2 @ ue, d1 @ ue
            hoop = slope / r if r > 1e-9 else curvature
            r_out.append(r); w.append(n @ ue)
            mr.append(-rigidity * (curvature + NU * hoop)); mt.append(-rigidity * (hoop + NU * curvature))
    return dict(r=np.array(r_out), w=np.array(w), mr=np.array(mr), mt=np.array(mt), pressure=ground * np.array(w))


def shear(s, with_rings=True):
    """Shear force per metre of circumference just inside and just outside each node, from equilibrium."""
    u, ground = s["u"], s["ground"]
    total = np.zeros(len(NODES))
    for e, (a, b) in enumerate(zip(NODES, NODES[1:])):
        length = b - a
        ue = u[2 * e:2 * e + 4]
        net = 0.
        for x, weight_ in GAUSS:
            r = a + x * length
            n, _, _ = shapes(x, length)
            net += weight_ * length * 2 * math.pi * r * (s["pressure"](r) - ground * (n @ ue))
        total[e + 1] = total[e] + net
    before, after = total.copy(), total.copy()
    if with_rings:
        for _, r, line in L["rings"]:
            i = int(np.argmin(abs(NODES - r)))
            before[i + 1:] += 2 * math.pi * r * line; after[i:] += 2 * math.pi * r * line
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.nan_to_num(before / (2 * math.pi * NODES)), np.nan_to_num(after / (2 * math.pi * NODES))


def at(values, r):
    return float(np.interp(r, NODES, values))


def one_way(thickness, ratio, stirrups):
    """Design one-way shear strength of the slab per metre, ACI 318-19 Section 22.5.5."""
    d = thickness - F["cover_mm"] / 1000 - .05
    size = min(1., math.sqrt(2 / (1 + .004 * d * 1000)))
    stress = .17 * math.sqrt(FC) if stirrups else .66 * size * ratio**(1 / 3) * math.sqrt(FC)
    return PHI_SHEAR * stress * 1e6 * d, d


def design(thickness, ground_name=None):
    ground = GROUND[ground_name or F["design_ground"]]
    full = solve(thickness, ground)
    res = results(full)
    before, after = shear(full)
    empty = results(solve(thickness, ground, liquid=False))
    d = thickness - F["cover_mm"] / 1000 - .05
    # Flexure: the largest moments each way, top and bottom. Positive moment puts the bottom in tension.
    def steel(moment):
        return LOAD * abs(moment) / (PHI_FLEXURE * FY * .9 * d)
    least = .0018 * thickness / 2                                   # ACI 318-19 Section 8.6.1, each face
    faces = {}
    for name, values in (("radial", res["mr"]), ("hoop", res["mt"])):
        for face, moment in (("bottom", values.max()), ("top", values.min())):
            area = max(least, steel(moment)) if (moment > 0) == (face == "bottom") else least
            faces[name, face] = dict(moment=moment, area=area, bars=walls.one_face(area))
    # Tension across the floor of the store from the feet of the two walls, shared by the two faces.
    tie = max(L["tie"])
    tie_area = LOAD * tie / (PHI_FLEXURE * FY)
    # Shear at a depth d from each face of each wall.
    ratio = max(faces["radial", "bottom"]["area"], faces["radial", "top"]["area"]) / d
    sections = []
    for name, r, half in (("outer wall", R_OUTER, T_OUT / 2), ("inner wall", R_INNER, T_IN / 2)):
        for side in (-1, 1):
            at_r = r + side * (half + d)
            if not 0 < at_r < RADIUS: continue
            sections.append(dict(wall=name, side="inside" if side < 0 else "outside", r=at_r, shear=abs(at(before, at_r))))
    worst = max(sections, key=lambda x: x["shear"])
    plain, _ = one_way(thickness, ratio, False)
    tied, _ = one_way(thickness, ratio, True)
    # Punching round the base ring of the shaft, ACI 318-19 Section 22.6.
    ring = BASE["ring_outside_m"] / 2
    perimeter = 2 * math.pi * (ring + d / 2)
    size = min(1., math.sqrt(2 / (1 + .004 * d * 1000)))
    punch_strength = PHI_SHEAR * .33 * size * math.sqrt(FC) * 1e6 * perimeter * d
    relief = sum(full["ground"] * at(res["w"][::2] if False else np.interp(NODES, res["r"], res["w"]), r) * 2 * math.pi * r * F["mesh_m"]
                 for r in np.arange(F["mesh_m"] / 2, ring + d / 2, F["mesh_m"]))
    punch = LOAD * max(0., L["totals"]["shaft"] - relief + thickness * GAMMA_C * math.pi * (ring + d / 2)**2)
    w_nodes = np.interp(NODES, res["r"], res["w"])
    w_empty = np.interp(NODES, empty["r"], empty["w"])
    return dict(thickness=thickness, d=d, ground=ground, res=res, before=before, after=after, w=w_nodes, w_empty=w_empty,
                pressure=dict(most=res["pressure"].max(), least=res["pressure"].min(), mean=full["applied"] / (math.pi * RADIUS**2)),
                settle=dict(shaft=at(w_nodes, R_SHAFT), inner=at(w_nodes, R_INNER), outer=at(w_nodes, R_OUTER), most=w_nodes.max(), least=w_nodes.min(),
                            fill_shaft=at(w_nodes - w_empty, R_SHAFT), fill_inner=at(w_nodes - w_empty, R_INNER)),
                faces=faces, tie=tie, tie_area=tie_area, sections=sections, worst=worst, vu=LOAD * worst["shear"], plain=plain, tied=tied,
                stirrups=LOAD * worst["shear"] > plain, shear_ok=LOAD * worst["shear"] <= tied,
                punch=punch, punch_strength=punch_strength, applied=full["applied"],
                reaction=float(sum(full["ground"] * .5 * (w_nodes[i] + w_nodes[i + 1]) * math.pi * (NODES[i + 1]**2 - NODES[i]**2) for i in range(len(NODES) - 1))))


def anchorage():
    """The base of the shaft: a ring plate on anchor bolts cast into the slab.

    The top of the shaft is held by the support rig before the first pod is loaded. The base is still
    designed to stand alone with the worst out-of-balance load, as an accident, so that the pods do not
    depend on the rig alone.
    """
    n, circle = BASE["bolts"], BASE["bolt_circle_m"]
    shaft = structure.C["shaft"]
    cases = []
    for group, factor, source in (("Top held", LOAD, shaft["chosen"]["cases"]), ("Top free, as an accident", BASE["accident_load_factor"], shaft["free"]["cases"])):
        for case in source:
            moment, axial = abs(case["result"]["base"]), case["axial"]
            if moment < 1: continue
            tension = factor * (4 * moment / (n * circle) - axial / n)
            line = factor * (axial / (math.pi * circle) + 4 * moment / (math.pi * circle**2))
            cases.append(dict(group=group, name=case["name"] if "name" in case else case["key"], key=case["key"], factor=factor, moment=moment, axial=axial,
                              tension=max(0., tension), line=line, accident=group != "Top held", shear=abs(case["result"].get("reaction", 0))))
    stress = min(BASE["anchor_fu_mpa"], 1.9 * BASE["anchor_fy_mpa"], 860) * 1e6
    worst = max(cases, key=lambda c: c["tension"])
    for name, diameter, area in BASE["sizes"]:
        strength = PHI_ANCHOR * area / 1e6 * stress
        if all(c["tension"] <= strength * (BASE["most_use_in_accident"] if c["accident"] else 1) for c in cases): break
    else:
        raise ValueError("No anchor in the list holds the base of the shaft. Add bolts or a larger size.")
    width = (BASE["ring_outside_m"] - BASE["ring_inside_m"]) / 2
    bearing = PHI_BEARING * .85 * FC * 1e6 * width
    line = max(c["line"] for c in cases)
    pitch = math.pi * circle / n
    plate = math.sqrt(4 * (worst["tension"] * pitch / 8) / (PHI_FLEXURE * BASE["plate_fy_mpa"] * 1e6 * pitch))
    hairpins = worst["tension"] * n / math.pi / (PHI_ANCHOR * FY)
    drive_torque = 0.
    friction = BASE["friction"] * min(c["axial"] for c in cases) * circle / 2
    return dict(cases=cases, worst=worst, bolt=name, diameter=diameter / 1000, area=area / 1e6, strength=strength, use=worst["tension"] / strength,
                width=width, bearing=bearing, line=line, pitch=pitch, plate=plate, hairpins=hairpins, friction=friction, n=n, circle=circle)


def compute():
    def least(options):
        """The thinnest slab that is strong enough, with shear ties if it needs them."""
        return next(o for o in options if o["shear_ok"] and o["punch"] <= o["punch_strength"])
    table = {name: [design(t, name) for t in F["thickness_options_m"]] for name in GROUND}
    grounds = {name: least(options) for name, options in table.items()}
    options = table[F["design_ground"]]
    chosen = grounds[F["design_ground"]]
    drawn = cfg.PROJECT["logistics"]["concrete"]["slab_thickness_m"]
    as_drawn = {name: next(o for o in options_ if abs(o["thickness"] - drawn) < 1e-9) for name, options_ in table.items()}
    weights = dict(walls=(T_OUT * 2 * math.pi * R_OUTER + T_IN * 2 * math.pi * R_INNER) * walls.HEIGHT * GAMMA_C,
                   liquid=L["liquid"][2] * math.pi * (WET[1]**2 - WET[0]**2), slab=chosen["thickness"] * GAMMA_C * math.pi * RADIUS**2,
                   floor=L["floor"][2] * math.pi * cfg.BORE_R**2, **L["totals"])
    return dict(options=options, chosen=chosen, grounds=grounds, drawn=drawn, as_drawn=as_drawn, table=table, weights=weights, total=sum(weights.values()),
                area=math.pi * RADIUS**2, base=anchorage())


C = compute()


def check():
    c = C
    # The spring used gives back the settlement of a stiff slab on an elastic ground.
    name = F["design_ground"]
    stiff_slab = results(solve(50., GROUND[name]))["w"].mean()
    mean = solve(50., GROUND[name])["applied"] / (math.pi * RADIUS**2)
    assert abs(stiff_slab - mean * 2 * RADIUS * (1 - F["ground_poisson"]**2) * math.pi / (4 * MODULUS[name])) < 2e-2 * stiff_slab
    for d in list(c["grounds"].values()) + c["options"]:
        # The ground pushes back with the whole load, and nowhere does the slab lift off it.
        assert abs(d["reaction"] - d["applied"]) < 2e-3 * d["applied"], (d["reaction"], d["applied"])
        assert d["pressure"]["least"] > 0
    assert abs(c["total"] - c["chosen"]["applied"]) < 1e-6 * c["total"]
    # A stiff slab on soft ground settles evenly: the plate model returns the mean pressure.
    stiff = results(solve(50., 1e5))
    assert abs(stiff["pressure"].max() / stiff["pressure"].min() - 1) < 2e-3
    # A plate under even pressure with nothing else on it settles evenly, with no bending.
    even = solve(1.5, GROUND[F["design_ground"]], liquid=False, others=False)
    flat = results(even)
    assert abs(flat["w"].max() / flat["w"].min() - 1) < 1e-6 and abs(flat["mr"]).max() < 1e-3 * 1.5 * GAMMA_C * RADIUS**2
    assert c["chosen"]["shear_ok"] and c["chosen"]["punch"] <= c["chosen"]["punch_strength"]
    assert c["base"]["line"] <= c["base"]["bearing"]


def summary():
    c = C
    d, b = c["chosen"], c["base"]
    return (f"Foundation: slab {d['thickness']:.2f} m, {'with' if d['stirrups'] else 'without'} shear ties. On {F['design_ground']} the pressure is {d['pressure']['least']/1e3:.0f} to {d['pressure']['most']/1e3:.0f} kPa "
            f"and the fill lowers the inner wall {(d['settle']['fill_inner']-d['settle']['fill_shaft'])*1000:.1f} mm more than the shaft. Shaft base: {b['n']} {b['bolt']} anchors.")
