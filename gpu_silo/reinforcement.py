"""Scope of reinforcement for the outer wall: carbon steel, stainless steel and glass FRP.

Each scheme is designed lift by lift for the same hoop tension, with the rules of walls.py for layers,
spacing and room in the wall. What changes between schemes is the stress the bar may carry, its stiffness
and the sizes it comes in. The temperatures are those of check 5.

SI units: metres, newtons, pascals.
"""
import math

from . import design as cfg
from . import thermal
from . import walls

R = walls.W["reinforcement"]
CRACK = R["crack_limit_mm"] / 1000
SEGMENTS = R["segments_per_lift"]
SCHEMES = {s["key"]: s for s in R["schemes"]}
INNER = thermal.C["creep"]["t"]                    # inner wall, with the creep of warm concrete


def allowed(scheme):
    """Design strength and the limits on service stress of a bar, in Pa. None where a limit does not apply."""
    f = scheme["environment_factor"] * scheme["strength_mpa"] * 1e6
    return dict(design=scheme["phi"] * f,
                service=scheme["service_stress_mpa"] * 1e6 if scheme["service_stress_mpa"] else None,
                sustained=scheme["sustained_fraction"] * f if scheme["sustained_fraction"] else None)


def lift(scheme, index, above):
    limits = allowed(scheme)
    modulus = scheme["modulus_gpa"] * 1e9
    bars = [dict(name=name, d=d / 1000, area=area / 1e6) for name, d, area in scheme["bars"]]
    faces = scheme["max_layers_per_face"]
    z = index * walls.LIFT
    p = walls.pressure(z)
    t = max(walls.T_MIN, above)
    while True:
        radius = walls.R_OUT - t
        tension = p * radius
        needs = {"strength": walls.LOAD * tension / limits["design"], "least reinforcement": walls.W["min_steel_ratio"] * t}
        if limits["service"]: needs["service stress"] = tension / limits["service"]
        if limits["sustained"]: needs["sustained stress"] = tension / limits["sustained"]
        governs = max(needs, key=needs.get)
        need = needs[governs]
        while True:
            chosen = walls.arrangement(need, bars, faces)
            if chosen is None: break
            stress = tension / chosen["provided"]
            crack = walls.crack_width(chosen, stress, modulus, scheme["bond"]) if tension else 0.
            if not scheme["crack_limited"] or crack <= CRACK: break
            governs, need = "crack width", need * 1.01
        if chosen is None:
            raise ValueError(f"{scheme['name']}: the bars for lift {index+1} do not fit in {2*faces} layers.")
        if chosen["provided"] / t <= walls.W["max_hoop_steel_ratio"] + 1e-12 and t >= walls.fit(chosen) - 1e-9: break
        t = round(t + walls.STEP, 6)
    # Winter: the store at its return temperature against the winter design air, wall not insulated and insulated.
    depth = walls.COVER + (chosen["per_face"] * chosen["bar"]["d"] + (chosen["per_face"] - 1) * walls.W["layer_gap_mm"] / 1000) / 2
    winter = {}
    for key, clad in (("bare", False), ("clad", True)):
        wall = thermal.through(t, thermal.HOT, thermal.AMBIENT["winter_design_c"], thermal.FILMS["outside_wind"], clad)
        extra = thermal.bar_stress(t, depth, wall["gradient"], modulus)
        winter[key] = dict(gradient=wall["gradient"], extra=extra, stress=stress + extra,
                           crack=walls.crack_width(chosen, stress + extra, modulus, scheme["bond"]) if tension else 0.)
    mid = walls.R_OUT - t / 2
    hoop = chosen["provided"] * 2 * math.pi * mid * walls.LIFT * scheme["density_kg_m3"]
    vertical = walls.W["min_steel_ratio"] * t * 2 * math.pi * mid * walls.LIFT * scheme["density_kg_m3"]
    return dict(lift=index + 1, z0=z, z1=z + walls.LIFT, pressure=p, t=t, radius=radius, tension=tension, need=need, governs=governs,
                bars=chosen, ratio=chosen["provided"] / t, stress=stress, strain=stress / modulus, growth=stress / modulus * mid,
                crack=crack, winter=winter, use=walls.LOAD * tension / (limits["design"] * chosen["provided"]),
                hoop=hoop, vertical=vertical, cage=hoop + vertical,
                concrete=math.pi * (walls.R_OUT**2 - radius**2) * walls.LIFT)


def vertical_gradient(t, gradient, modulus):
    """Vertical bending from a gradient across the wall, on a section cracked on its cold face, with the least vertical steel.

    The wall is long, so it cannot curve up its height either. The curvature it is denied is α ΔT / t.
    """
    area = walls.W["min_steel_ratio"] * t / 2                                  # one face
    d = t - walls.COVER - walls.BARS[-1]["d"] - walls.VERTICAL / 2             # inside one layer of the largest hoop bar
    n = modulus / walls.EC
    k = math.sqrt(2 * area / d * n + (area / d * n)**2) - area / d * n
    inertia = (k * d)**3 / 3 + n * area * (d - k * d)**2
    moment = walls.EC * inertia * thermal.ALPHA * gradient / t
    return dict(moment=moment, stress=n * moment * (d - k * d) / inertia, d=d, area=area)


def foot(scheme, first):
    """Foot of the outer wall, built into the base slab, designed for strength with this bar."""
    limits = allowed(scheme)
    base = walls.base(first["t"], walls.R_OUT - first["t"] / 2, walls.pressure(0))
    vertical = walls.LOAD * base["moment"] / (limits["design"] * .9 * base["d"])
    bars = walls.one_face(vertical)
    most = walls.PHI_SHEAR * .66 * math.sqrt(walls.W["concrete_fc_mpa"]) * 1e6 * base["d"]      # ACI 318-19 22.5.1.2
    ties = max(0., base["vu"] - base["vc"]) / (walls.PHI_SHEAR * walls.FY * base["d"])
    return dict(moment=base["moment"], shear=base["shear"], vu=base["vu"], vc=base["vc"], most=base["vc"] + most, d=base["d"],
                vertical=vertical, bars=bars, ties=ties, reach=base["reach"])


def design(scheme):
    lifts = []
    above = walls.T_MIN
    for index in reversed(range(walls.LIFTS)):
        lifts.append(lift(scheme, index, above))
        above = lifts[-1]["t"]
    lifts.reverse()
    inner_face = walls.R_BORE + INNER
    volume = sum(math.pi * (l["radius"]**2 - inner_face**2) * max(0., min(l["z1"], walls.LIQUID) - l["z0"]) for l in lifts)
    concrete = sum(l["concrete"] for l in lifts)
    inner_concrete = math.pi * (inner_face**2 - walls.R_BORE**2) * walls.HEIGHT
    first = lifts[0]
    # Bar area that the crack limit of the liner would ask for at the base, whatever else governs.
    area = first["bars"]["provided"]
    for_crack = area * max(1., first["crack"] / CRACK)
    return dict(scheme=scheme, lifts=lifts, volume=volume, foot=foot(scheme, first) if scheme["ductile"] else None,
                vertical=vertical_gradient(first["t"], first["winter"]["bare"]["gradient"], scheme["modulus_gpa"] * 1e9), concrete=concrete, inner_concrete=inner_concrete, total_concrete=concrete + inner_concrete,
                bar_mass=sum(l["cage"] for l in lifts), heaviest=max(l["cage"] for l in lifts), thicknesses=sorted({l["t"] for l in lifts}, reverse=True),
                layers=max(l["bars"]["layers"] for l in lifts), crack=max(l["crack"] for l in lifts), growth=max(l["growth"] for l in lifts),
                for_crack=for_crack, ride=thermal.ride(volume), meets_crack=max(l["crack"] for l in lifts) <= CRACK + 1e-9,
                limits=allowed(scheme))


def carbon_fibre():
    """Carbon FRP is not designed lift by lift. Its bar area at the base is set by strain, to hold the same crack width as the proposal."""
    c = R["cfrp"]
    base = C["schemes"][R["adopted"]]["lifts"][0]
    modulus = c["modulus_gpa"] * 1e9
    stress = base["strain"] * modulus / 1.2                 # same strain, less the bond factor of an FRP bar
    area = base["tension"] / stress
    name, d, bar = c["largest_bar"]
    return dict(stress=stress, area=area, creep=c["sustained_fraction"] * c["strength_mpa"] * 1e6, bar=name,
                most=4 * bar / 1e6 / walls.S_MIN, ratio=stress / (c["strength_mpa"] * 1e6))


def compute():
    schemes = {key: design(s) for key, s in SCHEMES.items()}
    # Inner wall: the least reinforcement each way, in ordinary bar. It is in compression, lined on one face and dry on the other.
    inner_mass = 2 * walls.W["min_steel_ratio"] * INNER * 2 * math.pi * (walls.R_BORE + INNER / 2) * walls.HEIGHT * 7850
    return dict(schemes=schemes, proposed=schemes[R["adopted"]], inner=INNER, inner_mass=inner_mass)


def tightest():
    """Crack width at the base of the proposed wall with two layers of its largest bar at the closest spacing allowed."""
    scheme, first = SCHEMES[R["adopted"]], C["proposed"]["lifts"][0]
    name, d, area = scheme["bars"][-1]
    bars = dict(bar=dict(name=name, d=d / 1000, area=area / 1e6), layers=2, per_face=1, spacing=walls.S_MIN, provided=2 * area / 1e6 / walls.S_MIN)
    return walls.crack_width(bars, first["tension"] / bars["provided"], scheme["modulus_gpa"] * 1e9, scheme["bond"])


C = compute()
C["cfrp"] = carbon_fibre()
C["tightest"] = tightest()


def check():
    c = C
    # The carbon steel scheme is the design of check 3, reached by a separate routine.
    for a, b in zip(c["schemes"]["carbon"]["lifts"], walls.C["lifts"]):
        assert abs(a["t"] - b["t"]) < 1e-9 and abs(a["bars"]["provided"] - b["bars"]["provided"]) < 1e-12 and abs(a["crack"] - b["crack"]) < 1e-12
    for key, s in c["schemes"].items():
        scheme = s["scheme"]
        for l in s["lifts"]:
            assert l["bars"]["provided"] >= l["need"] - 1e-12 and l["use"] <= 1 + 1e-9, key
            assert l["ratio"] <= walls.W["max_hoop_steel_ratio"] + 1e-12 and l["t"] >= walls.fit(l["bars"]) - 1e-9, key
            if scheme["crack_limited"]: assert l["crack"] <= CRACK + 1e-12, key
            if s["limits"]["sustained"]: assert l["stress"] <= s["limits"]["sustained"] * (1 + 1e-9), key
        assert all(a["t"] >= b["t"] for a, b in zip(s["lifts"], s["lifts"][1:])), key
    p = c["proposed"]
    # The walls in the design file are the ones designed here.
    assert p["thicknesses"] == [cfg.SILO["outer_wall_m"]] and abs(INNER - cfg.SILO["inner_wall_m"]) < 1e-9, "the walls in the design file are not those of the design report"
    assert p["foot"]["vu"] <= p["foot"]["most"], "the foot of the proposed wall is too thin for its shear"
    assert p["volume"] >= walls.TARGET, "the store no longer holds its target volume with the proposed walls"
    assert p["meets_crack"]


def summary():
    p = C["proposed"]
    first = p["lifts"][0]
    return (f"Reinforcement adopted: {p['scheme']['name']}, outer wall {first['t']*1000:.0f} mm at the base with "
            f"{first['bars']['layers']} layers of {first['bars']['bar']['name']} at {first['bars']['spacing']*1000:.0f} mm, "
            f"crack {first['crack']*1000:.2f} mm. Store {p['volume']:,.0f} m³.")
