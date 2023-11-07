from bqplot import Label
from bqplot.marks import Lines
from cosmicds.components.toolbar import Toolbar
from echo import delay_callback
from glue.config import viewer_tool
from glue.viewers.common.utils import get_viewer_tools
from glue.viewers.scatter.state import ScatterViewerState
from glue_jupyter.bqplot.scatter import BqplotScatterView
import numpy as np

from cosmicds.mixins import LineHoverStateMixin, LineHoverViewerMixin
from cosmicds.viewers.cds_viewer import cds_viewer
from ..utils import H_ALPHA_REST_LAMBDA, MG_REST_LAMBDA

__all__ = ['SpectrumView', 'SpectrumViewerState']


class SpectrumViewerState(LineHoverStateMixin, ScatterViewerState):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def reset_y_limits_for_view(self):
        with delay_callback(self, 'y_min', 'y_max'):
            ymin, ymax = self.y_min, self.y_max
            layers = list(filter(lambda layer: layer.visible, self.layers))
            if len(layers) == 0:
                new_ymin, new_ymax = 0, 1
            else:
                new_ymin, new_ymax = np.inf, -np.inf
                for layer in layers: 
                    x_values = layer.layer[self.x_att]
                    y_values = layer.layer[self.y_att]
                    y_values = y_values[np.where((x_values >= self.x_min) & (x_values <= self.x_max))]
                    new_ymin = min(new_ymin, np.nanmin(y_values))
                    new_ymax = max(new_ymax, np.nanmax(y_values))

            self.y_min = new_ymin
            self.y_max = self._YMAX_FACTOR * new_ymax
            self.resolution_y *= (self.y_max - self.y_min) / (ymax - ymin)


class SpecView(LineHoverViewerMixin, BqplotScatterView):

    inherit_tools = False
    tools = ['bqplot:home', 'hubble:wavezoom', 'hubble:restwave'] # remove 'cds:info' for now
    _state_cls = SpectrumViewerState
    LABEL = "Spectrum Viewer"

    observed_text = ' (observed)'
    rest_text = ' (rest)'

    def __init__(self, *args, **kwargs):
        super(SpecView, self).__init__(*args, **kwargs)

        self.element = None

        self.element_tick = Lines(
            x=[],
            y=[0, 0],
            x_offset=-10,
            opacities=[0.7],
            colors=['red'],
            stroke_width=10,
            scales={
                'x': self.scales['x'],
                'y': self.scales['y'],
            })

        self.element_label = Label(
            text=["H-α"],
            x=[],
            y=[],
            x_offset=-5,
            opacities=[0.7],
            colors=['red'],
            scales={
                'x': self.scales['x'],
                'y': self.scales['y'],
            })
        
        self.figure.marks += [self.element_tick, self.element_label]

        self.toolbar.observe(self._active_tool_change, names=['active_tool'])

    @staticmethod
    def _label_text(value):
        return f"{value:.0f} Å"

    def _active_tool_change(self, change):
        is_tool = change.new is not None
        line_visible = not is_tool or change.new.tool_id != 'hubble:wavezoom'
        for mark in [self.line, self.line_label,
                     self.label_background]:
            mark.visible = line_visible

    def _update_y_locations(self, resolution=None):
        super()._update_y_locations()
        scale = self.scales['y']
        ymin, ymax = scale.min, scale.max

        if ymin is None or ymax is None:
            return

        tick_bounds = [ymax * 0.74, ymax * 0.87]
        bottom_label_position = ymax * 0.91
        self.element_tick.y = tick_bounds
        self.element_label.y = [bottom_label_position]

    def update(self, name, element, z, previous=None):
        self.spectrum_name = name
        self.element = element
        self.z = z
        rest = MG_REST_LAMBDA if element == 'Mg-I' else H_ALPHA_REST_LAMBDA
        self.shifted = rest * (1 + z)
        items_visible = bool(
            z > 0)  # The bqplot Mark complained without the explicit bool() call
        self.element_label.visible = items_visible
        self.element_tick.visible = items_visible
        self.line.visible = items_visible
        self.line_label.visible = items_visible
        self.label_background.visible = items_visible
        has_previous = previous is not None
        self.previous_line.visible = has_previous
        self.previous_line_label.visible = has_previous
        self.previous_label_background.visible = has_previous
        if has_previous:
            self.previous_line.x = [previous, previous]
            self.previous_line_label.x = [previous, previous]
            self.previous_line_label.text = [self._label_text(previous)]
            self.previous_label_background.x = self._x_background_coordinates(
                previous)
        self.element_label.x = [self.shifted, self.shifted]
        self.element_label.text = [f"{element} (observed)"]
        self.element_tick.x = [self.shifted, self.shifted]
        self._update_locations()
        self._resolution_dirty = True

    def add_data(self, data):
        super().add_data(data)
        self.state.x_att = data.id['lambda']
        self.state.y_att = data.id['flux']
        self.layers[0].state.attribute = data.id['flux']
        for layer in self.layers:
            if layer.state.layer.label != data.label:
                layer.state.visible = False
            else:
                layer.state.color = "#507FB6"
                layer.state.alpha = 1
                layer.state.markers_visible = False
                layer.state.line_visible = True
                layer.state.linewidth = 1.8

        bring_to_front = [
            self.previous_label_background, self.previous_line,
            self.previous_line_label,
            self.label_background, self.line, self.line_label
        ]
        marks = [x for x in self.figure.marks if x not in bring_to_front]
        self.figure.marks = marks + bring_to_front

    def initialize_toolbar(self):
        self.toolbar = Toolbar(self)

        tool_ids, subtool_ids = get_viewer_tools(self.__class__)

        if subtool_ids:
            raise ValueError(
                'subtools are not yet supported in Jupyter viewers')

        for tool_id in tool_ids:
            mode_cls = viewer_tool.members[tool_id]
            mode = mode_cls(self)
            self.toolbar.add_tool(mode)

    @property
    def line_visible(self):
        return self.line.visible


SpectrumView = cds_viewer(SpecView, "SpectrumView")
