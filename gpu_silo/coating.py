"""Spray coating of the inside of the store, before it is filled. Short film only.

Four stages hang in the gap between the walls and rise as their crews spray both faces.
The concrete is not drawn in this part of the film, so the liner is shown as a tinted
film that climbs the two faces and is cleared again when the scene ends.
"""
import math

from . import crew as people
from . import design as cfg
from . import film
from . import silo_model as s

D = cfg.PROJECT["coating"]
SPAN = tuple(f - film.LOADING for f in film.COATING_CUT)     # frames after the store is full
RISE = (SPAN[0] + 8, SPAN[1] - 24)
CLEAR = SPAN[1]
STAGES = D["stages"]
TURNS = .5
MID = (s.RO_INNER + s.RI_OUTER) / 2
ON, OFF = (1., 1., 1.), (0., 0., 0.)


def liner_mesh():
    """One metre of liner on both faces of the store. The node is scaled to the height reached."""
    m = s.Mesh("Store liner | sprayed on both faces of the gap")
    m.material = 6
    colour = D["colour"].lstrip("#")
    n = 72
    for radius in (s.RO_INNER + .02, s.RI_OUTER - .02):
        for i in range(n):
            a, b = s.TAU * i / n, s.TAU * (i + 1) / n
            quad = [s.polar(radius, a, 0), s.polar(radius, b, 0), s.polar(radius, b, 1), s.polar(radius, a, 1)]
            m.face(quad, colour); m.face(quad[::-1], colour)
    return m


def stage_mesh():
    m = s.Mesh("Spray stage | suspended platform with rails and spray lances")
    m.material = 3
    half = math.radians(11)
    s.sector(m, s.RO_INNER + .35, s.RI_OUTER - .35, -.12, 0, -half, half, 4, ["8f8064"] * 4)
    for radius in (s.RO_INNER + .4, s.RI_OUTER - .4):
        for a in (-half, 0, half):
            s.bar(m, s.polar(radius, a, 0), s.polar(radius, a, 1.1), .05, "e2bd76")
        for z in (.55, 1.08):
            s.bar(m, s.polar(radius, -half, z), s.polar(radius, half, z), .04, "e2bd76")
    # A fan of spray toward each wall.
    for radius, face in ((s.RO_INNER + .45, s.RO_INNER + .03), (s.RI_OUTER - .45, s.RI_OUTER - .03)):
        for a in (-half * .5, half * .5):
            tip = s.polar(radius, a, 1.25)
            fan = [tip, s.polar(face, a - .05, .7), s.polar(face, a + .05, .7), s.polar(face, a + .05, 1.8), s.polar(face, a - .05, 1.8)]
            for i in range(1, 4):
                m.face([fan[0], fan[i], fan[i + 1]], "d8efe9"); m.face([fan[0], fan[i + 1], fan[i]], "d8efe9")
    return m


def cable_mesh():
    m = s.Mesh("Spray stage | one metre of suspension cable")
    m.material = 3
    half = math.radians(9)
    for a in (-half, half):
        x, y, _ = s.polar(MID, a, 0)
        s.box(m, x - .025, y - .025, x + .025, y + .025, 0, 1, "5d5445")
    return m


def level(after):
    """Height the liner has reached, in frames after the store is full."""
    return s.WALL_HEIGHT * s.step(*RISE, after)


def install(scene, node, p):
    base = p.FILLED
    frames = range(SPAN[0] - 4, CLEAR + 1)
    seen = [(0, OFF), (base + SPAN[0] - 4.02, OFF), (base + SPAN[0] - 4, ON), (base + CLEAR - .02, ON), (base + CLEAR, OFF)]
    node("Store liner", scene.mesh(liner_mesh()), "Store coating",
         tracks={"scale": [(0, OFF), (base + frames[0] - .02, OFF)] + [(base + f, (1, 1, max(.001, level(f)))) for f in frames[:-1]] + [(base + CLEAR, OFF)]})
    turn = node("Spray stages | carrier", -1, "Store coating",
                tracks={"yaw": [(0, (0.,))] + [(base + f, (s.TAU * TURNS * s.step(*RISE, f),)) for f in frames], "scale": seen})
    stage, cable = scene.mesh(stage_mesh()), scene.mesh(cable_mesh())
    poses = {}
    for n in range(STAGES):
        a = n * s.TAU / STAGES + .4
        heights = [(base + f, (0, 0, min(s.WALL_HEIGHT - 1.4, level(f)))) for f in frames]
        deck = node(f"Spray stage {n+1}", stage, "Store coating", turn, ang=a, tracks={"translation": [(0, heights[0][1])] + heights})
        node(f"Spray stage {n+1} | cables", cable, "Store coating", deck,
             tracks={"scale": [(0, (1, 1, s.WALL_HEIGHT))] + [(f, (1, 1, max(.2, s.WALL_HEIGHT + .6 - v[2]))) for f, v in heights]})
        actor = node(f"Spray stage {n+1} | sprayer", -1, "Coating crew", deck, ang=(0 if n % 2 else math.pi), t=(MID, 0, 0))
        count = people.MODES["inspect"]
        for index in range(count):
            key = (n % 3, "inspect", index)
            if key not in poses: poses[key] = scene.mesh(people.technician(*key))
            keys = [(0, ON if index == 0 else OFF)]
            for f in frames:
                was, now = ((f - 1) // 3 + n) % count == index, (f // 3 + n) % count == index
                if was != now: keys += [(base + f - .025, ON if was else OFF), (base + f, ON if now else OFF)]
            node(f"Spray stage {n+1} | sprayer | pose {index+1}", poses[key], "Coating crew poses", actor, tracks={"scale": keys})
    scene.project_info.update(storeLiner=D["system"], storeLinerThickness_mm=D["thickness_mm"], sprayStages=STAGES)
