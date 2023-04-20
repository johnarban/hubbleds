from functools import partial
from os.path import join
from pathlib import Path

from numpy import asarray, where
from cosmicds.components.layer_toggle import LayerToggle
from cosmicds.components.table import Table
from cosmicds.phases import CDSState
from cosmicds.registries import register_stage
from cosmicds.utils import extend_tool, load_template, update_figure_css
from echo import CallbackProperty, add_callback, remove_callback, DictCallbackProperty
from glue.core.message import NumericalDataChangedMessage
from glue.core.data import Data
from hubbleds.utils import IMAGE_BASE_URL, AGE_CONSTANT
from traitlets import default, Bool
from ..data.styles import load_style

from ..components import HubbleExpUniverseSlideshow

from ..data_management import *
from ..stage import HubbleStage
from ..viewers import HubbleScatterView
from ..viewers.viewers import HubbleFitLayerView


class StageState(CDSState):
    trend_response = CallbackProperty(False)
    relvel_response = CallbackProperty(False)
    race_response = CallbackProperty(False)
    hubble_dialog_opened = CallbackProperty(False)
    class_layer_toggled = CallbackProperty(0)
    trend_line_drawn = CallbackProperty(False)
    best_fit_clicked = CallbackProperty(False)
    stage_4_complete = CallbackProperty(False)

    marker = CallbackProperty("")
    indices = CallbackProperty({})
    advance_marker = CallbackProperty(True)

    image_location = CallbackProperty(f"{IMAGE_BASE_URL}/stage_three")

    hypgal_distance = CallbackProperty(0)
    hypgal_velocity = CallbackProperty(0)
    age_const = CallbackProperty(float(AGE_CONSTANT))


    #TrendsData ver
    define_trend = CallbackProperty(False)
    
    age_calc_state = DictCallbackProperty({
        'short_one': '',
        'short_two': '',
        'short_other': ''
    })
    
    markers = CallbackProperty([
        'exp_dat1',
        'tre_dat1',
        'tre_dat2',
        'tre_dat3',
        'rel_vel1',
        'hub_exp1',
        'tre_lin1',
        'tre_lin2',
        'bes_fit1',
        'age_uni1',
        'hyp_gal1',
        'age_rac1',
        'age_uni2',
        'age_uni3',
        'age_uni4',
        'you_age1',
        'sho_est1',
        'sho_est2', # last marker now
    ])

    step_markers = CallbackProperty([
        'exp_dat1',
    ])

    table_highlights = CallbackProperty([
        'exp_dat1',
    ])

    my_galaxies_plot_highlights = CallbackProperty([
        'tre_dat1',
        'tre_dat2',
        'tre_dat3',
        'rel_vel1',
        'hub_exp1',
        'tre_lin1',
        'tre_lin2',
        'bes_fit1',
        'age_uni1',
        'hyp_gal1',
        'age_rac1',
        'age_uni2',
        'age_uni3',
        'you_age1',
        'sho_est1',
    ])

    _NONSERIALIZED_PROPERTIES = [
        'markers', 'indices', 'step_markers',
        'table_highlights', 'image_location',
        'my_galaxies_plot_highlights', 'all_galaxies_plot_highlights',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.marker_index = 0
        self.marker = self.markers[0]
        self.indices = {marker: idx for idx, marker in enumerate(self.markers)}

    def marker_before(self, marker):
        return self.indices[self.marker] < self.indices[marker]

    def marker_after(self, marker):
        return self.indices[self.marker] > self.indices[marker]
    
    def marker_reached(self, marker):
        return self.indices[self.marker] >= self.indices[marker]

    def move_marker_forward(self, marker_text, _value=None):
        index = min(self.markers.index(marker_text) + 1, len(self.markers) - 1)
        self.marker = self.markers[index]

@register_stage(story="hubbles_law", index=4, steps=["MY DATA"])
class StageThree(HubbleStage):
    show_team_interface = Bool(False).tag(sync=True)

    _state_cls = StageState

    @default('stage_state')
    def _default_state(self):
        return StageState()

    @default('template')
    def _default_template(self):
        return load_template("stage_4.vue", __file__)

    @default('stage_icon')
    def _default_stage_icon(self):
        return "3"

    @default('title')
    def _default_title(self):
        return "Explore Data"

    @default('subtitle')
    def _default_subtitle(self):
        return "Perhaps a small blurb about this stage"

    viewer_ids_for_data = {
        STUDENT_DATA_LABEL: ["layer_viewer"],
        CLASS_DATA_LABEL: ["layer_viewer"],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        add_callback(self.stage_state, 'stage_4_complete',
                     self._on_stage_4_complete)

        self.show_team_interface = self.app_state.show_team_interface

        student_data = self.get_data(STUDENT_DATA_LABEL)
        class_meas_data = self.get_data(CLASS_DATA_LABEL)

        fit_table = Table(self.session,
                          data=student_data,
                          glue_components=[NAME_COMPONENT,
                                           VELOCITY_COMPONENT,
                                           DISTANCE_COMPONENT],
                          key_component=NAME_COMPONENT,
                          names=['Galaxy Name',
                                 'Velocity (km/s)',
                                 'Distance (Mpc)'],
                          title='My Galaxies',
                          subset_label="fit_table_selected"
                          )
        self.add_widget(fit_table, label="fit_table")

        # Create viewers
        layer_viewer = self.add_viewer(HubbleFitLayerView, "layer_viewer", "Our Data")
        
        hubble_race_viewer = self.add_viewer(HubbleScatterView,
                                                "hubble_race_viewer",
                                                 "Race")

        layer_toggle = LayerToggle(layer_viewer, names={
            STUDENT_DATA_LABEL: "My Data",
            CLASS_DATA_LABEL: "Class Data",
            fit_table.subset_label: "Table selection",
            BEST_FIT_SUBSET_LABEL: "Best Fit Galaxy"
        })
        self.ignore_class_layer = lambda layer_state: layer_state.layer.label == CLASS_DATA_LABEL
        layer_toggle.add_ignore_condition(self.ignore_class_layer)
        layer_toggle.add_ignore_condition(lambda layer_state: layer_state.layer.label in [fit_table.subset_label, BEST_FIT_SUBSET_LABEL])
        self.add_component(layer_toggle, label="py-layer-toggle")     
                                                 
        for key in hubble_race_viewer.toolbar.tools:
            hubble_race_viewer.toolbar.set_tool_enabled(key, False)
        
        hubble_race_data = Data(label='hubble_race_data')
        hubble_race_data.add_component([12,24,30], 'Distance (km)')
        hubble_race_data.add_component([4,8,10], 'Velocity (km/hr)')
        self.add_data(hubble_race_data)
        hubble_race_viewer.add_data(hubble_race_data)
        hubble_race_viewer.state.x_att = hubble_race_data.id['Distance (km)']
        hubble_race_viewer.state.y_att = hubble_race_data.id['Velocity (km/hr)']

        hubble_slideshow = HubbleExpUniverseSlideshow([self.viewers["hubble_race_viewer"], self.viewers["layer_viewer"]], self.stage_state.image_location)
        self.add_component(hubble_slideshow, label='py-hubble-slideshow')
        hubble_slideshow.observe(self._on_slideshow_opened, names=['opened'])

        layer_viewer.toolbar.set_tool_enabled("hubble:linedraw", self.stage_state.marker_reached("tre_lin2"))
        layer_viewer.toolbar.set_tool_enabled("hubble:linefit", self.stage_state.marker_reached("bes_fit1"))

        add_callback(self.stage_state, 'marker',
                     self._on_marker_update, echo_old=True)
        self.trigger_marker_update_cb = True


        not_ignore = {
            fit_table.subset_label: [layer_viewer],
            BEST_FIT_SUBSET_LABEL: [layer_viewer]
        }

        def label_ignore(x, label):
            return x.label == label

        for label, listeners in not_ignore.items():
            ignorer = partial(label_ignore, label=label)
            for viewer in self.all_viewers:
                if viewer not in listeners:
                    viewer.ignore(ignorer)
        
        # layers from the table selection have the same label, but we only want student_data selected
        layer_viewer.ignore(lambda layer: layer.label == fit_table.subset_label and layer.data != student_data)

        # load all the initial styles
        self._update_viewer_style(dark=self.app_state.dark_mode)

        # set reasonable offset for y-axis labels
        # it would be better if axis labels were automatically well placed
        layer_viewer.figure.axes[1].label_offset = "5em"
        
        # Set hypothetical galaxy info, if we have it
        self._update_hypgal_info()

        # Whenever data is updated, the appropriate viewers should update their bounds
        self.hub.subscribe(self, NumericalDataChangedMessage,
                           handler=self._on_data_change)

        # We want the hub_fit_viewer to be selecting for the same subset as the table
        def fit_selection_activate():
            table = self.get_widget('fit_table')
            table.initialize_subset_if_needed()
            self.session.edit_subset_mode.edit_subset = [table.subset]

        def fit_selection_deactivate():
            self.session.edit_subset_mode.edit_subset = []
        
        extend_tool(layer_viewer, 'bqplot:rectangle', fit_selection_activate,
                    fit_selection_deactivate)

        # If possible, we defer some of the setup for later, to make loading faster
        if self.story_state.stage_index < self.index:
            add_callback(self.story_state, 'stage_index', self._on_stage_index_changed)
        else:
            self._deferred_setup()
    
    def _on_marker_update(self, old, new):
        if not self.trigger_marker_update_cb:
            return
        markers = self.stage_state.markers
        advancing = markers.index(new) > markers.index(old)
        if advancing and new == "tre_dat2":
            layer_viewer = self.get_viewer("layer_viewer")
            layer_viewer.toolbar.set_tool_enabled('hubble:toggleclass', True)
        if advancing and new == "tre_lin1":
            layer_viewer = self.get_viewer("layer_viewer")
            class_meas_data = self.get_data(CLASS_DATA_LABEL)
            class_layer = layer_viewer.layer_artist_for_data(class_meas_data)
            class_layer.state.visible = False
        if advancing and new == "you_age1":
            layer_viewer = self.get_viewer("layer_viewer")                
            layer_viewer.toolbar.tools["hubble:linefit"].show_labels = True
        if advancing and new == "tre_lin1":
            layer_viewer = self.get_viewer("layer_viewer")
            layer_viewer.toolbar.set_tool_enabled('hubble:toggleclass', False)
        if advancing and new == "tre_lin2":
            layer_viewer = self.get_viewer("layer_viewer")
            layer_viewer.toolbar.tools["hubble:linefit"].show_labels = True
            layer_viewer.toolbar.set_tool_enabled("hubble:linedraw", True )
        if advancing and new == "bes_fit1":
            layer_viewer = self.get_viewer("layer_viewer")
            layer_viewer.toolbar.set_tool_enabled("hubble:linefit", True)   
            layer_viewer.toolbar.tools["hubble:linefit"].show_labels = False         
        if advancing and new == "hyp_gal1":
            layer_viewer = self.get_viewer("layer_viewer")
            layer_viewer.toolbar.tools["hubble:linefit"].show_labels = False  
            self.story_state.has_best_fit_galaxy = True
            layer_viewer.toolbar.tools["hubble:linedraw"].erase_line()
        if advancing and new =="age_rac1":
            self._update_hypgal_info()

    def _on_slideshow_opened(self, msg):
        self.stage_state.hubble_dialog_opened = msg["new"]
    
    def _on_class_layer_toggled(self, used):
        self.stage_state.class_layer_toggled = used
        if self.stage_state.marker == 'tre_dat2':
            self.stage_state.marker = 'tre_dat3'
            layer_toggle = self.get_component("py-layer-toggle")
            layer_toggle.remove_ignore_condition(self.ignore_class_layer)

    def _setup_scatter_layers(self):
        layer_viewer = self.get_viewer("layer_viewer")
        student_data = self.get_data(STUDENT_DATA_LABEL)
        class_meas_data = self.get_data(CLASS_DATA_LABEL)
        layer_viewer.add_data(student_data)
        layer_viewer.state.x_att = student_data.id[DISTANCE_COMPONENT]
        layer_viewer.state.y_att = student_data.id[VELOCITY_COMPONENT]
        
        # PALETTE: Y:FFBE0B, O:FB5607, Pi:FF006E, Pu:8338EC, Bl:3A86FF, LiBl:619EFF
        student_layer = layer_viewer.layer_artist_for_data(student_data)
        student_layer.state.color = '#FB5607'
        student_layer.state.zorder = 5
        student_layer.state.size = 8                    
        student_layer.state.alpha = 1
        # add class measurement data and hide by default
        layer_viewer.add_data(class_meas_data)
        layer_viewer.state.reset_limits()
        class_layer = layer_viewer.layer_artist_for_data(class_meas_data)
        class_layer.state.zorder = 1
        class_layer.state.color = "#3A86FF"
        class_layer.state.alpha = 1
        class_layer.state.size = 4
        class_layer.state.visible = False
        toggle_tool = layer_viewer.toolbar.tools['hubble:toggleclass']
        toggle_tool.set_layer_to_toggle(class_layer)

        layer_viewer.toolbar.set_tool_enabled('hubble:toggleclass', not self.stage_state.marker_before("tre_dat2"))

        # cosmicds PR157 - turn off fit line label for layer_viewer
        layer_viewer.toolbar.tools["hubble:linefit"].show_labels = False
    
        draw_tool = layer_viewer.toolbar.tools['hubble:linedraw'] 
        add_callback(draw_tool, 'line_drawn', self._on_trend_line_drawn)
        
        line_fit_tool = layer_viewer.toolbar.tools['hubble:linefit']
        add_callback(line_fit_tool, 'active', self._on_best_fit_line_shown)
        
        layer_toolbar = layer_viewer.toolbar
        layer_toolbar.set_tool_enabled("hubble:toggleclass", self.stage_state.marker_reached("tre_dat2"))
        add_callback(toggle_tool, 'toggled_count', self._on_class_layer_toggled) 
        add_callback(self.story_state, 'has_best_fit_galaxy', self._on_best_fit_galaxy_added)

        # Ignore the best-fit-galaxy subset in the layer viewer for line fitting
        layer_toolbar = layer_viewer.toolbar
        linefit_id = "hubble:linefit"
        layer_linefit = layer_toolbar.tools[linefit_id]
        layer_linefit.add_ignore_condition(lambda layer: layer.layer.label == BEST_FIT_SUBSET_LABEL)

        layer_toggle = self.get_component("py-layer-toggle")
        student_layer = layer_viewer.layer_artist_for_data(student_data)
        class_layer = layer_viewer.layer_artist_for_data(class_meas_data)
        
        table = self.get_widget('fit_table')
        table_subset_label = table.subset_label
        def layer_toggle_sort(state):
            labels = [STUDENT_DATA_LABEL, CLASS_DATA_LABEL, table_subset_label]
            try:
                return labels.index(state.layer.label)
            except ValueError:
                return len(labels)
        layer_toggle.sort_by(layer_toggle_sort)

        race_viewer = self.get_viewer("hubble_race_viewer")
        race_data = self.get_data("hubble_race_data")
        race_layer = race_viewer.layer_artist_for_data(race_data)
        race_layer.state.color = '#111111'
        race_layer.state.alpha = 1
        race_layer.state.size = 8
        race_viewer.state.reset_limits()
        race_viewer.state.x_max = 1.1 * race_viewer.state.x_max 
        race_viewer.state.y_max = 1.1 * race_viewer.state.y_max 

    def _on_stage_index_changed(self, index):
        print("Stage Index: ",self.story_state.stage_index)
        if index > 0:
            self._deferred_setup()

            # Remove this callback once we're done
            remove_callback(self.story_state, 'stage_index', self._on_stage_index_changed)

    def _deferred_setup(self):
        self._setup_scatter_layers()

    @property
    def all_viewers(self):
        return [layout.viewer for layout in self.viewers.values()]

    def _update_hypgal_info(self):
        data = self.get_data(STUDENT_DATA_LABEL)
        indices = where(data[NAME_COMPONENT] == BEST_FIT_GALAXY_NAME)
        if indices[0]:
            index = indices[0][0]
            self.stage_state.hypgal_velocity = data[VELOCITY_COMPONENT][index]
            self.stage_state.hypgal_distance = data[DISTANCE_COMPONENT][index]
            self.stage_state.our_age = (AGE_CONSTANT * self.stage_state.hypgal_distance/self.stage_state.hypgal_velocity)

    def reset_viewer_limits(self):
        self._reset_limits_for_data(STUDENT_DATA_LABEL)
        self._reset_limits_for_data(CLASS_DATA_LABEL)

    def _reset_limits_for_data(self, label):
        viewer_id = self.viewer_ids_for_data.get(label, [])
        for vid in viewer_id:
            self.get_viewer(vid).state.reset_limits()

    def _on_data_change(self, msg):
        label = msg.data.label
        if label in [STUDENT_DATA_LABEL, CLASS_DATA_LABEL]:
            self._reset_limits_for_data(label)
        if label == STUDENT_DATA_LABEL:
            self._update_hypgal_info() 

    def _update_viewer_style(self, dark):
        viewers = ['layer_viewer',
                   'hubble_race_viewer',
                   ]

        viewer_type = ["scatter",
                       "scatter",]

        theme_name = "dark" if dark else "light"
        for viewer, vtype in zip(viewers, viewer_type):
            viewer = self.get_viewer(viewer)
            style = load_style(f"default_{vtype}_{theme_name}")
            update_figure_css(viewer, style_dict=style)

    def _on_dark_mode_change(self, dark):
        super()._on_dark_mode_change(dark)
        self._update_viewer_style(dark)

    def table_selected_color(self, dark):
        return "colors.lightBlue.darken4"

    def _update_image_location(self, using_voila):
        prepend = "voila/files/" if using_voila else ""
        self.stage_state.image_location = prepend + "data/images/stage_three"

    def _on_trend_line_drawn(self, is_drawn):
        print("Trend line drawn: ", is_drawn)
        self.stage_state.trend_line_drawn = is_drawn
        
    def _on_best_fit_line_shown(self, is_active):
        print("Best fit line shown: ", is_active)
        if not self.stage_state.best_fit_clicked:
            self.stage_state.best_fit_clicked = is_active

    def _on_best_fit_galaxy_added(self, value):
        layer_viewer = self.get_viewer("layer_viewer")
        linefit_tool = layer_viewer.toolbar.tools["hubble:linefit"]
        if value and not linefit_tool.active:
            linefit_tool.activate()
    
    def _on_stage_4_complete(self, change):
        if change:
            self.story_state.stage_index =  self.story_state.stage_index + 1

            # We need to do this so that the stage will be moved forward every
            # time the button is clicked, not just the first
            self.stage_state.stage_4_complete = False
