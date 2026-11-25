"""Crown floor, guide, anchorage and site-envelope calculations for the design report."""
from . import completion as c, crown_detail, design as cfg, structure


def section():
    from . import plant
    decks,lat,seats,u,g=c.compute()
    aux=c.ancillary()
    rows=[]
    stages=[]
    local=[]
    concrete=[]
    bar=crown_detail.anchorage()
    for i,(floor,seat) in enumerate(zip(decks,seats)):
        dims=c.D["turbine_box_m" if i else "diesel_box_m"]
        name="Turbine" if i else "Diesel"
        stage=c.stage_envelope(i,floor)
        critical=", ".join(f"{j:02}" for j in floor["critical_seats"])
        stages.append(f"| {name} | {stage['cases']} | {stage['bare']:.0f} | {stage['one']:.0f} | "
                      f"{floor['mount']:.0f} | {critical} | {floor['rail_hz']:.2f} |")
        local.append(f"| {name} | {seat['stud']:.0f} / {seat['stud_strength']:.0f} | "
                     f"{seat['key_moment']:.1f} / {seat['key_strength']:.1f} | {seat['leg_interaction']:.2f} |")
        seat_z=plant.power_base(cfg.CROWN,i)+plant.SEAT_Z
        joint, adjacent=crown_detail.cone_clearances(seat_z,c.angles(len(floor['all_mounts'])),seat['hef'])
        concrete.append(f"| {name} | {seat['group_tension']:.0f} / {seat['breakout']:.0f} | "
                        f"{seat['stud']:.0f} / {seat['pullout']:.0f} | {joint:.2f} / {adjacent:.2f} |")
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

The staged check superposes each machine or full day tank on the bare floor at its assumed skid centre. Every subset balances the applied gravity load and every individual seat stays within its fully loaded vertical envelope. The 120 t floor allowance and 2.5 kPa live load apply at each stage. The bare lower rig also braces the shaft before delivery of the diesels.

| Floor | Equipment combinations | Bare peak, kN | Highest with one item, kN | Fully loaded peak, kN | Governing seat numbers | Lowest estimated loaded rail frequency, Hz |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
{chr(10).join(stages)}

All three reaction columns are factored. The indicated frequency uses a simply supported rail with a sine-shaped first mode, its share of the floor and live mass, and each machine mass at its own position. A resonance assessment needs the coupled floor, bearings, machine isolators, vendor forcing spectra and permissible vibration at the feet. [Steel design basis](https://www.aisc.org/aisc/publications/current-standards/aisc-360)

### 7.6 Check 8 · Shaft-top guide

Four 280 × 380 × 20 × 16 mm box arms connect the split collar to the ring. Use four replaceable 200 × 300 × 15 mm preadjusted sliding pads, 0.20 mm maximum installed lateral play and ±{c.D['collar_travel_mm']:.0f} mm unobstructed vertical travel. The rig has no vertical shaft seat. Mechanical stops lie outside the operating travel. Require pad service-temperature compressive capacity ≥25 MPa. Bounded pressure is {lat['pad_pressure']:.1f} MPa. Design shaft force is {lat['shaft']:.0f} kN including the assumed acceleration and the uncontrolled loading envelope. A single arm carrying that force has {lat['arm_strength']:,.0f} kN compression resistance at the adopted pin-ended length.

Pad compression, one arm per engaged axis, in-plane ring bending and the wall seats are springs in series. Their stiffnesses are {', '.join(f'{n:.0f}' for n in lat['components'])} kN/mm. With two orthogonal pad pairs, the greatest free lateral movement before engagement is √2 times the per-pad play, or {lat['deadband']:.3f} mm. The conservative secant stiffness is **{lat['k']:.1f} kN/mm** at the governing nonzero service load in §7.2 and {lat['uncontrolled_k']:.1f} kN/mm at the uncontrolled fill load. Both exceed the required 16 kN/mm. The section 5 shaft shortening is {1000*structure.C['shaft']['chosen']['movement']['shortening']:.2f} mm, within the specified minimum 2 mm free stroke and the modeled ±{c.D['collar_travel_mm']:g} mm travel. Verify pad modulus, play after welding, friction and free axial movement over the site settlement and temperature range. Engage the guide before hanging the first pod.

### 7.7 Checks 9 and 10 · Cast-in support groups

For the actual mount bearings, the lateral reaction in a radial seat of direction n is nᵀ(Σ n nᵀ)⁻¹H. The greatest share over all load directions is **{100*lat['fraction']:.2f}%**. The rig takes the factored shaft force and its own horizontal inertia. The upper mounts carry turbine floor inertia. The gravity envelope from §7.5 governs the most heavily loaded seats.

| Group | Peak vertical, kN | Peak horizontal, kN | Eccentric tension / resistance, kN | Key bearing / resistance, kN | Group bar utilisation | Peak weld line load / resistance, kN/m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(mounts)}

Each 600 × 950 × 40 mm flush plate has eight 32 mm headed studs and a bearing key. The group calculation uses four legs in tension and eight in shear. An additional check puts direct outward load into the four upper studs, distributes the moment from the 200 mm eccentricity in proportion to their distance above the lowest row, and combines the most loaded bar leg with its share of vertical shear. It assumes a rigid plate and an engaged lower compression toe. The key acts as a 60 mm thick cantilever with uniform underside bearing. The closure weld check uses direct shear plus the peak tension from direct force and eccentric bending on a 400 × 440 mm effective weld perimeter, with a 16 mm fillet leg.

| Group | Governing stud tension / resistance, kN | Key root moment / elastic resistance, kN·m | Governing bar-leg tension and shear utilisation |
| --- | ---: | ---: | ---: |
{chr(10).join(local)}

The stud tips now reach {1000*c.D['stud_embed_m']:.0f} mm behind the bore surface. Subtracting the recessed plate and the head thickness gives {1000*seats[0]['hef']:.0f} mm of effective embedment for the concrete check. The tension demand sums the row forces. For the two upper rows, the cracked-concrete breakout resistance uses their projected group area, the eccentricity of the tension resultant, normal-weight concrete and a 0.70 resistance factor. Single-head pullout uses the net head bearing area. The positive key carries gravity shear. These figures assume an uninterrupted concrete failure surface with clearance to free edges and other embeds.

| Group | Upper-row tension / concrete breakout resistance, kN | Peak stud tension / head pullout resistance, kN | Clear projection to nearest nominal lift joint / adjacent group, m |
| --- | ---: | ---: | ---: |
{chr(10).join(concrete)}

The revision J bar paths passed through the bearing key and two stud lines. The revised four U-bars per seat bend above the anchor group and run behind the key. The minimum calculated clearances are {1000*bar['key_clear']:.0f} mm to the key, {1000*bar['stud_clear']:.0f} mm to a conservative stud-head envelope, and {1000*bar['cover']:.0f} mm to the wall face. The inside bend diameter is {1000*bar['bend']:.0f} mm for a minimum 8 bar diameters.

For a conservative length check, measure the straight tail below the lowest stud and a further 1.5 times the full stud tip depth. This gives **{1000*bar['available']:.0f} mm available against {1000*bar['required']:.0f} mm required** for a straight Grade 420 bar. The calculation uses ACI 318M-19 §25.4.2.4, normal-weight concrete, uncoated vertical bars, no confinement credit, and the lesser of centre cover and half the leg spacing ({1000*bar['cb']:.0f} mm). The IFC contains the same bar layout. [ACI 318-19, chapters 17 and 25](https://www.concrete.org/Portals/0/Files/PDF/Previews/318-19_preview.pdf)

The wall detail relies on anchor reinforcement that intercepts the actual cracking surface and develops on both sides. The tail check covers the outside length. The lower bar tails cross a nominal construction joint and need continuity into the preceding lift. Verify the local compression strut and splitting resistance around the key, steel engagement inside the failure surface, actual edge distances, lift-joint transfer, connections into both wall mats, plate prying and weld access. Any shear assigned to the studs requires a corresponding concrete shear breakout, pryout and combined-load check. Survey fit after landing and before welding the closure. These conditions apply separately to the lower and upper groups.

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
| Installed rack design / normal IT ceiling / emergency priority IT | {c.calcs.C['heat_mw']:.0f} / {cfg.CLUSTER['normal_it_limit_mw']:g} / {u['emergency']:.0f} MW | Operator selects the rack mix. Turbine output and cooling can reduce normal IT. Diesels serve declared emergencies |
| Two main buses / each transformer primary | {u['amps']:.0f} A each / {u['level_amps']:.0f} A | 1,600 / 400 A at 13.8 kV |
| Pod branch current / example cable drop | {aux['feeder_a']:.0f} A / {aux['bus_drop_pct']:.2f}% | 630 A plug, 120 m example, two parallel conductors per phase, 0.060 Ω/km each. Verify actual grouped ampacity and impedance |
| Layered, all coolers off | {u['ride']:.1f} min gross, {u['ride']*.98:.1f} min with 2% displacement allowance | 60 min target from a fully charged store |
| Bore room load / duty air handler | {u['bore']:.0f} / {c.MECH['ahu_kw']} kW | One additional standby unit |
| Controlled fill overrun / receiver | {u['catch']:.1f} / {cfg.PROJECT['thermal']['overflow']['catch_tank_m3']} m³ | Verify independent high-high trip |

The [assumption register](assumptions.md) records the site, procurement, programme and independent checks for this issue. The design actions and response spectrum need confirmation at a real location before the numerical results can be used there.
"""
