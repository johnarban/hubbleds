import logging
from random import sample

import astropy.units as u
from astropy.coordinates import SkyCoord
from cosmicds.components.table import Table
from cosmicds.phases import CDSState
from cosmicds.registries import register_stage
from cosmicds.utils import load_template, update_figure_css, debounce
from echo import add_callback, ignore_callback, CallbackProperty, \
    DictCallbackProperty, ListCallbackProperty, callback_property
from glue.core import Data
from glue.core.message import NumericalDataChangedMessage
from numpy import isin, zeros
from traitlets import Bool, default

from ..components import SpectrumSlideshow, SelectionTool, SpectrumMeasurementTutorialSequence, DotplotTutorialSlideshow
from ..data.styles import load_style
from ..data_management import *
from ..stage import HubbleStage
from ..utils import GALAXY_FOV, H_ALPHA_REST_LAMBDA, IMAGE_BASE_URL, \
    MG_REST_LAMBDA, velocity_from_wavelengths
from ..viewers import SpectrumView, HubbleDotPlotView

log = logging.getLogger()


import inspect
from IPython.display import Javascript, display

def print_log(*args, color = None, **kwargs):
    if False:
        print(*args, **kwargs)
        s = 'stage 1: ' + ' '.join([str(a) for a in args])
        color = color or 'red'
        display(Javascript(f'console.log("%c{s}","color:{color}");'))

    return
def print_function_name(func):
    def wrapper(*args, **kwargs):
        calling_function_name = inspect.stack()[1][3]
        print_log(f"Calling  {func.__name__} from {calling_function_name}")
        return func(*args, **kwargs)
    return wrapper

class StageState(CDSState):
    gals_total = CallbackProperty(0)
    gals_max = CallbackProperty(5)
    gal_selected = CallbackProperty(False)
    spec_viewer_reached = CallbackProperty(False)
    spec_tutorial_opened = CallbackProperty(False)
    dotplot_tutorial_finished = CallbackProperty(False) 
    dot_zoom_activated = CallbackProperty(True) # Need to initialize as false later
    dot_zoomed = CallbackProperty(True) # Need to initialize as false later
    dot_seq8_q = CallbackProperty(False)
    ref_vel1_q = CallbackProperty(False)
    lambda_used = CallbackProperty(False)
    lambda_on = CallbackProperty(False)
    waveline_set = CallbackProperty(False)
    obswaves_total = CallbackProperty(0)
    velocities_total = CallbackProperty(0)
    zoom_tool_activated = CallbackProperty(False)
    stage_1_complete = CallbackProperty(False)
    show_meas_tutorial = CallbackProperty(False)
    
    

    doppler_calc_state = DictCallbackProperty({
        'step': 0,
        'length': 6,
        'currentTitle': "Doppler Calculation",
        'failedValidation4': False,
        'failedValidation5': False,
        'interactSteps5': [3, 4],
        'maxStepCompleted5': 0,
        'studentc': 0,
        'student_vel_calc': False,
        'complete': False,
        'titles': [
            "Doppler Calculation",
            "Doppler Calculation",
            "Doppler Calculation",
            "Reflect on Your Result",
            "Enter Speed of Light",
            "Your Galaxy's Velocity",
        ]
    })
    
    # place state variables from spectrum_measurement_tutorial.py here
    spectrum_tut_vars = {v: False for v in [
            'dialog',
            'opened',
            'been_opened',
            'show_specviewer', 
            'allow_specview_mouse_interaction', 
            'show_first_measurement',
            'show_second_measurement',
            'zoom_tool_activated', 
            'show_selector_lines', 
            ]}
    spectrum_tut_vars['show_selector_lines'] = True
    spectrum_tut_vars.update({'step': 0, 'length':19, 'maxStepCompleted': 0})
    spectrum_tut_state = DictCallbackProperty(spectrum_tut_vars)
    
    meas_two_row_selected = CallbackProperty(False) #need to reinitialize to false
    meas_two_made = CallbackProperty(False) #need to reinitialize to false
    
    marker = CallbackProperty("")
    marker_backward = CallbackProperty()
    marker_forward = CallbackProperty()
    indices = DictCallbackProperty()
    image_location = CallbackProperty(f"{IMAGE_BASE_URL}/stage_one_spectrum")
    lambda_rest = CallbackProperty(0)
    lambda_obs = CallbackProperty(0)
    galaxy = DictCallbackProperty()
    reflection_complete = CallbackProperty(False)
    doppler_calc_reached = CallbackProperty(False)
    doppler_calc_dialog = CallbackProperty(True)  # Should the doppler calculation be displayed when marker == dop_cal5?
    student_vel = CallbackProperty(0)  # Value of student's calculated velocity
    doppler_calc_complete = CallbackProperty(False)  # Did student finish the doppler calculation?
    show_galaxy_table = CallbackProperty(False)
    show_example_galaxy_table = CallbackProperty(False)
    spectrum_clicked = CallbackProperty(False)
    allow_first_measurement_change = CallbackProperty(True)
    allow_second_measurement_change = CallbackProperty(True)
    
    random_state_variable = CallbackProperty(True)
    velocity_tolerance = CallbackProperty(0.5)
    has_bad_velocities = CallbackProperty(False)
    bad_velocity_index = ListCallbackProperty([])
    has_multiple_bad_velocities = CallbackProperty(False)
    
    
    
    markers = CallbackProperty([
        'mee_gui1',
        'sel_gal1',
        'sel_gal2',
        'sel_gal3',
        'sel_gal4',
        'cho_row1',
        'mee_spe1',
        'spe_tut1',
        'res_wav1',
        'obs_wav1',
        'obs_wav2',
        'dop_cal0',
        # 'dop_cal1',
        'dop_cal2',
        # 'dop_cal3',
        'dop_cal4',
        'dop_cal5',
        'che_mea1',
        'int_dot1', # add dot plot tutorial (like hubble race)
        'dot_seq1',
        'dot_seq2',
        'dot_seq3',
        'dot_seq4',
        'dot_seq5', # show first measurement
        'dot_seq6',
        'dot_seq7', # activate and check for zoom tool, auto advance
        'dot_seq8', # allow next after zoomed (pat: auto advance)
        'dot_seq9',
        'dot_seq10',
        'dot_seq11',
        'dot_seq12', # go split make second measuremtn or remaining galaxies
        'dot_seq13',
        'dot_seq13a',
        'dot_seq14',
        'rem_gal1',
        'ref_dat1',
        'dop_cal6',
        'ref_vel1',
        'end_sta1'
    ])

    step_markers = ListCallbackProperty([])

    # step_markers = ListCallbackProperty([
    #     'mee_gui1',
    #     'mee_spe1',
    #     'ref_dat1',
    #     'dop_cal0',
    # ])

    csv_highlights = ListCallbackProperty([
        'sel_gal1',
        'sel_gal2',
        'sel_gal3',
    ])

    table_highlights = ListCallbackProperty([
        'cho_row1',
        # 'dop_cal3',
        'dop_cal4',
        'dop_cal5',
        'dop_cal6',
    ])

    spec_highlights = ListCallbackProperty([
        'mee_spe1',
        'res_wav1',
        'obs_wav1',
        'obs_wav2',
        'rem_gal1',
        'ref_dat1',
        'dop_cal0',
        'dop_cal1',
        'dop_cal2',
    ])

    _NONSERIALIZED_PROPERTIES = [
        'markers',  # 'indices',
        'marker_forward', 'marker_backward',
        #'step_markers', 
        'csv_highlights',
        'table_highlights', 'spec_highlights',
        # 'gals_total', 'obswaves_total',
        'velocities_total', 'image_location',
        'velocity_tolerance', 'has_bad_velocities',
        'bad_velocity_index', 'has_multiple_bad_velocities'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.marker = self.markers[0]
        self.indices = {marker: idx for idx, marker in enumerate(self.markers)}

    @callback_property
    def marker_forward(self):
        return None

    @callback_property
    def marker_backward(self):
        return None
    
    @marker_backward.setter
    def marker_backward(self, value):
        index = self.indices[self.marker]
        new_index = min(max(index - value, 0), len(self.markers) - 1)
        self.marker = self.markers[new_index]

    @marker_forward.setter
    def marker_forward(self, value):
        index = self.indices[self.marker]
        new_index = min(max(index + value, 0), len(self.markers) - 1)
        self.marker = self.markers[new_index]

    def marker_before(self, marker):
        return self.indices[self.marker] < self.indices[marker]

    def marker_after(self, marker):
        return self.indices[self.marker] > self.indices[marker]

    def marker_reached(self, marker):
        return self.indices[self.marker] >= self.indices[marker]

    def marker_index(self, marker):
        return self.indices[marker]


@register_stage(story="hubbles_law", index=1, steps=[
    # "Explore celestial sky",
    # "COLLECT DATA",
    # "MEASURE SPECTRA",
    # "REFLECT",
    # "CALCULATE VELOCITIES"
])
class StageOne(HubbleStage):
    show_team_interface = Bool(False).tag(sync=True)
    START_COORDINATES = SkyCoord(180 * u.deg, 25 * u.deg, frame='icrs')

    _state_cls = StageState

    @default('template')
    def _default_template(self):
        return load_template("stage_1.vue", __file__)

    @default('stage_icon')
    def _default_stage_icon(self):
        return "1"

    @default('title')
    def _default_title(self):
        return "Spectra & Velocities"

    @default('subtitle')
    def _default_subtitle(self):
        return "Perhaps a small blurb about this stage"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.show_team_interface = self.app_state.show_team_interface

        # This flag indicates whether we're using one of the convenience "fill" methods
        # In which case we don't need to do all of the UI manipulation in quite the same way
        self._filling_data = False

        # Set up any Data-based state values
        self._update_state_from_measurements()
        self.hub.subscribe(
            self, NumericalDataChangedMessage,
            filter=lambda msg: ((msg.data.label == STUDENT_MEASUREMENTS_LABEL) | (msg.data.label == EXAMPLE_GALAXY_MEASUREMENTS)),
            handler=self._on_measurements_changed)
        

        # Set up viewers
        spectrum_viewer = self.add_viewer(
            SpectrumView, label="spectrum_viewer")
        if spectrum_viewer.toolbar.tools.get("hubble:specflag") is not None:
            sf_tool = spectrum_viewer.toolbar.tools["hubble:specflag"]
            add_callback(sf_tool, "flagged", self._on_spectrum_flagged)
        
        # Add new dotplot viewer with single galaxy seed data
        dotplot_viewer = self.add_viewer(HubbleDotPlotView, label='dotplot_viewer', viewer_label = 'Example Galaxy Measurement')
        dotplot_viewer_2 = self.add_viewer(HubbleDotPlotView, label='dotplot_viewer_2', viewer_label = 'Second Measurement')
        dotplot_viewer_3 = self.add_viewer(HubbleDotPlotView, label='dotplot_viewer_3', viewer_label = 'Dot Plot')

        ### Disable anything to do with towerselect for now
        # dotplot_viewer.toolbar.set_tool_enabled('hubble:towerselect', False)
        # dotplot_viewer_2.toolbar.set_tool_enabled('hubble:towerselect', False)
        # dotplot_viewer_3.toolbar.set_tool_enabled('hubble:towerselect', False)

        dotplot_viewer.toolbar.set_tool_enabled('hubble:wavezoom', False)
        dotplot_viewer_2.toolbar.set_tool_enabled('hubble:wavezoom', False)
        dotplot_viewer_3.toolbar.set_tool_enabled('hubble:wavezoom', False)
        dotplot_viewer_3.toolbar.set_tool_enabled('bqplot:home', False)
                
        #     HubbleHistogramView, label="dotplot_viewer")
        example_galaxy_data = self.get_data(EXAMPLE_GALAXY_SEED_DATA)
        first = example_galaxy_data.new_subset(example_galaxy_data.id['measurement_number']=='first', label='first measurement')
        second = example_galaxy_data.new_subset(example_galaxy_data.id['measurement_number']=='second', label='second measurement')
        
        # the layer what you find in viewer.layers[0].state.layer or viewer.state.layers[0].layer
        # which is either the glue Data or Subset object that is being displayed
        dotplot_viewer.ignore(lambda layer: layer in [second])
        dotplot_viewer_2.ignore(lambda layer: layer in [first])
        dotplot_viewer_3.ignore(lambda layer: layer in [second])
        
        for i,viewer in enumerate([dotplot_viewer, dotplot_viewer_2,dotplot_viewer_3]):
            viewer.add_data(example_galaxy_data)
            viewer.state.x_att = example_galaxy_data.id['velocity_value']
            viewer.layer_artist_for_data(example_galaxy_data).visible = False
            viewer.figure.axes[0].label = 'Velocity (km/s)'
            viewer.state.hist_n_bin = 75
            viewer.state.reset_limits()
            viewer.state.viewer_height = 150
            for subset in [first, second]:
                layer = viewer.layer_artist_for_data(subset)
                if layer is not None:
                    layer.state.color = '#787878'
                    layer.state.alpha = 1
                    layer.state.skew = 0.1
                    layer.state.rotation = 90

        
        
        add_velocities_tool = dict(
            id="update-velocities",
            icon="mdi-run-fast",
            tooltip="Fill in velocities",
            disabled=self.stage_state.marker_before(
                'dop_cal6'),
            activate=self.update_velocities)
        galaxy_table = Table(
            self.session,
            data=self.get_data(STUDENT_MEASUREMENTS_LABEL),
            glue_components=[NAME_COMPONENT,
                             ELEMENT_COMPONENT,
                             RESTWAVE_COMPONENT,
                             MEASWAVE_COMPONENT,
                             VELOCITY_COMPONENT],
            key_component=NAME_COMPONENT,
            names=['Galaxy Name',
                   'Element',
                   '&lambda;<sub>rest</sub> (&Aring;)',
                   '&lambda;<sub>obs</sub> (&Aring;)',
                   'Velocity (km/s)'],
            title='My Galaxies',
            selected_color=self.table_selected_color(
                self.app_state.dark_mode),
            use_subset_group=False,
            single_select=True,  # True for now
            tools=[add_velocities_tool])

        self.add_widget(galaxy_table, label="galaxy_table")
        galaxy_table.row_click_callback = lambda item, _data=None: self.on_table_row_click(item, _data, table=galaxy_table)
        galaxy_table.observe(
            self.table_selected_change, names=["selected"])
        self.galaxy_table.allow_row_click = not self.stage_state.has_bad_velocities
        
        def _on_has_bad_velocities(*args):
            self.galaxy_table.allow_row_click = not self.stage_state.has_bad_velocities
            if self.stage_state.has_bad_velocities or self.stage_state.has_multiple_bad_velocities:
                self.select_bad_measurement_row()
        
        add_callback(self.stage_state, 'has_bad_velocities', _on_has_bad_velocities)
        add_callback(self.stage_state, 'has_multiple_bad_velocities', _on_has_bad_velocities)
        
        
        add_velocities_tool2 = dict(
            id="update-velocities",
            icon="mdi-run-fast",
            tooltip="Fill in velocities",
            disabled=~self.show_team_interface,
            activate=self.update_velocities)
        example_galaxy_table = Table(
            self.session,
            data=self.get_data(EXAMPLE_GALAXY_MEASUREMENTS),
            glue_components=[NAME_COMPONENT,
                            ELEMENT_COMPONENT,
                            RESTWAVE_COMPONENT,
                            MEASWAVE_COMPONENT,
                            VELOCITY_COMPONENT,
                            MEASUREMENT_NUMBER_COMPONENT],
            key_component=MEASUREMENT_NUMBER_COMPONENT,
            names=['Galaxy Name',
                    'Element',
                    '&lambda;<sub>rest</sub> (&Aring;)',
                    '&lambda;<sub>obs</sub> (&Aring;)',
                    'Velocity (km/s)',
                    'Measurement Number'],
            title='Example Galaxy',
            selected_color=self.table_selected_color(
                self.app_state.dark_mode),
            item_filter= lambda item: item[MEASUREMENT_NUMBER_COMPONENT] == 'first',
            use_subset_group=False,
            single_select=True,
            tools=[add_velocities_tool2])
        
        # self.upload_example_galaxy_table()
        
        self.add_widget(example_galaxy_table, label="example_galaxy_table")
        example_galaxy_table.row_click_callback = lambda item, _data=None: self.on_table_row_click(item, _data, table=example_galaxy_table)
        example_galaxy_table.observe(
            self.table_selected_change, names=["selected"])
        # add the row for the second measurement
        self.initialize_spectrum_data(EXAMPLE_GALAXY_MEASUREMENTS)
        
        # Set up components
        sdss_data = self.get_data(SDSS_DATA_LABEL)
        selected = self.get_data(STUDENT_MEASUREMENTS_LABEL).to_dataframe()
        selection_tool = SelectionTool(data=sdss_data,
                                       selected_data=selected,
                                       show_galaxies=self.stage_state.marker_reached("sel_gal1"))
        self.add_component(selection_tool, label='py-selection-tool')
        selection_tool.on_galaxy_selected = self._on_galaxy_selected
        selection_tool._on_reset_view = self._on_selection_viewer_reset
        selection_tool.observe(self._on_selection_tool_flagged,
                               names=['flagged'])
        selection_tool.observe(self._on_selection_tool_selected,
                               names=['selected'])

        spectrum_slideshow = SpectrumSlideshow(self.stage_state.image_location)
        self.add_component(spectrum_slideshow, label='py-spectrum-slideshow')
        spectrum_slideshow.observe(self._spectrum_slideshow_marker_changed,
                                   names=['marker'])
        spectrum_slideshow.observe(self._spectrum_slideshow_tutorial_opened,
                                   names=['opened'])
        
        dotplot_slideshow = DotplotTutorialSlideshow([self.viewers["dotplot_viewer_3"]])
        self.add_component(dotplot_slideshow, label='py-dotplot-tutorial-slideshow')
        dotplot_slideshow.observe(self._dotplot_slideshow_tutorial_finished, names=['finished'])
        
        # callback places velocity value in table
        add_callback(self.stage_state, 'student_vel',
                     lambda *args, **kwargs: self.add_student_velocity(example_galaxy_table, *args, **kwargs))
        add_callback(self.stage_state, 'stage_1_complete', self._on_stage_complete)
        


        # Callbacks
        def update_count(change):
            if self.stage_state.gals_total > 0 and self.stage_state.marker == "sel_gal2":
                self.stage_state.marker = "sel_gal3"

            self.stage_state.gals_total = change["new"]

        selection_tool.observe(update_count, names=['selected_count'])
        add_callback(self.stage_state, 'marker',
                     self._on_marker_update, echo_old=True)
        # add_callback(self.story_state, 'step_index',
        #              self._on_step_index_update)
        self.trigger_marker_update_cb = True

        self.update_spectrum_style(dark=self.app_state.dark_mode)
        self._update_viewer_style(dark=self.app_state.dark_mode)

        add_callback(self.stage_state, 'doppler_calc_complete',
                     self.enable_velocity_tool)

        spectrum_viewer = self.get_viewer("spectrum_viewer")
        spec_toolbar = spectrum_viewer.toolbar
        restwave_tool = spec_toolbar.tools["hubble:restwave"]
        add_callback(restwave_tool, 'lambda_used', self._on_lambda_used)
        add_callback(restwave_tool, 'lambda_on', self._on_lambda_on)
        wavezoom_tool = spec_toolbar.tools["hubble:wavezoom"]
        add_callback(wavezoom_tool, 'zoom_tool_activated',
                     self._on_zoom_tool_activated)
        spec_toolbar.set_tool_enabled("hubble:restwave",
                                      self.stage_state.marker_reached(
                                          "res_wav1"))
        spec_toolbar.set_tool_enabled("hubble:wavezoom",
                                      self.stage_state.marker_reached(
                                          "obs_wav2"))
        spec_toolbar.set_tool_enabled("bqplot:home",
                                      self.stage_state.marker_reached(
                                          "obs_wav2"))
        if self.stage_state.galaxy:
            self._on_galaxy_update(self.stage_state.galaxy)
        add_callback(self.stage_state, 'galaxy', self._on_galaxy_update)
        
        # ADD SPECTRUM MEASUREMENT TUTORIAL
        smts_viewers = [self.viewers["dotplot_viewer"],self.viewers["dotplot_viewer_2"], self.viewers["spectrum_viewer"], self.get_widget("example_galaxy_table")]
        self.spectrum_measurement_tutorial = SpectrumMeasurementTutorialSequence(smts_viewers, self.stage_state.spectrum_tut_state, self.stage_state.marker, self.stage_state.indices)
        # self.add_component(spectrum_measurement_tutorial, label='c-spectrum-measurement-tutorial')
        def print_dict_diff(dict_old, dict_new):
            for key in dict_new:
                if dict_old[key] != dict_new[key]:
                    print_log('changed', key, 'from', dict_old[key], 'to', dict_new[key], color='red')
        

        def _smts_state_update(change):
            print_log('update spectrum tutorial state', color='red')
            # print the changes between the two states
            dict_old = change['old']
            dict_new = change['new']
            print_dict_diff(self.stage_state.spectrum_tut_state, dict_new)
            self.stage_state.spectrum_tut_state = change['new']
        self.spectrum_measurement_tutorial.observe(_smts_state_update, ['tutorial_state'])
        # self.spectrum_measurement_tutorial._on_dialog_open({'new': True})
        

        # INITIALIZE STATE VARIABLES WHEN LOADING A STORED STATE
        # reset the state variables when we load a story state
        self.stage_state.spec_tutorial_opened = self.stage_state.marker_reached(
            'spe_tut1')
        self.stage_state.spec_viewer_reached = self.stage_state.marker_reached(
            'cho_row1')
        self.stage_state.doppler_calc_reached = self.stage_state.marker_reached(
            'dop_cal2')
        self.stage_state.dotplot_tutorial_finished = self.stage_state.marker_reached(
            'dot_seq1')

        # Initialize viewers to provide story state
        if self.stage_state.marker_reached('sel_gal1'):
            selection_tool.show_galaxies()
            selection_tool.widget.center_on_coordinates(
                self.START_COORDINATES, fov=60 * u.deg, instant=True)
        
        if self.stage_state.marker_reached('sel_gal4'):
            pass
            # self.stage_state.show_galaxy_table = False
            # self.stage_state.show_example_galaxy_table = True
        
        if self.stage_state.marker_reached("res_wav1"):
            spectrum_viewer.toolbar.set_tool_enabled("hubble:restwave", True)

        if self.stage_state.marker_reached("obs_wav1"):
            spectrum_viewer.add_event_callback(spectrum_viewer._on_mouse_moved,
                                               events=['mousemove'])
            spectrum_viewer.add_event_callback(spectrum_viewer._on_click,
                                               events=['click'])
            spectrum_viewer.add_event_callback(self.on_spectrum_click,
                                               events=['click'])
            spectrum_viewer.add_event_callback(self.on_spectrum_click_example_galaxy,
                                               events=['click'])
        else:
            spectrum_viewer.remove_event_callback(spectrum_viewer._on_mouse_moved)
            spectrum_viewer.remove_event_callback(spectrum_viewer._on_click)

        if self.stage_state.marker_reached("obs_wav2"):
            spectrum_viewer.toolbar.set_tool_enabled("hubble:wavezoom", True)
            spectrum_viewer.toolbar.set_tool_enabled("bqplot:home", True)
        
        if self.stage_state.marker_reached("dop_cal6"):
            # if self.stage_state.doppler_calc_reached:
            self.enable_velocity_tool(True)
        
        if self.stage_state.marker_reached("rem_gal1"):
            self.select_bad_measurement_row()

        # Uncomment this to pre-fill galaxy data for convenience when testing later stages
        # self.vue_fill_data()
        # self.vue_select_galaxies()
    
    #@print_function_name
    def _on_measurements_changed(self, msg):
        self._update_state_from_measurements_debounced()
        self.num_bad_student_velocities()
        
    
    #@print_function_name
    def _update_state_from_measurements(self):
        student_measurements = self.get_data(STUDENT_MEASUREMENTS_LABEL)
        self.stage_state.gals_total = int(student_measurements.size)
        measwaves = student_measurements[MEASWAVE_COMPONENT]
        self.stage_state.obswaves_total = measwaves[measwaves != None].size - self.num_bad_student_velocities()
        velocities = student_measurements[VELOCITY_COMPONENT]
        self.stage_state.velocities_total = velocities[velocities != None].size
        
        example_measurements = self.get_data(EXAMPLE_GALAXY_MEASUREMENTS)
        measwaves = example_measurements[MEASWAVE_COMPONENT]
        velocities = example_measurements[VELOCITY_COMPONENT]

    @debounce(wait=2)
    def _update_state_from_measurements_debounced(self):
        self._update_state_from_measurements()

    #@print_function_name
    def _on_marker_update(self, old, new):
        if not self.trigger_marker_update_cb:
            return
        markers = self.stage_state.markers
        advancing = markers.index(new) > markers.index(old)
        print_log(f"Marker changed from {old} to {new} and is {'not ' if not advancing else ''}advancing")
        # if new in self.stage_state.step_markers and advancing:
        #     self.story_state.step_complete = True
        #     self.story_state.step_index = self.stage_state.step_markers.index(
        #         new)
        if advancing and new == "dop_cal6":
            self.stage_state.doppler_calc_complete = True
            
        if advancing and old == "sel_gal1":
            self.selection_tool.show_galaxies()
            self.selection_tool.widget.center_on_coordinates(
                self.START_COORDINATES, fov=60 * u.deg, instant=True)
            
        if advancing and old == "sel_gal3":
            self.galaxy_table.selected = []
            self.example_galaxy_table.selected = []
            self.selection_tool.widget.center_on_coordinates(
                self.START_COORDINATES, instant=True)
            
        if advancing and new == 'sel_gal4':
            print_log('commented out: showing example galaxy table')
            # self.stage_state.show_galaxy_table = False
            # self.stage_state.show_example_galaxy_table = True
            
            
        if advancing and new == "cho_row1" and self.example_galaxy_table.index is not None:
            self.stage_state.spec_viewer_reached = True
            self.stage_state.marker = "mee_spe1"
            
        if advancing and old == "dop_cal2" and (self.example_galaxy_table.index is not None) :
            self.stage_state.doppler_calc_reached = True
            self.stage_state.marker = "dop_cal4"
            
        if advancing and old == "dop_cal2":
            self.selection_tool.widget.center_on_coordinates(
                self.START_COORDINATES, instant=True)
            
        if advancing and new == "res_wav1":
            spectrum_viewer = self.get_viewer("spectrum_viewer")
            spectrum_viewer.toolbar.set_tool_enabled("hubble:restwave", True)
            
        if advancing and new == "obs_wav1":
            spectrum_viewer = self.get_viewer("spectrum_viewer")
            spectrum_viewer.add_event_callback(spectrum_viewer._on_mouse_moved,
                                               events=['mousemove'])
            spectrum_viewer.add_event_callback(spectrum_viewer._on_click,
                                               events=['click'])
            spectrum_viewer.add_event_callback(self.on_spectrum_click,
                                               events=['click'])
            spectrum_viewer.add_event_callback(self.on_spectrum_click_example_galaxy,
                                               events=['click'])
            
        if advancing and new == "obs_wav2":
            spectrum_viewer = self.get_viewer("spectrum_viewer")
            spectrum_viewer.toolbar.set_tool_enabled("hubble:wavezoom", True)
            spectrum_viewer.toolbar.set_tool_enabled("bqplot:home", True)
        
        if advancing and new == "che_mea1":
            spectrum_viewer = self.get_viewer("spectrum_viewer")
            spectrum_viewer.state.reset_limits()
        
        # activate the dot plot sequence stuff
        if self.stage_state.marker_reached('int_dot1'):
            if (not self.spectrum_measurement_tutorial.been_opened) and self.stage_state.marker_before('rem_gal1'):
                self.spectrum_measurement_tutorial._on_dialog_open({'new': True, 'marker': new})
         
        if self.stage_state.marker_reached('int_dot1') and self.stage_state.marker_before('rem_gal1'):
            self.spectrum_measurement_tutorial._on_marker_change(old, new)
        
        if advancing and new == "rem_gal1":
            self.spectrum_measurement_tutorial.vue_on_close()
    
    # def _on_step_index_update(self, index):
    #     # If we aren't on this stage, ignore
    #     if self.story_state.stage_index != self.index:
    #         return

    #     # Change the marker without firing the associated stage callback
    #     # We can't just use ignore_callback, since other stuff (i.e. the
    #     # frontend) may depend on marker callbacks
    #     self.trigger_marker_update_cb = False
    #     index = min(index, len(self.stage_state.step_markers) - 1)
    #     self.stage_state.marker = self.stage_state.step_markers[index]
    #     self.trigger_marker_update_cb = True

    def _on_galaxy_update(self, galaxy):
        if galaxy:
            self.story_state.load_spectrum_data(galaxy["name"], galaxy["type"])
            if not self._filling_data:
                if galaxy[NAME_COMPONENT] in self.example_galaxy_table._glue_data[NAME_COMPONENT]:
                    self.example_galaxy_table.selected = [galaxy]
                elif galaxy[NAME_COMPONENT] in self.galaxy_table._glue_data[NAME_COMPONENT]:
                    self.galaxy_table.selected = [galaxy]

    def _on_galaxy_selected(self, galaxy):
        data = self.get_data(STUDENT_MEASUREMENTS_LABEL)
        is_in = isin(data['name'], galaxy['name'])  # Avoid duplicates
        already_present = is_in.size > 0 and is_in[0]
        if already_present:
            # To do nothing
            return
            # If instead we wanted to remove the point from the student's
            # selection
            # index = next(idx for idx, val in enumerate(component_dict['ID'])
            #              if val == galaxy['ID'])
            # for component, values in component_dict.items():
            #     values.pop(index)
        else:
            filename = galaxy['name']
            gal_type = galaxy['type']
            if not self._filling_data:
                galaxy.pop("element")
            self.story_state.load_spectrum_data(filename, gal_type)
            self.add_data_values(STUDENT_MEASUREMENTS_LABEL, galaxy)
            self.stage_state.galaxy = galaxy

    def _on_lambda_used(self, used):
        self.stage_state.lambda_used = used

    def _on_lambda_on(self, on):
        self.stage_state.lambda_on = on

    def _on_zoom_tool_activated(self, used):
        self.stage_state.zoom_tool_activated = used

    def _select_from_data(self, dc_name):
        data = self.get_data(dc_name)
        components = [x.label for x in data.main_components]
        measurements = self.get_data(STUDENT_MEASUREMENTS_LABEL)
        need = self.selection_tool.gals_max - measurements.size
        indices = sample(range(data.size), need)
        for index in indices:
            galaxy = {c: data[c][index] for c in components}
            self.selection_tool.select_galaxy(galaxy)
    
    #@print_function_name

    def vue_fill_data(self, _args=None):
        self._filling_data = True
        self._select_from_data("dummy_student_data")
        self.galaxy_table.selected = []
        self.selection_tool.widget.center_on_coordinates(
            self.START_COORDINATES, instant=True)
        if self.stage_state.marker_before("sel_gal3"):
            self.stage_state.marker = "sel_gal3"
        self._filling_data = False

    def vue_select_galaxies(self, _args=None):
        self._filling_data = True
        self._select_from_data(SDSS_DATA_LABEL)
        self.galaxy_table.selected = []
        self.selection_tool.widget.center_on_coordinates(
            self.START_COORDINATES, instant=True)
        if self.stage_state.marker_before("sel_gal3"):
            self.stage_state.marker = "sel_gal3"
        self._filling_data = False

    #@print_function_name
    def update_spectrum_viewer(self, name, z, table):
        specview = self.get_viewer("spectrum_viewer")
        specview.toolbar.active_tool = None
        filename = name
        spec_name = filename.split(".")[0]
        data = self.get_data(spec_name)
        self.story_state.update_data(SPECTRUM_DATA_LABEL, data)
        if len(specview.layers) == 0:
            spec_data = self.get_data(SPECTRUM_DATA_LABEL)
            specview.add_data(spec_data)
            specview.figure.axes[0].label = "Wavelength (Angstroms)"
            specview.figure.axes[1].label = "Brightness"
        specview.state.reset_limits()
        self.stage_state.waveline_set = False

        index = table.index
        measurements = table.glue_data
        measwave = measurements[MEASWAVE_COMPONENT][index]

        sdss = self.get_data(SDSS_DATA_LABEL)
        sdss_index = next(
            (i for i in range(sdss.size) if sdss["name"][i] == name), None)
        if sdss_index is not None:
            element = sdss['element'][sdss_index]
            label = STUDENT_MEASUREMENTS_LABEL
        else:
            element = measurements[ELEMENT_COMPONENT][index]
            label = EXAMPLE_GALAXY_MEASUREMENTS

        specview.update(name, element, z, previous=measwave)
        self.stage_state.element = element
        restwave = MG_REST_LAMBDA if element == 'Mg-I' else H_ALPHA_REST_LAMBDA
        self.update_data_value(label, ELEMENT_COMPONENT, element, index)
        self.update_data_value(label, RESTWAVE_COMPONENT, restwave, index)
        
    def _spectrum_slideshow_marker_changed(self, msg):
        self.stage_state.marker = msg['new']

    def _spectrum_slideshow_tutorial_opened(self, msg):
        self.stage_state.spec_tutorial_opened = msg['new']

    def _dotplot_slideshow_tutorial_finished(self, msg):
        self.stage_state.dotplot_tutorial_finished = msg['new']

    def _on_doppler_dialog_changed(self, msg):
        self.stage_state.doppler_calc_dialog = msg['new']

    #@print_function_name
    def table_selected_change(self, change):
        if change["new"] == change["old"]:
            return
        table = change['owner']
        if table.glue_data.size == 0:
            self._empty_spectrum_viewer()
            return
        index = table.index
        if index is None:
            self._empty_spectrum_viewer()
            return
        data = table.glue_data
        galaxy = {x.label: data[x][index] for x in data.main_components}
        name = galaxy["name"]
        gal_type = galaxy["type"]
        if name is None or gal_type is None:
            return

        self.selection_tool.current_galaxy = galaxy
        self.stage_state.galaxy = galaxy

        # Load the spectrum data, if necessary
        filename = name
        spec_data = self.story_state.load_spectrum_data(filename, gal_type)

        z = galaxy["z"]
        self.story_state.update_data(SPECTRUM_DATA_LABEL, spec_data)
        self.update_spectrum_viewer(name, z,  table )
        
        if self.stage_state.marker_reached('cho_row1'):
            self.stage_state.spec_viewer_reached = True

        if self.stage_state.marker == 'cho_row1':
            self.stage_state.spec_viewer_reached = True
            self.stage_state.marker = 'mee_spe1'

        if self.stage_state.marker == 'dop_cal2':
            self.stage_state.doppler_calc_reached = True
            self.stage_state.marker = 'dop_cal4'

    #@print_function_name
    def on_table_row_click(self, item, _data=None, table=None):
        index = table.indices_from_items([item])[0]
        data = table.glue_data
        name = data["name"][index]
        gal_type = data["type"][index]
        if name is None or gal_type is None:
            return

        self.selection_tool.go_to_location(data["ra"][index],
                                           data["decl"][index], fov=GALAXY_FOV)
        self.stage_state.lambda_rest = data[RESTWAVE_COMPONENT][index]
        self.stage_state.lambda_obs = data[MEASWAVE_COMPONENT][index]
        self.stage_state.sel_gal_index = index
        
        if table is self.example_galaxy_table:
            if index == 1:
                self.stage_state.meas_two_row_selected = True
                self.stage_state.marker_forward = 1


    def _on_selection_viewer_reset(self) -> None:
        """ clear selection from galaxy table"""
        self.galaxy_table.selected = []
        self.stage_state.sel_gal_index = None

    def on_spectrum_click(self, event):
        specview = self.get_viewer("spectrum_viewer")
        if event["event"] != "click" or not specview.line_visible:
            return

        new_value = round(event["domain"]["x"], 0)
        data = self.galaxy_table.glue_data
        if data.size == 0:
            return 
        index = self.galaxy_table.index
        if index is None:
            return

        if not (data['name'][index] in self.get_data(STUDENT_MEASUREMENTS_LABEL)['name']):
            return

        self.stage_state.waveline_set = True
        self.stage_state.lambda_obs = new_value

        skip = self.stage_state.has_multiple_bad_velocities \
                and index not in self.stage_state.bad_velocity_index
        if skip:
            return
      
        self.update_data_value(STUDENT_MEASUREMENTS_LABEL, MEASWAVE_COMPONENT,
                               new_value, index)
        self.story_state.update_student_data()
        self.stage_state.spectrum_clicked = True
    
    #@print_function_name
    def on_spectrum_click_example_galaxy(self, event):
        specview = self.get_viewer("spectrum_viewer")
        if event["event"] != "click" or not specview.line_visible:
            return

        new_value = round(event["domain"]["x"], 0)
        # table = self.get_widget("example_galaxy_table")
        index = self.example_galaxy_table.index
        #print(index, f"index is none: {index is None}")
        data = self.example_galaxy_table.glue_data
        if data[NAME_COMPONENT][index] in self.get_data(EXAMPLE_GALAXY_MEASUREMENTS)[NAME_COMPONENT]:
            
            self.stage_state.waveline_set = True
            self.stage_state.lambda_obs = new_value

            if index is None:
                return

           # if we're on the first example galaxy and we've reached the tutorial, don't allow changes to
           # the first measurement anymore. when it changes to the second measurement we'll allow it again
            if (index == 0) and (self.stage_state.marker_reached('che_mea1')):
               # don't allow user to change the first measurement once we begin the tutorial section
               return
            self.update_data_value(EXAMPLE_GALAXY_MEASUREMENTS, MEASWAVE_COMPONENT,
                               new_value, index)
            # if we are in the tutorial, update the velocity
            if self.stage_state.marker_reached('dot_seq13'):
                self.stage_state.meas_two_made = True
                velocity = velocity_from_wavelengths(new_value,data[RESTWAVE_COMPONENT][index])
                self.update_data_value(EXAMPLE_GALAXY_MEASUREMENTS, VELOCITY_COMPONENT,
                                       velocity, index)
                if self.stage_state.marker == 'dot_seq13a':
                    self.stage_state.marker_forward = 1
            # self.story_state.update_student_data()
            self.stage_state.spectrum_clicked = True
    
    #@print_function_name
    def vue_add_current_velocity(self, _args=None):
        data = self.get_data(STUDENT_MEASUREMENTS_LABEL)
        index = self.galaxy_table.index
        if index is not None:
            lamb_rest = data[RESTWAVE_COMPONENT][index]
            lamb_meas = data[MEASWAVE_COMPONENT][index]
            velocity = velocity_from_wavelengths(lamb_meas, lamb_rest)
            self.update_data_value(STUDENT_MEASUREMENTS_LABEL, VELOCITY_COMPONENT,
                                   velocity, index)
            self.story_state.update_student_data()
    
    #@print_function_name
    def add_student_velocity(self, table, *args, **kwargs):
        index = table.index
        data_label = table._glue_data.label
        if self.stage_state.student_vel is None:
            return
        velocity = round(self.stage_state.student_vel)
        self.update_data_value(data_label, VELOCITY_COMPONENT,
                            velocity, index)

    @property
    def selection_tool(self):
        return self.get_component("py-selection-tool")

    @property
    def slideshow(self):
        return self.get_component('py-spectrum-slideshow')

    #@print_function_name
    def _update_image_location(self, using_voila):
        prepend = "voila/files/" if using_voila else ""
        self.stage_state.image_location = prepend + "data/images/stage_one_spectrum"

    @property
    def galaxy_table(self):
        return self.get_widget("galaxy_table")
    
    @property
    def example_galaxy_table(self):
        return self.get_widget("example_galaxy_table")
    
    def outside_bad_velocity_limit(self, measwave,  restwave, z):
        """
        Returns boolean area where True indicates a bad velocity measurement
        """
        z_meas =  (measwave - restwave) / restwave
        fractional_difference = (((z_meas - z) / z)** 2)**0.5
        return fractional_difference > self.stage_state.velocity_tolerance
        
    
    def velocity_guard(self):
        """
        Returns boolean area where True indicates a bad velocity measurement
        """
        data = self.get_data(STUDENT_MEASUREMENTS_LABEL)
        wavelength = data[MEASWAVE_COMPONENT][:]
        good = wavelength != None
        wavelength = wavelength[good]
        if len(wavelength) == 0:
            return []
        rest_wavelength = data[RESTWAVE_COMPONENT][good]
        # calculate velocity from wavelength        
        outside_tol = self.outside_bad_velocity_limit(wavelength, rest_wavelength,  data[Z_COMPONENT][good])
        bad_velocities = zeros(len(data[MEASWAVE_COMPONENT]))
        bad_velocities[good] = outside_tol
        return bad_velocities
    
    def num_bad_student_velocities(self):
        velocity_guard = self.velocity_guard()
        num = sum(velocity_guard)
        
        self.stage_state.bad_velocity_index = [i for i, x in enumerate(velocity_guard) if x]
        self.stage_state.has_multiple_bad_velocities = num > 1
        self.stage_state.has_bad_velocities = num == 1
        return num
    
    def select_bad_measurement_row(self):
        if self.stage_state.has_bad_velocities:
                if len(self.stage_state.bad_velocity_index) > 0:
                    index = self.stage_state.bad_velocity_index[0]
                    galaxy = self.galaxy_table.items[index]
                    self.galaxy_table.selected = [galaxy]

    def update_spectrum_style(self, dark):
        spectrum_viewer = self.get_viewer("spectrum_viewer")
        theme_name = "dark" if dark else "light"
        style = load_style(f"default_spectrum_{theme_name}")
        update_figure_css(spectrum_viewer, style_dict=style)


    def _update_viewer_style(self, dark):
        viewers = ['dotplot_viewer','dotplot_viewer_2','dotplot_viewer_3']
        viewer_type = ["histogram","histogram","histogram"]
        theme_name = "dark" if dark else "light"
        for viewer, vtype in zip(viewers, viewer_type):
            viewer = self.get_viewer(viewer)
            style = load_style(f"default_{vtype}_{theme_name}")
            update_figure_css(viewer, style_dict=style)

    def _on_dark_mode_change(self, dark):
        super()._on_dark_mode_change(dark)
        self.update_spectrum_style(dark)
        self._update_viewer_style(dark)
    
    #@print_function_name
    def _empty_spectrum_viewer(self):
        dc_name = SPECTRUM_DATA_LABEL
        spec_data = self.get_data(dc_name)
        data = Data(label=spec_data.label, **{
            c.label: [0] for c in spec_data.main_components
        })
        spectrum_viewer = self.get_viewer("spectrum_viewer")
        self.story_state.update_data(dc_name, data)
        spectrum_viewer.update("", "", 0)

    def _on_selection_tool_flagged(self, change):
        if not change["new"]:
            return
        index = self.galaxy_table.index
        if index is None:
            return
        item = self.galaxy_table.selected[0]
        galaxy_name = item["name"]
        self.remove_measurement(galaxy_name)

    def _on_selection_tool_selected(self, change):
        self.stage_state.gal_selected = change['new']

    def _on_spectrum_flagged(self, flagged):
        if not flagged:
            return
        # index = self.galaxy_table.index
        item = self.galaxy_table.selected[0]
        galaxy_name = item["name"]
        self.remove_measurement(galaxy_name)
        self._empty_spectrum_viewer()

        spectrum_viewer = self.get_viewer("spectrum_viewer")
        if spectrum_viewer.toolbar.tools.get("hubble:specflag") is not None:
            sf_tool = spectrum_viewer.toolbar.tools["hubble:specflag"]
            with ignore_callback(sf_tool, "flagged"):
                sf_tool.flagged = False
    
    #@print_function_name
    def update_velocities(self, table = None, tool=None):
        # if table is None:
        #     table = self.galaxy_table
        for table in [self.galaxy_table, self.example_galaxy_table]:
            data = table.glue_data
            for item in table.items:
                index = table.indices_from_items([item])[0]
                if index is not None :#and data[VELOCITY_COMPONENT][index] is None:
                    lamb_rest = data[RESTWAVE_COMPONENT][index]
                    lamb_meas = data[MEASWAVE_COMPONENT][index]
                    if lamb_rest is None or lamb_meas is None or (lamb_meas==0):
                        continue
                    velocity = velocity_from_wavelengths(lamb_meas, lamb_rest)
                    self.update_data_value(data.label, VELOCITY_COMPONENT,
                                        velocity, index)
            self.story_state.update_student_data()

            if tool is not None:
                table.update_tool(tool)
        
    #@print_function_name
    def vue_update_velocities(self, _args):
        self.update_velocities(self.galaxy_table)
    
    #@print_function_name
    def enable_velocity_tool(self, enable):
        if enable:
            tool = self.galaxy_table.get_tool("update-velocities")
            tool["disabled"] = False
            self.galaxy_table.update_tool(tool)

    #@print_function_name
    def initialize_spectrum_data(self, label):
        data = self.get_data(label)
        if data.size > 0:
            name = data[data.id['name']][0]
            spectype = data[data.id['type']][0]
            self.story_state.load_spectrum_data(name, spectype)
            data = self.get_data(name.split(".")[0])
            self.story_state.update_data(SPECTRUM_DATA_LABEL, data)

    def _on_stage_complete(self, complete):
        return 
        if complete:
            self.story_state.stage_index = 2
           #print("end Stage 1. stage_state.stage_1_complete value after last guideline:", self.stage_state.stage_1_complete)

            # We need to do this so that the stage will be moved forward every
            # time the button is clicked, not just the first
            self.stage_state.stage_1_complete = False
    
    def vue_stage_one_complete(self, *args):
        # print('vue_stage_one_complete')
        self.story_state.stage_index = 2
        self.stage_state.stage_1_complete = False

    def vue_print_state(self, _args=None):
       # pass
       print("stage state:")
       print(self.stage_state)
       print("   ")
       print("story state:")
       print(self.story_state)

    def fill_table(self, table, tool=None):
        self.update_data_value(table._glue_data.label, MEASWAVE_COMPONENT, 6830, 0) 
        self.update_data_value(table._glue_data.label, VELOCITY_COMPONENT, 12130, 0)

    def vue_fill_table(self, _args):
        self.fill_table(self.example_galaxy_table)
