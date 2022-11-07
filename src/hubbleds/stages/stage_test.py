from functools import partial
from os.path import join
from pathlib import Path

from echo import CallbackProperty, add_callback, remove_callback
from glue_jupyter.link import dlink, link
from traitlets import Bool, default

from cosmicds.components.generic_state_component import GenericStateComponent
from cosmicds.phases import CDSState
from cosmicds.registries import register_stage
from cosmicds.utils import (RepeatedTimer, extend_tool, load_template,
                            update_figure_css)
from hubbleds.utils import IMAGE_BASE_URL

from ..components import AgeCalc, HubbleExp, ProData, TrendsData, ExampleComponent
from ..data.styles import load_style
from ..data_management import (ALL_CLASS_SUMMARIES_LABEL, ALL_DATA_LABEL,
                               ALL_STUDENT_SUMMARIES_LABEL,
                               BEST_FIT_GALAXY_NAME, BEST_FIT_SUBSET_LABEL,
                               CLASS_DATA_LABEL, CLASS_SUMMARY_LABEL,
                               HUBBLE_1929_DATA_LABEL, HUBBLE_KEY_DATA_LABEL,
                               STUDENT_DATA_LABEL)
from ..stage import HubbleStage


class StageState(CDSState):
    
    marker = CallbackProperty("")
    indices = CallbackProperty({})
    
    stage_test_complete = CallbackProperty(False)
    
    # add toggles or other state variables here
    # these can be acccessed from the vue component
    # using state.variable_name
    # e.g. 
    # interaction_one_done = CallbackProperty(False)
    # interaction_two_done = CallbackProperty(False)
    # a callback should be associated with the variable
    # to trigger a change in the vue component
    # e.g.
    # add_callback(self, 'interaction_one_done', self._on_interaction_one_done)
    # we generally use the "_on_" prefix for these callbacks
    # and these are placed at the end of the HubbleStage class
    
    
    markers = [
        "ex_com1",
        "ex_com2",
        ]
        
    step_markers = CallbackProperty([
        'ex_com1',
        'ex_com2',
    ])
    
    _NONSERIALIZED_PROPERTIES = [
        'markers', 'indices', 'step_markers', 'image_location',
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


@register_stage(story="hubbles_law", index=7, steps=["TEST STEP1", "TEST STEP2"])
class StageTest(HubbleStage):
    show_team_interface = Bool(False).tag(sync=True)
    _state_cls = StageState
    
    @default('stage_state')
    def _default_state(self):
        return StageState()
    
    @default('template')
    def _default_template(self):
        return load_template("stage_test.vue", __file__)

    @default('stage_icon')
    def _default_stage_icon(self):
        return "4"

    @default('title')
    def _default_title(self):
        return "Test"

    @default('subtitle')
    def _default_subtitle(self):
        return "Testing"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_team_interface = self.app_state.show_team_interface
        
        # add callbacks here
        # e.g. add callback for self.stage_state.stage_test_complete
        add_callback(self.stage_state, 'stage_test_complete',
                     self._on_stage_complete)
        
        # add some state components
        state_components = ["example_component_1", "example_component_2"]
        state_components_dir = str(
            Path(
                __file__).parent.parent / "components" / "example_component")
        path = join(state_components_dir, "")
        self.add_components_from_path(state_components, path, ExampleComponent)
        
        # add a veiwer from a previous stage
        self.add_viewer(label="layer_viewer")
        
        # run deferred setup if we are at or past this stage
        # _on_stage_index_changed is a good example of removing a callback
        if self.story_state.stage_index < self.index:
            add_callback(self.story_state, 'stage_index', self._on_stage_index_changed)
        else:
            self._deferred_setup()
    
    
    # ===========================================
    # =========== BEGIN STAGE METHODS ===========
    # ===========================================
    
    def _setup_scatter_layers(self):
        pass
        
    def _setup_histogram_layers(self):
        pass
        
    def _deferred_setup(self):
        """ run only after the stage is loaded """
        self._setup_scatter_layers()
        self._setup_histogram_layers()
        
    
    
    def _on_marker_update(self, old, new):
        if not self.trigger_marker_update_cb:
            return
        
        markers = self.stage_stage.makers
        advancing = markers.index(new) > markers.index(old)
        
        if advancing:
            """ Do something when advancing """
            if new == "ex_com1":
                # do something here
                pass
        
    
    
    
    
    
    
    def add_components_from_path(self, state_components, path, component_cls = GenericStateComponent):
        """ Add components from a path."""
        ext = ".vue"
        for comp in state_components:
            label = f"c-{comp}".replace("_", "-") # transform to kebab-case
            component = component_cls(comp + ext, path,self.stage_state)
            self.add_component(component, label=label)
    




    # =========== CALLBACK FUNCTIONS ===========
    def _on_stage_complete(self, change):
        if change:
            self.story_state.stage_index = self.story_state.stage_index + 1
            # We need to do this so that the stage will be moved forward every
            # time the button is clicked, not just the first (via Carifio)
            self.stage_state.stage_four_complete = False
    
    def _on_stage_index_changed(self, index):
        print("Stage Index: ",self.story_state.stage_index)
        if index > 0:
            self._deferred_setup()
            # Remove this callback once we're done
            remove_callback(self.story_state, 'stage_index', self._on_stage_index_changed)
    
    
    def _update_viewer_style(self, dark):
        viewers = ['layer_viewer',
                   # some histogram viewer
                   ]

        viewer_type = ["scatter",
                     # "histogram" # add more viewers here
                       ]
                       
        theme_name = "dark" if dark else "light"
        for viewer, vtype in zip(viewers, viewer_type):
            viewer = self.get_viewer(viewer)
            style = load_style(f"default_{vtype}_{theme_name}")
            update_figure_css(viewer, style_dict=style)
    
    # _on_dark_mode_change is called when the dark mode button is clicked
    # it doesn't need a separate callback function
    def _on_dark_mode_change(self, dark):
        super()._on_dark_mode_change(dark)
        self._update_viewer_style(dark)
    