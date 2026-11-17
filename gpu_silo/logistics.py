"""Truck loads and the 28-day programme, worked out from design/project.json.

Day 0 is the day the last wall lift is poured. The concrete reaches its 28-day
strength on day 28, and the programme is laid out so the crew leaves that day.
"""
import math

from . import design as cfg

L = cfg.PROJECT["logistics"]
S = cfg.PROJECT["schedule"]
J = cfg.PROJECT["jumpform"]
DAYS = S["days"]
HOURS = L["working_hours_per_day"]
ACTIVITIES = S["activities"]
BY_KEY = {a["key"]: a for a in ACTIVITIES}


def span(key):
    a = BY_KEY[key]
    return a["start"], a["end"], a["end"] - a["start"] + 1


def compute():
    c = {}
    silo, pod, fl, fu = cfg.SILO, cfg.POD, cfg.FLUID, cfg.PROJECT["fuel"]
    di, pw, co = cfg.PROJECT["diesel"], cfg.POWER, cfg.COOL
    flat = L["flatbed"]
    # Pods: weight decides the load, not the deck.
    c["pod_t"] = cfg.CLUSTER["racks_per_pod"] * pod["rack_mass_t"] + pod["frame_mass_t"] + pod["cdu_pump_mass_t"]
    length = cfg.BODY_LENGTH + cfg.SECTION
    gap = L["pods"]["load_gap_m"]
    c["deck_rows"] = int((flat["deck_length_m"] + gap) // (length + gap))
    c["deck_across"] = int((flat["deck_width_m"] + gap) // (cfg.FRAME_WIDTH + gap))
    c["pods_by_space"] = c["deck_rows"] * c["deck_across"]
    c["pods_by_weight"] = int(flat["payload_t"] // c["pod_t"])
    c["pods_per_truck"] = max(1, min(c["pods_by_space"], c["pods_by_weight"]))
    c["pod_trucks"] = math.ceil(cfg.TOTAL / c["pods_per_truck"])
    c["pod_load_t"] = c["pods_per_truck"] * c["pod_t"]
    c["pod_load_height"] = flat["deck_height_m"] + cfg.FRAME_HEIGHT
    _, _, days = span("pods")
    c["pods_per_day"] = cfg.TOTAL / days
    c["pod_trucks_per_day"] = c["pod_trucks"] / days
    c["hoist_per_day"] = HOURS * 60 / L["pods"]["hoist_minutes_per_pod"]
    c["gantry_per_day"] = HOURS * 60 / L["pods"]["unload_minutes_per_pod"]
    c["truck_turn_min"] = c["pods_per_truck"] * L["pods"]["unload_minutes_per_pod"]
    c["dock_trucks_per_day"] = L["pods"]["dock_lanes"] * HOURS * 60 / c["truck_turn_min"]
    c["buffer_hours"] = L["pods"]["buffer_cradles"] * L["pods"]["hoist_minutes_per_pod"] / 60
    # Water-glycol
    volume = math.pi * ((cfg.OUTSIDE_R - silo["outer_wall_m"])**2 - (cfg.BORE_R + silo["inner_wall_m"])**2) * cfg.LIQUID_TOP
    c["water_m3"] = volume
    c["water_t"] = volume * fl["density_kg_m3"] / 1000
    w = L["water"]
    c["tanker_m3"] = w["tanker_payload_t"] * 1000 / fl["density_kg_m3"]
    c["water_loads"] = math.ceil(c["water_t"] / w["tanker_payload_t"])
    c["glycol_m3"] = volume * fl["glycol_fraction"]
    _, _, days = span("water")
    c["water_days"] = days
    c["water_per_day"] = c["water_loads"] / days
    c["water_headway_min"] = HOURS * 60 / c["water_per_day"]
    c["water_turn_min"] = w["connect_minutes"] + c["tanker_m3"] / w["pump_m3_per_minute"]
    c["water_bay_per_day"] = HOURS * 60 / c["water_turn_min"]
    c["water_bays_needed"] = math.ceil(c["water_per_day"] / c["water_bay_per_day"] - 1e-9)
    c["water_capacity_per_day"] = w["bays"] * c["water_bay_per_day"]
    c["water_rise_m_per_day"] = cfg.LIQUID_TOP / days
    # Age of the concrete when the water reaches it. Lift k is poured on day k - lifts.
    lifts = round(silo["height_m"] / silo["concrete_lift_m"])
    start = BY_KEY["water"]["start"]
    ages = []
    for k in range(1, lifts + 1):
        poured = (k - lifts) / J["lifts_per_day"]
        reached = start + (k - 1) * silo["concrete_lift_m"] / c["water_rise_m_per_day"]
        ages.append(reached - poured)
    c["wet_age_min"] = min(ages)
    c["full_head_age"] = BY_KEY["water"]["end"] + (lifts - 1) / J["lifts_per_day"]
    # Liner sprayed on the faces of the store before it is filled
    coat = cfg.PROJECT["coating"]
    r_out, r_in = cfg.OUTSIDE_R - silo["outer_wall_m"], cfg.BORE_R + silo["inner_wall_m"]
    c["coat_wall_m2"] = 2 * math.pi * (r_out + r_in) * silo["height_m"]
    c["coat_floor_m2"] = math.pi * (r_out**2 - r_in**2)
    c["coat_m2"] = c["coat_wall_m2"] + c["coat_floor_m2"]
    c["coat_m3"] = c["coat_m2"] * coat["thickness_mm"] / 1000
    c["coat_m2_per_day"] = coat["sprayers"] * coat["m2_per_sprayer_hour"] * HOURS
    c["coat_days_needed"] = c["coat_m2"] / c["coat_m2_per_day"]
    c["coat_age_min"] = BY_KEY["coating"]["start"]
    # Coolers and their frames
    k = L["coolers"]
    c["cooler_load_t"] = k["cooler_mass_t"] + k["pump_unit_mass_t"]
    c["cooler_trucks"] = cfg.COOLERS
    c["frame_trucks"] = cfg.FRAMES
    c["cooler_load_height"] = flat["deck_height_m"] + co["cooler_section_m"]
    _, _, days = span("frames")
    c["cooler_trucks_per_day"] = (c["cooler_trucks"] + c["frame_trucks"]) / days
    c["cooler_lifts_per_day"] = HOURS * 60 / k["lift_minutes_per_cooler"]
    # Fuel
    radius = fu["tank_diameter_m"] / 2
    each = math.pi * radius**2 * (fu["tank_length_m"] - 2 * radius) + 4 / 3 * math.pi * radius**3
    c["propane_m3"] = each * fu["tanks"] * fu["fill_fraction"]
    p = L["propane"]
    c["propane_loads"] = math.ceil(c["propane_m3"] / p["transport_load_m3"])
    c["propane_load_t"] = p["transport_load_m3"] * fu["liquid_density_kg_m3"] / 1000
    c["tank_hauls"] = fu["tanks"]
    c["diesel_m3"] = math.pi * (di["bulk_tank_diameter_m"] / 2)**2 * di["bulk_tank_length_m"] * di["bulk_fill_fraction"]
    c["diesel_loads"] = math.ceil(c["diesel_m3"] / L["diesel"]["tanker_load_m3"])
    _, _, days = span("propane")
    c["propane_per_day"] = (c["propane_loads"] + c["diesel_loads"]) / days
    c["propane_bay_per_day"] = HOURS * 60 / p["unload_minutes"]
    c["propane_capacity_per_day"] = p["bays"] * c["propane_bay_per_day"]
    _, _, days = span("tanks")
    c["tanks_per_day"] = (fu["tanks"] + 1) / days
    # Concrete
    k = L["concrete"]
    ro, ri = cfg.OUTSIDE_R, cfg.BORE_R
    ring = math.pi * (ro**2 - (ro - silo["outer_wall_m"])**2) + math.pi * ((ri + silo["inner_wall_m"])**2 - ri**2)
    c["lifts"] = lifts
    c["wall_m3"] = ring * silo["height_m"]
    c["lift_m3"] = ring * silo["concrete_lift_m"]
    c["lift_trucks"] = math.ceil(c["lift_m3"] / k["mixer_load_m3"])
    c["wall_trucks"] = c["lift_trucks"] * lifts
    c["lift_pour_h"] = c["lift_m3"] / k["pump_m3_per_hour"]
    c["mixer_headway_min"] = c["lift_pour_h"] * 60 / c["lift_trucks"]
    c["slab_m3"] = math.pi * (ro + k["slab_overhang_m"])**2 * k["slab_thickness_m"]
    c["slab_trucks"] = math.ceil(c["slab_m3"] / k["mixer_load_m3"])
    c["rebar_t"] = (c["wall_m3"] + c["slab_m3"]) * k["reinforcement_kg_per_m3"] / 1000
    c["rebar_trucks"] = math.ceil(c["rebar_t"] / flat["payload_t"])
    c["wall_days"] = lifts / J["lifts_per_day"]
    c["crew"] = sum(count for _, count in J["crew"])
    # Pod cage, built a level a day beside the silo while the walls go up
    cage = L["cage"]
    c["cage_modules"] = cfg.LEVELS + 1
    c["cage_trucks"] = c["cage_modules"] * cage["trucks_per_level"]
    # Power plant
    c["turbine_hauls"] = pw["modules"]
    c["diesel_set_trucks"] = di["sets"]
    # Totals by programme activity: (activity, what, loads, vehicle)
    c["loads"] = [
        ("walls", "Concrete for the walls", c["wall_trucks"], f"{k['mixer_load_m3']:g} m³ mixer"),
        ("cagebuild", "Pod cage steel", c["cage_trucks"], f"flatbed, {cage['trucks_per_level']} a level"),
        ("frames", "Dry coolers with their pump units", c["cooler_trucks"], "flatbed, one each"),
        ("frames", "Cooler frame steel", c["frame_trucks"], "flatbed, one frame each"),
        ("water", "Water-glycol", c["water_loads"], f"{w['tanker_payload_t']:g} t tanker"),
        ("pods", f"{cfg.NAME} pods", c["pod_trucks"], f"flatbed, {c['pods_per_truck']} each"),
        ("tanks", "Propane tanks and the diesel tank", fu["tanks"] + 1, "oversize load, one each"),
        ("propane", "Propane", c["propane_loads"], f"{p['transport_load_m3']:g} m³ transport"),
        ("propane", "Diesel", c["diesel_loads"], f"{L['diesel']['tanker_load_m3']:g} m³ tanker"),
        ("fabricate", "Turbine generator sets", pw["modules"], f"heavy haul, {pw['set_weight_t']:g} t each"),
        ("fabricate", "Diesel sets", di["sets"], f"lowboy, {di['set_weight_t']:g} t each"),
        ("fabricate", "Deck steel for the power levels", math.ceil(2 * L["power_fabrication"]["deck_steel_t"] / flat["payload_t"]), "flatbed"),
    ]
    c["loads_after_pour"] = sum(n for key, _, n, _ in c["loads"] if key not in ("walls", "cagebuild"))
    # Loads per day through the programme
    per_day = {}
    for key, _, count, _ in c["loads"]:
        a, b, days = span(key)
        for day in range(a, b + 1):
            per_day[day] = per_day.get(day, 0) + count / days
    c["per_day"] = per_day
    c["peak_day"] = max((d for d in per_day if d > 0), key=lambda d: per_day[d])
    c["peak_loads"] = per_day[c["peak_day"]]
    return c


C = compute()


def check():
    for a in ACTIVITIES:
        if a["end"] < a["start"] or a["end"] > DAYS:
            raise ValueError(f"'{a['name']}' must start before it ends and finish by day {DAYS}.")
    if BY_KEY["pods"]["start"] <= BY_KEY["cage"]["end"] or BY_KEY["power"]["start"] <= BY_KEY["pods"]["end"]:
        raise ValueError("The pods follow the cage, and the power levels follow the pods.")
    if BY_KEY["coating"]["end"] >= BY_KEY["water"]["start"] or C["coat_days_needed"] > span("coating")[2] + 1e-9:
        raise ValueError("The store is coated before it is filled, and the sprayers need enough days to cover it.")
    if BY_KEY["water"]["end"] != DAYS or BY_KEY["fabricate"]["end"] >= BY_KEY["power"]["start"]:
        raise ValueError("The fill runs to the last day, and the power levels are fabricated before they are lifted.")
    if BY_KEY["hang"]["end"] >= BY_KEY["power"]["start"] or BY_KEY["propane"]["start"] <= BY_KEY["tanks"]["end"]:
        raise ValueError("One crane hangs the frames before it lifts the power levels, and the tanks are set before they are filled.")
    if C["hoist_per_day"] < C["pods_per_day"] or C["dock_trucks_per_day"] < C["pod_trucks_per_day"]:
        raise ValueError("The hoist or the receiving dock cannot keep up with the pod programme. Allow more days or more lanes.")
    if C["water_capacity_per_day"] < C["water_per_day"]:
        raise ValueError("The water bays cannot unload the tankers in the days allowed. Add a bay or allow more days.")
    if C["propane_capacity_per_day"] < C["propane_per_day"]:
        raise ValueError("The fuel unloading bays cannot keep up. Add a bay or allow more days.")
    if C["cooler_lifts_per_day"] < cfg.COOLERS / span("frames")[2]:
        raise ValueError("One assist crane cannot place the coolers in the days allowed.")


check()


def days_text(key):
    a, b, _ = span(key)
    return f"Day {a}" if a == b else f"Days {a} to {b}"


def gantt():
    """Rows for the programme chart: name, first day, last day."""
    return [(a["name"].replace("Pods", cfg.NAME + " pods"), a["start"], a["end"]) for a in ACTIVITIES]
