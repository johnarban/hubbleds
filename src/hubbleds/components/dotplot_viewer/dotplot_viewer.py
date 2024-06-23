from random import randint

import solara
from glue.core import Data
from reacton import ipyvuetify as rv

from hubbleds.viewers.hubble_dotplot import HubbleDotPlotView, HubbleDotPlotViewer


@solara.component
def DotplotViewer(gjapp, data=None, component_id=None, title = None, height=400, on_click_callback = None):
    
    vertical_line_visible = solara.use_reactive(True)
    
    with rv.Card() as main:
        with rv.Toolbar(dense=True, color="primary"):
            with rv.ToolbarTitle():
                title_container = rv.Html(tag="div")

            rv.Spacer()
            toolbar_container = rv.Html(tag="div")

        viewer_container = rv.Html(tag="div", style_=f"width: 100%; height: {height}px")

        def _add_viewer():
            if data is None:
                viewer_data = Data(label = "Test Data", x=[randint(1, 10) for _ in range(30)])
                gjapp.data_collection.append(viewer_data)
            else: 
                viewer_data = data
            

            dotplot_view: HubbleDotPlotViewer = gjapp.new_data_viewer(
                HubbleDotPlotView, data=viewer_data, show=False
            )

            
            # def on_click(**kwargs):
            #     fig = dotplot_view.figure
            #     fig.add_vline(
            #         x=kwargs['points']['xs'][0],
            #         line_width=1,
            #         line_color="red",
            #         annotation=f"{round(kwargs['points']['xs'][0])}",
            #         visible=vertical_line_visible.value
            #     )
                
            #     if on_click_callback is not None:
            #         on_click_callback(**kwargs)
                    
            
            # if on_click_callback is not None:
            #     dotplot_view.set_selection_active(True)
            #     dotplot_view.set_selection_callback(on_click)
            # else:
            #     dotplot_view.set_selection_callback(None)
            #     dotplot_view.set_selection_active(False)
            #     dotplot_view.figure.on_edits_completed(dotplot_view.figure.plotly_relayout({'selections': [], 'dragmode': False}))
            
            
            print("component_id", component_id)
            if component_id is not None:
                dotplot_view.state.x_att = viewer_data.id[component_id]
            
            if title is not None:
                dotplot_view.state.title = title
    
            title_widget = solara.get_widget(title_container)
            title_widget.children = (dotplot_view.state.title or "DOTPLOT VIEWER",)

            toolbar_widget = solara.get_widget(toolbar_container)
            toolbar_widget.children = (dotplot_view.toolbar,)

            viewer_widget = solara.get_widget(viewer_container)
            viewer_widget.children = (dotplot_view.figure_widget,)

            # The auto sizing in the plotly widget only works if the height
            #  and width are undefined. First, unset the height and width,
            #  then enable auto sizing.
            dotplot_view.figure_widget.update_layout(height=None, width=None)
            dotplot_view.figure_widget.update_layout(autosize=True, height=height)
            dotplot_view.figure_widget.update_layout(
                hovermode="x",
                spikedistance=-1,
                xaxis=dict(
                    spikecolor="black",
                    spikethickness=1,
                    spikedash="solid",
                    spikemode="across",
                    spikesnap="cursor",
                    showspikes=True
                ),
            )

            def cleanup():
                for cnt in (title_widget, toolbar_widget, viewer_widget):
                    cnt.children = ()

                for wgt in (dotplot_view.toolbar, dotplot_view.figure_widget):
                    # wgt.layout.close()
                    wgt.close()

            return cleanup

        solara.use_effect(_add_viewer, dependencies=[])

    return main
