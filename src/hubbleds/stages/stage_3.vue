<template>
  <v-container>
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
            console.log('jumping');
            stage_state.marker = 'dot_seq5';
            fill_table();

          }"
        >
          jump
        </v-btn>
        Marker: {{ stage_state.marker }}
      </v-col>
    </v-row>
    <v-row
      class="d-flex align-stretch"
    >
      <v-col
        cols="12"
        lg="4"
      >
        <guideline-angsize-meas1
          v-if="stage_state.marker == 'ang_siz1'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-angsize-meas2
          v-if="stage_state.marker == 'ang_siz2'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-angsize-meas2b
          v-if="stage_state.marker == 'ang_siz2b'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-angsize-meas3
          v-if="stage_state.marker == 'ang_siz3'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-angsize-meas4
          v-if="stage_state.marker == 'ang_siz4'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-angsize-meas5a
          v-if="stage_state.marker == 'ang_siz5a'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-angsize-meas6
          v-if="stage_state.marker == 'ang_siz6'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-dotplot-seq5
          v-if="stage_state.marker == 'dot_seq5'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-dotplot-seq5b
          v-if="stage_state.marker == 'dot_seq5b'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
      </v-col>
      <v-col
        cols="12"
        lg="8"
      >
        <v-row>
          <v-col
            class="py-0"
          >
          <!-- v-if="stage_state.distance_tool_shown.includes(stage_state.marker)" -->
            <v-card
              :color="stage_state.csv_highlights.includes(stage_state.marker) ? 'info' : 'black'"
              :class="stage_state.csv_highlights.includes(stage_state.marker) ? 'pa-1 my-n1' : 'pa-0'"
              outlined
            >
              <py-distance-tool 
              @brightness="(value) => {stage_state.brightness = (value/100); console.log('brightness', Math.round(value)/100);}"
              />
            </v-card>
          </v-col>
        </v-row>
        <v-row
          v-if="stage_state.indices[stage_state.marker] >= stage_state.indices['ang_siz5a']"
        >
          <v-col
            cols="6"
            offset="3"
          >
            <py-dosdonts-slideshow />
          </v-col>
        </v-row>
      </v-col>
      <v-col
        cols="12"
        lg="8"
        offset-lg="4"
        v-if="stage_state.distance_sidebar"
      >
        <py-distance-sidebar />
      </v-col>
    </v-row>

    <v-row>
      <v-col
        cols="12"
        lg="4"
      >
        <guideline-choose-row1
          v-if="stage_state.marker == 'cho_row1'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-angsize-meas5
          v-if="stage_state.marker == 'ang_siz5'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-estimate-distance1
          v-if="stage_state.marker == 'est_dis1'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-estimate-distance2
          v-if="stage_state.marker == 'est_dis2'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-choose-row2
          v-if="stage_state.marker == 'cho_row2'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />    
        <guideline-estimate-distance3
          v-if="stage_state.marker == 'est_dis3'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-estimate-distance4
          v-if="stage_state.marker == 'est_dis4'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-dotplot-seq5a
          v-if="stage_state.marker == 'dot_seq5a'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-dotplot-seq5c
          v-if="stage_state.marker == 'dot_seq5c'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-repeat-remaining-galaxies
          v-if="stage_state.marker == 'rep_rem1'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-fill-remaining-galaxies
          v-if="stage_state.marker == 'fil_rem1'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" 
          @stage_complete="() => {stage_three_complete(); console.log('emit: stage three complete');}"
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
        >
          <jupyter-widget v-if="stage_state.show_galaxy_table || (stage_state.indices[stage_state.marker] >= stage_state.indices['rep_rem1'])" :widget="widgets.distance_table" />        
          <jupyter-widget v-if="stage_state.show_exgal_table || (stage_state.indices[stage_state.marker] < stage_state.indices['rep_rem1'])" :widget="widgets.example_galaxy_distance_table"/>
        </v-card>
      </v-col>
    </v-row>  
    <v-row>
      <v-col
        cols="12"
        lg="4"
      >
        <guideline-dotplot-seq1
          v-if="stage_state.marker == 'dot_seq1'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
        <guideline-dotplot-seq2
          v-if="stage_state.marker == 'dot_seq2'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.dot_seq2_q = true"/>
        <guideline-dotplot-seq3
          v-if="stage_state.marker == 'dot_seq3'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
        <guideline-dotplot-seq4
          v-if="stage_state.marker == 'dot_seq4'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
        <guideline-dotplot-seq4a
          v-if="stage_state.marker == 'dot_seq4a'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" 
          @ready="stage_state.dot_seq4a_q = true"/>
        <guideline-dotplot-seq6
          v-if="stage_state.marker == 'dot_seq6'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.dot_seq6_q = true" />
        <guideline-dotplot-seq7
          v-if="stage_state.marker == 'dot_seq7'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView" />
      </v-col>
      <v-col
        cols="12"
        lg="8"
      >
        <v-row>
          <v-col
            class="py-0"
          >
            <v-card class="dotplot" v-if="stage_state.show_dotplot1 || ((stage_state.indices['dot_seq1'] <= stage_state.indices[stage_state.marker]) && (stage_state.indices[stage_state.marker] <= stage_state.indices['dot_seq5'])) || (stage_state.marker == 'dot_seq6')">
            <jupyter-widget :widget="viewers.dotplot_viewer_dist"/>
            </v-card>

            <v-card class="dotplot" v-if="stage_state.show_dotplot2 || ((stage_state.indices['dot_seq5c'] <= stage_state.indices[stage_state.marker]) && (stage_state.indices[stage_state.marker] < stage_state.indices['rep_rem1']))">
              <jupyter-widget :widget="viewers.dotplot_viewer_dist_2"/>
            </v-card>
            <v-card class='dotplot' v-if="stage_state.show_dotplot1_ang || stage_state.marker == 'dot_seq4' || stage_state.marker == 'dot_seq4a'">
              <jupyter-widget :widget="viewers.dotplot_viewer_ang"/>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <!-- <v-row>
      <v-col
        cols="12"
        lg="4"
      >
        <guideline-dotplot-seq4
        v-if="stage_state.marker == 'dot_seq4'" 
          :state="stage_state"
          v-intersect.once="scrollIntoView"/>
      </v-col>
      <v-col
        cols="12"
        lg="8"
      >
        <v-row>
          <v-col
            class="py-0"
          >
            <v-card class='dotplot' v-if="stage_state.show_dotplot1_ang || stage_state.marker == 'dot_seq4' || stage_state.marker == 'dot_seq4a'">
              <jupyter-widget :widget="viewers.dotplot_viewer_ang"/>
            </v-card>
            <v-btn
              v-if="show_team_interface"
              color="success"
              class="black--text"
              @click="update_distances()"
            >
              calculate distances
            </v-btn>
          </v-col>
        </v-row>
      </v-col>
    </v-row> -->
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

</style>


<script>

module.exports = {
  methods: {
    scrollIntoView: function(entries, observer, isIntersecting) {
      if (isIntersecting) {
        entries[0].target.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }
    }
  }
}

</script>
