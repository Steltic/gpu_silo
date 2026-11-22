"""Pipes inside the store that keep it layered, the cover over it and its overflow. From check 5.

The pods draw the cool layer from the bottom of the store and return to the warm layer at the top.
The coolers do the reverse. Each bay of pods and each cooler frame has one pair of vertical pipes,
and every open end faces a plate so that the liquid leaves sideways and slowly.
"""
import math

from . import cooler_frames
from . import design as cfg
from . import services
from . import silo_model as s
from . import site
from . import thermal

L = cfg.PROJECT["thermal"]["layering"]
COVER = cfg.PROJECT["thermal"]["cover"]
OVERFLOW = cfg.PROJECT["thermal"]["overflow"]
RADIUS = L["riser_diameter_m"] / 2
BORE = RADIUS - L["riser_wall_mm"] / 1000
PLATE = L["diffuser_diameter_m"] / 2
GAP = L["diffuser_gap_m"]
COLD_FILL = cfg.LIQUID_TOP - thermal.C["swell"]["to_hot"]
FLOOR_MOUTH = L["mouth_above_floor_m"]
TOP_MOUTH = round(COLD_FILL - L["top_mouth_below_cold_fill_m"], 3)
POD_R = services.TANK_END + L["pod_riser_beyond_sleeve_m"]
POD_Y = L["pod_riser_offset_m"]
COOLER_R = s.RI_OUTER - L["cooler_riser_off_wall_m"]
COVER_Z = (s.WALL_HEIGHT - COVER["below_rim_m"] - COVER["thickness_m"], s.WALL_HEIGHT - COVER["below_rim_m"])
OVERFLOW_Z = cfg.LIQUID_TOP + OVERFLOW["above_liquid_m"]
OVERFLOW_R = s.RI_OUTER - .30
WARM, COOL, STEEL, PLATE_COLOUR = "c98a62", "4f86a6", "8d9896", "aab3ae"
ON, OFF = (1., 1., 1.), (0., 0., 0.)


def plate(m, x, y, z, colour=PLATE_COLOUR):
    """A round plate facing an open pipe end, on three legs."""
    services.pipe(m, (x, y, z), (x, y, z + .03), PLATE, colour, n=20)


def riser(m, x, y, low, high, colour, opens):
    """One vertical pipe. `opens` is 'top' or 'bottom': that end is open and faces a plate."""
    services.pipe(m, (x, y, low), (x, y, high), RADIUS, colour, ri=BORE, n=14)
    if opens == "top":
        services.pipe(m, (x, y, low - .02), (x, y, low), RADIUS, colour, n=14)
        plate(m, x, y, high + GAP)
        ends = (high, high + GAP)
    else:
        services.pipe(m, (x, y, high), (x, y, high + .02), RADIUS, colour, n=14)
        plate(m, x, y, low - GAP - .03)
        ends = (low - GAP, low)
    for k in range(3):
        a = k * s.TAU / 3 + .5
        px, py = x + (PLATE - .08) * math.cos(a), y + (PLATE - .08) * math.sin(a)
        s.bar(m, (px, py, ends[0]), (px, py, ends[1]), .04, STEEL)


def pod_mesh():
    """The pair of pipes for one bay, in the bay's own axes: x is outward along the bay line."""
    m = s.Mesh("Store pipes | pod supply from the bottom of the store and return to the top")
    m.material = 3
    ports = [services.port_height(level) for level in range(1, cfg.LEVELS + 1)]
    riser(m, POD_R, -POD_Y, FLOOR_MOUTH, ports[-1] + .30, COOL, "bottom")
    riser(m, POD_R, POD_Y, ports[0] - .30, TOP_MOUTH, WARM, "top")
    for z in ports:
        for side, colour in ((-1, COOL), (1, WARM)):
            services.pipe(m, (services.TANK_END - .02, side * services.PORT_OFFSET, z + .015), (POD_R, side * POD_Y, z + .015), services.BRANCH_BORE+.006, colour, n=12)
    for z in [p + cfg.STORE["pitch_m"] / 2 for p in ports[:-1]] + [ports[-1] + 4, ports[-1] + 8]:
        for side in (-1, 1):
            if side < 0 and z > ports[-1] + .3: continue
            s.bar(m, (s.RO_INNER, side * POD_Y, z), (POD_R - RADIUS, side * POD_Y, z), .07, STEEL)
    return m


def cooler_points(k):
    """Angle from the frame bearing, and the conduit heights, of the return and suction sides of frame k."""
    points = cooler_frames.conduit_points(k)
    rows = cooler_frames.ROWS
    return (points[0][0], [z for _, z in points[:rows]]), (points[rows][0], [z for _, z in points[rows:]])


def cooler_mesh(k):
    """The pair of pipes for one cooler frame, about the frame's bearing."""
    m = s.Mesh("Store pipes | cooler suction from the top of the store and return to the bottom")
    m.material = 3
    (turn_return, z_return), (turn_suction, z_suction) = cooler_points(k)
    x, y, _ = s.polar(COOLER_R, turn_return, 0)
    riser(m, x, y, FLOOR_MOUTH, max(z_return) + .30, COOL, "bottom")
    for z in z_return:
        services.pipe(m, s.polar(s.RI_OUTER - .05, turn_return, z), (x, y, z), .11, COOL, n=8)
    x, y, _ = s.polar(COOLER_R, turn_suction, 0)
    riser(m, x, y, min(z_suction) - .30, TOP_MOUTH, WARM, "top")
    for z in z_suction:
        services.pipe(m, s.polar(s.RI_OUTER - .05, turn_suction, z), (x, y, z), .11, WARM, n=8)
    for turn, low, high in ((turn_return, FLOOR_MOUTH + 1, max(z_return)), (turn_suction, min(z_suction), TOP_MOUTH - .5)):
        z = low + 2.5
        while z < high:
            s.bar(m, s.polar(COOLER_R + RADIUS, turn, z), s.polar(s.RI_OUTER, turn, z), .07, STEEL)
            z += 5.
    return m


def overflow_point(radius, z):
    """A point on the overflow line, which runs beside the fill line."""
    return services.beside(site.WATER_BEARING, OVERFLOW["offset_from_fill_line_m"], radius, z)


def cover_mesh():
    m = s.Mesh("Store cover | sealed deck over the liquid, with a breather")
    m.material = 3
    s.sector(m, s.RO_INNER + .01, s.RI_OUTER - .01, COVER_Z[0], COVER_Z[1], 0, s.TAU, 48, [PLATE_COLOUR, PLATE_COLOUR, "b9c1bc", PLATE_COLOUR], caps=False)
    bearing = site.WATER_BEARING + .35
    z = COVER_Z[0] - .08
    services.pipe(m, s.polar(s.RI_OUTER - .1, bearing, z), s.polar(s.RO + .25, bearing, z), .05, STEEL, n=8)
    services.pipe(m, s.polar(s.RO + .25, bearing, z), s.polar(s.RO + .25, bearing, z - .30), .05, STEEL, n=8)
    return m


def overflow_mesh():
    """The standpipe inside the store. Its rim is the overflow level. It leaves through the outer wall beside the fill line."""
    m = s.Mesh("Store overflow | standpipe to the catch tank")
    m.material = 3
    r = OVERFLOW["pipe_diameter_m"] / 2
    top, low = overflow_point(OVERFLOW_R, OVERFLOW_Z), overflow_point(OVERFLOW_R, .9)
    services.pipe(m, low, top, r, STEEL, ri=r - .012, n=10)
    services.pipe(m, (top[0], top[1], top[2] - .14), top, r + .10, STEEL, ri=r + .08, n=12)
    services.pipe(m, low, overflow_point(s.RO + .2, .9), r, STEEL, n=10)
    return m


def start(levels):
    """The frame on which the store begins to fill. The pipes and the cover are in place by then."""
    return next((f for f, z in enumerate(levels) if z > 0), 1)


def install(scene, node, levels):
    first = max(1, start(levels))
    show = [(0, OFF), (first - 1, OFF), (first, ON)]
    pods = scene.mesh(pod_mesh())
    for bay, angle in enumerate(services.PORT_ANGLES, 1):
        node(f"Bay {bay:02} | store pipes", pods, "Store pipes", ang=angle, tracks={"scale": show})
    meshes = {}
    for k in range(cooler_frames.N):
        tier = cooler_frames.tier(k)
        if tier not in meshes: meshes[tier] = scene.mesh(cooler_mesh(k))
        node(f"Cooler frame {k+1:02} | store pipes", meshes[tier], "Store pipes", ang=cooler_frames.THETA[k], tracks={"scale": show})
    node("Store cover | sealed deck", scene.mesh(cover_mesh()), "Store cover", tracks={"scale": show})
    node("Store overflow | standpipe", scene.mesh(overflow_mesh()), "Store overflow", tracks={"scale": show})
    scene.project_info.update(storePipePairs=cfg.BAYS + cooler_frames.N, storePipeDiameter_m=L["riser_diameter_m"],
                              storeColdFill_m=round(COLD_FILL, 3), storeOverflow_m=round(OVERFLOW_Z, 3), storeCover=True)


def check():
    """The pipes fit in the store, stay under the liquid when it is cold, and miss the doorway."""
    assert s.RO_INNER + PLATE < POD_R and POD_R + PLATE < COOLER_R - PLATE and COOLER_R + PLATE < s.RI_OUTER, "the plates do not fit across the store"
    assert TOP_MOUTH + GAP + .03 < COLD_FILL, "the top openings are not covered when the store is cold"
    assert FLOOR_MOUTH - GAP - .03 > 0 and cfg.LIQUID_TOP < OVERFLOW_Z < COVER_Z[0] and COVER_Z[1] <= s.WALL_HEIGHT
    clear = services.JAMB + PLATE + .2
    for k in range(cooler_frames.N):
        for turn, heights in cooler_points(k):
            angle = cooler_frames.THETA[k] + turn - s.ENTRY
            assert math.cos(angle) < 0 or abs(COOLER_R * math.sin(angle)) > clear, f"a pipe of cooler frame {k+1} comes down on the doorway"
            assert FLOOR_MOUTH < min(heights) and max(heights) < TOP_MOUTH
    for angle in services.PORT_ANGLES:
        assert math.cos(angle - s.ENTRY) < 0 or abs(POD_R * math.sin(angle - s.ENTRY)) - POD_Y > clear, "a pod pipe comes down on the doorway"
    # The overflow standpipe stands clear of the cooler pipes.
    ox, oy, _ = overflow_point(OVERFLOW_R, 0)
    for k in range(cooler_frames.N):
        for turn, _ in cooler_points(k):
            x, y, _z = s.polar(COOLER_R, cooler_frames.THETA[k] + turn, 0)
            assert math.hypot(x - ox, y - oy) > PLATE + .3, f"the overflow is too close to a pipe of cooler frame {k+1}"
