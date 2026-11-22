"""Site roads, staging areas and the vehicles that use them.

The haul ring is one-way, anticlockwise seen from above, with a running lane and
an inner stopping lane. One two-way access road joins it from the public road.
Water tankers use their own drive off the public road and never enter the ring.
Traffic keeps to the right. Coordinates are metres, X east, Y north.
"""
import bisect
import math

from . import design as cfg
from . import services
from . import silo_model as s

G = cfg.PROJECT["logistics"]["site"]
FLAT = cfg.PROJECT["logistics"]["flatbed"]
R_RUN = G["haul_ring_radius_m"]
R_STOP = G["stopping_lane_radius_m"]
LANE = G["lane_width_m"]
HALF = LANE / 2 + .1
ACCESS = math.radians(G["access_bearing_degrees"])
PUBLIC_Y = G["public_road_north_m"]
EAST_LANE = PUBLIC_Y - HALF
LEG_X = -68.
FAR = 300.
HOLDING = G["holding_lanes"]
HOLD_X = [LEG_X - HALF - 4.3 - 3.8 * i for i in range(HOLDING)]
HOLD_Y = (71., 93.)
WATER_BEARING = math.radians(G["water_fill_bearing_degrees"])
WATER_IN, WATER_OUT = -36., 8.
WATER_BAYS = cfg.PROJECT["logistics"]["water"]["bays"]
WATER_Y = [PUBLIC_Y - 27. - 3.9 * i for i in range(WATER_BAYS)]
WATER_STOP = -3.
PUMP_SKID = s.polar(71.5, WATER_BEARING, 0)
# The fuel farm lies on the bearing of the gas riser, behind one cooler frame.
_FUEL = cfg.PROJECT["fuel"]
FARM_BEARING = s.ENTRY + s.TAU / cfg.FRAMES * (_FUEL["riser_behind_frame"] - .5) + math.asin(_FUEL["riser_offset_m"] / s.RO)
FARM_R = _FUEL["distance_m"]
BACK_ROAD = FARM_R + _FUEL["tank_length_m"] / 2 + 16.
LAYBY_R = 48.6
DOCK_Y = 7.0
DOCK_FRONT = 36.4
CONCRETE_Y = 2.3
CONCRETE_FRONT = 29.6
GRAVEL, PAD, ASPHALT, LINE = "cbc2a6", "c2b99f", "a7a699", "e4dfc8"
TAU = s.TAU


def unit(angle):
    return math.cos(angle), math.sin(angle)


def local(bearing, x, y):
    """A point x metres out along a bearing and y metres to its left."""
    c, d = unit(bearing)
    return (x * c - y * d, x * d + y * c)


def ring(start, end, radius=R_RUN, step=3.):
    """Points on a circle from one bearing to another, in degrees, anticlockwise."""
    count = max(1, math.ceil((end - start) / step))
    return [s.polar(radius, math.radians(start + (end - start) * i / count), 0)[:2] for i in range(count + 1)]


def offset(points, distance):
    """Shift a polyline sideways. Positive is to the right of the direction of travel."""
    lines = []
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        length = math.hypot(bx - ax, by - ay)
        nx, ny = (by - ay) / length * distance, -(bx - ax) / length * distance
        lines.append(((ax + nx, ay + ny), (bx + nx, by + ny)))
    result = [lines[0][0]]
    for (a, b), (c, d) in zip(lines, lines[1:]):
        r = (b[0] - a[0], b[1] - a[1]); q = (d[0] - c[0], d[1] - c[1])
        det = r[0] * q[1] - r[1] * q[0]
        if abs(det) < 1e-9:
            result.append(b); continue
        t = ((c[0] - a[0]) * q[1] - (c[1] - a[1]) * q[0]) / det
        result.append((a[0] + r[0] * t, a[1] + r[1] * t))
    result.append(lines[-1][1])
    return result


def rounded(points, radius=9., keep=12.):
    """Replace each sharp corner with an arc. Corners turning less than `keep` degrees are left."""
    points = [p for i, p in enumerate(points) if i == 0 or math.hypot(p[0] - points[i - 1][0], p[1] - points[i - 1][1]) > 1e-6]
    n = len(points)
    legs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])]
    turns, cuts = [0.] * n, [0.] * n
    for i in range(1, n - 1):
        a, b, c = points[i - 1], points[i], points[i + 1]
        u = ((b[0] - a[0]) / legs[i - 1], (b[1] - a[1]) / legs[i - 1]); v = ((c[0] - b[0]) / legs[i], (c[1] - b[1]) / legs[i])
        turns[i] = math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])
        if abs(math.degrees(turns[i])) >= keep: cuts[i] = radius * math.tan(abs(turns[i]) / 2)
    limit = list(cuts)
    for i, leg in enumerate(legs):
        total = cuts[i] + cuts[i + 1]
        if total > leg * .98:
            for j in (i, i + 1):
                limit[j] = min(limit[j], cuts[j] * leg * .98 / total)
    out = [points[0]]
    for i in range(1, n - 1):
        b = points[i]
        if limit[i] <= 0:
            out.append(b); continue
        a, c = points[i - 1], points[i + 1]
        u = ((b[0] - a[0]) / legs[i - 1], (b[1] - a[1]) / legs[i - 1])
        turn, cut = turns[i], limit[i]
        r = cut / math.tan(abs(turn) / 2)
        start = (b[0] - u[0] * cut, b[1] - u[1] * cut)
        side = 1 if turn > 0 else -1
        centre = (start[0] - u[1] * side * r, start[1] + u[0] * side * r)
        a0 = math.atan2(start[1] - centre[1], start[0] - centre[0])
        steps = max(2, math.ceil(abs(math.degrees(turn)) / 9))
        for k in range(steps + 1):
            ang = a0 + turn * k / steps
            out.append((centre[0] + r * math.cos(ang), centre[1] + r * math.sin(ang)))
    out.append(points[-1])
    return out


class Path:
    """A route on the ground with distance measured along it."""

    def __init__(self, points, radius=9.):
        self.points = rounded(points, radius)
        self.at_length = [0.]
        for a, b in zip(self.points, self.points[1:]):
            self.at_length.append(self.at_length[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.length = self.at_length[-1]

    def at(self, distance):
        if distance <= 0:
            (ax, ay), (bx, by) = self.points[:2]; span = self.at_length[1]
            return (ax + (bx - ax) * distance / span, ay + (by - ay) * distance / span)
        if distance >= self.length:
            (ax, ay), (bx, by) = self.points[-2:]; span = self.length - self.at_length[-2]
            over = distance - self.at_length[-2]
            return (ax + (bx - ax) * over / span, ay + (by - ay) * over / span)
        i = bisect.bisect_right(self.at_length, distance) - 1
        (ax, ay), (bx, by) = self.points[i], self.points[i + 1]
        t = (distance - self.at_length[i]) / (self.at_length[i + 1] - self.at_length[i])
        return (ax + (bx - ax) * t, ay + (by - ay) * t)

    def nearest(self, point, after=0.):
        """Distance along the path of the point closest to a given position."""
        best, where = 1e18, 0.
        for i, ((ax, ay), (bx, by)) in enumerate(zip(self.points, self.points[1:])):
            if self.at_length[i + 1] < after: continue
            dx, dy = bx - ax, by - ay
            t = s.clamp(((point[0] - ax) * dx + (point[1] - ay) * dy) / (dx * dx + dy * dy))
            gap = math.hypot(ax + dx * t - point[0], ay + dy * t - point[1])
            if gap < best - 1e-9:
                best, where = gap, self.at_length[i] + t * (self.at_length[i + 1] - self.at_length[i])
        return where


# Lane centrelines of the access road, travelling in and travelling out.
_SPINE = [(LEG_X, EAST_LANE), (LEG_X, None), s.polar(R_STOP - 6, ACCESS, 0)[:2]]
_SPINE[1] = (LEG_X, LEG_X * math.tan(ACCESS))
BEND = _SPINE[1]
INBOUND = offset(_SPINE, HALF)
OUTBOUND = offset(_SPINE[::-1], HALF)


def _junction(radius, lane):
    """Bearing in degrees at which an access lane meets a ring lane."""
    return math.degrees(ACCESS + lane * math.asin(HALF / radius))


JOIN = {R_RUN: _junction(R_RUN, 1), R_STOP: _junction(R_STOP, 1)}
LEAVE = {R_RUN: _junction(R_RUN, -1) + 360, R_STOP: _junction(R_STOP, -1) + 360}


def arrive(radius=R_RUN, holding=None, spawn=-FAR):
    """Public road, gate and access road to the point where a lane of the ring is joined."""
    points = [(spawn, EAST_LANE), (INBOUND[0][0], EAST_LANE)]
    if holding is not None:
        x = HOLD_X[holding]; run = max(7., .8 * (INBOUND[0][0] - x))
        points += [(INBOUND[0][0], HOLD_Y[1] + run + 4), (x, HOLD_Y[1] + 3), (x, HOLD_Y[0] - 3), (INBOUND[0][0], HOLD_Y[0] - 3 - run)]
    points.append(INBOUND[1])
    c, d = unit(ACCESS); tx, ty = -d * HALF, c * HALF
    reach = math.sqrt(radius**2 - HALF**2)
    points.append((c * reach + tx, d * reach + ty))
    return points


def depart(radius=R_RUN, spawn=FAR):
    """From a ring lane out along the access road and away east on the public road."""
    c, d = unit(ACCESS); tx, ty = d * HALF, -c * HALF
    reach = math.sqrt(radius**2 - HALF**2)
    return [(c * reach + tx, d * reach + ty), OUTBOUND[1], (OUTBOUND[2][0], EAST_LANE), (spawn, EAST_LANE)]


TURN = 13.


def lap(first, last, radius=R_RUN, lead=TURN, tail=TURN):
    """Ring points between two bearings in degrees, leaving room at each end for the turn on or off the ring."""
    if last - tail <= first + lead: return []
    return ring(first + lead, last - tail, radius)


def back_road(start=None):
    """Centreline of the one-way road from the back of the fuel farm north to the public road."""
    c, d = unit(FARM_BEARING)
    # Local Y runs to the left of the bearing. The road runs along local X = BACK_ROAD until it meets the eastbound lane.
    y = (EAST_LANE - BACK_ROAD * d) / c
    first = local(FARM_BEARING, BACK_ROAD, 26. if start is None else start)
    return [first, local(FARM_BEARING, BACK_ROAD, y), (FAR, EAST_LANE)]


def holding_stop(lane):
    """Front of a truck waiting in a holding lane."""
    return (HOLD_X[lane], HOLD_Y[0])


def ground(scene):
    """Add the roads and pads to the terrain, and the fixed site furniture to the landscape details."""
    land, details = scene.meshes[0], scene.meshes[1]

    def strip(points, width, z, colour):
        left, right = offset(points, -width / 2), offset(points, width / 2)
        for a, b, c, d in zip(left, left[1:], right[1:], right):
            land.face([(a[0], a[1], z), (d[0], d[1], z), (c[0], c[1], z), (b[0], b[1], z)], colour)

    def pad(points, z, colour):
        land.face([(x, y, z) for x, y in points], colour)

    # Public road with a centre line.
    s.quad_xy(land, -700, PUBLIC_Y - 3.9, 700, PUBLIC_Y + 3.9, .004, ASPHALT)
    for x in range(-690, 690, 9):
        s.quad_xy(land, x, PUBLIC_Y - .09, x + 4.5, PUBLIC_Y + .09, .006, LINE)
    # Access road, two lanes, and the holding lanes beside it.
    spine = rounded(_SPINE[:2] + [s.polar(R_RUN + HALF, ACCESS, 0)[:2]], 14)
    spine[0] = (LEG_X, PUBLIC_Y - 3.9)
    strip(spine, 2 * LANE + 1.6, .005, GRAVEL)
    strip(offset(spine, 0), .14, .007, LINE)
    west, east = HOLD_X[-1] - 2.3, LEG_X - LANE - .8
    pad([(west, HOLD_Y[0] - 16), (east, HOLD_Y[0] - 16), (east, HOLD_Y[1] + 16), (west, HOLD_Y[1] + 16)], .0045, PAD)
    for i in range(HOLDING + 1):
        x = HOLD_X[0] + 1.9 - 3.8 * i
        s.quad_xy(land, x - .07, HOLD_Y[0] - 4, x + .07, HOLD_Y[1] + 2, .0065, LINE)
    # Haul ring: stopping lane inside, running lane outside.
    inner, outer = R_STOP - HALF - .3, R_RUN + HALF + .3
    n = 120
    for i in range(n):
        a, b = TAU * i / n, TAU * (i + 1) / n
        land.face([s.polar(inner, a, .005), s.polar(outer, a, .005), s.polar(outer, b, .005), s.polar(inner, b, .005)], GRAVEL)
        if i % 2 == 0:
            mid = (R_RUN + R_STOP) / 2
            land.face([s.polar(mid - .07, a, .007), s.polar(mid + .07, a, .007), s.polar(mid + .07, b, .007), s.polar(mid - .07, b, .007)], LINE)
    # Road out of the back of the fuel farm to the public road.
    strip(back_road()[:-1] + [(back_road()[-2][0], PUBLIC_Y - 3.9)], LANE + 1.6, .005, GRAVEL)
    # Water unloading drive off the public road.
    south = WATER_Y[-1] - 3.2
    s.quad_xy(land, WATER_IN - 3.4, south, WATER_OUT + 3.4, WATER_Y[0] + 3.2, .005, GRAVEL)
    for x in (WATER_IN, WATER_OUT):
        s.quad_xy(land, x - 3.4, WATER_Y[0] + 3.2, x + 3.4, PUBLIC_Y - 3.9, .005, GRAVEL)
    for y in WATER_Y[:-1]:
        s.quad_xy(land, WATER_IN + 8, y - 2.02, WATER_OUT - 8, y - 1.88, .007, LINE)
    # Fixed furniture: gatehouse, water manifold and pump skid, fill line to the silo wall.
    def block(x0, y0, x1, y1, z0, z1, colour):
        s.box(details, x0, y0, x1, y1, z0, z1, colour)
    block(LEG_X - 9.6, PUBLIC_Y - 13.5, LEG_X - 5.6, PUBLIC_Y - 9.0, 0, 2.7, "768b84")
    block(LEG_X - 9.8, PUBLIC_Y - 13.7, LEG_X - 5.4, PUBLIC_Y - 8.8, 2.7, 2.86, "b4bbae")
    header = WATER_Y[-1] - 2.6
    services.pipe(details, (WATER_STOP - 15, header, .45), (WATER_STOP + 1, header, .45), .16, "5f8f9a", n=8)
    for i, y in enumerate(WATER_Y):
        x = WATER_STOP - 5.5 - 3.2 * i
        block(x - .25, header - .25, x + .25, header + .25, 0, 1.25, "49666b")
        services.pipe(details, (x, header, 1.1), (x, y - 1.25, .9), .07, "30383a", n=6)
    px, py, _ = PUMP_SKID
    block(px - 2.2, py - 1.2, px + 2.2, py + 1.2, .05, 1.7, "6c938f")
    block(px - 2.4, py - 1.4, px + 2.4, py + 1.4, 0, .12, "a2997b")
    services.pipe(details, (WATER_STOP - 15, header, .45), (px, py + 1.2, .45), .16, "5f8f9a", n=8)
    # The fill line is buried from the ring to the silo. Headwalls mark where it goes under and a riser where it enters the wall.
    edge = s.polar(R_RUN + HALF + 1.2, WATER_BEARING, .45)
    services.pipe(details, (px, py - 1.2, .45), edge, .16, "5f8f9a", n=8)
    c, d = unit(WATER_BEARING)
    for radius in (R_RUN + HALF + 1.0, s.RO + 1.3):
        cx, cy, _ = s.polar(radius, WATER_BEARING, 0)
        pts = [(cx + c * u - d * v, cy + d * u + c * v) for u, v in ((-.25, -.7), (.25, -.7), (.25, .7), (-.25, .7))]
        details.face([(x, y, .75) for x, y in pts], "9aa39c")
        for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
            details.face([(ax, ay, 0), (bx, by, 0), (bx, by, .75), (ax, ay, .75)], "8d9a95")
    foot = s.polar(s.RO + 1.3, WATER_BEARING, .45); wall = s.polar(s.RO + .2, WATER_BEARING, .45)
    services.pipe(details, foot, wall, .16, "5f8f9a", n=8)
    services.pipe(details, wall, (wall[0], wall[1], 1.4), .16, "5f8f9a", n=8)
    services.pipe(details, (wall[0], wall[1], 1.4), s.polar(s.RO - .05, WATER_BEARING, 1.4), .16, "49666b", n=8)
    # The overflow from the store leaves beside the fill line, is buried under the ring with it and ends in a catch tank by the pump skid.
    o = cfg.PROJECT["thermal"]["overflow"]
    side = lambda radius, z: services.beside(WATER_BEARING, o["offset_from_fill_line_m"], radius, z)
    bore = o["pipe_diameter_m"] / 2
    services.pipe(details, side(s.RO + .2, .9), side(s.RO + .2, .45), bore, "8d9896", n=8)
    services.pipe(details, side(s.RO + .2, .45), side(s.RO + 1.3, .45), bore, "8d9896", n=8)
    tx, ty, _ = services.beside(WATER_BEARING, o["catch_tank_from_pump_skid_m"], 71.5, 0)
    services.pipe(details, side(R_RUN + HALF + 1.2, .45), (tx, ty, .45), bore, "8d9896", n=8)
    radius = o["catch_tank_diameter_m"] / 2
    height = o["catch_tank_m3"] / (math.pi * radius**2)
    services.pipe(details, (tx, ty, 0), (tx, ty, .12), radius + .25, "a2997b", n=20)
    services.pipe(details, (tx, ty, .12), (tx, ty, .12 + height), radius, "9fb0ad", n=20)


# ---------------------------------------------------------------------------------------------
# Vehicles. A tractor's origin is its fifth wheel and a trailer's origin is its kingpin, X forward.
STEER = 3.4          # fifth wheel to the front axle, which is the point that follows the route
DECK = FLAT["deck_height_m"]
DECK_L, DECK_W = FLAT["deck_length_m"], FLAT["deck_width_m"]
DECK_FRONT = 1.2     # deck ahead of the kingpin
FLAT_AXLE = 11.2     # kingpin to the middle of the trailer axles
TIRE, HUB = "293238", "88928d"
CABS = ("6c938f", "b8894f", "8f9a96", "5f7f96", "a65f4a", "c9c7ae")


def closed(m, x0, y0, x1, y1, z0, z1, colour):
    s.box(m, x0, y0, x1, y1, z0, z1, colour)
    m.face([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], colour)


def steel(name):
    m = s.Mesh(name); m.material = 3
    return m


def axle(m, x, half=1.02, radius=.52, width=.56):
    for sign in (-1, 1):
        services.pipe(m, (x, sign * (half - width / 2), radius), (x, sign * (half + width / 2), radius), radius, TIRE, n=8)
        services.pipe(m, (x, sign * (half + width / 2), radius), (x, sign * (half + width / 2 + .03), radius), radius * .5, HUB, n=6)


def tractor(colour):
    m = steel("Road tractor | day cab")
    closed(m, -1.5, -.48, 4.5, .48, .62, .95, "414b4c")
    closed(m, 1.55, -1.22, 3.45, 1.22, .95, 2.95, colour)
    closed(m, 3.45, -1.12, 4.75, 1.12, .95, 1.95, colour)
    closed(m, 1.50, -1.24, 3.50, 1.24, 2.95, 3.10, "c9c7ae")
    closed(m, 3.44, -1.02, 3.47, 1.02, 2.0, 2.8, "4b6971")
    for sign in (-1, 1):
        y = sign * 1.225
        closed(m, 2.1, min(y, y + sign * .02), 3.3, max(y, y + sign * .02), 2.0, 2.8, "4b6971")
    closed(m, 4.75, -1.18, 4.95, 1.18, .55, .95, "a7b0a6")
    closed(m, -.55, -.55, .55, .55, .95, 1.12, "343c3d")
    for x in (STEER, .65, -.65):
        axle(m, x, width=.34 if x == STEER else .56)
    for sign in (-1, 1):
        services.pipe(m, (1.3, sign * 1.0, 1.0), (1.3, sign * 1.0, 3.5), .09, "9aa39c", n=6)
    return m


def running_gear(m, length, axles):
    """Main beams, landing legs and axles common to every semi-trailer."""
    closed(m, -length, -.5, DECK_FRONT - .2, .5, .78, 1.12, "414b4c")
    for x in axles: axle(m, x)
    for sign in (-1, 1):
        closed(m, -2.3, sign * .62 - .08, -2.1, sign * .62 + .08, .12, .8, "59646a")


def flatbed():
    m = steel(f"Flatbed semi-trailer | {DECK_L:g} m deck")
    rear = DECK_FRONT - DECK_L
    running_gear(m, -rear, (-FLAT_AXLE - .65, -FLAT_AXLE + .65))
    closed(m, rear, -DECK_W / 2, DECK_FRONT, DECK_W / 2, 1.12, DECK, "a2997b")
    closed(m, rear, -DECK_W / 2, DECK_FRONT, DECK_W / 2, 1.10, 1.22, "536667")
    closed(m, DECK_FRONT - .08, -DECK_W / 2, DECK_FRONT, DECK_W / 2, DECK, DECK + 1.3, "536667")
    return m


TANKER_AXLE = 9.6


def tanker(name, colour, length, diameter, band=None):
    m = steel(name)
    rear = DECK_FRONT - length
    running_gear(m, -rear, (-TANKER_AXLE - .65, -TANKER_AXLE + .65))
    r = diameter / 2; z = 1.25 + r
    services.pipe(m, (rear + r * .5, 0, z), (DECK_FRONT - r * .5, 0, z), r, colour, n=12)
    for sign, x in ((-1, rear + r * .5), (1, DECK_FRONT - r * .5)):
        services.pipe(m, (x, 0, z), (x + sign * r * .32, 0, z), r * .82, colour, n=12)
        services.pipe(m, (x + sign * r * .32, 0, z), (x + sign * r * .5, 0, z), r * .5, colour, n=12)
    if band:
        mid = (rear + DECK_FRONT) / 2
        services.pipe(m, (mid - .5, 0, z), (mid + .5, 0, z), r + .015, band, n=12)
    for x in (rear + 2.2, -2.6, (rear - 2.6) / 2 + 1.1):
        closed(m, x - .18, -.75, x + .18, .75, 1.1, z - r * .6, "59646a")
    closed(m, rear - .1, -1.15, rear + .1, 1.15, .7, .95, "a7b0a6")
    return m


HAUL_AXLE = 19.0


def haul_trailer(length=22.5):
    """Beam trailer for a long vessel: gooseneck, low beam and a three-axle bogie."""
    m = steel("Heavy-haul beam trailer | three-axle rear bogie")
    closed(m, -1.6, -.75, DECK_FRONT - .2, .75, .9, 1.25, "8a5a3c")
    closed(m, -length, -.62, -1.6, .62, .55, .98, "8a5a3c")
    for x in (-HAUL_AXLE - 1.35, -HAUL_AXLE, -HAUL_AXLE + 1.35):
        axle(m, x, half=1.12, radius=.5)
    closed(m, -length - .1, -1.4, -length + .1, 1.4, .6, .9, "d4af6b")
    return m


MIXER_BASE = 5.3     # rear bogie to the front axle


def mixer(colour):
    """A rigid truck mixer. Its origin is the middle of the rear bogie and the chute is at the back."""
    m = steel("Truck mixer | rear discharge")
    closed(m, -2.3, -.5, MIXER_BASE + 1.2, .5, .62, .98, "414b4c")
    closed(m, MIXER_BASE - 1.0, -1.2, MIXER_BASE + .9, 1.2, .98, 2.9, colour)
    closed(m, MIXER_BASE + .9, -1.1, MIXER_BASE + 1.35, 1.1, .98, 1.9, colour)
    closed(m, MIXER_BASE + .88, -1.0, MIXER_BASE + .91, 1.0, 2.0, 2.75, "4b6971")
    services.pipe(m, (MIXER_BASE - 1.3, 0, 2.15), (.9, 0, 2.55), 1.18, "d8d6c8", n=10)
    services.pipe(m, (.9, 0, 2.55), (-1.5, 0, 3.05), .98, "c9c7b9", n=10)
    services.pipe(m, (-1.5, 0, 3.05), (-2.1, 0, 3.2), .55, "b9b7a9", n=10)
    services.pipe(m, (2.6, 0, 2.33), (3.0, 0, 2.25), 1.20, colour, n=10)
    s.bar(m, (-2.2, 0, 2.5), (-3.3, 0, 1.45), .46, "7b8582", .12)
    closed(m, -2.35, -.9, -2.2, .9, .98, 3.0, "59646a")
    for x in (MIXER_BASE, .65, -.65):
        axle(m, x, width=.34 if x == MIXER_BASE else .56)
    return m


def crane_carrier():
    m = steel("Assist crane | all-terrain carrier and slewing deck")
    closed(m, -5.2, -1.3, 5.0, 1.3, .7, 1.55, "d7a84c")
    closed(m, 3.6, -1.3, 5.0, -.1, 1.55, 2.75, "d7a84c")
    closed(m, 3.62, -1.25, 5.02, -.15, 1.9, 2.6, "4b6971")
    for x in (-3.9, -2.4, 1.6, 3.2):
        axle(m, x, half=1.05, radius=.62, width=.5)
    for x in (-4.6, 0.2):
        closed(m, x - .2, -3.4, x + .2, 3.4, .62, .82, "59646a")
        for sign in (-1, 1):
            closed(m, x - .4, sign * 3.4 - .4, x + .4, sign * 3.4 + .4, 0, .62, "8d9a95")
    services.pipe(m, (-.8, 0, 1.55), (-.8, 0, 1.85), 1.25, "59646a", n=12)
    return m


CRANE_PIVOT = (-.8, 2.6)     # boom foot ahead of the carrier origin, and its height
CRANE_NOMINAL = (10., 14.)


def crane_boom():
    m = steel("Assist crane | telescopic boom")
    dx, dz = CRANE_NOMINAL
    s.bar(m, (0, 0, 0), (dx * .5, 0, dz * .5), .62, "d7a84c", .7)
    s.bar(m, (dx * .46, 0, dz * .46), (dx * .78, 0, dz * .78), .5, "e2bb6b", .56)
    s.bar(m, (dx * .74, 0, dz * .74), (dx, 0, dz), .38, "ecd08c", .42)
    return m


def crane_deck():
    m = steel("Assist crane | operator cab and counterweight")
    closed(m, -3.4, -1.25, -1.2, 1.25, 0, 1.2, "59646a")
    closed(m, -1.0, .35, 1.2, 1.25, 0, 1.5, "d7a84c")
    closed(m, -.98, .4, 1.22, 1.2, .5, 1.4, "4b6971")
    return m


RAMP = .35


def ramp(u):
    """Pull away from rest over the first part of a leg, then hold a steady speed."""
    if u < RAMP: return u * u / (2 * RAMP) / (1 - RAMP / 2)
    return (u - RAMP / 2) / (1 - RAMP / 2)


def frames_for(distance, speed, ease=(True, True), fps=24):
    """Frames a leg takes when its top speed is `speed` metres a second."""
    factor = 1.5 if all(ease) else 1 / (1 - RAMP / 2) if any(ease) else 1.
    return max(2, math.ceil(abs(distance) / speed * fps * factor))


class Trip:
    """A vehicle's journey: legs along routes, with waits between them."""

    def __init__(self):
        self.legs = []

    def drive(self, path, start, end, begin, finish, ease=(True, True)):
        self.legs.append((begin, finish, path, start, end, ease))
        return self

    @property
    def begin(self): return self.legs[0][0]

    @property
    def finish(self): return self.legs[-1][1]

    def state(self, t):
        """The route and the distance along it of the front axle at time t."""
        current = self.legs[0]
        for leg in self.legs:
            if t >= leg[0]: current = leg
        begin, finish, path, start, end, (ease_in, ease_out) = current
        u = s.clamp((t - begin) / max(1e-9, finish - begin))
        if ease_in and ease_out: u = u * u * (3 - 2 * u)
        elif ease_in: u = ramp(u)
        elif ease_out: u = 1 - ramp(1 - u)
        return path, start + (end - start) * u


def heading(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def rig_pose(path, distance, axle_back):
    """Tractor and trailer of an articulated truck whose front axle is `distance` along a route.

    Returns the kingpin position, the tractor heading and the trailer heading.
    """
    front, pin = path.at(distance), path.at(distance - STEER)
    back = path.at(distance - STEER - axle_back)
    return pin, heading(pin, front), heading(back, pin)


def rigid_pose(path, distance, wheelbase):
    front, back = path.at(distance), path.at(distance - wheelbase)
    return back, heading(back, front)


def unwrap(values):
    out = [values[0]]
    for v in values[1:]:
        out.append(v - TAU * round((v - out[-1]) / TAU))
    return out


OFF, ON = (0., 0., 0.), (1., 1., 1.)


def hold(frame, pause=None):
    """Site clock. Traffic stands still while the film cross-fades from the cutaway walls to the full walls."""
    if pause is None: pause = (s.LAST_POUR + 2, s.LAST_POUR + s.REVEAL)
    a, b = pause
    if frame <= a: return float(frame)
    if frame <= b: return float(a)
    catch = 3 * (b - a)
    if frame >= b + catch: return float(frame)
    return a + (frame - b) * (b + catch - a) / catch


def window(first, last):
    keys = [(0, ON if first <= 0 else OFF)]
    if first > 0: keys += [(first - .02, OFF), (first, ON)]
    keys += [(last - .02, ON), (last, OFF)]
    return keys


def span(trip, total, clock=hold):
    """First and last film frames on which a trip is on site."""
    first = max(0, math.floor(trip.begin)); last = min(total - 1, math.ceil(trip.finish) + 60)
    while first > 0 and clock(first) > trip.begin: first -= 1
    while last > first and clock(last - 1) >= trip.finish: last -= 1
    return first, last


class Fleet:
    """Adds vehicles to the scene and keeps one copy of each mesh."""

    def __init__(self, scene, node, flat_keys, total):
        self.scene, self.node, self.flat, self.total = scene, node, flat_keys, total
        self.meshes = {}
        self.count = 0

    def mesh(self, key, build):
        if key not in self.meshes: self.meshes[key] = self.scene.mesh(build())
        return self.meshes[key]

    def curve(self, first, values):
        keys = [(first + k, v) for k, v in self.flat(values, 1e-4)]
        return keys if first <= 0 else [(0, values[0])] + keys

    def rig(self, name, trip, trailer, axle_back, clock=hold, group="Road vehicles"):
        """An articulated truck. Returns the trailer node, its on-site frames and a function giving its pose."""
        first, last = span(trip, self.total, clock)
        pins, cab, tow = [], [], []
        for f in range(first, last + 1):
            path, distance = trip.state(clock(f))
            pin, a, b = rig_pose(path, distance, axle_back)
            pins.append((pin[0], pin[1], 0.)); cab.append(a); tow.append(b)
        cab, tow = unwrap(cab), unwrap(tow)
        colour = CABS[self.count % len(CABS)]; self.count += 1
        seen = window(first, last)
        place = self.curve(first, pins)
        self.node(name + " | tractor", self.mesh(("tractor", colour), lambda: tractor(colour)), group,
                  tracks={"translation": place, "yaw": self.curve(first, [(v,) for v in cab]), "scale": seen})
        towed = self.node(name + " | trailer", trailer, group,
                          tracks={"translation": place, "yaw": self.curve(first, [(v,) for v in tow]), "scale": seen})

        def pose(frame):
            k = min(last, max(first, frame)) - first
            return pins[k], tow[k]
        return towed, (first, last), pose

    def rigid(self, name, trip, body, wheelbase, clock=hold, group="Road vehicles"):
        first, last = span(trip, self.total, clock)
        at, yaw = [], []
        for f in range(first, last + 1):
            path, distance = trip.state(clock(f))
            back, a = rigid_pose(path, distance, wheelbase)
            at.append((back[0], back[1], 0.)); yaw.append(a)
        yaw = unwrap(yaw)
        return self.node(name, body, group, tracks={"translation": self.curve(first, at), "yaw": self.curve(first, [(v,) for v in yaw]),
                                                    "scale": window(first, last)}), (first, last)


def check():
    site = cfg.SITE
    frames_edge = site["laydown_radius_m"] + cfg.COOL["frame_depth_m"]
    if R_STOP - LANE / 2 < frames_edge + .3:
        raise ValueError("The stopping lane runs into the cooler frames in laydown. Increase logistics.site.stopping_lane_radius_m.")
    if R_RUN - R_STOP < LANE:
        raise ValueError("The running lane and the stopping lane overlap. Move the haul ring out.")
    if R_RUN + LANE / 2 > site["crane_track_radius_m"] - 3.4:
        raise ValueError("The haul ring is inside the crawler's tail swing. Move the ring in or the crane track out.")
    if PUBLIC_Y < HOLD_Y[1] + 20 or WATER_Y[-1] < R_RUN + 20:
        raise ValueError("Keep the public road far enough north for the holding lanes and the water drive.")
    if DOCK_Y + DECK_W / 2 > site["laydown_radius_m"] * math.sin(math.radians(18)) - .3:
        raise ValueError("The dock lanes run into the cooler frames stood beside the entry.")


check()
