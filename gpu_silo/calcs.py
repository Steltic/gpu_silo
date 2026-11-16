"""Design calculations derived from design/project.json.

Run ``python -m gpu_silo calcs`` to rewrite design/calcs.md. The same numbers
feed the design panels in the animation, so the film, the model and the written
calculations cannot drift apart.
"""
import math
from pathlib import Path

from . import design as cfg

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
    c["duty_coolers"] = math.ceil(c["heat_mw"] / co["cooler_capacity_mw"] - 1e-9)
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
    # The store against the load, compared with the earlier 20 m, 32 MW design
    def store(od, mw):
        volume = math.pi * ((od / 2 - silo["outer_wall_m"])**2 - c["tank_r_in"]**2) * c["liquid_top"]
        return volume, volume * rho * cp / 1000 / mw / 60 * c["swing"]
    c["store_cases"] = [(20.0, 32.0, *store(20.0, 32.0)), (20.0, c["heat_mw"], *store(20.0, c["heat_mw"])),
                        (silo["outside_diameter_m"], c["heat_mw"], c["tank_m3"], c["ride_min"])]
    want = c["store_cases"][0][3] * c["heat_mw"] * 60 / c["swing"] / (rho * cp / 1000)
    c["od_same_ride"] = 2 * (math.sqrt(want / (math.pi * c["liquid_top"]) + c["tank_r_in"]**2) + silo["outer_wall_m"])
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
    # Power modules
    pw=cfg.POWER
    c["gen_mw"]=pw["modules"]*pw["module_output_mw"]
    c["gen_margin"]=c["gen_mw"]/c["heat_mw"]-1
    c["turbine_air_m3s"]=pw["inlet_air_kg_s"]/air_rho
    c["exhaust_rho"]=353/(pw["exhaust_temperature_c"]+273.15)
    c["exhaust_m3s"]=pw["exhaust_flow_kg_s"]/c["exhaust_rho"]
    c["vent_area"]=pw["vents_per_module"]*math.pi*(pw["vent_diameter_m"]/2)**2
    c["vent_ms"]=c["exhaust_m3s"]/c["vent_area"]
    c["vent_need_m"]=math.sqrt(4*c["exhaust_m3s"]/pw["vents_per_module"]/30/math.pi)
    c["turbine_heat_mw"]=pw["module_output_mw"]/fu["generation_efficiency"]-pw["module_output_mw"]
    c["fuel_hours"]=c["fuel_mwh_e"]/c["gen_mw"]
    # Natural convection in the bore: in through the door plug, out through the roof vents
    ve=cfg.PROJECT["ventilation"]
    c["door_fan_area"]=ve["door_fans"]*math.pi*(ve["door_fan_diameter_m"]/2)**2
    c["roof_vent_area"]=ve["roof_air_vents"]*math.pi*(ve["roof_air_vent_diameter_m"]/2)**2
    c["stack_height"]=silo["height_m"]-cfg.DOOR_HEIGHT/2
    c["stack_pa"]=air_rho*G*c["stack_height"]*ve["air_rise_k"]/300
    c["stack_ms"]=math.sqrt(2*c["stack_pa"]/(air_rho*ve["loss_coefficient"]))
    c["stack_m3s"]=c["stack_ms"]*c["door_fan_area"]
    c["stack_kw"]=c["stack_m3s"]*air_rho*air_cp*ve["air_rise_k"]
    c["both_turbines_air_m3s"]=pw["modules"]*c["turbine_air_m3s"]
    c["fuel_burn_m3_h"]=c["fuel_m3"]/c["fuel_hours"]
    # Pod fit
    longest = cfg.BODY_LENGTH + max([cfg.SECTION, *cfg.SECTIONS.values()])
    c["pod_length"] = cfg.BODY_LENGTH + cfg.SECTION
    c["pod_tip_r"] = cfg.STORE["root_radius_m"] + longest
    c["pod_corner_r"] = math.hypot(c["pod_tip_r"], cfg.FRAME_WIDTH / 2)
    c["pod_clearance"] = ri - c["pod_corner_r"]
    c["store_height"] = cfg.LEVELS * cfg.STORE["pitch_m"]
    return c


C = compute()


def n(value, digits=0):
    return f"{value:,.{digits}f}"


def strip():
    """Five figures kept on screen for the whole film."""
    return [(n(C["racks"]), f"{cfg.CLUSTER['rack_model'].split()[-1]} racks"),
            (n(C["pods"]), f"{cfg.NAME} pods"),
            (n(C["heat_mw"]) + " MW", "liquid heat"),
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
        ("Liquid heat load", f"{C['heat_mw']:.0f} MW"),
        ("SILO", ""),
        ("Outside / inside", f"{s['outside_diameter_m']:g} / {s['inside_diameter_m']:g} m"),
        ("Height", f"{s['height_m']:g} m"),
        ("Liquid gap", f"{C['wall_gap']:.2f} m"),
        ("THERMAL STORE", ""),
        ("Water-glycol", f"{n(C['tank_m3'])} m³"),
        ("", f"{C['tank_gal']/1e6:.2f} M US gal"),
        ("Loop flow", f"{n(C['flow_total'][1]/1000,1)} m³/min"),
        ("Heat buffer", f"{C['min_per_k']:.1f} min / K"),
        ("HEAT REJECTION", ""),
        ("Dry coolers", f"{C['coolers']} × {co['cooler_capacity_mw']:g} MW"),
        ("Steel frames", f"{C['frames']}"),
        ("Frame size", f"{co['frame_width_m']:g} × {co['frame_height_m']:g} m"),
        ("Cooler pumps", f"{C['cooler_pumps']}"),
        ("Capacity / load", f"{C['reject_mw']:.0f} / {C['heat_mw']:.0f} MW"),
    ]


def panel():
    """Short label and value pairs used by the scene panels."""
    return {
        "store": [("Liquid gap", f"{C['wall_gap']:.2f} m"), ("Fill level", f"{C['liquid_top']:.2f} m"),
                  ("Volume", f"{n(C['tank_m3'])} m³"), ("", f"{C['tank_gal']/1e6:.2f} M US gal"),
                  ("Target", f"{C['target_gal']/1e6:.2f} M US gal"),
                  ("Heat buffer", f"{C['min_per_k']:.1f} min / K")],
        "fuel": [("Tanks", f"{cfg.PROJECT['fuel']['tanks']} × {cfg.PROJECT['fuel']['tank_length_m']:g} m"),
                 ("Tank diameter", f"{cfg.PROJECT['fuel']['tank_diameter_m']:g} m"),
                 ("Stored propane", f"{n(C['fuel_m3'])} m³"),
                 ("Heat in the fuel", f"{n(C['fuel_mwh_th'])} MWh"),
                 ("Electricity", f"{n(C['fuel_mwh_e'])} MWh"),
                 (f"Run time at {C['heat_mw']:.0f} MW", f"{C['fuel_hours']:.0f} h")],
        "plan": [("Liquid heat", f"{C['heat_mw']:.0f} MW"), ("Loop flow", f"{n(C['flow_total'][1]/1000,1)} m³/min"),
                 ("Rise across the pods", f"{C['dt']:g} K"), ("Store", f"{n(C['tank_m3'])} m³"),
                 ("Store turnover", f"{C['turnover_min']:.0f} min")],
        "turbine": [("Output", f"{cfg.POWER['module_output_mw']:g} MW"), ("Type", "Aeroderivative"),
                    ("Class", "GE LM2500"), ("Air", f"{cfg.POWER['inlet_air_kg_s']:.0f} kg/s"),
                    ("Exhaust", f"{cfg.POWER['exhaust_temperature_c']:.0f} °C")],
        "air": [("Door plug", f"{cfg.PROJECT['ventilation']['door_fans']} fans"), ("Roof vents", f"{cfg.PROJECT['ventilation']['roof_air_vents']}"),
                ("Natural convection", f"{C['stack_m3s']:.1f} m³/s"), ("Heat carried", f"{C['stack_kw']:.0f} kW")],
        "section": [("Power modules", f"{cfg.POWER['modules']} × {cfg.POWER['module_output_mw']:g} MW"), ("Electrical load", f"{C['heat_mw']:.0f} MW"),
                    (f"{cfg.NAME} pods on the shaft", f"{C['pods']}"), ("Dry coolers", f"{C['coolers']} × {cfg.COOL['cooler_capacity_mw']:g} MW"),
                    ("Propane stored", f"{n(C['fuel_m3'])} m³"), ("Run time", f"{C['fuel_hours']:.0f} h")],
        "frames": [("Dry coolers", f"{cfg.COOL['coolers_per_frame']} × {cfg.COOL['cooler_capacity_mw']:g} MW"),
                   ("Pump units", f"{cfg.COOL['coolers_per_frame']}"),
                   ("Cast-in anchors", f"{C['anchors_per_frame']}"),
                   ("Cast-in conduits", f"{C['conduits_per_frame']}"),
                   ("All frames", f"{C['reject_mw']:.0f} MW")],
    }


def markdown():
    c, s, co, fl, fu = C, cfg.SILO, cfg.COOL, cfg.FLUID, cfg.PROJECT["fuel"]
    pw, ve = cfg.POWER, cfg.PROJECT["ventilation"]
    kg, lpm, gpm = c["flow_total"]
    short = c["target_m3"] - c["tank_m3"]
    if short > 0:
        verdict = (f"**This geometry does not hold {c['target_gal']/1e6:.1f} million US gallons.** With two {s['outer_wall_m']*1000:.0f} mm skins it holds "
                   f"{c['tank_gal']/1e6:.2f} M gal. Keeping the other inputs, the target needs a silo {c['need_height']:.1f} m high or {c['need_od']:.2f} m in outside diameter.")
    else:
        verdict = (f"**This geometry holds {c['tank_gal']/1e6:.2f} million US gallons, {c['tank_of_target']*100-100:.0f}% more than the {c['target_gal']/1e6:.1f} M target.**")
    cases = "\n".join(f"| {od:g} m{' (earlier design)' if i==0 else ' (this design)' if i==2 else ''} | {mw:.0f} MW | {n(vol)} m³ | {ride:.0f} min |"
                      for i,(od,mw,vol,ride) in enumerate(c["store_cases"]))
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
| Ride-through on a {c['swing']:g} K swing | {c['ride_min']:.0f} min, {c['ride_mwh']:.0f} MWh | input swing |
| Static pressure at the base | {c['head_kpa']:.0f} kPa | ρ g h |
| Outer skin hoop tension at the base | {n(c['outer_hoop_kn_m'])} kN/m, {c['outer_hoop_mpa']:.1f} MPa on the gross section | p r, thin wall |
| Inner skin hoop compression at the base | {n(c['inner_hoop_kn_m'])} kN/m, {c['inner_hoop_mpa']:.1f} MPa | p r, thin wall |

{verdict}

### Does the store match the load?

The store's job is to carry the load while heat rejection is reduced. The measure is how long the full load takes to warm the store through the usable {c['swing']:g} K.

| Silo outside diameter | Load | Store | Ride-through on {c['swing']:g} K |
| --- | ---: | ---: | ---: |
{cases}

Going from 20 m to {s['outside_diameter_m']:g} m adds {n(c['tank_m3']-c['store_cases'][0][2])} m³ and brings the ride-through at {c['heat_mw']:.0f} MW from {c['store_cases'][1][3]:.0f} to {c['ride_min']:.0f} minutes. The earlier 32 MW design had {c['store_cases'][0][3]:.0f} minutes. Matching that at {c['heat_mw']:.0f} MW needs an outside diameter of {c['od_same_ride']:.1f} m, or a silo {c['store_cases'][0][3]/c['ride_min']*c['liquid_top']+fl['freeboard_m']:.1f} m high at {s['outside_diameter_m']:g} m.

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
| Dry coolers needed for the load | {c['duty_coolers']} | {c['heat_mw']:.0f} MW ÷ {co['cooler_capacity_mw']:g} MW |
| Spare coolers | {c['standby_coolers']} | N+{c['standby_coolers']} |
| Cooler pumps | {c['cooler_pumps']} | one per cooler |
| **Rejection capacity** | **{c['reject_mw']:.0f} MW** | |
| Margin over the heat load | {c['margin']*100:.0f}% | {c['reject_mw']:.0f} / {c['heat_mw']:.0f} MW |
| One cooler out of service | {c['one_out_mw']:.0f} MW | {out_one} |
| One whole frame out of service | {c['frame_out_mw']:.0f} MW | {out_frame} |
| Two whole frames out of service | {c['reject_mw']-2*co['coolers_per_frame']*co['cooler_capacity_mw']:.0f} MW | {out_two} |

{c['duty_coolers']} coolers carry the load and ten frames of three give {c['coolers']}, so {c['standby_coolers']} are spare. A whole frame can be lowered for service at full load.

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
| {cfg.NAME} length | {c['pod_length']:.2f} m | {cfg.BODY_LENGTH:g} m rack housing + {cfg.SECTION:g} m CDU and pump section |
| Root radius on the shaft | {cfg.STORE['root_radius_m']:.2f} m | input |
| Wall-end radius | {c['pod_tip_r']:.2f} m | |
| Corner radius of the rotating frame | {c['pod_corner_r']:.3f} m | {cfg.FRAME_WIDTH:.2f} m wide frame |
| Clear bore radius | {cfg.BORE_R:.2f} m | |
| **Radial clearance** | **{c['pod_clearance']*1000:.0f} mm** | bore − corner |
| Storage height | {c['store_height']:.1f} m | {cfg.LEVELS} levels × {cfg.STORE['pitch_m']:g} m |

## 6. Power and fuel

| Quantity | Value | Basis |
| --- | ---: | --- |
| Power modules | {pw['modules']} × {pw['module_output_mw']:g} MW | {pw['prime_mover']} |
| **Generating capacity** | **{c['gen_mw']:.0f} MW** | |
| Margin over the load | {c['gen_margin']*100:.0f}% | no spare module |
| Combustion air, one turbine | {pw['inlet_air_kg_s']:g} kg/s, {c['turbine_air_m3s']:.0f} m³/s | published figure for a 25 MW LM2500 |
| Exhaust, one turbine | {pw['exhaust_flow_kg_s']:g} kg/s at {pw['exhaust_temperature_c']:.0f} °C, {c['exhaust_m3s']:.0f} m³/s | published figure |
| Exhaust vents as drawn | {pw['vents_per_module']} × {pw['vent_diameter_m']:g} m per module | {c['vent_ms']:.0f} m/s in the vent |
| Vent diameter for 30 m/s | {c['vent_need_m']:.1f} m | each of {pw['vents_per_module']} per module |
| Heat rejected by one turbine | {c['turbine_heat_mw']:.0f} MW | at {fu['generation_efficiency']*100:.0f}% efficiency, mostly in the exhaust |

The modules burn {fu['gas'].lower()} from tanks beside the silo. One gas line runs along the ground, up the outside wall, over the lid and down to the modules.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Tanks | {fu['tanks']} | {fu['tank_length_m']:g} m long × {fu['tank_diameter_m']:g} m diameter, {fu['distance_m']:g} m from the silo axis |
| Volume of one tank | {c['tank_each_m3']:.0f} m³ | cylinder with hemispherical ends |
| Stored liquid | {n(c['fuel_m3'])} m³ = {n(c['fuel_gal'])} US gal | {fu['fill_fraction']*100:.0f}% fill |
| Stored energy | {n(c['fuel_mwh_th'])} MWh thermal | {fu['energy_mj_per_litre']:g} MJ per litre, lower heating value |
| Electricity generated | {n(c['fuel_mwh_e'])} MWh | {fu['generation_efficiency']*100:.0f}% generation efficiency |
| **Run time at full load** | **{c['fuel_hours']:.0f} h ({c['fuel_hours']/24:.1f} days)** | {c['gen_mw']:.0f} MW |
| Burn rate at full load | {c['fuel_burn_m3_h']:.1f} m³/h | one {fu['tank_length_m']:g} m tank every {c['tank_each_m3']*fu['fill_fraction']/c['fuel_burn_m3_h']:.1f} h |

## 7. Air in the bore

A panel with {ve['door_fans']} fans plugs the ground door and {ve['roof_air_vents']} vents sit in the lid. Air warmed by the pods rises, leaves through the roof and draws cool air in at the bottom.

| Quantity | Value | Basis |
| --- | ---: | --- |
| Height of the air column | {c['stack_height']:.1f} m | door centre to the lid |
| Driving pressure | {c['stack_pa']:.1f} Pa | {ve['air_rise_k']:g} K warmer inside, ρ g h ΔT / T |
| Inlet area | {c['door_fan_area']:.2f} m² | {ve['door_fans']} fans of {ve['door_fan_diameter_m']:g} m in the door plug |
| Outlet area | {c['roof_vent_area']:.1f} m² | {ve['roof_air_vents']} roof vents of {ve['roof_air_vent_diameter_m']:g} m |
| Air speed at the inlet | {c['stack_ms']:.1f} m/s | loss coefficient {ve['loss_coefficient']:g} |
| Air flow by natural convection | {c['stack_m3s']:.1f} m³/s | |
| **Heat carried away** | **{c['stack_kw']:.0f} kW** | {c['stack_kw']/c['heat_mw']/10:.2f}% of the {c['heat_mw']:.0f} MW load |
| Combustion air for both turbines | {c['both_turbines_air_m3s']:.0f} m³/s | {c['both_turbines_air_m3s']/c['stack_m3s']:.0f} times the convection flow |

Natural convection through a door-sized inlet moves tens of kilowatts. That suits pods that put all of their heat into the liquid. It cannot supply the turbines, which need their own air inlets.

## 8. Open questions raised by these numbers

1. **Store size.** {c['tank_gal']/1e6:.2f} M US gal gives {c['ride_min']:.0f} minutes of ride-through at {c['heat_mw']:.0f} MW. Decide the ride-through the site needs. See section 2.
2. **Rack heat.** {c['rack_kw']:.0f} kW per rack is {c['heat_mw']:.0f} MW over {c['racks']} racks. Published figures for the Vera Rubin NVL72 run from about 190 to 230 kW, so the upper end would be {c['racks']*.23:.0f} MW.
3. **Generation.** Two {pw['module_output_mw']:g} MW modules match the {c['heat_mw']:.0f} MW load with no spare, and pumps, fans and conversion losses add to that load. A 25 MW aeroderivative package with its generator, inlet filter and exhaust silencer is far larger than the 2.5 × 2.5 m section drawn.
4. **Turbine air and exhaust.** Each turbine needs about {c['turbine_air_m3s']:.0f} m³/s of air and discharges about {c['exhaust_m3s']:.0f} m³/s of exhaust at {pw['exhaust_temperature_c']:.0f} °C. The vents as drawn would run at {c['vent_ms']:.0f} m/s. Inlets, vent sizes and the heat next to the pods and the store are not designed.
5. **Wall design.** {c['head_kpa']:.0f} kPa at the base puts about {c['outer_hoop_mpa']:.0f} MPa of hoop tension in a {s['outer_wall_m']*1000:.0f} mm outer skin. That needs post-tensioning or a thicker wall, and the inner skin needs a buckling check under external pressure.
6. **Pod clearance.** {c['pod_clearance']*1000:.0f} mm between the rotating pod and the bore is tight for a {c['pod_length']:.1f} m cantilever.
7. **Cooler air path.** Three coolers stacked vertically discharge outward at {c['cooler_face_ms']:.1f} m/s. Recirculation between rows and between the two tiers has not been checked.
8. **Frame weight.** A frame of three 12 m coolers is a heavy pick at {cfg.SITE['crane_track_radius_m']-cfg.OUTSIDE_R-co['wall_standoff_m']-co['frame_depth_m']/2:.0f} m radius. The crane and the cast-in anchors are not sized.
9. **Fuel.** {n(c['fuel_m3'])} m³ of propane runs the site for about {c['fuel_hours']:.0f} hours. Separation distances, bunding and the resupply rate have not been checked.
10. **Power in the shaft.** {c['heat_mw']:.0f} MW passes down the steel shaft to {c['pods']} pods, {c['pod_kw']:.0f} kW each. The busbar, its cooling and the connection at each level are not designed.
11. **Pod spacing.** The levels are {cfg.STORE['pitch_m']:g} m apart, which leaves {(cfg.STORE['pitch_m']-cfg.FRAME_HEIGHT)*1000:.0f} mm between pods. A full 0.5 m needs {(cfg.FRAME_HEIGHT+.5-cfg.STORE['pitch_m'])*(cfg.LEVELS-1):.1f} m more height than the two power modules leave under the lid.

## Fluid properties used

{fl['fluid']}, {fl['glycol_fraction']*100:.0f}% glycol by volume: density {c['rho']:.0f} kg/m³, specific heat {c['cp']:.2f} kJ/kg·K. These are round values for a warm loop and should be replaced with supplier data at the design temperature. 1 US gal = 3.785 L.
"""
    return lines


def write(path=FILE):
    Path(path).write_text(markdown(), encoding="utf-8", newline="\n")
    return path


def current(path=FILE):
    return Path(path).is_file() and Path(path).read_text(encoding="utf-8") == markdown()
