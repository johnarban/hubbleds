import ipyvuetify as v
from cosmicds.utils import load_template
from glue_jupyter.state_traitlets_helpers import GlueState
from traitlets import Bool, Unicode, Int


class ExampleComponent(v.VuetifyTemplate):
    template = Unicode().tag(sync=True)
    state = GlueState().tag(sync=True)
    can_advance = Bool(False).tag(sync=True)

    def __init__(self, filename, path, state, *args, **kwargs):
        self.state = state
        super().__init__(*args, **kwargs)
        self.template = load_template(filename, path)
