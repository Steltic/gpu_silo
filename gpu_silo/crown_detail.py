"""Crown seat reinforcement shared by the anchor calculation, the films and the IFC."""
import math

import numpy as np

from . import design as cfg

D = cfg.PROJECT["coordination"]["decks"]
WALL = cfg.PROJECT["structure"]["walls"]


def hairpin_path(offset):
    """Bar centreline in local radial, tangential and vertical metres from the bore at the seat."""
    near, far = D["hairpin_leg_depths_m"]
    shift = math.copysign(D["hairpin_tangent_offset_m"], offset)
    radius = math.hypot(far-near, shift)/2
    tangent_z = D["hairpin_top_m"]-radius
    tail_z = -D["hairpin_tail_below_seat_m"]
    points = [(near, offset, tail_z)]
    for i in range(25):
        angle = math.pi*i/24
        fraction = (1-math.cos(angle))/2
        points.append((near+(far-near)*fraction, offset+shift*fraction, tangent_z+radius*math.sin(angle)))
    points.append((far, offset+shift, tail_z))
    return points


def segment_distance(a,b,c,d):
    """Minimum distance of two finite centreline segments, including parallel segments."""
    u,v = b-a,d-c
    def point_distance(p, origin, direction):
        position = np.clip(np.dot(p-origin,direction)/np.dot(direction,direction),0,1)
        return np.linalg.norm(p-origin-position*direction)
    distance = min(point_distance(p,c,v) for p in (a,b))
    distance = min(distance, *(point_distance(p,a,u) for p in (c,d)))
    axes = np.column_stack((u,-v))
    t,_,rank,_ = np.linalg.lstsq(axes,c-a,rcond=None)
    if rank==2 and all(0 <= x <= 1 for x in t):
        distance = min(distance,np.linalg.norm(a-c+axes@t))
    return distance


def anchorage():
    db = D["anchor_rebar_mm"]/1000
    if WALL["fy_mpa"] > 420 or not .029 <= db <= .036:
        raise ValueError("Recheck the grade factor and bend diameter for the selected crown bar")
    near,far = D["hairpin_leg_depths_m"]
    radius = math.hypot(far-near,D["hairpin_tangent_offset_m"])/2
    paths = [np.array(hairpin_path(y)) for y in D["hairpin_near_leg_offsets_m"]]
    legs = [p[i,:2] for p in paths for i in (0,-1)]
    spacing = min(math.dist(p,q) for i,p in enumerate(legs) for q in legs[:i])
    # Far cover is measured to the curved wet face, including each tangential offset.
    bore = cfg.BORE_R
    wet_face = bore+cfg.SILO["inner_wall_m"]
    gross_cover = min(near, *(wet_face-math.hypot(bore+x,y) for x,y in legs))
    cb = min(gross_cover,spacing/2)
    factor = min(cb/db,2.5)
    # ACI 318M-19 §25.4.2.4. Grade 420 uncoated vertical bars, normal-weight concrete,
    # no transverse-confinement credit or reduction for excess reinforcement.
    required = max(.300, WALL["fy_mpa"]*db/(1.1*math.sqrt(WALL["concrete_fc_mpa"])*factor))
    embed = D["stud_embed_m"]
    bottom = min(D["stud_rows_m"])
    available = D["hairpin_tail_below_seat_m"]+bottom-1.5*embed
    # Use the full head diameter over the entire stud as a conservative clash envelope.
    axes = [(np.array((D["plate_thickness_m"],y,z)),np.array((embed,y,z)))
            for y in D["stud_columns_m"] for z in D["stud_rows_m"]]
    min_distance = min(segment_distance(a,b,c,d) for path in paths for a,b in zip(path,path[1:]) for c,d in axes)
    sagitta = radius*(1-math.cos(math.pi/48))
    stud_clear = min_distance-(db+D["stud_head_diameter_mm"]/1000)/2-sagitta
    key_clear = near-db/2-D["plate_thickness_m"]-D["key_width_projection_thickness_m"][1]
    return dict(db=db, required=required, available=available, cb=cb, bend=2*radius-db,
                cover=gross_cover-db/2, stud_clear=stud_clear, key_clear=key_clear)


def check():
    a = anchorage()
    assert a["available"] >= a["required"] and a["bend"] >= 8*a["db"]
    assert a["cover"] >= WALL["cover_mm"]/1000 and min(a["stud_clear"],a["key_clear"]) > 0


def cone_clearances(seat_z, bearings, hef):
    """Clearances of the projected eight-stud footprint to a lift joint and the adjacent group."""
    lift = cfg.SILO["concrete_lift_m"]
    low_joint = math.floor(seat_z/lift)*lift
    above = seat_z+max(D["stud_rows_m"])+1.5*hef
    below = seat_z+min(D["stud_rows_m"])-1.5*hef
    joint_margin = min(below-low_joint,low_joint+lift-above)
    gaps = np.diff([*bearings, bearings[0]+2*math.pi])
    pitch = 2*cfg.BORE_R*math.sin(min(gaps)/2)
    group_width = max(D["stud_columns_m"])-min(D["stud_columns_m"])+3*hef
    return joint_margin,pitch-group_width
