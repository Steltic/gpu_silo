"""Where the film is in the 28-day programme, and the truck counts shown with each scene.

Each tag is (first frame, last frame, days, title, note, counters). A note may hold {a} and {b},
which the renderer replaces with the running counts named in `counters`.
"""
from . import clock
from . import closing
from . import design as cfg
from . import logistics

COUNTERS = ("concrete", "water", "coolers", "pod_trucks", "pods_landed", "propane")
LG = logistics.C


def days(*keys):
    first = min(logistics.BY_KEY[k]["start"] for k in keys)
    last = max(logistics.BY_KEY[k]["end"] for k in keys)
    return f"DAY {first}" if first == last else f"DAYS {first} TO {last}"


def rig_card():
    from . import plant
    return ("SHAFT SUPPORT","Top support rig","Bare steel before pod loading",
            [("Wall mounts",str(plant.RIG["wall_mounts"])),("Collar arms",str(plant.RIG["arms"])),
             ("Diesel sets",f"Day {logistics.BY_KEY['power']['start']} onward")],
            [(clock.CAGE_END,"Rig the bare steel"),(clock.RIG_PICK+55,"Slew over the shaft"),
             (clock.RIG_PICK+91,"Lower onto the mounts"),(clock.RIG_PICK+plant.PICK_LENGTH,"Shaft braced")])


def tags(p):
    full = p.FILLED
    care = p.care
    water = f"Tankers {{a}} / {LG['water_loads']}"
    rows = [
        (0, p.C, days("walls"), f"Jumpform the walls, {cfg.PROJECT['jumpform']['lifts_per_day']:g} lift a day",
         f"Mixers {{a}} / {LG['wall_trucks']}, {LG['lift_trucks']} a lift", ("concrete",)),
        (p.C, clock.CAGE_END, days("cage"), "Lift in the pod cage", water + f", coolers {{b}} / {cfg.COOLERS}", ("water", "coolers")),
        (clock.CAGE_END,clock.STORE_FILL[0],days("rig"),"Set the top support rig","Seat the collar and weld the shoes to the wall plates",()),
        (clock.STORE_FILL[0], clock.DELIVERY_AT, days("water"), "Water-glycol fill",
         water + f", {LG['water_per_day']:.0f} a day through {cfg.PROJECT['logistics']['water']['bays']} bays", ("water",)),
        (clock.DELIVERY_AT, p.FIRST_POD, f"DAY {logistics.BY_KEY['pods']['start']}", "First pods at the receiving dock",
         f"{LG['pods_per_truck']} pods a truck: {LG['pod_load_t']:.1f} t of {cfg.PROJECT['logistics']['flatbed']['payload_t']:g} t allowed", ()),
        (p.FIRST_POD, full, days("pods", "hang"), "Pods loaded, cooler frames hung",
         f"Pod trucks {{a}} / {LG['pod_trucks']}, coolers {{b}} / {cfg.COOLERS}", ("pod_trucks", "coolers")),
        (full, full + care.CREW, days("power"), "Power levels and lid", "One crane for every lift", ()),
        (full + care.CREW, full + care.SOLID_BEGIN, "IN SERVICE", "Access for maintenance", "", ()),
        (full + care.SOLID_BEGIN, full + closing.FUEL, f"DAY {logistics.DAYS}", "Concrete at full strength, the crew leaves", "", ()),
        (full + closing.FUEL, full + closing.PLAN, days("tanks", "propane"), "Fuel tanks set and filled",
         f"Propane loads {{a}} / {LG['propane_loads']} through {cfg.PROJECT['logistics']['propane']['bays']} bays", ("propane",)),
        (full + care.REPAIR, full + closing.FINAL[0], "IN SERVICE", "Pod and cooler replacement", "", ()),
    ]
    return [(a, b, day, cfg.display(title), cfg.display(note), tuple(COUNTERS.index(c) for c in which)) for a, b, day, title, note, which in rows]
