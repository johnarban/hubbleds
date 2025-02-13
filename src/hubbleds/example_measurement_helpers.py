
from glue.core import Data
from glue_jupyter import JupyterApplication
from .data_management import (
    EXAMPLE_GALAXY_MEASUREMENTS, 
    EXAMPLE_GALAXY_SEED_DATA,
    DB_VELOCITY_FIELD,
    DB_MEASWAVE_FIELD,
    DB_ANGSIZE_FIELD,
    DB_DISTANCE_FIELD,
)
from .viewer_marker_colors import (
    MY_DATA_COLOR,
    GENERIC_COLOR,
)

from .utils import _add_link
from .state import StudentMeasurement



def create_example_subsets(gjapp: JupyterApplication, data: Data):
    if EXAMPLE_GALAXY_MEASUREMENTS in gjapp.data_collection:
        example_data = gjapp.data_collection[EXAMPLE_GALAXY_MEASUREMENTS]
        current_subsets = example_data.subsets
        if 'first measurement' not in (s.label for s in current_subsets):
            first = example_data.new_subset(example_data.id['measurement_number'] == 'first', label='first measurement')
            first.style.color = MY_DATA_COLOR
            first.style.alpha = 1.0
        if 'second measurement' not in (s.label for s in current_subsets):
            second = example_data.new_subset(example_data.id['measurement_number'] == 'second', label='second measurement')
            second.style.color = MY_DATA_COLOR
            second.style.alpha = 1.0
            

def link_example_seed_and_measurements(gjapp: JupyterApplication):
    if EXAMPLE_GALAXY_SEED_DATA in gjapp.data_collection and EXAMPLE_GALAXY_MEASUREMENTS in gjapp.data_collection:
        egsd = gjapp.data_collection[EXAMPLE_GALAXY_SEED_DATA]
        example_data = gjapp.data_collection[EXAMPLE_GALAXY_MEASUREMENTS]
        _add_link(gjapp, egsd, DB_VELOCITY_FIELD, example_data, "velocity_value")
        _add_link(gjapp, egsd, DB_MEASWAVE_FIELD, example_data, "obs_wave_value")
        _add_link(gjapp, egsd, DB_ANGSIZE_FIELD, example_data, "ang_size_value")
        _add_link(gjapp, egsd, DB_DISTANCE_FIELD, example_data, "est_dist_value")


def link_seed_data(gjapp):
    if EXAMPLE_GALAXY_SEED_DATA in gjapp.data_collection:
        egsd = gjapp.data_collection[EXAMPLE_GALAXY_SEED_DATA]
        if EXAMPLE_GALAXY_SEED_DATA + '_first' in gjapp.data_collection:
            first = gjapp.data_collection[EXAMPLE_GALAXY_SEED_DATA + '_first']
            _add_link(gjapp, egsd, DB_VELOCITY_FIELD, first, DB_VELOCITY_FIELD)
            _add_link(gjapp, egsd, DB_MEASWAVE_FIELD, first, DB_MEASWAVE_FIELD)
            _add_link(gjapp, egsd, DB_ANGSIZE_FIELD, first, DB_ANGSIZE_FIELD)
            _add_link(gjapp, egsd, DB_DISTANCE_FIELD, first, DB_DISTANCE_FIELD)
        if EXAMPLE_GALAXY_SEED_DATA + '_second' in gjapp.data_collection:
            second = gjapp.data_collection[EXAMPLE_GALAXY_SEED_DATA + '_second']
            _add_link(gjapp, egsd, DB_VELOCITY_FIELD, second, DB_VELOCITY_FIELD)
            _add_link(gjapp, egsd, DB_MEASWAVE_FIELD, second, DB_MEASWAVE_FIELD)
            _add_link(gjapp, egsd, DB_ANGSIZE_FIELD, second, DB_ANGSIZE_FIELD)
            _add_link(gjapp, egsd, DB_DISTANCE_FIELD, second, DB_DISTANCE_FIELD)


def _update_second_example_measurement(example_measurements: list[StudentMeasurement]):
        changed = ''
        if len(example_measurements) == 2:
            first = example_measurements[0]
            second = example_measurements[1]
            if second.obs_wave_value is None and first.obs_wave_value is not None:
                second.obs_wave_value = first.obs_wave_value
                changed += 'obs_wave_value '
            if second.velocity_value is None and first.velocity_value is not None:
                second.velocity_value = first.velocity_value
                changed += 'velocity_value '
            if second.ang_size_value is None and first.ang_size_value is not None:
                second.ang_size_value = first.ang_size_value
                changed += 'ang_size_value '
            if second.est_dist_value is None and first.est_dist_value is not None:
                second.est_dist_value = first.est_dist_value
                changed += 'est_dist_value '
            
            return changed, second
        return changed, None
