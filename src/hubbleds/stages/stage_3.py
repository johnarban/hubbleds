import logging
import requests

import astropy.units as u
from astropy.coordinates import SkyCoord
from cosmicds.components.table import Table
from cosmicds.phases import CDSState
from cosmicds.registries import register_stage
from cosmicds.utils import load_template, API_URL
from echo import CallbackProperty, add_callback, ignore_callback, callback_property
from traitlets import default, Bool

from ..components import DistanceSidebar, DistanceTool, DosDontsSlideShow
from ..data_management import *
from ..stage import HubbleStage
from ..utils import DISTANCE_CONSTANT, GALAXY_FOV, HUBBLE_ROUTE_PATH, IMAGE_BASE_URL, distance_from_angular_size, format_fov

from ..viewers import HubbleDotPlotView
from ..data.styles import load_style
from cosmicds.utils import  update_figure_css
from numpy import searchsorted

from bqplot.marks import Scatter


log = logging.getLogger()

import inspect
def print_log(*args, **kwargs):
    if True:
        print(*args, **kwargs)
    return
def print_function_name(func):
    def wrapper(*args, **kwargs):
        calling_function_name = inspect.stack()[1][3]
        print_log(f"Calling  {func.__name__} from {calling_function_name}")
        return func(*args, **kwargs)
    return wrapper

class StageState(CDSState):
    intro = CallbackProperty(True)
    galaxy = CallbackProperty({})
    galaxy_selected = CallbackProperty(False)
    galaxy_dist = CallbackProperty(None)
    dos_donts_opened = CallbackProperty(False)
    make_measurement = CallbackProperty(False)
    angsizes_total = CallbackProperty(0)
    distances_total = CallbackProperty(0)

    marker = CallbackProperty("")
    indices = CallbackProperty({})
    advance_marker = CallbackProperty(True)
    image_location_distance = CallbackProperty(f"{IMAGE_BASE_URL}/stage_two_distance")
    image_location_dosdonts = CallbackProperty(f"{IMAGE_BASE_URL}/stage_two_dos_donts")
    distance_sidebar = CallbackProperty(False)
    n_meas = CallbackProperty(0)
    show_ruler = CallbackProperty(False)
    meas_theta = CallbackProperty(0)
    distance_calc_count = CallbackProperty(0)
    ruler_clicked_total = CallbackProperty(0)
    
    show_dotplot1 = CallbackProperty(False)
    show_dotplot2 = CallbackProperty(False)
    show_dotplot1_ang = CallbackProperty(False)
    show_dotplot2_ang = CallbackProperty(False)
    show_exgal_table = CallbackProperty(False)
    show_galaxy_table = CallbackProperty(False)
    
    dot_seq2_q = CallbackProperty(False)
    dot_seq4_q = CallbackProperty(False)
    dot_seq6_q = CallbackProperty(False)
    exgal_second_row_selected = CallbackProperty(False)
    
    # distance calc component variables
    distance_const = CallbackProperty(DISTANCE_CONSTANT)
    
    # stage 3 complete component variables
    stage_3_complete = CallbackProperty(False)

    markers = CallbackProperty([
        'ang_siz1',
        'cho_row1',
        'ang_siz2',
        'ang_siz2b',
        'ang_siz3',
        'ang_siz4',
        'ang_siz5',
        'est_dis1',
        'est_dis2',
        'cho_row2',
        'est_dis3',
        'est_dis4',
        'dot_seq1', # show dot plot dist
        'dot_seq2',
        'dot_seq3',
        'dot_seq4', # show dot plot ang size
        'ang_siz5a', # directs to dos/donts # hide angular size
        'dot_seq5', 
        'dot_seq6a', 
        'dot_seq6', # show dot plot dist 2
        'rep_rem1',
        'fil_rem1',
        'two_com1',
    ])

    step_markers = CallbackProperty([
        'ang_siz1',
        'est_dis1'
    ])

    csv_highlights = CallbackProperty([
        'ang_siz1',
        'ang_siz2',
        'ang_siz2b',
        'ang_siz3',
        'ang_siz4',
        'ang_siz5',
        'ang_siz6',
        'rep_rem1',
        'est_dis1',
        'est_dis2',
    ])

    table_highlights = CallbackProperty([
        'cho_row1',
        'cho_row2',
        'est_dis3',
        'est_dis4',
        'fil_rem1',
        'two_com1',
    ])
    
    distance_tool_shown = CallbackProperty([
        'ang_siz1',
        'cho_row1',
        'ang_siz2',
        'ang_siz2b',
        'ang_siz3',
        'ang_siz4',
        'ang_siz5',
        'est_dis1',
        'est_dis2',
        'cho_row2',
        'est_dis3',
        'est_dis4',
        'ang_siz5a', 
        'dot_seq5', 
        'dot_seq6', 
        'rep_rem1',
        'fil_rem1',
        'two_com1',
    ])

    _NONSERIALIZED_PROPERTIES = [
        'markers', 'indices', 'step_markers',
        'csv_highlights', 'table_highlights',
        'distances_total', 'image_location'
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

    def move_marker_forward(self, marker_text, _value=None):
        index = min(self.markers.index(marker_text) + 1, len(self.markers) - 1)
        self.marker = self.markers[index]
    
    def marker_after(self, marker):
        return self.indices[self.marker] > self.indices[marker]

    def marker_reached(self, marker):
        return self.indices[self.marker] >= self.indices[marker]

    def marker_index(self, marker):
        return self.indices[marker]
    

@register_stage(story="hubbles_law", index=3, steps=[
    "MEASURE SIZE",
    "ESTIMATE DISTANCE"
])
class StageTwo(HubbleStage):
    show_team_interface = Bool(False).tag(sync=True)

    _state_cls = StageState

    @default('template')
    def _default_template(self):
        return load_template("stage_3.vue", __file__)

    @default('stage_icon')
    def _default_stage_icon(self):
        return "2"

    @default('title')
    def _default_title(self):
        return "Galaxy Distances"

    @default('subtitle')
    def _default_subtitle(self):
        return "Perhaps a small blurb about this stage"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        dosdonts_slideshow = DosDontsSlideShow(self.stage_state.image_location_dosdonts)
        self.add_component(dosdonts_slideshow, label='py-dosdonts-slideshow')
        dosdonts_slideshow.observe(self._dosdonts_opened, names=['opened'])

        add_callback(self.stage_state, 'stage_3_complete', self._on_stage_complete)
        
        self.show_team_interface = self.app_state.show_team_interface

        self.add_component(DistanceTool(), label="py-distance-tool")
        
        dotplot_viewer_ang = self.add_viewer(HubbleDotPlotView, label='dotplot_viewer_ang', viewer_label = 'First Angular Size Measurement')
        dotplot_viewer_ang_2 = self.add_viewer(HubbleDotPlotView, label='dotplot_viewer_ang_2', viewer_label = 'Second Angular Size Measurement')
        
        dotplot_viewer_dist = self.add_viewer(HubbleDotPlotView, label='dotplot_viewer_dist', viewer_label = 'First Distance Measurement')
        dotplot_viewer_dist_2 = self.add_viewer(HubbleDotPlotView, label='dotplot_viewer_dist_2', viewer_label = 'Second Distance Measurement')
        
        dotplot_viewer_ang._label_text = lambda value: f"{value:.1f} arcmin"
        dotplot_viewer_ang_2._label_text = lambda value: f"{value:.1f} arcmin"
        
        dotplot_viewer_dist._label_text = lambda value: f"{value:.1f} Mpc"
        dotplot_viewer_dist_2._label_text = lambda value: f"{value:.1f} Mpc"
        
        for viewer in [dotplot_viewer_ang, dotplot_viewer_ang_2, dotplot_viewer_dist, dotplot_viewer_dist_2]:
            viewer.toolbar.set_tool_enabled('hubble:towerselect', False)
        
        example_galaxy_data = self.get_data(EXAMPLE_GALAXY_SEED_DATA)
        first = next((s for s in example_galaxy_data.subsets if s.label=='first measurement'), None)
        second = next((s for s in example_galaxy_data.subsets if s.label=='second measurement'), None)
        
        
        
        dotplot_viewer_ang.ignore(lambda layer: layer in [second])
        dotplot_viewer_dist.ignore(lambda layer: layer in [second])
        
        dotplot_viewer_ang_2.ignore(lambda layer: layer in [first])
        dotplot_viewer_dist_2.ignore(lambda layer: layer in [first])
        
        self.setup_dotplot_viewers()
        
        add_distances_tool = \
            dict(id="update-distances",
                 icon="mdi-tape-measure",
                 tooltip="Fill in distances",
                 disabled=True,
                 activate=self.update_distances)
        distance_table = Table(self.session,
                               data=self.get_data(STUDENT_MEASUREMENTS_LABEL),
                               glue_components=[NAME_COMPONENT,
                                                ANGULAR_SIZE_COMPONENT,
                                                DISTANCE_COMPONENT],
                               key_component=NAME_COMPONENT,
                               names=['Galaxy Name',
                                      'θ (arcsec)',
                                      'Distance (Mpc)'],
                               title='My Galaxies',
                               selected_color=self.table_selected_color(
                                   self.app_state.dark_mode),
                               use_subset_group=False,
                               single_select=True,
                               tools=[add_distances_tool])

        self.add_widget(distance_table, label="distance_table")
        distance_table.observe(
            self.distance_table_selected_change, names=["selected"])
        
        add_distances_tool = \
            dict(id="update-distances",
                 icon="mdi-tape-measure",
                 tooltip="Fill in distances",
                 disabled=True,
                 activate=self.update_distances)
        example_galaxy_distance_table = Table(self.session,
                               data=self.get_data(EXAMPLE_GALAXY_MEASUREMENTS),
                               glue_components=[NAME_COMPONENT,
                                                ANGULAR_SIZE_COMPONENT,
                                                DISTANCE_COMPONENT,
                                                MEASUREMENT_NUMBER_COMPONENT],
                               key_component=MEASUREMENT_NUMBER_COMPONENT,
                               names=['Galaxy Name',
                                      'θ (arcsec)',
                                      'Distance (Mpc)',
                                      'Measurement Number'],
                               title='Example Galaxy',
                               selected_color=self.table_selected_color(
                                   self.app_state.dark_mode),
                               use_subset_group=False,
                               item_filter= lambda item: item[MEASUREMENT_NUMBER_COMPONENT] == 'first',
                               single_select=True,
                               tools=[add_distances_tool])

        self.add_widget(example_galaxy_distance_table, label="example_galaxy_distance_table")
        example_galaxy_distance_table.observe(
            self.distance_table_selected_change, names=["selected"])

        self.add_component(DistanceSidebar(self.stage_state),
                           label="py-distance-sidebar")
        self.distance_tool.observe(self._angular_size_update,
                                   names=["angular_size"])
        self.distance_tool.observe(self._angular_height_update,
                                   names=["angular_height"])
        self.distance_tool.observe(self._ruler_click_count_update,
                                   names=['ruler_click_count'])
        self.distance_tool.observe(self._measurement_count_update,
                                   names=['measurement_count'])
        self.distance_sidebar.angular_height = format_fov(
            self.distance_tool.angular_height)

        self.distance_tool.observe(self._distance_tool_flagged,
                                   names=["flagged"])

        add_callback(self.stage_state, 'galaxy', self._on_galaxy_changed)
        add_callback(self.stage_state, 'show_ruler', self._show_ruler_changed)

        # Callbacks
        add_callback(self.stage_state, 'marker',
                     self._on_marker_update, echo_old=True)
        add_callback(self.story_state, 'step_index',
                     self._on_step_index_update)
        self.trigger_marker_update_cb = True

        add_callback(self.stage_state, 'make_measurement',
                     self._make_measurement)
        add_callback(self.stage_state, 'distance_calc_count',
                     self.add_student_distance)
        
        if self.stage_state.marker_before('rep_rem1'):
            self.current_table = self.example_galaxy_distance_table
        else:
            self.current_table = self.distance_table
        
        # ang_siz2 -> cho_row1, est_dis3 -> cho_row2
        for marker in ['ang_siz2', 'est_dis3']:
            if self.stage_state.marker_reached(marker):
                marker_index = self.stage_state.markers.index(marker)
                new_index = marker_index - 1
                self.stage_state.marker = self.stage_state.marker[new_index]
        
    def setup_dotplot_viewers(self):
        
        dist_dotplots = [self.get_viewer('dotplot_viewer_dist'), self.get_viewer('dotplot_viewer_dist_2')]
        ang_dotplots = [self.get_viewer('dotplot_viewer_ang'), self.get_viewer('dotplot_viewer_ang_2')]
        
        data = self.get_data(EXAMPLE_GALAXY_SEED_DATA)
        
        for viewer in dist_dotplots + ang_dotplots:
            viewer.add_data(data)
            viewer.layer_artist_for_data(data).visible = False
            if viewer in dist_dotplots:
                viewer.state.x_att = data.id[DB_DISTANCE_FIELD]
                viewer.figure.axes[0].label = 'Distance (Mpc)'
            elif viewer in ang_dotplots:
                viewer.state.x_att = data.id[DB_ANGSIZE_FIELD]
                viewer.figure.axes[0].label = 'Angular Size (arcminutes))'
            viewer.state.hist_n_bin = 75
            viewer.state.alpha = 1
            viewer.state.reset_limits()
            viewer.state.viewer_height = 150
            viewer.layer_artist_for_data(data).state.color = '#787878'
        
        self._update_viewer_style(dark=self.app_state.dark_mode)
        
    def _on_marker_update(self, old, new):
        # print_log(f"Marker update: {old} -> {new}")
        if not self.trigger_marker_update_cb:
            return
        markers = self.stage_state.markers
        if new not in markers:
            new = markers[0]
            self.stage_state.marker = new
        if old not in markers:
            old = markers[0]
        advancing = markers.index(new) > markers.index(old)
        if new in self.stage_state.step_markers and advancing:
            self.story_state.step_complete = True
            self.story_state.step_index = self.stage_state.step_markers.index(
                new)
        if advancing and (new == "cho_row1" or new == "cho_row2"):
            self.distance_table.selected = []
            self.example_galaxy_distance_table.selected = []
            self.distance_tool.reset_canvas()
            # need to turn off ruler marker also.False
            # and start stage 2 at the start coordinates
        
        if advancing and (new == 'ang_siz5'):
            self.distance_tool.reset_canvas()

        if advancing and (new == "dot_seq1"):
            self.show_dotplot1 = True
            
        if advancing and (new == 'dot_seq4'):
            self.show_dotplot1_ang = True
            v1 = self.get_viewer('dotplot_viewer_dist')
            v2 = self.get_viewer('dotplot_viewer_ang')
            # previous line shows up when you click on the figure
            v1.show_previous_line(show = True, show_label = True)
            v2.show_previous_line(show = True, show_label = True)

            def _on_dotplot_click(plot, event = None):
                # it doesn't matter which plot we get the event from
                # because d = C / \theta and \theta = C / d
                if event is None:
                    return
                the_other_plot = v2 if plot is v1 else v1
                event['domain']['x'] = self.binned_x(the_other_plot.state.bins, DISTANCE_CONSTANT / event['domain']['x'])
                the_other_plot._on_click(event)

            v1.add_event_callback(lambda event:_on_dotplot_click(v1,event), events=['click'])
            v2.add_event_callback(lambda event:_on_dotplot_click(v2,event), events=['click'])
            
        if advancing and (new == 'dot_seq5'):
            self.show_dotplot1 = False
            self.show_dotplot1_ang = False
            self.show_dotplot2 = False
            
            # self.example_galaxy_distance_table.selected = []
            self.example_galaxy_distance_table.filter_by(None)
            
        if advancing and (new == 'dot_seq6'):
            self.example_galaxy_distance_table.selected = []
            self.show_dotplot2 = True
            self.show_dotplot2_ang = True
            
        if advancing and (new == 'rep_rem1'):
            self.show_dotplot1 = False
            self.show_dotplot2 = False
            self.show_dotplot1_ang = False
            self.show_dotplot2_ang = False
        
        if advancing and (new == 'fil_rem1'):
            tool = self.distance_table.get_tool("update-distances")
            tool["disabled"] = False
            self.distance_table.update_tool(tool)
    
    @staticmethod
    def add_point(viewer, x, color, label = None): 
        scales = {'x': viewer.figure.scale_x, 'y': viewer.figure.scale_y}
        size = viewer.layers[0].bars.default_size 
        return  Scatter(x=[x], y=[1], 
                         scales=scales, colors=[color], 
                         labels=[label], opacities = [1],
                         default_size = size,marker='circle',)

    @staticmethod
    def add_mark(viewer, mark):
        marks = viewer.figure.marks
        # function to flatten list of lists
        def flatten(l):
            return [item for sublist in l for item in (sublist if len(sublist) > 0 else [None])]
        labels = flatten([m.labels for m in marks])
        if mark.labels[0] in labels:
            old_mark = marks[labels.index(mark.labels[0])]
            old_mark.x = mark.x
        else:
            viewer.figure.marks = marks + [mark]
        
        print(viewer,len(viewer.figure.marks))
        
    @staticmethod  
    def binned_x(bins, x):
        # index = searchsorted(bins, x, side='right')
        # return (bins[index] + bins[index-1]) / 2
        bin_width = bins[1] - bins[0]
        index = int((x - bins[0])/bin_width)
        return bins[0] + bin_width * (index + 1/2)
    
    def plot_measurement(self, viewer, x, color, label = None):
        # x needs to be in a bin
        x_bin = self.binned_x(viewer.state.bins, x)
        mark = self.add_point(viewer, x_bin, color, label)
        self.add_mark(viewer, mark)

    def _on_step_index_update(self, index):
        # If we aren't on this stage, ignore
        if self.story_state.stage_index != self.index:
            return

        # Change the marker without firing the associated stage callback
        # We can't just use ignore_callback, since other stuff (i.e. the frontend)
        # may depend on marker callbacks
        self.trigger_marker_update_cb = False
        index = min(index, len(self.stage_state.step_markers) - 1)
        self.stage_state.marker = self.stage_state.step_markers[index]
        self.trigger_marker_update_cb = True

    def _dosdonts_opened(self, msg):
        self.stage_state.dos_donts_opened = msg["new"]
    
    @print_function_name
    def distance_table_selected_change(self, change):
        selected = change["new"]
        if not selected or selected == change["old"]:
            return
        
        table = change["owner"]
        self.current_table = table
        index = table.index
        data = table.glue_data
        galaxy = {x.label: data[x][index] for x in data.main_components}
        self.distance_tool.reset_canvas()
        self.distance_tool.go_to_location(galaxy["ra"], galaxy["decl"],
                                          fov=GALAXY_FOV)

        self.distance_tool.reset_brightness_contrast() # reset the style of viewer
        
        self.stage_state.galaxy = galaxy
        self.stage_state.galaxy_dist = None
        self.distance_tool.measuring_allowed = bool(galaxy)
        self.stage_state.meas_theta = data[ANGULAR_SIZE_COMPONENT][index]

        if self.stage_state.marker == 'cho_row1' or self.stage_state.marker == 'cho_row2':
            self.stage_state.move_marker_forward(self.stage_state.marker)
            self.stage_state.galaxy_selected = True
    
        if self.stage_state.marker == 'dot_seq6a':
            self.stage_state.exgal_second_row_selected = index == 1
        self._update_viewer_style(dark=self.app_state.dark_mode)
    
    @print_function_name
    def _angular_size_update(self, change):
        new_ang_size = change["new"]
        if new_ang_size != 0 and new_ang_size is not None:
            self._make_measurement()
    
    @print_function_name
    def _angular_height_update(self, change):
        self.distance_sidebar.angular_height = format_fov(change["new"])
    
    @print_function_name
    def _ruler_click_count_update(self, change):
        count = change["new"]
        self.stage_state.ruler_clicked_total = count
        if count == 1:
            self.stage_state.marker = 'ang_siz4'  # auto-advance guideline if it's the first ruler click
    
    @print_function_name
    def _measurement_count_update(self, change):
        count = change["new"]
        self.stage_state.n_meas = count
        if count == 1:
            self.stage_state.marker = 'ang_siz5'  # auto-advance guideline if it's the first measurement made

    def _show_ruler_changed(self, show):
        self.distance_tool.show_ruler = show
    
    @print_function_name
    def _on_galaxy_changed(self, galaxy):
        self.distance_tool.galaxy_selected = bool(galaxy)
    
    @print_function_name
    def _make_measurement(self):
        galaxy = self.stage_state.galaxy
        table = self.current_table
        data_label = table._glue_data.label
        index = self.get_data_indices(data_label, NAME_COMPONENT,
                                      lambda x: x == galaxy["name"],
                                      single=True)
        
        angular_size = self.distance_tool.angular_size
        # ang_size_deg = angular_size.value
        # distance = round(MILKY_WAY_SIZE_MPC * 180 / (ang_size_deg * pi))
        # angular_size_as = round(angular_size.to(u.arcsec).value)

        index = table.index
        if index is None:
            return
        data = table.glue_data
        curr_value = data[ANGULAR_SIZE_COMPONENT][index]

        if (curr_value is None) and (data_label == STUDENT_MEASUREMENTS_LABEL):
            self.stage_state.angsizes_total = self.stage_state.angsizes_total + 1

        # self.stage_state.galaxy_dist = distance
        # self.update_data_value(STUDENT_MEASUREMENTS_LABEL, DISTANCE_COMPONENT, distance, index)
        # self.update_data_value(STUDENT_MEASUREMENTS_LABEL, ANGULAR_SIZE_COMPONENT, angular_size_as, index)

        self.stage_state.meas_theta = round(angular_size.to(u.arcsec).value)
        if data_label == STUDENT_MEASUREMENTS_LABEL:
            self.update_data_value(data_label, ANGULAR_SIZE_COMPONENT,
                                self.stage_state.meas_theta, index)
        elif data_label == EXAMPLE_GALAXY_MEASUREMENTS:
            if (index==0) and self.stage_state.marker_reached('dot_seq1'):
                return
            self.update_example_data_value(data_label, ANGULAR_SIZE_COMPONENT,
                               self.stage_state.meas_theta, index)
            colors = ["#FF0000", "#0000FF"]
            labels = ['First', 'Second']
            v1 = self.get_viewer('dotplot_viewer_ang')
            v2 = self.get_viewer('dotplot_viewer_ang_2')
            
            v3 = self.get_viewer('dotplot_viewer_dist')
            v4 = self.get_viewer('dotplot_viewer_dist_2')

            
            self.plot_measurement(v1, self.stage_state.meas_theta, color = colors[index], label = labels[index])
            self.plot_measurement(v2, self.stage_state.meas_theta, color = colors[index], label = labels[index])
            self.plot_measurement(v3, distance_from_angular_size(self.stage_state.meas_theta), color = colors[index], label = labels[index])
            self.plot_measurement(v4, distance_from_angular_size(self.stage_state.meas_theta), color = colors[index], label = labels[index])
            
            if self.stage_state.marker_after('est_dis4'):
                self.add_student_distance()
            
            for val in ['x_min','x_max','layers']:
                add_callback(v1.state, val , lambda x: self.plot_measurement(v1, self.stage_state.meas_theta, color = colors[index], label = labels[index]))
                add_callback(v2.state, val , lambda x: self.plot_measurement(v2, self.stage_state.meas_theta, color = colors[index], label = labels[index]))
                add_callback(v3.state, val , lambda x: self.plot_measurement(v3, distance_from_angular_size(self.stage_state.meas_theta), color = colors[index], label = labels[index]))
                add_callback(v4.state, val , lambda x: self.plot_measurement(v4, distance_from_angular_size(self.stage_state.meas_theta), color = colors[index], label = labels[index]))
            

        # if data_label == STUDENT_MEASUREMENTS_LABEL:
        #     self.story_state.update_student_data()
        with ignore_callback(self.stage_state, 'make_measurement'):
            self.stage_state.make_measurement = False

    def _distance_tool_flagged(self, change):
        if not change["new"]:
            return
        

        galaxy = self.state.galaxy
        if galaxy["id"]:
            data = {"galaxy_id": int(galaxy["id"])}
        else:
            name = galaxy["name"]
            if not name.endswith(".fits"):
                name += ".fits"
            data = {"galaxy_name": name}
        requests.post(f"{API_URL}/{HUBBLE_ROUTE_PATH}/mark-tileload-bad",
                      json=data)

        index = self.distance_table.index
        if index is None:
            return
        item = self.distance_table.selected[0]
        galaxy_name = item["name"]
        self.remove_measurement(galaxy_name)
        self.distance_tool.flagged = False
    
    @print_function_name
    def add_student_distance(self, _args=None):
        table = self.current_table
        index = table.index
        if index is None:
            return
        distance = distance_from_angular_size(self.stage_state.meas_theta)
        if table is self.distance_table:
            self.update_data_value(table._glue_data.label, DISTANCE_COMPONENT, distance,
                                index)
        elif table is self.example_galaxy_distance_table:
            self.update_example_data_value(table._glue_data.label, DISTANCE_COMPONENT, distance,
                                index)
        self.story_state.update_student_data()
        if self.stage_state.distance_calc_count == 1:  # as long as at least one thing has been measured, tool is enabled. But if students want to loop through calculation by hand they can.
            self.enable_distance_tool(True)
        self.get_distance_count()
    
    @print_function_name
    def update_distances(self, table, tool=None):
        data = table.glue_data
        for item in table.items:
            index = table.indices_from_items([item])[0]
            if index is not None and data[DISTANCE_COMPONENT][index] is None:
                theta = data[ANGULAR_SIZE_COMPONENT][index]
                if (theta is None) or (theta == 0):
                    continue
                print(theta)
                distance = distance_from_angular_size(theta)
                if table is self.distance_table:
                    self.update_data_value(table._glue_data.label, DISTANCE_COMPONENT,
                                       distance, index)
                elif table is self.example_galaxy_distance_table:
                    self.update_example_data_value(table._glue_data.label, DISTANCE_COMPONENT,
                                        distance, index)

        self.story_state.update_student_data()
        if tool is not None:
            table.update_tool(tool)
        self.get_distance_count()
    
    @print_function_name
    def vue_update_distances(self, _args):
        self.update_distances(self.distance_table)
        self.update_distances(self.example_galaxy_distance_table)
    
    @print_function_name
    def vue_add_distance_data_point(self, _args=None):
        self.stage_state.make_measurement = True

    def enable_distance_tool(self, enable):
        if enable:
            tool = self.distance_table.get_tool("update-distances")
            tool["disabled"] = False
            self.distance_table.update_tool(tool)
            
            tool = self.example_galaxy_distance_table.get_tool("update-distances")
            tool["disabled"] = False
            self.example_galaxy_distance_table.update_tool(tool)
    
    def get_distance_count(self):
        student_measurements = self.get_data(STUDENT_MEASUREMENTS_LABEL)
        distances = student_measurements[DISTANCE_COMPONENT]
        self.stage_state.distances_total = distances[distances != None].size
    
    def _update_viewer_style(self, dark):
        viewers = ['dotplot_viewer_ang','dotplot_viewer_ang_2','dotplot_viewer_dist','dotplot_viewer_dist_2']
        viewer_type = ["histogram","histogram","histogram","histogram"]
        theme_name = "dark" if dark else "light"
        for viewer, vtype in zip(viewers, viewer_type):
            viewer = self.get_viewer(viewer)
            style = load_style(f"default_{vtype}_{theme_name}")
            update_figure_css(viewer, style_dict=style)
    
    def _on_dark_mode_change(self, dark):
        super()._on_dark_mode_change(dark)
        self._update_viewer_style(dark)
    
    @property
    def distance_sidebar(self):
        return self.get_component("py-distance-sidebar")

    @property
    def distance_tool(self):
        return self.get_component("py-distance-tool")

    @property
    def distance_table(self):
        return self.get_widget("distance_table")
    
    @property
    def example_galaxy_distance_table(self):
        return self.get_widget("example_galaxy_distance_table")
    
    @property
    def current_table_data_label(self):
        return self.current_table._glue_data.label

    @property
    def last_guideline(self):
        return self.get_component('guideline-stage-3-complete')

    def _on_stage_complete(self, complete):
        if complete:
            self.story_state.stage_index = 4

            # We need to do this so that the stage will be moved forward every
            # time the button is clicked, not just the first
            self.last_guideline.stage_3_complete = False
