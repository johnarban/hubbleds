from cosmicds.utils import API_URL
from cosmicds.state import GLOBAL_STATE
from .utils import HUBBLE_ROUTE_PATH
from .data_models.student import student_data, StudentMeasurement, example_data
from contextlib import closing
from io import BytesIO
from astropy.io import fits
from .state import LOCAL_STATE
import datetime
from .data_management import DB_VELOCITY_FIELD

from numpy.random import Generator, PCG64, SeedSequence
from numpy import arange, asarray
from typing import Any

ELEMENT_REST = {"H-α": 6562.79, "Mg-I": 5176.7}


class DatabaseAPI:
    @staticmethod
    def _load_spectrum_data(gal_info):
        file_name = f"{gal_info['name'].replace('.fits', '')}.fits"
        gal_type = gal_info["type"]

        print(file_name)

        type_folders = {"Sp": "spiral", "E": "elliptical", "Ir": "irregular"}
        folder = type_folders[gal_type]
        url = f"{API_URL}/{HUBBLE_ROUTE_PATH}/spectra/{folder}/{file_name}"
        response = GLOBAL_STATE.request_session.get(url)

        print(response)

        with closing(BytesIO(response.content)) as f:
            f.name = gal_info["name"]

            with fits.open(f) as hdulist:
                data = hdulist["COADD"].data if "COADD" in hdulist else None

        if data is None:
            print("No extension named 'COADD' in spectrum fits file.")
            return

        spec_data = dict(
            name=gal_info["name"],
            wave=10 ** data["loglam"],
            flux=data["flux"],
            ivar=data["ivar"],
        )

        return spec_data

    @staticmethod
    def _parse_measurement(measurement):
        meas_dict = {}

        for k, v in measurement.items():
            if not (k.endswith("_value") or k == "galaxy"):
                continue

            meas_dict[k.replace("_value", "")] = v

            if k != "galaxy":
                continue

            gal_dict = {}

            for gk, gv in v.items():
                if gk in ["galaxy_id", "id"]:
                    gk = "id"
                    gv = str(gv)

                gal_dict[gk] = gv

            gal_dict["spectrum"] = DatabaseAPI._load_spectrum_data(gal_dict)

            meas_dict[k] = gal_dict

        return meas_dict

    @staticmethod
    def get_measurements(samples=False):
        url = f"{API_URL}/{HUBBLE_ROUTE_PATH}/{'sample-' if samples else ''}measurements/{GLOBAL_STATE.student.id.value}"
        r = GLOBAL_STATE.request_session.get(url)
        res_json = r.json()

        measurements = []

        for measurement in res_json["measurements"]:
            meas_dict = DatabaseAPI._parse_measurement(measurement)

            measurement = StudentMeasurement(**meas_dict)
            measurements.append(measurement)

        return measurements

    @staticmethod
    def put_measurements(samples=False):
        url = f"{API_URL}/{HUBBLE_ROUTE_PATH}/{'sample' if samples else 'submit'}-measurement/"
        data = example_data if samples else student_data

        for measurement in data.measurements:
            sub_dict = {
                "student_id": GLOBAL_STATE.student.id.value,
                "galaxy_id": int(measurement.galaxy.id),
                "rest_wave_value": measurement.rest_wave,
                "rest_wave_unit": "angstrom",
                "obs_wave_value": measurement.obs_wave,
                "obs_wave_unit": "angstrom",
                "velocity_value": measurement.velocity,
                "velocity_unit": "km / s",
                "ang_size_value": measurement.ang_size,
                "ang_size_unit": "arcsecond",
                "est_dist_value": measurement.est_dist,
                "est_dist_unit": "Mpc",
                "brightness": 1,
                "last_modified": f"{datetime.datetime.now(datetime.UTC)}",
                "galaxy": {
                    "id": measurement.galaxy.id,
                    "ra": measurement.galaxy.ra,
                    "decl": measurement.galaxy.decl,
                    "z": measurement.galaxy.z,
                    "type": measurement.galaxy.type,
                    "name": measurement.galaxy.name,
                    "element": measurement.galaxy.element,
                },
            }

            r = GLOBAL_STATE.request_session.put(url, json=sub_dict)

    @staticmethod
    def get_measurement(galaxy_id, samples=False):
        url = f"{API_URL}/{HUBBLE_ROUTE_PATH}/{'sample-' if samples else ''}measurements/{GLOBAL_STATE.student.id.value}/{galaxy_id}"
        r = GLOBAL_STATE.request_session.get(url)
        res_json = r.json()

        meas_dict = DatabaseAPI._parse_measurement(res_json["measurement"])

        measurement = StudentMeasurement(**meas_dict)

        return measurement

    @staticmethod
    def delete_all_measurements(samples=False):
        url = f"{API_URL}/{HUBBLE_ROUTE_PATH}/{'sample-' if samples else ''}measurements/{GLOBAL_STATE.student.id.value}"
        r = GLOBAL_STATE.request_session.get(url)
        res_json = r.json()

        for measurement in res_json["measurements"]:
            # NOTE: FOR DELETING DB MEASUREMENTS
            url = f"{API_URL}/{HUBBLE_ROUTE_PATH}/{'sample-' if samples else ''}measurement/{GLOBAL_STATE.student.id.value}"
            url = url + "/first" if samples else url + f"/{measurement['galaxy']['id']}"
            r = GLOBAL_STATE.request_session.delete(url)
            print("Deleted ", r)

    @staticmethod
    def get_sample_galaxy():
        example_galaxy_data = GLOBAL_STATE.request_session.get(
            f"{API_URL}/{HUBBLE_ROUTE_PATH}/sample-galaxy"
        ).json()

        example_galaxy_data = {k: example_galaxy_data[k] for k in example_galaxy_data}
        example_galaxy_data["id"] = str(example_galaxy_data["id"])
        example_galaxy_data["name"] = example_galaxy_data["name"].replace(".fits", "")

        # Load the spectrum associated with the example data
        spec_data = DatabaseAPI._load_spectrum_data(example_galaxy_data)
        example_galaxy_data["spectrum"] = spec_data

        return {
            "rest_wave": round(ELEMENT_REST[example_galaxy_data["element"]]),
            "galaxy": example_galaxy_data,
        }

    @staticmethod
    def get_story_state(component_state):
        r = GLOBAL_STATE.request_session.get(
            f"{API_URL}/story-state/{GLOBAL_STATE.student.id.value}/hubbles_law"
        )
        res_json = r.json()

        try:
            app_state = res_json["state"]["app"]
            story_state = res_json["state"]["story"]
            stage_state = res_json["state"]["stage"][
                f"{component_state.stage_name.value}"
            ]
        except Exception as e:
            print(f"Stored DB state is malformed; failed to load.\n{e}")
            return

        # NOTE: the way the loading from a dict works, solara with trigger
        #  the reactive variables one after another, as there are loaded from
        #  the database. It is possible that `current_step` will be set early,
        #  and that some other event will cause it to revert to an early step.
        #  To avoid this, remove `current_step` and re-add it as the last one.
        stage_step = stage_state.pop("current_step")
        stage_state.update(
            {"current_step": component_state.current_step.value.__class__(stage_step)}
        )

        GLOBAL_STATE.from_dict(app_state)
        LOCAL_STATE.from_dict(story_state)
        component_state.from_dict(stage_state)

    @staticmethod
    def put_story_state(component_state):
        print("Serializing state into DB.")
        comp_state_dict = component_state.as_dict()
        comp_state_dict.update(
            {"current_step": component_state.current_step.value.value}
        )

        state = {
            "app": GLOBAL_STATE.as_dict(),
            "story": LOCAL_STATE.as_dict(),
            "stage": {f"{component_state.stage_name.value}": comp_state_dict},
        }

        r = GLOBAL_STATE.request_session.put(
            f"{API_URL}/story-state/{GLOBAL_STATE.student.id.value}/hubbles_law",
            json=state,
        )
    
    @staticmethod
    def get_example_seed_measurement() -> list[dict[str, Any]]:
        url = f"{API_URL}/{HUBBLE_ROUTE_PATH}/sample-measurements"
        r = GLOBAL_STATE.request_session.get(url)
        res_json = r.json()
        
        
        # TODO: Note that though this is from the old code
        # it seems to only pick the 2nd measurement
        vels = [record[DB_VELOCITY_FIELD] for record in res_json]
        good = [vel is not None for vel in vels]
        seq = SeedSequence(42)
        gen = Generator(PCG64(seq))
        indices = arange(len(good))
        indices = indices[1::2][:85] # we need to keep the first 85 so that it always selects the same galaxies "randomly"
        random_subset = gen.choice(indices[good[1::2][:85]], size=40, replace=False)
        # This is the subset
        # [121, 11, 143, 21, 161, 127, 111, 15, 69, 105, 
        # 81, 9, 129, 91, 99, 17, 35, 169, 67, 107, 119, 
        # 123, 43, 141, 73, 137, 85, 59, 87, 25, 109, 49, 
        # 47, 95, 157, 63, 89, 57, 149, 103]
        measurements = []
        for i in random_subset:
            measurements.append(res_json[i])

        return measurements

