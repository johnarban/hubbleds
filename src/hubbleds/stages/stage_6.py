from os.path import join
from pathlib import Path

from echo import CallbackProperty, add_callback, callback_property
from glue.core.message import NumericalDataChangedMessage
from glue.core import Subset
from traitlets import Bool, default

from cosmicds.components.layer_toggle import LayerToggle
from cosmicds.phases import CDSState
from cosmicds.registries import register_stage
from cosmicds.utils import (RepeatedTimer, extend_tool, load_template,
                            update_figure_css)
from hubbleds.utils import IMAGE_BASE_URL

from ..data.styles import load_style
from ..data_management import *
from ..stage import HubbleStage

from ..viewers.viewers import HubbleScatterView

class StageState(CDSState):
    
    marker = CallbackProperty("")
    indices = CallbackProperty({})

    hst_age = CallbackProperty(13)
    our_age = CallbackProperty(0)

    max_prodata_index = CallbackProperty(0)
    
    markers = [
        'pro_dat0',
        'pro_dat1',
        'pro_dat2',
        'pro_dat3',
        'pro_dat4',
        'pro_dat5',
        'pro_dat6',
        'pro_dat7',
        'pro_dat8',
        'pro_dat9',
        'sto_fin1',
        ]
        
    step_markers = CallbackProperty([
        'pro_dat0',
        'pro_dat6',
    ])
    
    _NONSERIALIZED_PROPERTIES = [
        'markers', 'indices', 'step_markers', 'image_location',
        'marker_forward', 'marker_backward',
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.marker_index = 0
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

    def move_marker_forward(self, marker_text, _value=None):
        index = min(self.markers.index(marker_text) + 1, len(self.markers) - 1)
        self.marker = self.markers[index]


@register_stage(story="hubbles_law", index=6, steps=["Edwin Hubble", "Hubble Telescope"])
class StageFive(HubbleStage):
    show_team_interface = Bool(False).tag(sync=True)
    _state_cls = StageState

    @default('stage_state')
    def _default_state(self):
        return StageState()
        
    @default('template')
    def _default_template(self):
        return load_template("stage_6.vue", __file__)

    @default('stage_icon')
    def _default_stage_icon(self):
        return "5"

    @default('title')
    def _default_title(self):
        return "Professional Data"

    @default('subtitle')
    def _default_subtitle(self):
        return "Comparing your data with professional data"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_team_interface = self.app_state.show_team_interface
        
        # self.stage_state.marker = self.stage_state.markers[0]
        
        add_callback(self.stage_state, 'marker', self._on_marker_update, echo_old=True)
        
        prodata_viewer = self.add_viewer(HubbleScatterView, "prodata_viewer",
                                         "Professional Data")
        prodata_viewer.toolbar.set_tool_enabled("hubble:linefit", False)
        prodata_viewer.figure.axes[1].label_offset = "5em"

        layer_toggle = LayerToggle(prodata_viewer, names={
            STUDENT_DATA_LABEL: "My Data",
            CLASS_DATA_LABEL: "Class Data",
            HUBBLE_1929_DATA_LABEL: "Hubble 1929 Data",
            HUBBLE_KEY_DATA_LABEL: "HST Key Project 2001 Data"
        })
        self.ignore_slider_layer = lambda layer_state: layer_state.layer.label == "student_slider_subset"
        layer_toggle.add_ignore_condition(self.ignore_slider_layer)
        self.add_component(layer_toggle, label="py-layer-toggle")    
        
        self.setup_prodata_viewer()
        
        self._update_viewer_style(dark=self.app_state.dark_mode)

        # Functions to call on data updates
        self.hub.subscribe(self, NumericalDataChangedMessage,
                           filter=lambda msg: msg.data.label == STUDENT_DATA_LABEL,
                           handler=self._on_student_data_update)
        self.hub.subscribe(self, NumericalDataChangedMessage,
                           filter=lambda msg: msg.data.label == CLASS_DATA_LABEL,
                           handler=self._on_class_data_update)

    def setup_prodata_viewer(self):
        # load the prodata_viewer
        prodata_viewer = self.get_viewer("prodata_viewer")
        
        # load the student, class, hubble, and hst data
        student_data = self.get_data(STUDENT_DATA_LABEL)
        class_data = self.get_data(CLASS_DATA_LABEL)
        hubble_data = self.get_data(HUBBLE_1929_DATA_LABEL)
        hst_data = self.get_data(HUBBLE_KEY_DATA_LABEL)

        # Set up links between various data sets

        for field in [DISTANCE_COMPONENT, VELOCITY_COMPONENT]:
            self.add_link(CLASS_DATA_LABEL, field, STUDENT_DATA_LABEL, field)
        self.add_link(HUBBLE_1929_DATA_LABEL, 'Distance (Mpc)', HUBBLE_KEY_DATA_LABEL,
                      'Distance (Mpc)')
        self.add_link(HUBBLE_1929_DATA_LABEL, 'Tweaked Velocity (km/s)', HUBBLE_KEY_DATA_LABEL,
                      'Velocity (km/s)')
        self.add_link(HUBBLE_KEY_DATA_LABEL, 'Distance (Mpc)', STUDENT_DATA_LABEL,
                      DISTANCE_COMPONENT)
        self.add_link(HUBBLE_KEY_DATA_LABEL, 'Velocity (km/s)', STUDENT_DATA_LABEL,
                      VELOCITY_COMPONENT)

        # Avoid picking up subsets of the different layers.
        prodata_viewer.ignore(lambda layer: layer.label not in [STUDENT_DATA_LABEL, CLASS_DATA_LABEL, HUBBLE_KEY_DATA_LABEL, HUBBLE_1929_DATA_LABEL] and isinstance(layer, Subset))

        # load data into the viewer and style
        prodata_viewer.add_data(class_data)
        class_layer = prodata_viewer.layer_artist_for_data(class_data)
        class_layer.state.zorder = 1
        class_layer.state.color = "#3A86FF"
        class_layer.state.alpha = 1
        class_layer.state.size = 4

        prodata_viewer.state.x_att = class_data.id[DISTANCE_COMPONENT]
        prodata_viewer.state.y_att = class_data.id[VELOCITY_COMPONENT]

        prodata_viewer.add_data(student_data)
        student_layer = prodata_viewer.layer_artist_for_data(student_data)
        student_layer.state.color = '#FF7043'
        student_layer.state.zorder = 5
        student_layer.state.size = 8                    
        student_layer.state.alpha = 1
        student_layer.state.visible = self.stage_state.marker_reached('pro_dat0')
 
        # load hubble 1929 data
        prodata_viewer.add_data(hubble_data)
        hubble_layer = prodata_viewer.layer_artist_for_data(hubble_data)
        hubble_layer.state.color = '#D500F9'
        hubble_layer.state.visible = self.stage_state.marker_reached('pro_dat1')
        
        # load hubble key data
        prodata_viewer.add_data(hst_data)
        hst_layer = prodata_viewer.layer_artist_for_data(hst_data)
        hst_layer.state.color = '#AEEA00'
        hst_layer.state.visible = self.stage_state.marker_reached('pro_dat5')
        
        prodata_viewer.state.reset_limits()

        layer_toggle = self.get_component("py-layer-toggle")
        layer_toggle.set_layer_order([student_layer, class_layer, hubble_layer, hst_layer])
    
    def _update_viewer_style(self, dark):
        viewers = ['prodata_viewer']

        viewer_type = ["scatter"]

        theme_name = "dark" if dark else "light"
        for viewer, vtype in zip(viewers, viewer_type):
            viewer = self.get_viewer(viewer)
            style = load_style(f"default_{vtype}_{theme_name}")
            update_figure_css(viewer, style_dict=style)

    def _on_dark_mode_change(self, dark):
        super()._on_dark_mode_change(dark)
        self._update_viewer_style(dark)
    
    def reset_viewer_limits(self):
        prodata_viewer = self.get_viewer("prodata_viewer")
        prodata_viewer.state.reset_limits()
    
    def _on_class_data_update(self, *args):
        self.reset_viewer_limits()
    
    def _on_student_data_update(self, *args):
        self.reset_viewer_limits()
    
    def _on_marker_update(self, old, new):
        
        markers = self.stage_state.markers
        advancing = markers.index(new) > markers.index(old)
        
        if advancing:
            prodata_viewer = self.get_viewer("prodata_viewer")
        
            if  new == "pro_dat1": # show hubble 1929 data. enable line fit tool
                hubble_layer = prodata_viewer.layer_artist_for_data(self.get_data(HUBBLE_1929_DATA_LABEL))
                hubble_layer.state.visible = True
                prodata_viewer.toolbar.set_tool_enabled("hubble:linefit", True)
                prodata_viewer.toolbar.tools["hubble:linefit"].show_labels = False
            
            elif new == "pro_dat2":
                # show best fits
                if not prodata_viewer.toolbar.tools["hubble:linefit"].active: # if off
                    prodata_viewer.toolbar.tools["hubble:linefit"].activate() # toggle on
            # pro_dat3 is skipped
            # elif new == "pro_dat3":
            #     if prodata_viewer.toolbar.tools["hubble:linefit"].active:  # if on
            #         prodata_viewer.toolbar.tools["hubble:linefit"].activate() # toggle off
            elif new == 'pro_dat5':
                # deactivates the tool. activate() is a toggle
                if prodata_viewer.toolbar.tools["hubble:linefit"].active: # if on
                    prodata_viewer.toolbar.tools["hubble:linefit"].activate() # toggle off
                hst_layer = prodata_viewer.layer_artist_for_data(self.get_data(HUBBLE_KEY_DATA_LABEL))
                hst_layer.state.visible = True
            
            elif new == 'pro_dat6':
                # turn off the line fit tool
                prodata_viewer.toolbar.tools["hubble:linefit"].show_labels = False
                if not prodata_viewer.toolbar.tools["hubble:linefit"].active:
                    prodata_viewer.toolbar.tools["hubble:linefit"].activate()
            
            elif new == 'pro_dat8':
                # show all the ages
                prodata_viewer.toolbar.tools["hubble:linefit"].show_labels = True
            
            
     