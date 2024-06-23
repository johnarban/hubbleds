import numpy as np
import solara
from cosmicds.widgets.table import Table
from cosmicds.components import ScaffoldAlert, ViewerLayout
from cosmicds import load_custom_vue_components
from glue_jupyter.app import JupyterApplication
from reacton import ipyvuetify as rv
from pathlib import Path
from astropy.table import Table
import time
from cosmicds.components import MathJaxSupport, PlotlySupport, StateEditor

from hubbleds.components.dotplot_tutorial_slideshow import DotplotTutorialSlideshow

from ...components import (
    DataTable,
    SpectrumViewer,
    SpectrumSlideshow,
    DopplerSlideshow,
    ReflectVelocitySlideshow,
    DotplotViewer,
)

from ...state import GLOBAL_STATE, LOCAL_STATE
from ...widgets.selection_tool import SelectionTool
from ...data_models.student import student_data, StudentMeasurement, example_data
from .component_state import ComponentState, Marker, ELEMENT_REST
from ...remote import DatabaseAPI
from ...data_management import EXAMPLE_GALAXY_SEED_DATA, DB_VELOCITY_FIELD
from glue.core import Data

GUIDELINE_ROOT = Path(__file__).parent / "guidelines"

component_state = ComponentState()


def _on_galaxy_selected(galaxy):
    is_in = np.isin(
        [x.galaxy.name for x in student_data.measurements], galaxy["name"]
    )  # Avoid duplicates
    already_present = is_in.size > 0 and is_in[0]

    if not already_present:
        galaxy["spectrum"] = component_state._load_spectrum_data(galaxy)
        student_data.measurements.append(
            StudentMeasurement(
                **{
                    "rest_wave": round(ELEMENT_REST[galaxy["element"]]),
                    "galaxy": galaxy,
                }
            )
        )
        component_state.total_galaxies.value += 1
        component_state.selected_galaxies.set(
            [*component_state.selected_galaxies.value, galaxy["id"]]
        )
        DatabaseAPI.put_measurements()


def _on_example_galaxy_table_row_selected(row):
    measurement = example_data.get_by_galaxy_id(row["item"]["galaxy"]["id"])
    component_state.selected_example_galaxy.set(measurement["galaxy"]["id"])
    component_state.lambda_rest.set(measurement["rest_wave"])
    component_state.lambda_obs.set(0.0)
    component_state.student_vel.set(0.0)


def _on_galaxy_table_row_selected(row):
    measurement = student_data.get_by_galaxy_id(
        row["item"]["galaxy"]["id"], exclude={"spectrum"}
    )
    component_state.selected_galaxy.set(measurement["galaxy"]["id"])
    component_state.lambda_rest.set(measurement["rest_wave"])
    component_state.lambda_obs.set(0.0)
    component_state.student_vel.set(0.0)


def _on_wavelength_measured(value, update_example=False, update_student=False):
    if update_example:
        example_data.update(
            component_state.selected_example_galaxy.value, {"obs_wave": value}
        )
        component_state.lambda_obs.set(value)
        DatabaseAPI.put_measurements(samples=True)
    elif update_student:
        student_data.update(component_state.selected_galaxy.value, {"obs_wave": value})
        component_state.lambda_obs.set(value)
        component_state.obswaves_total.value += 1
        DatabaseAPI.put_measurements()


def _on_velocity_calculated(value, update_example=False, update_student=False):
    if update_example:
        example_data.update(
            component_state.selected_example_galaxy.value, {"velocity": round(value)}
        )
        component_state.student_vel.set(round(value))
        DatabaseAPI.put_measurements(samples=True)
    elif update_student:
        student_data.update(
            component_state.selected_galaxy.value, {"velocity": round(value)}
        )
        component_state.student_vel.set(round(value))
        DatabaseAPI.put_measurements()


def _calculate_velocity(*args, **kwargs):
    for gal_id in component_state.selected_galaxies.value:
        measurement = student_data.get_by_galaxy_id(gal_id, exclude={"spectrum"})
        rest_wave = measurement["rest_wave"]
        obs_wave = measurement["obs_wave"]
        velocity = round((3 * (10**5) * (obs_wave / rest_wave - 1)), 0)
        student_data.update(measurement["galaxy"]["id"], {"velocity": velocity})
        component_state.velocities_total.value += 1
        DatabaseAPI.put_measurements()


def transition_to_next_stage():
    route, routes = solara.use_route()
    _, set_location_path = solara.use_pathname()
    index = routes.index(route)
    set_location_path(solara.resolve_path(routes[index + 1]))


@solara.lab.computed
def selected_galaxy_measurement():
    return student_data.get_by_galaxy_id(
        component_state.selected_galaxy.value,
        # exclude={"galaxy": {"spectrum"}},
    )


@solara.lab.computed
def selected_example_galaxy_measurement():
    return example_data.get_by_galaxy_id(
        component_state.selected_example_galaxy.value,
        # exclude={"galaxy": {"spectrum"}},
    )


@solara.lab.computed
def table_data():
    vel_tot = component_state.velocities_total.value

    is_example_data = (
        Marker.cho_row1.value
        <= component_state.current_step.value.value
        < Marker.rem_gal1.value
    )

    tab_data = student_data.get_measurements(is_example=is_example_data)

    return tab_data


@solara.lab.computed
def spec_data():
    print("Getting spec data...")

    # TODO: find a way to get rid of this; it's the same as below to show/hide
    #  the spectrum viewer and tutorial, shouldn't need it twice...
    show_example_galaxy_spec = (
        (component_state.current_step.value.value >= Marker.mee_spe1.value)
        and (component_state.current_step.value.value < Marker.int_dot1.value)
    ) or (
        Marker.dot_seq4.value
        <= component_state.current_step.value.value
        < Marker.rem_gal1.value
    )

    show_galaxy_spec = component_state.current_step.value.value >= Marker.rem_gal1.value

    if show_example_galaxy_spec and selected_example_galaxy_measurement.value:
        data = selected_example_galaxy_measurement.value["galaxy"]["spectrum"]
    elif show_galaxy_spec and selected_galaxy_measurement.value:
        data = selected_galaxy_measurement.value["galaxy"]["spectrum"]
    else:
        data = {}

    return Table(
        {
            "wave": data.get("wave", []),
            "flux": data.get("flux", []),
        }
    ).to_pandas()


@solara.component
def Page():
    def _load_db_state():
        # Load stored component state from database, measurement data is
        #   considered higher-level and is loaded when the story starts.
        DatabaseAPI.get_story_state(component_state)

    solara.use_thread(_load_db_state)

    # TODO: This should not be here! This should be loaded in the top-level
    #  layout. However, some very recent change causes the top-level memo
    #  to not actually load. Seems to be something with the threading.
    def _load_math_jax():
        MathJaxSupport()
        PlotlySupport()

    solara.use_memo(_load_math_jax, dependencies=[])

    def _component_setup():
        # Solara's reactivity is often tied to the _context_ of the Page it's
        #  being rendered in. Currently, in order to trigger subscribed
        #  callbacks, state connections need to be initialized _inside_ a Page.
        component_state.setup()

        # Custom vue-only components have to be registered in the Page element
        #  currently, otherwise they will not be available in the front-end
        load_custom_vue_components()

        # Setup database write listeners. TODO: put writers into a separate
        #  thread so they are never blocking the render.
        GLOBAL_STATE._setup_database_write_listener(
            lambda: DatabaseAPI.put_story_state(component_state)
        )
        LOCAL_STATE._setup_database_write_listener(
            lambda: DatabaseAPI.put_story_state(component_state)
        )
        component_state._setup_database_write_listener(
            lambda: DatabaseAPI.put_story_state(component_state)
        )

    solara.use_memo(_component_setup)

    # NOTE: use_memo has to be part of the main page render. Including it in
    #  a conditional will result in an error.
    def glue_setup():
        gjapp = JupyterApplication(GLOBAL_STATE.data_collection, GLOBAL_STATE.session)
        # Get the example seed data
        if EXAMPLE_GALAXY_SEED_DATA not in gjapp.data_collection:
            example_seed_data = DatabaseAPI.get_example_seed_measurement()
            data = Data(label=EXAMPLE_GALAXY_SEED_DATA, **{k: np.asarray([r[k] for r in example_seed_data]) for k in example_seed_data[0].keys()})
            gjapp.data_collection.append(data)
        else:
            data = gjapp.data_collection[EXAMPLE_GALAXY_SEED_DATA]
        return gjapp

    gjapp = solara.use_memo(glue_setup)

    # solara.Text(
    #     f"Current step: {component_state.current_step.value} <|> "
    #     f"Next step: {Marker(component_state.current_step.value.value + 1)} <|> "
    #     f"Can advance: {component_state.can_transition(next=True)} <|> "
    #     f"Can regress: {component_state.can_transition(prev=True)} <|> "
    #     f"Student vel: {component_state.student_vel.value}"
    # )
    StateEditor(Marker, component_state=component_state)
    
    if LOCAL_STATE.debug_mode:

        def _on_select_galaxies_clicked():
            gal_tab = Table(component_state.galaxy_data)
            gal_tab["id"] = [str(x) for x in gal_tab["id"]]

            for i in range(5 - component_state.total_galaxies.value):
                gal = dict(gal_tab[i])
                _on_galaxy_selected(gal)

            component_state.transition_to(Marker.sel_gal3, force=True)

        with solara.Row():
            solara.Button("Select 5 Galaxies", on_click=_on_select_galaxies_clicked)

        def _load_state():
            DatabaseAPI.get_story_state(component_state)

        def _write_state():
            DatabaseAPI.put_story_state(component_state)
            DatabaseAPI.put_measurements()

        def _delete_measurements():
            DatabaseAPI.delete_all_measurements()
            DatabaseAPI.delete_all_measurements(samples=True)

        # solara.Text(f"{component_state.as_dict()}")

        with solara.Row():
            solara.Button("Load State", on_click=_load_state)
            solara.Button("Write State", on_click=_write_state)
            solara.Button("Delete Measurements", on_click=_delete_measurements)

    # Flag to show/hide the selection tool. TODO: we shouldn't need to be
    #  doing this here; revisit in the future and implement proper handling
    #  in the ipywwt package itself.
    show_selection_tool, set_show_selection_tool = solara.use_state(False)

    def _delay_selection_tool():
        time.sleep(2)
        set_show_selection_tool(True)

    solara.use_thread(_delay_selection_tool)

    with rv.Row():
        with rv.Col(cols=4):
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineIntro.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.mee_gui1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineSelectGalaxies1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.sel_gal1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineSelectGalaxies2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.sel_gal2),
                state_view={
                    "total_galaxies": component_state.total_galaxies.value,
                    "selected_galaxy": bool(component_state.selected_galaxy.value),
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineSelectGalaxies3.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.sel_gal3),
                state_view={
                    "total_galaxies": component_state.total_galaxies.value,
                    "selected_galaxy": bool(component_state.selected_galaxy.value),
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineSelectGalaxies4.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.sel_gal4),
            )

        with rv.Col(cols=8):
            # TODO: for some reason, if a component using `element` takes too
            #  long to load, it'll be inserted at the end of the page render.
            #  Wrapping in a card seems to alleviate this.
            with rv.Card(class_="pa-0 ma-0", elevation=0):
                selection_tool = SelectionTool.element(
                    table_layer_data=component_state.galaxy_data
                )

            def _define_selection_tool_callbacks():
                """Store a galaxy that has been clicked in the selection tool"""
                selection_tool_widget = solara.get_widget(selection_tool)
                selection_tool_widget.on_galaxy_selected = (
                    lambda gal: _on_galaxy_selected(gal)
                )
                selection_tool_widget.observe(
                    lambda v: component_state.selected_galaxy.set(v["new"].get("id")),
                    ["current_galaxy"],
                )

            def _update_selection_tool():
                """Whenever the step changes, check to see if we need to update
                the highlighting or show/hide the green dots."""
                selection_tool_widget = solara.get_widget(selection_tool)
                focus_view = component_state.is_current_step(
                    Marker.sel_gal2
                ) or component_state.is_current_step(Marker.sel_gal3)

                selection_tool_widget.show_galaxies(focus_view)

                if focus_view:
                    selection_tool_widget.center_on_start_coordinates()

                selection_tool_widget.highlighted = focus_view

            def _update_selected_position():
                """
                When a data table row is selected, move to galaxy location.
                """
                if selected_galaxy_measurement.value:
                    selection_tool_widget = solara.get_widget(selection_tool)
                    measurement = selected_galaxy_measurement.value

                    if measurement is not None:
                        selection_tool_widget.go_to_location(
                            measurement["galaxy"]["ra"], measurement["galaxy"]["decl"]
                        )

            def _update_example_selected_position():
                """
                When an example data table row is selected, move to galaxy
                location.
                """
                if selected_example_galaxy_measurement.value:
                    selection_tool_widget = solara.get_widget(selection_tool)
                    measurement = selected_example_galaxy_measurement.value

                    if measurement is not None:
                        selection_tool_widget.go_to_location(
                            measurement["galaxy"]["ra"], measurement["galaxy"]["decl"]
                        )

            solara.use_effect(_define_selection_tool_callbacks)
            solara.use_effect(
                _update_selection_tool,
                [component_state.current_step.value, show_selection_tool],
            )
            solara.use_effect(
                _update_selected_position, [component_state.selected_galaxy.value]
            )
            solara.use_effect(
                _update_example_selected_position,
                [component_state.selected_example_galaxy.value],
            )

    with rv.Row():
        with rv.Col(cols=4):
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineNoticeGalaxyTable.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.not_gal_tab),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineChooseRow.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.cho_row1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDopplerCalc4.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dop_cal4)
                or component_state.is_current_step(Marker.dop_cal5),
                state_view={
                    "lambda_obs": component_state.lambda_obs.value,
                    "lambda_rest": component_state.lambda_rest.value,
                    "failed_validation_4": component_state.doppler_calc_state.failed_validation_4.value,
                },
                event_failed_validation_4_callback=lambda v: component_state.doppler_calc_state.failed_validation_4.set(
                    v
                ),
                event_show_doppler_slideshow=lambda v: component_state.doppler_calc_dialog.set(
                    v
                ),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineCheckMeasurement.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.che_mea1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence12.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq12),
                event_remeasure_example_galaxy=lambda *args: component_state.transition_to(
                    Marker.dot_seq13, force=True
                ),
                event_continue_to_galaxies=lambda *args: component_state.transition_to(
                    Marker.rem_gal1, force=True
                ),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence13.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq13),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineRemainingGals.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.rem_gal1),
                state_view={
                    "obswaves_total": component_state.obswaves_total.value,
                    "has_bad_velocities": component_state.has_bad_velocities.value,
                    "has_multiple_bad_velocities": component_state.has_multiple_bad_velocities.value,
                    "selected_galaxy": selected_galaxy_measurement.value,
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDopplerCalc6.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dop_cal6),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineReflectVelValues.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ref_vel1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineEndStage1.vue",
                event_next_callback=transition_to_next_stage,
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.end_sta1),
                state_view={
                    "has_bad_velocities": component_state.has_bad_velocities.value,
                    "has_multiple_bad_velocities": component_state.has_multiple_bad_velocities.value,
                },
            )

        with rv.Col(cols=8):
            show_example_data_table = (
                Marker.cho_row1.value
                <= component_state.current_step.value.value
                < Marker.rem_gal1.value
            )

            @solara.lab.computed
            def data_table_kwargs():
                # Computed values are recomputed when a reactive variables
                #  inside them changes. We use the `velocities_total` variable
                #  to track when certain events should trigger changes in the
                #  frontend.
                vel_tot = component_state.velocities_total.value

                if show_example_data_table:
                    tab_data = example_data.dict(
                        exclude={"measurements": {"__all__": {"galaxy": {"spectrum"}}}}
                    )["measurements"]

                    tab_kwargs = {
                        "title": "Example Galaxy",
                        "highlighted": component_state.is_current_step(Marker.cho_row1),
                        "items": tab_data,
                        "event_on_row_selected": _on_example_galaxy_table_row_selected,
                    }
                else:
                    tab_data = student_data.dict(
                        exclude={"measurements": {"__all__": {"galaxy": {"spectrum"}}}}
                    )["measurements"]

                    tab_kwargs = {
                        "title": "My Galaxies",
                        "highlighted": component_state.is_current_step(
                            Marker.not_gal_tab
                        ),
                        "items": tab_data,
                        "event_on_row_selected": _on_galaxy_table_row_selected,
                        "show_velocity_button": component_state.is_current_step(
                            Marker.dop_cal6
                        ),
                        "event_calculate_velocity": _calculate_velocity,
                    }

                return tab_kwargs

            DataTable(**data_table_kwargs.value)

    with rv.Row():
        with rv.Col(cols=4):
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineIntroDotplot.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.int_dot1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence01.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence02.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq2),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence03.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq3),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence05.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq5),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence06.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq6),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence07.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq7),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence08.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq8),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence09.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq9),
            )

        with rv.Col(cols=8):
            if (component_state.current_step.value.value >= Marker.mee_spe1.value) and (
                component_state.current_step.value.value < Marker.int_dot1.value
            ):

                def _set_student_c(light_speed):
                    component_state.doppler_calc_state.student_c.set(light_speed)
                    _on_velocity_calculated(
                        component_state.doppler_calc_state.student_c.value
                        * (
                            component_state.lambda_obs.value
                            / component_state.lambda_rest.value
                            - 1
                        ),
                        update_example=True,
                    )

                DopplerSlideshow(
                    dialog=component_state.doppler_calc_dialog.value,
                    titles=component_state.doppler_calc_state.titles.value,
                    step=component_state.doppler_calc_state.step.value,
                    length=component_state.doppler_calc_state.length.value,
                    lambda_obs=component_state.lambda_obs.value,
                    lambda_rest=component_state.lambda_rest.value,
                    max_step_completed_5=component_state.doppler_calc_state.max_step_completed_5.value,
                    failed_validation_5=component_state.doppler_calc_state.failed_validation_5.value,
                    interact_steps_5=component_state.doppler_calc_state.interact_steps_5.value,
                    student_vel=component_state.student_vel.value,
                    student_c=component_state.doppler_calc_state.student_c.value,
                    event_set_dialog=lambda v: component_state.doppler_calc_dialog.set(
                        v
                    ),
                    event_set_step=lambda v: component_state.doppler_calc_state.step.set(
                        v
                    ),
                    event_set_failed_validation_5=lambda v: component_state.doppler_calc_state.failed_validation_5.set(
                        v
                    ),
                    event_set_max_step_completed_5=lambda v: component_state.doppler_calc_state.max_step_completed_5.set(
                        v
                    ),
                    event_set_student_vel_calc=lambda *args: component_state.doppler_calc_state.student_vel_calc.set(
                        True
                    ),
                    event_set_student_c=_set_student_c,
                    event_next_callback=lambda *args: component_state.transition_next(),
                )

            if (component_state.current_step.value.value >= Marker.int_dot1.value) and (
                component_state.current_step.value.value < Marker.rem_gal1.value
            ):
                DotplotTutorialSlideshow(
                    dialog=component_state.dotplot_tutorial_dialog.value,
                    step=component_state.dotplot_tutorial_state.step.value,
                    length=component_state.dotplot_tutorial_state.length.value,
                    max_step_completed=component_state.dotplot_tutorial_state.max_step_completed.value,
                    dotplot_viewer=DotplotViewer(gjapp),
                    event_tutorial_finished=lambda *args: component_state.dotplot_tutorial_finished.set(
                        True
                    ),
                )

                DotplotViewer(gjapp, data=gjapp.data_collection[EXAMPLE_GALAXY_SEED_DATA], component_id=DB_VELOCITY_FIELD)

            if component_state.is_current_step(Marker.ref_dat1):
                ReflectVelocitySlideshow(
                    reflection_complete=component_state.reflection_complete.value,
                    event_on_reflection_completed=lambda *args: component_state.reflection_complete.set(
                        True
                    ),
                )

    with rv.Row():
        with rv.Col(cols=4):
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineSpectrum.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.mee_spe1),
                state_view={
                    "spectrum_tutorial_opened": component_state.spectrum_tutorial_opened.value
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineRestwave.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.res_wav1),
                state_view={
                    "selected_example_galaxy": selected_example_galaxy_measurement.value,
                    "lambda_on": component_state.lambda_on.value,
                    "lambda_used": component_state.lambda_used.value,
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineObswave1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.obs_wav1),
                state_view={
                    "selected_example_galaxy": selected_galaxy_measurement.value,
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineObswave2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.obs_wav2),
                state_view={
                    "selected_example_galaxy": selected_galaxy_measurement.value,
                    "zoom_tool_activate": component_state.zoom_tool_activated.value,
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDopplerCalc0.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dop_cal0),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDopplerCalc2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dop_cal2),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence04.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq4),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence10.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq10),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence11.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq11),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineReflectOnData.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ref_dat1),
            )

        with rv.Col(cols=8):
            show_example_galaxy_spec = (
                (component_state.current_step.value.value >= Marker.mee_spe1.value)
                and (component_state.current_step.value.value < Marker.int_dot1.value)
            ) or (
                Marker.dot_seq4.value
                <= component_state.current_step.value.value
                < Marker.rem_gal1.value
            )

            show_galaxy_spec = (
                component_state.current_step.value.value >= Marker.rem_gal1.value
            )

            if show_example_galaxy_spec or show_galaxy_spec:
                with solara.Column():
                    SpectrumViewer(
                        spec_data,
                        lambda_obs=component_state.lambda_obs,
                        spectrum_click_enabled=component_state.current_step.value.value
                        >= Marker.obs_wav1.value,
                        on_wavelength_measured=lambda v: _on_wavelength_measured(
                            v,
                            update_example=show_example_galaxy_spec,
                            update_student=show_galaxy_spec,
                        ),
                        on_lambda_clicked=lambda: component_state.lambda_used.set(True),
                        on_zoom_clicked=lambda: component_state.zoom_tool_activated.set(
                            True
                        ),
                        on_spectrum_clicked=lambda: component_state.spectrum_clicked.set(
                            True
                        ),
                    )

                    SpectrumSlideshow(
                        event_on_dialog_opened=lambda *args: component_state.spectrum_tutorial_opened.set(
                            True
                        )
                    )
