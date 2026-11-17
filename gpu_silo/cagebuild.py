"""The pod cage built beside the silo while the walls go up. Short film only.

One module is built each day of the jumpform: a level for each pod level and then the crown.
Its steel arrives on trucks, is welded together on a pad, lifted onto the stack by the south
crawler and welded on. The finished stack is the cage the two crawlers then lift into the silo.
"""
import math

from . import crew as people
from . import design as cfg
from . import silo_model as s
from . import site
from . import traffic

PAD = (0., -27.)
PAD_BEARING = 270.
REST = .25                 # a module stands this far off the pad on timber
SLING = 3.6
SECTORS = 8
ARRIVE = (5, 8, 11, 17, 20, 23, 29, 32)   # frames into the day at which each sector is on the pad
TRUCKS = cfg.PROJECT["logistics"]["cage"]["trucks_per_level"]
WELD_PAD = (12, 45)
HOOK_ON = 46
LIFT, SLEW, LOWER = (48, 57), (57, 69), (69, 77)
WELD_ON = (77, 84)
CLEAR = 1.6                # height above the stack at which a module travels
SPARK = "ffe9a0"
ON, OFF = (1., 1., 1.), (0., 0., 0.)


def day(m):
    """First frame of the day on which module m is built."""
    return s.INTRO + s.SLOW_CYCLE + m * s.FAST_CYCLE


def swap():
    """Frame at which the stack becomes the finished cage."""
    return s.LAST_POUR + 1


def offset(p, m, frame):
    """Translation of module m from its place in the finished stack: on the pad, in the air or seated."""
    cuts = p.cage_bounds()
    t = frame - day(m)
    low = REST - cuts[m]
    travel = s.step(*SLEW, t)
    z = low + (CLEAR - low) * s.step(*LIFT, t) - CLEAR * s.step(*LOWER, t)
    x = PAD[0] + (p.PICK_X - PAD[0]) * travel
    return (x, PAD[1] * (1 - travel), z)


def hook(p, frame):
    """The south crawler's hook while it builds the cage."""
    cuts = p.cage_bounds()
    m = max(0, min(p.CAGE_TOP - 1, (frame - day(0)) // s.FAST_CYCLE))
    t = frame - day(m)

    def carried(k, f):
        x, y, z = offset(p, k, f)
        return (x, y, cuts[k + 1] + z + SLING)
    if HOOK_ON <= t <= LOWER[1] + 2:
        return carried(m, frame)
    if t > LOWER[1] + 2:
        # Rise off the seated module. After the crown, wait where the tandem lift begins.
        a = carried(m, day(m) + LOWER[1] + 2)
        if m == p.CAGE_TOP - 1:
            q = s.step(day(m) + LOWER[1] + 2, p.C - 1, frame)
            return (p.PICK_X, -3.65 * q, a[2] + (p.CROWN + 4 - a[2]) * q)
        b = carried(m + 1, day(m + 1) + HOOK_ON)
        start, end = day(m) + LOWER[1] + 2, day(m + 1) + HOOK_ON
    else:
        b = carried(m, day(m) + HOOK_ON)
        if m == 0:
            return (b[0], b[1], b[2] + 7 * (1 - s.step(HOOK_ON - 14, HOOK_ON, t)))
        a = carried(m - 1, day(m - 1) + LOWER[1] + 2)
        start, end = day(m - 1) + LOWER[1] + 2, day(m) + HOOK_ON
    q = (frame - start) / (end - start)
    high = max(a[2], b[2]) + 5
    across = s.step(.18, .74, q)
    z = a[2] + (high - a[2]) * s.step(0, .22, q) + (b[2] - high) * s.step(.70, 1, q)
    return (a[0] + (b[0] - a[0]) * across, a[1] + (b[1] - a[1]) * across, z)


def split(mesh, name):
    """Divide a module into the sectors it arrives in."""
    pieces = [s.Mesh(f"{name} | sector {i+1}") for i in range(SECTORS)]
    for piece in pieces: piece.material = 3
    for a, b, c, colour in mesh.tris:
        angle = math.atan2((a[1] + b[1] + c[1]) / 3, (a[0] + b[0] + c[0]) / 3) % s.TAU
        pieces[min(SECTORS - 1, int(angle / s.TAU * SECTORS))].tris.append((a, b, c, colour))
    return pieces


def flicker(spans, phase):
    """Scale keys for a welding arc: lit in bursts inside each span of frames."""
    keys = [(0, OFF)]; lit = False
    for first, last in spans:
        for f in range(first, last + 2):
            now = f <= last and (f * 7 + phase * 3) % 5 < 3
            if now != lit:
                size = .7 + .5 * ((f * 13 + phase) % 4) / 3
                keys += [(f - .02, (size,) * 3 if lit else OFF), (f, (size,) * 3 if now else OFF)]
                lit = now
    return keys


def spark_mesh():
    m = s.Mesh("Welding arc | spark")
    for a in range(3):
        c, d = math.cos(a * math.pi / 3), math.sin(a * math.pi / 3)
        for w in (.34, .12):
            pts = [(-w * c, -w * d, .0), (w * c, w * d, .0), (w * c * .2, w * d * .2, w * 1.4), (-w * c * .2, -w * d * .2, w * 1.4)]
            m.face(pts, SPARK if w > .2 else "ffffff"); m.face(pts[::-1], SPARK if w > .2 else "ffffff")
    return m


def sling_mesh(height):
    m = s.Mesh("Cage module | four-leg sling"); m.material = 3
    for a in range(4):
        s.bar(m, s.polar(7.6, a * s.TAU / 4 + .4, height), (0, 0, height + SLING), .07, "766953")
    return m


def pad_mesh():
    m = s.Mesh("Cage assembly pad | gravel and timber"); m.material = 3
    s.sector(m, 0, 9.6, -.02, .012, 0, s.TAU, 24, ["c2b99f"] * 4, caps=False)
    for a in range(8):
        s.bar(m, s.polar(7.2, a * s.TAU / 8 + .2, REST / 2), s.polar(9.0, a * s.TAU / 8 + .2, REST / 2), .35, "8f8064", REST)
    return m


def install(scene, node, p):
    fleet = scene.fleet
    parts = p.cage_parts(); cuts = p.cage_bounds(); top = p.CAGE_TOP
    done = swap()
    shapes = {}       # module shape -> (mesh id, sector mesh ids, elevation the mesh is drawn at)
    for kind, k in (("base", 0), ("typical", 1), ("crown", top - 1)):
        shapes[kind] = (scene.mesh(parts[k]), [scene.mesh(piece) for piece in split(parts[k], parts[k].name)], cuts[k])
    node("Cage assembly pad", scene.mesh(pad_mesh()), "Cage build", t=(*PAD, 0), tracks={"scale": [(0, ON), (p.C - .02, ON), (p.C, OFF)]})
    route, stop = traffic.stop_route(PAD_BEARING)
    flat = fleet.mesh("flatbed", site.flatbed)
    bundle = fleet.mesh("bundle", traffic.bundle_mesh)
    arcs = fleet.mesh("spark", spark_mesh)
    slings = {}
    seated = []
    for m in range(top):
        kind = "base" if m == 0 else "crown" if m == top - 1 else "typical"
        whole, sectors, drawn = shapes[kind]
        lift = cuts[m] - drawn          # the shared level mesh is raised to this module's place
        start = day(m)
        label = f"Cage level {m+1:02}" if m < top - 1 else "Cage crown"
        for i in range(TRUCKS):
            at = start + 2 + 12 * i
            trip = site.Trip()
            traffic.come(trip, route, stop, at); traffic.go(trip, route, stop, at + 10)
            towed, _, _ = fleet.rig(f"{label} | steel delivery {i+1}", trip, flat, site.FLAT_AXLE, group="Cage build")
            node(f"{label} | steel on truck {i+1}", bundle, "Cage build", towed, t=(traffic.DECK_MID, 0, site.DECK), tracks={"scale": site.window(0, at + 4)})
        picked = start + HOOK_ON - 2
        low = REST - cuts[m]
        for i, piece in enumerate(sectors):
            node(f"{label} | sector {i+1} on the pad", piece, "Cage build", t=(PAD[0], PAD[1], low + lift),
                 tracks={"scale": site.window(start + ARRIVE[i], picked)})
        values = [offset(p, m, f) for f in range(picked, start + LOWER[1] + 1)]
        body = node(f"{label} | module", whole, "Cage build",
                    tracks={"translation": [(0, (PAD[0], PAD[1], low + lift))] + [(picked + k, (x, y, z + lift)) for k, (x, y, z) in p.flat_keys(values)],
                            "scale": site.window(picked, done)})
        height = round(cuts[m + 1] - lift, 3)
        if height not in slings: slings[height] = scene.mesh(sling_mesh(height))
        node(f"{label} | lifting sling", slings[height], "Cage build", body, tracks={"scale": site.window(picked, start + LOWER[1] + 3)})
        seated.append(start + LOWER[1])
    # Welding: on the pad as the sectors are joined, then round the stack as each module is welded on.
    for i in range(SECTORS):
        x, y, _ = s.polar(8.45, (i + .5) * s.TAU / SECTORS, 0)
        node(f"Cage build | pad weld {i+1}", arcs, "Welding", t=(PAD[0] + x, PAD[1] + y, 1.1 + .5 * (i % 3)),
             tracks={"scale": flicker([(day(m) + max(WELD_PAD[0], ARRIVE[i] + 3), day(m) + WELD_PAD[1]) for m in range(top)], i)})
    for i in range(6):
        x, y, _ = s.polar(8.5, i * s.TAU / 6 + .3, 0)
        heights = [(0, (p.PICK_X + x, y, .3))] + [(day(m) + LOWER[0], (p.PICK_X + x, y, max(.3, cuts[m] + .15))) for m in range(1, top)]
        steps = []
        for (f, v), (g, w) in zip(heights, heights[1:]): steps += [(f, v), (g - .02, v)]
        steps.append(heights[-1])
        node(f"Cage build | stack weld {i+1}", arcs, "Welding", tracks={"translation": steps,
             "scale": flicker([(day(m) + WELD_ON[0], day(m) + WELD_ON[1]) for m in range(top)], i + 2)})
    # Welders on the pad.
    poses = {}
    begin, end = day(0) + WELD_PAD[0] - 6, done
    for n in range(cfg.PROJECT["logistics"]["cage"]["welders"]):
        a = n * s.TAU / 4 + .5
        x, y, _ = s.polar(9.25, a, 0)
        actor = node(f"Cage build | welder {n+1}", -1, "Cage crew", ang=a + math.pi, t=(PAD[0] + x, PAD[1] + y, .02), tracks={"scale": site.window(begin, end)})
        count = people.MODES["inspect"]
        for index in range(count):
            key = (n % 3, "inspect", index)
            if key not in poses: poses[key] = scene.mesh(people.technician(*key))
            keys = [(0, ON if index == 0 else OFF)]
            for f in range(begin, end + 1):
                was, now = ((f - 1) // 3 + n) % count == index, (f // 3 + n) % count == index
                if was != now: keys += [(f - .025, ON if was else OFF), (f, ON if now else OFF)]
            node(f"Cage build | welder {n+1} | pose {index+1}", poses[key], "Cage crew poses", actor, tracks={"scale": keys})
    block = s.Mesh("Cage build | hook block"); block.material = 3
    s.box(block, -.22, -.17, .22, .17, -.07, .37, "d69751")
    node(block.name, scene.mesh(block), "Cage build", tracks={"translation": p.flat_keys([hook(p, f) for f in range(p.C)]), "scale": [(0, ON), (p.C - .02, ON), (p.C, OFF)]})
    scene.project_info.update(cageModules=top, cageBuiltBesideSilo=True, cageSteelTrucks=top * TRUCKS)
    return [sum(1 for f0 in seated if f >= f0) for f in range(p.FRAMES)]
