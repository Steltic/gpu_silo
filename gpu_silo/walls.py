"""Check 3: the two concrete walls of the silo under the liquid in the store between them.

The outer wall is in hoop tension and the inner wall in hoop compression. Neither is post-tensioned.
Thickness may change at each jumpform lift. The outside face of the outer wall and the bore face of
the inner wall stay plumb, so the extra thickness goes into the store.

Reinforced to ACI 350-06 with ACI 318-19. SI units: metres, newtons, pascals.
"""
import math

from . import design as cfg

W = cfg.PROJECT["structure"]["walls"]
G = 9.80665
FC = W["concrete_fc_mpa"] * 1e6
FY = W["fy_mpa"] * 1e6
FS = W["service_steel_stress_mpa"] * 1e6
ES = 200e9
EC = 4700 * math.sqrt(W["concrete_fc_mpa"]) * 1e6          # ACI 318-19 19.2.2.1, normal-weight concrete
N_RATIO = ES / EC
NU = W["poisson"]
GAMMA = cfg.FLUID["density_kg_m3"] * G
LOAD = W["fluid_load_factor"]
HEIGHT = cfg.SILO["height_m"]
LIFT = cfg.SILO["concrete_lift_m"]
LIFTS = round(HEIGHT / LIFT)
LIQUID = cfg.LIQUID_TOP
R_OUT = cfg.OUTSIDE_R
R_BORE = cfg.BORE_R
STEP = W["thickness_step_mm"] / 1000
T_MIN = W["min_thickness_mm"] / 1000
COVER = W["cover_mm"] / 1000
BARS = [dict(name=name, d=d / 1000, area=area / 1e6) for name, d, area in W["bars"]]
VERTICAL = W["vertical_bar_mm"] / 1000
S_MIN, S_MAX = W["min_bar_spacing_mm"] / 1000, W["max_bar_spacing_mm"] / 1000
TARGET = cfg.FLUID["target_volume_us_gal"] * .003785411784
FCT = .7 * .3 * W["concrete_fc_mpa"]**(2 / 3) * 1e6        # lower characteristic tensile strength, fib Model Code
PHI_SHEAR, PHI_COMPRESSION = .75, .65


def pressure(z):
    return GAMMA * max(0., LIQUID - z)


def steps(value):
    return math.ceil(value / STEP - 1e-9) * STEP


def arrangement(area, bars=None, faces=None):
    """Fewest layers, then the smallest bar, that gives the bar area per metre within the spacing limits."""
    for faces in range(1, (faces or W["max_layers_per_face"]) + 1):
        layers = 2 * faces
        for bar in bars or BARS:
            spacing = math.floor(layers * bar["area"] / area * 100 + 1e-9) / 100       # down to 10 mm
            if spacing >= S_MIN - 1e-9:
                spacing = min(spacing, S_MAX)
                return dict(bar=bar, layers=layers, per_face=faces, spacing=spacing, provided=layers * bar["area"] / spacing)
    return None


def one_face(area):
    """Bars for steel needed on one face only: one layer if it fits, otherwise two."""
    for layers in range(1, W["max_layers_per_face"] + 1):
        for bar in BARS:
            spacing = math.floor(layers * bar["area"] / area * 100 + 1e-9) / 100
            if spacing >= S_MIN - 1e-9:
                spacing = min(spacing, S_MAX)
                return dict(bar=bar, layers=layers, spacing=spacing, provided=layers * bar["area"] / spacing)
    return None


def fit(bars):
    """Least thickness that holds the layers: cover, the hoop layers outside the verticals, and a core to place concrete in."""
    face = COVER + bars["per_face"] * bars["bar"]["d"] + (bars["per_face"] - 1) * W["layer_gap_mm"] / 1000 + VERTICAL
    return 2 * face + W["core_mm"] / 1000


def crack_width(bars, stress=FS, modulus=ES, bond=1.):
    """Largest crack width in a member in direct tension, ACI 224.2R: w = 0.10 fs (dc A)^(1/3) × 10⁻³ in inches and ksi.

    The expression is for steel. For a bar of another modulus the stress is scaled to the same strain, and a bond factor applies.
    """
    face = COVER + (bars["per_face"] * bars["bar"]["d"] + (bars["per_face"] - 1) * W["layer_gap_mm"] / 1000) / 2
    dc = COVER + bars["bar"]["d"] / 2
    effective = 2 * face * bars["spacing"] / bars["per_face"]
    inch = .0254
    return bond * .10 * (stress * ES / modulus / 6.894757e6) * (dc / inch * effective / inch**2)**(1 / 3) * 1e-3 * inch


def outer_lift(index, above):
    """One lift of the outer wall, designed at its lower edge. Thickness never grows upwards."""
    z = index * LIFT
    p = pressure(z)
    t = max(T_MIN, above)
    while True:
        radius = R_OUT - t                              # the wet face
        tension = p * radius
        need = max(tension / FS, W["min_steel_ratio"] * t)
        bars = arrangement(need)
        if bars is None:
            raise ValueError(f"The hoop steel for outer wall lift {index+1} does not fit in the layers allowed. Allow a larger bar or closer spacing.")
        if bars["provided"] / t <= W["max_hoop_steel_ratio"] + 1e-12 and t >= fit(bars) - 1e-9: break
        t = round(t + STEP, 6)
    uncracked = (W["shrinkage_strain"] * ES * bars["provided"] + tension) / (t + N_RATIO * bars["provided"])
    # Thickness at which the concrete would not crack: the same expression solved for t with the tensile strength.
    no_crack = (W["shrinkage_strain"] * ES * need + tension) / FCT - N_RATIO * need
    return dict(lift=index + 1, z0=z, z1=z + LIFT, pressure=p, t=t, radius=radius, tension=tension, factored=LOAD * tension,
                need=need, bars=bars, ratio=bars["provided"] / t, stress=tension / bars["provided"] if tension else 0.,
                uncracked=uncracked, no_crack=max(T_MIN, no_crack), crack=crack_width(bars) * (tension / bars["provided"] / FS if tension else 0),
                governs="minimum steel" if need > tension / FS + 1e-12 else "hoop tension")


def base(t, radius, p):
    """Moment and shear at the foot of a wall built into the base slab, from the theory of a long cylinder."""
    beta = (3 * (1 - NU * NU))**.25 / math.sqrt(radius * t)
    depth = LIQUID
    moment = p / (2 * beta * beta) * (1 - 1 / (beta * depth))
    shear = p / beta * (1 - 1 / (2 * beta * depth))
    d = t - COVER - VERTICAL / 2
    vertical = moment / (FS * .9 * d)
    vu = LOAD * shear
    vc = PHI_SHEAR * .17 * math.sqrt(W["concrete_fc_mpa"]) * 1e6 * d          # ACI 318-19 22.5, with minimum shear reinforcement
    sd = PHI_SHEAR * FY / (LOAD * W["shear_steel_stress_mpa"] * 1e6)          # ACI 350-06 9.2.6
    ties = max(0., sd * (vu - vc)) / (PHI_SHEAR * FY * d)                     # m² of tie per metre run per metre height
    return dict(beta=beta, moment=moment, shear=shear, d=d, vertical=vertical, vu=vu, vc=vc, sd=sd, ties=ties,
                reach=1 / beta, bars=one_face(vertical))


def buckling(t, creep=None):
    """Elastic critical pressure of the inner wall, and the pressure allowed in design, for a thickness t.

    The critical pressure is that of a cylinder of moderate length held round at both ends (Donnell),
    with the modulus reduced for creep. The design value allows for imperfections and carries a strength reduction factor.
    """
    b = W["inner_wall_buckling"]
    radius = R_BORE + t / 2
    modulus = EC / (1 + (b["creep_coefficient"] if creep is None else creep))
    critical = .855 / (1 - NU * NU)**.75 * modulus * (t / radius)**2.5 * radius / HEIGHT
    return critical, b["strength_reduction"] * b["imperfection_factor"] * critical


def inner_wall(creep=None):
    """Uniform thickness for the inner wall: buckling under the pressure of the store, then crushing."""
    b = W["inner_wall_buckling"]
    p = pressure(0)
    modulus = EC / (1 + (b["creep_coefficient"] if creep is None else creep))
    t = T_MIN
    while True:
        radius = R_BORE + t / 2
        # Elastic critical pressure of a cylinder of moderate length held round at both ends (Donnell).
        critical = .855 / (1 - NU * NU)**.75 * modulus * (t / radius)**2.5 * radius / HEIGHT
        design = b["strength_reduction"] * b["imperfection_factor"] * critical
        compression = p * (R_BORE + t)
        strength = PHI_COMPRESSION * .80 * .85 * FC * t
        if LOAD * p <= design and LOAD * compression <= strength: break
        t = round(t + STEP, 6)
    # Lower bound: a ring with no help from the ends, with the stiffness ACI 318 gives a column under sustained load.
    ring = (R_BORE + .3) * (LOAD * p * 12 / (.75 * 3 * .2 * EC))**(1 / 3)
    for _ in range(20): ring = (R_BORE + ring / 2) * (LOAD * p * 12 / (.75 * 3 * .2 * EC))**(1 / 3)
    steel = W["min_steel_ratio"] * t
    return dict(t=t, radius=radius, pressure=p, critical=critical, design=design, modulus=modulus, compression=compression,
                factored=LOAD * compression, strength=strength, stress=compression / t, ring=steps(ring),
                omega=HEIGHT / math.sqrt(radius * t), bars=arrangement(steel), steel=steel, base=base(t, radius, p))


def compute():
    lifts = []
    above = T_MIN
    for index in reversed(range(LIFTS)):
        lift = outer_lift(index, above)
        above = lift["t"]
        lifts.append(lift)
    lifts.reverse()
    inner = inner_wall()
    foot = base(lifts[0]["t"], lifts[0]["radius"] + lifts[0]["t"] / 2, pressure(0))
    present = dict(outer=cfg.SILO["outer_wall_m"], inner=cfg.SILO["inner_wall_m"])
    volume = concrete = hoop = 0.
    for lift in lifts:
        wet = max(0., min(lift["z1"], LIQUID) - lift["z0"])
        lift["gap"] = lift["radius"] - (R_BORE + inner["t"])
        volume += math.pi * (lift["radius"]**2 - (R_BORE + inner["t"])**2) * wet
        lift["concrete"] = math.pi * (R_OUT**2 - lift["radius"]**2 + (R_BORE + inner["t"])**2 - R_BORE**2) * LIFT
        concrete += lift["concrete"]
        lift["hoop_t"] = lift["bars"]["provided"] * 2 * math.pi * (R_OUT - lift["t"] / 2) * LIFT * 7850 / 1000
        hoop += lift["hoop_t"]
    now_volume = math.pi * ((R_OUT - present["outer"])**2 - (R_BORE + present["inner"])**2) * LIQUID
    now_concrete = math.pi * (R_OUT**2 - (R_OUT - present["outer"])**2 + (R_BORE + present["inner"])**2 - R_BORE**2) * HEIGHT
    inner_steel = 2 * inner["bars"]["provided"] * 2 * math.pi * inner["radius"] * HEIGHT * 7850 / 1000
    vertical = sum(max(W["min_steel_ratio"] * lift["t"], 0) * 2 * math.pi * (R_OUT - lift["t"] / 2) * LIFT for lift in lifts) * 7850 / 1000
    present_tension = pressure(0) * (R_OUT - present["outer"])
    lift_steel = [lift["hoop_t"] + W["min_steel_ratio"] * lift["t"] * 2 * math.pi * (R_OUT - lift["t"] / 2) * LIFT * 7.85
                  + inner_steel / LIFTS for lift in lifts]
    return dict(lifts=lifts, inner=inner, foot=foot, volume=volume, now_volume=now_volume, target=TARGET, concrete=concrete,
                now_concrete=now_concrete, hoop_t=hoop, inner_steel_t=inner_steel, vertical_t=vertical, present=present,
                present_tension=present_tension, present_steel=present_tension / FS,
                present_ratio=present_tension / FS / present["outer"], gap_base=lifts[0]["gap"], gap_top=lifts[-1]["gap"],
                tie_total=pressure(0) * (R_OUT - present["outer"] - R_BORE - present["inner"]),
                present_buckling=buckling(present["inner"]), lift_steel=lift_steel, steel_t=hoop + inner_steel + vertical)


C = compute()


def check():
    c = C
    assert all(a["t"] >= b["t"] for a, b in zip(c["lifts"], c["lifts"][1:])), "the outer wall must not thicken upwards"
    for lift in c["lifts"]:
        assert lift["bars"]["provided"] >= lift["need"] - 1e-12 and lift["stress"] <= FS * (1 + 1e-9)
        assert S_MIN - 1e-9 <= lift["bars"]["spacing"] <= S_MAX + 1e-9 and lift["t"] >= T_MIN
    # The whole hoop force on a cut through the silo is the pressure on the gap. The two walls must add up to it.
    lift = c["lifts"][0]
    inner = c["inner"]
    assert abs(lift["tension"] - inner["compression"] - lift["pressure"] * lift["gap"]) < 1e-6 * lift["tension"]
    assert LOAD * inner["pressure"] <= inner["design"] and inner["factored"] <= inner["strength"]
    assert c["volume"] >= c["target"], "the store no longer holds its target volume with these walls"


def summary():
    c = C
    first, last = c["lifts"][0], c["lifts"][-1]
    return (f"Walls: outer {first['t']*1000:.0f} mm at the base to {last['t']*1000:.0f} mm at the top, inner {c['inner']['t']*1000:.0f} mm. "
            f"Hoop tension {first['tension']/1000:,.0f} kN/m at the base. Store {c['volume']:,.0f} m³ against a target of {c['target']:,.0f} m³.")
