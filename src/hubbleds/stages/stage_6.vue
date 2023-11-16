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
        <!-- v-select with all the markers -->
        <v-select
          class="demo_v-select"
          v-model="stage_state.marker"
          :items="stage_state.markers"
          label="Marker"
          outlined
          dense
        />
          <v-chip
            v-for="(marker, index) in stage_state.markers"
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
        Marker: {{ stage_state.marker }}
      </v-col>
    </v-row>
    
                  <!-- Professional Data stage -->
    <v-row
      class="d-flex align-stretch"
          v-if="stage_state.indices[stage_state.marker] <= stage_state.indices['sto_fin3']"
    >
      <v-col
        cols="12"
        lg = "4"
      >
        <guideline-professional-data0
          v-if="stage_state.marker == 'pro_dat0'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"/>
        <guideline-professional-data1
          v-if="stage_state.marker == 'pro_dat1'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.prodata_response = true"
          :state="stage_state"/>
        <guideline-professional-data2
          v-if="stage_state.marker == 'pro_dat2'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.prodata_response = true"
          :state="stage_state"/>
        <guideline-professional-data3
          v-if="stage_state.marker == 'pro_dat3'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.prodata_response = true"
          :state="stage_state"/>
        <guideline-professional-data4
          v-if="stage_state.marker == 'pro_dat4'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.prodata_response = true"
          :state="stage_state"/>
        <guideline-professional-data5
          v-if="stage_state.marker == 'pro_dat5'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"/>
        <guideline-professional-data6
          v-if="stage_state.marker == 'pro_dat6'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.prodata_response = true"
          :state="stage_state"/>
        <guideline-professional-data7
          v-if="stage_state.marker == 'pro_dat7'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.prodata_response = true"
          :state="stage_state"/>
        <guideline-professional-data8
          v-if="stage_state.marker == 'pro_dat8'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"/>
        <guideline-professional-data9
          v-if="stage_state.marker == 'pro_dat9'"
          v-intersect.once="scrollIntoView"
          @ready="stage_state.prodata_response = true"
          :state="stage_state"/>
        <guideline-story-finish
          v-if="stage_state.marker == 'sto_fin1'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"/>
        <guideline-story-finish2
          v-if="stage_state.marker == 'sto_fin2'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"/>
        <guideline-story-finish3
          v-if="stage_state.marker == 'sto_fin3'"
          v-intersect.once="scrollIntoView"
          :state="stage_state"/>

      </v-col>
      <v-col
        cols="12"
        lg="8"
      >
        <v-row>
          <v-col cols="3">
            <v-card
              color="#385F73"
            >
              <py-layer-toggle/>
            </v-card>
          </v-col>
          <v-col>
            <v-card
              :color="'black'"
              :class="'pa-0'"
              outlined
            >
              <v-lazy>
            <jupyter-widget :widget="viewers.prodata_viewer"/>
              </v-lazy>
            </v-card>
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
  fill: #F002 !important;
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
