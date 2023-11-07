from echo import delay_callback, add_callback
from glue.viewers.scatter.state import ScatterViewerState
from glue_jupyter.bqplot.histogram import BqplotHistogramView, BqplotHistogramLayerArtist
from glue_jupyter.bqplot.scatter import BqplotScatterView
from cosmicds.viewers.cds_viewer import CDSHistogramViewerState, CDSScatterViewerState
from cosmicds.viewers.cds_viewer import cds_viewer
from cosmicds.viewers.dotplot.viewer import BqplotDotPlotView
from .hubble_dotplot import HubbleDotPlotView

from cosmicds.mixins import LineHoverStateMixin, LineHoverViewerMixin

__all__ = [
    "HubbleScatterViewerState", "HubbleFitViewerState",
    "HubbleFitView", "HubbleScatterView", "HubbleClassHistogramView",
    "HubbleDotPlotView"
]


class HubbleScatterViewerState(CDSScatterViewerState):

    def reset_limits(self, visible_only=True):
        with delay_callback(self, 'x_min', 'x_max', 'y_min', 'y_max'):
            super().reset_limits(visible_only=visible_only)
            self.x_min = min(self.x_min, 0) if self.x_min is not None else 0
            self.y_min = min(self.y_min, 0) if self.y_min is not None else 0


class HubbleFitViewerState(HubbleScatterViewerState):
    
    def reset_limits(self, visible_only=True):
        with delay_callback(self, 'x_min', 'x_max', 'y_min', 'y_max'):
            super().reset_limits(visible_only=visible_only)
            self.x_max = 1.1 * self.x_max
            self.y_max = 1.1 * self.y_max

class HubbleHistogramViewerState(LineHoverStateMixin, CDSHistogramViewerState):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_line = False
        
        
    def reset_limits(self):
        with delay_callback(self, 'x_min', 'x_max', 'y_min', 'y_max'):
            CDSHistogramViewerState.reset_limits(self)
            # check that histogram bin edges are included
            self.x_min = min(self.x_min, self.hist_x_min)
            self.x_max = max(self.x_max, self.hist_x_max)
    
    def show_measuring_line(self):
        self.show_line = True
    
    def hide_measuring_line(self):
        self.show_line = False


class HubleHistogramLayerArtist(BqplotHistogramLayerArtist):
    
    def _update_visual_attributes(self, *args, **kwargs):
        super()._update_visual_attributes(*args, **kwargs)
        if not self.enabled:
            return
        
        if hasattr(self.view, 'line') and hasattr(self.view, 'line_label'):
            if getattr(self.view,'line_visible', False):
                self.view.figure.marks = self.view.figure.marks + [self.view.line, self.view.line_label]
    
    
class HubbleHistogramViewer(LineHoverViewerMixin, BqplotHistogramView):
    
    _state_cls = HubbleHistogramViewerState
    _data_artist_cls = HubleHistogramLayerArtist
    _subset_artist_cls = HubleHistogramLayerArtist
    
    def __init__(self, *args, **kwargs):
        super(HubbleHistogramViewer, self).__init__(*args, **kwargs)
        self.line_visible = False
        add_callback(self.state, 'show_line', self._update_visibility)
        add_callback(self.state, 'show_label', self._update_visibility)
        
        
    
    def _add_marks(self, *args):
        if not self.measuring_line_visible:
            marks = [self.line, self.line_label]
            marks = [m for m in marks if m not in self.figure.marks]
            self.figure.marks = self.figure.marks + marks

    
    def _update_visibility(self, val):
        if val:
            self.add_measuring_line()
            self.line_visible = True
        else:
            self.remove_measuring_line()
            self.line_visible = False
    
    def add_measuring_line(self):
        self._add_marks()
        if self._on_mouse_moved not in self._event_callbacks:
            self.add_event_callback(self._on_mouse_moved, events = ['mousemove'])
    
    def remove_measuring_line(self):
        if self.measuring_line_visible:
            self.figure.marks = [m for m in self.figure.marks if m not in [self.line, self.line_label]]
            self.remove_event_callback(self._on_mouse_moved)
            if self.state.show_line:
                self.state.show_line = False

    
    @property
    def measuring_line_visible(self):
        in_marks = all([mark in self.figure.marks for mark in [self.line, self.line_label]])
        # visible = all([mark.visible for mark in [self.line, self.line_label]])
        # has_callback = self._on_mouse_moved in self._event_callbacks
        # print(f"{self.LABEL}: Measuring line visible: in_marks: {in_marks}, visible: {visible}, callback: {has_callback}, line_visible: {self.line_visible}")
        return in_marks


HubbleFitView = cds_viewer(
    BqplotScatterView,
    name="HubbleFitView",
    viewer_tools=[
        "bqplot:home",
        "bqplot:rectzoom",
        "bqplot:rectangle",
        "cds:linedraw",
        "hubble:linefit"
    ],
    label='Fit View',
    state_cls=HubbleFitViewerState
)

HubbleFitLayerView = cds_viewer(
    BqplotScatterView,
    name="HubbleFitLayerView",
    viewer_tools=[
        # "bqplot:home",
        # 'bqplot:rectangle',
        "hubble:linefit",
        "hubble:linedraw",
    ],
    label='Layer View',
    state_cls=HubbleFitViewerState
)

HubbleScatterView = cds_viewer(
    BqplotScatterView,
    name="HubbleScatterView",
    viewer_tools=[
        'bqplot:home',
        'bqplot:rectzoom',
        'hubble:linefit'
    ],
    label='Scatter View',
    state_cls=HubbleScatterViewerState
)

HubbleHistogramView = cds_viewer(
    HubbleHistogramViewer,
    state_cls=HubbleHistogramViewerState,
    name="HubbleHistogramView",
    viewer_tools=[
        "bqplot:home",
        "bqplot:xzoom",
    ],
    label="Class Histogram"
)

HubbleClassHistogramView = cds_viewer(
    HubbleHistogramViewer,
    state_cls=HubbleHistogramViewerState,
    name="HubbleClassHistogramView",
    viewer_tools=[
        "bqplot:home",
        "bqplot:xzoom",
        "bqplot:xrange"
    ],
    label="Class Histogram"
)


# HubbleDotPlotView = cds_viewer(
#     BqplotDotPlotView,
#     name="HubbleDotPlotView",
#     viewer_tools=[
#         "bqplot:home",
#         "bqplot:xzoom",
#     ],
#     label="Dot Plot"
# )
