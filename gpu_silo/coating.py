"""Spray coating of the inside of the store, before it is filled. Short film only.

The concrete is not drawn in this part of the film, so the liner is shown as a tinted
film that climbs the two faces and is cleared again when the scene ends.
"""

from . import design as cfg
from . import film
from . import silo_model as s

D = cfg.PROJECT["coating"]
SPAN = tuple(f - film.LOADING for f in film.COATING_CUT)     # frames after the store is full
RISE = (SPAN[0] + 8, SPAN[1] - 24)
CLEAR = SPAN[1]
STAGES = D["stages"]
OFF = (0., 0., 0.)


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


def level(after):
    """Height the liner has reached, in frames after the store is full."""
    return s.WALL_HEIGHT * s.step(*RISE, after)


def install(scene, node, p):
    base = p.FILLED
    frames = range(SPAN[0] - 4, CLEAR + 1)
    node("Store liner", scene.mesh(liner_mesh()), "Store coating",
         tracks={"scale": [(0, OFF), (base + frames[0] - .02, OFF)] + [(base + f, (1, 1, max(.001, level(f)))) for f in frames[:-1]] + [(base + CLEAR, OFF)]})
    scene.project_info.update(storeLiner=D["system"], storeLinerThickness_mm=D["thickness_mm"], sprayStages=STAGES)
