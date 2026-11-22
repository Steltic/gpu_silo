"""Tables for the issued revision J design basis and the four crown checks."""
from . import completion as c, design as cfg


def section():
    decks,lat,seats,u,g=c.compute()
    aux=c.ancillary()
    rows=[]
    for i,(floor,seat) in enumerate(zip(decks,seats)):
        dims=c.D["turbine_box_m" if i else "diesel_box_m"]
        rows.append(f"| {'Turbine' if i else 'Diesel'} | {' × '.join(str(round(1000*x)) for x in dims)} | "
                    f"{floor['mass']:.1f} / {floor['budget']:.0f} | {floor['moment']:,.0f} / {floor['strength']:,.0f} | "
                    f"{floor['shear']:,.0f} / {floor['shear_strength']:,.0f} | {floor['deflection']:.1f} (L/{floor['span_ratio']:.0f}) | "
                    f"{floor['ring_m']:.0f} / {floor['ring_strength']:,.0f} |")
    mounts=[]
    for name,x in zip(("Rig","Turbine"),seats):
        mounts.append(f"| {name} | {x['v']:.0f} | {x['h']:.0f} | {x['t']:.0f} / {x['tension_cap']:,.0f} | "
                      f"{x['v']:.0f} / {x['key_cap']:,.0f} | {x['interaction']:.2f} | {x['weld_demand']:.0f} / {x['weld_cap']:,.0f} |")
    return f"""### 7.5 Checks 7 and 10 · Independent gravity floors

Each machine bears on fabricated box girders spanning to the open perimeter ring. Rail centrelines and actual skid positions are in the design inputs. Lower and upper mounting planes are independent. A simple span with 15% operating machinery allowance, full 120 t permanent floor budget and 2.5 kPa live load is used. For the member envelope all rail point loads move to midspan, and a conservative factor of 1.6 applies to all service forces for strength. The elastic box properties omit corner weld metal. The reaction calculation keeps the equipment at its actual horizontal position. Chord-end forces are distributed to the bracketing ring seats. Each floor balances the applied vertical load to numerical precision.

| Floor | Box width × depth × flange × web, mm | Primary steel / all-in budget, t | Rail moment / resistance, kN·m | Rail shear / resistance, kN | Service deflection, mm | Ring M / resistance, kN·m |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

The modeled 480 × 580 × 35 × 25 mm ring is discontinuous at the service wedge. Girders finish on the supported arc. The span limit is L/300. Provide transverse diaphragms at rail ends, skid feet and collar arms, 20 mm seat stiffeners, continuously welded box seams and positively restrained resilient machine mounts. The allowance above the primary steel takeoff covers diaphragms, shoes, decking, gratings and fittings. Obtain equipment foot reactions, operating frequencies and a floor modal analysis before releasing either deck. Raising the bolted lid by {c.D['roof_curb_m']:.2f} m gives 0.78 m nominal access above the turbine skid envelope.

### 7.6 Check 8 · Shaft-top guide

Four 280 × 380 × 20 × 16 mm box arms connect the split collar to the ring. Use four replaceable 200 × 300 × 15 mm preadjusted sliding pads, 0.20 mm maximum installed lateral play and ±{c.D['collar_travel_mm']:.0f} mm unobstructed vertical travel. The rig has no vertical shaft seat. Mechanical stops lie outside the operating travel. Require pad service-temperature compressive capacity ≥25 MPa. Bounded pressure is {lat['pad_pressure']:.1f} MPa. Design shaft force is {lat['shaft']:.0f} kN including the assumed acceleration and the uncontrolled loading envelope. A single arm carrying that force has {lat['arm_strength']:,.0f} kN compression resistance at the adopted pin-ended length.

Pad compression, axial arms, in-plane ring bending and the wall seats are springs in series. Their directional stiffnesses are {', '.join(f'{n:.0f}' for n in lat['components'])} kN/mm. The effective secant stiffness **including guide play** is {lat['k']:.1f} kN/mm at the uncontrolled service reaction, against 16 kN/mm required. Prove the assumed installed seat/pad stiffness and release of axial motion after welding. Do not load the first pod until the bare rig is seated and the guide engaged.

### 7.7 Checks 9 and 10 · Cast-in support groups

For the actual mount bearings, the lateral reaction in a radial seat of direction n is nᵀ(Σ n nᵀ)⁻¹H. The greatest share over all load directions is **{100*lat['fraction']:.2f}%**. The rig takes the factored shaft force and its own horizontal inertia. The upper mounts carry turbine floor inertia. The gravity envelope from §7.5 governs the most heavily loaded seats.

| Group | Peak vertical, kN | Peak horizontal, kN | Eccentric tension / resistance, kN | Bearing key force / resistance, kN | Combined bar utilisation | Weld force / resistance, kN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(mounts)}

Each 600 × 950 × 40 mm flush plate has eight 32 mm headed studs embedded 320 mm and a 520 × 120 mm bearing key. A 200 mm eccentricity over a 640 mm lever arm adds tension. Four developed two-legged 32 mm anchor hairpins transfer splitting and shear to both wall reinforcement mats. The tension resistance is the lesser of four engaged studs and four developed bar legs. Shear uses eight legs, with linear tension/shear interaction. A 16 mm effective-leg perimeter fillet transfers the shoe force. Cast plates stay flush with the wall. The lifted assembly retains at least 50 mm radial clearance. Fit and weld separate closure plates only after each floor has landed. The numerical checks depend on a fully developed reinforced load path in cracked concrete. Verify local strut bearing, edge distances, confinement, pryout, weld access, lift-joint proximity and anchorage development on the final detail before casting.

### 7.8 Site envelope and secondary checks

| Quantity | Calculated result | Adopted limit or disposition |
| --- | ---: | --- |
| Assumed equivalent lateral shear of facility and design wind resultant | {g['shear']:,.0f} and {g['wind']:.0f} kN | Base contact and sliding screened together |
| Contact pressure with lateral action | {g['qmin']:.0f}–{g['qmax']:.0f} kPa | 0–{c.SITE['allowable_bearing_kpa']} kPa |
| Friction resistance / demand at base | {g['sliding']:.2f} | ≥1.5 with μ = 0.35 |
| Slosh crest / hot free depth to underside of cover | {1000*g['crest']:.0f} / {1000*g['air']:.0f} mm | Reference long-period spectrum only |
| Combined shaft elastic stress / screening limit | {aux['shaft_stress']:.0f} / {aux['shaft_limit']:.0f} MPa | Gravity, eccentric operating loads and 0.05g inertia |
| Pod chord axial screening utilisation | {aux['chord_ratio']:.2f} | Gravity result with superposed transverse action |
| Primary cooler seat vertical / horizontal | {aux['frame_v']:.0f} / {aux['frame_h']:.0f} kN | Reinforced load path utilisation {aux['frame_ratio']:.2f} |
| Raft shear demand / reinforced strip resistance | {g['slab_shear']:.0f} / {g['ties']:.0f} kN/m | Two-legged 16 mm links at 400 × 400 mm |
| Shaft anchor steel per half-circle provided / required | {1e6*g['hairpins']:,.0f} / {1e6*g['shaft_req']:,.0f} mm² | Twenty-four two-legged hairpins overall |
| Pod / cooler branch velocity | {u['speeds'][0]:.2f} / {u['speeds'][1]:.2f} m/s | At 125 / 200 mm internal diameter |
| Pod / cooler calculated pump input | {u['pumps'][0]:.1f} / {u['pumps'][1]:.1f} kW | Design head 30 / 35 m at 75% efficiency |
| Normal auxiliary subtotal / allowance | {u['aux_mw']:.2f} / {c.MECH['facility_aux_mw']:.0f} MW | {u['pump_mw']:.2f} MW pumps, 30 × 45 kW fans, 0.40 MW other services including HVAC and 1.6% electrical losses |
| Normal / island / diesel-only IT limit | 50 / {u['island']:.0f} / {u['emergency']:.0f} MW | Thermal dispatch can require a lower limit |
| Two main buses / each transformer primary | {u['amps']:.0f} A each / {u['level_amps']:.0f} A | 1,600 / 400 A at 13.8 kV |
| Pod branch current / example cable drop | {aux['feeder_a']:.0f} A / {aux['bus_drop_pct']:.2f}% | 630 A plug, 120 m example, two parallel conductors per phase, 0.060 Ω/km each. Verify actual grouped ampacity and impedance |
| Layered, all coolers off | {u['ride']:.1f} min gross, {u['ride']*.98:.1f} min with 2% displacement allowance | 60 min target from a fully charged store |
| Bore room load / duty air handler | {u['bore']:.0f} / {c.MECH['ahu_kw']} kW | One additional standby unit |
| Controlled fill overrun / receiver | {u['catch']:.1f} / {cfg.PROJECT['thermal']['overflow']['catch_tank_m3']} m³ | Verify independent high-high trip |

The [assumption register](assumptions.md) records the site, procurement, programme and independent checks for this issue. The design actions and response spectrum need confirmation at a real location before the numerical results can be used there.
"""
