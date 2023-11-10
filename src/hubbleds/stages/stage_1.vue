<template>
  <v-container>
    <v-row v-if="show_team_interface">
      <v-col>
        <v-btn
          color="success"
          class="black--text"
          @click="fill_data();"
        >fill data points</v-btn>
        <v-btn
          color="success"
          class="black--text"
          @click="() => {
            console.log('stage state:', stage_state);
            console.log('story state:', story_state);
          }"
        >
          console.log State
        </v-btn>
        <v-btn
          color="success"
          class="black--text"
          @click="() => {
            print_state();
          }"
        >
          Print Python State
        </v-btn>
        <v-btn
          color="success"
          class="black--text"
          @click="() => {
            fill_data();
            stage_state.marker = 'dop_cal6';
            stage_state.reflection_complete = true;
          }"
        >
          Jump
        </v-btn>
        Marker: {{ stage_state.marker }}
      </v-col>
    </v-row>

    <v-row>
      <v-col
        cols="12"
        lg="4"
        :style="$vuetify.breakpoint.lg ? 'max-height: 100px' : 'max-height: 2500px'"
      >
        <guideline-intro-guidelines
          v-if="stage_state.marker === 'mee_gui1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-select-galaxies-1
          v-if="stage_state.marker === 'sel_gal1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-select-galaxies-2
          v-if="stage_state.marker === 'sel_gal2' && stage_state.gals_total === 0"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-select-galaxies-3
          v-if="stage_state.marker === 'sel_gal3'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-select-galaxies-4
          v-if="stage_state.marker === 'sel_gal4'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <v-btn
          v-if="show_team_interface && (stage_state.marker === 'sel_gal2' || 'sel_gal3 || sel_gal4' && stage_state.gals_total < stage_state.gals_max)"
          color="success"
          class="black--text"
          block
          max-width="800"
          @click="select_galaxies();"
        >select 5 galaxies</v-btn>
      </v-col>
      <v-col
        cols="12"
        lg="8"
      >
        <v-card
          :color="stage_state.csv_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.csv_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
        >
          <py-selection-tool/>
          <!-- <v-card-actions>
            <v-btn @click="story_state.step_index += 1; story_state.step_complete = true">Next Step</v-btn>
          </v-card-actions> -->
        </v-card>
      </v-col>
    </v-row>

<!-- Table Row -->
    <v-row>
      <v-col
        cols="12"
        lg="4"
        :style="$vuetify.breakpoint.lg ? 'max-height: 400px' : 'max-height: 2500px'"
      >
        <guideline-notice-galaxy-table 
          v-if="stage_state.marker === 'sel_gal2' && stage_state.gals_total === 1"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-choose-row
          v-if="stage_state.marker === 'cho_row1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-doppler-calc-3
          v-if="stage_state.marker === 'dop_cal3'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-doppler-calc-4
          v-if="stage_state.marker === 'dop_cal4' || stage_state.marker === 'dop_cal5'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <slideshow-doppler-calc-5
          v-if="stage_state.marker === 'dop_cal5'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-check-measurement
          v-if="stage_state.marker === 'che_mea1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-12
          v-if="stage_state.marker === 'dot_seq12'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-13
          v-if="stage_state.marker === 'dot_seq13'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-remaining-gals
          v-if="stage_state.marker === 'rem_gal1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-doppler-calc-6
          v-if="stage_state.marker === 'dop_cal6'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-reflect-vel-values
          v-if="stage_state.marker === 'ref_vel1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
          @ready="stage_state.ref_vel1_q = true"
        />       
        <guideline-end-stage1
          v-if="stage_state.marker === 'end_sta1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
          @stage_complete="() => {stage_one_complete(); console.log('emit: stage one complete');}"
        />  
      </v-col>
      <v-col
        cols="12"
        lg="8"
        class="galtable_column"
      >
        <v-card
          :color="stage_state.table_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.table_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
          v-if="stage_state.show_galaxy_table || ((stage_state.indices[stage_state.marker] < stage_state.indices['cho_row1'])  || (stage_state.indices[stage_state.marker] >= stage_state.indices['rem_gal1']) )"
        > 
          <jupyter-widget  :widget="widgets.galaxy_table"/>
        </v-card>
        <v-card
          :color="stage_state.table_highlights.includes(stage_state.marker) ? 'info' : 'black'"
          :class="stage_state.table_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
          outlined
          v-if="stage_state.show_example_galaxy_table || ((stage_state.indices[stage_state.marker] >= stage_state.indices['cho_row1'])  && (stage_state.indices[stage_state.marker] < stage_state.indices['rem_gal1']) )" 
        > 
          <jupyter-widget :widget="widgets.example_galaxy_table"/>
        </v-card>
      </v-col>
    </v-row>

    <v-row v-if="show_team_interface || (stage_state.indices[stage_state.marker] >= stage_state.indices['int_dot1'] && (stage_state.indices[stage_state.marker] < stage_state.indices['rem_gal1']) )">
      <v-col
        cols="12"
        lg="6"
      >
      </v-col>
      <v-col
        cols="12"
        lg="4"
      >     
        <py-dotplot-tutorial-slideshow
        />
      </v-col>
    </v-row>

<!-- Row for First Velocity Dot Plot -->
    <v-row
      v-if="stage_state.indices[stage_state.marker] >= stage_state.indices['int_dot1'] && stage_state.indices[stage_state.marker] < stage_state.indices['dot_seq13'] || stage_state.indices[stage_state.marker] == stage_state.indices['dot_seq14']">
      <v-col
        cols="12"
        lg="4"
      >
        <guideline-intro-dotplot
          v-if="stage_state.marker === 'int_dot1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-01
          v-if="stage_state.marker === 'dot_seq1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-02
          v-if="stage_state.marker === 'dot_seq2'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-03
          v-if="stage_state.marker === 'dot_seq3'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-05
          v-if="stage_state.marker === 'dot_seq5'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-06
          v-if="stage_state.marker === 'dot_seq6'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-07
          v-if="stage_state.marker === 'dot_seq7'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-08
          v-if="stage_state.marker === 'dot_seq8'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
          @ready="stage_state.dot_seq8_q = true"
        />
        <guideline-dot-sequence-09
          v-if="stage_state.marker === 'dot_seq9'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
      </v-col>
      <v-col
        cols="12"
        lg="8"
        class="py-0"
      >
        <v-card
          outlined
        >
            <jupyter-widget :widget="viewers.dotplot_viewer"
            />
        </v-card>
      </v-col>
    </v-row>


<!-- Row for 2nd Velocity Dot Plot -->
    <v-row
      v-if="stage_state.indices[stage_state.marker] == stage_state.indices['dot_seq14']"
    >
      <v-col
        cols="12"
        lg="4"
      >
        <guideline-dot-sequence-14
          v-if="stage_state.marker === 'dot_seq14'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
      </v-col>
      <v-col
        cols="12"
        lg="8"
      >
        <v-row>
          <v-col
            class="py-0"
          >
            <v-card
              outlined
            >
                <jupyter-widget :widget="viewers.dotplot_viewer_2"
                />
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>

<!-- Row for Spectrum Viewer -->
    <v-row>
      <v-col
        cols="12"
        lg="4"
      >
        <guideline-spectrum
          v-if="stage_state.marker === 'mee_spe1' || stage_state.marker === 'spe_tut1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-restwave
          v-if="stage_state.marker === 'res_wav1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-obswave-1
          v-if="stage_state.marker === 'obs_wav1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-obswave-2
          v-if="stage_state.marker === 'obs_wav2'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-reflect-on-data
          v-if="stage_state.marker === 'ref_dat1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-doppler-calc-0
          v-if="stage_state.marker === 'dop_cal0'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-doppler-calc-1
          v-if="stage_state.marker === 'dop_cal1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-doppler-calc-2
          v-if="stage_state.marker === 'dop_cal2'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-04
          v-if="stage_state.marker === 'dot_seq4'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-10
          v-if="stage_state.marker === 'dot_seq10'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-11
          v-if="stage_state.marker === 'dot_seq11'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
        <guideline-dot-sequence-13a
          v-if="stage_state.marker === 'dot_seq13a'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"
        />
      </v-col>
      <v-col
        v-if="(stage_state.spec_viewer_reached && stage_state.indices[stage_state.marker] < stage_state.indices['int_dot1']) || (stage_state.indices[stage_state.marker] >= stage_state.indices['dot_seq4'] && stage_state.indices[stage_state.marker] < stage_state.indices['dot_seq14']) || (stage_state.indices[stage_state.marker] >= stage_state.indices['rem_gal1'])"
        cols="12"
        lg="8"
      >
        <v-row>
          <v-col
            class="py-0"
          >
            <v-card
              :color="stage_state.spec_highlights.includes(stage_state.marker) ? 'info' : 'black'"
              :class="stage_state.spec_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
              outlined
            >
              <jupyter-widget :widget="viewers.spectrum_viewer"/>
            </v-card>
          </v-col>
        </v-row>
        <v-row>
          <v-col
            cols="4"
            offset="2"
          >
            <!-- LEARN MORE Dialog -->
            <py-spectrum-slideshow />
            <py-dotplot-tutorial-slideshow 
              v-if="stage_state.indices[stage_state.marker] >= stage_state.indices['rem_gal1']" 
            />
          </v-col>
          <v-col
            cols="4"
          >
            <!-- REFLECTION Dialog -->
            <reflect-velocity-windows
              v-if="(stage_state.obswaves_total >= 5) && !(stage_state.marker === 'rem_gal1')"
              button-text="reflect"
              close-text="submit"
              :state="stage_state"
              :require-responses="!show_team_interface"
              @submit="
                stage_state.reflection_complete = true;
                console.log('Submit button was clicked.');
              "
            >
            </reflect-velocity-windows>
            <!-- Placeholder for Reflection button -->
            <v-btn
              v-if="(stage_state.obswaves_total < 5) || (stage_state.marker === 'rem_gal1')"
              disabled
              block
              color="info"
              elevation="2"
            >
              <v-spacer></v-spacer>
              reflect
              <v-spacer></v-spacer>
              <v-icon
                class="ml-4"
              >
                mdi-circle-outline
              </v-icon>
            </v-btn>
          </v-col>
        </v-row>
        <v-row>
          <v-col
            v-if="show_team_interface">
            <v-btn
              color="success"
              class="black--text"
              @click="update_velocities()"
            >
              calculate velocities
            </v-btn>
          Marker: {{ stage_state.marker }}
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>


<style>

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
