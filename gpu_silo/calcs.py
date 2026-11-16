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
        "frames": [("Dry coolers", f"{cfg.COOL['coolers_per_frame']} × {cfg.COOL['cooler_capacity_mw']:g} MW"),
                   ("Pump units", f"{cfg.COOL['coolers_per_frame']}"),
                   ("Cast-in anchors", f"{C['anchors_per_frame']}"),
                   ("Cast-in conduits", f"{C['conduits_per_frame']}"),
                   ("All frames", f"{C['reject_mw']:.0f} MW")],
    }


def markdown():
    c, s, co, fl = C, cfg.SILO, cfg.COOL, cfg.FLUID
    kg, lpm, gpm = c["flow_total"]
    short = c["target_m3"] - c["tank_m3"]
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
| Volume against target | {c['tank_of_target']*100:.0f}% | {n(short)} m³ short |
| Envelope with no wall thickness, full height | {n(c['gross_m3'])} m³ = {n(c['gross_gal'])} US gal | upper bound for 20 / 13 / 30 m |
| Liquid mass | {n(c['tank_t'])} t | {c['rho']:.0f} kg/m³ |
| Heat capacity | {c['store_mj_k']/1000:.1f} GJ/K = {c['store_mwh_k']:.2f} MWh/K | cp {c['cp']:.2f} kJ/kg·K |
| Temperature rise with no heat rejection | 1 K every {c['min_per_k']:.1f} min | at {c['heat_mw']:.0f} MW |
| Ride-through on a {c['swing']:g} K swing | {c['ride_min']:.0f} min, {c['ride_mwh']:.0f} MWh | input swing |
| Static pressure at the base | {c['head_kpa']:.0f} kPa | ρ g h |
| Outer skin hoop tension at the base | {n(c['outer_hoop_kn_m'])} kN/m, {c['outer_hoop_mpa']:.1f} MPa on the gross section | p r, thin wall |
| Inner skin hoop compression at the base | {n(c['inner_hoop_kn_m'])} kN/m, {c['inner_hoop_mpa']:.1f} MPa | p r, thin wall |

**The 20 m / 13 m / 30 m geometry does not hold 1.5 million US gallons.** Even with zero wall thickness the annulus holds {c['gross_gal']/1e6:.2f} M gal. With two {s['outer_wall_m']*1000:.0f} mm skins it holds {c['tank_gal']/1e6:.2f} M gal. Keeping the other inputs, the target needs one of:

| Change | Required value |
| --- | ---: |
| Taller silo | {c['need_height']:.1f} m |
| Larger outside diameter | {c['need_od']:.2f} m |
| Smaller inside diameter | {c['need_id']:.2f} m, which no longer fits a {c['pod_length']:.1f} m pod |

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
| Dry coolers | {c['coolers']} × {co['cooler_capacity_mw']:g} MW | {co['coolers_per_frame']} stacked per frame |
| Cooler pumps | {c['cooler_pumps']} | one per cooler |
| **Rejection capacity** | **{c['reject_mw']:.0f} MW** | |
| Margin over the heat load | {c['margin']*100:.0f}% | {c['reject_mw']:.0f} / {c['heat_mw']:.0f} MW |
| One cooler out of service | {c['one_out_mw']:.0f} MW | store warms 1 K every {c['one_out_h_per_k']:.1f} h at full load |
| One whole frame out of service | {c['frame_out_mw']:.0f} MW | store warms 1 K every {c['frame_out_min_per_k']:.0f} min at full load |

The coolers match the load with no spare unit. The thermal store carries a single cooler outage for hours, but there is no installed N+1.

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

Eight {co['frame_width_m']:g} m frames need {c['frame_run_m']:.0f} m of wall and the silo has {c['circumference_m']:.1f} m, so they cannot share one level. They sit in two tiers of four, each tier turned 45° from the other. The upper tier finishes at RL {max(co['tier_base_m'])+co['frame_height_m']:g} m.

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

## 6. Open questions raised by these numbers

1. **Tank volume.** The geometry gives {c['tank_gal']/1e6:.2f} M US gal against a 1.5 M target. See the three options in section 2.
2. **Rack generation.** {c['rack_kw']:.0f} kW per rack matches a GB200-class NVL72 (about 120 to 132 kW). Published figures for the Vera Rubin NVL72 are about 190 to 230 kW per rack, which would put {c['racks']} racks at {c['racks']*0.19:.0f} to {c['racks']*0.23:.0f} MW. Confirm the rack generation before fixing the cooler count.
3. **Cooling redundancy.** {c['coolers']} MW of coolers for a {c['heat_mw']:.0f} MW load has no spare. The earlier concept allowed 32 to 35 MW with N+1 pumps.
4. **Wall design.** {c['head_kpa']:.0f} kPa at the base puts about {c['outer_hoop_mpa']:.0f} MPa of hoop tension in a {s['outer_wall_m']*1000:.0f} mm outer skin. That needs post-tensioning or a thicker wall, and the inner skin needs a buckling check under external pressure.
5. **Pod clearance.** {c['pod_clearance']*1000:.0f} mm between the rotating pod and the bore is tight for a {c['pod_length']:.1f} m cantilever.
6. **Air path.** Four coolers stacked vertically discharge outward. Recirculation between rows and between the two tiers has not been checked.
7. **Electrical supply.** The two power modules in the film are placeholders. Supplying about {c['heat_mw']:.0f} MW of IT load is not yet sized.

## Fluid properties used

{fl['fluid']}, {fl['glycol_fraction']*100:.0f}% glycol by volume: density {c['rho']:.0f} kg/m³, specific heat {c['cp']:.2f} kJ/kg·K. These are round values for a warm loop and should be replaced with supplier data at the design temperature. 1 US gal = 3.785 L.
"""
    return lines


def write(path=FILE):
    Path(path).write_text(markdown(), encoding="utf-8", newline="\n")
    return path


def current(path=FILE):
    return Path(path).is_file() and Path(path).read_text(encoding="utf-8") == markdown()
