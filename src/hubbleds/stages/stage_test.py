from cosmicds.phases import CDSState
from cosmicds.registries import register_stage
from cosmicds.utils import load_template
from ..stage import HubbleStage

from traitlets import default

class StageState(CDSState):
    pass

@register_stage(story="hubbles_law", index=5, steps=["TEST STEP"])
class StageTest(HubbleStage):

    _state_cls = StageState

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

        self.add_viewer(label="layer_viewer")
