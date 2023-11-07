from fsspec import Callback
# from hubbleds.stages.stage_1 import print_log
import ipyvuetify as v
from traitlets import Int, Bool, Unicode, Instance, Dict
from cosmicds.utils import load_template
from ipywidgets import widget_serialization, DOMWidget

from cosmicds.utils import extend_tool

from bqplot import Label

from glue_jupyter.link import link
from echo import add_callback, ignore_callback, CallbackProperty
from bqplot import Label
from bqplot.marks import Lines, Scatter
from cosmicds.utils import vertical_line_mark



from hubbleds.data_management import VELOCITY_COMPONENT
from glue.core.message import NumericalDataChangedMessage, SubsetUpdateMessage
from glue.core import HubListener
from glue.core.subset import RangeSubsetState

from itertools import cycle
from functools import partial
# theme_colors()
from IPython.display import Javascript, display


import inspect
from IPython.display import Javascript, display

def print_log(*args, color = None, **kwargs):
    if False:
        ##print(*args, **kwargs)
        s = 'spe tut: ' + ' '.join([str(a) for a in args])
        color = color or 'green'
        display(Javascript(f'console.log("%c{s}","color:{color}");'))

    return
def print_function_name(func):
    def wrapper(*args, **kwargs):
        calling_function_name = inspect.stack()[1][3]
        print_log(f"Calling  {func.__name__} from {calling_function_name}")
        return func(*args, **kwargs)
    return wrapper

class SpectrumMeasurementTutorialSequence(v.VuetifyTemplate, HubListener):
    template = load_template("./spectrum_measurement_tutorial.vue", __file__, traitlet=True).tag(sync=True)
    step = Int(0).tag(sync=True)
    length = Int(19).tag(sync=True)
    dialog = Bool(False).tag(sync=True)
    opened = Bool(False).tag(sync=True)
    been_opened = Bool(False).tag(sync=True)
    currentTitle = Unicode("").tag(sync=True)
    maxStepCompleted = Int(0).tag(sync=True)
    spectrum_viewer_widget = Instance(DOMWidget).tag(sync=True, **widget_serialization)
    dotplot_viewer_widget = Instance(DOMWidget).tag(sync=True, **widget_serialization)
    dotplot_viewer_2_widget = Instance(DOMWidget).tag(sync=True, **widget_serialization)
    example_galaxy_table = Instance(DOMWidget).tag(sync=True, **widget_serialization)
    show_specviewer = Bool(False).tag(sync=True)
    allow_specview_mouse_interaction = Bool(False).tag(sync=True)
    show_first_measurement = Bool(False).tag(sync=True)
    show_second_measurement = Bool(False).tag(sync=True)
    zoom_tool_activated = Bool(False).tag(sync=True)
    show_selector_lines = Bool(True).tag(sync=True)
    tutorial_state = Dict({}).tag(sync=True)

    _titles = [
        "Measurement Tutorial",
    ]
    _default_title = "Specrum Measurement Tutorial"

    def __init__(self, viewer_layouts, tutorial_state, marker, indices, *args, **kwargs):
        
        self.currentTitle = self._default_title
        self.tutorial_state = tutorial_state
        # self.saving_state  = tutorial_state
        
        self.indices = indices
        # loop through all the keys in the tutorial state and set the values
        # so that self.variable stores the correct value and make sure the 
        # value in the tutorial state is updated when the value changes
        for key in self.tutorial_state.keys():
            if hasattr(self, key):
                setattr(self, key, self.tutorial_state[key])
                self.observe(self._on_tutorial_state_change, [key])
            
        self.marker_index = {v:k for k, v in indices.items()}
        self.tutorial_start_marker = 'che_mea1'
        self.init_marker = marker
        
        self.disable_next_button = [1, 9, 17]
        
        self.dotplot_viewer_widget = viewer_layouts[0]
        self.dotplot_viewer_2_widget = viewer_layouts[1]
        self.spectrum_viewer_widget = viewer_layouts[2]
        self.example_galaxy_table = viewer_layouts[3]
        
        super().__init__(*args, **kwargs)
        
        self.observe(self._on_dialog_open, 'dialog')
        
        self.dotplot_viewer = self.dotplot_viewer_widget.viewer
        self.dotplot_viewer_2 = self.dotplot_viewer_2_widget.viewer
        self.spectrum_viewer = self.spectrum_viewer_widget.viewer
        self.viewers = [self.dotplot_viewer, self.dotplot_viewer_2, self.spectrum_viewer]
        
        
        self.glue_data = self.dotplot_viewer.state.layers[0].layer

        # cycle will cycle infitely through the list of colors
        self.color_cycle = cycle(['#9e17bf','#d98d0b','#07e856','#e80707','#e807e8','#07e8e8'])
        
        
        
        self.element = self.spectrum_viewer.element 
        H_ALPHA_REST_LAMBDA = 6565 
        MG_REST_LAMBDA = 5172
        self.rest = MG_REST_LAMBDA if self.element == 'Mg-I' else H_ALPHA_REST_LAMBDA
        
        self.which_measurement = {
            'first': {
            'label': 'first measurement',
            'viewer': self.dotplot_viewer
            },
            'second': {
            'label': 'second measurement',
            'viewer': self.dotplot_viewer_2
            }
        }
        
        
        self.first_meas_plotted = False
        self.second_meas_plotted = False
        
        self.first_meas_line = self.add_point(self.dotplot_viewer, x=0, color='#FB5607', label='first_meas_line')
        self.second_meas_line = self.add_point(self.dotplot_viewer_2, x=0, color='#FB5607', label='second_meas_line')
        self.first_meas_line.visible = True
        self.second_meas_line.visible = True
        
        self.spec_view_first = self.vertical_line_mark(self.spectrum_viewer, x=0, color=self.first_meas_line.colors[0], label='spec_view_first')
        self.spec_view_second = self.vertical_line_mark(self.spectrum_viewer, x=0, color=self.second_meas_line.colors[0] , label='spec_view_second')
        self.spec_view_first_label = Label(
                        text=[""],
                        x=[self.spec_view_first.x[0]],
                        y=[self.spec_view_first.y[1]],
                        x_offset=10,
                        y_offset=10,
                        scales=self.spec_view_first.scales,
                        colors=self.spec_view_first.colors,
                        visible=True
                    )
        
        self.spec_view_second_label = Label(
                        text=["#2"],
                        x=[self.spec_view_second.x[0]],
                        y=[self.spec_view_second.y[1]],
                        x_offset=10,
                        y_offset=10,
                        scales=self.spec_view_second.scales,
                        colors=self.spec_view_second.colors,
                        visible=True
                    )

        
            

        # do something whenever the axis limits change
        for val in ['x_min','x_max','layers']:
            add_callback(self.dotplot_viewer.state, val ,self._on_dotplot_change)
            add_callback(self.dotplot_viewer_2.state, val ,self._on_dotplot_change)

        # for viewer in [self.dotplot_viewer, self.dotplot_viewer_2]:
        #     for subset in [self.selected_tower, self.selected_tower_2]:
        #         if subset is not None:
        #             layer = viewer.layer_artist_for_data(subset)
        #             if layer is not None:
        #                 layer.state.skew = 0.3
        #                 layer.state.rotation = 90 # This is currently being ignored - not sure why
        
        # clear_subsets currently does nothing
        extend_tool(self.dotplot_viewer, 'bqplot:home', partial(self.clear_subsets,self.dotplot_viewer))
        extend_tool(self.dotplot_viewer_2, 'bqplot:home', partial(self.clear_subsets,self.dotplot_viewer_2))
        
        def func(*args, **kwargs):
            if self.spectrum_viewer.state.y_max is not None:
                self.spectrum_viewer.state.reset_limits()
        extend_tool(self.dotplot_viewer,'bqplot:home', func, activate_before_tool=False)
        
        # run through steps to open run necessary setup calls in the vue file
    
    @property
    def table_data(self):
        return self.example_galaxy_table._glue_data
    
    def _on_tutorial_state_change(self, change):
        self.print_log(f'name: {change["name"]}, old: {change["old"]}, new: {change["new"]}')
        temp_state = self.tutorial_state.copy()
        temp_state.update({change['name']:change['new']})
        # self.tutorial_state.update({change['name']:change['new']})
        self.tutorial_state =  temp_state
    
    def _on_dialog_open(self, change):
        if change['new'] & (not self.been_opened):
            self.been_opened = True
            self.spectrum_viewer.toolbar.set_tool_enabled("bqplot:home",True)
            
            
            
            self.example_galaxy_table._glue_data.hub.subscribe(
                self, NumericalDataChangedMessage,
                filter = lambda msg: msg.data.label == self.table_data.label,
                handler=self._on_data_change)
            
            self.example_galaxy_table._glue_data.hub.subscribe(
                self, SubsetUpdateMessage,
                # filter = lambda msg: msg.data.label == self.table_data.label,
                handler=self._on_data_change)
            
            self.add_selector_lines()
            self.vue_tracking_lines_off()
            self.dotplot_viewer.toolbar.set_tool_enabled("hubble:wavezoom",self.zoom_tool_activated)
            
            self.spectrum_viewer.add_event_callback(self._update_selector_tool_sv, events=['mousemove'])
            self.dotplot_viewer.add_event_callback(self._update_selector_tool_dp, events=['mousemove'])
            self.dotplot_viewer_2.add_event_callback(self._update_selector_tool_dp2, events=['mousemove'])
            
            self.observe(lambda msg: self.plot_measurements(self.table_data), ['show_first_measurement', 'show_second_measurement'])
            self.observe(self.toggle_specview_mouse_interaction, 'allow_specview_mouse_interaction')
            # self.observe(self._on_step_change, ['step'])
            
            self.spectrum_viewer.add_event_callback(
                callback = lambda event: self._on_viewer_focus(self.spectrum_viewer, event), 
                events=['moustenter', 'mouseleave'])
            self.dotplot_viewer.add_event_callback(
                callback = lambda event: self._on_viewer_focus(self.dotplot_viewer, event),
                events=['moustenter', 'mouseleave'])
            self.dotplot_viewer_2.add_event_callback(
                callback = lambda event: self._on_viewer_focus(self.dotplot_viewer_2, event),
                events=['moustenter', 'mouseleave'])
            
            
            self.dotplot_viewer.add_event_callback(
                callback = lambda event: self._activate_gray_markers(self.dotplot_viewer, event),
                events=['click'])
            self.dotplot_viewer_2.add_event_callback(
                callback = lambda event: self._activate_gray_markers(self.dotplot_viewer_2, event),
                events=['click'])
            self.spectrum_viewer.add_event_callback(
                callback = lambda event: self._activate_gray_markers(self.spectrum_viewer, event),
                events=['click'])
            
            if len(self.example_galaxy_table.selected) == 0:
                if self.marker_before(change['marker'], 'dot_seq13'):
                    index = 0
                galaxy = {c.label:self.table_data[c][index] for c in self.table_data.components}
                self.example_galaxy_table.selected = [galaxy]
                self.example_galaxy_table.selected = []
            
            self._on_marker_change(self.tutorial_start_marker, change['marker'])
            
        elif change['new'] & self.been_opened:
            self.vue_on_reopen()
        else:
            pass
    
    def _on_step_change(self, change):
        # stubb
        pass
    
    
    def at_marker(self, new, check):
        return new == check #self.indices[new] == self.indices[check]
    
    def marker_after(self, marker, check):
        return self.indices[marker] >= self.indices[check]
    
    def marker_before(self, marker, check):
        return self.indices[marker] <= self.indices[check]
    
    def _on_marker_change(self, old, new):
        if self.marker_before(old, self.tutorial_start_marker):
            old = self.tutorial_start_marker
        if (self.indices[new] - self.indices[old])  > 1:
            self._on_marker_change(old, self.marker_index[self.indices[new]-1])
            
        self.print_log(f"marker change: {old} -> {new}")
        
        advancing = (self.indices[new] - self.indices[old]) == 1
        
        if not self.been_opened:
            self._on_dialog_open({'new': True})
        
        if self.at_marker(new, 'int_dot1'):
            link((self.spectrum_viewer.state, 'x_min'), (self.dotplot_viewer.state, 'x_min'), self.w2v, self.v2w )
            link((self.spectrum_viewer.state, 'x_max'), (self.dotplot_viewer.state, 'x_max'), self.w2v, self.v2w)
            
            extend_tool(self.dotplot_viewer, "hubble:wavezoom", 
                        activate_cb=self.spectrum_viewer.state.reset_y_limits_for_view, 
                        activate_before_tool=False)
            self.show_first_measurement = True
        
        if self.at_marker(new, 'dot_seq1'):
            try:
                self.spectrum_viewer.remove_event_callback(self.spectrum_viewer._on_click) # turns on measuring interaction
            except:
                print_log('on_click not found')
            
        if self.at_marker(new, 'dot_seq2'):
            self.dotplot_viewer.toolbar.set_tool_enabled("hubble:wavezoom", True)
            
        if self.at_marker(new, 'dot_seq5'):
            self.show_selector_lines = True
            for viewer in [self.dotplot_viewer, self.dotplot_viewer_2]:
                viewer.show_line(True,True)
                viewer.show_previous_line() # just adds the line, clicking makes it visible
                viewer.add_event_callback(viewer._on_click, events = ['click'])
            self.spectrum_viewer.line.visible = True
            self.spectrum_viewer.line_label.visible = True

            self.spectrum_viewer.toolbar.active_tool = None # make sure it is inactive before adding callback
            self.spectrum_viewer.add_event_callback(self.spectrum_viewer._on_click, events=['click'])
            # self.spectrum_viewer.add_event_callback(self.spectrum_viewer._on_mouse_moved, events = ['mousemove'])
            
            def activateMeasuringTool(viewer):
                viewer.show_line(True, True)

            def activate_selector(viewer):
                viewer.show_previous_line(False, False)
                
            
            def removeMeasuringTool(viewer):
                viewer.show_previous_line(False, False)
                viewer.show_line(False, False)
            
            def on_zoom_active(viewer, *args, **kwargs):
                removeMeasuringTool(viewer)
                
            
            def on_zoom_deactive(viewer, *args, **kwargs):
                activateMeasuringTool(viewer)
                activate_selector(viewer)
                
            extend_tool(self.dotplot_viewer, "hubble:wavezoom", 
                        activate_cb=partial(on_zoom_active, self.dotplot_viewer), 
                        deactivate_cb=partial(on_zoom_deactive, self.dotplot_viewer))
            extend_tool(self.dotplot_viewer_2, "hubble:wavezoom", 
                        activate_cb=partial(on_zoom_active, self.dotplot_viewer_2), 
                        deactivate_cb=partial(on_zoom_deactive, self.dotplot_viewer_2))
        
        if self.at_marker(new, 'dot_seq13'):
            self.show_second_measurement = True
            self.example_galaxy_table.filter_by(None)#lambda item: item['measurement_number'] == 'second')
    
        if self.at_marker(new, 'dot_seq14'):
            self.dotplot_viewer_2.toolbar.set_tool_enabled("hubble:wavezoom", True)
            link((self.spectrum_viewer.state, 'x_min'), (self.dotplot_viewer_2.state, 'x_min'), self.w2v, self.v2w)
            link((self.spectrum_viewer.state, 'x_max'), (self.dotplot_viewer_2.state, 'x_max'), self.w2v, self.v2w)
            extend_tool(self.dotplot_viewer_2, "hubble:wavezoom", 
                        activate_cb=self.spectrum_viewer.state.reset_y_limits_for_view, 
                        activate_before_tool=False)
            self.show_second_measurement = True
            self.example_galaxy_table.filter_by(None)  #lambda item: item['measurement_number'] == 'second')
        
        if self.marker_after(new, 'rem_gal1'):
            self.show_selector_lines = False
            self.second_meas_plotted = False
            self.first_meas_plotted = False
            self.show_second_measurement = False
            self.show_first_measurement = False


    def _on_viewer_focus(self, viewer, event=None):
        if event is None:
            return
        if event['event'] == 'mouseenter':
            # viewer.line.visible = True
            viewer.previous_line.visible = True
            viewer.previous_line_label.visible = True
        elif event['event'] == 'mouseleave':
            # viewer.line.visible = False
            viewer.previous_line.visible = False
            viewer.previous_line_label.visible = False
    
    def _activate_gray_markers(self, viewer, event=None):
        if event is None:
            return
        if self.show_selector_lines:
            if viewer is self.spectrum_viewer:
                w = event['domain']['x']
                v = self.w2v(w)
            else:
                v = event['domain']['x']
                w = self.v2w(v)
        
            self.dotplot_viewer._on_click(event={'domain': {'x': v}})
            self.dotplot_viewer_2._on_click(event={'domain': {'x': v}})
            self.spectrum_viewer._on_click(event={'domain': {'x': w}})


    
    def _on_data_change(self, message):
        # things that need to be redrawn when dotplots are changed
        self.plot_measurements(self.table_data)
        self.add_selector_lines()
    
        
    def create_range_subsets(self, viewer, data, label=None):
        subset_init = {
            'lo': viewer.state.x_min,
            'hi': viewer.state.x_max,
            'att': viewer.state.x_att
        }
        self.range_subset = RangeSubsetState(**subset_init)
        
        new_subset_init = {
            'label': label,
            'subset_state': self.range_subset,
            'color': next(self.color_cycle,'#000000')
        }
        return data.new_subset(**new_subset_init)
    
    def _on_dotplot_change(self, change = None):
        if change is not None:
            self.add_selector_lines()
        self.plot_measurements(self.table_data) # plots the measurements again

        
    
    def clear_subsets(self,viewer):
        # this should clear or hide the 
        # self.selected_tower and self.selected_tower_2
        # subsets
        pass

    def add_selector_lines(self):
        self.dotplot_viewer.add_lines_to_figure()
        self.dotplot_viewer_2.add_lines_to_figure()
        
    def get_y_bounds(self, viewer, frac = 0.8):
        """ y limits for middle frac of plot (not used)"""
        y_min, y_max = viewer.state.y_min, viewer.state.y_max
        frac = (1 - frac) / 2 if frac > 0 else 0
        return y_min + frac * (y_max - y_min), y_max - frac * (y_max - y_min)
        
    def v2w(self, v):
        # convert v from velocity (km/s) to wavelength (Angstroms)
        return self.rest * (1 + v / (3 * (10 ** 5)))
    
    def w2v(self, l):
        # convert x from wavelength (Angstroms) to velocity (km/s)
        return (3 * (10 ** 5) * (l / self.rest - 1))

    
    @staticmethod
    def get_layer_by_name(viewer, name):
        return next((layer for layer in viewer.layers if name in layer.layer.label), None)
    
    @staticmethod
    def get_data_subset_by_name(data,  name):
        for subset in data.subsets:
            if subset.label == name:
                return subset
        return None
    
    @staticmethod    
    def search_sorted(arr, x):
        """ 
        returns the right most index of the array that is less than x
        """
        if len(arr) == 0:
            return 0
        if arr[-1] < x:
            return len(arr)
        if arr[0] > x:
            return 0
        for i in range(len(arr)):
            if arr[i] > x:
                return i
        return len(arr)
        
    @staticmethod
    def vertical_line_mark(viewer, x, color, label=None):
        scales = {'x': viewer.figure.scale_x, 'y': viewer.figure.scale_y}
        ymin, ymax = scales['y'].min, scales['y'].max
        return Lines(x=[x,x], y=[ymin, ymax], scales=scales, colors=[color], labels=[label])
    
    @staticmethod
    def add_point(viewer, x, color, label = None): 
        scales = {'x': viewer.figure.scale_x, 'y': viewer.figure.scale_y}
        size = viewer.layers[0].bars.default_size * 5
        return  Scatter(x=[x], y=[1], 
                         scales=scales, colors=[color], 
                         labels=[label], opacities=[1],
                         default_size=size,marker='circle',)
    
    def _update_selector_tool_dp(self, event=None):
        if not self.show_selector_lines:
            return
        if event is not None:
            new_x = event['domain']['x']
            self.dotplot_viewer_2.line.x = [new_x, new_x]
            self.dotplot_viewer_2._update_x_locations()
            self.dotplot_viewer_2.line_label.text = [self.dotplot_viewer_2._label_text(new_x)]
            
            w = self.v2w(new_x)
            self.spectrum_viewer.line.x = [w, w]
            self.spectrum_viewer._update_x_locations()  
            self.spectrum_viewer.line_label.text = [self.spectrum_viewer._label_text(w)]
    
    def _update_selector_tool_dp2(self, event=None):
        if not self.show_selector_lines:
            return
        if event is not None:
            new_x = event['domain']['x']
            self.dotplot_viewer.line.x = [new_x, new_x]
            self.dotplot_viewer._update_x_locations()
            self.dotplot_viewer.line_label.text = [self.dotplot_viewer._label_text(new_x)]
            
            w = self.v2w(new_x)
            if w is None:
                return
            self.spectrum_viewer.line.x = [w,w]
            self.spectrum_viewer._update_x_locations()
            self.spectrum_viewer.line_label.text = [self.spectrum_viewer._label_text(w)]
            

    def _update_selector_tool_sv(self, event=None):
        if not self.show_selector_lines:
            return
        if event is not None:
            new_x = self.w2v(event['domain']['x'])
            self.dotplot_viewer.line.x = [new_x, new_x]
            self.dotplot_viewer._update_x_locations()
            self.dotplot_viewer.line_label.text = [self.dotplot_viewer._label_text(new_x)]
            
            self.dotplot_viewer.line_label.x = [new_x]
            self.dotplot_viewer_2._update_x_locations()
            self.dotplot_viewer_2.line_label.text = [self.dotplot_viewer_2._label_text(new_x)]

    @staticmethod
    def get_bin(bins, x):
        bin_width = bins[1] - bins[0]
        index = int((x - bins[0])/bin_width)
        return bins[0] + bin_width * (index + 1/2)
    
    def plot_measurements(self, data):
        """ data should be a glue data"""
        vel = data.to_dataframe()[VELOCITY_COMPONENT]
        
        if self.show_first_measurement and (vel[0] is not None):
            viewer = self.dotplot_viewer
            x = self.get_bin(viewer.state.bins, vel[0])
            self.first_meas_line.x = [x,x]
            self.first_meas_line.default_size = self.dotplot_viewer.layers[0].bars.default_size * 5
            self.first_meas_plotted = True
        else:
            self.first_meas_plotted = False
        
        if self.show_second_measurement and (vel[1] is not None):
            viewer = self.dotplot_viewer_2
            bins = viewer.state.bins
            x = self.get_bin(viewer.state.bins, vel[1])
            self.second_meas_line.x = [x,x]
            self.second_meas_line.default_size = self.dotplot_viewer_2.layers[0].bars.default_size * 5
            self.second_meas_plotted = True
        else:
            self.second_meas_plotted = False
        
        if self.first_meas_plotted and self.first_meas_line not in self.dotplot_viewer.figure.marks:
            self.dotplot_viewer.figure.marks = self.dotplot_viewer.figure.marks + [self.first_meas_line]
        
        if self.second_meas_plotted and self.second_meas_line not in self.dotplot_viewer_2.figure.marks:
            self.dotplot_viewer_2.figure.marks = self.dotplot_viewer_2.figure.marks + [self.second_meas_line]
        

        self.show_measurements_on_specviewer()
    
    def show_measurements_on_specviewer(self):
        
        viewer = self.spectrum_viewer
        
        new_marks = []
        d = 0.2 # fraction of the y range to use for the line
        ymin = viewer.state.y_min
        ymax = viewer.state.y_max
        
        if ymin is None or ymax is None:
            # spectrum viewer is not yet initialized
            return
        
        ymax = ymin + d * (ymax - ymin)
        vars = {
            'first': {
                'line': self.spec_view_first,
                'label': self.spec_view_first_label,
                'plotted': self.first_meas_plotted
            },
            'second': {
                'line': self.spec_view_second,
                'label': self.spec_view_second_label,
                'plotted': self.second_meas_plotted
                }
            }
        
        for k, v in vars.items():
            if v['plotted']:
                x0 = self.v2w(self.first_meas_line.x[0] if k == 'first' else self.second_meas_line.x[0])
                
                if v['line'].x[0] != x0:
                    v['line'].x = [x0, x0]
                    v['label'].x = [x0]
                    
                if any(v['line'].y != [ymin, ymax]):
                    v['line'].y = [ymin, ymax]
                    v['label'].y = [v['line'].y[1]]
                
                if v['line'] not in viewer.figure.marks:
                    new_marks = new_marks + [v['line']] + [v['label']]
            else:
                if v['line'] in viewer.figure.marks:
                    new_marks = new_marks + [v['line']] + [v['label']]
        
        
        if len(new_marks) > 0:
            self.spectrum_viewer.figure.marks = self.spectrum_viewer.figure.marks + new_marks
        
    
    def toggle_specview_mouse_interaction(self, change):
        """ callback function for self.allow_specview_mouse_interaction """
        if change['new']:
            # on mouse moved is the blue/grey tracking line
            self.spectrum_viewer.add_event_callback(self.spectrum_viewer._on_mouse_moved, events=['mousemove'])
            self.spectrum_viewer.add_event_callback(self.spectrum_viewer._on_click, events=['click'])
        else:
            self.spectrum_viewer.remove_event_callback(self.spectrum_viewer._on_mouse_moved)
            self.spectrum_viewer.remove_event_callback(self.spectrum_viewer._on_click) # turns on measuring interaction
    
    
    # vue callable functions
    

    def vue_set_x_axis_limits(self, data=None):
        if data is not None:
            self.dotplot_viewer.state.x_min = data['xmin']
            self.dotplot_viewer.state.x_max = data['xmax']
        self._on_dotplot_change()
     
    def vue_show_second_measurement_table(self, data=None):
        self.example_galaxy_table.filter_by(lambda item: item['measurement_number'] == 'second')
        
    def vue_tracking_lines_on(self, _data=None):
        self.show_selector_lines = True
        for viewer in self.viewers:
            viewer.line.visible = True
            viewer.line_label.visible = True  
            # the _on_click callback turns the previous line on
            viewer.add_event_callback(viewer._on_click, events=['click'])     

    def vue_tracking_lines_off(self, _data = None):
        self.show_selector_lines = False
        for viewer in self.viewers:
            viewer.line.visible = False
            viewer.line_label.visible = False
            viewer.previous_line.visible = False
            viewer.previous_line_label.visible = False
            # the _on_click callback turns the previous line on. do disable it
            try:
                viewer.remove_event_callback(viewer._on_click)
            except:
                pass
    
    def vue_on_close(self, data=None):
        # need to clean up the spectrum viewer before returning to the main page
        self.spectrum_viewer.state.reset_limits()
        marks_to_remove = [self.spec_view_first, 
               self.spec_view_second, 
               self.spec_view_first_label, 
               self.spec_view_second_label
               ]
        marks = [m for m in self.spectrum_viewer.figure.marks if m in marks_to_remove]
        for mark in marks:
            mark.visible = False
        # self.spectrum_viewer.figure.marks = marks
        self.spectrum_viewer.line.visible = True
        self.spectrum_viewer.line_label.visible = True
        try:
            self.spectrum_viewer.remove_event_callback(self._update_selector_tool_sv)
        except:
            print_log('could not remove _update_selector_tool_sv callback')
            pass


    def print_log(self, *args, **kwargs):
        if False:
            # combine all args into a single string
            s = ' '.join([str(a) for a in args])
            s = 'py: ' + s
            # print this to the javascript console
            # create needed imports
            display(Javascript(f'console.log("%c{s}","color:green");'))
        
    def vue_on_reopen(self):
        self.plot_measurements(self.table_data)
        self.spectrum_viewer.add_event_callback(self._update_selector_tool_sv, events=['mousemove'])
        

