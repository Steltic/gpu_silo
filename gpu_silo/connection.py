"""Check 6: the root connection of a pod, the hub of a level and the drive that turns it.

A hub turns on the fixed shaft at each level: a top ring and a bottom ring joined by a drum. Each
truss of a pod hangs from an arm on the top ring by a pin, and bears on an arm on the bottom ring.
A slewing ring under the hub carries the weight and has the gear for the drive. Guide rollers on the
top ring run on the shaft. Together the two take the out-of-balance moment of a part-filled level.

Steel to AISC 360-22, load and resistance factor design. SI units: metres, newtons, pascals.
"""
import math

from . import design as cfg
from . import foundation
from . import structure as st
from . import thermal

R = cfg.PROJECT["structure"]["root"]
DRIVE = cfg.PROJECT["structure"]["level_drive"]
PIN, LUG, HUB = R["pin"], R["lug"], R["hub"]
E = st.E
FACTOR = st.T["dead_load_factor"]
IMPACT = st.T["hoist_impact_factor"]
DEPTH = st.C["design"]["model"]["depth"]                    # between the clevis and the lower bearing
ARM = st.ROOT - R["hub_ring_radius_m"]                      # an arm stands this far out from the hub ring
RATIO = st.SPAN / DEPTH                                     # drop of the tip for each unit of stretch at the root
FY_ARM = 345e6
G = 9.80665


def pin_and_lug(force):
    """Smallest pin, and the thinnest pair of lug plates, for a factored force. AISC 360-22 Sections D5 and J7.

    The pin is in double shear between two lugs on the arm, with the truss plate between them.
    """
    fy, fu = PIN["fy_mpa"] * 1e6, PIN["fu_mpa"] * 1e6
    span = PIN["span_mm"] / 1000
    for mm in PIN["diameters_mm"]:
        d = mm / 1000
        area, modulus = math.pi * d * d / 4, d**3 / 6           # plastic modulus of a round bar
        shear = 1.0 * .6 * fy * area * 2                         # shear yielding on two planes
        bending = .9 * fy * modulus                              # as a beam between the lugs, load at mid-span
        moment = force * span / 4
        if force <= shear and moment <= bending: break
    else:
        raise ValueError("No pin in the list carries the root of the truss.")
    lfy, lfu = LUG["fy_mpa"] * 1e6, LUG["fu_mpa"] * 1e6
    hole = d + LUG["hole_clearance_mm"] / 1000
    for mm in LUG["thickness_mm"]:
        t = mm / 1000                                            # one plate. Two plates share the force.
        be = min(2 * t + .016, 2.5 * d)                          # D5.1, with the plate at least this wide each side of the hole
        a = 1.33 * be + .005                                     # edge distance beyond the hole, D5.2
        checks = {"tension on the net section": .75 * lfu * 2 * t * be,
                  "shear behind the pin": .75 * .6 * lfu * 2 * t * (a + d / 2),
                  "bearing on the pin": .75 * 1.8 * lfy * d * t,
                  "yielding of the plate": .9 * lfy * (2 * be + hole) * t}
        if all(force / 2 <= v for v in checks.values()): break
    else:
        raise ValueError("No lug plate in the list carries the root of the truss.")
    governs = min(checks, key=checks.get)
    return dict(d=d, shear=shear, bending=bending, moment=moment, t=t, be=be, a=a, width=2 * be + hole, checks=checks, governs=governs,
                use=max(force / shear, moment / bending, force / 2 / checks[governs]),
                # Flexibility: the pin bending between the lugs, and the lug plates stretching over the edge distance.
                give=force / FACTOR / IMPACT * (span**3 / (48 * E * math.pi * d**4 / 64) + (a + d) / (2 * t * (2 * be + hole) * E)))


def arm(pull, thrust, weight):
    """The arms on the hub rings for one truss. The top arm carries the pull and the weight as a cantilever. The bottom arm carries the thrust."""
    limit = R["arm_deflection_limit_mm"] / 1000
    for name, area, inertia, plastic, depth, web in R["arm_sections"]:
        area, inertia, plastic, depth, web = area / 1e6, inertia / 1e12, plastic / 1e9, depth / 1000, web / 1000
        bend = weight * ARM**3 / (3 * E * inertia)
        shear = weight * ARM / (E / 2.6 * depth * web)
        drop = bend + shear
        tension, moment = FACTOR * IMPACT * pull, FACTOR * IMPACT * weight * ARM
        pn, mn, vn = .9 * FY_ARM * area, .9 * FY_ARM * plastic, 1.0 * .6 * FY_ARM * depth * web
        ratio = tension / pn
        use = ratio + 8 / 9 * moment / mn if ratio >= .2 else ratio / 2 + moment / mn          # AISC 360-22 H1
        if drop <= limit and use <= 1 and FACTOR * IMPACT * weight <= vn: break
    else:
        raise ValueError("No arm in the list is stiff enough.")
    stretch = (pull + thrust) * ARM / (area * E)                 # the top arm lengthens and the bottom arm shortens
    return dict(name=name, area=area, inertia=inertia, depth=depth, drop=drop, bend=bend, shear_drop=shear, use=use, tension=tension, moment=moment,
                stretch=stretch, kg=area * 7850 * ARM, shear_use=FACTOR * IMPACT * weight / vn)


def compute():
    d = st.C["design"]
    pull, thrust, weight = d["root_pull"], d["root_thrust"], d["root_shear"]
    resultant = math.hypot(pull, weight)
    factored = FACTOR * IMPACT * resultant
    pin = pin_and_lug(factored)
    beam = arm(pull, thrust, weight)
    # Movement of the tip from the root connection, under the dead load of the pod.
    horizontal = beam["stretch"] + pin["give"] * pull / resultant
    tip = dict(arm=beam["drop"], stretch=RATIO * horizontal, pin=pin["give"] * weight / resultant)
    tip["total"] = sum(tip.values())
    c = dict(pull=pull, thrust=thrust, weight=weight, resultant=resultant, factored=factored, pin=pin, arm=beam, tip=tip, horizontal=horizontal)

    # The hub. With a level full the pulls on the top ring balance round it, and so do the thrusts on the bottom ring.
    n = cfg.BAYS
    pod_pull = 2 * pull
    ring_force = pod_pull / (2 * math.sin(math.pi / n))
    ring_area = FACTOR * ring_force / (.9 * FY_ARM)
    drum_r = HUB["drum_diameter_m"] / 2
    ring_r = R["hub_ring_radius_m"]
    ring_plate = math.pi * (ring_r**2 - drum_r**2 + .15 * 2 * drum_r) * HUB["ring_plate_mm"] / 1000      # outside the drum, and 150 mm inside it
    masses = dict(drum=math.pi * HUB["drum_diameter_m"] * HUB["drum_wall_mm"] / 1000 * DEPTH * 7850, rings=2 * ring_plate * 7850,
                  arms=4 * n * beam["kg"] * 1.5,                                                         # two trusses, top and bottom, with lugs and stiffeners
                  floor=math.pi * (st.ROOT**2 - (st.SHAFT_D / 2 + .22)**2) * HUB["floor_kg_per_m2"], bearing=HUB["slewing_ring_t"] * 1e3, drive=HUB["drive_t"] * 1e3)
    hub_mass = sum(masses.values())
    allowance = st.SHAFT["hub_and_floor_t_per_level"] * 1e3
    axial = st.C["level_weight"] + hub_mass * G
    u = st.C["unbalance"]
    cases = []
    for key, name, moment in (("partial", "Level half filled, four pods side by side", u["partial_max"]), ("bunched", "Level full and bunched", u["bunched"])):
        radial = moment / DEPTH
        cases.append(dict(key=key, name=name, moment=moment, radial=radial, roller=radial / DRIVE["guide_rollers_sharing"]))
    worst = cases[0]
    # Stiffness the two bearings must have for the tilt of the hub to stay within its allowance at the pod tips.
    allow = R["allowance_mm"]["hub_tilt"] / 1000
    tilt = allow / st.TIP_R
    rotational = worst["moment"] / tilt
    radial_stiffness = 2 * rotational / DEPTH**2
    c["hub"] = dict(ring_force=ring_force, ring_area=ring_area, masses=masses, mass=hub_mass, allowance=allowance, axial=axial, cases=cases,
                    tilt=tilt, rotational=rotational, radial_stiffness=radial_stiffness, allow=allow,
                    opposite=u["bunched"] / worst["moment"])       # filling in opposite pairs leaves one pod out of balance at most

    # The drive of one level.
    mu, dia = DRIVE["friction_coefficient"], DRIVE["raceway_diameter_m"]
    friction = mu / 2 * (4.4 * 0 + axial * dia + 3.81 * worst["radial"] * dia) * DRIVE["start_factor"]
    lean = st.C["shaft"]["chosen"]["movement"]["lean"] + DRIVE["plumb_tolerance"] + tilt
    gravity = worst["moment"] * lean
    inertia = st.C["index_torque"]
    running = friction + gravity + inertia
    design = DRIVE["service_factor"] * running
    step = math.tau / n
    peak_speed = 2 * step / DRIVE["index_seconds"]                # accelerate for half the turn, brake for half
    power = design * peak_speed / DRIVE["drive_efficiency"]
    gear_r = DRIVE["gear_pitch_diameter_m"] / 2
    tooth = design / gear_r
    lock = DRIVE["lock_factor"] * design
    lock_force = lock / st.ROOT
    lock_pin = math.sqrt(4 * lock_force / (math.pi * .6 * PIN["fy_mpa"] * 1e6))
    # Torsion in the shaft with every level driven at once.
    section = st.C["shaft"]["chosen"]["section"]
    torque = cfg.LEVELS * design
    polar = 2 * section["i"]
    c["drive"] = dict(friction=friction, gravity=gravity, inertia=inertia, running=running, design=design, lean=lean, peak_speed=peak_speed,
                      rpm=peak_speed * 60 / math.tau, power=power, tooth=tooth, pinion=design / DRIVE["pinion_teeth_ratio"], lock=lock, lock_force=lock_force,
                      lock_pin=lock_pin, torque=torque, shear_stress=torque * section["d"] / 2 / polar, hold=DRIVE["service_factor"] * gravity)

    # The limit on the accumulated movement of a pod tip, with allowances for the root connection and the tilt of the hub.
    budget = st.C["budget"]
    need = R["allowance_mm"]["root"] / 1000 + allow
    rows = []
    lightest = st.C["shaft"]["lightest"]
    for w in st.C["shaft"]["walls"]:
        if not w["passes"]: continue
        total = budget["truss"] + w["movement"]["total"] + need
        rows.append(dict(wall=w, shaft=w["movement"]["total"], total=total, ok=total <= st.ACCUMULATED + 1e-12,
                         extra=(w["mass"] - lightest["mass"]) / 1e3))
    c["budget"] = dict(truss=budget["truss"], shaft=budget["shaft"], root=R["allowance_mm"]["root"] / 1000, hub=allow, need=need,
                       now=budget["total"] + need, rows=rows, least=next((r for r in rows if r["ok"]), None),
                       adopted=next(r for r in rows if r["wall"] is st.C["shaft"]["chosen"]))
    c["flexible"] = flexible(c)
    return c


def flexible(c):
    """Movement between a pod tip and its wall sleeve that the flexible section of the wall connection has to take.

    The pod hangs from the shaft and the sleeve is in the inner wall. Some causes lower the tip against
    the sleeve and some raise it, so the two directions are added separately.
    """
    w = cfg.PROJECT["structure"]["wall_connection"]
    slab = foundation.C["chosen"]["settle"]
    move = thermal.C["movement"]
    squeeze = thermal.C["squeeze"][1]["creep"]
    down = [("Structure: truss, shaft, root connection and hub", c["budget"]["adopted"]["total"], "section 12.9, limit " + format(st.ACCUMULATED * 1000, "g") + " mm"),
            ("Inner wall warms and rises before the shaft does", move["wall_pod"], "section 9.13, top level")]
    up = [("Filling the store settles the wall more than the shaft", slab["fill_inner"] - slab["fill_shaft"], "section 11.5"),
          ("Settlement over time", w["settlement_over_time_mm"] / 1000, "allowance until the ground is known")]
    closes = [("Inner wall squeezed by the liquid, with creep", squeeze, "section 9.13, lowest level"), ("Pod lengthens as it warms", move["pod"], "section 9.13")]
    opens = [("Bore widens as the wall warms", move["bore"], "section 9.13")]
    step = w["round_to_mm"] / 1000
    def rate(*groups):
        return math.ceil(w["margin"] * max(sum(v for _, v, _ in g) for g in groups) / step - 1e-9) * step
    across, along = rate(down, up), rate(closes, opens)
    bend = w["hose_bend_radius_mm"] / 1000
    length = math.sqrt(6 * across * bend + across**2)             # live length of a hose for a sideways offset, makers' formula
    return dict(down=down, up=up, closes=closes, opens=opens, across=across, along=along, length=length, gap=st.TIP_R + cfg.POD["tip_clearance_m"] - st.TIP_R,
                pressure=thermal.walls.pressure(st.level_height(1)), temperature=thermal.HOT)


C = compute()


def check():
    c = C
    assert c["tip"]["total"] <= R["allowance_mm"]["root"] / 1000, "the root connection moves the pod tip more than its allowance"
    assert c["tip"]["total"] <= st.LIMIT
    assert c["pin"]["use"] <= 1 and c["arm"]["use"] <= 1
    # The pulls of a full level are in balance round the top ring: eight forces at 45° close.
    n = cfg.BAYS
    assert abs(sum(math.cos(i * math.tau / n) for i in range(n))) < 1e-9
    # The ring force is the pull over twice the sine of half the angle between pods: check by resolving at one pod.
    assert abs(2 * c["hub"]["ring_force"] * math.sin(math.pi / n) - 2 * c["pull"]) < 1e-6
    assert c["budget"]["adopted"]["ok"], "the shaft wall in the design file does not keep the pod tips within the accumulated limit"


def summary():
    c = C
    p = c["budget"]["adopted"]
    return (f"Root: {c['pin']['d']*1000:.0f} mm pin in two {c['pin']['t']*1000:.0f} mm lugs on {c['arm']['name']} arms, tip moves {c['tip']['total']*1000:.2f} mm. "
            f"Drive: {c['drive']['design']/1e3:.0f} kN·m and {c['drive']['power']/1e3:.1f} kW a level. "
            f"With the {st.inches(p['wall']['section']['wall_in'])} in shaft wall the pod tips move {p['total']*1000:.2f} mm of {st.ACCUMULATED*1000:g} mm. "
            f"Flexible section: {c['flexible']['across']*1000:.0f} mm across, {c['flexible']['along']*1000:.0f} mm along.")
