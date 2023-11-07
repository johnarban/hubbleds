import json

import ipyvuetify as v
from cosmicds.components import Table
from cosmicds.phases import Stage
from cosmicds.utils import API_URL, CDSJSONEncoder
from echo import add_callback

from .data_management import *
from .utils import HUBBLE_ROUTE_PATH, distance_from_angular_size, velocity_from_wavelengths


class HubbleStage(Stage):

    def __init__(self, session, story_state, app_state, *args, **kwargs):
        super().__init__(session, story_state, app_state, *args, **kwargs)

        # Respond to dark/light mode change
        add_callback(self.app_state, 'dark_mode', self._on_dark_mode_change)

    @staticmethod
    def _map_key(key):
        return MEAS_TO_STATE.get(key, key)

    def _prepare_measurement(self, measurement):
        prepared = {HubbleStage._map_key(k): measurement.get(k, None) for k in
                    MEAS_TO_STATE.keys()}
        prepared.update(UNITS_TO_STATE)
        prepared[DB_STUDENT_ID_FIELD] = self.app_state.student["id"]
        if not prepared[DB_GALNAME_FIELD].endswith(SPECTRUM_EXTENSION):
            prepared[DB_GALNAME_FIELD] += SPECTRUM_EXTENSION
        prepared = json.loads(json.dumps(prepared, cls=CDSJSONEncoder))
        return prepared
    
    def _prepare_sample_measurement(self, measurement):
        """ for the example galaxy data """
        prepared = {HubbleStage._map_key(k): measurement.get(k, None) for k in
                    MEAS_TO_STATE.keys()}
        prepared.update(UNITS_TO_STATE)
        prepared[DB_STUDENT_ID_FIELD] = self.app_state.student["id"]
        prepared[DB_MEASNUM_FIELD] = measurement[MEASUREMENT_NUMBER_COMPONENT]
        prepared[DB_BRIGHT_FIELD] = measurement[BRIGHTNESS_COMPONENT] 
        if not prepared[DB_GALNAME_FIELD].endswith(SPECTRUM_EXTENSION):
            prepared[DB_GALNAME_FIELD] += SPECTRUM_EXTENSION
        prepared = json.loads(json.dumps(prepared, cls=CDSJSONEncoder))
        return prepared


    def submit_measurement(self, measurement):
        if self.app_state.update_db:
            prepared = self._prepare_measurement(measurement)
            self._request_session.put(f"{API_URL}/{HUBBLE_ROUTE_PATH}/submit-measurement",
                        json=prepared)
   
    def submit_example_galaxy_measurement(self, measurement):
        if self.app_state.update_db:
            prepared = self._prepare_sample_measurement(measurement)
            endpoint = f"{API_URL}/{HUBBLE_ROUTE_PATH}/sample-measurement"
            self._request_session.put(endpoint, json=prepared)

    def remove_measurement(self, galaxy_name):
        name = str(galaxy_name)
        condition = lambda x: x == name
        if not galaxy_name.endswith(SPECTRUM_EXTENSION):
            galaxy_name += SPECTRUM_EXTENSION
        self.remove_data_values(STUDENT_MEASUREMENTS_LABEL, NAME_COMPONENT, condition,
                                single=True)
        user = self.app_state.student
        if self.app_state.update_db and user.get("id", None) is not None:
            self._request_session.delete(
                f"{API_URL}/{HUBBLE_ROUTE_PATH}/measurement/{user['id']}/{galaxy_name}")

    def update_data_value(self, dc_name, comp_name, value, index, block_submit=False):
        super().update_data_value(dc_name, comp_name, value, index)
        if dc_name not in [STUDENT_MEASUREMENTS_LABEL, EXAMPLE_GALAXY_MEASUREMENTS]:
            return

        # Update dependent values, if the student has already has a value for them
        # We block submission to avoid sending unnecessary requests
        data = self.data_collection[dc_name]
        if comp_name == MEASWAVE_COMPONENT:
            velocity = data[VELOCITY_COMPONENT][index]
            if velocity is not None:
                rest = data[RESTWAVE_COMPONENT][index]
                new_velocity = velocity_from_wavelengths(value, rest)
                self.update_data_value(dc_name, VELOCITY_COMPONENT, new_velocity, index, block_submit=True)

        if comp_name == ANGULAR_SIZE_COMPONENT:
            distance = data[DISTANCE_COMPONENT][index]
            if distance is not None:
                new_distance = distance_from_angular_size(value)
                self.update_data_value(dc_name, DISTANCE_COMPONENT, new_distance, index, block_submit=True)

        # Submit a measurement, if necessary
        if self.app_state.update_db \
                and comp_name in MEAS_TO_STATE.keys() \
                and not block_submit:
            measurement = {comp.label: data[comp][index] for comp in
                           data.main_components}
            if dc_name == STUDENT_MEASUREMENTS_LABEL:
                self.submit_measurement(measurement)
            elif dc_name == EXAMPLE_GALAXY_MEASUREMENTS:
                self.submit_example_galaxy_measurement(measurement)
    
    def upload_example_galaxy_table(self):
        data = self.data_collection[EXAMPLE_GALAXY_MEASUREMENTS]
        df = data.to_dataframe()
        # Submit a measurement, if necessary
        if self.app_state.update_db:
            for index in range(len(df)):
                measurement = {comp.label: data[comp][index] for comp in
                            data.main_components}
                self.submit_example_galaxy_measurement(measurement)
        

    def add_data_values(self, dc_name, values):
        super().add_data_values(dc_name, values)
        self.story_state.update_student_data()

        if self.app_state.update_db and dc_name == STUDENT_MEASUREMENTS_LABEL:
            self.submit_measurement(values)

    def table_selected_color(self, dark):
        theme = v.theme.themes.dark if dark else v.theme.themes.light
        return theme.info

    def _on_dark_mode_change(self, dark):
        color = self.table_selected_color(dark)
        for widget in self.widgets.values():
            if isinstance(widget, Table):
                widget.selected_color = color

