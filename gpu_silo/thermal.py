"""Check 5: heat balance of the store.

The store is the water-glycol between the two walls. The pods put heat into it through their CDUs and
the dry coolers take heat out of it. This module works out the temperatures the store has to run at,
what the coolers can reject at a given outside air temperature, how long the store carries the load,
how far the liquid rises as it warms, and the temperatures of the two walls.

SI units: kelvin differences, degrees Celsius, watts, metres.
"""
import math

from . import design as cfg
from . import structure
from . import walls

T = cfg.PROJECT["thermal"]
AMBIENT = T["ambient"]
CONCRETE = T["concrete"]
FILMS = T["films_w_m2k"]
COOL = cfg.COOL
RISE = cfg.FLUID["loop_delta_t_k"]
HEAT = cfg.RACKS * cfg.CLUSTER["liquid_heat_per_rack_kw"] * 1e3          # W, from the racks
LOAD = HEAT * (1 + T["pump_heat_fraction"])                               # W, to reject
COLD = T["rack_supply_limit_c"] - T["cdu_approach_k"]                     # warmest the store may supply
HOT = COLD + RISE                                                         # what comes back from the pods
MEAN = (COLD + HOT) / 2
CAPACITY = cfg.FLUID["density_kg_m3"] * cfg.FLUID["specific_heat_kj_kgk"] * 1e3      # J/m³·K, as the other calculations
FOM = T["stratification_figure_of_merit"]
INSTALLED = cfg.COOLERS
ALPHA = CONCRETE["expansion_per_k"]

# One dry cooler, from its rating.
Q_RATED = COOL["cooler_capacity_mw"] * 1e6
C_LIQUID = Q_RATED / RISE                                                 # W/K, liquid at rated flow
C_AIR = Q_RATED / COOL["air_rise_k"]                                      # W/K, air at full fan speed
ITD_RATED = T["cooler_rating"]["liquid_in_c"] - T["cooler_rating"]["air_in_c"]
EPS_RATED = Q_RATED / (min(C_LIQUID, C_AIR) * ITD_RATED)
DUTY = math.ceil(LOAD / Q_RATED - 1e-9)                                   # coolers running when each gives its rating


def effectiveness(ntu, ratio):
    """Counterflow heat exchanger."""
    if abs(1 - ratio) < 1e-9: return ntu / (1 + ntu)
    e = math.exp(-ntu * (1 - ratio))
    return (1 - e) / (1 - ratio * e)


def transfer_units(eps, ratio):
    if abs(1 - ratio) < 1e-9: return eps / (1 - eps)
    return math.log((1 - eps * ratio) / (1 - eps)) / (1 - ratio)


RATIO_RATED = min(C_LIQUID, C_AIR) / max(C_LIQUID, C_AIR)
UA = transfer_units(EPS_RATED, RATIO_RATED) * min(C_LIQUID, C_AIR)        # W/K, taken as fixed by the coil and the air flow


def density(t):
    table = T["fluid"]["density_by_temperature"]
    for (t0, r0), (t1, r1) in zip(table, table[1:]):
        if t <= t1 or (t1, r1) == tuple(table[-1]):
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)


def cooler(liquid_in, air_in, flow=1.):
    """Heat rejected by one cooler at full fan speed, and the temperature of the liquid leaving it. Flow is a fraction of rated."""
    c = C_LIQUID * flow
    low, high = min(c, C_AIR), max(c, C_AIR)
    q = effectiveness(UA / low, low / high) * low * (liquid_in - air_in)
    return q, liquid_in - q / c


def cooler_duty(liquid_in, liquid_out, air_in):
    """Most heat one cooler rejects while it returns liquid no warmer than liquid_out. The liquid flow is turned down to suit."""
    if liquid_out <= air_in: return 0., 0.
    if cooler(liquid_in, air_in)[1] <= liquid_out:
        return C_LIQUID * (liquid_in - liquid_out), 1.          # full flow, fans turned down
    low, high = 1e-6, 1.
    for _ in range(60):
        mid = (low + high) / 2
        if cooler(liquid_in, air_in, mid)[1] <= liquid_out: low = mid
        else: high = mid
    return C_LIQUID * low * (liquid_in - liquid_out), low


def stratified_capacity(air, coolers=INSTALLED):
    """Heat the plant rejects with the store layered: coolers draw the warm layer and return the cool one."""
    return coolers * cooler_duty(HOT, COLD, air)[0]


def mixed_store(air, coolers=INSTALLED, load=LOAD):
    """Temperature a fully mixed store settles at. The coolers draw liquid at the temperature the pods are supplied with."""
    return air + load / (coolers * cooler(1., 0.)[0])


def air_limit(coolers, mixed=False):
    """Warmest outside air at which the coolers carry the whole load and the supply stays within its limit."""
    if mixed: return COLD - LOAD / (coolers * cooler(1., 0.)[0])
    low, high = -60., COLD
    for _ in range(60):
        mid = (low + high) / 2
        if stratified_capacity(mid, coolers) >= LOAD: low = mid
        else: high = mid
    return low


def ride(volume):
    """How long a store of this volume carries the load, in seconds."""
    energy = volume * CAPACITY                                  # J/K
    layered = FOM * energy * RISE / LOAD
    mixed = {key: max(0., COLD - mixed_store(AMBIENT[key])) * energy / LOAD for key in ("annual_mean_c", "summer_design_c")}
    hot = stratified_capacity(AMBIENT["extreme_hot_c"])
    day = stratified_capacity(AMBIENT["summer_design_c"])
    night = stratified_capacity(AMBIENT["summer_design_c"] - AMBIENT["daily_range_k"])
    return dict(volume=volume, energy=energy, per_k=energy / LOAD, layered=layered, mixed=mixed,
                day_capacity=day, day=FOM * energy * RISE / (LOAD - day) if day < LOAD else float("inf"),
                hot_capacity=hot, hot=FOM * energy * RISE / (LOAD - hot) if hot < LOAD else float("inf"),
                night_capacity=night, recharge=FOM * energy * RISE / (night - LOAD) if night > LOAD else float("inf"))


def through(thickness, liquid, air, film, insulated=False):
    """Steady heat flow through a wall with liquid on one face, and the temperatures of the concrete faces."""
    liner = cfg.PROJECT["coating"]["thickness_mm"] / 1000 / T["liner_conductivity_w_mk"]
    inside = 1 / FILMS["liquid"] + liner
    concrete = thickness / CONCRETE["conductivity_w_mk"]
    outside = 1 / film + (T["insulation"]["thickness_mm"] / 1000 / T["insulation"]["conductivity_w_mk"] if insulated else 0)
    flux = (liquid - air) / (inside + concrete + outside)
    wet = liquid - flux * inside
    dry = wet - flux * concrete
    return dict(flux=flux, wet=wet, dry=dry, gradient=wet - dry, mean=(wet + dry) / 2, u=1 / (inside + concrete + outside))


def bar_stress(thickness, depth, gradient, modulus):
    """Change of stress in a hoop bar at this depth from the cold face, in a wall cracked through, from a gradient across the wall.

    A ring cannot change its curvature, so the strain is the same across the wall. The cold face wants to be
    shorter, so its bars are stretched by α ΔT times their distance from the middle of the wall over the thickness.
    """
    return modulus * ALPHA * gradient * (thickness / 2 - depth) / thickness


def creep_at(temperature):
    """Creep coefficient for concrete held at this temperature, from the one used at 20 °C. fib Model Code 2010, effect of temperature on creep."""
    return walls.W["inner_wall_buckling"]["creep_coefficient"] * math.exp(CONCRETE["creep_per_k_above_20c"] * (temperature - 20))


def calcs_volume():
    """The store with the walls in the design file."""
    return math.pi * ((walls.R_OUT - cfg.SILO["outer_wall_m"])**2 - (walls.R_BORE + cfg.SILO["inner_wall_m"])**2) * walls.LIQUID


def compute():
    c = dict(heat=HEAT, load=LOAD, cold=COLD, hot=HOT)
    c["flow"] = LOAD / (cfg.FLUID["specific_heat_kj_kgk"] * 1e3 * RISE)                       # kg/s through the pods
    c["cooler"] = dict(eps=EPS_RATED, ntu=UA / min(C_LIQUID, C_AIR), ua=UA, itd=ITD_RATED, approach=T["cooler_rating"]["liquid_in_c"] - RISE - T["cooler_rating"]["air_in_c"])
    c["limit"] = {(n, mixed): air_limit(n, mixed) for n in (DUTY, INSTALLED) for mixed in (False, True)}
    c["mixed_coolers"] = math.ceil(LOAD / (cooler(1., 0.)[0] * (COLD - AMBIENT["summer_design_c"])) - 1e-9)
    rows = []
    for air in sorted({AMBIENT["winter_design_c"], 0., AMBIENT["annual_mean_c"], 25., 30., AMBIENT["summer_design_c"], AMBIENT["extreme_hot_c"]}):
        each, flow = cooler_duty(HOT, COLD, air)
        rows.append(dict(air=air, each=each, flow=flow, capacity=INSTALLED * each, needed=math.ceil(LOAD / each - 1e-9) if each else None,
                         mixed=mixed_store(air), mixed_duty=mixed_store(air, DUTY)))
    c["rows"] = rows
    c["rides"] = dict(drawn=ride(walls.C["now_volume"]), proposed=ride(walls.C["volume"]), adopted=ride(calcs_volume()))

    # Layering: the height of opening that lets the flow enter without stirring the layers (densimetric Froude number of 1).
    buoyancy = walls.G * (density(COLD) - density(HOT)) / density(MEAN)
    volume_flow = c["flow"] / density(MEAN)
    ring = 2 * math.pi * (walls.R_OUT + walls.R_BORE) / 2
    per_metre = volume_flow / (2 * ring)                       # the flow leaves a ring both ways
    c["layering"] = dict(buoyancy=buoyancy, difference=density(COLD) - density(HOT), flow=volume_flow, ring=ring,
                         opening=(per_metre**2 / buoyancy)**(1 / 3), conduction=math.sqrt(4 * 1.5e-7 * 86400))

    # The pipes as modelled: one pair for each bay of pods and one for each cooler frame, every open end facing a plate.
    pipes = T["layering"]
    bore = math.pi * (pipes["riser_diameter_m"] / 2 - pipes["riser_wall_mm"] / 1000)**2
    edge = math.pi * pipes["diffuser_diameter_m"]
    def froude(count): return volume_flow / (count * edge) / math.sqrt(buoyancy * pipes["diffuser_gap_m"]**3)
    c["pipes"] = dict(pairs=cfg.BAYS + cfg.FRAMES, pod_speed=volume_flow / cfg.BAYS / bore, cooler_speed=volume_flow / cfg.FRAMES / bore,
                      warm_froude=froude(cfg.BAYS), cool_froude=froude(cfg.FRAMES))

    # The liquid swells as it warms.
    depth, fill = walls.LIQUID, T["fill_temperature_c"]
    c["swell"] = dict(fill=fill, to_cold=depth * (density(fill) / density(COLD) - 1), to_hot=depth * (density(fill) / density(HOT) - 1),
                      cold_to_hot=depth * (density(COLD) / density(HOT) - 1), per_k=depth * (density(MEAN - .5) / density(MEAN + .5) - 1),
                      freeboard=cfg.FLUID["freeboard_m"], density=density(MEAN), density_fill=density(fill),
                      capacity=density(MEAN) * T["fluid"]["specific_heat_at_50c_kj_kgk"] * 1e3)

    # Walls. The outer wall as proposed in check 3, lift by lift, on the winter design day with the wind blowing.
    winter, summer, mean_air = AMBIENT["winter_design_c"], AMBIENT["summer_design_c"], AMBIENT["annual_mean_c"]
    lifts = []
    for lift in walls.C["lifts"]:
        wet = max(0., min(lift["z1"], walls.LIQUID) - lift["z0"])
        area = 2 * math.pi * walls.R_OUT * wet
        bare = through(lift["t"], HOT, winter, FILMS["outside_wind"])
        clad = through(lift["t"], HOT, winter, FILMS["outside_wind"], True)
        lifts.append(dict(lift=lift["lift"], t=lift["t"], area=area, bare=bare, clad=clad,
                          mean_loss=area * through(lift["t"], MEAN, mean_air, FILMS["outside_still"])["flux"],
                          mean_loss_clad=area * through(lift["t"], MEAN, mean_air, FILMS["outside_still"], True)["flux"]))
    c["lifts"] = lifts
    c["outer_loss"] = dict(winter=sum(l["area"] * l["bare"]["flux"] for l in lifts), winter_clad=sum(l["area"] * l["clad"]["flux"] for l in lifts),
                           mean=sum(l["mean_loss"] for l in lifts), mean_clad=sum(l["mean_loss_clad"] for l in lifts))
    inner_t = walls.C["inner"]["t"]
    bore = through(inner_t, MEAN, T["bore_air_c"], FILMS["bore"])
    bore_area = 2 * math.pi * walls.R_BORE * walls.LIQUID
    c["inner"] = dict(t=inner_t, wall=bore, area=bore_area, heat=bore["flux"] * bore_area,
                      per_k=bore["u"] * bore_area, hot=through(inner_t, HOT, T["bore_air_c"], FILMS["bore"]))
    energy = c["rides"]["proposed"]["energy"]
    c["idle"] = dict(rate=(c["outer_loss"]["winter"] + bore["u"] * bore_area * (MEAN - winter)) / energy * 86400,
                     rate_clad=(c["outer_loss"]["winter_clad"] + bore["u"] * bore_area * (MEAN - winter)) / energy * 86400)

    # Evaporation from the surface of the store if it were left open. ASHRAE pool formula for still air, in kg/s.
    def vapour(t): return .61094 * math.exp(17.625 * t / (t + 243.04))        # kPa, Magnus
    surface = math.pi * ((walls.R_OUT - walls.C["lifts"][-1]["t"])**2 - (walls.R_BORE + inner_t)**2)
    latent = 2.38e6
    rate = surface * (vapour(HOT) - .5 * vapour(20.)) * .089 / (latent / 1e3)       # kg/s, air at 20 °C and 50% humidity
    c["evaporation"] = dict(surface=surface, rate=rate, heat=rate * latent)

    warm_t = walls.inner_wall(creep_at(bore["mean"]))["t"]
    # Movement of the walls against the steel inside them.
    erect, steel = T["erection_temperature_c"], T["steel_expansion_per_k"]
    top_pod = structure.level_height(cfg.LEVELS)
    wall_rise = ALPHA * (bore["mean"] - erect)
    shaft_rise = steel * (T["bore_air_c"] - erect)
    squeeze = {}
    for level in (1, cfg.LEVELS):
        z = structure.level_height(level)
        stress = walls.pressure(z) * (walls.R_BORE + warm_t) / warm_t
        squeeze[level] = dict(z=z, elastic=stress / walls.EC * walls.R_BORE, creep=stress / walls.EC * (1 + creep_at(bore["mean"])) * walls.R_BORE)
    c["squeeze"] = squeeze
    c["movement"] = dict(top_pod=top_pod, wall_mean=bore["mean"], wall_pod=wall_rise * top_pod, shaft_pod=shaft_rise * top_pod,
                         wall_rig=wall_rise * structure.SHAFT_TOP, shaft_rig=shaft_rise * structure.SHAFT_TOP,
                         bore=wall_rise * walls.R_BORE, pod=shaft_rise * structure.TIP_R,
                         outer=ALPHA * (through(walls.C["lifts"][0]["t"], COLD, summer, FILMS["outside_still"])["mean"] - erect) * walls.R_OUT)

    # The inner wall: creep is faster in warm concrete, and creep sets its buckling pressure.
    creep = creep_at(bore["mean"])
    warm = walls.inner_wall(creep)
    c["creep"] = dict(cold=walls.W["inner_wall_buckling"]["creep_coefficient"], warm=creep, t=warm["t"], design=walls.buckling(inner_t, creep)[1],
                      demand=walls.LOAD * walls.pressure(0))

    fluid = T["fluid"]
    c["freeze"] = dict(freeze=fluid["freeze_point_c"], burst=fluid["burst_point_c"], winter=winter,
                       slush=winter < fluid["freeze_point_c"], bursts=winter < fluid["burst_point_c"])
    return c


C = compute()


def check():
    c = C
    # The cooler model returns its rating at its rated condition.
    rated, out = cooler(T["cooler_rating"]["liquid_in_c"], T["cooler_rating"]["air_in_c"])
    assert abs(rated - Q_RATED) < 1e-6 * Q_RATED and abs(out - (T["cooler_rating"]["liquid_in_c"] - RISE)) < 1e-6
    # Energy balance at the air limit: the coolers reject exactly the load.
    for coolers in (DUTY, INSTALLED):
        assert abs(stratified_capacity(c["limit"][coolers, False], coolers) - LOAD) < 1e-6 * LOAD
        assert abs(mixed_store(c["limit"][coolers, True], coolers) - COLD) < 1e-9
    # A layered store always does better than a mixed one, by about the rise across the pods.
    assert all(c["limit"][n, False] > c["limit"][n, True] for n in (DUTY, INSTALLED))
    # Heat flow through a wall is the same through each layer.
    wall = c["lifts"][0]["bare"]
    assert abs(wall["flux"] - wall["gradient"] * CONCRETE["conductivity_w_mk"] / c["lifts"][0]["t"]) < 1e-9 * wall["flux"]
    assert 0 < FOM <= 1 and COLD < HOT
    # The openings of the store pipes are slow enough not to stir the layers.
    assert max(c["pipes"]["warm_froude"], c["pipes"]["cool_froude"]) <= 1, "the openings of the store pipes are too small to keep the store layered"


def summary():
    c = C
    return (f"Store: supply {COLD:.0f} °C, return {HOT:.0f} °C. Layered, {INSTALLED} coolers carry {LOAD/1e6:.2f} MW up to {c['limit'][INSTALLED, False]:.1f} °C outside; "
            f"mixed, only up to {c['limit'][INSTALLED, True]:.1f} °C. Ride-through {c['rides']['adopted']['layered']/60:.0f} min layered.")
