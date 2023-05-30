from glue_jupyter.bqplot.common.tools import BqplotSelectionTool
from glue.config import viewer_tool
from echo import CallbackProperty
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

__all__ = ['SingleBinSelectNoRoi', 'BinRangeSelectNoRoi']

# this decorator tells glue this is a viewer tool, so it knows what to do with
# all this info
@viewer_tool
class SingleBinSelectNoRoi(InteractCheckableTool):
    icon = 'glue_crosshair'
    mdi_icon = "mdi-cursor-default-click"
    tool_id = 'hubble:singlebinselectonly'
    action_text = 'Select a bin or range'
    tool_tip = 'Select a bin or range'
    tool_activated = CallbackProperty(False)
    x = CallbackProperty(0)
    x_min = CallbackProperty(0)
    x_max = CallbackProperty(0)
    x_sel = CallbackProperty(0)
    
    sel_bin = CallbackProperty(0)
    sel_bin_center = CallbackProperty(0)
    sel_binrange = CallbackProperty(0)

    def __init__(self, viewer, **kwargs):

        super().__init__(viewer, **kwargs)
        
        self.interact = MouseInteraction(
            x_scale=self.viewer.scale_x,
            y_scale=self.viewer.scale_y,
            move_throttle=70,
            next=None,
            events=['click']
        )
        self.sel_binrange = (None, None)
        self.sel_bin = None
        
        self.interact.on_msg(self._message_handler)
    
    def _message_handler(self, interaction, content, buffers):
        if content['event'] == 'click':
            x = content['domain']['x']
            self.x_sel = x
            print('click', x)
            self.bin_select(x)

        
            
    def bin_select(self, x):
        # select the histogram bin corresponding to the x-position of the selector line
        if x is None:
            return
        
        # now get the bin
        viewer = self.viewer
        layer = viewer.layers[0]
        bins, hist = layer.bins, layer.hist
        dx = bins[1] - bins[0]
        index = np.searchsorted(bins, x, side='right')
        
        # only update the subset if the bin is not empty
        right_edge = bins[index]
        left_edge = right_edge - dx
        
        self.sel_bin = (left_edge, right_edge)
        self.sel_bin_center = (left_edge + right_edge) / 2
        print('bin', self.sel_bin, self.sel_bin_center)
        
        self.viewer.toolbar.active_tool = None
    

    def activate(self):
        return super().activate()
    
    def deactivate(self):
        self.x = None
        return super().deactivate()
   

@viewer_tool
class BinRangeSelectNoRoi(BqplotSelectionTool):
    icon = 'glue_xrange_select'
    mdi_icon = "mdi-select-compare"
    tool_id = 'hubble:binselectonly'
    action_text = 'Select fully enclosed bins'
    tool_tip = 'Select fully enclosed bins'
    tool_activated = CallbackProperty(False)
    x_min = CallbackProperty(0)
    x_max = CallbackProperty(0)
    x_range = CallbackProperty(0)
    

    def __init__(self, viewer, **kwargs):

        super().__init__(viewer, **kwargs)

        self.interact = BrushIntervalSelector(scale=self.viewer.scale_x,
                                              color=INTERACT_COLOR)

        self.interact.observe(self.update_selection, "brushing")

    def update_selection(self, *args):
        print('dragging')
        with self.viewer._output_widget or nullcontext():
            bins = self.viewer.state.bins
            bin_centers = (bins[:-1] + bins[1:]) / 2
            if self.interact.selected is not None:
                x = self.interact.selected
                x_min = min(x)
                x_max = max(x)
                if x_min != x_max:
                    left = np.searchsorted(bin_centers, x_min, side='left')
                    right = np.searchsorted(bin_centers, x_max, side='right')
                    x = bins[left], bins[right]
                self.x_min = x_min
                self.x_max = x_max
                self.x_range = (self.x_min, self.x_max)
                print('range', self.x_range)
            self.interact.selected = None
        

    def activate(self):
        with self.viewer._output_widget or nullcontext():
            self.interact.selected = None
        super().activate()
        self.tool_activated = True
    

