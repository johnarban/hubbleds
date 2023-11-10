<template>
  <v-container>
        <v-row>
      <!-- for these markers ['age_dis1', 'con_int1', 'cla_res1c','two_his1'] create chips in a v-chip group
        where clicking on the chip will set the marker to that value -->
        <v-chip-group
          active-class="primary"
          column
        >
        
           <v-text-field
          class="demo_v-text-field"
          v-model="stage_state.marker"
          rounded
          outlined
          dense
          label="Marker"
          @change="() => {
            console.log('stage state:', stage_state);
            console.log('story state:', story_state);
          }"
        />
          <v-chip
            v-for="(marker, index) in stage_state.demo_markers"
            dark
            :color="stage_state.marker == marker ? 'deep-purple darken-4' : 'blue-grey darken-3'"
            text-color="blue-grey lighten-5"
            :key="index"
            @click="stage_state.marker = marker"
          >
            {{ marker }}
          </v-chip>
        </v-chip-group>
      
    </v-row>
    <v-row v-if="show_team_interface">
      <v-col>
        <v-btn
          color="success"
          class="black--text"
          @click="() => {
            console.log('stage state:', stage_state);
            console.log('story state:', story_state);
          }"
        >
          State
        </v-btn>
        <v-btn
          color="success"
          class="black--text"
          @click="() => {
            stage_state.marker = 'lea_unc1';
          }"
        >
          jump
        </v-btn>
        Marker: {{ stage_state.marker }}
      </v-col>
    </v-row>

    <!--------------------- OUR DATA HUBBLE VIEWER ----------------------->

    <v-row
      class="d-flex align-stretch"
      v-if="
        (stage_state.indices[stage_state.marker] >= stage_state.indices['ran_var1']
          &&
          stage_state.indices[stage_state.marker] < stage_state.indices['cla_res1'])
        || // OR
        (stage_state.indices[stage_state.marker] > stage_state.indices['con_int3']
          &&
          stage_state.indices[stage_state.marker] < stage_state.indices['cla_res1c'])"
    >
      <v-col
        cols="12"
        lg="5"
      >

        <guideline-random-variability
          v-if="stage_state.marker == 'ran_var1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-class-data
          v-if="stage_state.marker == 'cla_dat1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-trend-lines-draw2-c
          v-if="stage_state.marker == 'tre_lin2c'"
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-best-fit-line-c
          v-if="stage_state.marker == 'bes_fit1c'"
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-your-age-estimate-c
          v-if="stage_state.marker == 'you_age1c'"
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.my_galaxies_plot_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.my_galaxies_plot_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <!-- <py-layer-toggle/> -->
          <v-lazy>
            <jupyter-widget :widget="viewers.layer_viewer"/>
          </v-lazy>
        </v-card>
        <v-row>
          <v-col
            cols="10"
            offset="1"
          >
            <py-hubble-slideshow/>  
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <!--------------------- SLIDER VERSION: OUR DATA HUBBLE VIEWER ----------------------->

    <v-row
      class="d-flex align-stretch"
      v-if="stage_state.indices[stage_state.marker] > stage_state.indices['ran_var1'] && stage_state.indices[stage_state.marker] < stage_state.indices['cla_dat1']"
    > 
      <v-col
        cols="12"
        lg="5"
      >
        <guideline-classmates-results
          v-if="stage_state.marker == 'cla_res1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-relationship-age-slope-mc
          v-if="stage_state.marker == 'rel_age1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.relage_response = true"  />
        <guideline-class-age-range
          v-if="stage_state.marker == 'cla_age1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
        <guideline-class-age-range2
          v-if="stage_state.marker == 'cla_age2'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
        <guideline-class-age-range3
          v-if="stage_state.marker == 'cla_age3'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
        <guideline-class-age-range4
          v-if="stage_state.marker == 'cla_age4'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
        <guideline-learn-uncertainty1
          v-if="stage_state.marker == 'lea_unc1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
        <guideline-most-likely-value1
          v-if="stage_state.marker == 'mos_lik1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.all_galaxies_plot_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.all_galaxies_plot_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <v-lazy>
            <jupyter-widget
              :widget="viewers.comparison_viewer"
              class="comparison_viewer"
              />
          </v-lazy>
          <py-student-slider 
            class="slider_card"
            />
        </v-card>
        <py-hubble-slideshow/>  
      </v-col>
    </v-row>
    <v-row
      v-if="stage_state.indices[stage_state.marker] >= stage_state.indices['lea_unc1'] && stage_state.indices[stage_state.marker] <= stage_state.indices['you_age1c']"
    >
      <v-col
        cols="12"
        lg="5"
      >
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-row>
          <v-col
            cols="10"
            offset="1"
          >
            <slideshow-uncertainty1
              :state="stage_state"
            />  
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <!--------------------- ALL DATA HUBBLE VIEWER - during class sequence ----------------------->
    <v-row
      class="d-flex align-stretch"
      v-if="(stage_state.indices[stage_state.marker] > stage_state.indices['you_age1c'])"
    >
      <v-col
        cols="12"
        lg="5"
      >
        <guideline-classmates-results-c
          v-if="stage_state.marker == 'cla_res1c'"
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-class-age-range-c
          v-if="stage_state.marker == 'cla_age1c'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          outlined
        >
          <v-lazy>
            <jupyter-widget :widget="viewers.all_viewer"/>
          </v-lazy>
          <py-class-slider 
            class="slider_card"
            />
        </v-card>
      </v-col>
    </v-row>

    <v-row
      v-if="stage_state.indices[stage_state.marker] >= stage_state.indices['cla_res1c']"
    >
      <v-col
        cols="12"
        lg="5"
      >
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-row>
          <v-col
            cols="10"
            offset="1"
          >
            <slideshow-uncertainty1
              :state="stage_state"
            />  
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <!--------------------- OUR CLASS HISTOGRAM VIEWER ----------------------->
    <v-row
      class="d-flex align-stretch"
      v-if="stage_state.indices[stage_state.marker] >= stage_state.indices['age_dis1'] && stage_state.indices[stage_state.marker] <= stage_state.indices['con_int3'] "
    >
      <v-col
        cols="12"
        lg="5"
      >
        <v-row
          class="mb-2"
        >
          <v-col>
            <py-myclass-statistics-selector
            v-if="stage_state.indices[stage_state.marker] >= stage_state.indices['mos_lik2'] && stage_state.indices[stage_state.marker] <= stage_state.indices['con_int3'] " 
            />
          </v-col>
          <v-col>
            <py-myclass-percentage-selector 
            v-if="stage_state.indices[stage_state.marker] >= stage_state.indices['con_int2'] && stage_state.indices[stage_state.marker] <= stage_state.indices['con_int3'] "
            />
          </v-col>
        </v-row>
        <guideline-class-age-distribution
          v-if="stage_state.marker == 'age_dis1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
        <guideline-most-likely-value2
          v-if="stage_state.marker == 'mos_lik2'"
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-most-likely-value3
          v-if="stage_state.marker == 'mos_lik3'"
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-confidence-interval
        v-if="stage_state.marker == 'con_int1'"
        :state="stage_state"
        v-intersect.once="scrollIntoView" />
        <guideline-confidence-interval2
          v-if="stage_state.marker == 'con_int2'"
          :state="stage_state"
          v-intersect.once="scrollIntoView" />

      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.my_class_hist_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.my_class_hist_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <v-lazy>
            <jupyter-widget :widget="viewers.class_distr_viewer"/>
          </v-lazy>
        </v-card>
      </v-col>
    </v-row>


    <guideline-most-likely-value-reflect4
      v-if="stage_state.marker == 'mos_lik4'"
      :state="stage_state"
      v-intersect.once="scrollIntoView" />
    <guideline-confidence-interval-reflect3
      v-if="stage_state.marker == 'con_int3'"
      :state="stage_state"
      v-intersect.once="scrollIntoView" />

    <!--------------------- ALL DATA HISTOGRAM VIEWER ----------------------->
    <!-- cla_age1c -->
  
    <v-row
      class="d-flex align-stretch"
      v-if="stage_state.indices[stage_state.marker] > stage_state.indices['cla_age1c']"
    >
      <v-col
        cols="12"
        lg="5"
      >
        <v-row
          class="mb-2"
        >
          <v-col>
            <py-all-statistics-selector />
          </v-col>
          <v-col>
            <py-all-percentage-selector />
          </v-col>
        </v-row>
        <guideline-class-age-distribution-c
          v-if="stage_state.marker == 'age_dis1c'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>       
        <guideline-two-histograms1
          v-if="stage_state.marker == 'two_his1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
        <guideline-two-histograms-mc2
          v-if="stage_state.marker == 'two_his2'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.two_hist_response = true"/>
        <guideline-two-histograms-mc3
          v-if="stage_state.marker == 'two_his3'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.two_hist3_response = true"/>
          <guideline-two-histograms-mc3a
          v-if="stage_state.marker == 'two_his3a'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.two_hist3a_response = true"/>
        <guideline-two-histograms-reflect5
          v-if="stage_state.marker == 'two_his5'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>               
        <guideline-lack-bias-mc1
          v-if="stage_state.marker == 'lac_bia1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.lack_bias_response = true"/>
        <!-- <guideline-lack-bias-reflect2
          v-if="stage_state.marker == 'lac_bia2'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/> -->
        <guideline-lack-bias-reflect3
          v-if="stage_state.marker == 'lac_bia3'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
        <guideline-more-data-distribution
          v-if="stage_state.marker == 'mor_dat1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"
          @stage_complete="() => {stage_five_complete(); console.log('emit: stage five complete');}"
        />
        <!-- <guideline-account-uncertainty
          v-if="stage_state.marker == 'acc_unc1'"
          :state="stage_state"
          v-intersect.once="scrollIntoView"
          @stage_complete="() => {stage_five_complete(); console.log('emit: stage five complete');}"
          /> -->
      </v-col>
      <v-col
        cols="12"
        lg="7"
      >
        <v-card
          :color="stage_state.all_classes_hist_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.all_classes_hist_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <v-lazy>
            <!-- Change v-if marker to include when we want to start showing student value -->

          <jupyter-widget :widget="viewers.all_distr_viewer_student"
              v-if="stage_state.indices[stage_state.marker] > stage_state.indices['con_int2c']"
            />
          </v-lazy>
          <v-lazy>
            <jupyter-widget :widget="viewers.all_distr_viewer_class"/>
          </v-lazy>
        </v-card>
      </v-col>
    </v-row>

    <guideline-confidence-interval-reflect2-c
      v-if="stage_state.marker == 'con_int2c'"
      :state="stage_state"
      v-intersect.once="scrollIntoView"/>

      <v-row v-if="show_team_interface">
      <v-col>
        <v-btn
          color="success"
          class="black--text"
          @click="() => {
            console.log('stage state:', stage_state);
            console.log('story state:', story_state);
          }"
        >
          State
        </v-btn>
        <v-btn
          color="success"
          class="black--text"
          @click="() => {
            stage_state.marker = 'lea_unc1';
          }"
        >
          jump
        </v-btn>
        Marker: {{ stage_state.marker }}
      </v-col>
    </v-row>
  </v-container>
</template>


<style>


.demo_v-text-field {
  flex: none;
  margin: auto 10px;
}
.demo_v-text-field div.v-input__slot {
  width: 15ch;
  font-size: 10pt;
}

.v-dialog .v-card__text {
  font-size: 18px !important;
}

.v-radio label.theme--dark{
  color: white !important;
}
.v-radio label.theme--light{
  color: black !important;
}

.v-alert .v-input--radio-group+.v-alert, .v-dialog .v-input--radio-group+.v-alert {
  background-color: #000b !important;
}

.v-slider__thumb:hover, .v-slider__thumb-label-container:hover {
  cursor: grab;
}

.v-slider__thumb:active, .v-slider__thumb-label-container:active {
  cursor: grabbing;
}

.comparison_viewer.v-card {
  border-bottom-left-radius: 0px !important;
  border-bottom-right-radius: 0px !important;
  margin-bottom: 1px !important;
}

.slider_card {
  border-top-left-radius: 0px !important;
  border-top-right-radius: 0px !important;
}

.g_legend{
  fill: #FF006E30 !important;
}

.legendtext {
  fill: #000!important;
}

StudentResponse.StudentResponses {
  font-weight: bold;
  padding: 1px 6px;
  background-color: #FFA3;
  border-radius: 5px;
}

p.StudentResponses {
  font-weight: bold;
  padding: 10px 15px;
  background-color: #8882;
  border-radius: 10px;
}

</style>


<script>

module.exports = {
  mounted() {
    const config = { childList: true, subtree: true };
    const onMutation = (mutationList, observer) => {
      for (const mutation of mutationList) {
        if (mutation.type === 'childList') {
          const target = mutation.target;
          const viewerName = this.viewerName(target);
          if (viewerName !== null) {
            const resizeObserver = new ResizeObserver((entries) => {
              for (const entry of entries) {
                const pixelSize = entry.devicePixelContentBoxSize[0];
                const width = pixelSize.inlineSize;
                const nticks = Math.floor(width / 125);
                this.set_viewer_nticks({ nticks: nticks, axis: 'x', viewer: viewerName });
              }
            });
            resizeObserver.observe(target, { box: 'device-pixel-content-box' });
          }
        }
      }
    }
    const observer = new MutationObserver(onMutation);
    observer.observe(this.$el, config);
  },
  methods: {
    scrollIntoView: function(entries, observer, isIntersecting) {
      if (isIntersecting) {
        entries[0].target.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }
    },
    viewerName: function(node) {
      for (const key of Object.keys(this.viewers)) {
        if (node.classList.contains(key)) {
          return key;
        }
      }
      return null;
    }
  }
}

</script>
