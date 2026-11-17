"""The trucks on site: concrete, water, coolers and fuel. The pod trucks are in yard.py.

Each vehicle drives a route from site.py on the film's own frame clock. Only a sample of
the real loads is shown. The counters written for the panels scale to the full number.
"""
import math

from . import clock
from . import cooler_frames as fr
from . import design as cfg
from . import logistics
from . import site
from . import silo_model as s

LG = logistics.C
ROAD, YARD, SLOW = 40., 22., 7.     # metres a second on the public road, on site and when reversing
ENTRY_DEG = math.degrees(s.ENTRY)


def dock_lane(offset_y, front, radius=5.5):
    """Route out of a back-in bay beside the pod rail: the lane, the turn onto the ring and the way out.

    Returns the route and the distance along it at which a parked vehicle's front axle stands.
    """
    reach = math.sqrt(site.R_RUN**2 - offset_y**2)
    bearing = ENTRY_DEG + math.degrees(math.atan2(offset_y, reach))
    while bearing < site.JOIN[site.R_RUN]: bearing += 360
    points = [site.local(s.ENTRY, 14., offset_y), site.local(s.ENTRY, reach, offset_y)]
    points += site.lap(bearing, site.LEAVE[site.R_RUN]) + site.depart()
    path = site.Path(points, radius)
    return path, path.nearest(site.local(s.ENTRY, front, offset_y)), bearing


GATE_IN = (site.INBOUND[0][0], site.EAST_LANE - 10.)
GATE_OUT = (site.OUTBOUND[-1][0], site.EAST_LANE - 10.)


def come(trip, path, end, at, gate=GATE_IN, start=0.):
    """Arrive at distance `end` along a route at frame `at`: road speed to the gate, site speed after it."""
    turn = min(end, max(start, path.nearest(gate)))
    inside = site.frames_for(end - turn, YARD, (False, True))
    outside = site.frames_for(turn - start, ROAD, (False, False))
    if turn > start: trip.drive(path, start, turn, at - inside - outside, at - inside, (False, False))
    trip.drive(path, turn, end, at - inside, at, (turn <= start, True))
    return at - inside - outside


def go(trip, path, start, at, gate=GATE_OUT):
    """Pull away at frame `at` and leave by the public road."""
    turn = max(start, path.nearest(gate, after=start))
    inside = site.frames_for(turn - start, YARD, (True, False))
    trip.drive(path, start, turn, at, at + inside, (True, False))
    outside = site.frames_for(path.length - turn, ROAD, (False, False))
    trip.drive(path, turn, path.length, at + inside, at + inside + outside, (False, False))
    return at + inside + outside


def back_in(trip, lane, parked, bearing, behind, ready, holding=None, spawn=-site.FAR, waits=None, reverse=None):
    """Drive to the ring, pass the bay and reverse into it. `behind` is the vehicle's length behind its front axle.

    The vehicle is parked at frame `ready`. With a holding lane it waits there from frame `waits`.
    """
    past = bearing + math.degrees((9. + behind + 3.) / site.R_RUN)
    points = site.arrive(holding=holding, spawn=spawn) + site.lap(site.JOIN[site.R_RUN], past, tail=0) + [s.polar(site.R_RUN, math.radians(past), 0)[:2]]
    approach = site.Path(points)
    turn = lane.nearest(approach.points[-1], after=parked)
    if reverse is None: reverse = site.frames_for(turn - parked, SLOW)
    stopped = ready - reverse - 3
    if holding is None:
        come(trip, approach, approach.length, stopped)
    else:
        wait = approach.nearest(site.holding_stop(holding))
        onward = site.frames_for(approach.length - wait, YARD)
        called = stopped - onward
        come(trip, approach, wait, called - 60 if waits is None else min(waits, called - 4))
        trip.drive(approach, wait, approach.length, called, stopped)
    trip.drive(lane, turn, parked, stopped + 3, ready)
    return trip


def leave(trip, lane, parked, at):
    go(trip, lane, parked, at)
    return trip


# ---------------------------------------------------------------------------------------------
# Concrete for the jumpform
PUMP_X = (14.6, 19.2)
HOPPER_X = 20.3
MIXER_REAR = 3.3     # chute behind the rear bogie
MIXER_BAY_Y = 1.75
MIXER_FRONT = HOPPER_X + .3 + MIXER_REAR + site.MIXER_BASE
MIXER_BODY = site.MIXER_BASE + 2.4


def pours():
    """Film frames in which each lift is poured."""
    spans = []
    for k in range(s.COUNT):
        start = s.INTRO + (0 if k == 0 else s.SLOW_CYCLE + (k - 1) * s.FAST_CYCLE)
        cycle = s.SLOW_CYCLE if k == 0 else s.FAST_CYCLE
        spans.append((start + round(.01 * cycle), start + round(.42 * cycle)))
    return spans


def mixer_visits():
    """(bay, parked from, parked until) for each mixer shown."""
    spans = pours()
    first = spans[0]
    visits = [(0, first[0] - 9, first[0] + 24), (1, first[0] + 12, first[1] + 5)]
    for k, (a, b) in enumerate(spans[1:], 1):
        visits.append(((k + 1) % 2, a - 5, b + 7))
    return visits


def pump_mesh():
    m = site.steel("Concrete pump | trailer pump, hopper and line to the placing boom")
    x0, x1 = PUMP_X
    site.closed(m, x0, -1.0, x1, 1.0, .55, 1.75, "c98d45")
    site.closed(m, x0 + .3, -.8, x0 + 1.7, .8, 1.75, 2.25, "8a5a3c")
    for x in (x0 + 1.0, x1 - 1.2):
        site.axle(m, x, half=.95, radius=.42, width=.3)
    site.closed(m, x1, -1.9, HOPPER_X + .5, 1.9, .5, 1.25, "7b8582")
    site.closed(m, x1 + .12, -1.75, HOPPER_X + .38, 1.75, 1.25, 1.32, "a9aea4")
    # The delivery line runs through the ground opening to the foot of the mast.
    from . import services
    services.pipe(m, (x0, 0, .9), (s.RO + .4, 0, .35), .075, "59646a", n=6)
    services.pipe(m, (s.RO + .4, 0, .35), (.9, 0, .35), .075, "59646a", n=6)
    return m


def concrete(scene, node, fleet, p):
    lanes = [dock_lane(sign * MIXER_BAY_Y, MIXER_FRONT, 7.) for sign in (1, -1)]
    ends = s.LAST_POUR + s.REVEAL // 2
    node("Concrete pump at the ground opening", scene.mesh(pump_mesh()), "Concrete supply", ang=s.ENTRY, tracks={"scale": site.window(0, ends)})
    colours = ("c9c7ae", "b8894f", "8f9a96")
    for n, (bay, a, b) in enumerate(mixer_visits()):
        lane, parked, bearing = lanes[bay]
        trip = site.Trip()
        back_in(trip, lane, parked, bearing, MIXER_BODY, a, spawn=-230.)
        leave(trip, lane, parked, b)
        colour = colours[n % len(colours)]
        fleet.rigid(f"Truck mixer {n + 1:02}", trip, fleet.mesh(("mixer", colour), lambda: site.mixer(colour)), site.MIXER_BASE, group="Concrete supply")
    counts = []
    for f in range(p.FRAMES):
        k, fill, *_ = s.sequence(min(f, s.FRAMES - 1))
        counts.append(min(LG["wall_trucks"], math.ceil(LG["lift_trucks"] * (k + fill) - 1e-6)) if f >= s.INTRO else 0)
    return counts


# ---------------------------------------------------------------------------------------------
# Water-glycol tankers on their own drive
TANKER_BEHIND = site.STEER + site.TANKER_AXLE + 2.4
WATER_DWELL = 58
WATER_HEADWAY = 30


def water_route(bay):
    y = site.WATER_Y[bay]
    return site.Path([(-site.FAR, site.EAST_LANE), (site.WATER_IN, site.EAST_LANE), (site.WATER_IN, y), (site.WATER_OUT, y),
                      (site.WATER_OUT, site.EAST_LANE), (site.FAR, site.EAST_LANE)], 8.)


def water_visits(p):
    """(bay, connected from, connected until) for each tanker shown."""
    first = p.C - 12
    last = clock.STORE_FILL[1] - 8
    visits = []
    n = 0
    while first + n * WATER_HEADWAY + WATER_DWELL <= last:
        visits.append((n % site.WATER_BAYS, first + n * WATER_HEADWAY, first + n * WATER_HEADWAY + WATER_DWELL))
        n += 1
    return visits


def water(scene, node, fleet, p, level):
    routes = [water_route(b) for b in range(site.WATER_BAYS)]
    body = fleet.mesh("water tanker", lambda: site.tanker("Water tanker semi-trailer", "b9c4c2", 11.2, 2.0, "5f8f9a"))
    for n, (bay, a, b) in enumerate(water_visits(p)):
        route = routes[bay]
        stop = route.nearest((site.WATER_STOP, site.WATER_Y[bay]))
        trip = site.Trip()
        come(trip, route, stop, a, gate=(site.WATER_IN, site.EAST_LANE - 10.))
        go(trip, route, stop, b, gate=(site.WATER_OUT, site.EAST_LANE - 10.))
        fleet.rig(f"Water tanker {n + 1:02}", trip, body, site.TANKER_AXLE, group="Water delivery")
    top = cfg.LIQUID_TOP
    return [min(LG["water_loads"], math.ceil(LG["water_loads"] * level[f] / top - 1e-6)) for f in range(p.FRAMES)]


# ---------------------------------------------------------------------------------------------
# Dry coolers and frame steel to the laydown, with an assist crane that lifts each cooler into its frame
DECK_MID = site.DECK_FRONT - site.DECK_L / 2
RIG_BEHIND = site.STEER - DECK_MID + site.DECK_L / 2
LIFT = 22            # frames to lift one cooler from the truck into the frame
ERECT = 22
COOLER_X = (fr.COOL_X0 + fr.COOL_X1) / 2
GAP = math.radians(18)


def normal(bearing):
    """A bearing in degrees, counted round the ring from the junction."""
    value = math.degrees(bearing)
    while value < site.JOIN[site.R_STOP]: value += 360
    return value


def cooler_times(p):
    """For each frame in installation order: when its steel arrives and when each cooler is in place."""
    plan = {0: (p.C + 30, [p.C + 121, p.C + 181, p.C + 241]), fr.N - 1: (p.C + 205, [p.C + 316, p.C + 376, p.C + 436])}
    start, step = clock.DELIVERY_AT + 61, 54
    for i in range(1, fr.N - 1):
        done = [start + step * (3 * (i - 1) + n) for n in range(fr.ROWS)]
        plan[i] = (done[0] - LIFT - 84, done)
        if done[-1] > fr.times(i)[0] - 16:
            raise ValueError(f"Cooler frame {fr.ORDER[i]+1} is picked before its coolers arrive.")
    return plan


def stop_route(bearing):
    """A lap that pulls into the stopping lane beside a laydown position. Returns the route and the stop for the deck centre."""
    near_in = bearing - site.JOIN[site.R_RUN] < 44
    near_out = site.LEAVE[site.R_RUN] - bearing < 44
    first, last = site.JOIN[site.R_STOP if near_in else site.R_RUN], site.LEAVE[site.R_STOP if near_out else site.R_RUN]

    def radius(b):
        r = site.R_STOP
        if not near_in: r += (site.R_RUN - site.R_STOP) * (1 - s.step(bearing - 36, bearing - 24, b))
        if not near_out: r += (site.R_RUN - site.R_STOP) * s.step(bearing + 17, bearing + 29, b)
        return r
    count = math.ceil((last - first - 2 * site.TURN) / 3)
    marks = [first + site.TURN + (last - first - 2 * site.TURN) * k / count for k in range(count + 1)]
    points = site.arrive(site.R_STOP if near_in else site.R_RUN, spawn=-230.) + [s.polar(radius(b), math.radians(b), 0)[:2] for b in marks]
    points += site.depart(site.R_STOP if near_out else site.R_RUN)
    path = site.Path(points)
    return path, path.nearest(s.polar(site.R_STOP, math.radians(bearing), 0)[:2]) + site.STEER - DECK_MID


def crane_station(i):
    """Where the assist crane stands for a frame: in the gap beside it, clear of both ring lanes."""
    side = -1 if i in (0, fr.N - 2) else 1
    return fr.lay_bearing(i) + side * GAP


def bundle_mesh():
    m = site.steel("Cooler frame steel | bundled members for one frame")
    for k, (z, w) in enumerate(((0, 1.1), (.45, 1.0), (.9, .8))):
        site.closed(m, -6.2, -w, 6.2, w, z, z + .4, ("4c6266", "566b6f", "4c6266")[k])
    for x in (-4.5, 0, 4.5):
        site.closed(m, x - .06, -1.14, x + .06, 1.14, 0, 1.34, "d4af6b")
    return m


def coolers(scene, node, fleet, p):
    plan = cooler_times(p)
    flat = fleet.mesh("flatbed", site.flatbed)
    frames = scene.cooler_frames
    cooler_mesh = scene.nodes[frames[0]["coolers"][0]]["mesh"]
    pump_mesh = scene.nodes[frames[0]["pumps"][0]]["mesh"]
    bundle = scene.mesh(bundle_mesh())
    routes = {}
    arrivals = []
    lifts = []       # (begin, end, from, to) for the crane hook
    for i in range(fr.N):
        k = fr.ORDER[i]; info = frames[k]
        lay = fr.lay_bearing(i); bearing = normal(lay)
        if bearing not in routes: routes[bearing] = stop_route(bearing)
        route, stop = routes[bearing]
        steel_at, done = plan[i]
        # The frame steel arrives first and the frame is stood up on its dunnage.
        trip = site.Trip()
        come(trip, route, stop, steel_at); go(trip, route, stop, steel_at + 14)
        towed, _, _ = fleet.rig(f"Cooler frame {k+1:02} | steel delivery", trip, flat, site.FLAT_AXLE, group="Cooler delivery")
        node(f"Cooler frame {k+1:02} | steel on the truck", bundle, "Cooler delivery", towed, t=(DECK_MID, 0, site.DECK),
             tracks={"scale": site.window(0, steel_at + 8)})
        root = scene.nodes[info["root"]]
        grow = [(0, site.OFF), (steel_at + 7.98, site.OFF), (steel_at + 8, (1, 1, .03)), (steel_at + 8 + ERECT, site.ON)]
        root["tracks"]["scale"] = grow
        dunnage = scene.nodes[info["dunnage"]]
        dunnage["tracks"]["scale"] = [(0, site.OFF), (steel_at - 20.02, site.OFF), (steel_at - 20, site.ON)] + [x for x in dunnage["tracks"]["scale"] if x[0] > fr.START]
        scene.nodes[info["screen"]]["tracks"]["scale"] = [(0, site.OFF), (done[-1] + 5.98, site.OFF), (done[-1] + 6, site.ON)]
        base = s.polar(fr.LAY_R, lay, fr.GROUND)
        for row, at in enumerate(done):
            trip = site.Trip()
            come(trip, route, stop, at - LIFT - 8); go(trip, route, stop, at - LIFT + 10)
            towed, _, pose = fleet.rig(f"Cooler frame {k+1:02} | cooler {row+1} delivery", trip, flat, site.FLAT_AXLE, group="Cooler delivery")
            gone = at - LIFT
            for mesh_id, along, label in ((cooler_mesh, fr.COOL_Y, "dry cooler"), (pump_mesh, fr.PUMP_Y, "pump unit")):
                node(f"Cooler frame {k+1:02} | {label} {row+1} on the truck", mesh_id, "Cooler delivery", towed, ang=-math.pi / 2,
                     t=(DECK_MID + along, COOLER_X, site.DECK), tracks={"scale": site.window(0, gone)})
                (px, py, _), yaw = pose(gone)
                c, d = math.cos(yaw), math.sin(yaw)
                x, y = DECK_MID + along, COOLER_X
                start = (px + x * c - y * d, py + x * d + y * c, site.DECK); turn0 = yaw - math.pi / 2
                turn0 -= s.TAU * round((turn0 - lay) / s.TAU)
                cl, dl = math.cos(lay), math.sin(lay)
                z = fr.GROUND + row * fr.ROW + .15
                end = (base[0] - along * dl, base[1] + along * cl, z)
                high = max(site.DECK + .4, z + .35)
                values, turns = [], []
                for f in range(LIFT + 1):
                    u = f / LIFT; q = s.step(.22, .86, u)
                    height = site.DECK + (high - site.DECK) * s.step(0, .28, u) + (z - high) * s.step(.80, 1, u)
                    values.append((start[0] + (end[0] - start[0]) * q, start[1] + (end[1] - start[1]) * q, height))
                    turns.append((turn0 + (lay - turn0) * q,))
                node(f"Cooler frame {k+1:02} | {label} {row+1} on the crane", mesh_id, "Cooler delivery",
                     tracks={"translation": fleet.curve(gone, values), "yaw": fleet.curve(gone, turns), "scale": site.window(gone, at)})
                if label == "dry cooler":
                    top = fr.COOL_H + 1.9
                    lifts.append((gone, at, i, [(vx + COOLER_X * math.cos(t[0]), vy + COOLER_X * math.sin(t[0]), vz + top) for (vx, vy, vz), t in zip(values, turns)]))
            for item in (info["coolers"][row], info["pumps"][row]):
                later = [key for key in scene.nodes[item]["tracks"].get("scale", []) if key[0] > at]
                scene.nodes[item]["tracks"]["scale"] = [(0, site.OFF), (at - .02, site.OFF), (at, site.ON)] + later
            arrivals.append(at)
    assist_crane(scene, node, fleet, p, plan, sorted(lifts))
    arrivals.sort()
    return [sum(1 for a in arrivals if f >= a) for f in range(p.FRAMES)]


def assist_crane(scene, node, fleet, p, plan, lifts):
    """One all-terrain crane works its way round the laydown ahead of the crawler."""
    order = sorted(range(fr.N), key=lambda i: plan[i][0])
    stays = []       # (from, until, bearing)
    for n, i in enumerate(order):
        begin = plan[i][0] - 30 if n else plan[i][0] - 60
        stays.append([begin, plan[i][1][-1] + 6, crane_station(i)])
    first, last = stays[0][0], stays[-1][1] + 70
    park_r, road_r = fr.LAY_R + 1.2, site.R_STOP

    def carrier(f):
        if f >= stays[-1][1]:
            # Leave by the stopping lane and the access road.
            q = s.step(stays[-1][1], last, f); b = stays[-1][2]
            r = park_r + (road_r - park_r) * s.step(0, .25, q) + 70 * s.step(.3, 1, q)
            return s.polar(r, b, 0), b
        for n, (a, e, b) in enumerate(stays):
            if f <= e or n == len(stays) - 1:
                if n == 0 or f >= a: return s.polar(park_r, b, 0), b
                prev = stays[n - 1]; q = s.step(prev[1], a, f)
                turn = b - prev[2]; turn -= s.TAU * round(turn / s.TAU)
                if abs(turn) < 1e-6: return s.polar(park_r, b, 0), b
                bearing = prev[2] + turn * s.step(.2, .8, q)
                r = park_r + (road_r - park_r) * (s.step(0, .2, q) - s.step(.8, 1, q))
                face = math.pi / 2 * (s.step(0, .2, q) - s.step(.8, 1, q)) * (1 if turn > 0 else -1)
                return s.polar(r, bearing, 0), bearing + face
    span = range(first, last + 1)
    spots = [carrier(f) for f in span]
    hooks = []
    for f, (at, yaw) in zip(span, spots):
        rest = (at[0] + 7.5 * math.cos(yaw + 2.6), at[1] + 7.5 * math.sin(yaw + 2.6), 7.5)
        target = rest
        for a, e, i, pts in lifts:
            if a - 10 <= f <= e + 8:
                q = s.step(a - 10, a - 2, f) * (1 - s.step(e + 1, e + 8, f))
                goal = pts[min(len(pts) - 1, max(0, f - a))]
                target = tuple(u + (v - u) * q for u, v in zip(rest, goal))
        hooks.append(target)
    seen = site.window(first, last)
    car = node("Assist crane | carrier", scene.mesh(site.crane_carrier()), "Assist crane",
               tracks={"translation": fleet.curve(first, [at for at, _ in spots]), "yaw": fleet.curve(first, [(yaw,) for _, yaw in spots]), "scale": seen})
    tip = 17.5
    slew, reach = [], []
    for (at, yaw), hook in zip(spots, hooks):
        px, py = at[0] + site.CRANE_PIVOT[0] * math.cos(yaw), at[1] + site.CRANE_PIVOT[0] * math.sin(yaw)
        slew.append(math.atan2(hook[1] - py, hook[0] - px) - yaw)
        reach.append((math.hypot(hook[0] - px, hook[1] - py) / site.CRANE_NOMINAL[0], 1, (tip - site.CRANE_PIVOT[1]) / site.CRANE_NOMINAL[1]))
    slew = site.unwrap(slew)
    deck = node("Assist crane | slewing deck", scene.mesh(site.crane_deck()), "Assist crane", car, t=(site.CRANE_PIVOT[0], 0, 1.85),
                tracks={"yaw": fleet.curve(first, [(v,) for v in slew])})
    node("Assist crane | boom", scene.mesh(site.crane_boom()), "Assist crane", deck, t=(0, 0, site.CRANE_PIVOT[1] - 1.85),
         tracks={"scale": fleet.curve(first, reach)})
    rope = site.steel("Assist crane | hoist rope and hook block")
    site.closed(rope, -.03, -.03, .03, .03, 0, 1, "5d5445")
    node(rope.name, scene.mesh(rope), "Assist crane", tracks={"translation": fleet.curve(first, hooks),
         "scale": [(0, site.OFF), (first - .02, site.OFF)] + [(first + n, v) for n, v in fleet.flat([(1, 1, tip - h[2]) for h in hooks[:-1]], 1e-4)] + [(last, site.OFF)]})
    block = site.steel("Assist crane | hook block")
    site.closed(block, -.2, -.16, .2, .16, -.3, .1, "d69751")
    node(block.name, scene.mesh(block), "Assist crane", tracks={"translation": fleet.curve(first, hooks), "scale": seen})


def install(scene, node, p):
    fleet = scene.fleet
    scene.counts.update(concrete=concrete(scene, node, fleet, p), water=water(scene, node, fleet, p, scene.liquid),
                        coolers=coolers(scene, node, fleet, p))
