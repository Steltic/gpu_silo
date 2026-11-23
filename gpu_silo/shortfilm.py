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
from . import short_reels

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
    if frame < clock.CAGE_END: return blend(lift, install, smooth(t, 185, 307))
    if frame < yard.INSERT_AT: return plant.rig_camera(p,frame,install)
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
    office = cam(yard.coords(s.ENTRY, (30., -4.4, 2.4)), entry - 65, 10, 34)
    start = cam((0,0,18.6), -62, 8, 105.)
    if after < closing.RUN[1] - 12: return blend(lid, farm, smooth(after, clock.LINES, clock.LINES + 34))
    if after < closing.RISER[1] - 18: return blend(farm, wall, smooth(after, closing.RUN[1] - 12, closing.RISER[0] + 22))
    if after < closing.FUEL_END: return blend(wall, top, smooth(after, closing.RISER[1] - 18, closing.ROOF[1] + 4))
    if clock.DETAIL_START <= after < clock.SOLID_BEGIN: return short_reels.camera(p,frame)
    if after < clock.DETAIL_START: return blend(top, office, smooth(after, closing.FUEL_END, clock.OFFICE[0] + 8))
    if after < clock.ORBIT:
        from . import short_art
        antenna=cam((*short_art.DISH,plant.LID_Z+1.12),-87,48,3.05)
        return blend(antenna,start,smooth(after,clock.SOLID_END-4,clock.ORBIT-1))
    u = care.orbit_fraction(after)
    return cam((0,0,18.6), -62 + 360 * u, 8 + 3 * math.sin(math.pi * u)**2, 105.)


def cards(p):
    """Panels for the scenes the long film does not have: (kicker, heading, subheading, rows, steps)."""
    full = p.FILLED
    fab, coat = (tuple(p.FIRST_POD + f for f in span) for span in (film.FABRICATE_CUT, film.COATING_CUT))
    power, diesel, lc = cfg.POWER, cfg.PROJECT["diesel"], cfg.PROJECT["coating"]
    fabricate = ("SITE FABRICATION", "Power plant", "Diesels and turbine deck",
                 [("Turbine level", f"{power['modules']} × {power['module_output_mw']:g} MW"), ("Diesel level", f"{diesel['sets']} × {diesel['set_output_mw']:g} MW"),
                  ("One turbine set", f"{power['set_weight_t']:g} t"), ("One diesel set", f"{diesel['set_weight_t']:g} t"),
                  ("Deck steel, each", f"{cfg.PROJECT['logistics']['power_fabrication']['deck_steel_t']:g} t")],
                 [(fab[0], "Weld the turbine deck"), (fab[0] + 84, "Stage the diesel sets"), (fab[0] + 150, "Land the turbine sets")])
    coating = ("STORE LINER", "Spray coating", "Both faces of the store",
               [("System", "Polyurea liner"), ("Thickness", f"{lc['thickness_mm']:g} mm"), ("Area", f"{LG['coat_m2']:,.0f} m²"),
                ("Sprayers", f"{lc['sprayers']}"), ("Time", f"{LG['coat_days_needed']:.0f} days"), ("Concrete age", f"{LG['coat_age_min']}+ days")],
               [(coat[0], "Coat both wall faces"), (coat[1] - 26, "Liner complete")])
    office = ("SITE OPERATIONS", "Control room", "One receiving lane converted",
              [("Operators", "3 consoles"), ("Frontage", "Glazed"), ("Other lane", "Pod exchange"), ("Gantry", "Retained")],
              [(full+clock.OFFICE[0],"Fit out the operator lane"), (full+clock.OFFICE[0]+70,"Close in the roof")])
    cards=[fabricate,coating,office]
    for i,title in enumerate(short_reels.TITLES):
        start=full+clock.DETAIL_START+i*clock.DETAIL_LENGTH
        cards.append(("IFC4  /  COMPONENT DETAIL",title,short_reels.SUBS[i],short_reels.ROWS[i],
                      list(zip((start,start+58,start+clock.DETAIL_LENGTH-76),short_reels.STEPS[i]))))
    return cards


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
            (full + closing.FUEL_END, full + clock.DETAIL_START, CARD, 2), (full + clock.SOLID_BEGIN, p.FRAMES, DESIGN, 0)] + [
            (full+clock.DETAIL_START+i*clock.DETAIL_LENGTH,full+clock.DETAIL_START+(i+1)*clock.DETAIL_LENGTH,12,3+i) for i in range(4)]


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
        (p.C, clock.CAGE_END, days("cage"), "Lift in the pod cage", f"Coolers {{a}} / {cfg.COOLERS}", ("coolers",)),
        (clock.CAGE_END,yard.INSERT_AT,days("rig"),"Set the top support rig","Seat the collar and weld the shoes to the wall plates",()),
        (yard.INSERT_AT, p.FIRST_POD, f"DAY {logistics.BY_KEY['pods']['start']}", "First pods at the receiving dock",
         f"{LG['pods_per_truck']} pods a truck: {LG['pod_load_t']:.1f} t of {cfg.PROJECT['logistics']['flatbed']['payload_t']:g} t allowed", ()),
        (p.FIRST_POD, full, days("pods", "hang"), "Pods loaded, cooler frames hung",
         f"Pod trucks {{a}} / {LG['pod_trucks']}, coolers {{b}} / {cfg.COOLERS}", ("pod_trucks", "coolers")),
        (fuel[0], fuel[1], days("tanks"), "Fuel tanks set", f"Tanks on the pad {{a}} / {cfg.PROJECT['fuel']['tanks'] + 1}", ("tanks",)),
        (fab[0], fab[1], days("fabricate"), "Prepare the power plant", "Stage the diesels and assemble the turbine level", ()),
        (coat[0], coat[1], days("coating"), "Line both faces of the store", f"{LG['coat_m2']:,.0f} m² of bonded liner", ()),
        (full, full + clock.LINES, days("power"), "Power levels and lid lifted in. The fill begins.", tankers, ("water",)),
        (full + clock.LINES, full + closing.FUEL_END, days("propane", "lines"), "Propane fill and fuel lines",
         f"Propane loads {{a}} / {LG['propane_loads']}, water tankers {{b}} / {LG['water_loads']}", ("propane", "water")),
        (full + closing.FUEL_END, full + clock.DETAIL_START, days("office"), "One dock lane becomes the control room", tankers, ("water",)),
        (full + clock.DETAIL_START, full + clock.SOLID_BEGIN, "IFC4", "Installed component assemblies", "", ()),
        (full + clock.SOLID_BEGIN, full + closing.PLAN, f"DAY {logistics.DAYS}", "Store full, concrete at full strength, handed over", tankers, ("water",)),
    ]
    return [(a, b, day, cfg.display(title), cfg.display(note), tuple(COUNTERS.index(c) for c in which)) for a, b, day, title, note, which in rows]
