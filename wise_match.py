import os
import traceback

from astropy.table import Table
from astroquery.mpc import MPC


WISE_OBS_CODE = "C51"
CACHE_DIR = "./data/mpc_wise_xmatch_cache/"
DTYPE_MAP = {
    "absolute_magnitude": float,
    "aphelion_distance": float,
    "arc_length": float,
    "argument_of_perihelion": float,
    "ascending_node": float,
    "critical_list_numbered_object": bool,
    "delta_v": float,
    "designation": str,
    "earth_moid": str, # can be None
    "eccentricity": float,
    "epoch": str,
    "epoch_jd": str,
    "first_observation_date_used": "U",
    "first_opposition_used": str,
    "inclination": float,
    "jupiter_moid": str, # can be None
    "km_neo": bool,
    "last_observation_date_used": "U",
    "last_opposition_used": str,
    "mars_moid": str, # can be None
    "mean_anomaly": float,
    "mean_daily_motion": float,
    "mercury_moid": str, # can be None
    "name": "U", # None is not getting recasted
    "neo": bool,
    "number": "U", # something weird can happen to strings, cast None as None ()but not floats?)
    "observations": int,
    "oppositions": int,
    "orbit_type": int,
    "orbit_uncertainty": "U", # these are usually ints, but sometimes 'E', None is not recasted, so U
    "pha": bool,
    "phase_slope": float,
    "q_vector_x": float,
    "q_vector_y": float,
    "q_vector_z": float,
    "residual_rms": float,
    "saturn_moid": str, # can be None
    "semimajor_axis": float,
    "tisserand_jupiter": float,
    "updated_at": str,
    "uranus_moid": str, # can be None
    "venus_moid": str # can be None
}


def normalize_objects_table(tbl):
    for col, typ in DTYPE_MAP.items():
        if typ != "U" and isinstance(tbl[col][0], typ):
            continue
        else:
            try:
                tbl[col] = tbl[col].astype(typ)
            except ValueError as e:
                traceback.print_exc()
                raise ValueError(f"Can not cast {col}\n")

    return tbl


def get_distant_objects():
    fpath = os.path.join(CACHE_DIR, "distant_objects.fits.gz")
    if os.path.exists(fpath):
        distant_objects = Table.read(fpath)
    else:
        distant_objects = Table(MPC.query_objects("asteroid", orbit_type=10))
        distant_objects = normalize_objects_table(distant_objects)
        distant_objects.write(fpath)

    return distant_objects


def get_obj_observations(obj):
    match obj:
        case str():
            fpath = os.path.join(CACHE_DIR, obj)
        case _:
            fpath = os.path.join(CACHE_DIR, obj["number"])
    fpath += ".fits.gz"

    if os.path.exists(fpath):
        obj_obs = Table.read(fpath)
    else:
        obj_obs = MPC.get_observations(obj["number"])
        obj_obs.write(fpath)

    return obj_obs


def get_distant_obj_observed_by_wise():
    observed_objs = []
    distant_objects = get_distant_objects()
    totnobjs = len(distant_objects)
    for i, do in enumerate(distant_objects):
        print(f"Fetching {i}/{totnobjs}: Obj(name={do['name']}, number={do['number']})")
        # Sometimes the object has no name or number assigned to it,
        # which means we can't recover observations from MPC, we
        # skip those cases gracefully
        if do["number"] is None or do["number"] == "None":
            print(f"    Object name={do['name']} skipped. "
                  f"Cannot interpret target object number={do['number']}.")
            continue
        obs = get_obj_observations(do)

        # Annoyingly the returned types are not always the same, they get
        # casted as strings, sometimes int, sometimes it's a masked array
        # other times just an ndarray.
        loc_matches = obs["observatory"].astype(str) == WISE_OBS_CODE

        if isinstance(loc_matches, bool):
            # only 1 observation exists
            add_to_list = loc_matches
        else:
            # the return types here can be nearly any iterable (list, tuple, array)
            # for some reason - we try, in case observations come back as None
            # We attempt to fail gracefully.
            try:
                add_to_list = any(loc_matches)
            except TypeError:
                print(f"Object {do['number']} skipped. "
                      "Unrecognized returned observations format.\n"
                      f"Expected list or bool, got {type(loc_matches)} instead.")
                continue

        if add_to_list:
            observed_objs.append(obs)

        print("    Success.")

    print()
    objnums = [o["number"][0] for o in observed_objs]
    print(f"Found {len(objnums)} distant objects detected by WISE.")
    print("    ", objnums)
    return observed_objs


observed_objs = get_distant_obj_observed_by_wise()

breakpoint()
a = 1
a + 1
