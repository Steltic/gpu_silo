"""The short film: the build only, cut in the order of the programme.

This module holds what differs from the long film: the camera, the list of scenes
that tells the renderer which panel to draw, the cards for the new scenes and the programme tags.
"""
import math

from . import clock
from . import closing
from . import design as cfg
from . import film
from . import logistics
from . import silo_model as s
from . import site

LG = logistics.C
# Panel kinds understood by the renderer.
STEEL, DOCK, STORAGE, COOLERS, FUEL, CARD, POWER, DESIGN = 1, 2, 3, 4, 5, 6, 8, 11
COUNTERS = ("concrete", "water", "coolers", "pod_trucks", "pods_landed", "propane", "cage", "tanks")


def cuts(p):
    """Film frames of the three cutaways from the pod loading."""
    return [tuple(p.FIRST_POD + f for f in span) for span in (film.FUEL_CUT, film.COATING_CUT, film.FABRICATE_CUT)]


def camera(frame, p):
    from . import cooler_frames as frames
    from . import fuel
    from . import maintenance as care
    from . import plant
    from . import yard
    cam, blend, smooth = p.camera, p.blend, p.smooth
    if frame < p.C:
        base = s.camera_at(frame)
        k, fill, _, jump, _ = s.sequence(frame)
        height = s.clamp((k + .65 * fill + .35 * jump) / s.COUNT)
        # Draw back and to the west to take in the cage going up beside the silo.
        wide = cam((-8.5, -7., base["target"][2] * .9 + 1.), -76, 15.5, 98 + 34 * height)
        weight = smooth(frame, s.INTRO + s.SLOW_CYCLE - 34, s.INTRO + s.SLOW_CYCLE + 40) * (1 - smooth(frame, s.LAST_POUR + 2, s.LAST_POUR + 46))
        return blend(base, wide, weight)
    t = frame - p.C
    lift = cam((-10, 0, 26.0), -65, 11.8, 130)
    if t < 58: return blend(s.camera_at(p.C - 1), lift, smooth(t, 0, 54))
    install = cam((-.8, 0, 17), -59, 19, 85)
    if frame < yard.INSERT_AT: return blend(lift, install, smooth(t, 185, 307))
    last = yard.INSERT_AT + yard.DELIVERY_FRAMES - 1
    if frame <= last: return yard.delivery_camera(frame, p)
    dock = yard.delivery_camera(last, p)
    if frame < p.FIRST_POD: return dock
    elapsed = frame - p.FIRST_POD
    close = cam((3.4, -2.1, 3.5), -110, 16, 36)
    if elapsed < 40: return blend(dock, close, smooth(elapsed, 0, 28))
    middle = cam((0, 0, 14.3), -55, 24, 62)
    if elapsed < 151: return blend(close, middle, smooth(elapsed, 44, 106))
    follow = p.frames_camera(frame)
    bearing = math.degrees(fuel.BEARING)
    farm = cam(s.polar(31, fuel.BEARING, 7), bearing + 40, 19, 150)
    if frame < p.FILLED:
        view = blend(middle, follow, smooth(elapsed, 151, 188))
        shots = (farm, cam((0, 0, 26.), -58, 47, 56), cam((-25., -2., 3.5), 196, 25, 60))
        for (a, b), shot in zip(cuts(p), shots):
            if a - 18 <= frame < b + 18:
                view = blend(view, shot, smooth(frame, a - 18, a) * (1 - smooth(frame, b, b + 18)))
        return view
    after = frame - p.FILLED
    if after < clock.LINES: return plant.camera_power(p, frame, follow, cam, blend)
    lid = plant.camera_power(p, p.FILLED + clock.LINES - 1, follow, cam, blend)
    wall = cam(s.polar(7, fuel.BEARING, 19), bearing + 32, 22, 96)
    top = cam((0, 0, 29.5), bearing + 26, 40, 64)
    entry = math.degrees(s.ENTRY)
    office = cam(yard.coords(s.ENTRY, (27., 0., 3.)), entry - 34, 21, 62)
    start = cam(care.EXTERIOR, -62, 15, 92.0)
    if after < closing.RUN[1] - 12: return blend(lid, farm, smooth(after, clock.LINES, clock.LINES + 34))
    if after < closing.RISER[1] - 18: return blend(farm, wall, smooth(after, closing.RUN[1] - 12, closing.RISER[0] + 22))
    if after < closing.FUEL_END: return blend(wall, top, smooth(after, closing.RISER[1] - 18, closing.ROOF[1] + 4))
    if after < clock.OFFICE[1] - 10: return blend(top, office, smooth(after, closing.FUEL_END, clock.OFFICE[0] + 6))
    if after < clock.ORBIT: return blend(office, start, smooth(after, clock.OFFICE[1] - 10, clock.ORBIT - 4))
    u = care.orbit_fraction(after)
    return cam(care.EXTERIOR, -62 + 360 * u, 15 + 6 * math.sin(math.pi * u)**2, 92.0)


def cards(p):
    """Panels for the scenes the long film does not have: (kicker, heading, subheading, rows, steps)."""
    full = p.FILLED
    fab, coat = (tuple(p.FIRST_POD + f for f in span) for span in (film.FABRICATE_CUT, film.COATING_CUT))
    power, diesel, lc = cfg.POWER, cfg.PROJECT["diesel"], cfg.PROJECT["coating"]
    fabricate = ("SITE FABRICATION", "Power levels", "Built on the ground",
                 [("Turbine level", f"{power['modules']} × {power['module_output_mw']:g} MW"), ("Diesel level", f"{diesel['sets']} × {diesel['set_output_mw']:g} MW"),
                  ("One turbine set", f"{power['set_weight_t']:g} t"), ("One diesel set", f"{diesel['set_weight_t']:g} t"),
                  ("Deck steel, each", f"{cfg.PROJECT['logistics']['power_fabrication']['deck_steel_t']:g} t")],
                 [(fab[0], "Weld the deck steel"), (fab[0] + 84, "Land the diesel sets"), (fab[0] + 150, "Land the turbine sets")])
    coating = ("STORE LINER", "Spray coating", "Both faces of the store",
               [("System", "Polyurea liner"), ("Thickness", f"{lc['thickness_mm']:g} mm"), ("Area", f"{LG['coat_m2']:,.0f} m²"),
                ("Sprayers", f"{lc['sprayers']}"), ("Time", f"{LG['coat_days_needed']:.0f} days"), ("Concrete age", f"{LG['coat_age_min']}+ days")],
               [(coat[0], "Stages rise up the gap"), (coat[1] - 26, "Liner complete")])
    office = ("RECEIVING DOCK", "Control office", "Dock roofed and walled",
              [("Use", "Control office"), ("Gantry", "Kept inside"), ("Pod rail", "Kept for exchanges"), ("Roof", "Flat")],
              [(full + clock.OFFICE[0], "Stand the wall panels"), (full + clock.OFFICE[0] + 70, "Lay the flat roof"), (full + clock.OFFICE[1] - 14, "Office closed in")])
    return [fabricate, coating, office]


def scenes(p):
    """(first frame, last frame, panel kind, card) in drawing order. A later entry replaces an earlier one."""
    from . import cooler_frames as frames
    from . import yard
    full = p.FILLED
    first = frames.times(0)
    fuel, coat, fab = cuts(p)
    return [(p.C, yard.INSERT_AT, STEEL, 0), (yard.INSERT_AT, p.FIRST_POD - 8, DOCK, 0), (p.FIRST_POD - 8, full, STORAGE, 0),
            (first[0], first[7], COOLERS, 0), (fuel[0], fuel[1], FUEL, 0), (fab[0], fab[1], CARD, 0), (coat[0], coat[1], CARD, 1),
            (full, full + clock.LINES, POWER, 0), (full + clock.LINES, full + closing.FUEL_END, FUEL, 0),
            (full + closing.FUEL_END, full + clock.SOLID_BEGIN, CARD, 2), (full + clock.SOLID_BEGIN, p.FRAMES, DESIGN, 0)]


def tags(p):
    from . import programme
    from . import yard
    days = programme.days
    full = p.FILLED
    fuel, coat, fab = cuts(p)
    tankers = f"Water tankers {{a}} / {LG['water_loads']}"
    lc = cfg.PROJECT["coating"]
    rows = [
        (0, p.C, days("walls"), "Jumpform the walls. The pod cage goes up beside them, a level a day.",
         f"Mixers {{a}} / {LG['wall_trucks']}, cage modules {{b}} / {LG['cage_modules']}", ("concrete", "cage")),
        (p.C, yard.INSERT_AT, days("cage"), "Lift in the pod cage", f"Coolers {{a}} / {cfg.COOLERS}", ("coolers",)),
        (yard.INSERT_AT, p.FIRST_POD, f"DAY {logistics.BY_KEY['pods']['start']}", "First pods at the receiving dock",
         f"{LG['pods_per_truck']} pods a truck: {LG['pod_load_t']:.1f} t of {cfg.PROJECT['logistics']['flatbed']['payload_t']:g} t allowed", ()),
        (p.FIRST_POD, full, days("pods", "hang"), "Pods loaded, cooler frames hung",
         f"Pod trucks {{a}} / {LG['pod_trucks']}, coolers {{b}} / {cfg.COOLERS}", ("pod_trucks", "coolers")),
        (fuel[0], fuel[1], days("tanks"), "Fuel tanks set", f"Tanks on the pad {{a}} / {cfg.PROJECT['fuel']['tanks'] + 1}", ("tanks",)),
        (fab[0], fab[1], days("fabricate"), "Power levels fabricated on site", "Deck steel welded, then the sets are landed", ()),
        (coat[0], coat[1], days("coating"), "Spray-coat the inside of the store", f"{LG['coat_m2']:,.0f} m² of liner from {lc['stages']} stages", ()),
        (full, full + clock.LINES, days("power"), "Power levels and lid lifted in. The fill begins.", tankers, ("water",)),
        (full + clock.LINES, full + closing.FUEL_END, days("propane", "lines"), "Propane fill and fuel lines",
         f"Propane loads {{a}} / {LG['propane_loads']}, water tankers {{b}} / {LG['water_loads']}", ("propane", "water")),
        (full + closing.FUEL_END, full + clock.SOLID_BEGIN, days("office"), "Dock enclosed as the control office", tankers, ("water",)),
        (full + clock.SOLID_BEGIN, full + closing.PLAN, f"DAY {logistics.DAYS}", "Store full, concrete at full strength, handed over", tankers, ("water",)),
    ]
    return [(a, b, day, cfg.display(title), cfg.display(note), tuple(COUNTERS.index(c) for c in which)) for a, b, day, title, note, which in rows]
