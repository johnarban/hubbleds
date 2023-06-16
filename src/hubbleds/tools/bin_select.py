from glue_jupyter.bqplot.common.tools import BqplotSelectionTool
from glue.config import viewer_tool
from echo import CallbackProperty, add_callback
from bqplot_image_gl.interacts import MouseInteraction, mouse_events
from glue_jupyter.bqplot.common.tools import InteractCheckableTool, CheckableTool


from glue.config import viewer_tool
from glue_jupyter.bqplot.common.tools import INTERACT_COLOR

from contextlib import nullcontext


from bqplot.interacts import BrushIntervalSelector, IndexSelector

from glue.core.roi import RangeROI
from glue.core.subset import RangeSubsetState
from glue.config import viewer_tool
import numpy as np


# this decorator tells glue this is a viewer tool, so it knows what to do with
# all this info
@viewer_tool
class BinSelect(BqplotSelectionTool):
    icon = 'glue_xrange_select'
    mdi_icon = "mdi-select-compare"
    tool_id = 'hubble:binselect'
    action_text = 'Select fully enclosed bins'
    tool_tip = 'Select fully enclosed bins'
    tool_activated = CallbackProperty(False)
    
    _x_min = CallbackProperty(0)
    _x_max = CallbackProperty(0)
    _selected_range = CallbackProperty((0,0))
    
    _apply_roi = True
    

    def __init__(self, viewer, **kwargs):

        super().__init__(viewer, **kwargs)

        self.interact = BrushIntervalSelector(scale=self.viewer.scale_x,
                                              color=INTERACT_COLOR)

        self.interact.observe(self.update_selection, "brushing")
        
        self.roi = None
    
    def apply_roi(self, lo, hi):
        if self._apply_roi:
            self.roi = RangeROI(min=lo, max=hi, orientation='x')
            self.viewer.apply_roi(self.roi)

    def update_selection(self, *args):
        with self.viewer._output_widget or nullcontext():
            bins = self.viewer.state.bins
            bin_centers = (bins[:-1] + bins[1:]) / 2
            if self.interact.selected is not None:
                x = self.interact.selected
                x_min = min(x)
                x_max = max(x)
                self._selected_range = (x_min, x_max)
                if x_min != x_max:
                    left = np.searchsorted(bin_centers, x_min, side='left')
                    right = np.searchsorted(bin_centers, x_max, side='right')
                    x_min, x_max = bins[left], bins[right]
                self._x_min = x_min
                self._x_max = x_max
                self.apply_roi(x_min, x_max)

            self.interact.selected = None
    
    @property
    def subset_state(self):
        if self._x_min == self._x_max:
            return None
        return RangeSubsetState(lo=self._x_min, 
                         hi=self._x_max, 
                         att=self.viewer.state.x_att)
    
    @property
    def selection(self):
        selection = {
            'bin_min': self._x_min,
            'bin_max': self._x_max,
            'bin_center': (self._x_min + self._x_max) / 2,
            'selected_range': self._selected_range
        }
        return selection
    
    def activate(self):
        with self.viewer._output_widget or nullcontext():
            self.interact.selected = None
        super().activate()
        # self.tool_activated = True
    




# this decorator tells glue this is a viewer tool, so it knows what to do with
# all this info
@viewer_tool
class SingleBinSelect(InteractCheckableTool):
    icon = 'glue_crosshair'
    mdi_icon = "mdi-cursor-default-click"
    tool_id = 'hubble:singlebinselect'
    action_text = 'Select a bins'
    tool_tip = 'Select a bins'
    tool_activated = CallbackProperty(False)
    
    allow_nonzero_bins = True
    
    _apply_roi = True
    _roi_orientation = 'x'
    
    _selected_value = CallbackProperty(0.0)
    _bin_edges = CallbackProperty((0,0))
    _bin_center = CallbackProperty(0.0)
    

    def __init__(self, viewer, **kwargs):

        super().__init__(viewer, **kwargs)
        
        
        self.roi = None
        self.interact = MouseInteraction(
            x_scale=self.viewer.scale_x,
            y_scale=self.viewer.scale_y,
            move_throttle=70,
            next=None,
            events=['click']
        )
        self.interact.on_msg(self._message_handler)
        
        def reset_selected_value(old, new):
            if new is None:
                self._selected_value = old
                
        add_callback(self, '_selected_value', reset_selected_value, echo_old=True)
        
    def _message_handler(self, interaction, content, buffers):
        if content['event'] == 'click':
            x = content['domain']['x']
            
            self.bin_select(x)
    
    def apply_roi(self, lo, hi):
        if self._apply_roi:
            self.roi = RangeROI(min=lo, max=hi, orientation=self._roi_orientation)
            self.viewer.apply_roi(self.roi)
    
    def bin_select(self, x):
        # select the histogram bin corresponding to the x-position of the selector line
        if x is None:
            return
        self._selected_value = x
        viewer = self.viewer
        layer = viewer.layers[0]
        bins, hist = layer.bins, layer.hist
        dx = bins[1] - bins[0]
        index = np.searchsorted(bins, x, side='right')
        # only update the subset if the bin is not empty
        if self.allow_nonzero_bins or (hist[max(index-1,0)] > 0):
            right_edge = bins[index]
            left_edge = right_edge - dx
            self._bin_edges = left_edge, right_edge
            self._bin_center = (right_edge + left_edge) / 2
            self.apply_roi(left_edge, right_edge)
        
        self.viewer.toolbar.active_tool = None
    
    @property
    def subset_state(self):
        if self._bin_edges[0] == self._bin_edges[1]:
            return None
        return RangeSubsetState(lo=self._bin_edges[0], 
                         hi=self._bin_edges[0], 
                         att=self.viewer.state.x_att)
    
    @property
    def selection(self):
        selection = {
            'bin_min': self._bin_edges[0],
            'bin_max': self._bin_edges[1],
            'bin_center': self._bin_center,
            'selected_val': self._selected_value
        }
        return selection
        
    def activate(self):
        return super().activate()
    
    def deactivate(self):
        self._selected_value = None
        return super().deactivate()
   
