import logging

import astropy.units as u
from cosmicds.components.table import Table
from cosmicds.phases import CDSState
from cosmicds.registries import register_stage
from cosmicds.utils import extend_tool, load_template, API_URL
from echo import CallbackProperty, add_callback, ignore_callback, callback_property, delay_callback, ListCallbackProperty
from traitlets import default, Bool

from ..components import DistanceSidebar, DistanceTool, DosDontsSlideShow
from ..data_management import *
from ..stage import HubbleStage
from ..utils import DISTANCE_CONSTANT, GALAXY_FOV, HUBBLE_ROUTE_PATH, IMAGE_BASE_URL, distance_from_angular_size, format_fov

from ..viewers import HubbleDotPlotView
from ..data.styles import load_style
from cosmicds.utils import  update_figure_css

from bqplot.marks import Scatter

from glue_jupyter.link import link
from glue.core.message import NumericalDataChangedMessage
from functools import partial

log = logging.getLogger()

import inspect
def print_log(*args, **kwargs):
    if False:
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
    bad_angsize = CallbackProperty(False)
    bad_angsize_index = CallbackProperty(None)
    
    show_dotplot1 = CallbackProperty(False)
    show_dotplot2 = CallbackProperty(False)
    show_dotplot1_ang = CallbackProperty(False)
    show_dotplot2_ang = CallbackProperty(False)
    show_exgal_table = CallbackProperty(False)
    show_galaxy_table = CallbackProperty(False)
    
    dot_seq2_q = CallbackProperty(False)
    dot_seq4a_q = CallbackProperty(False)
    dot_seq6_q = CallbackProperty(False)
    exgal_second_row_selected = CallbackProperty(False)
    exgal_second_measured = CallbackProperty(False) # This should initialize as False and be set to True when the condition is met - will do later.
    
    brightness = CallbackProperty(1.0)

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
        'dot_seq4a',
        'ang_siz5a', # directs to dos/donts # hide angular size
        'dot_seq5', 
        'dot_seq5a',
        'dot_seq5b',
        'dot_seq5c',
        'dot_seq6', # show dot plot dist 2
        'dot_seq7',
        'rep_rem1',
        'fil_rem1',
    ])

    step_markers = ListCallbackProperty([])

    # step_markers = CallbackProperty([
    #     'ang_siz1',
    #     'est_dis1'
    # ])

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
    ])

    _NONSERIALIZED_PROPERTIES = [
        'markers', 'indices', #'step_markers',
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
        if value is None:
            return
        index = self.indices[self.marker]
        new_index = min(max(index - value, 0), len(self.markers) - 1)
        self.marker = self.markers[new_index]

    @marker_forward.setter
    def marker_forward(self, value):
        if value is None:
            return
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
    # "MEASURE SIZE",
    # "ESTIMATE DISTANCE"
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
        
        # What we really want is for enable_distance_tool to be true if initialized at fil_rem1, but that isn't working, so this is our hacky fix for now. (And really, they shouldn't have to re-click the measuring tape if their distances are already there. It should just be 'next')
        if self.stage_state.marker in ['fil_rem1']: 
            self.stage_state.marker_backward = 1
        
        dosdonts_slideshow = DosDontsSlideShow(self.stage_state.image_location_dosdonts)
        self.add_component(dosdonts_slideshow, label='py-dosdonts-slideshow')
        dosdonts_slideshow.observe(self._dosdonts_opened, names=['opened'])

        add_callback(self.stage_state, 'stage_3_complete', self._on_stage_complete)
        
        self.show_team_interface = self.app_state.show_team_interface

        self.add_component(DistanceTool(), label="py-distance-tool")
        
        dotplot_viewer_ang = self.add_viewer(HubbleDotPlotView, label='dotplot_viewer_ang', viewer_label = 'First Angular Size Measurement')
        
        dotplot_viewer_dist = self.add_viewer(HubbleDotPlotView, label='dotplot_viewer_dist', viewer_label = 'First Distance Measurement')
        dotplot_viewer_dist_2 = self.add_viewer(HubbleDotPlotView, label='dotplot_viewer_dist_2', viewer_label = 'Second Distance Measurement')
        
        dotplot_viewer_ang._label_text = lambda value: f"{value:.0f} arcsec"
        
        dotplot_viewer_dist._label_text = lambda value: f"{value:.0f} Mpc"
        dotplot_viewer_dist_2._label_text = lambda value: f"{value:.0f} Mpc"
        

        example_galaxy_data = self.get_data(EXAMPLE_GALAXY_SEED_DATA)
        first = next((s for s in example_galaxy_data.subsets if s.label=='first measurement'), None)
        second = next((s for s in example_galaxy_data.subsets if s.label=='second measurement'), None)
        
        dotplot_viewer_ang.ignore(lambda layer: layer in [second])
        dotplot_viewer_dist.ignore(lambda layer: layer in [second])
        
        dotplot_viewer_dist_2.ignore(lambda layer: layer in [first])
        
        self.setup_dotplot_viewers()
        self.get_distance_count()
        
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
                                      '&theta; (arcsec)',
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
        self.distance_table.allow_row_click = not self.stage_state.bad_angsize

        def _on_has_bad_angsize(val):
            self.distance_table.allow_row_click = not self.stage_state.bad_angsize
        
        add_callback(self.stage_state, 'bad_angsize', _on_has_bad_angsize)
        
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
                                      '&theta; (arcsec)',
                                      'Distance (Mpc)',
                                      'Measurement Number'],
                               title='Example Galaxy',
                               selected_color=self.table_selected_color(
                                   self.app_state.dark_mode),
                               use_subset_group=False,
                               item_filter= lambda item: item[MEASUREMENT_NUMBER_COMPONENT] == 'first',
                               single_select=True,
                               tools=[add_distances_tool])

        if self.stage_state.marker_reached('dot_seq5a'):
            example_galaxy_distance_table.filter_by(None)

        if self.stage_state.marker_reached('rep_rem1'):
            self.select_bad_measurement_row()
        
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

        self.distance_tool.activate_guard()
        self.distance_tool.set_guard(max = '30 arcmin', min = '5 arcsec')
        
        add_callback(self.stage_state, 'galaxy', self._on_galaxy_changed)
        add_callback(self.stage_state, 'show_ruler', self._show_ruler_changed)
        add_callback(self.stage_state, 'brightness', self._update_brightness)

        # Callbacks
        add_callback(self.stage_state, 'marker',
                     self._on_marker_update, echo_old=True)
        # add_callback(self.story_state, 'step_index',
        #              self._on_step_index_update)
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
        if self.stage_state.marker in ['ang_siz2', 'est_dis3']:
            marker_index = self.stage_state.markers.index(self.stage_state.marker)
            new_index = marker_index - 1
            self.stage_state.marker = self.stage_state.markers[new_index]
        
        if self.stage_state.marker_reached('fil_rem1'):
            self.enable_distance_tool(True)
        
        # Show_ruler should be true from marker ang_siz3 to est_dis4 (inclusive) and from dot_seq5b forward.
        if  self.stage_state.marker_reached('ang_siz3') and (not self.stage_state.marker_after('est_dis4')):
            self.stage_state.show_ruler = True
        elif self.stage_state.marker_reached('dot_seq5b'):
            self.stage_state.show_ruler = True
        else:
            self.stage_state.show_ruler = False
        self._show_ruler_changed(self.stage_state.show_ruler)
            
        if self.stage_state.marker_reached("ang_siz5a"):
            # hide lines
            dotplot_viewer_dist.remove_lines_from_figure(line=True, previous_line = True)
            dotplot_viewer_ang.remove_lines_from_figure(line=True, previous_line = True)
            
        if self.stage_state.marker_reached("dot_seq4"):
            v1 = dotplot_viewer_dist
            v2 = dotplot_viewer_ang
            v1.add_event_callback(lambda event:self._on_dotplot_click(v1,event), events=['click'])
            v2.add_event_callback(lambda event:self._on_dotplot_click(v2,event), events=['click'])
            show = self.stage_state.marker_before("ang_siz5a")
            v1.show_previous_line(show = show, show_label = show)
            v2.show_previous_line(show = show, show_label = show)
        
        if self.stage_state.marker_reached("dot_seq6"):
            self.example_galaxy_distance_table.selected = []
            self.stage_state.show_dotplot2 = True
        
       #print('at end of init', self.stage_state.marker)

    def setup_dotplot_viewers(self):
        
        dist_dotplots = [self.get_viewer('dotplot_viewer_dist'), self.get_viewer('dotplot_viewer_dist_2')]
        ang_dotplots = [self.get_viewer('dotplot_viewer_ang')]
        
        data = self.get_data(EXAMPLE_GALAXY_SEED_DATA)
        
        for viewer in dist_dotplots + ang_dotplots:
            viewer.add_data(data)
            viewer.layer_artist_for_data(data).visible = False
            if viewer in dist_dotplots:
                viewer.state.x_att = data.id[DB_DISTANCE_FIELD]
                viewer.figure.axes[0].label = 'Distance (Mpc)'
            elif viewer in ang_dotplots:
                viewer.state.x_att = data.id[DB_ANGSIZE_FIELD]
                viewer.figure.axes[0].label = 'Angular Size (arcseconds))'
            viewer.state.hist_n_bin = 75
            viewer.state.alpha = 1
            viewer.state.reset_limits()
            viewer.state.viewer_height = 150
            viewer.layer_artist_for_data(data).state.color = '#787878'
        
        def d_a(x):
            return DISTANCE_CONSTANT / x
        
        link((dist_dotplots[0].state, 'x_min'), (ang_dotplots[0].state, 'x_max'), d_a, d_a)
        link((dist_dotplots[0].state, 'x_max'), (ang_dotplots[0].state, 'x_min'), d_a, d_a)
        link((dist_dotplots[0].state, 'x_min'), (dist_dotplots[1].state, 'x_min'))
        link((dist_dotplots[0].state, 'x_max'), (dist_dotplots[1].state, 'x_max'))
        
        def set_x_lim(viewer):
            xmin = min(min(m.x) for m in viewer.figure.marks if len(m.x))
            xmax = max(max(m.x) for m in viewer.figure.marks if len(m.x))
            padding = (xmax-xmin) * 0.05
            with delay_callback(viewer.state, 'x_min', 'x_max'):
                viewer.state.x_min = xmin - padding
                viewer.state.x_max = xmax + padding
        viewers = dist_dotplots + ang_dotplots
        for i in range(len(viewers)):
            extend_tool(viewers[i], 'bqplot:home', partial(set_x_lim,viewers[i]), activate_before_tool= False)
        
        self._update_viewer_style(dark=self.app_state.dark_mode)
    
     #@print_function_name
    def _update_state_from_measurements(self):
        student_measurements = self.get_data(STUDENT_MEASUREMENTS_LABEL)
        angsizes = student_measurements[ANGULAR_SIZE_COMPONENT]
        self.stage_state.angsizes_total = angsizes[angsizes != None].size

        
    def _on_marker_update(self, old, new):
        #print_log(f"Marker update: {old} -> {new}")
        if not self.trigger_marker_update_cb:
            return
        markers = self.stage_state.markers
        if new not in markers:
            print_log(f"Marker {new} not found, defaulting to {markers[0]}")
            new = markers[0]
            self.stage_state.marker = new
        if old not in markers:
            old = markers[0]
        advancing = markers.index(new) > markers.index(old)
        # if new in self.stage_state.step_markers and advancing:
        #     self.story_state.step_complete = True
        #     self.story_state.step_index = self.stage_state.step_markers.index(
        #         new)
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
            v1.toolbar.tools['bqplot:home'].activate()
            v2.toolbar.tools['bqplot:home'].activate()
            # previous line shows up when you click on the figure
            v1.show_previous_line(show = True, show_label = True)
            v2.show_previous_line(show = True, show_label = True)
            
            v1.add_event_callback(lambda event:self._on_dotplot_click(v1,event), events=['click'])
            v2.add_event_callback(lambda event:self._on_dotplot_click(v2,event), events=['click'])
        
        if advancing and (new == "ang_siz5a"):
            # hide lines
            v1 = self.get_viewer('dotplot_viewer_dist')
            v2 = self.get_viewer('dotplot_viewer_ang')
            v1.remove_lines_from_figure(line=True, previous_line = True)
            v2.remove_lines_from_figure(line=True, previous_line = True)
            
        if advancing and (new == 'dot_seq5a'):
            self.show_dotplot1 = False
            self.show_dotplot1_ang = False
            self.show_dotplot2 = False
            
            self.example_galaxy_distance_table.selected = []
            self.example_galaxy_distance_table.filter_by(None)
            
        if advancing and (new == 'dot_seq6'):
            v3 = self.get_viewer('dotplot_viewer_dist_2')
            v3.toolbar.tools['bqplot:home'].activate()
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
            
        if advancing and (new in ['rep_rem1', 'fil_rem']) and self.show_team_interface and (self.stage_state.angsizes_total < 5):
            # this condition occurs if we use fill values in stage 1
            self._update_state_from_measurements()
    
    @staticmethod
    def add_point(viewer, x, color, label=None): 
        scales = {'x': viewer.figure.scale_x, 'y': viewer.figure.scale_y}
        size = viewer.layers[0].bars.default_size 
        return  Scatter(x=[x], y=[1], 
                         scales=scales, colors=[color], 
                         labels=[label], opacities = [1],
                         default_size = size,marker='circle',)

    @staticmethod
    def add_mark(viewer, mark, label = None):
        marks = viewer.figure.marks
        # function to flatten list of lists
        def flatten(l):
            for item in l:
                if len(item.labels) > 0:
                    yield item.labels[0]
                else:
                    yield 'no label'
            # return [item for sublist in l for item in (sublist if len(sublist) > 0 else [None])]
        labels = list(flatten(marks))
        marks = [m for i, m in enumerate(marks) if label != labels[i]]
        viewer.figure.marks = marks + [mark]

        
    @staticmethod  
    def binned_x(bins, x):
        # index = searchsorted(bins, x, side='right')
        # return (bins[index] + bins[index-1]) / 2
        bin_width = bins[1] - bins[0]
        index = int((x - bins[0])/bin_width)
        return bins[0] + bin_width * (index + 1/2)
    
    def plot_measurement(self, viewer, index, distance=False, color='black', label=None):
        viewer = self.get_viewer(viewer)
        x = self.get_data(EXAMPLE_GALAXY_MEASUREMENTS)[ANGULAR_SIZE_COMPONENT][index]
        if distance:
            x = distance_from_angular_size(x)
            label = label + ' (distance)'
        # x needs to be in a bin
        x_bin = self.binned_x(viewer.state.bins, x)
        mark = self.add_point(viewer, x_bin, color, label)
        self.add_mark(viewer, mark, label)

    # def _on_step_index_update(self, index):
    #     # If we aren't on this stage, ignore
    #     if self.story_state.stage_index != self.index:
    #         return

    #     # Change the marker without firing the associated stage callback
    #     # We can't just use ignore_callback, since other stuff (i.e. the frontend)
    #     # may depend on marker callbacks
    #     self.trigger_marker_update_cb = False
    #     index = min(index, len(self.stage_state.step_markers) - 1)
    #     self.stage_state.marker = self.stage_state.step_markers[index]
    #     self.trigger_marker_update_cb = True
    
    def _on_dotplot_click(self,plot, event):
        if self.stage_state.marker_reached('ang_siz5a'):
            return
        # it doesn't matter which plot we get the event from
        # because d = C / \theta and \theta = C / d
        event['domain']['x'] = round(DISTANCE_CONSTANT / event['domain']['x'], 0)
        if event is None:
           #print("No event")
            return
        v1 = self.get_viewer('dotplot_viewer_dist')
        v2 = self.get_viewer('dotplot_viewer_ang')
        
        if plot is v1:
            v2._on_click(event)
        else:
            v1._on_click(event)

    def _dosdonts_opened(self, msg):
        self.stage_state.dos_donts_opened = msg["new"]
    
    #@print_function_name
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
    
        if self.stage_state.marker == 'dot_seq5a':
            self.stage_state.exgal_second_row_selected = index == 1
            if self.stage_state.exgal_second_row_selected == 1:
                self.stage_state.show_ruler = True
                self.stage_state.marker = 'dot_seq5b'
        self._update_viewer_style(dark=self.app_state.dark_mode)
    
    #@print_function_name
    def _angular_size_update(self, change):
        new_ang_size = change["new"]
        if new_ang_size != 0 and new_ang_size is not None:
            self._make_measurement()
    
    #@print_function_name
    def _angular_height_update(self, change):
        self.distance_sidebar.angular_height = format_fov(change["new"])
    
    #@print_function_name
    def _ruler_click_count_update(self, change):
        count = change["new"]
        self.stage_state.ruler_clicked_total = count
        if (count == 1) and self.stage_state.marker_before('ang_siz4'):
            self.stage_state.marker = 'ang_siz4'  # auto-advance guideline if it's the first ruler click
    
    #@print_function_name
    def _measurement_count_update(self, change):
        count = change["new"]
        self.stage_state.n_meas = count
        if (count == 1) and self.stage_state.marker_before('ang_siz5'):
            self.stage_state.marker = 'ang_siz5'  # auto-advance guideline if it's the first measurement made

    def _show_ruler_changed(self, show):
        self.distance_tool.show_ruler = show
    
    #@print_function_name
    def _on_galaxy_changed(self, galaxy):
        self.distance_tool.galaxy_selected = bool(galaxy)
    
    def _update_brightness(self, val):
         table = self.current_table
         data_label = table._glue_data.label
         # currently only example galaxy has brightness value defined
         if data_label != EXAMPLE_GALAXY_MEASUREMENTS:
             return
         index = table.index
         self.update_data_value(EXAMPLE_GALAXY_MEASUREMENTS, BRIGHTNESS_COMPONENT, val, index)
    
    #@print_function_name
    def _make_measurement(self):
        # We don't want a student's data to change once they've reached stage 4
        if self.story_state.max_stage_index >= 4:
            return

        galaxy = self.stage_state.galaxy
        table = self.current_table
        data_label = table._glue_data.label
        index = self.get_data_indices(data_label, NAME_COMPONENT,
                                      lambda x: x == galaxy["name"],
                                      single=True)
        
        angular_size = self.distance_tool.angular_size

        index = table.index
        if index is None:
            return

        self.stage_state.bad_angsize = self.distance_tool.bad_measurement

        if self.stage_state.bad_angsize:
            change = {'new':galaxy, 'old': None, 'owner': table}
            self.distance_table_selected_change(change)
            self.stage_state.bad_angsize_index = index
            return

        data = table.glue_data
        curr_value = data[ANGULAR_SIZE_COMPONENT][index]

        if (curr_value is None) and (data_label == STUDENT_MEASUREMENTS_LABEL):
            self.stage_state.angsizes_total = self.stage_state.angsizes_total + 1

        self.stage_state.meas_theta = round(angular_size.to(u.arcsec).value)

        self.update_data_value(data_label, ANGULAR_SIZE_COMPONENT,
                            self.stage_state.meas_theta, index)
        if data_label == EXAMPLE_GALAXY_MEASUREMENTS:
            if (index==0) and self.stage_state.marker_reached('dot_seq1'):
                return
            
            if (index == 1) and self.stage_state.marker == 'dot_seq5b':
                self.stage_state.exgal_second_measured = True
                self.stage_state.marker_forward = 1

            colors = ["#FB5607", "#FB5607"]
            labels = ['First', 'Second']
            v1 = self.get_viewer('dotplot_viewer_ang')
            
            v3 = self.get_viewer('dotplot_viewer_dist')
            v4 = self.get_viewer('dotplot_viewer_dist_2')
                
            
            if self.stage_state.marker_after('est_dis4'):
                self.add_student_distance()
            
            for val in ['x_min','x_max','layers']:
                if index == 0:
                    v1_plot = lambda *args: self.plot_measurement('dotplot_viewer_ang', index, color = colors[index], label = labels[index])
                    v3_plot = lambda *args: self.plot_measurement('dotplot_viewer_dist', index, distance = True, color = colors[index], label = labels[index])
                    add_callback(v1.state, val , v1_plot)
                    add_callback(v3.state, val , v3_plot)
                    def both_plots(change):
                        v1_plot()
                        v3_plot()
                    self.hub.subscribe(self, NumericalDataChangedMessage,
                           filter=lambda msg: msg.data.label == EXAMPLE_GALAXY_MEASUREMENTS,
                           handler=both_plots)
                    v1.toolbar.tools['bqplot:home'].activate()
                    v3.toolbar.tools['bqplot:home'].activate()
                    
                if index == 1:
                    v4_plot = lambda *args: self.plot_measurement('dotplot_viewer_dist_2', index, distance = True, color = colors[index], label = labels[index])
                    add_callback(v4.state, val , v4_plot)
                    self.hub.subscribe(self, NumericalDataChangedMessage,
                           filter=lambda msg: msg.data.label == EXAMPLE_GALAXY_MEASUREMENTS,
                           handler=v4_plot)
                    v4.toolbar.tools['bqplot:home'].activate()

        if data_label == STUDENT_MEASUREMENTS_LABEL:
            self.story_state.update_student_data()
        with ignore_callback(self.stage_state, 'make_measurement'):
            self.stage_state.make_measurement = False

    def select_bad_measurement_row(self):
        if self.stage_state.bad_angsize:
            index = self.stage_state.bad_angsize_index
            galaxy = self.distance_table.items[index]
            self.distance_table.selected = [galaxy]        

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
        self._request_session.post(f"{API_URL}/{HUBBLE_ROUTE_PATH}/mark-tileload-bad",
                      json=data)

        index = self.distance_table.index
        if index is None:
            return
        item = self.distance_table.selected[0]
        galaxy_name = item["name"]
        self.remove_measurement(galaxy_name)
        self.distance_tool.flagged = False
    
    #@print_function_name
    def add_student_distance(self, _args=None):
        table = self.current_table
        index = table.index
        if index is None:
            return
        distance = distance_from_angular_size(self.stage_state.meas_theta)

        self.update_data_value(table._glue_data.label, DISTANCE_COMPONENT, distance,
                            index)

        self.story_state.update_student_data()
        self.get_distance_count()
    
    #@print_function_name
    def update_distances(self, table, tool=None):
        data = table.glue_data
        for item in table.items:
            index = table.indices_from_items([item])[0]
            if index is not None and data[DISTANCE_COMPONENT][index] is None:
                theta = data[ANGULAR_SIZE_COMPONENT][index]
                if (theta is None) or (theta == 0):
                    continue

                distance = distance_from_angular_size(theta)
                self.update_data_value(table._glue_data.label, DISTANCE_COMPONENT,
                                    distance, index)
        self.story_state.update_student_data()
        if tool is not None:
            table.update_tool(tool)
        self.get_distance_count()
    
    def fill_table(self, table, tool=None):
        self.update_data_value(table._glue_data.label, ANGULAR_SIZE_COMPONENT, 35, 0)
        self.update_data_value(table._glue_data.label, DISTANCE_COMPONENT, distance_from_angular_size(35), 0)

    #@print_function_name
    def vue_update_distances(self, _args):
        self.update_distances(self.distance_table)
        self.update_distances(self.example_galaxy_distance_table)

    def vue_fill_table(self, _args):
        self.fill_table(self.example_galaxy_distance_table)
    
    #@print_function_name
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
        viewers = ['dotplot_viewer_ang','dotplot_viewer_dist','dotplot_viewer_dist_2']
        viewer_type = ["histogram","histogram","histogram"]
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

    def _on_stage_complete(self, complete):
        return
        if complete:
            self.story_state.stage_index = 4

            # We need to do this so that the stage will be moved forward every
            # time the button is clicked, not just the first
            self.stage_state.stage_3_complete = False
    
    def vue_stage_three_complete(self, *args):
        # print('vue_stage_three_complete')
        self.story_state.stage_index = 4
        self.stage_state.stage_3_complete = False
