from collections import defaultdict, Counter
from datetime import datetime
from io import BytesIO
from math import floor
from pathlib import Path
import requests

import ipyvuetify as v
import numpy as np
from numpy.random import Generator, PCG64, SeedSequence
from astropy.io import fits
from cosmicds.phases import Story
from cosmicds.registries import story_registry
from cosmicds.utils import API_URL, RepeatedTimer
from dateutil.parser import isoparse
from echo import DictCallbackProperty, CallbackProperty
from echo.callback_container import CallbackContainer
from glue.core import Data
from glue.core.component import CategoricalComponent, Component
from glue.core.data_factories.fits import fits_reader
from glue.core.message import NumericalDataChangedMessage
from glue.core.subset import CategorySubsetState

from hubbleds.data.hubble_simulation.simulate import H0

from .data_management import *
from .utils import AGE_CONSTANT, H_ALPHA_REST_LAMBDA, HUBBLE_ROUTE_PATH, age_in_gyr_simple, fit_line, MG_REST_LAMBDA

@story_registry(name="hubbles_law")
class HubblesLaw(Story):
    title = CallbackProperty("Hubble's Law")
    measurements = DictCallbackProperty({})
    calculations = DictCallbackProperty({})
    validation_failure_counts = DictCallbackProperty({})
    has_best_fit_galaxy = CallbackProperty(False)
    enough_students_ready = CallbackProperty(False)

    name_ext = ".fits"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._set_theme()

        self._on_timer_cbs = CallbackContainer()

        self.add_callback('has_best_fit_galaxy', self.update_student_data)

        self.hub.subscribe(self, NumericalDataChangedMessage,
                           filter=lambda msg: msg.data.label == CLASS_DATA_LABEL,
                           handler=self._on_class_data_updated)

        # Load data needed for Hubble's Law
        data_dir = Path(__file__).parent / "data"
        output_dir = data_dir / "hubble_simulation" / "output"

        # Load some simulated measurements as summary data
        self.app.load_data([
            f"{dataset}.csv" for dataset in (
                data_dir / "galaxy_data",
                data_dir / "Hubble 1929-Table 1",
                data_dir / "HSTkey2001",
                data_dir / "dummy_student_data",
                output_dir / "HubbleData_ClassSample",
                output_dir / "HubbleData_All",
                output_dir / "HubbleSummary_ClassSample",
                output_dir / "HubbleSummary_Students",
                output_dir / "HubbleSummary_Classes",
            )
        ])

        # Load in the galaxy data
        galaxies = requests.get(f"{API_URL}/{HUBBLE_ROUTE_PATH}/galaxies?types=Sp").json()
        galaxies_dict = { k : [x[k] for x in galaxies] for k in galaxies[0] }
        galaxies_dict["name"] = [x[:-len(self.name_ext)] for x in galaxies_dict["name"]]
        self.data_collection.append(Data(
            label=SDSS_DATA_LABEL,
            **galaxies_dict
        ))

        # Load in the overall data
        all_json = requests.get(f"{API_URL}/{HUBBLE_ROUTE_PATH}/all-data").json()
        all_measurements = all_json["measurements"]
        for measurement in all_measurements:
            measurement.update({"galaxy_id": measurement["galaxy"]["id"]})
            measurement.pop("galaxy")
            measurement.pop("student")
        all_student_summaries = all_json["studentData"]
        all_class_summaries = all_json["classData"]
        all_data = Data(
            label=ALL_DATA_LABEL,
            **{ STATE_TO_MEAS.get(k, k) : [x[k] for x in all_measurements] for k in all_measurements[0] }
        )
        HubblesLaw.prune_none(all_data)
        self.data_collection.append(all_data)
        self.base_all_dict = None

        all_student_summ_data = self.data_from_summaries(all_student_summaries, label=ALL_STUDENT_SUMMARIES_LABEL, id_key=STUDENT_ID_COMPONENT)
        all_class_summ_data = self.data_from_summaries(all_class_summaries, label=ALL_CLASS_SUMMARIES_LABEL, id_key=CLASS_ID_COMPONENT)
        self.data_collection.append(all_student_summ_data)
        self.data_collection.append(all_class_summ_data)
        for comp in [AGE_COMPONENT, H0_COMPONENT]:
            self.app.add_link(all_student_summ_data, comp, all_class_summ_data, comp)

        # Compose empty data containers to be populated by user
        self.student_cols = [NAME_COMPONENT, RA_COMPONENT, DEC_COMPONENT, Z_COMPONENT,
                             GALTYPE_COMPONENT, MEASWAVE_COMPONENT, RESTWAVE_COMPONENT,
                             STUDENT_ID_COMPONENT, VELOCITY_COMPONENT, DISTANCE_COMPONENT,
                             ELEMENT_COMPONENT, ANGULAR_SIZE_COMPONENT]
        self.categorical_cols = [NAME_COMPONENT, ELEMENT_COMPONENT, GALTYPE_COMPONENT]
        student_measurements = Data(label=STUDENT_MEASUREMENTS_LABEL)
        class_data = Data(label=CLASS_DATA_LABEL)
        student_data = Data(label=STUDENT_DATA_LABEL)
        for col in self.student_cols:
            categorical = col in self.categorical_cols
            ctype = CategoricalComponent if categorical else Component
            meas_comp = ctype(np.array([]))
            data = ['X'] if categorical else [0]
            student_data_comp = ctype(np.array(data))
            class_data_comp = ctype(np.array(data))
            student_measurements.add_component(meas_comp, col)
            student_data.add_component(student_data_comp, col)
            class_data.add_component(class_data_comp, col)

        self.data_collection.append(student_measurements)
        self.data_collection.append(student_data)
        self.data_collection.append(class_data)
        for comp in [DISTANCE_COMPONENT, VELOCITY_COMPONENT, STUDENT_ID_COMPONENT]:
            self.app.add_link(student_measurements, comp, student_data, comp)
            self.app.add_link(student_measurements, comp, class_data, comp)

        class_summary_cols = [STUDENT_ID_COMPONENT, H0_COMPONENT, AGE_COMPONENT]
        class_summary_data = Data(label=CLASS_SUMMARY_LABEL)
        for col in class_summary_cols:
            component = Component(np.array([0]))
            class_summary_data.add_component(component, col)
        self.data_collection.append(class_summary_data)
        
        # create example galaxy data sets
        # example_galaxy_measurements
        # example_galaxy_student_data
        # SINGLE_GALAXY_SEED_DATA
        example_galaxy_meas = self.setup_example_galaxy()
        for comp in [DISTANCE_COMPONENT, VELOCITY_COMPONENT, STUDENT_ID_COMPONENT]:
            self.app.add_link(student_measurements, comp, example_galaxy_meas, comp)
            self.app.add_link(student_measurements, comp, example_galaxy_meas, comp)
        # Make all data writeable
        for data in self.data_collection:
            HubblesLaw.make_data_writeable(data)

        self.class_last_modified = None
        self.class_data_timer = RepeatedTimer(30, self._on_timer)
        self.class_data_timer.start()

    def _on_timer(self):
        self.fetch_class_data()
        for cb in self._on_timer_cbs:
            cb()

    def _set_theme(self):
        v.theme.dark = True
        v.theme.themes.dark.primary = 'colors.blue.darken4'   # Overall theme & header bars
        v.theme.themes.light.primary = 'colors.blue.darken3'
        v.theme.themes.dark.secondary = 'colors.cyan.darken3'    # Headers on dialogs & buttons that pop up dialogs
        v.theme.themes.light.secondary = 'colors.cyan.darken4'
        v.theme.themes.dark.accent = 'colors.amber.accent3'   # Next/Back buttons
        v.theme.themes.light.accent = 'colors.amber.accent2'
        v.theme.themes.dark.error = 'colors.pink.lighten1'  # Team insider buttons that will not appear for user
        v.theme.themes.light.error = 'colors.indigo.lighten2'
        v.theme.themes.dark.info = 'colors.deepOrange.darken4'  # Instruction scaffolds & viewer highlights
        v.theme.themes.light.info = 'colors.deepOrange.lighten1'
        v.theme.themes.dark.success = 'colors.green.accent3'   # Actions and interactions
        v.theme.themes.light.success = 'colors.green.accent3'
        v.theme.themes.dark.warning = 'colors.deepOrange.accent4' # Unallocated (maybe viewer highlights?)
        v.theme.themes.light.warning = 'colors.deepOrange.accent4'
        #Alt Palette 1:  Y:FFBE0B, O:FB5607, Pi:FF006E, Pu:8338EC, Bl:3A86FF, LiBl:619EFF


    def load_spectrum_data(self, name, gal_type):
        if not name.endswith(self.name_ext):
            filename = name + self.name_ext
        else:
            filename = name
            name = name[:-len(self.name_ext)]

        # Don't load data that we've already loaded
        dc = self.data_collection
        if name not in dc:
            data_name = name + '[COADD]'
            type_folders = { "Sp" : "spiral", "E" : "elliptical", "Ir" : "irregular" }
            folder = type_folders[gal_type]
            url = f"{API_URL}/{HUBBLE_ROUTE_PATH}/spectra/{folder}/{filename}"
            response = requests.get(url)
            f = BytesIO(response.content)
            f.name = name
            hdulist = fits.open(f)
            data = next((d for d in fits_reader(hdulist) if d.label == data_name), None)
            if data is None:
                return
            data.label = name
            dc.append(data)
            data['lambda'] = 10 ** data['loglam']
            HubblesLaw.make_data_writeable(data)
        return dc[name]

    def _best_fit_galaxy(self, measurements):
        distances = measurements[DISTANCE_COMPONENT]
        velocities = measurements[VELOCITY_COMPONENT]
        line = fit_line(distances, velocities)
        if line is None:
            return None

        dmin = min(distances)
        dmax = max(distances)
        d = round(0.5 * (dmin + dmax))
        v = round(line.slope.value * d)
        return {
            NAME_COMPONENT: BEST_FIT_GALAXY_NAME,
            DISTANCE_COMPONENT: d,
            VELOCITY_COMPONENT: v,
            RA_COMPONENT: 0, DEC_COMPONENT: 0,
            GALTYPE_COMPONENT: "Sp",
            MEASWAVE_COMPONENT: 0,
            RESTWAVE_COMPONENT: H_ALPHA_REST_LAMBDA,
            Z_COMPONENT: 0, ANGULAR_SIZE_COMPONENT: 0,
            ELEMENT_COMPONENT: "H-α",
            STUDENT_ID_COMPONENT: self.student_user["id"],
            DB_LAST_MODIFIED_FIELD: datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def setup_example_galaxy(self):
        """
        Load in the example galaxy data and seed data for the example galaxy
        Create empty Data for student measurements of example galaxy
        """
        # Load in the galaxy data
        example_galaxy_data = requests.get(f"{API_URL}/{HUBBLE_ROUTE_PATH}/sample-galaxy").json()
        example_galaxy_data = { k : [example_galaxy_data[k]] for k in example_galaxy_data }
        example_galaxy_data['galaxy_id'] = [name.replace('.fits','') for name in example_galaxy_data['name']]
        self.data_collection.append(Data(label=EXAMPLE_GALAXY_DATA, **example_galaxy_data))
        
        # load the seed data for the example galaxy to populate
        # parse the json into a dictionary of arrays
        # create glue Data object [each dictionary item becomes a component]
        example_galaxy_seed_data = requests.get(f"{API_URL}/{HUBBLE_ROUTE_PATH}/sample-measurements").json()
        example_galaxy_seed_data = {k: np.array([record[k] for record in example_galaxy_seed_data]) for k in example_galaxy_seed_data[0]}
        good = example_galaxy_seed_data[DB_VELOCITY_FIELD] != None

        # Uncomment this and comment out next block to get all seed galaxies
        # example_galaxy_seed_data = {k: np.array(v)[good] for k,v in example_galaxy_seed_data.items()}

        # This block chooses a subset of size N from the seed data
        seq = SeedSequence(42)
        gen = Generator(PCG64(seq))
        indices = np.arange(len(good))
        indices = indices[1::2][:85] # we need to keep the first 85 so that it always selects the same galaxies "randomly"
        random_subset = gen.choice(indices[good[1::2][:85]], size=40, replace=False)
        random_subset = np.ravel(np.column_stack((random_subset, random_subset+1)))
        example_galaxy_seed_data = {k: np.array(v)[random_subset] for k,v in example_galaxy_seed_data.items()}

        example_galaxy_seed_data[DB_VELOCITY_FIELD] = np.array(example_galaxy_seed_data[DB_VELOCITY_FIELD], dtype = type(example_galaxy_seed_data[DB_VELOCITY_FIELD][0]))
        example_galaxy_seed_data = Data(label=EXAMPLE_GALAXY_SEED_DATA, **example_galaxy_seed_data)
        
        self.data_collection.append(example_galaxy_seed_data)
        
        
        # Create empty Data for student measurements of example galaxy
        single_gal_student_cols = [SAMPLE_ID_COMPONENT, NAME_COMPONENT, RA_COMPONENT, DEC_COMPONENT, Z_COMPONENT,
                             GALTYPE_COMPONENT, MEASWAVE_COMPONENT, RESTWAVE_COMPONENT,
                             STUDENT_ID_COMPONENT, VELOCITY_COMPONENT, DISTANCE_COMPONENT,
                             ELEMENT_COMPONENT, ANGULAR_SIZE_COMPONENT, MEASUREMENT_NUMBER_COMPONENT, BRIGHTNESS_COMPONENT]
        
        categorical_components = [SAMPLE_ID_COMPONENT, ELEMENT_COMPONENT, GALTYPE_COMPONENT, NAME_COMPONENT, MEASUREMENT_NUMBER_COMPONENT]
        transfered_components = [NAME_COMPONENT, ELEMENT_COMPONENT, GALTYPE_COMPONENT, RA_COMPONENT, DEC_COMPONENT, Z_COMPONENT]
        empty_record = {}
        for col in transfered_components:
            empty_record[col] = example_galaxy_data[col][0]
        
        empty_record[RESTWAVE_COMPONENT] = H_ALPHA_REST_LAMBDA if ('H' in example_galaxy_data[ELEMENT_COMPONENT][0]) else MG_REST_LAMBDA
        empty_record[MEASUREMENT_NUMBER_COMPONENT] = 'first'
        empty_record[BRIGHTNESS_COMPONENT] = 1.0
        
        example_galaxy_measurements = Data(label=EXAMPLE_GALAXY_MEASUREMENTS)
        
        for col in single_gal_student_cols:
            categorical = col in categorical_components
            ctype = CategoricalComponent if categorical else Component
            meas_comp = ctype(np.array([]))
            example_galaxy_measurements.add_component(meas_comp, col)
        
        # add in the prefilled data
        main_components = [x.label for x in example_galaxy_measurements.main_components]
        component_dict = {c : list(example_galaxy_measurements[c]) for c in main_components}
        for component, vals in component_dict.items():
            vals.append(empty_record.get(component, None))
        new_data = Data(label=example_galaxy_measurements.label, **component_dict)
        example_galaxy_measurements.update_values_from_data(new_data)
        
        self.data_collection.append(example_galaxy_measurements)
        self.add_new_row(data = example_galaxy_measurements, changes = {MEASUREMENT_NUMBER_COMPONENT : 'second'})

        self.app.add_link(example_galaxy_seed_data, DB_STUDENT_ID_FIELD, example_galaxy_measurements, STUDENT_ID_COMPONENT)
        self.app.add_link(example_galaxy_seed_data, DB_DISTANCE_FIELD, example_galaxy_measurements, DISTANCE_COMPONENT)
        self.app.add_link(example_galaxy_seed_data, DB_VELOCITY_FIELD, example_galaxy_measurements, VELOCITY_COMPONENT)
        self.app.add_link(example_galaxy_seed_data, DB_MEASNUM_FIELD, example_galaxy_measurements, MEASUREMENT_NUMBER_COMPONENT)
        self.app.add_link(example_galaxy_seed_data, DB_ANGSIZE_FIELD, example_galaxy_measurements, ANGULAR_SIZE_COMPONENT)
        
        return example_galaxy_measurements
    
    def add_new_row(self, dc_name = None, data = None, changes ={}):
        """
        add_new_row _summary_

        Parameters
        ----------
        dc_name : str, optional
            label of existing Data in data collection, by default None
        data : Data, optional
            Data object which exists in data collection, by default None
        changes : dict, optional
            new values, defaults to duplicating 1st row, by default {}
        """
        if dc_name is None:
            if data is None:
                return
        else:
            data = self.data_collection[dc_name]
            return
        new_meas = {x.label:data[x][0] for x in data.main_components}
        for k,v in changes.items():
            new_meas[k] = v

        self.add_data_values(data,new_meas)
        
    def add_data_values(self, data = None, values = {}):
        if data is None:
            return
        main_components = [x.label for x in data.main_components]
        component_dict = {c : list(data[c]) for c in main_components}
        for component, vals in component_dict.items():
            vals.append(values.get(component, None))
        new_data = Data(label=data.label, **component_dict)
        self.make_data_writeable(new_data)
        data.update_values_from_data(new_data)


    def update_data(self, label, new_data):
        dc = self.data_collection
        if label in dc:
            data = dc[label]
            data.update_values_from_data(new_data)
            data.label = label
        else:
            main_comps = [x.label for x in new_data.main_components]
            components = { col: list(new_data[col]) for col in main_comps }
            data = Data(label=label, **components)
            HubblesLaw.make_data_writeable(data) 
            dc.append(data)

    def update_student_data(self, *args):
        dc = self.data_collection
        meas_data = dc[STUDENT_MEASUREMENTS_LABEL]
        df = meas_data.to_dataframe()
        df = df[df[DISTANCE_COMPONENT].notna() & \
                df[VELOCITY_COMPONENT].notna() & \
                df[ANGULAR_SIZE_COMPONENT].notna()]
        df[NAME_COMPONENT] = df[NAME_COMPONENT].astype(np.dtype(str))
        main_components = [x.label for x in meas_data.main_components]
        components = { col: list(df[col]) for col in main_components }
        if not all(len(v) > 0 for v in components.values()):
            return

        # Add the best-fit galaxy, if appropriate
        if self.has_best_fit_galaxy:
            bfg = self._best_fit_galaxy(components)
            for col, data in components.items():
                data.append(bfg.get(col, None))

        new_data = Data(label=STUDENT_DATA_LABEL)
        for col, data in components.items():
            categorical = col in self.categorical_cols
            ctype = CategoricalComponent if categorical else Component
            comp = ctype(np.array(data))
            new_data.add_component(comp, col)
        
        student_data = dc[STUDENT_DATA_LABEL]
        student_data.update_values_from_data(new_data)
        HubblesLaw.make_data_writeable(student_data)

        # We also need to update the all students summary data
        dists = new_data[DISTANCE_COMPONENT]
        vels = new_data[VELOCITY_COMPONENT]
        h0, age = self.create_single_summary(dists, vels)
        all_students_summ_data = self.data_collection[ALL_STUDENT_SUMMARIES_LABEL]
        student_id = self.student_user["id"]
        index = next((i for i in range(all_students_summ_data.size) if all_students_summ_data[STUDENT_ID_COMPONENT][i] == student_id), None)
        if index is None:
            self.add_data_values(
                data=all_students_summ_data,
                values={
                    H0_COMPONENT: h0,
                    AGE_COMPONENT: age,
                    STUDENT_ID_COMPONENT: student_id
                }
            )
        else:
            h0s = all_students_summ_data[H0_COMPONENT]
            ages = all_students_summ_data[AGE_COMPONENT]
            h0s[index] = h0
            ages[index] = age
            all_students_summ_data.update_components({
                all_students_summ_data.id[H0_COMPONENT]: h0s,
                all_students_summ_data.id[AGE_COMPONENT]: ages
            })

        # Make sure that the best-fit galaxy subset is correct
        if self.has_best_fit_galaxy:
            c = student_data.get_component(NAME_COMPONENT)
            indices = np.where(c.labels == bfg[NAME_COMPONENT])[0]
            codes = c.codes[indices]
            subset_state = CategorySubsetState(student_data.id[NAME_COMPONENT], codes)
            subset = next((s for s in student_data.subsets if s.label == BEST_FIT_SUBSET_LABEL), None)
            if subset is not None:
                subset.subset_state = subset_state
            else:
                student_data.new_subset(label=BEST_FIT_SUBSET_LABEL,
                                                 subset=subset_state,
                                                 color="blue",
                                                 alpha=1,
                                                 markersize=10)
                

    @staticmethod
    def prune_none(data):
        keep = set()
        for i in range(data.size):
            if all(data[comp][i] is not None for comp in data.main_components):
                keep.add(i)

        pruned_components = { comp.label: [data[comp][x] for x in keep] for comp in data.main_components }
        pruned = Data(label=data.label, **pruned_components)
        data.update_values_from_data(pruned)

    @staticmethod
    def make_data_writeable(data):
        for comp in data.main_components:
            data[comp.label].setflags(write=True)

    def galaxy_info(self, galaxy_ids):
        sdss = self.data_collection[SDSS_DATA_LABEL]
        indices = [i for i in range(sdss.size) if sdss['id'][i] in galaxy_ids]
        components = [x for x in sdss.main_components if x.label != 'id']
        return { sdss['id'][index]: { comp.label: sdss[comp][index] for comp in components } for index in indices }

    def data_from_measurements(self, measurements):
        for measurement in measurements:
            measurement.update(measurement.get("galaxy", {}))
        components = { STATE_TO_MEAS.get(k, k) : [measurement.get(k, None) for measurement in measurements] for k in DB_MEASUREMENT_FIELDS }

        for i, name in enumerate(components[NAME_COMPONENT]):
            if name.endswith(self.name_ext):
                components[NAME_COMPONENT][i] = name[:-len(self.name_ext)]
        return Data(**components)

    def data_from_summaries(self, summaries, id_key=None, label=None):
        components = { STATE_TO_SUMM.get(k, k) : [summary.get(k, None) for summary in summaries] for k in DB_SUMMARY_FIELDS }
        if id_key is not None:
            ids = [summary.get(id_key, None) for summary in summaries]
            ids = [x for x in ids if x is not None]
            components.update({ id_key: ids})

        data = Data(**components)
        if label is not None:
            data.label = label
        return data

    def fetch_measurements(self, url):
        response = requests.get(url)
        res_json = response.json()
        return res_json["measurements"]

    def fetch_measurement_data_and_update(self, url, label, prune_none=False, make_writeable=False, check_update=None, update_if_empty=True, callbacks=None):
        measurements = self.fetch_measurements(url)
        need_update = check_update is None or check_update(measurements)
        if not need_update:
            return None, None
        new_data = self.data_from_measurements(measurements)
        if not update_if_empty and new_data.size == 0:
            return None, None
        new_data.label = label
        if prune_none:
            HubblesLaw.prune_none(new_data)
        data = self.data_collection[label]
        data.update_values_from_data(new_data)
        if make_writeable:
            HubblesLaw.make_data_writeable(data)

        if callbacks is not None:
            for cb in callbacks:
                cb()

        return measurements, new_data

    def create_single_summary(self, distances, velocities):
        line = fit_line(distances, velocities)
        h0 = line.slope.value
        age = age_in_gyr_simple(h0)
        return h0, age

    def update_summary_data(self, measurements, summ_label, id_field):
        dists = defaultdict(list)
        vels = defaultdict(list)
        d = measurements[DISTANCE_COMPONENT]
        v = measurements[VELOCITY_COMPONENT]
        components = {}
        ids = set()
        for i in range(measurements.size):
            id_num = measurements[id_field][i]
            ids.add(id_num)
            dists[id_num].append(d[i])
            vels[id_num].append(v[i])
        
        hubbles = []
        ages = []
        for id_num in ids:
            h0, age = self.create_single_summary(dists[id_num], vels[id_num])
            hubbles.append(h0)
            ages.append(age)

        components = {
            H0_COMPONENT: hubbles,
            AGE_COMPONENT: ages
        }
        components[id_field] = list(ids)
        new_data = Data(label=summ_label, **components)

        data = self.data_collection[summ_label]
        data.update_values_from_data(new_data)

    def fetch_student_data(self):
        student_meas_url = f"{API_URL}/{HUBBLE_ROUTE_PATH}/measurements/{self.student_user['id']}"
        self.fetch_measurement_data_and_update(student_meas_url, STUDENT_MEASUREMENTS_LABEL, make_writeable=True)
        self.update_student_data()

    def on_timer(self, cb):
        self._on_timer_cbs.append(cb)

    def _on_class_data_updated(self, _message):
        if not self.enough_students_ready:
            class_data = self.data_collection[CLASS_DATA_LABEL]
            counter = Counter(class_data[STUDENT_ID_COMPONENT])
            students_ready = len([k for k, v in counter.items() if v >= 5])
            if students_ready >= 6:
                self.enough_students_ready = True

    def fetch_class_data(self):
        def check_update(measurements):
            last_modified = max([isoparse(m[DB_LAST_MODIFIED_FIELD]) for m in measurements], default=None)
            need_update = self.class_last_modified is None or last_modified is None or last_modified > self.class_last_modified
            if need_update and last_modified is not None:
                self.class_last_modified = last_modified
            return need_update
        class_data_url = f"{API_URL}/{HUBBLE_ROUTE_PATH}/stage-3-data/{self.student_user['id']}/{self.classroom['id']}"
        if self.class_last_modified is not None:
            timestamp = floor(self.class_last_modified.timestamp() * 1000)
            class_data_url = f"{class_data_url}?last_checked={timestamp}"
        updated_meas, updated_data = self.fetch_measurement_data_and_update(class_data_url, CLASS_DATA_LABEL, prune_none=True, update_if_empty=False, check_update=check_update)
        
        if updated_data is not None:
            class_id = self.classroom["id"]
            self.update_summary_data(updated_data, CLASS_SUMMARY_LABEL, STUDENT_ID_COMPONENT)
            all_data = self.data_collection[ALL_DATA_LABEL]

            # We can't do this when all_data is created
            # because it seems that the classroom info hasn't been populated
            if self.base_all_dict is None:
                indices = all_data[CLASS_ID_COMPONENT] != self.classroom["id"]
                self.base_all_dict = { k.label : all_data[k][indices] for k in all_data.main_components }

            all_dict = self.base_all_dict.copy()
            all_dict[CLASS_ID_COMPONENT] = np.concatenate([all_dict[CLASS_ID_COMPONENT], [class_id] * len(updated_meas)]) 
            for k in all_dict:
                if k == CLASS_ID_COMPONENT:
                    continue
                all_dict[k] = np.concatenate([all_dict[k], [m[MEAS_TO_STATE.get(k, k)] for m in updated_meas]])
            new_all = Data(label=all_data.label, **all_dict)
            all_data.update_values_from_data(new_all)
            HubblesLaw.prune_none(all_data)

            # We also need to update the all class summary data
            dists = updated_data[DISTANCE_COMPONENT]
            vels = updated_data[VELOCITY_COMPONENT]
            h0, age = self.create_single_summary(dists, vels)
            all_summ_data = self.data_collection[ALL_CLASS_SUMMARIES_LABEL]
            index = next((i for i in range(all_summ_data.size) if all_summ_data[CLASS_ID_COMPONENT][i] == class_id), None)
            if index is None:
                self.add_data_values(
                    data=all_summ_data,
                    values={
                        H0_COMPONENT: h0,
                        AGE_COMPONENT: age,
                        CLASS_ID_COMPONENT: class_id
                    }
                )
            else:
                h0s = all_summ_data[H0_COMPONENT]
                ages = all_summ_data[AGE_COMPONENT]
                h0s[index]= h0
                ages[index]= age
                all_summ_data.update_components({
                    all_summ_data.id[H0_COMPONENT]: h0s,
                    all_summ_data.id[AGE_COMPONENT]: ages
                })


    def setup_for_student(self, app_state):
        super().setup_for_student(app_state)
        if self.student_user["id"] in range(2989, 3018):
            #print("Warning! You are using the ID of a beta test student.")
            app_state.update_db = False
        self.fetch_student_data()
        self.fetch_class_data()
