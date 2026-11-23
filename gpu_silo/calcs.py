"""Design calculations derived from design/project.json.

Run ``python -m gpu_silo calcs`` to rewrite design/calcs.md. The same numbers
feed the design panels in the animation, so the film, the model and the written
calculations cannot drift apart.
"""
import math
from pathlib import Path

from . import connection as cn
from . import design as cfg
from . import foundation as fd
from . import logistics
from . import reinforcement as rf
from . import structure as st
from . import thermal as th
from . import walls

US_GAL = 0.003785411784  # m3
G = 9.80665
FILE = Path(__file__).resolve().parents[1] / "design" / "calcs.md"


def compute():
    c = {}
    cl, fl, co, silo = cfg.CLUSTER, cfg.FLUID, cfg.COOL, cfg.SILO
    # Cluster
    c["pods"] = cfg.TOTAL
    c["racks"] = cfg.RACKS
    c["cdus"] = cfg.TOTAL * cl["cdus_per_pod"]
    c["cdu_pumps"] = c["cdus"] * cl["pumps_per_cdu"]
    c["rack_kw"] = cl["liquid_heat_per_rack_kw"]
    c["pod_kw"] = c["rack_kw"] * cl["racks_per_pod"]
    c["heat_mw"] = c["racks"] * c["rack_kw"] / 1000
    spare_kw = cl["reference_spare_kw"]
    cap_kw = 1000*cl["normal_it_limit_mw"]
    if not 0 <= spare_kw < c["rack_kw"] or cap_kw < c["racks"]*spare_kw:
        raise ValueError("The reference rack assignment needs a valid active and standby power budget")
    c["reference_active"] = min(c["racks"],math.floor((cap_kw-c["racks"]*spare_kw)/(c["rack_kw"]-spare_kw)))
    c["reference_spare"] = c["racks"]-c["reference_active"]
    c["reference_it_mw"] = (c["reference_active"]*c["rack_kw"]+c["reference_spare"]*spare_kw)/1000
    # Silo and thermal store
    ro, ri = cfg.OUTSIDE_R, cfg.BORE_R
    c["tank_r_out"] = ro - silo["outer_wall_m"]
    c["tank_r_in"] = ri + silo["inner_wall_m"]
    c["wall_gap"] = cfg.WALL_GAP
    c["tank_area"] = math.pi * (c["tank_r_out"]**2 - c["tank_r_in"]**2)
    c["liquid_top"] = cfg.LIQUID_TOP
    c["tank_m3"] = c["tank_area"] * c["liquid_top"]
    c["tank_gal"] = c["tank_m3"] / US_GAL
    c["target_gal"] = fl["target_volume_us_gal"]
    c["target_m3"] = c["target_gal"] * US_GAL
    c["tank_of_target"] = c["tank_m3"] / c["target_m3"]
    c["gross_m3"] = math.pi * (ro**2 - ri**2) * silo["height_m"]
    c["gross_gal"] = c["gross_m3"] / US_GAL
    # Ways to reach the target while keeping the other inputs
    c["need_height"] = c["target_m3"] / c["tank_area"] + fl["freeboard_m"]
    c["need_od"] = 2 * (math.sqrt(c["target_m3"] / (math.pi * c["liquid_top"]) + c["tank_r_in"]**2) + silo["outer_wall_m"])
    inner = c["tank_r_out"]**2 - c["target_m3"] / (math.pi * c["liquid_top"])
    c["need_id"] = 2 * (math.sqrt(inner) - silo["inner_wall_m"]) if inner > 0 else float("nan")
    rho, cp = fl["density_kg_m3"], fl["specific_heat_kj_kgk"]
    c["rho"], c["cp"] = rho, cp
    c["tank_t"] = c["tank_m3"] * rho / 1000
    c["store_mj_k"] = c["tank_m3"] * rho * cp / 1000
    c["store_mwh_k"] = c["store_mj_k"] / 3600
    c["min_per_k"] = c["store_mj_k"] / c["heat_mw"] / 60
    c["swing"] = fl["usable_temperature_swing_k"]
    c["ride_min"] = c["min_per_k"] * c["swing"]
    c["ride_mwh"] = c["store_mwh_k"] * c["swing"]
    c["head_kpa"] = rho * G * c["liquid_top"] / 1000
    c["outer_hoop_kn_m"] = c["head_kpa"] * c["tank_r_out"]
    c["outer_hoop_mpa"] = c["outer_hoop_kn_m"] / silo["outer_wall_m"] / 1000
    c["inner_hoop_kn_m"] = c["head_kpa"] * c["tank_r_in"]
    c["inner_hoop_mpa"] = c["inner_hoop_kn_m"] / silo["inner_wall_m"] / 1000
    # Flows
    dt = fl["loop_delta_t_k"]
    c["dt"] = dt
    def flow(kw):
        kg_s = kw / (cp * dt)
        m3_s = kg_s / rho
        return kg_s, m3_s * 60000, m3_s / US_GAL * 60
    c["flow_total"] = flow(c["heat_mw"] * 1000)
    c["flow_pod"] = flow(c["pod_kw"])
    c["flow_cooler"] = flow(co["cooler_capacity_mw"] * 1000)
    c["turnover_min"] = c["tank_m3"] / (c["flow_total"][1] / 1000)
    # Dry coolers
    c["frames"] = cfg.FRAMES
    c["coolers"] = cfg.COOLERS
    c["cooler_pumps"] = c["coolers"] * co["pumps_per_cooler"]
    c["reject_mw"] = c["coolers"] * co["cooler_capacity_mw"]
    c["margin"] = c["reject_mw"] / c["heat_mw"] - 1
    c["duty_coolers"] = math.ceil(th.LOAD / 1e6 / co["cooler_capacity_mw"] - 1e-9)
    c["standby_coolers"] = c["coolers"] - c["duty_coolers"]
    # Air side of one cooler and pipe bores for 2 m/s
    air_rho, air_cp = 1.2, 1.006
    c["cooler_air_m3s"] = co["cooler_capacity_mw"] * 1000 / (air_rho * air_cp * co["air_rise_k"])
    c["cooler_face_m2"] = co["cooler_length_m"] * co["cooler_section_m"]
    c["cooler_face_ms"] = c["cooler_air_m3s"] / c["cooler_face_m2"]
    c["cooler_fans"] = max(1, round(co["cooler_length_m"] / 2.25))
    def bore(lpm, speed=2.0):
        return math.sqrt(4 * lpm / 60000 / (math.pi * speed)) * 1000
    c["cooler_bore_mm"] = bore(c["flow_cooler"][1])
    c["pod_bore_mm"] = bore(c["flow_pod"][1])
    # The store against the load, through the three versions of the design
    def store(od, bore, height, mw):
        volume = math.pi * ((od / 2 - silo["outer_wall_m"])**2 - (bore / 2 + silo["inner_wall_m"])**2) * (height - fl["freeboard_m"])
        return volume, volume * rho * cp / 1000 / mw / 60 * c["swing"]
    c["store_cases"] = [(od, bore, height, mw, *store(od, bore, height, mw)) for od, bore, height, mw in
                        ((20.0, 13.0, 30.0, 32.0), (22.0, 13.0, 30.0, 50.0),
                         (silo["outside_diameter_m"], silo["inside_diameter_m"], silo["height_m"], c["heat_mw"]))]
    same_bore = store(silo["outside_diameter_m"], 13.0, silo["height_m"], c["heat_mw"])[0]
    c["bore_cost_m3"] = same_bore - c["tank_m3"]
    c["one_out_mw"] = c["reject_mw"] - co["cooler_capacity_mw"]
    deficit = c["heat_mw"] - c["one_out_mw"]
    c["one_out_h_per_k"] = c["store_mj_k"] / deficit / 3600 if deficit > 0 else float("inf")
    c["frame_out_mw"] = c["reject_mw"] - co["coolers_per_frame"] * co["cooler_capacity_mw"]
    deficit = c["heat_mw"] - c["frame_out_mw"]
    c["frame_out_min_per_k"] = c["store_mj_k"] / deficit / 60 if deficit > 0 else float("inf")
    back = ro + co["wall_standoff_m"]
    c["frame_back_r"] = back
    c["frame_subtends_deg"] = math.degrees(2 * math.asin(co["frame_width_m"] / 2 / back))
    c["frames_per_tier"] = cfg.FRAMES // len(co["tier_base_m"])
    c["frame_run_m"] = cfg.FRAMES * co["frame_width_m"]
    c["circumference_m"] = 2 * math.pi * ro
    c["end_gap_m"] = back - math.sqrt(ro**2 - (co["frame_width_m"] / 2)**2)
    c["row_height"] = co["frame_height_m"] / co["coolers_per_frame"]
    c["anchors_per_frame"] = len(co["anchor_columns_m"]) * (co["coolers_per_frame"] + 1)
    c["anchors"] = c["anchors_per_frame"] * cfg.FRAMES
    c["conduits_per_frame"] = co["conduits_per_cooler"] * co["coolers_per_frame"]
    c["frame_conduits"] = c["conduits_per_frame"] * cfg.FRAMES
    # Fuel storage
    fu=cfg.PROJECT["fuel"];radius=fu["tank_diameter_m"]/2
    c["tank_each_m3"]=math.pi*radius**2*(fu["tank_length_m"]-2*radius)+4/3*math.pi*radius**3
    c["fuel_m3"]=c["tank_each_m3"]*fu["tanks"]*fu["fill_fraction"]
    c["fuel_gal"]=c["fuel_m3"]/US_GAL
    c["fuel_mwh_th"]=c["fuel_m3"]*1000*fu["energy_mj_per_litre"]/3600
    c["fuel_mwh_e"]=c["fuel_mwh_th"]*fu["generation_efficiency"]
    # Power: two in-line turbine sets on one level
    pw=cfg.POWER
    c["gen_mw"]=pw["modules"]*pw["module_output_mw"]
    c["gen_margin"]=c["gen_mw"]/c["heat_mw"]-1
    c["set_diagonal"]=math.hypot(pw["set_length_m"],pw["set_width_m"])
    c["pair_corner_r"]=math.hypot(pw["set_length_m"]/2,pw["aisle_m"]/2+pw["set_width_m"])
    c["pair_clear"]=cfg.BORE_R-c["pair_corner_r"]
    c["turbine_air_m3s"]=pw["inlet_air_kg_s"]/air_rho
    c["exhaust_rho"]=353/(pw["exhaust_temperature_c"]+273.15)
    c["exhaust_m3s"]=pw["exhaust_flow_kg_s"]/c["exhaust_rho"]
    c["stack_area"]=math.pi*(pw["exhaust_stack_diameter_m"]/2)**2
    c["stack_ms"]=c["exhaust_m3s"]/c["stack_area"]
    c["filter_face_need"]=c["turbine_air_m3s"]/pw["inlet_filter_velocity_m_s"]
    hl,hw,hh=pw["inlet_house_m"]
    c["filter_face_have"]=2*hl*hh
    c["filter_ms"]=c["turbine_air_m3s"]/c["filter_face_have"]
    c["turbine_heat_mw"]=pw["module_output_mw"]/fu["generation_efficiency"]-pw["module_output_mw"]
    c["fuel_hours"]=c["fuel_mwh_e"]/c["gen_mw"]
    # Height above the pods
    di=cfg.PROJECT["diesel"]
    c["levels_need"]=di["set_height_m"]+pw["set_height_m"]+2*pw["floor_structure_m"]
    c["levels_have"]=silo["height_m"]+cfg.PROJECT["coordination"]["decks"]["roof_curb_m"]-cfg.CROWN
    # Propane line: both turbines at full load
    c["fuel_mw_th"]=c["gen_mw"]/fu["generation_efficiency"]
    c["propane_kg_s"]=c["fuel_mw_th"]/fu["lhv_mj_per_kg"]
    c["propane_l_s"]=c["propane_kg_s"]/fu["liquid_density_kg_m3"]*1000
    c["line_area"]=math.pi*(fu["line_diameter_m"]/2)**2
    c["line_liquid_ms"]=c["propane_l_s"]/1000/c["line_area"]
    c["line_liquid_need_mm"]=math.sqrt(4*c["propane_l_s"]/1000/(math.pi*fu["liquid_velocity_m_s"]))*1000
    # Vapour at tank pressure and at turbine supply pressure, as an ideal gas with a compressibility of 0.8
    def vapour(bar,temp_c,z=.8):
        return bar*1e5*.0441/(z*8.314*(temp_c+273.15))
    c["vapour_cases"]=[]
    for label,bar,temp in (("Vapour at tank pressure",9.5,25.),(f"Vapour at turbine pressure",pw["fuel_supply_pressure_bar"],90.)):
        rho_v=vapour(bar,temp);flow=c["propane_kg_s"]/rho_v
        c["vapour_cases"].append((label,bar,temp,rho_v,flow,flow/c["line_area"],math.sqrt(4*flow/(math.pi*fu["vapour_velocity_m_s"]))*1000))
    c["vaporise_mw"]=c["propane_kg_s"]*.43
    # Backup diesel
    c["diesel_mw"]=di["sets"]*di["set_output_mw"]
    c["diesel_share"]=c["diesel_mw"]/c["heat_mw"]
    c["diesel_m3_h"]=di["sets"]*di["fuel_l_per_h_per_set"]/1000
    c["day_tank_m3"]=math.pi*(di["day_tank_diameter_m"]/2)**2*di["day_tank_length_m"]
    c["day_m3"]=di["day_tanks"]*c["day_tank_m3"]
    c["day_hours"]=c["day_m3"]/c["diesel_m3_h"]
    c["bulk_m3"]=math.pi*(di["bulk_tank_diameter_m"]/2)**2*di["bulk_tank_length_m"]*di["bulk_fill_fraction"]
    c["bulk_hours"]=c["bulk_m3"]/c["diesel_m3_h"]
    c["diesel_line_ms"]=c["diesel_m3_h"]/3600/(math.pi*(di["line_diameter_m"]/2)**2)
    c["diesel_room_kw"]=di["sets"]*di["heat_to_room_kw_per_set"]
    c["diesel_room_m3s"]=c["diesel_room_kw"]/(air_rho*air_cp*di["room_air_rise_k"])
    vl,vw,vh=di["room_vent_m"]
    c["room_vent_area"]=vl*vw
    c["room_vent_ms"]=c["diesel_room_m3s"]/c["room_vent_area"]
    c["diesel_stack_ms"]=di["exhaust_m3_s_per_set"]/(math.pi*(di["exhaust_stack_diameter_m"]/2)**2)
    c["top_weight_t"]=pw["modules"]*pw["set_weight_t"]+di["sets"]*di["set_weight_t"]
    c["fuel_burn_m3_h"]=c["fuel_m3"]/c["fuel_hours"]
    # Pod fit
    longest = cfg.BODY_LENGTH + max([cfg.SECTION, *cfg.SECTIONS.values()])
    c["pod_length"] = cfg.BODY_LENGTH + cfg.SECTION
    c["pod_tip_r"] = cfg.STORE["root_radius_m"] + longest
    c["pod_corner_r"] = math.hypot(c["pod_tip_r"], cfg.FRAME_WIDTH / 2)
    c["pod_clearance"] = ri - c["pod_corner_r"]
    c["store_height"] = cfg.LEVELS * cfg.STORE["pitch_m"]
    # Clearances at the root of the pods, where they come closest to each other.
    root, half = cfg.STORE["root_radius_m"], cfg.FRAME_WIDTH / 2
    packed = math.radians(cfg.STORE["packed_pitch_degrees"])
    lane = (2 * math.pi - (cfg.BAYS - 1) * packed) / 2
    c["root_gap_packed"] = 2 * (root * math.sin(packed / 2) - half * math.cos(packed / 2))
    c["root_gap_lane"] = root * math.sin(lane) - half * math.cos(lane) - half
    c["root_gap_stored"] = 2 * (root * math.sin(math.pi / cfg.BAYS) - half * math.cos(math.pi / cfg.BAYS))
    c["access_for_100"] = max((.05 + half * math.cos(packed / 2)) / math.sin(packed / 2),
                              (.10 + half * (1 + math.cos(lane))) / math.sin(lane)) - cfg.STORE["shaft_radius_m"]
    return c


C = compute()


def n(value, digits=0):
    return f"{value:,.{digits}f}"


def strip():
    """Five figures kept on screen for the whole film."""
    return [(n(C["racks"]), f"{cfg.CLUSTER['rack_model'].split()[-1]} racks"),
            (n(C["pods"]), f"{cfg.NAME} pods"),
            (n(cfg.CLUSTER["normal_it_limit_mw"]) + " MW", "normal IT limit"),
            (f"{C['coolers']} × {cfg.COOL['cooler_capacity_mw']:g} MW", "dry coolers"),
            (n(C["tank_gal"] / 1e6, 2) + " M gal", "water-glycol")]


def summary():
    """Rows of the closing design-basis panel."""
    s, co = cfg.SILO, cfg.COOL
    return [
        ("CLUSTER", ""),
        ("GPU racks", f"{C['racks']} × {cfg.CLUSTER['rack_model'].split()[-1]}"),
        (f"{cfg.NAME} pods", f"{C['pods']}"),
        ("Per level", f"{cfg.BAYS} on {cfg.LEVELS} levels"),
        ("Pod length", f"{C['pod_length']:.2f} m"),
        ("CDUs and pumps", f"{C['cdus']} + {C['cdu_pumps']}"),
        ("Normal IT limit", f"{cfg.CLUSTER['normal_it_limit_mw']:g} MW"),
        ("SILO", ""),
        ("Outside / inside", f"{s['outside_diameter_m']:g} / {s['inside_diameter_m']:g} m"),
        ("Height", f"{s['height_m']:g} m"),
        ("Liquid gap", f"{C['wall_gap']:.2f} m"),
        ("THERMAL STORE", ""),
        ("Water-glycol", f"{n(C['tank_m3'])} m³"),
        ("", f"{C['tank_gal']/1e6:.2f} M US gal"),
        ("Loop flow", f"{n(C['flow_total'][1]/1000,1)} m³/min"),
        ("Ride-through", f"{th.C['rides']['adopted']['layered']/60:.0f} min"),
        ("HEAT REJECTION", ""),
        ("Dry coolers", f"{C['coolers']} × {co['cooler_capacity_mw']:g} MW"),
        ("Steel frames", f"{C['frames']}"),
        ("Frame size", f"{co['frame_width_m']:g} × {co['frame_height_m']:g} m"),
        ("Cooler pumps", f"{C['cooler_pumps']}"),
        ("Capacity / duty", f"{C['reject_mw']:.0f} / {th.LOAD/1e6:.2f} MW"),
    ]


def panel():
    """Short label and value pairs used by the scene panels."""
    return {
        "store": [("Liquid gap", f"{C['wall_gap']:.2f} m"), ("Fill level", f"{C['liquid_top']:.2f} m"),
                  ("Volume", f"{n(C['tank_m3'])} m³"), ("", f"{C['tank_gal']/1e6:.2f} M US gal"),
                  ("Target", f"{C['target_gal']/1e6:.2f} M US gal"),
                  ("Ride-through", f"{th.C['rides']['adopted']['layered']/60:.0f} min")],
        "fuel": [("Tanks", f"{cfg.PROJECT['fuel']['tanks']} × {cfg.PROJECT['fuel']['tank_length_m']:g} m"),
                 ("Stored propane", f"{n(C['fuel_m3'])} m³"),
                 (f"Run time at {C['heat_mw']:.0f} MW", f"{C['fuel_hours']:.0f} h"),
                 ("Propane line", f"{cfg.PROJECT['fuel']['line_diameter_m']*1000:.0f} mm"),
                 ("Bulk diesel", f"{C['bulk_m3']:.0f} m³"),
                 (f"Backup at {C['diesel_mw']:.0f} MW", f"{C['bulk_hours']:.0f} h")],
        "plan": [("Liquid heat", f"{C['heat_mw']:.0f} MW"), ("Loop flow", f"{n(C['flow_total'][1]/1000,1)} m³/min"),
                 ("Rise across the pods", f"{C['dt']:g} K"), ("Store", f"{n(C['tank_m3'])} m³"),
                 ("Store turnover", f"{C['turnover_min']:.0f} min")],
        "turbine": [("Output", f"{cfg.POWER['module_output_mw']:g} MW"), ("Type", "Aeroderivative"),
                    ("Class", "GE LM2500"), ("Air", f"{cfg.POWER['inlet_air_kg_s']:.0f} kg/s"),
                    ("Exhaust", f"{cfg.POWER['exhaust_temperature_c']:.0f} °C")],
        "backup": [("Diesel sets", f"{cfg.PROJECT['diesel']['sets']} × {cfg.PROJECT['diesel']['set_output_mw']:g} MW"),
                   ("Backup", f"{C['diesel_mw']:.0f} MW"), ("Day tanks", f"{C['day_hours']:.1f} h"), ("Bulk diesel", f"{C['bulk_hours']:.0f} h")],
        "section": [("Power modules", f"{cfg.POWER['modules']} × {cfg.POWER['module_output_mw']:g} MW"), ("Facility / IT", f"{C['heat_mw']+cfg.PROJECT['coordination']['services']['facility_aux_mw']:.0f} / {C['heat_mw']:.0f} MW"),
                    (f"{cfg.NAME} pods on the shaft", f"{C['pods']}"), ("Dry coolers", f"{C['coolers']} × {cfg.COOL['cooler_capacity_mw']:g} MW"),
                    ("Propane stored", f"{n(C['fuel_m3'])} m³"), ("Run time", f"{C['fuel_hours']:.0f} h")],
        "crew": [(name, str(count)) for name, count in cfg.PROJECT["jumpform"]["crew"]]
                + [("Concrete a lift", f"{logistics.C['lift_m3']:.0f} m³"), ("Mixers a lift", f"{logistics.C['lift_trucks']}"),
                   ("Pour", f"{logistics.C['lift_pour_h']:.1f} h")],
        "dock": [("Pod weight", f"{logistics.C['pod_t']:.1f} t"), ("Each truck", f"{logistics.C['pods_per_truck']} pods"),
                 ("Trucks", f"{logistics.C['pod_trucks']}"), ("Dock lanes", f"{cfg.PROJECT['logistics']['pods']['dock_lanes']}")],
        "frames": [("Dry coolers", f"{cfg.COOL['coolers_per_frame']} × {cfg.COOL['cooler_capacity_mw']:g} MW"),
                   ("Pump units", f"{cfg.COOL['coolers_per_frame']}"),
                   ("Cast-in anchors", f"{C['anchors_per_frame']}"),
                   ("Cast-in conduits", f"{C['conduits_per_frame']}"),
                   ("All frames", f"{C['reject_mw']:.0f} MW")],
    }


def markdown():
    c, s, co, fl, fu = C, cfg.SILO, cfg.COOL, cfg.FLUID, cfg.PROJECT["fuel"]
    pw, di = cfg.POWER, cfg.PROJECT["diesel"]
    hl, hw, hh = pw["inlet_house_m"]
    vl, vw, vh = di["room_vent_m"]
    vapour_rows = "\n".join(f"| {label}, {bar:g} bar, {temp:g} °C | {rho_v:.0f} kg/m³ | {flow*1000:.0f} L/s | {speed:.1f} m/s | {need:.0f} mm for {fu['vapour_velocity_m_s']:g} m/s |" for label,bar,temp,rho_v,flow,speed,need in c["vapour_cases"])
    kg, lpm, gpm = c["flow_total"]
    short = c["target_m3"] - c["tank_m3"]
    if short > 0:
        verdict = (f"**This geometry does not hold {c['target_gal']/1e6:.1f} million US gallons.** With two {s['outer_wall_m']*1000:.0f} mm skins it holds "
                   f"{c['tank_gal']/1e6:.2f} M gal. Keeping the other inputs, the target needs a silo {c['need_height']:.1f} m high or {c['need_od']:.2f} m in outside diameter.")
    else:
        verdict = (f"**This geometry holds {c['tank_gal']/1e6:.2f} million US gallons, {c['tank_of_target']*100-100:.0f}% more than the {c['target_gal']/1e6:.1f} M target.**")
    cases = "\n".join(f"| {od:g} m | {bore:g} m | {height:g} m | {mw:.0f} MW | {n(vol)} m³ | {ride:.0f} min{' (this design)' if i==2 else ''} |"
                      for i,(od,bore,height,mw,vol,ride) in enumerate(c["store_cases"]))
    def outage(mw):
        deficit = c["heat_mw"] - mw
        if deficit <= 1e-9: return "still carries the full load"
        minutes = c["store_mj_k"] / deficit / 60
        return f"store warms 1 K every {minutes/60:.1f} h at full load" if minutes > 120 else f"store warms 1 K every {minutes:.0f} min at full load"
    out_one, out_frame = outage(c["one_out_mw"]), outage(c["frame_out_mw"])
    out_two = outage(c["reject_mw"]-2*co["coolers_per_frame"]*co["cooler_capacity_mw"])
    face_note = (f"A face velocity of {c['cooler_face_ms']:.1f} m/s is high for a dry cooler, where 2 to 4 m/s is usual. A {co['cooler_capacity_mw']:g} MW unit in this casing needs a larger air rise, a deeper coil or more face area. Confirm against a supplier selection."
                 if c["cooler_face_ms"] > 4 else "The face velocity is within the usual 2 to 4 m/s for a dry cooler.")
    word = {8:"Eight",10:"Ten"}.get(c["frames"], str(c["frames"]))
    trucking = trucking_markdown()
    lg = logistics.C
    sc = st.C
    sd = sc["design"]
    wl = walls.C
    lines = f"""# Design calculations

This file is generated from [project.json](project.json) by `python -m gpu_silo calcs`. Change an input, run the command and commit both files. The same numbers appear on the design panels in the animation.

These are concept-stage sizing checks to steer design decisions. They are not a structural, hydraulic or thermal design and have not been reviewed by an engineer.

## 1. Cluster and heat load

| Quantity | Value | Basis |
| --- | ---: | --- |
| {cfg.NAME} pods | {c['pods']} | {cfg.BAYS} per level × {cfg.LEVELS} levels |
| GPU racks | {c['racks']} | {cfg.CLUSTER['racks_per_pod']} × {cfg.CLUSTER['rack_model']} per pod |
| CDUs | {c['cdus']} | one per pod, in the light-grey wall-end section |
| CDU pumps | {c['cdu_pumps']} | one per CDU, VFD controlled |
| Liquid heat per rack | {c['rack_kw']:.0f} kW | input |
| Liquid heat per pod | {c['pod_kw']:.0f} kW | {cfg.CLUSTER['racks_per_pod']} racks |
| **Liquid heat load** | **{c['heat_mw']:.1f} MW** | {c['racks']} × {c['rack_kw']:.0f} kW |

## 2. Thermal store between the concrete walls

The water-glycol fills the gap between the two concrete skins to {c['liquid_top']:.2f} m, {fl['freeboard_m']:.2f} m below the {s['height_m']:g} m rim. There is no separate upper tank.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Outside / inside diameter | {s['outside_diameter_m']:g} / {s['inside_diameter_m']:g} m | input |
| Outer / inner skin | {s['outer_wall_m']*1000:.0f} / {s['inner_wall_m']*1000:.0f} mm | input |
| Liquid gap | {c['wall_gap']:.2f} m | radius {c['tank_r_in']:.2f} to {c['tank_r_out']:.2f} m |
| Plan area of liquid | {c['tank_area']:.1f} m² | π (r₂² − r₁²) |
| **Volume** | **{n(c['tank_m3'])} m³ = {n(c['tank_gal'])} US gal** | area × {c['liquid_top']:.2f} m |
| Target | {n(c['target_m3'])} m³ = {n(c['target_gal'])} US gal | input |
| Volume against target | {c['tank_of_target']*100:.0f}% | {n(abs(short))} m³ {'short' if short>0 else 'over'} |
| Envelope with no wall thickness, full height | {n(c['gross_m3'])} m³ = {n(c['gross_gal'])} US gal | upper bound for {s['outside_diameter_m']:g} / {s['inside_diameter_m']:g} / {s['height_m']:g} m |
| Liquid mass | {n(c['tank_t'])} t | {c['rho']:.0f} kg/m³ |
| Heat capacity | {c['store_mj_k']/1000:.1f} GJ/K = {c['store_mwh_k']:.2f} MWh/K | cp {c['cp']:.2f} kJ/kg·K |
| Temperature rise with no heat rejection | 1 K every {c['min_per_k']:.1f} min | at {c['heat_mw']:.0f} MW |
| Ride-through on a {c['swing']:g} K swing | {c['ride_min']:.0f} min, {c['ride_mwh']:.0f} MWh | input swing. A mixed store can be held {c['swing']:g} K below its limit only in mild weather. |
| Ride-through with the store layered | {th.C['rides']['drawn']['layered']/60:.0f} min | [check 5](report.md#9-check-5-heat-balance-of-the-store): one pass of the store, {th.FOM*100:.0f}% usable, in any weather |
| Static pressure at the base | {c['head_kpa']:.0f} kPa | ρ g h |
| Outer skin hoop tension at the base | {n(c['outer_hoop_kn_m'])} kN/m, {c['outer_hoop_mpa']:.1f} MPa on the gross section | p r, thin wall |
| Inner skin hoop compression at the base | {n(c['inner_hoop_kn_m'])} kN/m, {c['inner_hoop_mpa']:.1f} MPa | p r, thin wall |

{verdict}

### Does the store match the load?

The store's job is to carry the load while heat rejection is reduced. The measure is how long the full load takes to warm the store through the usable {c['swing']:g} K.

| Outside diameter | Bore | Height | Load | Store | Ride-through on {c['swing']:g} K |
| ---: | ---: | ---: | ---: | ---: | ---: |
{cases}

Widening the bore from 13 m to {s['inside_diameter_m']:g} m for the in-line turbine sets takes {n(c['bore_cost_m3'])} m³ out of the store. The {s['outside_diameter_m']:g} m outer wall and the {s['height_m']:g} m height more than give it back.

## 3. Loop flows

Based on a {c['dt']:g} K rise across the load and the same {c['dt']:g} K drop across the coolers.

| Loop | Heat | Mass flow | Volume flow |
| --- | ---: | ---: | ---: |
| Whole cluster | {c['heat_mw']:.0f} MW | {kg:.0f} kg/s | {n(lpm)} L/min, {n(gpm)} US gpm |
| One {cfg.NAME} pod (one CDU pump) | {c['pod_kw']:.0f} kW | {c['flow_pod'][0]:.1f} kg/s | {n(c['flow_pod'][1])} L/min, {n(c['flow_pod'][2])} US gpm |
| One dry cooler (one pump) | {co['cooler_capacity_mw']*1000:.0f} kW | {c['flow_cooler'][0]:.1f} kg/s | {n(c['flow_cooler'][1])} L/min, {n(c['flow_cooler'][2])} US gpm |

At full flow the store turns over once every {c['turnover_min']:.0f} minutes.

## 4. Heat rejection

| Quantity | Value | Basis |
| --- | ---: | --- |
| Steel frames | {c['frames']} | {c['frames_per_tier']} per tier, tiers based at {' and '.join(f'{z:g} m' for z in co['tier_base_m'])} |
| Dry coolers installed | {c['coolers']} × {co['cooler_capacity_mw']:g} MW | {co['coolers_per_frame']} stacked per frame |
| Dry coolers needed for the load | {c['duty_coolers']} | {th.LOAD/1e6:.2f} MW including pump heat ÷ {co['cooler_capacity_mw']:g} MW |
| Spare coolers | {c['standby_coolers']} | N+{c['standby_coolers']} |
| Cooler pumps | {c['cooler_pumps']} | one per cooler |
| **Rejection capacity** | **{c['reject_mw']:.0f} MW** | |
| Margin over the heat load | {c['margin']*100:.0f}% | {c['reject_mw']:.0f} / {c['heat_mw']:.0f} MW |
| One cooler out of service | {c['one_out_mw']:.0f} MW | {out_one} |
| One whole frame out of service | {c['frame_out_mw']:.0f} MW | {out_frame} |
| Two whole frames out of service | {c['reject_mw']-2*co['coolers_per_frame']*co['cooler_capacity_mw']:.0f} MW | {out_two} |

{c['duty_coolers']} coolers carry the load and ten frames of three give {c['coolers']}, so {c['standby_coolers']} are spare. A whole frame can be lowered at full load when the remaining coils have sufficient measured thermal duty.

### One 2 MW cooler

| Quantity | Value | Basis |
| --- | ---: | --- |
| Casing | {co['cooler_length_m']:g} × {co['cooler_section_m']:g} × {co['cooler_section_m']:g} m | input |
| Water-glycol flow | {c['flow_cooler'][0]:.1f} kg/s, {n(c['flow_cooler'][1])} L/min | {c['dt']:g} K drop |
| Pipe bore for 2 m/s | {c['cooler_bore_mm']:.0f} mm | supply and return conduits are drawn at 300 mm |
| Air flow | {c['cooler_air_m3s']:.0f} m³/s | {co['air_rise_k']:g} K air rise |
| Face velocity | {c['cooler_face_ms']:.1f} m/s | over the {c['cooler_face_m2']:.0f} m² outward face |
| Fans drawn | {c['cooler_fans']} | one per 2.25 m of length |

{face_note}

### Frame arrangement

| Quantity | Value | Basis |
| --- | ---: | --- |
| Frame | {co['frame_width_m']:g} m across × {co['frame_height_m']:g} m high × {co['frame_depth_m']:g} m off the wall | input |
| Each row | {co['cooler_length_m']:g} m cooler + {co['pump_unit_length_m']:g} m pump unit | {c['row_height']:.2f} m row height |
| Total frame width | {c['frame_run_m']:.0f} m | {c['frames']} × {co['frame_width_m']:g} m |
| Silo circumference | {c['circumference_m']:.1f} m | π × {s['outside_diameter_m']:g} m |
| Angle taken by one frame | {c['frame_subtends_deg']:.1f}° | flat frame {co['wall_standoff_m']:.2f} m off the wall at its centre |
| Gap from frame back to the curved wall at each end | {c['end_gap_m']:.2f} m | bridged by the anchor struts |
| Cast-in anchors | {c['anchors_per_frame']} per frame, {c['anchors']} in total | {len(co['anchor_columns_m'])} columns × {co['coolers_per_frame']+1} rows |
| Cast-in conduits to the store | {c['conduits_per_frame']} per frame, {c['frame_conduits']} in total | supply and return for each cooler |

{word} {co['frame_width_m']:g} m frames need {c['frame_run_m']:.0f} m of wall and the silo has {c['circumference_m']:.1f} m, so they cannot share one level. They sit in two tiers of {c['frames_per_tier']}, each tier turned {180/c['frames_per_tier']:.0f}° from the other. The upper tier finishes at RL {max(co['tier_base_m'])+co['frame_height_m']:g} m.

## 5. Pod fit in the bore

| Quantity | Value | Basis |
| --- | ---: | --- |
| {cfg.NAME} length | {c['pod_length']:.2f} m | {cfg.BODY_LENGTH:g} m rack housing + {cfg.SECTION:g} m CDU and pump section, which fills the pod out to {cfg.POD['tip_clearance_m']*1000:.0f} mm from the wall |
| Access round the shaft | {cfg.STORE['shaft_access_m']:.2f} m | input |
| Root radius | {cfg.STORE['root_radius_m']:.2f} m | {cfg.STORE['shaft_radius_m']:g} m shaft radius + access |
| Wall-end radius | {c['pod_tip_r']:.2f} m | |
| Corner radius of the rotating frame | {c['pod_corner_r']:.3f} m | {cfg.FRAME_WIDTH:.2f} m wide frame |
| Clear bore radius | {cfg.BORE_R:.2f} m | |
| **Radial clearance** | **{c['pod_clearance']*1000:.0f} mm** | bore − corner |
| Storage height | {c['store_height']:.1f} m | {cfg.LEVELS} levels × {cfg.STORE['pitch_m']:g} m |

### Clearance at the pod roots

The pods come closest to each other at their roots, and a narrower access round the shaft brings the roots closer together.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Between frames, stored at {360/cfg.BAYS:g}° | {c['root_gap_stored']*1000:.0f} mm | at the root corners |
| Between frames, bunched at {cfg.STORE['packed_pitch_degrees']:g}° | {c['root_gap_packed']*1000:.0f} mm | at the root corners |
| Between a pod being lifted and the pods either side of the lifting lane | {c['root_gap_lane']*1000:.0f} mm | lane {360-(cfg.BAYS-1)*cfg.STORE['packed_pitch_degrees']:g}° wide between centre lines |
| Access that would give 100 mm in both cases | {c['access_for_100']:.2f} m | |

### Pod structure and weight

The side trusses are sized in the [design report](report.md#4-check-2-pod-truss). The numbers below come from that design.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Chords | {sd['chord']['name']} | long side vertical, {st.STEEL['hss']} |
| Verticals and diagonals | {sd['web']['name']} | |
| Tip deflection under dead load | {sd['tip']*1000:.1f} mm | span/{st.SPAN/sd['tip']:,.0f}; limit {sc['limit']*1000:g} mm |
| Frame and housing | {sd['frame']/1000:.2f} t | {sd['steel']/1000:.2f} t of steel, {sd['connections']/1000:.2f} t of connections, {sd['housing']/1000:.2f} t of housing |
| **One pod, operating** | **{sc['pod_t']:.2f} t** | {cfg.CLUSTER['racks_per_pod']} racks × {cfg.POD['rack_mass_t']:g} t, {cfg.POD['cdu_pump_mass_t']:g} t of CDU and pump, {cfg.POD['coolant_and_piping_t']:g} t of coolant and piping, frame and housing |
| Moment of one pod about the shaft axis | {sc['moment_axis']/1000:,.0f} kN·m | centre of gravity {sc['arm']:.2f} m from the axis |
| Weight on the shaft, {cfg.TOTAL} pods | {sc['store_weight']/1000:,.0f} kN | {cfg.TOTAL*sc['pod_t']:,.0f} t |
| Shaft | {st.SHAFT_D*1000:.0f} mm diameter, {sc['shaft']['chosen']['section']['wall']*1000:.1f} mm wall | fixed at the base and held at the top by the support rig. [Design report](report.md#5-check-1-central-shaft) |
| Movement of a pod tip from the shaft | {sc['shaft']['chosen']['movement']['total']*1000:.1f} mm | shortening and lean in the worst filling state; limit {sc['shaft']['limit']*1000:g} mm |
| Sideways force at the top of the shaft | {abs(sc['rig']['cases'][1]['reaction'])/1000:,.0f} kN | worst filling state, into the support rig and its {sc['rig']['mounts']} cast-in wall mounts |

## 6. Power

Two in-line gas turbine generator sets stand side by side on the top level, under the lid. The backup diesel sets are on the level below.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Turbine sets | {pw['modules']} × {pw['module_output_mw']:g} MW | {pw['prime_mover']} |
| **Generating capacity** | **{c['gen_mw']:.0f} MW** | |
| Margin over the load | {c['gen_margin']*100:.0f}% | no spare turbine |
| One set | {pw['set_length_m']:g} × {pw['set_width_m']:g} × {pw['set_height_m']:g} m, {pw['set_weight_t']:g} t | published figures for an LM2500+ generator set |
| Diagonal of one set | {c['set_diagonal']:.2f} m | the bore is {s['inside_diameter_m']:g} m |
| Two sets side by side | {c['pair_clear']:.2f} m clear of the wall | {pw['aisle_m']:g} m aisle between them |
| Height needed above the pods | {c['levels_need']:.2f} m | diesel level and turbine level, each with {pw['floor_structure_m']:g} m of floor structure |
| Height available | {c['levels_have']:.2f} m | crown at {cfg.CROWN:g} m, raised lid seat at {s['height_m']+cfg.PROJECT['coordination']['decks']['roof_curb_m']:g} m |
| Weight at the top of the silo | {c['top_weight_t']:.0f} t | {pw['modules']} turbine sets and {di['sets']} diesel sets |

### Roof vents

The lid carries the machine intakes and exhausts. Two interlocked air handlers serve the bore through separate supply and return ducts at the raised curb.

| Vent | Flow | Size on the roof | Speed |
| --- | ---: | --- | ---: |
| Turbine exhaust, each of {pw['modules']} | {pw['exhaust_flow_kg_s']:g} kg/s at {pw['exhaust_temperature_c']:.0f} °C, {c['exhaust_m3s']:.0f} m³/s | stack {pw['exhaust_stack_diameter_m']:g} m in diameter, {pw['exhaust_stack_height_m']:g} m high | {c['stack_ms']:.0f} m/s |
| Turbine air inlet, each of {pw['modules']} | {pw['inlet_air_kg_s']:g} kg/s, {c['turbine_air_m3s']:.0f} m³/s | filter house {hl:g} × {hw:g} × {hh:g} m, {c['filter_face_have']:.0f} m² of filter on two faces | {c['filter_ms']:.1f} m/s |
| Diesel exhaust, each of {di['sets']} | {di['exhaust_m3_s_per_set']:g} m³/s | stack {di['exhaust_stack_diameter_m']:g} m in diameter, {di['exhaust_stack_height_m']:g} m high | {c['diesel_stack_ms']:.0f} m/s |
| Diesel room air, in and out | {c['diesel_room_m3s']:.0f} m³/s | {di['room_vents']} cowls of {vl:g} × {vw:g} m | {c['room_vent_ms']:.1f} m/s |

The turbine filter face needed at {pw['inlet_filter_velocity_m_s']:g} m/s is {c['filter_face_need']:.0f} m². GE's nominal ducts for this engine are 4.5 m² for the inlet and 2.8 m² for the exhaust, so the {c['stack_area']:.1f} m² stack is larger than nominal. The diesel room air removes {c['diesel_room_kw']:.0f} kW radiated by the running sets at a {di['room_air_rise_k']:g} K rise. The diesel flows are typical figures for a 2.5 MW set, not datasheet values.

## 7. Fuel

### Propane for the turbines

| Quantity | Value | Basis |
| --- | ---: | --- |
| Tanks | {fu['tanks']} | {fu['tank_length_m']:g} m long × {fu['tank_diameter_m']:g} m diameter, {fu['distance_m']:g} m from the silo axis |
| Stored liquid | {n(c['fuel_m3'])} m³ = {n(c['fuel_gal'])} US gal | {fu['fill_fraction']*100:.0f}% fill |
| Stored energy | {n(c['fuel_mwh_th'])} MWh thermal | {fu['energy_mj_per_litre']:g} MJ per litre, lower heating value |
| Electricity generated | {n(c['fuel_mwh_e'])} MWh | {fu['generation_efficiency']*100:.0f}% generation efficiency |
| **Run time at full load** | **{c['fuel_hours']:.0f} h ({c['fuel_hours']/24:.1f} days)** | {c['gen_mw']:.0f} MW |
| Burn rate at full load | {c['fuel_burn_m3_h']:.1f} m³/h | one tank every {c['tank_each_m3']*fu['fill_fraction']/c['fuel_burn_m3_h']:.1f} h |

### Is one propane line big enough?

Yes. Both turbines at full load burn {c['fuel_mw_th']:.0f} MW of fuel, which is {c['propane_kg_s']:.2f} kg/s of propane.

| How the propane travels | Density | Flow | Speed in the {fu['line_diameter_m']*1000:.0f} mm line | Bore needed |
| --- | ---: | ---: | ---: | ---: |
| Liquid, pumped | {fu['liquid_density_kg_m3']:g} kg/m³ | {c['propane_l_s']:.1f} L/s | {c['line_liquid_ms']:.2f} m/s | {c['line_liquid_need_mm']:.0f} mm for {fu['liquid_velocity_m_s']:g} m/s |
{vapour_rows}

One {fu['line_diameter_m']*1000:.0f} mm line carries the full flow in any of the three ways with room to spare. A 100 mm line would also do. The turbines need gas at about {pw['fuel_supply_pressure_bar']:g} bar, and propane at that pressure is liquid below about 70 °C. The practical arrangement is to pump liquid up the line and vaporise it beside the turbines. Vaporising takes {c['vaporise_mw']:.1f} MW of heat. The store at 45 to 55 °C is too cool to do it at that pressure, so the vaporiser needs a hotter source such as turbine exhaust heat. The supply pressure is a typical figure for this class of turbine, not a datasheet value.

### Diesel for the backup sets

| Quantity | Value | Basis |
| --- | ---: | --- |
| Backup sets | {di['sets']} × {di['set_output_mw']:g} MW | {di['set_length_m']:g} × {di['set_width_m']:g} × {di['set_height_m']:g} m, {di['set_weight_t']:g} t each |
| **Backup capacity** | **{c['diesel_mw']:.0f} MW** | {c['diesel_share']*100:.0f}% of the load |
| Fuel burn, all sets at full load | {c['diesel_m3_h']:.2f} m³/h | {di['fuel_l_per_h_per_set']:g} L/h per set |
| Day tanks inside | {di['day_tanks']} × {c['day_tank_m3']:.1f} m³ | {c['day_hours']:.1f} h at full load |
| Bulk tank outside | {c['bulk_m3']:.0f} m³ | {di['bulk_tank_length_m']:g} m × {di['bulk_tank_diameter_m']:g} m at the propane tanks, {di['bulk_fill_fraction']*100:.0f}% fill |
| **Run time on the bulk tank** | **{c['bulk_hours']:.0f} h** | all sets at full load |
| Diesel line | {di['line_diameter_m']*1000:.0f} mm | {c['diesel_line_ms']:.2f} m/s at full burn |

The backup covers black start, controls, the cooling plant and about a fifth of the racks. It does not cover the loss of a turbine.

{trucking}

## 10. Operating limits and coordination decisions

The plant and thermal store are sized against {c['heat_mw']:g} MW of installed racks. Normal metered IT is capped at {cfg.CLUSTER['normal_it_limit_mw']:g} MW, subject to available turbine power after auxiliaries and available cooling. The operator chooses the rack mix. For example, {c['reference_active']} full-power racks and {c['reference_spare']} spares at {cfg.CLUSTER['reference_spare_kw']:g} kW each draw {c['reference_it_mw']:.3f} MW. Normal operation requires zero grid import. The four diesels supply the essential bus only during emergencies, with 3 MW reserved for essential plant and up to 7 MW for priority IT.

The [revision J assumption register](assumptions.md) gives the disposition of all 18 questions previously listed here. [Structural checks 7–10](report.md#7-checks-7-to-10-support-rig-shaft-connector-and-wall-mounts-design-loads) include the independent upper floor, the guided shaft collar and the wall seats. The IFC includes the buried fuel crossing, conversion plant and the individual rack positions.

## Fluid properties used

{fl['fluid']}, {fl['glycol_fraction']*100:.0f}% glycol by volume: density {c['rho']:.0f} kg/m³, specific heat {c['cp']:.2f} kJ/kg·K. These are round values for a warm loop and should be replaced with supplier data at the design temperature. 1 US gal = 3.785 L.
"""
    return lines


def trucking_markdown():
    lg, L, P = logistics.C, cfg.PROJECT["logistics"], cfg.PROJECT
    flat, w, site = L["flatbed"], L["water"], L["site"]
    sd = st.C["design"]
    fu = P["fuel"]
    coat = P["coating"]
    hours = L["working_hours_per_day"]
    def when(key):
        return logistics.days_text(key).replace("Days ", "").replace("Day ", "")
    rows = "\n".join(f"| {what} | {vehicle} | {n(count)} | {when(key)} | {count/logistics.span(key)[2]:.1f} |" for key, what, count, vehicle in lg["loads"])
    crew = "\n".join(f"| {name} | {count} |" for name, count in P["jumpform"]["crew"])
    chart = "\n".join(f"| {a['name'].replace('Pods', cfg.NAME + ' pods')} | {a['start']} | {a['end']} | {a['end']-a['start']+1} |" for a in logistics.ACTIVITIES)
    per_day = lg["per_day"]
    busiest = ", ".join(f"day {d}: {per_day[d]:.0f}" for d in sorted((d for d in per_day if d > 0), key=lambda d: -per_day[d])[:3])
    return f"""## 8. Trucking

Road trucks are taken at the usual US limit of {L['gross_vehicle_limit_t']:g} t gross (80,000 lb), working {hours} hours a day. Day numbers are days after the last wall pour. The film shows a sample of each kind of load, and its counters scale to the totals below.

| Load | Vehicle | Trucks | Days | Trucks a day |
| --- | --- | ---: | ---: | ---: |
{rows}

After the last pour {n(lg['loads_after_pour'])} loads arrive in {logistics.DAYS} days. The busiest days are {busiest} loads.

### Pods: the heaviest legal load

| Quantity | Value | Basis |
| --- | ---: | --- |
| One {cfg.NAME} pod | {lg['pod_t']:.1f} t | {cfg.CLUSTER['racks_per_pod']} racks × {cfg.POD['rack_mass_t']:g} t, {sd['frame']/1000:.2f} t of frame and housing as designed, {cfg.POD['cdu_pump_mass_t']:g} t of CDU and pump, {cfg.POD['coolant_and_piping_t']:g} t of coolant and piping |
| Flatbed | {flat['deck_length_m']:g} × {flat['deck_width_m']:g} m deck, {flat['payload_t']:g} t payload | five-axle tractor and trailer |
| Pods that fit on the deck | {lg['pods_by_space']} | {lg['deck_rows']} end to end × {lg['deck_across']} across |
| Pods the payload allows | {lg['pods_by_weight']} | {lg['pods_by_weight']} × {lg['pod_t']:.1f} t = {lg['pods_by_weight']*lg['pod_t']:.1f} t |
| **Pods on each truck** | **{lg['pods_per_truck']}** | {'weight decides, not space' if lg['pods_by_weight']<lg['pods_by_space'] else 'space decides, not weight' if lg['pods_by_space']<lg['pods_by_weight'] else 'space and weight agree'} |
| Height on the road | {lg['pod_load_height']:.2f} m | limit {flat['legal_height_m']:g} m |
| **Trucks for {cfg.TOTAL} pods** | **{lg['pod_trucks']}** | |

The deck has room for {lg['pods_by_space']} pods and the weight limit allows {lg['pods_by_weight']}. The rack weight is an allowance: NVIDIA has not published a shipping weight for the {cfg.CLUSTER['rack_model'].replace('NVIDIA ', '')}.

### Receiving dock

| Quantity | Value | Basis |
| --- | ---: | --- |
| Pods to load each day | {lg['pods_per_day']:.0f} | {cfg.TOTAL} pods in {logistics.span('pods')[2]} days |
| Hoist capacity | {lg['hoist_per_day']:.0f} pods a day | {L['pods']['hoist_minutes_per_pod']} minutes a pod |
| Gantry capacity | {lg['gantry_per_day']:.0f} pods a day | {L['pods']['unload_minutes_per_pod']} minutes a pod |
| Trucks each day | {lg['pod_trucks_per_day']:.0f} | {lg['pods_per_truck']} pods each |
| One truck unloaded in | {lg['truck_turn_min']:.0f} min | |
| Dock capacity | {lg['dock_trucks_per_day']:.0f} trucks a day | {L['pods']['dock_lanes']} back-in lanes under one gantry |
| Cradles on the rail | {L['pods']['buffer_cradles']} | {lg['buffer_hours']:.1f} hours of work for the hoist |

In real time one lane would be enough. The second lane lets one truck back in while another unloads, and the cradles keep the hoist working if a truck is late. The film runs {logistics.span('pods')[2]} days in under a minute, so every truck appears to arrive at once.

### Water-glycol by tanker

| Quantity | Value | Basis |
| --- | ---: | --- |
| Store | {n(lg['water_m3'])} m³, {n(lg['water_t'])} t | section 2 |
| Of which glycol | {n(lg['glycol_m3'])} m³ | {cfg.FLUID['glycol_fraction']*100:.0f}% by volume |
| One tanker | {w['tanker_payload_t']:g} t, {lg['tanker_m3']:.1f} m³ | {L['gross_vehicle_limit_t']:g} t gross |
| **Tanker loads** | **{lg['water_loads']}** | |
| Loads a day | {lg['water_per_day']:.0f} | {lg['water_days']} days, one every {lg['water_headway_min']:.0f} minutes |
| Time in a bay | {lg['water_turn_min']:.0f} min | {w['connect_minutes']} minutes to connect, then {w['pump_m3_per_minute']:g} m³ a minute |
| One bay unloads | {lg['water_bay_per_day']:.0f} loads a day | |
| Bays needed / provided | {lg['water_bays_needed']} / {w['bays']} | {w['bays']-lg['water_bays_needed']} spare |
| Level rises | {lg['water_rise_m_per_day']:.1f} m a day | |
| Youngest concrete the water reaches | {lg['wet_age_min']:.0f} days old | lifts poured one a day, fill from day {logistics.BY_KEY['water']['start']} |
| Bottom lift at full head | {lg['full_head_age']:.0f} days old | day {logistics.BY_KEY['water']['end']} |

The fill is left to the last {lg['water_days']} days so the concrete has as long as possible to dry and gain strength first. The tankers have their own drive off the public road, so {lg['water_loads']} loads never enter the haul ring.

### Liner inside the store

The faces of the store are sprayed with a liner before the fill, to keep the water-glycol off the concrete and its reinforcement.

| Quantity | Value | Basis |
| --- | ---: | --- |
| System | {coat['system']} | input, to be confirmed with a coating supplier for warm water-glycol |
| Wall faces | {n(lg['coat_wall_m2'])} m² | both faces of the gap, {cfg.SILO['height_m']:g} m high |
| Floor of the gap | {n(lg['coat_floor_m2'])} m² | |
| **Area to coat** | **{n(lg['coat_m2'])} m²** | |
| Liner | {coat['thickness_mm']:g} mm, {lg['coat_m3']:.1f} m³ | |
| Output | {n(lg['coat_m2_per_day'])} m² a day | {coat['sprayers']} sprayers at {coat['m2_per_sprayer_hour']:g} m² an hour, from {coat['stages']} stages hung in the gap |
| Time needed / allowed | {lg['coat_days_needed']:.1f} / {logistics.span('coating')[2]} days | days {logistics.BY_KEY['coating']['start']} to {logistics.BY_KEY['coating']['end']} |
| Concrete age when coated | {lg['coat_age_min']} days or more | the last lift is poured on day 0 |

### Coolers, fuel and concrete

| Quantity | Value | Basis |
| --- | ---: | --- |
| One cooler with its pump unit | {lg['cooler_load_t']:.1f} t, {cfg.COOL['cooler_length_m']+cfg.COOL['pump_unit_length_m']:g} m long | one to a {flat['deck_length_m']:g} m deck, {lg['cooler_load_height']:.2f} m high on the road |
| Cooler trucks | {lg['cooler_trucks']} | plus {lg['frame_trucks']} of frame steel |
| Assist crane | {lg['cooler_lifts_per_day']:.0f} lifts a day | {L['coolers']['lift_minutes_per_cooler']} minutes a cooler, {cfg.COOLERS/logistics.span('frames')[2]:.1f} a day needed |
| Propane to fill the tanks | {n(lg['propane_m3'])} m³ | section 7 |
| One propane transport | {L['propane']['transport_load_m3']:g} m³, {lg['propane_load_t']:.1f} t | MC-331 trailer at {L['gross_vehicle_limit_t']:g} t gross |
| **Propane loads** | **{lg['propane_loads']}** | {lg['propane_per_day']:.1f} a day with the diesel, {lg['propane_capacity_per_day']:.0f} a day through {L['propane']['bays']} bays |
| Fuel tanks | {fu['tanks']} propane and 1 diesel | one oversize load each, {L['propane']['tank_mass_t']:g} t a propane tank |
| Concrete in the walls | {n(lg['wall_m3'])} m³ | {lg['lifts']} lifts of {lg['lift_m3']:.0f} m³ |
| **Mixers for one lift** | **{lg['lift_trucks']}** | {L['concrete']['mixer_load_m3']:g} m³ each, one every {lg['mixer_headway_min']:.0f} minutes |
| Pour time for one lift | {lg['lift_pour_h']:.1f} h | {L['concrete']['pump_m3_per_hour']:g} m³ an hour through one pump |
| Mixers for the walls | {lg['wall_trucks']} | |
| Base slab, before the walls | {n(lg['slab_m3'])} m³, {lg['slab_trucks']} mixers | {L['concrete']['slab_thickness_m']:g} m thick, set by the project and checked in [check 4](report.md#11-check-4-foundation) |
| Reinforcement | {lg['rebar_t']:.0f} t, {lg['rebar_trucks']} trucks | {lg['wall_bar_t']:.0f} t in the walls from the design report, with {L['concrete']['wall_bar_allowance']*100:g}% for laps, feet, ties and openings. The slab at {L['concrete']['reinforcement_kg_per_m3']:g} kg per m³ is an allowance. |

### Crew on a typical lift

| Trade | People |
| --- | ---: |
{crew}
| **Total** | **{lg['crew']}** |

Each lift is poured, left to set, stripped, jumped {cfg.SILO['concrete_lift_m']:g} m and reset. The crew rides the forms: placers and finishers on the pour deck, ironworkers on the starter bars, carpenters and jack operators on the working platform below.

### Roads and staging areas

| Area | Layout | Used by |
| --- | --- | --- |
| Public road | {site['public_road_north_m']:g} m north of the silo. All site traffic arrives from the west and leaves to the east, so every turn is a right turn. | everything |
| Access road and gate | Two lanes from the public road to the ring at a bearing of {site['access_bearing_degrees']:g}° | all trucks except the water tankers |
| Holding lanes | {site['holding_lanes']} lanes beside the access road | pod trucks waiting to be called to the dock |
| Haul ring | One-way, anticlockwise. Running lane at {site['haul_ring_radius_m']:g} m radius and a stopping lane inside it at {site['stopping_lane_radius_m']:g} m. The crane track is outside it. | every truck makes one lap |
| Receiving dock | {L['pods']['dock_lanes']} back-in lanes either side of the rail, under one gantry | pod trucks |
| Cooler laydown | {cfg.FRAMES} frame positions inside the ring. Trucks stop in the stopping lane and an assist crane lifts each cooler into its frame. | cooler and frame-steel trucks |
| Water drive | Its own entrance and exit on the public road, {w['bays']} drive-through bays, a pump and a buried fill line to the wall | water tankers |
| Fuel farm | Each tank truck drives through its slot and leaves by a road out of the back. Transports unload in a {L['propane']['bays']}-bay lay-by on the ring beside the tank header. | tank deliveries, propane transports |
| Concrete bays | {L['concrete']['bays']} back-in bays at the pump hopper by the ground opening, before the dock is built | truck mixers |

## 9. Programme

Day 0 is the last wall pour. The concrete reaches its 28-day strength on day {logistics.DAYS}, and the work is laid out to finish that day.

| Activity | First day | Last day | Days |
| --- | ---: | ---: | ---: |
{chart}

The walls take {lg['wall_days']:.0f} days at {P['jumpform']['lifts_per_day']:g} lift a day and are outside the {logistics.DAYS} days. The pod cage is built beside the silo in those days, a level a day, so it is ready to lift in on day {logistics.BY_KEY['cage']['start']}. One crawler crane does every heavy lift, so the cooler frames are hung before the power levels and the lid. The power levels are fabricated on the ground while the pods load. The store is coated on days {logistics.BY_KEY['coating']['start']} to {logistics.BY_KEY['coating']['end']} and filled over the last {lg['water_days']} days. Commissioning follows handover and is not part of this programme. The busiest day is day {lg['peak_day']} with about {lg['peak_loads']:.0f} loads."""


def write(path=FILE):
    from . import report
    Path(path).write_text(markdown(), encoding="utf-8", newline="\n")
    report.write()
    return path


def current(path=FILE):
    return not differences(path)


def differences(path=FILE):
    from . import report
    found = [] if Path(path).is_file() and Path(path).read_text(encoding="utf-8") == markdown() else [f"{Path(path).name} differs"]
    return found + report.differences()
