from typing import Callable, Optional

import plotly.express as px
import reacton.ipyvuetify as rv
import solara
from hubbleds.state import GalaxyData
from pandas import DataFrame
from hubbleds.components.spectrum_viewer.plotly_figure import FigurePlotly
from cosmicds.logger import setup_logger

from glue_plotly.common import DEFAULT_FONT

logger = setup_logger("SPECTRUM")


@solara.component
def SpectrumViewer(
    galaxy_data: GalaxyData | None,
    obs_wave: float | None = None,
    spectrum_click_enabled: bool = False,
    show_obs_wave_line: bool = True,
    on_obs_wave_measured: Callable = None,
    on_obs_wave_tool_clicked: Callable = lambda: None,
    on_zoom_tool_clicked: Callable = lambda: None,
    marker_position: Optional[solara.Reactive[float]] = None,
    on_set_marker_position: Callable = lambda x: None,
    spectrum_bounds: Optional[solara.Reactive[list[float]]] = None,
    on_spectrum_bounds_changed: Callable = lambda x: None,
    max_spectrum_bounds: Optional[solara.Reactive[list[float]]] = None,
):
    
    logger.info("\n\n ==================== \n SpectrumViewer \n ==================== \n\n")
    # spectrum_bounds
    vertical_line_visible = solara.use_reactive(show_obs_wave_line)
    toggle_group_state = solara.use_reactive([])

    x_bounds = solara.use_reactive([])
    y_bounds = solara.use_reactive([])
    # spectrum_bounds = solara.use_reactive(spectrum_bounds or [], on_change=lambda x: x_bounds.set(x))
    if spectrum_bounds is not None:
        spectrum_bounds.subscribe(x_bounds.set)
    
    use_dark_effective = solara.use_trait_observe(solara.lab.theme, "dark_effective")

    async def _load_spectrum():
        if galaxy_data is None:
            return False

        return galaxy_data.spectrum_as_data_frame

    spec_data_task = solara.lab.use_task(   # noqa: SH101 
        _load_spectrum,
        dependencies=[galaxy_data],
    )
    
    if spec_data_task.finished and spec_data_task.value is not False:
        spec = spec_data_task.value 
        logger.info('spec_data_task is finished')
        if (spec is not None) and (max_spectrum_bounds is not None):
            logger.info(f"\tSetting max_spectrum_bounds to {spec['wave'].min()} and {spec['wave'].max()}")
            max_spectrum_bounds.set([spec["wave"].min(), spec["wave"].max()])
    

    def _obs_wave_tool_toggled():
        on_obs_wave_tool_clicked()



    def _on_relayout(event):
        if event is None:
            return

        try:
            x_bounds.set(
                [
                    event["relayout_data"]["xaxis.range[0]"],
                    event["relayout_data"]["xaxis.range[1]"],
                ]
            )
            # y_bounds.set(
            #     [
            #         event["relayout_data"]["yaxis.range[0]"],
            #         event["relayout_data"]["yaxis.range[1]"],
            #     ]
            # )
            toggle_group_state.set([x for x in toggle_group_state.value if x != 0])
        except:
            x_bounds.set([])
            y_bounds.set([])
        
        if "relayout_data" in event:
            if "xaxis.range[0]" in event["relayout_data"] and "xaxis.range[1]" in event["relayout_data"]:
                if spectrum_bounds is not None:
                    spectrum_bounds.set([
                        event["relayout_data"]["xaxis.range[0]"],
                        event["relayout_data"]["xaxis.range[1]"],
                    ])

    def _on_reset_button_clicked(*args, **kwargs):
        x_bounds.set([])
        y_bounds.set([])
        try:
            if spec_data_task.value is not None and spectrum_bounds is not None:
                spectrum_bounds.set([
                    spec_data_task.value["wave"].min(),
                    spec_data_task.value["wave"].max(),
                ])
        except Exception as e:
            print(e)

    def _spectrum_clicked(**kwargs):
        if spectrum_click_enabled:
            vertical_line_visible.set(True)
            on_obs_wave_measured(round(kwargs["points"]["xs"][0]))
        if marker_position is not None:
            # vertical_line_visible.set(False)
            value = kwargs["points"]["xs"][0]
            marker_position.set(value)
            on_set_marker_position(value)
            

    with rv.Card():
        with rv.Toolbar(class_="toolbar", dense=True):
            with rv.ToolbarTitle():
                solara.Text("SPECTRUM VIEWER")

            rv.Spacer()

            with rv.BtnToggle(
                v_model=toggle_group_state.value,
                on_v_model=toggle_group_state.set,
                flat=True,
                tile=True,
                group=True,
                multiple=True,
            ):

                solara.IconButton(
                    icon_name="mdi-select-search",
                    on_click=on_zoom_tool_clicked,
                )

                solara.IconButton(
                    icon_name="mdi-lambda",
                    on_click=_obs_wave_tool_toggled,
                )

            rv.Divider(vertical=True)

            solara.IconButton(
                flat=True,
                tile=True,
                icon_name="mdi-cached",
                on_click=_on_reset_button_clicked,
            )

        if spec_data_task.value is None:
            with rv.Sheet(
                style_="height: 360px", class_="d-flex justify-center align-center"
            ):
                rv.ProgressCircular(size=100, indeterminate=True, color="primary")

            return
        elif not isinstance(spec_data_task.value, DataFrame):
            with rv.Sheet(
                style_="height: 360px", class_="d-flex justify-center align-center"
            ):
                solara.Text("Select a galaxy to view its spectrum")

            return
        
        if galaxy_data is None:
            logger.info('galaxy_data is None')
            return

        fig = px.line(spec_data_task.value, x="wave", y="flux", 
                    #   template = "plotly_dark" if use_dark_effective else "plotly_white",)
                    template = "plotly_white",
                    hover_data={"wave": True, "flux": False},
                    # line_shape="hvh", # step line plot
                    )
        fig.update_traces(hovertemplate='Wavelength: %{x:0.1f} Å') #
        fig.update_layout(
            hoverlabel=dict(
                font_size=16,
            ),
        )

        
        fig.update_layout(
            font_family=DEFAULT_FONT,
            title_font_family=DEFAULT_FONT,
            margin=dict(l=0, r=10, t=10, b=0), 
            yaxis=dict(
                fixedrange=True,
                title="Brightness",
                showgrid=False,
                showline=True,
                linewidth=1,
                mirror=True,
                title_font_family=DEFAULT_FONT, 
                titlefont_size=20, 
                tickfont_size=12
                ),
            xaxis=dict(
                title="Wavelength (Angstroms)",
                showgrid=False,
                showline=True,
                linewidth=1,
                mirror=True,
                title_font_family=DEFAULT_FONT, 
                titlefont_size=20, 
                tickfont_size=12
                ),
        )

        fig.add_vline(
            x=obs_wave,
            line_width=1,
            line_color="red",
            # annotation_text="1BASE",
            # annotation_font_size=12,
            # annotation_position="top right",
            visible=vertical_line_visible.value and obs_wave > 0.0 and spectrum_click_enabled,
        )
        fig.add_shape(
            type='line',
            x0=obs_wave,
            x1=obs_wave,
            y0=0.0,
            y1=0.2,
            xref="x",
            yref="paper",
            line_color="red",
            line_width=2,
            fillcolor="red",
            label={
                "text": f"Your measurement",
                "textposition": "top center",
                "yanchor": "bottom",
                "textangle": 0,
                "padding": 35,
            },
            visible=vertical_line_visible.value and obs_wave > 0.0  and not spectrum_click_enabled,
        )
        
        if (marker_position is not None) and (not spectrum_click_enabled):
            fig.add_vline(
                x = marker_position.value,
                line_width = 2,
                line_color = "green",
                visible = True,
            )
        

        fig.add_shape(
            editable=False,
            x0=galaxy_data.redshift_rest_wave_value - 5,
            x1=galaxy_data.redshift_rest_wave_value + 5,
            y0=0.85,
            y1=0.9,
            xref="x",
            line_color="red",
            fillcolor="red",
            ysizemode="scaled",
            yref="paper",
            label={
                "text": f"{galaxy_data.element} (observed)",
                "textposition": "top center",
                "yanchor": "bottom",
            },
            # visible=
        )

        fig.add_shape(
            editable=False,
            type="line",
            x0=galaxy_data.rest_wave_value,
            x1=galaxy_data.rest_wave_value,
            xref="x",
            y0=0.0,
            y1=1.0,
            line_color="black",
            ysizemode="scaled",
            yref="paper",
            line=dict(dash="dot"),
            label={
                "text": f"{galaxy_data.element} (rest)",
                "textposition": "top center",
                "yanchor": "bottom",
            },
            visible=1 in toggle_group_state.value,
        )

        fig.update_layout(
            xaxis_zeroline=False,
            yaxis_zeroline=False,
            xaxis=dict(
                showspikes=spectrum_click_enabled,
                # showline=spectrum_click_enabled,
                spikecolor="black",
                spikethickness=1,
                spikedash="solid",
                spikemode="across",
                spikesnap="cursor",
            ),
            spikedistance=-1,
            hovermode="x",
        )

        if x_bounds.value:  # and y_bounds.value:
            fig.update_xaxes(range=x_bounds.value)
            # fig.update_yaxes(range=y_bounds.value)
        # else:
        fig.update_yaxes(
            range=[
                spec_data_task.value["flux"].min() * 0.95,
                spec_data_task.value["flux"].max() * 1.25,
            ]
        )

        fig.update_layout(dragmode="zoom" if 0 in toggle_group_state.value else False)
        
        
        
        dependencies = [
            obs_wave,
            spectrum_click_enabled,
            vertical_line_visible.value,
            toggle_group_state.value,
            x_bounds.value,
            y_bounds.value,
            
        ]
        
        if marker_position is not None:
            dependencies.append(marker_position.value)
        
        FigurePlotly(
            fig,
            on_click=lambda kwargs: _spectrum_clicked(**kwargs),
            on_relayout=_on_relayout,
            dependencies=dependencies,
            config={
                "displayModeBar": False,
            },
        )


