"""Shared, versioned design inputs and dimensions. Distances are in metres."""
import json
import math
import re
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "design" / "project.json"
with FILE.open(encoding="utf-8") as file:
    PROJECT = json.load(file)

CLUSTER = PROJECT["cluster"]
SILO = PROJECT["silo"]
POD = PROJECT["pod"]
STORE = PROJECT["storage"]
FLUID = PROJECT["thermal_store"]
COOL = PROJECT["dry_coolers"]
SITE = PROJECT["installation"]
POWER = PROJECT["power"]
SERVICE = PROJECT["service"]
MOVIE = PROJECT["movie"]
TITLE = PROJECT["project"]["name"]
NAME = POD["name"]
LEVELS, BAYS = STORE["levels"], STORE["bays"]
TOTAL = LEVELS * BAYS
RACKS = TOTAL * CLUSTER["racks_per_pod"]
BODY_LENGTH = POD["rack_housing_length_m"]
BODY_WIDTH = POD["body_width_m"]
BODY_HEIGHT = POD["body_height_m"]
FRAME_WIDTH = round(BODY_WIDTH + POD["frame_extra_width_m"], 8)
FRAME_HEIGHT = round(BODY_HEIGHT + POD["frame_extra_height_m"], 8)
DOOR_WIDTH = round(FRAME_WIDTH + 2 * POD["intake_clearance_each_side_m"], 8)
DOOR_HEIGHT = round(FRAME_HEIGHT + POD["intake_clearance_overhead_m"], 8)
SECTION = float(POD["cdu_pump_section_m"])
SECTIONS = {int(i): float(v) for i, v in POD["cdu_pump_section_m_by_unit"].items()}
OUTSIDE_R = SILO["outside_diameter_m"] / 2
BORE_R = SILO["inside_diameter_m"] / 2
WALL_GAP = round(OUTSIDE_R - BORE_R - SILO["outer_wall_m"] - SILO["inner_wall_m"], 8)
CROWN = STORE["crown_m"]
LIQUID_TOP = round(SILO["height_m"] - FLUID["freeboard_m"], 8)
FRAMES = COOL["frames"]
COOLERS = FRAMES * COOL["coolers_per_frame"]


def extension(unit):
    """Light-grey CDU and pump section at the wall end of a one-based unit."""
    return SECTIONS.get(unit, SECTION)


def length(unit):
    return BODY_LENGTH + extension(unit)


def display(text):
    return re.sub(r"\bpod(s?)\b", lambda match: NAME+("s" if match.group(1) else ""), text, flags=re.I)


def linear_rgb(value):
    channels = [int(value[i:i+2],16)/255 for i in (1,3,5)]
    return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels]


def check_inputs():
    if not NAME or not isinstance(NAME, str):
        raise ValueError("Give each pod a display name in pod.name.")
    if min(BODY_LENGTH, BODY_WIDTH, BODY_HEIGHT, STORE["pitch_m"], BORE_R) <= 0:
        raise ValueError("Body dimensions, tier pitch and the clear bore must be positive.")
    if WALL_GAP <= 0.5:
        raise ValueError("The two concrete skins leave no liquid gap. Check the inside and outside diameters.")
    if any(i < 1 or i > TOTAL+1 or not math.isfinite(v) or v < 0 for i,v in SECTIONS.items()) or SECTION < 0:
        raise ValueError("Each CDU and pump section needs a valid one-based unit number and a finite, nonnegative length.")
    if FRAME_HEIGHT + .074 >= STORE["pitch_m"]:
        raise ValueError("The frame and 74 mm service lift must clear the next tier. Increase the pitch or shorten the frame.")
    longest = BODY_LENGTH + max([SECTION, *SECTIONS.values()])
    if math.hypot(STORE["root_radius_m"] + longest, FRAME_WIDTH/2) >= BORE_R - .12:
        raise ValueError("The rotating pod reaches the perimeter steel. Increase the inside diameter or shorten the pod.")
    if len(SERVICE["wedge_destinations"]) != BAYS or len(SERVICE["crew_by_wedge"]) != BAYS:
        raise ValueError("Give each storage bay a crew size and a platform destination (0 = turbine level).")
    if not all(isinstance(size,int) and 0 <= size <= 3 for size in SERVICE["crew_by_wedge"]):
        raise ValueError("Each animated deck has three boarding positions. Use 0 to 3 technicians per wedge.")
    if LEVELS < 3 or BAYS < 3 or not 0 < STORE["packed_pitch_degrees"] < 360 / BAYS:
        raise ValueError("Use at least three tiers and bays for this sequence and a packed pitch smaller than the storage pitch.")
    if not 1 <= SERVICE["fault_level"] <= LEVELS or not 1 <= SERVICE["fault_bay"] <= BAYS:
        raise ValueError("The service exchange must select an installed level and bay.")
    if not all(0 <= d <= LEVELS for d in SERVICE["wedge_destinations"]):
        raise ValueError("Wedge destinations must lie inside the store.")
    tiers = COOL["tier_base_m"]
    if FRAMES % len(tiers) or FRAMES < 2:
        raise ValueError("Spread the cooler frames equally over the tiers.")
    per_tier = FRAMES // len(tiers)
    half = math.asin(min(1, COOL["frame_width_m"]/2 / (OUTSIDE_R + COOL["wall_standoff_m"])))
    if per_tier * 2 * half >= 2 * math.pi:
        raise ValueError("The frames on one tier overlap around the wall. Add a tier or narrow the frame.")
    ordered = sorted(tiers)
    if any(b - a < COOL["frame_height_m"] for a, b in zip(ordered, ordered[1:])):
        raise ValueError("Cooler tiers overlap vertically. Separate the tier bases by at least one frame height.")
    if ordered[0] < DOOR_HEIGHT + 2 or ordered[-1] + COOL["frame_height_m"] > SILO["height_m"] + 1e-6:
        raise ValueError("Keep the cooler frames above the ground entry and below the silo rim.")
    if COOL["cooler_length_m"] + COOL["pump_unit_length_m"] > COOL["frame_width_m"] + 1e-6:
        raise ValueError("A cooler and its pump unit must fit across the frame.")
    if COOL["cooler_section_m"] > COOL["frame_height_m"]/COOL["coolers_per_frame"] - .29 or COOL["cooler_section_m"] > COOL["frame_depth_m"] - .39:
        raise ValueError("Each cooler needs 0.3 m of frame steel above it and 0.4 m in depth. Enlarge the frame or reduce cooler_section_m.")
    heat = RACKS * CLUSTER["liquid_heat_per_rack_kw"] / 1000
    if not 1 <= COOL["duty_coolers"] <= COOLERS or COOL["duty_coolers"] * COOL["cooler_capacity_mw"] < heat - 1e-6:
        raise ValueError("duty_coolers must carry the liquid heat load and cannot exceed the coolers installed.")
    if POWER["modules"] != 2 or POWER["module_output_mw"] <= 0:
        raise ValueError("The model has two power modules, one above the other. Give each a positive output.")
    if POWER["modules"] * POWER["module_output_mw"] < heat - 1e-6:
        raise ValueError("The power modules generate less than the cluster's load.")
    diesel = PROJECT["diesel"]
    stack = CROWN + 2 * POWER["floor_structure_m"] + diesel["set_height_m"] + POWER["set_height_m"]
    if stack > SILO["height_m"] + .03:
        raise ValueError(f"The pod store and the two power levels reach {stack:.2f} m, above the lid. Reduce storage.pitch_m or crown_m, or raise the silo.")
    if math.hypot(POWER["set_length_m"]/2, POWER["aisle_m"]/2 + POWER["set_width_m"]) > BORE_R - .25:
        raise ValueError("Two turbine sets side by side do not fit in the bore with 0.25 m to the wall.")
    if diesel["sets"] > 4 or diesel["day_tanks"] > 2 or diesel["room_vents"] > 2:
        raise ValueError("The diesel level is laid out for up to four sets, two day tanks and two room vents.")
    if CROWN < STORE["lowest_berth_m"] + (LEVELS-1)*STORE["pitch_m"] + FRAME_HEIGHT + 1.5 - 1e-6:
        raise ValueError("Leave 1.5 m between the top pod and the crown for the hoist.")
    if not 0 <= SITE["first_frame"] < FRAMES:
        raise ValueError("installation.first_frame is a zero-based frame number.")
    if SITE["direction"] not in ("clockwise", "anticlockwise"):
        raise ValueError("installation.direction is 'clockwise' or 'anticlockwise', seen from above.")
    if any(not 1 <= int(k) <= FRAMES or abs(v) > 30 for k, v in SITE["laydown_offset_degrees_by_frame"].items()):
        raise ValueError("Laydown offsets are keyed by one-based frame number and stay within 30 degrees.")
    if not 1 <= SERVICE["cooler_service_frame"] <= FRAMES or not 1 <= SERVICE["cooler_service_row"] <= COOL["coolers_per_frame"]:
        raise ValueError("The cooler service must select an installed frame and one of its coolers.")
    fuel = PROJECT["fuel"]
    if fuel["tanks"] < 1 or min(fuel["tank_diameter_m"], fuel["tank_length_m"]) <= 0 or fuel["tank_length_m"] <= fuel["tank_diameter_m"]:
        raise ValueError("Fuel tanks are horizontal cylinders: give a positive count, diameter and a length greater than the diameter.")
    if fuel["tank_spacing_m"] < fuel["tank_diameter_m"] + .5 or fuel["distance_m"] < OUTSIDE_R + 25:
        raise ValueError("Leave 0.5 m between tanks and keep the tank farm at least 25 m from the silo wall.")
    if not 0 < fuel["fill_fraction"] <= .9 or not 0 < fuel["generation_efficiency"] < 1 or fuel["energy_mj_per_litre"] <= 0:
        raise ValueError("Use a fill fraction up to 0.9, an efficiency between 0 and 1 and a positive energy density.")
    if not 1 <= fuel["riser_behind_frame"] <= FRAMES or abs(fuel["riser_offset_m"]) >= COOL["frame_width_m"]/2:
        raise ValueError("The gas riser runs up the wall behind one cooler frame, inside its width.")
    if MOVIE["lower_tier_speed"] < 1 or any(int(n)!=n or n<=0 or n%2 for n in (MOVIE["width_px"],MOVIE["height_px"])):
        raise ValueError("Use a positive playback rate and positive, even video dimensions.")


check_inputs()
