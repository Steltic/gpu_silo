"""Revision J coordination calculations. Lengths in metres, loads in kN unless noted."""
import math
from itertools import combinations

import numpy as np

from . import calcs, connection, crown_detail, design as cfg, foundation, structure, thermal

BASIS = cfg.PROJECT["coordination"]
SITE, D, MECH = (BASIS[k] for k in ("site", "decks", "services"))
G = structure.G
E = structure.E / 1000
FY = structure.FY / 1000
R = D["ring_radius_m"]
START = math.radians(90 + D["access_half_deg"])
END = math.radians(450 - D["access_half_deg"])


def angles(count):
    margin = math.radians(D["end_margin_deg"])
    return np.linspace(START + margin, END - margin, count).tolist()


def rails(level):
    return D["turbine_rail_y_m" if level else "diesel_rail_y_m"]


def box(section):
    b, h, tf, tw = section
    area = b*h - (b-2*tw)*(h-2*tf)
    ix = (b*h**3 - (b-2*tw)*(h-2*tf)**3)/12
    iy = (h*b**3 - (h-2*tf)*(b-2*tw)**3)/12
    return area, ix, iy


def bracket(x, coords):
    i = int(np.searchsorted(coords, x, side="right"))
    if i == 0 or i == len(coords):
        if min(abs(x-coords[0]), abs(x-coords[-1])) > 1e-8:
            raise ValueError(f"Load at {x} outside its supports")
        return [(0 if i == 0 else i-1, 1.)]
    share = (x-coords[i-1])/(coords[i]-coords[i-1])
    return [(i-1, 1-share), (i, share)]


def machines(level):
    """Equipment centres in the local axes of the power floors. All operating masses in tonnes."""
    diesel = cfg.PROJECT["diesel"]
    if level:
        y = (cfg.POWER["aisle_m"] + cfg.POWER["set_width_m"])/2
        return [(0, sign*y, cfg.POWER["set_weight_t"]) for sign in (-1, 1)]
    gens = [(0,-.6), (-5.65,-.4), (0,-4.9), (5.65,-.4)]
    return [(x,y,diesel["set_weight_t"]) for x,y in gens] + [
        (x,3.2,structure.C["rig"]["tank_t"] + .6) for x in (-3.2,3.2)]


def floor(level, equipment=None):
    equipment = machines(level) if equipment is None else equipment
    lines = rails(level)
    half = [math.sqrt(R**2-y**2) for y in lines]
    lengths = [2*v for v in half]
    section = D["turbine_box_m" if level else "diesel_box_m"]
    area, ix, _ = box(section)
    takeoff = (sum(lengths)*area + R*(END-START)*box(D["ring_box_m"])[0]) * structure.RHO/1000
    if not level:
        takeoff += 4*(R-D["connector_radius_m"])*box(D["guide_arm_box_m"])[0]*structure.RHO/1000
    budget = cfg.PROJECT["logistics"]["power_fabrication"]["deck_steel_t"]
    live = math.pi*R**2*D["live_load_kpa"]
    w = (budget*G + live)/sum(lengths)
    supports = angles(cfg.PROJECT["structure"]["turbine_mounts" if level else "top_rig"]["wall_mounts"])
    reactions = np.zeros(len(supports))
    moves, moments, shears, span_ratios, rail_hz = [], [], [], [], []
    ring_moments = np.zeros(len(supports)-1)
    for k, (y,h,L) in enumerate(zip(lines,half,lengths)):
        # Each skid spans its adjacent rails. Putting its rail share at its centre
        # preserves reactions. Placing all those shares at midspan bounds M and delta.
        loads = []
        for x, cy, mass in equipment:
            for rail, f in bracket(cy, lines):
                if rail == k:
                    if abs(x) > h:
                        raise ValueError("Machine reaction lies outside the rail span")
                    loads.append((x, f*mass*G*D["machinery_factor"]))
        P = sum(p for _,p in loads)
        moments.append(1.6*(P*L/4+w*L**2/8))
        moves.append((P*L**3/48 + 5*w*L**4/384)/(E*ix))
        span_ratios.append(L/moves[-1])
        # Simply supported rail, sine trial mode. Use actual skid positions, static
        # equipment mass and the distributed floor/live load. All masses below are kg.
        modal_mass = w*1000/G*L/2 + sum(
            p*1000/(G*D["machinery_factor"])*math.sin(math.pi*(x+h)/L)**2 for x,p in loads)
        rail_hz.append(math.sqrt(structure.E*ix*math.pi**4/(2*L**3*modal_mass))/(2*math.pi))
        for sign in (-1, 1):
            v = w*L/2 + sum(p*(h+sign*x)/L for x,p in loads)
            shears.append(1.6*v)
            angle = math.atan2(y,sign*h)
            if angle < START: angle += 2*math.pi
            pairs = bracket(angle,supports)
            for i,f in pairs: reactions[i] += v*f
            if len(pairs) == 2:
                i, left = pairs[0]
                ring_moments[i] += 1.6*v*R*(supports[i+1]-supports[i])*left*(1-left)
    total = budget*G+live+sum(t*G*D["machinery_factor"] for _,_,t in equipment)
    assert math.isclose(sum(reactions),total,rel_tol=1e-9)
    _, ir, _ = box(D["ring_box_m"])
    return dict(mass=takeoff, budget=budget, load=total, mount=1.6*max(reactions),
                all_mounts=reactions, critical_seats=(np.flatnonzero(np.isclose(reactions,max(reactions)))+1).tolist(),
                rail_hz=min(rail_hz),
                moment=max(moments), strength=.9*FY*ix/(section[1]/2),
                shear=max(shears), shear_strength=.9*.6*FY*2*section[3]*(section[1]-2*section[2]),
                deflection=1000*max(moves), span_ratio=min(span_ratios), ring_m=max(ring_moments),
                ring_strength=.9*FY*ir/(D["ring_box_m"][1]/2))


def stage_envelope(level, loaded):
    """Superpose each equipment placement on the bare floor, including the live allowance."""
    units = machines(level)
    bare = floor(level, [])
    singles = [floor(level,[unit]) for unit in units]
    increments = [s["all_mounts"]-bare["all_mounts"] for s in singles]
    for count in range(len(units)+1):
        for subset in combinations(range(len(units)), count):
            reactions = bare["all_mounts"].copy()
            for i in subset:
                reactions += increments[i]
            total = bare["load"] + sum(units[i][2]*G*D["machinery_factor"] for i in subset)
            assert math.isclose(sum(reactions), total, rel_tol=1e-9)
            assert min(reactions) >= -1e-7 and np.all(reactions <= loaded["all_mounts"]+1e-7)
    assert np.allclose(bare["all_mounts"]+np.sum(increments,axis=0),loaded["all_mounts"])
    return dict(cases=2**len(units), bare=bare["mount"], one=max(s["mount"] for s in singles))


def radial_supports(count):
    a = angles(count)
    normals = np.array([(math.cos(v),math.sin(v)) for v in a])
    k = normals.T @ normals
    influence = normals @ np.linalg.inv(k)
    assert np.allclose(normals.T @ influence, np.eye(2))
    return a, k, max(np.linalg.norm(influence,axis=1))


def lateral():
    # The norm of each reaction row bounds all horizontal load directions.
    a,k,fraction = radial_supports(cfg.PROJECT["structure"]["top_rig"]["wall_mounts"])
    shaft_weight = max(v["axial"] for v in structure.C["shaft"]["chosen"]["cases"])/1000
    shaft = structure.C["rig"]["cases"][-1]["factored"]/1000 + 1.4*SITE["horizontal_coefficient"]*shaft_weight
    arm_length = R-D["connector_radius_m"]
    arm_area, ax, ay = box(D["guide_arm_box_m"])
    arm_k = E*arm_area/arm_length/1000  # credit one arm on each engaged pad axis
    pad = D["guide_pad_m"]
    pad_k = D["pad_modulus_mpa"]*pad[0]*pad[1]/pad[2]  # MPa*m = kN/mm
    bay = R*(a[1]-a[0])
    ring_k = 48*E*box(D["ring_box_m"])[2]/bay**3/1000
    seat_k = D["wall_seat_stiffness_kn_mm"]*min(np.linalg.eigvalsh(k))
    series = 1/sum(1/v for v in (arm_k,pad_k,ring_k,seat_k))
    if cfg.PROJECT["structure"]["top_rig"]["arms"] != 4:
        raise ValueError("Directional guide bound requires two orthogonal pairs of pads")
    # Orthogonal clearance components can both reach the per-pad play under a diagonal force.
    free_motion = math.sqrt(2)*D["guide_play_mm"]
    service = [s["reaction"]/1000 for s in structure.C["rig"]["cases"] if s["reaction"]>1.]
    stiffness = [f/(f/series+free_motion) for f in service]
    slender = arm_length/math.sqrt(min(ax,ay)/arm_area)
    comp = .9*structure.compression_stress(slender)*arm_area/1000
    return dict(fraction=fraction, shaft=shaft, arm_force=shaft, arm_strength=comp,
                k=min(stiffness), uncontrolled_k=stiffness[-1], deadband=free_motion,
                components=(pad_k,arm_k,ring_k,seat_k), bay=bay,
                pad_pressure=shaft/1000/(pad[0]*pad[1]))


def seat(level, deck, lat):
    count = cfg.PROJECT["structure"]["turbine_mounts" if level else "top_rig"]["wall_mounts"]
    fraction = radial_supports(count)[2]
    horiz = fraction*((lat["shaft"] if not level else 0) +
                             1.4*SITE["horizontal_coefficient"]*deck["load"])
    v = deck["mount"]
    # Bearing and a positive steel shear key carry gravity. Four two-legged,
    # developed hairpins behind each plate transfer tension/shear to both wall mats.
    rows = sorted(D["stud_rows_m"])
    lever = rows[-1]-rows[0]
    bar = math.pi*(D["anchor_rebar_mm"]/1000)**2/4
    stud_area = math.pi*(D["stud_diameter_mm"]/1000)**2/4
    n = D["seat_studs"]
    bar_fy = cfg.PROJECT["structure"]["walls"]["fy_mpa"]*1000
    tension_cap = min(.75*n/2*stud_area*D["stud_fu_mpa"]*1000, .75*4*bar*bar_fy)
    width,key_projection,thickness = D["key_width_projection_thickness_m"]
    key_cap = .65*.85*cfg.PROJECT["structure"]["walls"]["concrete_fc_mpa"]*1000*width*key_projection
    key_moment = v*key_projection/2  # uniform bearing under the key
    key_strength = .9*FY*width*thickness**2/6  # elastic steel resistance at the plate
    # Four upper studs resist outward force. Prising moment acts about the lowest row.
    # Distribute moment tension in proportion to row distance using a rigid embedded plate.
    columns = len(D["stud_columns_m"])
    distances = [z-rows[0] for z in rows if z>0]
    assert n==len(rows)*columns and len(distances)*columns==4
    stud_forces = [horiz/(columns*len(distances)) + v*D["shoe_eccentricity_m"]*d/(columns*sum(e*e for e in distances))
                   for d in distances]
    max_stud = max(stud_forces)
    group_tension = columns*sum(stud_forces)
    ecc = abs(sum(d*p for d,p in zip(distances,stud_forces))/sum(stud_forces)-np.mean(distances))
    fc = cfg.PROJECT["structure"]["walls"]["concrete_fc_mpa"]
    hef = D["stud_embed_m"]-D["plate_thickness_m"]-D["stud_head_thickness_mm"]/1000
    projection = 3*hef
    area_ratio = (projection+max(D["stud_columns_m"])-min(D["stud_columns_m"]))*(projection+max(distances)-min(distances))/projection**2
    # Cracked normal-weight concrete, cast-in stud group, no supplementary steel credit.
    # Use the basic SI 10*sqrt(fc)*hef^1.5 expression with hef in mm. ACI 318M-19 §17.6.
    breakout = .70*10*math.sqrt(fc)*(1000*hef)**1.5/1000*area_ratio/(1+2*ecc/projection)
    head_area = math.pi/4*(D["stud_head_diameter_mm"]**2-D["stud_diameter_mm"]**2)
    pullout = .70*8*head_area*fc/1000
    shear_cap = .75*8*bar*bar_fy
    weld_width,weld_height,leg = D["closure_weld_width_height_leg_m"]
    length = 2*(weld_width+weld_height)
    weld_ix = 2*weld_width*(weld_height/2)**2 + weld_height**3/6
    line_tension = horiz/length + v*D["shoe_eccentricity_m"]*(weld_height/2)/weld_ix
    weld_cap = .75*.6*490000*.707*leg  # kN/m along the weld line
    return dict(v=v, h=horiz, t=group_tension, tension_cap=tension_cap, key_cap=key_cap, shear_cap=shear_cap,
                weld_cap=weld_cap, weld_demand=math.hypot(line_tension,v/length),
                interaction=group_tension/tension_cap+v/shear_cap, fraction=fraction,
                stud=max_stud, stud_strength=.75*stud_area*D["stud_fu_mpa"]*1000,
                group_tension=group_tension, breakout=breakout, pullout=pullout, hef=hef,
                key_moment=key_moment, key_strength=key_strength,
                leg_interaction=max_stud/(.75*bar*bar_fy)+v/shear_cap)


def utilities():
    m = MECH
    heat = calcs.C["heat_mw"]
    amps = lambda mw: mw*1000/(math.sqrt(3)*m["bus_kv"]*m["power_factor"])
    # Coolers see outdoor air plus a commissioning limit on fan recirculation.
    inlet = cfg.PROJECT["thermal"]["ambient"]["summer_design_c"]+SITE["weather_recirculation_k"]
    rejection = thermal.stratified_capacity(inlet)/1e6
    extreme = cfg.PROJECT["thermal"]["ambient"]["extreme_hot_c"]+SITE["weather_recirculation_k"]
    hot = thermal.stratified_capacity(extreme)/1e6
    flows = (thermal.C["flow"]/cfg.TOTAL/thermal.C["swell"]["density"],
             calcs.C["flow_cooler"][0]/cfg.FLUID["density_kg_m3"])
    speeds = [4*q/(math.pi*d*d) for q,d in zip(flows,(m["pod_branch_id_m"],m["cooler_branch_id_m"]))]
    pumps = [cfg.FLUID["density_kg_m3"]*G*q*h/m["pump_efficiency"]/1000 for q,h in zip(flows,m["pump_head_m"])]
    pump_mw=(pumps[0]*cfg.TOTAL+pumps[1]*cfg.COOLERS)/1000
    aux_mw=pump_mw+cfg.COOLERS*m["fan_kw_per_cooler"]/1000+m["other_services_mw"]+heat*m["conversion_loss_fraction"]
    return dict(pump_mw=pump_mw,aux_mw=aux_mw,amps=amps(heat)/2, level_amps=amps(heat/cfg.LEVELS), total=heat+m["facility_aux_mw"],
                island=calcs.C["gen_mw"]-m["facility_aux_mw"], emergency=calcs.C["diesel_mw"]-m["essential_aux_mw"],
                summer=rejection/(1+cfg.PROJECT["thermal"]["pump_heat_fraction"]), extreme=hot/(1+cfg.PROJECT["thermal"]["pump_heat_fraction"]),
                speeds=speeds, pumps=pumps, bore=thermal.C["inner"]["heat"]/1000+m["bore_other_kw"],
                ride=thermal.C["rides"]["adopted"]["layered"]/60,
                catch=m["catch_inflow_m3h"]*m["fill_trip_minutes"]/60)


def ground():
    f = foundation.C["as_drawn"][foundation.F["design_ground"]]
    extra = math.pi*SITE["slab_boss_radius_m"]**2*SITE["slab_boss_extra_m"]*foundation.GAMMA_C/1000
    weight = foundation.C["total"]/1000+extra
    # All operating mass participates at a conservative common inertia height.
    h = cfg.SILO["height_m"]
    shear = SITE["horizontal_coefficient"]*weight
    wind = SITE["wind_pressure_kpa"]*cfg.SILO["outside_diameter_m"]*h
    moment = (shear+wind)*h/2
    q = 4*moment/(math.pi*foundation.RADIUS**3)
    return dict(qmax=f["pressure"]["most"]/1000+extra/foundation.C["area"]+q,
                qmin=f["pressure"]["least"]/1000-q, shear=shear, wind=wind,
                sliding=.35*weight/(shear+wind), crest=2*SITE["long_period_spectral_g"]*calcs.C["tank_r_out"],
                air=cfg.FLUID["freeboard_m"]-sum(cfg.PROJECT["thermal"]["cover"].values()),
                slab_shear=f["vu"]/1000,
                ties=f["plain"]/1000+.75*(2*math.pi*.016**2/4)/(.4*.4)*420000*f["d"],
                hairpins=24*math.pi*.032**2/4, shaft_req=foundation.C["base"]["hairpins"])


def compute():
    decks = [floor(i) for i in range(2)]
    lat = lateral()
    return decks,lat,[seat(i,deck,lat) for i,deck in enumerate(decks)],utilities(),ground()


def ancillary():
    """Secondary load paths and procurement envelopes carried into the coordination register."""
    shaft=structure.C["shaft"]["chosen"]
    sec=shaft["section"]
    full=max(c["axial"] for c in shaft["cases"])
    # Conservatively concentrate horizontal inertia at mid-height of a simply
    # supported shaft and add the maximum existing moment and axial stress.
    bending=max(c["mu"] for c in shaft["cases"])+1.4*SITE["horizontal_coefficient"]*full*structure.SHAFT_TOP/4
    stress=(1.4*full/sec["area"]+bending/sec["s"])/1e6
    chord=structure.C["design"]["chord"]
    pod=structure.C["weight"]/1000
    lateral_chord=1.4*SITE["horizontal_coefficient"]*pod*structure.SPAN/(4*structure.TRUSS_SPACING)
    limits=structure.C["design"]["groups"]
    chord_ratio=max(g["ratio"] for k,g in limits.items() if "chord" in k.lower())+lateral_chord/(.9*FY*chord["area"])
    frame_t=cfg.PROJECT["logistics"]["coolers"]["frame_steel_t"]+3*(cfg.PROJECT["logistics"]["coolers"]["cooler_mass_t"]+cfg.PROJECT["logistics"]["coolers"]["pump_unit_mass_t"])
    # Four gravity seats. Wind is reversible, with the eccentric vertical load resisted as a couple.
    frame_v=1.6*frame_t*G/4
    frame_h=(1.6*SITE["wind_pressure_kpa"]*cfg.COOL["frame_width_m"]*cfg.COOL["frame_height_m"]/4+
             1.6*frame_t*G*2.2/(cfg.COOL["frame_height_m"]-.6)/4)
    frame_cap=.75*4*math.pi*.025**2/4*420000
    portal=calcs.C["head_kpa"]*(cfg.OUTSIDE_R-cfg.SILO["outer_wall_m"])*cfg.DOOR_HEIGHT/2
    return dict(shaft_stress=stress,shaft_limit=.9*structure.FY_SHAFT/1e6,chord_ratio=chord_ratio,
                frame_v=frame_v,frame_h=frame_h,frame_cap=frame_cap,frame_ratio=(frame_h+frame_v)/frame_cap,
                portal=portal,portal_cap=24*.001006*248000,
                feeder_a=calcs.C["pod_kw"]/(math.sqrt(3)*MECH["power_factor"]),
                bus_drop_pct=100*math.sqrt(3)*.12*.060/2*calcs.C["pod_kw"]/(math.sqrt(3)*MECH["power_factor"])/1000)


def check():
    decks,lat,seats,u,g = compute()
    for level,(deck,seat_result) in enumerate(zip(decks,seats)):
        stage_envelope(level,deck)
        assert deck["mass"] < deck["budget"] and deck["moment"] < deck["strength"]
        assert deck["shear"] < deck["shear_strength"] and deck["ring_m"] < deck["ring_strength"]
        assert deck["span_ratio"] >= 300
        assert seat_result["interaction"] <= 1 and seat_result["v"] < seat_result["key_cap"]
        assert seat_result["weld_demand"] < seat_result["weld_cap"]
        assert seat_result["stud"] < seat_result["stud_strength"] and seat_result["leg_interaction"] <= 1
        assert seat_result["group_tension"] < seat_result["breakout"] and seat_result["stud"] < seat_result["pullout"]
        assert seat_result["key_moment"] < seat_result["key_strength"]
    assert lat["k"] >= 16 and D["collar_travel_mm"] >= 2 and lat["arm_force"] < lat["arm_strength"]
    assert lat["pad_pressure"] <= D["pad_pressure_limit_mpa"]
    crown_detail.check()
    assert 0 < g["qmin"] < g["qmax"] <= SITE["allowable_bearing_kpa"] and g["sliding"] >= 1.5
    assert g["crest"] < g["air"] and g["slab_shear"] < g["ties"] and g["shaft_req"] < g["hairpins"]
    assert u["pump_mw"] <= calcs.C["heat_mw"]*cfg.PROJECT["thermal"]["pump_heat_fraction"]
    assert u["aux_mw"] <= MECH["facility_aux_mw"]
    assert u["total"] <= calcs.C["gen_mw"]+MECH["grid_import_mw"]
    assert calcs.C["reference_it_mw"] <= cfg.CLUSTER["normal_it_limit_mw"] <= u["island"]
    assert u["amps"] <= MECH["bus_amps"] and u["level_amps"] <= MECH["level_amps"]
    assert u["ride"] >= MECH["ride_target_min"] and u["catch"] < cfg.PROJECT["thermal"]["overflow"]["catch_tank_m3"]
    assert u["bore"] < MECH["ahu_kw"] and max(u["speeds"]) < 2.5
    assert MECH["ups_mwh"]*.8 >= MECH["ups_mw"]*MECH["ups_minutes"]/60
    a=ancillary()
    assert a["shaft_stress"] < a["shaft_limit"] and a["chord_ratio"] < 1
    assert a["frame_ratio"] < 1 and a["portal"] < a["portal_cap"]
    assert a["feeder_a"] < 630 and a["bus_drop_pct"] < 2


def summary():
    return "Checks 7–10, power and cooling limits, settlement and lateral screening verified on the revision J assumptions."
