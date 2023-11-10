from functools import partial
from glue.core.subset import RangeSubsetState

from numpy import where
# from cosmicds.components.layer_toggle import LayerToggle
from cosmicds.components import PercentageSelector, StatisticsSelector, Table 
from cosmicds.phases import CDSState
from cosmicds.registries import register_stage
from cosmicds.utils import extend_tool, load_template, update_figure_css
from echo import CallbackProperty, DictCallbackProperty, add_callback, callback_property, ListCallbackProperty, delay_callback
from glue.core.message import NumericalDataChangedMessage
from glue_jupyter.link import link
from hubbleds.components.id_slider import IDSlider
from hubbleds.utils import IMAGE_BASE_URL, AGE_CONSTANT
from traitlets import default, Bool
from ..data.styles import load_style

from ..data_management import *
from ..histogram_listener import HistogramListener
from ..stage import HubbleStage
from ..viewers import HubbleScatterView
from ..viewers.viewers import \
    HubbleClassHistogramView, HubbleHistogramView

demo = True
class StageState(CDSState):
    relage_response = CallbackProperty(False)
    two_hist_response = CallbackProperty(False)
    two_hist3_response = CallbackProperty(False)
    two_hist3a_response = CallbackProperty(False)
    # two_hist4_response = CallbackProperty(False)
    lack_bias_response = CallbackProperty(False)
    uncertainty_hint_dialog = CallbackProperty(False)
    class_trend_line_drawn = CallbackProperty(False)
    class_best_fit_clicked = CallbackProperty(False)
    
    stage_5_complete = CallbackProperty(False)
    
    uncertainty_dialog = CallbackProperty(False)
    uncertainty_dialog_opened = CallbackProperty(False)
    uncertainty_dialog_complete = CallbackProperty(False)
    uncertainty_state = DictCallbackProperty({
        'step': 0,
        'length': 10,
        'titles': [
            'What is the true age of the universe?',
            "Shortcomings in our measurements",
            "Shortcomings in our measurements",
            "Messiness in our distance measurements",
            "Uncertainty",            
            "Random Uncertainty (Noise)",
            "Systematic Uncertainty (Bias)",
            "Causes of Systematic Uncertainty",
            "Systematic Uncertainty",
            "Finished Uncertainty Tutorial",
        ]
    })
    
    define_outlier = CallbackProperty(False)
    
    mmm_dialog = CallbackProperty(False)
    mmm_dialog_opened = CallbackProperty(False)
    mmm_dialog_complete = CallbackProperty(False)
    mmm_state = DictCallbackProperty({
        'step': 0,
        'length': 3,
        'titles': [
            'Mean',
            "Median",
            "Mode"
        ]
    })

    marker = CallbackProperty("")
    indices = CallbackProperty({})
    advance_marker = CallbackProperty(True)

    image_location = CallbackProperty(f"{IMAGE_BASE_URL}/mean_median_mode") 
    class_data_size = CallbackProperty(0)

    hypgal_distance = CallbackProperty(0)
    hypgal_velocity = CallbackProperty(0)

    stu_low_age = CallbackProperty(0)
    stu_high_age = CallbackProperty(0)

    cla_low_age = CallbackProperty(0)
    cla_high_age = CallbackProperty(0)

    age_calc_state = DictCallbackProperty({
        'hint1_dialog': False,
        'hint2_dialog': False,
        'hint3_dialog': False,
        'best_guess': '',
        'low_guess': '',
        'high_guess': '',
        'short_one': '',
        'short_two': '',
        'short_other': ''
    })

    markers = CallbackProperty([
        'ran_var1',
        'cla_res1',
        'rel_age1',
        'cla_age1',
        'cla_age2',
        'cla_age3',
        'cla_age4',
        'lea_unc1',
        'mos_lik1', 
        'age_dis1',
        'mos_lik2',
        'mos_lik3',
        'mos_lik4',
        'con_int1',
        'con_int2',
        'con_int3',

        'cla_dat1',
        'tre_lin2c',
        'bes_fit1c',
        'you_age1c',
        'cla_res1c',
        'cla_age1c',
        'age_dis1c',
        'con_int2c',
        
        'two_his1',
        'two_his2',
        'two_his3',
        'two_his3a',
        # 'two_his4', cutting because it's too long redundant
        'two_his5',
        #'lac_bia1',
        #'lac_bia2',
        #'lac_bia3',
        'mor_dat1',
        #'acc_unc1',
        
    ])
    
    demo_markers = ListCallbackProperty(['cla_res1','age_dis1', 'con_int1', 'cla_res1c','two_his1', 'acc_unc1'])

    step_markers = ListCallbackProperty([])

    # step_markers = CallbackProperty([
    #     'ran_var1',
    #     'tre_lin2c',
    #     'two_his1',
    # ])

    table_highlights = CallbackProperty([
        'exp_dat1',
    ])
    
    my_galaxies_plot_highlights = CallbackProperty([
    ])

    all_galaxies_plot_highlights = CallbackProperty([
    ])

    my_class_hist_highlights = CallbackProperty([
    ])

    all_classes_hist_highlights = CallbackProperty([
    ])


    _NONSERIALIZED_PROPERTIES = [
        'markers', 'indices', #'step_markers',
        'marker_forward', 'marker_backward',
        'table_highlights', 'image_location',
        'my_galaxies_plot_highlights', 'all_galaxies_plot_highlights',
        'my_class_hist_highlights', 'all_classes_hist_highlights',
        'demo_markers',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.marker_index = 0
        self.marker = self.markers[0]
        self.indices = {marker: idx for idx, marker in enumerate(self.markers)}

    @callback_property
    def marker_forward(self):
        return None

    @callback_property
    def marker_backward(self):
        return None
    
    @marker_backward.setter
    def marker_backward(self, value):
        index = self.indices[self.marker]
        new_index = min(max(index - value, 0), len(self.markers) - 1)
        self.marker = self.markers[new_index]

    @marker_forward.setter
    def marker_forward(self, value):
        index = self.indices[self.marker]
        new_index = min(max(index + value, 0), len(self.markers) - 1)
        self.marker = self.markers[new_index]

    def marker_before(self, marker):
        return self.indices[self.marker] < self.indices[marker]

    def marker_after(self, marker):
        return self.indices[self.marker] > self.indices[marker]
    
    def marker_reached(self, marker):
        return self.indices[self.marker] >= self.indices[marker]

    def move_marker_forward(self, marker_text, _value=None):
        index = min(self.markers.index(marker_text) + 1, len(self.markers) - 1)
        self.marker = self.markers[index]

@register_stage(story="hubbles_law", index=5, steps=[
    # "CLASS AGE",
    # "CLASS DATA",
    # "UNCERTAINTIES"
])
class StageFour(HubbleStage):
    show_team_interface = Bool(False).tag(sync=True)

    _state_cls = StageState

    @default('stage_state')
    def _default_state(self):
        return StageState()

    @default('template')
    def _default_template(self):
        return load_template("stage_5.vue", __file__)

    @default('stage_icon')
    def _default_stage_icon(self):
        return "4"

    @default('title')
    def _default_title(self):
        return "Class results & Uncertainty"

    @default('subtitle')
    def _default_subtitle(self):
        return "Perhaps a small blurb about this stage"

    viewer_ids_for_data = {
        STUDENT_DATA_LABEL: ["comparison_viewer","layer_viewer"],
        CLASS_DATA_LABEL: ["comparison_viewer","layer_viewer"],
        CLASS_SUMMARY_LABEL: ["class_distr_viewer", "comparison_viewer"]
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._setup_complete = False
    
        add_callback(self.stage_state, 'stage_5_complete',
                     self._on_stage_complete)

        add_callback(self.story_state, 'responses', self.age_calc_update_guesses)

        if demo and self.stage_state.marker == 'ran_var1':
            self.stage_state.marker = 'cla_res1'
            self.prep_demo()
        
        self.show_team_interface = self.app_state.show_team_interface

        # for testing so that we don't break when looking for best fit galaxy
        if self.app_state.allow_advancing & (self.story_state.stage_index >= self.index):
            if not self.story_state.has_best_fit_galaxy:
                self.story_state.has_best_fit_galaxy = True
                self.story_state.update_student_data()

        student_data = self.get_data(STUDENT_DATA_LABEL)
        class_meas_data = self.get_data(CLASS_DATA_LABEL)
        all_data = self.get_data(ALL_DATA_LABEL)

        # Set the size from the class data
        self.stage_state.class_data_size = int(self.get_data(CLASS_DATA_LABEL).size / 5)

        fit_table = Table(self.session,
                          data=student_data,
                          glue_components=[NAME_COMPONENT,
                                           VELOCITY_COMPONENT,
                                           DISTANCE_COMPONENT],
                          key_component=NAME_COMPONENT,
                          names=['Galaxy Name',
                                 'Velocity (km/s)',
                                 'Distance (Mpc)'],
                          title='My Galaxies',
                          subset_label="fit_table_selected"
                          )
        self.add_widget(fit_table, label="fit_table")

        # Set up links between various data sets
        for field in [DISTANCE_COMPONENT, VELOCITY_COMPONENT]:
            self.add_link(CLASS_DATA_LABEL, field, ALL_DATA_LABEL, field)

        # Create viewers
        layer_viewer = self.add_viewer(label='layer_viewer')
        comparison_viewer = self.add_viewer(HubbleScatterView, "comparison_viewer", "Data Comparison")
        all_viewer = self.add_viewer(HubbleScatterView, "all_viewer", "All Data")
        class_distr_viewer = self.add_viewer(HubbleClassHistogramView,
                                             'class_distr_viewer', "My Class Ages (5 galaxies each)")
        all_distr_viewer_student = self.add_viewer(HubbleHistogramView,
                                           'all_distr_viewer_student', "All Student Ages (5 galaxies each)") # really just All students, but need the title bar
        all_distr_viewer_class = self.add_viewer(HubbleHistogramView,
                                           'all_distr_viewer_class', "All Class Ages (~100 galaxies each)")
        all_distr_viewer_class.toolbar.tools['bqplot:home'].old_activate = all_distr_viewer_class.toolbar.tools['bqplot:home'].activate

        add_callback(self.stage_state, 'marker',
                     self._on_marker_update, echo_old=True)
        self.trigger_marker_update_cb = True

        # layer_toggle = LayerToggle(layer_viewer, names={
        #     STUDENT_DATA_LABEL: "My Data",
        #     CLASS_DATA_LABEL: "Class Data"
        # })
        # self.add_component(layer_toggle, label="py-layer-toggle")
            
        # Grab data
        class_summ_data = self.get_data(CLASS_SUMMARY_LABEL)
        classes_summary_data = self.get_data(ALL_CLASS_SUMMARIES_LABEL)
        students_summary_data = self.get_data(ALL_STUDENT_SUMMARIES_LABEL)

        # Set up the listener to sync the histogram <--> scatter viewers

        # Set up the functionality for the histogram <---> scatter sync
        # We add a listener for when a subset is modified/created on
        # the histogram viewer as well as extend the xrange tool for the
        # histogram to always affect this subset
        histogram_source_label = "histogram_source_subset"
        histogram_modify_label = "histogram_modify_subset"
        self.histogram_listener = HistogramListener(self.story_state,
                                                    None,
                                                    class_summ_data,
                                                    None,
                                                    class_meas_data,
                                                    source_subset_label=histogram_source_label,
                                                    modify_subset_label=histogram_modify_label)

        # Create the student slider
        self.student_slider_subset = class_meas_data.new_subset(label=STUDENT_SLIDER_SUBSET_LABEL)
        self.student_slider_subset.style.alpha = 1
        self.student_slider_subset.style.markersize = 56
        student_slider = IDSlider(class_summ_data, STUDENT_ID_COMPONENT, AGE_COMPONENT, highlight_ids=[self.story_state.student_user["id"]])
        self.add_component(student_slider, "py-student-slider")
        def student_slider_change(id, highlighted):
            self.student_slider_subset.subset_state = RangeSubsetState(id, id, class_meas_data.id[STUDENT_ID_COMPONENT])
            color = student_slider.highlight_color if highlighted else student_slider.default_color
            self.student_slider_subset.style.color = color
        def student_slider_refresh(slider):
            self.stage_state.stu_low_age = round(min(slider.values, default=0))
            self.stage_state.stu_high_age = round(max(slider.values, default=0))
            comparison_viewer.state.reset_limits(visible_only=False)
        
        extend_tool(comparison_viewer, 'bqplot:home', lambda *args: comparison_viewer.state.reset_limits(visible_only=False), activate_before_tool=False)
        extend_tool(all_viewer, 'bqplot:home', lambda *args: all_viewer.state.reset_limits(visible_only=False), activate_before_tool=False)

        student_slider.on_id_change(student_slider_change)
        student_slider.on_refresh(student_slider_refresh)

        if self.stage_state.marker_reached("cla_dat1"):
            layer_viewer.state.reset_limits()

        layer_viewer.toolbar.set_tool_enabled("hubble:linedraw", self.stage_state.marker_reached("cla_dat1"))
        layer_viewer.toolbar.set_tool_enabled("hubble:linefit", self.stage_state.marker_reached("bes_fit1c"))

        # Create the class slider
        self.class_slider_subset = all_data.new_subset(label=CLASS_SLIDER_SUBSET_LABEL)
        self.class_slider_subset.style.markersize = 56
        class_slider = IDSlider(classes_summary_data, CLASS_ID_COMPONENT, AGE_COMPONENT, highlight_ids=[self.story_state.classroom["id"]], default_color = "#FF006E", highlight_color = "#3A86FF")
        self.add_component(class_slider, "py-class-slider")
        def class_slider_change(id, highlighted):
            self.class_slider_subset.subset_state = RangeSubsetState(id, id, all_data.id[CLASS_ID_COMPONENT])
            color = "#3A86FF" if highlighted else "#FF006E"
            self.class_slider_subset.style.color = color
        def class_slider_refresh(slider):
            self.stage_state.cla_low_age = round(min(slider.values))
            self.stage_state.cla_high_age = round(max(slider.values))
            all_viewer.state.reset_limits(visible_only=False)

        class_slider.on_id_change(class_slider_change)
        class_slider.on_refresh(class_slider_refresh)

        allclasses_percentage_subset_label = "allclasses_percentage_subset"
        myclass_percentage_subset_label = "myclass_percentage_subset"
        allstudents_percentage_subset_label = "allstudents_percentage_subset"
        
        mmm_text = {
            'mean':"""The mean is the average of all values in the dataset. The 
                      average is calculated by adding all the values together and dividing by the number of values.
                      In this example, the mean of the distribution is 14.
                      """, 
            'median': """The median is the middle of the dataset. 
                        Fifty percent of the data is above the median and fifty percent is less than or equal to the median.
                        In this example, the median the distribution is 15
                        """, 
            'mode':"""The mode is the most commonly measured value or range 
                        of values in a set of data and appears as the tallest bar in a histogram. 
                        In this example, the mode of the distribution is 16.
                        """
            }
        mmm_urls = {
            'median': f"{self.stage_state.image_location}/median.png",  #'https://picsum.photos/900/600', #
            'mean':   f"{self.stage_state.image_location}/mean.png",     #'https://picsum.photos/900/600', #
            'mode':   f"{self.stage_state.image_location}/mode.png"      #'https://picsum.photos/900/600'  # 
        }
        
        all_percentage_selector = PercentageSelector([self.viewers["all_distr_viewer_class"], self.viewers["all_distr_viewer_student"]],
                                                 [classes_summary_data, students_summary_data],
                                                 units=["Gyr"] * 2,
                                                 resolution=0,
                                                 subset_labels=[allclasses_percentage_subset_label, allstudents_percentage_subset_label])
        self.add_component(all_percentage_selector, "py-all-percentage-selector")

        all_statistics_selector = StatisticsSelector([all_distr_viewer_class, all_distr_viewer_student],
                                                 [classes_summary_data, students_summary_data],
                                                 units=["Gyr"] * 2,
                                                 transform=round)
        all_statistics_selector.help_text = mmm_text
        all_statistics_selector.help_images = mmm_urls
        self.add_component(all_statistics_selector, "py-all-statistics-selector")

        myclass_percentage_selector = PercentageSelector([self.viewers["class_distr_viewer"]],
                                                 [class_summ_data],
                                                 units=["Gyr"],
                                                 resolution=0,
                                                 subset_labels=[myclass_percentage_subset_label])
        self.add_component(myclass_percentage_selector, "py-myclass-percentage-selector")

        myclass_statistics_selector = StatisticsSelector([class_distr_viewer],
                                                 [class_summ_data],
                                                 units=["Gyr"],
                                                 transform=round)
        myclass_statistics_selector.help_text = mmm_text
        myclass_statistics_selector.help_images = mmm_urls
        self.add_component(myclass_statistics_selector, "py-myclass-statistics-selector")
        
        
        self.selectors = {
            'all': [all_percentage_selector, all_statistics_selector, myclass_percentage_selector, myclass_statistics_selector],
            'myclass': {'percentage': myclass_percentage_selector, 'statistics':myclass_statistics_selector},
            'allclass': {'percentage': all_percentage_selector, 'statistics':all_statistics_selector}
        }

        not_ignore = {
            fit_table.subset_label: [layer_viewer],
            histogram_source_label: [class_distr_viewer],
            histogram_modify_label: [comparison_viewer],
            STUDENT_SLIDER_SUBSET_LABEL: [comparison_viewer],
            allclasses_percentage_subset_label: [all_distr_viewer_class],
            myclass_percentage_subset_label: [class_distr_viewer],
            allstudents_percentage_subset_label: [all_distr_viewer_student],
            BEST_FIT_SUBSET_LABEL: [layer_viewer]
        }

        def label_ignore(x, label):
            return x.label == label

        for label, listeners in not_ignore.items():
            ignorer = partial(label_ignore, label=label)
            for viewer in self.all_viewers:
                if viewer not in listeners:
                    viewer.ignore(ignorer)
        
        # layers from the table selection have the same label, but we only want student_data selected
        layer_viewer.ignore(lambda layer: layer.label == fit_table.subset_label and layer.data != student_data)

        def comparison_ignorer(x):
            return x.label == histogram_modify_label and x.data != self.histogram_listener.modify_data

        comparison_viewer.ignore(comparison_ignorer)

        # load all the initial styles
        self._update_viewer_style(dark=self.app_state.dark_mode)

        # set reasonable offset for y-axis labels
        # it would be better if axis labels were automatically well placed
        velocity_viewers = [comparison_viewer, layer_viewer, all_viewer]
        # velocity_viewers = [prodata_viewer, comparison_viewer, morphology_viewer, layer_viewer]
        for viewer in velocity_viewers:
            viewer.figure.axes[1].label_offset = "5em"
        
        # Just for accessibility while testing
        self.data_collection.histogram_listener = self.histogram_listener

        # Set hypothetical galaxy info, if we have it
        self._update_hypgal_info()

        # Whenever data is updated, the appropriate viewers should update their bounds
        self.hub.subscribe(self, NumericalDataChangedMessage,
                           handler=self._on_data_change)

        def hist_selection_activate():
            if self.histogram_listener.source_subset is None:
                self.histogram_listener.source_subset = self.data_collection.new_subset_group(
                    label=self.histogram_listener.source_subset_label)
            self.session.edit_subset_mode.edit_subset = [
                self.histogram_listener.source_subset]

        def hist_selection_deactivate():
            self.session.edit_subset_mode.edit_subset = []

        extend_tool(class_distr_viewer, 'bqplot:xrange',
                    hist_selection_activate, hist_selection_deactivate)

        # We want the hub_fit_viewer to be selecting for the same subset as the table
        def fit_selection_activate():
            table = self.get_widget('fit_table')
            table.initialize_subset_if_needed()
            self.session.edit_subset_mode.edit_subset = [table.subset]

        def fit_selection_deactivate():
            self.session.edit_subset_mode.edit_subset = []
        
        extend_tool(layer_viewer, 'bqplot:rectangle', fit_selection_activate,
                    fit_selection_deactivate)

        # JC: There's apparently a way to link axes in glue-jupyter, so we should use that
        # but I'm not familiar with it, so in the interest of time, let's do this
        for prop in ['x_min', 'x_max']: 
            link((all_distr_viewer_student.state, prop), (all_distr_viewer_class.state, prop))
            
        # def match_axes():
        #     if self.stage_state.marker_reached('two_his1'):
        #         all_distr_viewer_student.state.reset_limits()
        #     return
        
        # extend_tool(all_distr_viewer_class, 'bqplot:home', activate_cb = match_axes, activate_before_tool=False)
        
        self.match_student_class_hist_axes(self.stage_state.marker_reached('two_his1'))
        
        # we want to always reset using the range of the student

        # If possible, we defer some of the setup for later, to make loading faster
        add_callback(self.story_state, 'stage_index', self._on_stage_index_changed)
        if self.story_state.stage_index == self.index:
            self._deferred_setup()
        
        if self.stage_state.marker == 'age_dis1c':
            all_distr_viewer_class.state.reset_limits()
            
    def _on_marker_update(self, old, new):
        if not self.trigger_marker_update_cb:
            return
        markers = self.stage_state.markers
        advancing = markers.index(new) > markers.index(old)

        layer_viewer = self.get_viewer("layer_viewer")
        comparison_viewer = self.get_viewer("comparison_viewer")
        all_viewer = self.get_viewer("all_viewer")

        if new == 'ran_var1':
            student_layer = layer_viewer.layer_artist_for_data(self.get_data(STUDENT_DATA_LABEL))
            class_layer = layer_viewer.layer_artist_for_data(self.get_data(CLASS_DATA_LABEL))
            student_layer.state.visible = True
            class_layer.state.visible = False

        if new == 'cla_res1':
            self.get_component("py-student-slider").refresh()
            if not comparison_viewer.toolbar.tools["hubble:linefit"].active: # if off
                comparison_viewer.toolbar.tools["hubble:linefit"].activate() # toggle on

        if new == 'cla_res1c':
            if not all_viewer.toolbar.tools["hubble:linefit"].active: # if off
                all_viewer.toolbar.tools["hubble:linefit"].activate() # toggle on
                    
        if advancing and new == "cla_dat1":
            layer_viewer.toolbar.tools["hubble:linedraw"].erase_line() 
            layer_viewer.toolbar.set_tool_enabled("hubble:linedraw", False)
            student_data = self.get_data(STUDENT_DATA_LABEL)
            if len(student_data.subsets) > 0:
                best_fit_subset = student_data.subsets[0]
                best_fit_layer = layer_viewer.layer_artist_for_data(best_fit_subset)
                best_fit_layer.state.visible = False
            class_layer = layer_viewer.layer_artist_for_data(self.get_data(CLASS_DATA_LABEL))
            class_layer.state.visible = True
            student_layer = layer_viewer.layer_artist_for_data(student_data)
            student_layer.state.visible = False
            linefit_tool = layer_viewer.toolbar.tools["hubble:linefit"]
            if linefit_tool.active:
                linefit_tool.activate()
            layer_viewer.toolbar.set_tool_enabled("hubble:linefit", False )
            layer_viewer.state.reset_limits()

        if advancing and new == "tre_lin2c":
            layer_viewer.toolbar.set_tool_enabled("hubble:linedraw", True)

        if advancing and new == "bes_fit1c":
            linefit_tool = layer_viewer.toolbar.tools["hubble:linefit"]
            if linefit_tool.active:
                linefit_tool.activate()
            layer_viewer.toolbar.set_tool_enabled("hubble:linefit", True)     
            layer_viewer.toolbar.tools["hubble:linefit"].show_labels = True
        
        if advancing and new == 'age_dis1c':
            self.get_viewer("all_distr_viewer_class").state.reset_limits()
        
        if advancing and new == 'two_his1':
            self.get_viewer("all_distr_viewer_student").state.reset_limits()
            self.match_student_class_hist_axes(True)
            # reset the selectors going to a new view
            for selector in self.selectors['all']:
                selector.selected = None
            
            
        if demo and old == 'two_his1':
            self.stage_state.marker = 'acc_unc1'
        
        if not advancing and self.stage_state.marker_before('two_his1'):
            self.match_student_class_hist_axes(False)

    def match_student_class_hist_axes(self, match = True):        
        student_tool = self.get_viewer("all_distr_viewer_student").toolbar.tools['bqplot:home']
        class_tool = self.get_viewer("all_distr_viewer_class").toolbar.tools['bqplot:home']
        
        if match:
            if class_tool.activate == student_tool.activate:
                # already matchced
                return
            else:
                # save old method and replace with student method
                class_tool.old_activate = class_tool.activate # save old method
                class_tool.activate = student_tool.activate # replace with student method
                return
        else:
            if class_tool.activate == class_tool.old_activate:
                # already restored/unmatched
                return
            else:
                # restore old method
                class_tool.activate = class_tool.old_activate
                return
    
    def _setup_scatter_layers(self):
        layer_viewer = self.get_viewer("layer_viewer")
        comparison_viewer = self.get_viewer("comparison_viewer")
        all_viewer = self.get_viewer("all_viewer")
        student_data = self.get_data(STUDENT_DATA_LABEL)
        class_meas_data = self.get_data(CLASS_DATA_LABEL)
        for viewer in [comparison_viewer, layer_viewer, all_viewer]:
            viewer.add_data(student_data)
            viewer.state.x_att = student_data.id[DISTANCE_COMPONENT]
            viewer.state.y_att = student_data.id[VELOCITY_COMPONENT]

        student_layer = layer_viewer.layer_artist_for_data(student_data)
        student_layer.state.visible = False # Don't need to display this in Stage 4.
        class_layer = layer_viewer.layer_artist_for_data(class_meas_data)
        class_layer.state.visible = True

        layer_viewer.toolbar.tools["hubble:linefit"].deactivate() 

        if self.story_state.has_best_fit_galaxy:
            subsets = self.get_data(STUDENT_DATA_LABEL).subsets
            if len(subsets) > 0:
                best_fit_subset = subsets[0]
                best_fit_layer = layer_viewer.layer_artist_for_data(best_fit_subset)
                best_fit_layer.state.visible = False

        draw_tool = layer_viewer.toolbar.tools['hubble:linedraw'] 
        add_callback(draw_tool, 'line_drawn', self._on_trend_line_drawn)
        
        line_fit_tool = layer_viewer.toolbar.tools['hubble:linefit']
        add_callback(line_fit_tool, 'active', self._on_best_fit_line_shown)
        
        layer_toolbar = layer_viewer.toolbar
        
        add_callback(self.story_state, 'has_best_fit_galaxy', self._on_best_fit_galaxy_added)
        
        student_layer = comparison_viewer.layer_artist_for_data(student_data)
        student_layer.state.zorder = 5
        comparison_viewer.add_data(class_meas_data)
        class_layer = comparison_viewer.layer_artist_for_data(class_meas_data)
        comparison_viewer.layer_artist_for_data(student_data).state.visible = False # Turn off student's own data on comparison viewer
        class_layer.state.visible = False  # Turn off layer with the whole class
        class_layer.state.zorder = 2
        # comparison_viewer.add_subset(self.student_slider_subset)
        comparison_viewer.state.x_att = class_meas_data.id[DISTANCE_COMPONENT]
        comparison_viewer.state.y_att = class_meas_data.id[VELOCITY_COMPONENT]
        comparison_viewer.state.reset_limits(visible_only=False)

        comparison_viewer.toolbar.tools["hubble:linefit"].activate() 

        all_data = self.get_data(ALL_DATA_LABEL)
        student_layer = all_viewer.layer_artist_for_data(student_data)
        student_layer.state.zorder = 2
        student_layer.state.visible = False
        all_viewer.add_data(class_meas_data)
        class_layer = all_viewer.layer_artist_for_data(class_meas_data)
        class_layer.state.zorder = 1
        class_layer.state.visible = False
        all_viewer.add_data(all_data)
        all_layer = all_viewer.layer_artist_for_data(all_data)
        all_layer.state.zorder = 0
        all_layer.state.color = "#78909C"
        all_layer.state.size = 7
        all_layer.state.visible = False
        all_viewer.state.x_att = all_data.id[DISTANCE_COMPONENT]
        all_viewer.state.y_att = all_data.id[VELOCITY_COMPONENT]
        all_viewer.state.reset_limits(visible_only=False)

        # Set up all viewer tools
        all_fit_tool = all_viewer.toolbar.tools["hubble:linefit"]
        all_fit_tool.show_labels = True
        all_fit_tool.activate()

        # We want to turn this off here so that a it doesn't show up in previous stages

        student_slider_subset_layer = [layer for layer in layer_viewer.layers if STUDENT_SLIDER_SUBSET_LABEL in layer.layer.label]
        student_slider_subset_layer = next(student_slider_subset_layer.__iter__(), None) # get the first element or None if empty
        if student_slider_subset_layer is not None:
            student_slider_subset_layer.visible = False
    
    def _setup_histogram_layers(self):
        class_distr_viewer = self.get_viewer("class_distr_viewer")
        all_distr_viewer_class = self.get_viewer("all_distr_viewer_class")
        all_distr_viewer_student = self.get_viewer("all_distr_viewer_student")
        
        class_summ_data = self.get_data(CLASS_SUMMARY_LABEL)
        students_summary_data = self.get_data(ALL_STUDENT_SUMMARIES_LABEL)
        classes_summary_data = self.get_data(ALL_CLASS_SUMMARIES_LABEL)
        
        histogram_viewers = [class_distr_viewer, all_distr_viewer_class,all_distr_viewer_student]
        all_distr = [all_distr_viewer_class, all_distr_viewer_student]
        
        for viewer in histogram_viewers:
            label = 'Count' # if viewer == class_distr_viewer else 'Proportion'
            if viewer not in all_distr:
                viewer.add_data(class_summ_data)
                layer = viewer.layer_artist_for_data(class_summ_data)
                layer.state.color = '#8338EC' # purple from alt palette #1
                layer.state.alpha = 1
            if viewer != class_distr_viewer and viewer != all_distr_viewer_class:
                viewer.add_data(students_summary_data)
                layer = viewer.layer_artist_for_data(students_summary_data)
                layer.state.color = '#FFBE0B' # yellow from alt palette #1
                layer.state.alpha = 1
                if viewer == all_distr_viewer_class:
                    layer.state.visible = False
                viewer.state.hist_n_bin = 20
            if viewer != class_distr_viewer and viewer != all_distr_viewer_student:
                viewer.add_data(classes_summary_data)
                layer = viewer.layer_artist_for_data(classes_summary_data)
                layer.state.color = '#619EFF' # light blue from alt palette #1
                layer.state.alpha = 1
                if viewer == all_distr_viewer_student:
                    layer.state.visible = False
                # viewer.state.normalize = True
                # viewer.state.y_min = 0
                # viewer.state.y_max = 1
                # viewer.state.hist_n_bin = 6
            viewer.figure.axes[1].label = label
            viewer.figure.axes[1].tick_format = '0'
            # viewer.figure.axes[1].num_ticks = 5
            
        
            

        class_distr_viewer.state.x_att = class_summ_data.id[AGE_COMPONENT]
        all_distr_viewer_class.state.x_att = classes_summary_data.id[AGE_COMPONENT]
        all_distr_viewer_student.state.x_att = students_summary_data.id[AGE_COMPONENT]

        
        def _update_bins(*args):
            for hist in histogram_viewers:
                props = ('hist_n_bin', 'hist_x_min', 'hist_x_max')
                with delay_callback(hist.state, *props):
                    layer = hist.layers[0] # only works cuz there is only one layer 
                    component = hist.state.x_att                   
                    xmin = round(layer.layer.data[component].min(),0) - 0.5
                    xmax = round(layer.layer.data[component].max(),0) + 0.5
                    hist.state.hist_n_bin = int(xmax - xmin)
                    hist.state.hist_x_min = xmin
                    hist.state.hist_x_max = xmax
        
        _update_bins()
        
        self.hub.subscribe(self, NumericalDataChangedMessage,
                           handler=_update_bins)


        theme = "dark" if self.app_state.dark_mode else "light"
        style_name = f"default_histogram_{theme}"
        style = load_style(style_name)
        update_figure_css(all_distr_viewer_student, style_dict=style)
        update_figure_css(all_distr_viewer_class, style_dict=style)
        
        class_distr_viewer.state.show_measuring_line()
        all_distr_viewer_student.state.show_measuring_line()
        all_distr_viewer_class.state.show_measuring_line()
        
        
        for hist in histogram_viewers:
            hist._label_text = lambda x: f"{round(x,0):.0f}"
        # class_distr_viewer.state.hide_measuring_line()
        # all_distr_viewer_student.state.hide_measuring_line()
        # all_distr_viewer_class.state.hide_measuring_line()

    def _deferred_setup(self):
        if self._setup_complete:
            return
        self._setup_scatter_layers()
        self._setup_histogram_layers()
        self._setup_complete = True

    @property
    def all_viewers(self):
        return [layout.viewer for layout in self.viewers.values()]
     
    def _update_viewer_style(self, dark):
        viewers = ['layer_viewer',
                   'comparison_viewer',
                   'all_viewer',
                   'class_distr_viewer',
                   'all_distr_viewer_class',
                   'all_distr_viewer_student',
                   ]

        viewer_type = ["scatter",
                       "scatter",
                       "scatter",
                       "histogram",
                       "histogram",
                       "histogram",]

        theme_name = "dark" if dark else "light"
        for viewer, vtype in zip(viewers, viewer_type):
            viewer = self.get_viewer(viewer)
            style = load_style(f"default_{vtype}_{theme_name}")
            update_figure_css(viewer, style_dict=style)

    def table_selected_color(self, dark):
        return "colors.lightBlue.darken4"
    
    def _update_hypgal_info(self):
        data = self.get_data(STUDENT_DATA_LABEL)
        indices = where(data[NAME_COMPONENT] == BEST_FIT_GALAXY_NAME)
        if indices[0]:
            index = indices[0][0]
            self.stage_state.hypgal_velocity = data[VELOCITY_COMPONENT][index]
            self.stage_state.hypgal_distance = data[DISTANCE_COMPONENT][index]
            self.stage_state.our_age = (AGE_CONSTANT * self.stage_state.hypgal_distance/self.stage_state.hypgal_velocity)

    # Can we remove this? This looks very old as it is referencing "stage_three" 
    def _update_image_location(self, using_voila):
        prepend = "voila/files/" if using_voila else ""
        self.stage_state.image_location = prepend + "data/images/stage_three"

    def _on_trend_line_drawn(self, is_drawn):
       #print("Trend line drawn: ", is_drawn)
        self.stage_state.class_trend_line_drawn = is_drawn
        
    def _on_best_fit_line_shown(self, is_active):
       #print("Best fit line shown: ", is_active)
        if not self.stage_state.class_best_fit_clicked:
            self.stage_state.class_best_fit_clicked = is_active

    def _on_best_fit_galaxy_added(self, value):
        layer_viewer = self.get_viewer("layer_viewer")
        linefit_tool = layer_viewer.toolbar.tools["hubble:linefit"]
        if value and not linefit_tool.active:
            linefit_tool.activate()
    
    def _on_stage_complete(self, complete):
        return
        if complete:
            self.story_state.stage_index = 6

            # We need to do this so that the stage will be moved forward every
            # time the button is clicked, not just the first
            self.stage_state.stage_5_complete = False
    
    def vue_stage_five_complete(self, *args):
        # print('vue_stage_five_complete')
        self.story_state.stage_index = 6
        self.stage_state.stage_5_complete = False
    
    def _reset_limits_for_data(self, label):
        viewer_id = self.viewer_ids_for_data.get(label, [])
        for vid in viewer_id:
            self.get_viewer(vid).state.reset_limits()
   
    def reset_viewer_limits(self):
        self._reset_limits_for_data(STUDENT_DATA_LABEL)
        self._reset_limits_for_data(CLASS_DATA_LABEL)
        self._reset_limits_for_data(CLASS_SUMMARY_LABEL)
    
    def _on_data_change(self, msg):
        label = msg.data.label
        if self.story_state.stage_index == self.index:
            if label == STUDENT_DATA_LABEL:
                self.get_component("py-student-slider").refresh()
                self._update_hypgal_info()
            elif label == CLASS_SUMMARY_LABEL:
                self.get_component("py-student-slider").refresh()
            elif label == ALL_CLASS_SUMMARIES_LABEL:
                class_slider = self.get_component("py-class-slider")
                class_slider.update_data(msg.data)
            self._reset_limits_for_data(label)

        if label == CLASS_DATA_LABEL:
            self.stage_state.class_data_size = int(self.get_data(CLASS_DATA_LABEL).size / 5)

    def _on_dark_mode_change(self, dark):
        super()._on_dark_mode_change(dark)
        self._update_viewer_style(dark)
        
    def age_calc_update_guesses(self, responses):
        key = str(self.index)
        state = self.stage_state.age_calc_state
        if key in responses:
            r = responses[key]
            state['low_guess'] = r.get('likely-low-age', "")
            state['high_guess'] = r.get('likely-high-age', "")
            state['best_guess'] = r.get('best-guess-age', "")

        # The shortcomings text is in stage 4
        stage_4_key = str(4)
        if stage_4_key in responses:
            r = responses[stage_4_key]
            state['short_one'] = r.get('shortcoming-1', "")
            state['short_two'] = r.get('shortcoming-2', "")
            state['short_other'] = r.get('other-shortcomings', "")
    
    def _on_stage_index_changed(self, index):
       #print("Stage Index: ",self.story_state.stage_index)
        if index >= self.index:
            self._deferred_setup()

        if index == self.index:
            self.reset_viewer_limits()
            self.get_component("py-student-slider").refresh()

            if self.stage_state.marker == 'ran_var1':
                layer_viewer = self.get_viewer("layer_viewer")
                student_layer = layer_viewer.layer_artist_for_data(self.get_data(STUDENT_DATA_LABEL))
                class_layer = layer_viewer.layer_artist_for_data(self.get_data(CLASS_DATA_LABEL))
                student_layer.state.visible = True
                class_layer.state.visible = False

    def prep_demo(self):
        self.stage_state.class_trend_line_drawn = True
        self.stage_state.class_best_fit_clicked = True