"""Detail of the jumpform and the crew that works it.

silo_model.py builds the form panels and moves them. This module adds what climbs with them:
the pour decks, the hung trailing platforms, the climbing rails and jacks, the starter bars,
a placing boom on a centre mast, and a typical crew that changes task with each step of the cycle.
Heights are measured from the foot of the form panels.
"""
import math

from . import crew as people
from . import design as cfg
from . import services
from . import silo_model as s

CREW = cfg.PROJECT["jumpform"]["crew"]
MAIN = .27                 # the working platform already on the panels
POUR = s.LIFT - 1.06       # pour deck, a rail height below the top of the form
TRAIL = -2.26              # trailing platform, hung below for patching and anchor recovery
OUTER_OPEN = (255., 345.)  # bearings left open in the film so the walls can be seen in section
INNER_OPEN = (285., 330.)
FULL_RING = (360., 360.)
DECK, RAIL, STEEL, JACK, BAR = "8f8064", "e2bd76", "566b64", "c8563c", "7a5a45"
MAST_TOP = 3.4
REACH = (s.RO_INNER + s.RI_OUTER) / 2
ON, OFF = (1., 1., 1.), (0., 0., 0.)


def arc(m, inner, outer, z0, z1, open_span, colour, n=44):
    """A ring over every bearing except the open span."""
    start, end = math.radians(open_span[1] - 360), math.radians(open_span[0])
    s.sector(m, inner, outer, z0, z1, start, end, n, [colour] * 4)


def bearings(open_span, step):
    first, last = open_span[1] - 360, open_span[0]
    count = round((last - first) / step)
    return [math.radians(first + (last - first) * k / count) for k in range(count + 1)]


def handrail(m, radius, z, open_span, step=7.5):
    marks = bearings(open_span, step)
    for a in marks:
        s.bar(m, s.polar(radius, a, z), s.polar(radius, a, z + 1.1), .05, RAIL)
    for a, b in zip(marks, marks[1:]):
        for h in (.55, 1.08):
            s.bar(m, s.polar(radius, a, z + h), s.polar(radius, b, z + h), .04, RAIL)


def climbing_mesh(outer=OUTER_OPEN, inner=INNER_OPEN):
    m = s.Mesh("Jumpform | pour decks, climbing rails, jacks and ladders")
    m.material = 3
    # Pour decks outside the outer wall, inside the inner wall and across the gap between them.
    arc(m, s.RO + .13, s.RO + 1.18, POUR - .08, POUR, outer, DECK)
    arc(m, s.RI - .95, s.RI - .13, POUR - .08, POUR, inner, DECK, n=30)
    arc(m, s.RO_INNER + .13, s.RI_OUTER - .13, POUR - .08, POUR, outer, "9a8a6c")
    handrail(m, s.RO + 1.12, POUR, outer)
    handrail(m, s.RI - .89, POUR, inner, 10)
    # Brackets under the decks, climbing rails anchored to the lift below and a jack on each rail.
    for radius, sense, span, step in ((s.RO, 1, outer, 15.), (s.RI, -1, inner, 15.)):
        for a in bearings(span, step):
            s.bar(m, s.polar(radius + sense * .2, a, POUR - 1.15), s.polar(radius + sense * 1.08, a, POUR - .1), .07, STEEL)
            s.bar(m, s.polar(radius + sense * .24, a, TRAIL - .2), s.polar(radius + sense * .24, a, s.LIFT + .45), .13, "465a5e", .11)
            s.bar(m, s.polar(radius + sense * .40, a, .45), s.polar(radius + sense * .40, a, 1.55), .12, JACK)
            s.bar(m, s.polar(radius + sense * .17, a, -.55), s.polar(radius + sense * .32, a, -.55), .22, "d4af6b", .22)
    # Beams carry the gap deck between the two inner form faces.
    for a in bearings(outer, 15.):
        s.bar(m, s.polar(s.RO_INNER + .1, a, POUR - .16), s.polar(s.RI_OUTER - .1, a, POUR - .16), .10, STEEL, .14)
    # Ladders from the working platform to the pour deck.
    for degrees in (10., 242.):
        a = math.radians(degrees)
        for side in (-.22, .22):
            b = a + side / (s.RO + .9)
            s.bar(m, s.polar(s.RO + .98, b, MAIN), s.polar(s.RO + .78, b, POUR + .9), .045, RAIL)
        for k in range(8):
            z = MAIN + .3 + k * (POUR - MAIN) / 8
            r = s.RO + .98 - .2 * (z - MAIN) / (POUR + .9 - MAIN)
            s.bar(m, s.polar(r, a - .22 / (s.RO + .9), z), s.polar(r, a + .22 / (s.RO + .9), z), .035, RAIL)
    return m


def trailing_mesh(outer=OUTER_OPEN, inner=INNER_OPEN):
    m = s.Mesh("Jumpform | trailing platforms hung below the forms")
    m.material = 3
    arc(m, s.RO + .13, s.RO + .98, TRAIL - .07, TRAIL, outer, DECK)
    arc(m, s.RI - .80, s.RI - .13, TRAIL - .07, TRAIL, inner, DECK, n=30)
    handrail(m, s.RO + .93, TRAIL, outer, 15)
    handrail(m, s.RI - .75, TRAIL, inner, 15)
    for radius, sense, span in ((s.RO, 1, outer), (s.RI, -1, inner)):
        for a in bearings(span, 15.):
            s.bar(m, s.polar(radius + sense * .9, a, TRAIL), s.polar(radius + sense * .9, a, MAIN - .1), .05, STEEL)
    return m


def rebar_mesh(outer_span=OUTER_OPEN, inner_span=INNER_OPEN):
    m = s.Mesh("Jumpform | starter bars and hoops above the pour")
    m.material = 3
    for inner, outer, span in ((s.RI_OUTER, s.RO, outer_span), (s.RI, s.RO_INNER, inner_span)):
        for layer in (inner + .06, outer - .06):
            count = round((span[0] - span[1] + 360) / 360 * s.TAU * layer / .7)
            first, last = math.radians(span[1] - 360), math.radians(span[0])
            for k in range(count + 1):
                a = first + (last - first) * k / count
                s.bar(m, s.polar(layer, a, s.LIFT - .25), s.polar(layer, a, s.LIFT + 1.75 + .12 * (k % 2)), .035, BAR)
            for z in (s.LIFT + .35, s.LIFT + .95, s.LIFT + 1.5):
                arc(m, layer - .018, layer + .018, z - .018, z + .018, span, BAR, n=40)
    return m


def mast_mesh():
    """One metre of lattice mast on the silo axis. The node is scaled to the height of the forms."""
    m = s.Mesh("Placing boom | one metre of centre mast")
    m.material = 3
    half = .55
    corners = [(-half, -half), (half, -half), (half, half), (-half, half)]
    for x, y in corners:
        s.bar(m, (x, y, 0), (x, y, 1), .11, "d7a84c")
    return m


def mast_bracing():
    m = s.Mesh("Placing boom | mast head and slewing ring")
    m.material = 3
    s.box(m, -.75, -.75, .75, .75, -.25, 0, "8a5a3c")
    services.pipe(m, (0, 0, 0), (0, 0, .35), .62, "59646a", n=12)
    return m


def boom_mesh():
    m = s.Mesh("Placing boom | slewing arm, delivery line and drop hose")
    m.material = 3
    s.bar(m, (-2.6, 0, .55), (REACH * .52, 0, .9), .34, "d7a84c", .5)
    s.bar(m, (REACH * .5, 0, .9), (REACH, 0, .55), .26, "e2bb6b", .36)
    s.box(m, -3.3, -.5, -2.3, .5, .1, 1.1, "59646a")
    services.pipe(m, (0, 0, 1.0), (REACH * .52, 0, 1.22), .07, "59646a", n=6)
    services.pipe(m, (REACH * .52, 0, 1.22), (REACH, 0, .82), .07, "59646a", n=6)
    services.pipe(m, (REACH, 0, .82), (REACH, 0, POUR + 1.2 - s.LIFT - MAST_TOP), .085, "30383a", n=6)
    return m


def boom_angle(frame):
    """The boom makes one turn round the walls for each pour."""
    k, fill, *_ = s.sequence(min(frame, s.FRAMES - 1))
    return math.radians(20) + s.TAU * (k + fill)


# Each station: role, deck, radius, bearing in degrees, way faced (1 looks away from the axis), what is done in each step.
WORK, WATCH, WALK = "inspect", "stand", "walk"
STEPS = {"Forms in position": "ready", "Pour both walls": "pour", "Concrete sets": "set", "Strip the forms": "strip",
         "Jump the forms": "jump", "Reset for next pour": "reset", "Walls complete": "done"}
TASKS = {
    "Foreman": dict(),
    "Concrete placer": dict(pour=WORK),
    "Finisher": dict(pour=WORK, set=WORK),
    "Ironworker": dict(ready=WORK, set=WORK, strip=WORK, reset=WORK),
    "Form carpenter": dict(pour=WALK, set=WALK, strip=WORK, reset=WORK),
    "Jack operator": dict(jump=WORK),
    "Pump operator": dict(pour=WORK),
}
GAP_IN, GAP_OUT = REACH - .95, REACH + .95


def stations():
    out = s.RO + .70; inside = s.RI - .55
    rows = [("Foreman", POUR, out, 246., -1)]
    rows += [("Concrete placer", POUR, r, b, f) for r, b, f in ((GAP_OUT, 5., 1), (GAP_IN, 28., -1), (GAP_IN, 228., -1), (GAP_OUT, 248., 1))]
    rows += [("Finisher", POUR, r, b, f) for r, b, f in ((GAP_IN, 15., -1), (GAP_OUT, 238., 1))]
    rows += [("Ironworker", POUR, out, b, -1) for b in (0., 22., 236.)]
    rows += [("Ironworker", POUR, inside, b, 1) for b in (345., 268., 100.)]
    rows += [("Form carpenter", MAIN, s.RO + .62, b, -1) for b in (8., 32., 240.)]
    rows += [("Form carpenter", MAIN, s.RI - .45, b, 1) for b in (350., 275., 130.)]
    rows += [("Jack operator", MAIN, s.RO + .62, b, -1) for b in (20., 228.)]
    counts = {}
    for role, *_ in rows: counts[role] = counts.get(role, 0) + 1
    for role, count in counts.items():
        listed = next((c for name, c in CREW if name.lower().startswith(role.lower())), None)
        if listed != count:
            raise ValueError(f"The film shows {count} of '{role}' and jumpform.crew lists {listed}.")
    return rows


def install(scene, node, p):
    frames = s.FRAMES
    states = [s.sequence(i) for i in range(frames)]
    ends = s.FORMS_OFF
    rise = [(0, 0, s.LIFT * (k + jump)) for k, _, _, jump, _ in states]
    seen = [(0, ON), (ends - .02, ON), (ends, OFF)]
    climb = node("Jumpform | climbing assembly", -1, "Jumpform", tracks={"translation": s.keys(rise), "scale": seen})
    def ring_detail(name, make, first, last):
        close=scene.wall_close_frame
        for begin,end,outer,inner,suffix in (
                (first,min(close,last),OUTER_OPEN,INNER_OPEN,""),
                (max(first,close),last,FULL_RING,FULL_RING," | full ring")):
            if begin>=end:continue
            scale=[(0,OFF),(begin-.02,OFF),(begin,ON)] if begin else [(0,ON)]
            if end<ends:scale.extend([(end-.02,ON),(end,OFF)])
            node(name+suffix,scene.mesh(make(outer,inner)),"Jumpform",climb,tracks={"scale":scale})
    ring_detail("Jumpform | decks, rails and jacks",climbing_mesh,0,ends)
    first_jump = next(i for i, state in enumerate(states) if state[0] >= 1)
    ring_detail("Jumpform | trailing platforms",trailing_mesh,first_jump,ends)
    last_lift = next(i for i, state in enumerate(states) if state[0] == s.COUNT - 1)
    ring_detail("Jumpform | starter bars",rebar_mesh,0,last_lift)
    # Placing boom on a mast at the silo axis. The pump line comes in through the ground opening.
    node("Placing boom | centre mast", scene.mesh(mast_mesh()), "Jumpform",
         tracks={"scale": s.keys([(1, 1, rise[i][2] + s.LIFT + MAST_TOP) for i in range(ends)]) + [(ends, OFF)]})
    head = node("Placing boom | mast head", scene.mesh(mast_bracing()), "Jumpform", climb, t=(0, 0, s.LIFT + MAST_TOP))
    node("Placing boom | slewing arm", scene.mesh(boom_mesh()), "Jumpform", head,
         tracks={"yaw": s.keys([(boom_angle(i),) for i in range(frames)])})
    # The crew ride the forms. Each person keeps a station and changes task with the step of the cycle.
    poses = {}

    def pose(style, mode, index):
        key = (style, mode, index)
        if key not in poses: poses[key] = scene.mesh(people.technician(*key))
        return poses[key]
    steps = [STEPS[state[4]] for state in states]
    listing = stations()
    for n, (role, deck, radius, bearing, facing) in enumerate(listing):
        tasks = TASKS[role]; base = math.radians(bearing)
        sway = math.radians(5.5) * (1 if n % 2 else -1)
        places, turns, modes = [], [], []
        for f in range(frames):
            mode = tasks.get(steps[f], WATCH)
            a = base
            if role == "Form carpenter":
                # Walk the platform during the pour and come back to the panel for stripping.
                start = max(i for i in range(f + 1) if i == 0 or steps[i] != steps[i - 1])
                if steps[f] == "pour": a = base + sway * s.step(start, start + 14, f)
                elif steps[f] == "set": a = base + sway * (1 - s.step(start, start + 5, f))
                moving = mode == WALK and abs(a - (base + sway if steps[f] == "pour" else base)) > 1e-4
                if not moving and mode == WALK: mode = WATCH
            places.append(s.polar(radius, a, deck))
            if mode == WALK:
                going = sway if steps[f] == "pour" else -sway
                turns.append(a + math.pi / 2 * (1 if going > 0 else -1))
            else: turns.append(a + (0 if facing > 0 else math.pi))
            modes.append((mode, 0 if mode == WATCH else (f // 3 + n) % people.MODES[mode]))
        label = f"Jumpform crew | {role.lower()} {n+1:02}"
        actor = node(label, -1, "Jumpform crew", climb, tracks={"translation": s.keys(places), "yaw": s.keys([(v,) for v in turns])})
        style = n % 3
        for spec in dict.fromkeys(modes):
            keys = [(0, ON if modes[0] == spec else OFF)]
            for f in range(1, ends + 1):
                was, now = modes[f - 1] == spec, modes[f] == spec
                if was != now: keys.extend([(f - .025, ON if was else OFF), (f, ON if now else OFF)])
            node(label + f" | {spec[0]} {spec[1]+1}", pose(style, *spec), "Jumpform crew poses", actor, tracks={"scale": keys})
    # The pump operator stays on the ground at the hopper.
    at = (18.9, -2.9)
    c, d = math.cos(s.ENTRY), math.sin(s.ENTRY)
    spot = (at[0] * c - at[1] * d, at[0] * d + at[1] * c, 0.)
    actor = node("Jumpform crew | pump operator", -1, "Jumpform crew", ang=s.ENTRY + math.pi / 2, t=spot, tracks={"scale": seen})
    working = [steps[f] == "pour" for f in range(frames)]
    for index in range(people.MODES[WORK]):
        keys = [(0, OFF)]
        for f in range(1, ends + 1):
            was = working[f - 1] and (f - 1) // 3 % people.MODES[WORK] == index
            now = working[f] and f // 3 % people.MODES[WORK] == index
            if was != now: keys.extend([(f - .025, ON if was else OFF), (f, ON if now else OFF)])
        node(f"Jumpform crew | pump operator | inspect {index+1}", pose(1, WORK, index), "Jumpform crew poses", actor, tracks={"scale": keys})
    keys = [(0, ON)]
    for f in range(1, ends + 1):
        if working[f] != working[f - 1]: keys.extend([(f - .025, OFF if working[f] else ON), (f, OFF if working[f] else ON)])
    node("Jumpform crew | pump operator | stand 1", pose(1, WATCH, 0), "Jumpform crew poses", actor, tracks={"scale": keys})
    scene.project_info.update(jumpformCrew=len(listing) + 1, jumpformCrewRoles={name: count for name, count in CREW})
