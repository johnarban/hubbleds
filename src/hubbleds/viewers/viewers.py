from echo import delay_callback, add_callback
from glue.viewers.scatter.state import ScatterViewerState
from glue_jupyter.bqplot.histogram import BqplotHistogramView
from glue_jupyter.bqplot.scatter import BqplotScatterView
from cosmicds.viewers.cds_viewer import CDSHistogramViewerState, CDSScatterViewerState
from cosmicds.viewers.cds_viewer import cds_viewer
from cosmicds.viewers.dotplot.viewer import BqplotDotPlotView
from .hubble_dotplot import HubbleDotPlotView

from cosmicds.mixins import LineHoverStateMixin, LineHoverViewerMixin

__all__ = [
    "HubbleScatterViewerState", "HubbleFitViewerState",
    "HubbleFitView", "HubbleScatterView", "HubbleClassHistogramView",
    "HubbleDotPlotView", 'HubbleTestHist'
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
    
    def show_measuring_line(self):
        self.show_line = True
    
    def hide_measuring_line(self):
        self.show_line = False

class HubbleHistogramViewer(LineHoverViewerMixin, BqplotHistogramView):
    
    _state_cls = HubbleHistogramViewerState
    
    def __init__(self, *args, **kwargs):
        super(HubbleHistogramViewer, self).__init__(*args, **kwargs)
        
        add_callback(self.state, 'show_line', self._update_visibility)
        add_callback(self.state, 'show_label', self._update_visibility)
        
        
    
    def _add_marks(self, *args):
        marks = [self.line, self.line_label]
        for new_mark in marks:
            if new_mark not in self.figure.marks:
                self.figure.marks = self.figure.marks + [new_mark]

    
    def _update_visibility(self, val):
        if val:
           #print("Adding measuring line")
            self.add_measuring_line()
        else:
           #print("Removing measuring line")
            self.remove_measuring_line()
    
    def add_measuring_line(self):
        self._add_marks()
        self.add_event_callback(self._on_mouse_moved, events = ['mousemove'])
    
    def remove_measuring_line(self):
        self.figure.marks = [m for m in self.figure.marks if m not in [self.line, self.line_label]]
        self.remove_event_callback(self._on_mouse_moved)
        

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
        "hubble:singlebinselect",
        "hubble:binselect",
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
        "bqplot:xrange",
        "hubble:singlebinselect",
        "hubble:binselect",
    ],
    label="Class Histogram"
)

HubbleTestHist = cds_viewer(
    HubbleHistogramViewer,
    state_cls=HubbleHistogramViewerState,
    name="HubbleHistogramView",
    viewer_tools=[
        "bqplot:home",
        "bqplot:xzoom",
        "hubble:singlebinselect",
        "hubble:binselect",
    ],
    label="Test Histogram"
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
