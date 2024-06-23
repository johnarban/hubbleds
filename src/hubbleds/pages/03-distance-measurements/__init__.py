import solara
from cosmicds.widgets.table import Table
from cosmicds.components import ScaffoldAlert, StateEditor, MathJaxSupport, PlotlySupport
import astropy.units as u
from cosmicds import load_custom_vue_components
from glue_jupyter.app import JupyterApplication
from glue_jupyter.table import TableViewer
from reacton import component, ipyvuetify as rv
from pathlib import Path

from hubbleds.widgets.distance_tool.distance_tool import DistanceTool

from ...components import AngsizeDosDontsSlideshow, DataTable, DotplotViewer
from ...data_management import *
from ...utils import DISTANCE_CONSTANT, GALAXY_FOV, distance_from_angular_size, measurement_list_to_glue_data
from ...state import GLOBAL_STATE, LOCAL_STATE, mc_callback, mc_serialize_score
from ...widgets.selection_tool import SelectionTool
from ...data_models.student import student_data, StudentMeasurement, example_data, StudentData
from .component_state import ComponentState, Marker

from ...viewers.hubble_dotplot import HubbleDotPlotView, HubbleDotPlotViewer
from ...remote import DatabaseAPI
from cosmicds.components import ViewerLayout
from pandas import DataFrame
from numpy import asarray


GUIDELINE_ROOT = Path(__file__).parent / "guidelines"

from glue.core import Data
from typing import List, Optional, cast

component_state = ComponentState()

def _update_angular_size(data, galaxy, angular_size, count):
    if bool(galaxy) and angular_size is not None:
        arcsec_value = int(angular_size.to(u.arcsec).value)
        galaxy["angular_size"] = arcsec_value
        data.update(galaxy["id"], {"ang_size": arcsec_value, 'galaxy': galaxy})
        count.value += 1

def _update_distance_measurement(data, galaxy, theta):
    if bool(galaxy) and theta is not None:
        distance = distance_from_angular_size(theta)
        # galaxy = data.get_by_galaxy_id(galaxy["id"]).model_dump()
        galaxy["distance"] = distance
        data.update(galaxy["id"], {"est_dist": distance, 'galaxy': galaxy})


@solara.component
def DistanceToolComponent(galaxy, show_ruler, angular_size_callback, ruler_count_callback):
    tool = DistanceTool.element()

    def set_selected_galaxy():
        widget = solara.get_widget(tool)
        if galaxy:
            widget.measuring = False
            widget.go_to_location(galaxy["ra"], galaxy["decl"], fov=GALAXY_FOV)
        widget.measuring_allowed = bool(galaxy)

    solara.use_effect(set_selected_galaxy, [galaxy])

    def turn_ruler_on():
        widget = solara.get_widget(tool)
        widget.show_ruler = show_ruler

    solara.use_effect(turn_ruler_on, [show_ruler])

    def _define_callbacks():
        widget = solara.get_widget(tool)

        def update_angular_size(change):
            if widget.measuring:
                angle = change["new"]
                angular_size_callback(angle)

        widget.observe(update_angular_size, ["angular_size"])

        def get_ruler_click_count(change):
            count = change["new"]
            ruler_count_callback(count)

        widget.observe(get_ruler_click_count, ["ruler_click_count"])

    solara.use_effect(_define_callbacks, [])

@solara.component
def Page():
    def _load_db_state():
        # Load stored component state from database, measurement data is
        #   considered higher-level and is loaded when the story starts.
        DatabaseAPI.get_story_state(component_state)

    solara.use_thread(_load_db_state)
    
    # Mount external javascript libraries
    def _load_math_jax():
        MathJaxSupport()
        PlotlySupport()

    solara.use_memo(_load_math_jax, dependencies=[])
    
    # Custom vue-only components have to be registered in the Page element
    #  currently, otherwise they will not be available in the front-end
    load_custom_vue_components()

    # Solara's reactivity is often tied to the _context_ of the Page it's
    #  being rendered in. Currently, in order to trigger subscribed callbacks,
    #  state connections need to be initialized _inside_ a Page.
    component_state.setup()
    
    
    
    def glue_setup():
        gjapp = JupyterApplication(GLOBAL_STATE.data_collection, GLOBAL_STATE.session)
        
        # Get the example seed data
        if EXAMPLE_GALAXY_SEED_DATA not in gjapp.data_collection:
            example_seed_data = DatabaseAPI.get_example_seed_measurement()
            data = Data(label=EXAMPLE_GALAXY_SEED_DATA, **{k: asarray([r[k] for r in example_seed_data]) for k in example_seed_data[0].keys()})
            gjapp.data_collection.append(data)
        else:
            data = gjapp.data_collection[EXAMPLE_GALAXY_SEED_DATA]
        # cast is for type hinting purposes. It's not necessary for the code to run.
        v1  = cast(HubbleDotPlotViewer, gjapp.new_data_viewer(HubbleDotPlotView, data=data, show=False))
        v1.state.x_att = data.id[DB_ANGSIZE_FIELD] # ang_size_value
        v1.state.title = "Angular Size Measurements"
        v1.figure.update_xaxes(showline=True, mirror=False)
        v1.figure.update_yaxes(showline=True, mirror=False)
        
        v2  = cast(HubbleDotPlotViewer, gjapp.new_data_viewer(HubbleDotPlotView, data=data, show=False))
        v2.state.x_att = data.id[DB_DISTANCE_FIELD] # est_dist_value
        v2.state.title = "Distance Measurements"
        v2.figure.update_xaxes(showline=True, mirror=False)
        v2.figure.update_yaxes(showline=True, mirror=False)
        
        return gjapp, v1, v2
    
    gjapp, dotplot_angsize, dotplot_distance = solara.use_memo(glue_setup)
    

    mc_scoring, set_mc_scoring  = solara.use_state(LOCAL_STATE.mc_scoring.value)

    StateEditor(Marker, component_state) 
    # This will print the tables 
    # need to > from pandas import DataFrame
    def meas_to_df(meas):
        try:
            meas = meas.model_dump()
        except AttributeError:
            pass
        try:
            gal = meas.pop('galaxy')
        except:
            gal = {}
        # gal = gal.model_dump(exclude={'spectrum'})
        gal = {k:v for k,v in gal.items() if k != 'spectrum'}
        return {**gal, **meas}
    
    # solara.HTML(unsafe_innerHTML=DataFrame([meas_to_df(s) for s in student_data.measurements or []]).to_html())
    # solara.HTML(unsafe_innerHTML=DataFrame([meas_to_df(s) for s in example_data.measurements or []]).to_html())

    # if LOCAL_STATE.debug_mode:

        # def _on_select_galaxies_clicked():
        #     gal_tab = Table(component_state.galaxy_data)
        #     gal_tab["id"] = [str(x) for x in gal_tab["id"]]
        #     for i in range(5 - component_state.total_galaxies.value):
        #         gal = dict(gal_tab[i])
        #         _on_galaxy_selected(gal)

        #     component_state.transition_to(Marker.sel_gal3, force=True)

        # solara.Button("Select 5 Galaxies", on_click=_on_select_galaxies_clicked)

    with solara.ColumnsResponsive(12, large=[4,8]):
        with rv.Col():
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAngsizeMeas1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAngsizeMeas2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz2),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAngsizeMeas2b.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz2b),
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once measuring tool is implemented
                GUIDELINE_ROOT / "GuidelineAngsizeMeas3.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz3),
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once measuring tool is implemented
                GUIDELINE_ROOT / "GuidelineAngsizeMeas4.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz4),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAngsizeMeas5a.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz5a),
                state_view={
                    "dosdonts_tutorial_opened": component_state.dosdonts_tutorial_opened.value
                },
            )
            # This was skipped in voila version
            # ScaffoldAlert(
            #     GUIDELINE_ROOT / "GuidelineAngsizeMeas6.vue",
            #     event_next_callback=lambda *args: component_state.transition_next(),
            #     event_back_callback=lambda *args: component_state.transition_previous(),
            #     can_advance=component_state.can_transition(next=True),
            #     show=component_state.is_current_step(Marker.ang_siz6),
            # )
            
            # NOTE: We are skipping the 2nd measurement for now
            # So we want to skip forward to rep_rem1.
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq5.vue",
                # event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                event_next_callback=lambda *args: component_state.transition_to(Marker.rep_rem1), # 
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq5),
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once measuring tool is implemented
                GUIDELINE_ROOT / "GuidelineDotplotSeq5b.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq5b),
            )

        with rv.Col():
            def show_ruler_range(marker):
                component_state.show_ruler.value = Marker.is_between(marker, Marker.ang_siz3, Marker.est_dis4) or \
                Marker.is_between(marker, Marker.dot_seq5b, Marker.last())

            component_state.current_step.subscribe(show_ruler_range)

            @solara.lab.computed
            def on_example_galaxy_marker():
                return component_state.current_step_at_or_before(Marker.dot_seq7)


            @solara.lab.computed
            def current_galaxy():
                galaxy = component_state.selected_galaxy.value
                example_galaxy = component_state.selected_example_galaxy.value
                return example_galaxy if on_example_galaxy_marker.value else galaxy
            
            @solara.lab.computed
            def current_data():
                return example_data if on_example_galaxy_marker.value else student_data

            def _ang_size_cb(angle):
                """
                Callback for when the angular size is measured. This function
                updates the angular size of the galaxy in the data model and
                puts the measurements in the database.
                """
                data = current_data.value
                count = component_state.example_angular_sizes_total if on_example_galaxy_marker.value else component_state.angular_sizes_total
                _update_angular_size(data, current_galaxy.value, angle, count)
                DatabaseAPI.put_measurements(samples=on_example_galaxy_marker.value)
                if on_example_galaxy_marker.value:
                    value = int(angle.to(u.arcsec).value)
                    component_state.meas_theta.set(value)
                    component_state.n_meas.set(component_state.n_meas.value + 1)
            def _distance_cb(theta):
                """
                Callback for when the distance is estimated. This function
                updates the distance of the galaxy in the data model and
                puts the measurements in the database.
                """
                _update_distance_measurement(current_data.value, current_galaxy.value, theta)
                print('_distance_cb. example:', on_example_galaxy_marker.value)
                DatabaseAPI.put_measurements(samples=on_example_galaxy_marker.value)

            def _get_ruler_clicks_cb(count):
                component_state.ruler_click_count.set(count)

            DistanceToolComponent(
                galaxy=current_galaxy.value,
                show_ruler=component_state.show_ruler.value,
                angular_size_callback=_ang_size_cb,
                ruler_count_callback=_get_ruler_clicks_cb,
            )

            with rv.Col(cols=6, offset=3):
                if component_state.current_step_at_or_after(Marker.ang_siz5a):
                    AngsizeDosDontsSlideshow(
                        event_on_dialog_opened=lambda *args: component_state.dosdonts_tutorial_opened.set(
                            True
                        )
                    )

    with solara.ColumnsResponsive(12, large=[4,8]):
        with rv.Col():
            
            
            
            ScaffoldAlert(
                # TODO This will need to be wired up once table is implemented
                GUIDELINE_ROOT / "GuidelineChooseRow1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.cho_row1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAngsizeMeas5.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz5),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineEstimateDistance1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.est_dis1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineEstimateDistance2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.est_dis2),
                state_view={
                    "distance_const": DISTANCE_CONSTANT
                },
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once measuring tool is implemented
                GUIDELINE_ROOT / "GuidelineEstimateDistance3.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.est_dis3),
                event_set_distance=_distance_cb,
                state_view={
                    "distance_const": DISTANCE_CONSTANT,
                    "meas_theta": component_state.meas_theta.value,
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineEstimateDistance4.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.est_dis4),
                state_view={
                    "distance_const": DISTANCE_CONSTANT,
                    "meas_theta": component_state.meas_theta.value,
                },
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once table is implemented
                GUIDELINE_ROOT / "GuidelineDotplotSeq5a.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq5a),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq5c.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq5c),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineRepeatRemainingGalaxies.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_to(Marker.dot_seq5),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.rep_rem1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineFillRemainingGalaxies.vue",
                # event_next_callback should go to next stage but I don't know how to set that up.
                event_back_callback=lambda *args: component_state.transition_previous(),
                show=component_state.is_current_step(Marker.fil_rem1),
            )

        with rv.Col():
            with rv.Card(class_="pa-0 ma-0", elevation=0):
                
                def fill_galaxy_distances(dataset: StudentData):
                    print('Filling galaxy distances')
                    if dataset.measurements:
                        print('There are measurements')
                        count = 0
                        has_ang_size = all(measurement.ang_size is not None for measurement in dataset.measurements)
                        if not has_ang_size:
                            print("\n ======= Not all galaxies have angular sizes ======= \n")
                        for measurement in dataset.measurements:
                            if measurement.galaxy is not None:
                                count += 1
                                _update_distance_measurement(student_data, measurement.galaxy.model_dump(), measurement.ang_size)
                        print(f"Filled {count} distances")
                        DatabaseAPI.put_measurements(samples=False)
                        print(f"Filled {count} distances")
                    else:
                        print("No measurements to fill")
                        raise ValueError("No measurements to fill")

                
                if component_state.current_step_at_or_after(Marker.fil_rem1):
                    solara.Button("Fill Galaxy Distances", on_click=lambda *args: fill_galaxy_distances(student_data))
                    

                common_headers = [
                    {
                        "text": "Galaxy Name",
                        "align": "start",
                        "sortable": False,
                        "value": "name"
                    },
                    { "text": "&theta; (arcsec)", "value": "ang_size" },
                    { "text": "Distance (Mpc)", "value": "est_dist" },
                ]
            
            if component_state.current_step_at_or_before(Marker.dot_seq7):
                def update_example_galaxy(galaxy):
                    flag = galaxy.get("value", True)
                    value = galaxy["item"]["galaxy"] if flag else None
                    component_state.selected_example_galaxy.set(value)

                @solara.lab.computed
                def example_table_kwargs():
                    ang_size_tot = component_state.example_angular_sizes_total.value
                    tab = example_data.dict(exclude={'measurements': {'__all__': 'spectrum'}})["measurements"]
                    for i, row in enumerate(tab):
                        row["measurement_number"] = example_data.model_dump()["measurements"][i]["galaxy"]["measurement_number"]
                    return {
                        "title": "Example Galaxy",
                        "headers": common_headers, # + [{ "text": "Measurement Number", "value": "measurement_number" }], # we will be skipping the 2nd measurement for now
                        "items": tab,
                        "highlighted": False,  # TODO: Set the markers for this,
                        "event_on_row_selected": update_example_galaxy
                    }

                DataTable(**example_table_kwargs.value)

            else:
                def update_galaxy(galaxy):
                    flag = galaxy.get("value", True)
                    value = galaxy["item"]["galaxy"] if flag else None
                    component_state.selected_galaxy.set(value)

                @solara.lab.computed
                def table_kwargs():
                    ang_size_tot = component_state.angular_sizes_total.value
                    return {
                        "title": "My Galaxies",
                        "headers": common_headers + [{ "text": "Measurement Number", "value": "measurement_number" }],
                        "items": student_data.dict(exclude={'measurements': {'__all__': 'spectrum'}})["measurements"],
                        "highlighted": False,  # TODO: Set the markers for this,
                        "event_on_row_selected": update_galaxy
                    }

                DataTable(**table_kwargs.value)

    with solara.ColumnsResponsive(12, large=[4,8]):
        with rv.Col():
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq2),
                event_mc_callback=lambda event: mc_callback(event = event, local_state = LOCAL_STATE, callback=set_mc_scoring),
                state_view={'mc_score': mc_serialize_score(mc_scoring.get('ang_meas_consensus')), 'score_tag': 'ang_meas_consensus'}
            )            
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq3.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq3),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq4.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq4),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq4a.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq4a),
                event_mc_callback=lambda event: mc_callback(event = event, local_state = LOCAL_STATE, callback=set_mc_scoring),
                state_view={'mc_score': mc_serialize_score(mc_scoring.get('ang_meas_dist_relation')), 'score_tag': 'ang_meas_dist_relation'}
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq6.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq6),
                event_mc_callback=lambda event: mc_callback(event = event, local_state = LOCAL_STATE, callback=set_mc_scoring),
                state_view={'mc_score': mc_serialize_score(mc_scoring.get('ang_meas_consensus_2')), 'score_tag': 'ang_meas_consensus_2'}
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq7.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq7),
            )

        with rv.Col():
            
            with rv.Card(class_="pa-0 ma-0", elevation=0):
                
                
                def add_link(from_dc_name, from_att, to_dc_name, to_att):
                    if isinstance(from_dc_name, Data):
                        from_dc = from_dc_name
                    else:
                        from_dc = gjapp.data_collection[from_dc_name]
                    
                    if isinstance(to_dc_name, Data):
                        to_dc = to_dc_name
                    else:
                        to_dc = gjapp.data_collection[to_dc_name]
                    gjapp.add_link(from_dc, from_att, to_dc, to_att)

                
                def add_student_measurement():
                    if example_data.measurements:
                        example_data_glue = measurement_list_to_glue_data(example_data.measurements, label=EXAMPLE_GALAXY_MEASUREMENTS)
                        example_data_glue.style.color = "red"
                        gjapp.data_collection.append(example_data_glue)
                        egsd = gjapp.data_collection[EXAMPLE_GALAXY_SEED_DATA]
                        add_link(egsd, DB_ANGSIZE_FIELD, example_data_glue,"ang_size")
                        add_link(egsd, DB_DISTANCE_FIELD, example_data_glue,"est_dist")
                        dotplot_angsize.add_data(example_data_glue)
                        dotplot_distance.add_data(example_data_glue)
                
                # if component_state.current_step_at_or_after(Marker.dot_seq5):
                solara.Button("Add Example Data", on_click=add_student_measurement)
            solara.Markdown("blah blah")

                
                ViewerLayout(dotplot_angsize)
                ViewerLayout(dotplot_distance)

            
            