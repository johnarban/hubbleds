<template>
  <!-- add persistant to prevent closing by clicking out -->
  <v-dialog
      v-model="dialog"
      max-width="1000px"
  >
    <template v-slot:activator="{ on, attrs }">
      <v-btn
        class="my-2"
        block
        color="secondary"
        elevation="2"
        id="slideshow-button"
        @click.stop="() => { dialog = true; }"
      >
        Dot Plot Tutorial
      </v-btn>
    </template>
    <v-card
      class="mx-auto"
      ref="content"
    >
      <v-toolbar
        color="secondary"
        dense
        dark
      >
        <v-toolbar-title
          class="text-h6 text-uppercase font-weight-regular"
        >
          {{ currentTitle }}
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <speech-synthesizer
          :root="() => this.$refs.content.$el"
          :autospeak-on-change="step"
          :speak-flag="dialog"
          :selectors="['div.v-toolbar__title', 'div.v-card__text.black--text', 'h3', 'p']"
          />
        <v-btn
          icon
          @click="closeDialog()"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-toolbar>

        <v-window
          v-model="step"
          class="overflow-auto"
        >
        <v-row>
          <v-col
            cols="12"
            lg="5"
            >
            
            <v-window-item :value="0" class="no-transition">
              <v-card-text>
                <v-container>
                  <p>
                    This <strong>dot plot</strong> displays&#8212;as a dot&#8212;every velocity measurement in our sample (excluding yours for now).
                  </p>
                  <p>
                    Dots are stacked within velocity <strong>ranges</strong> called <strong>bins</strong>.
                  </p>
                  <p>
                    The horizontal axis shows the measured velocity values.
                  </p>
                  <p>
                    The vertical axis shows how many measurements were made in a particular velocity bin.
                  </p>
                </v-container>
              </v-card-text>
            </v-window-item>

            <v-window-item :value="1" class="no-transition">
              <v-card-text>
                <v-container>
                  <p>
                    As with the spectrum viewer, if you move your mouse left and right within the dot plot, the vertical marker will display the velocity value for the center of each bin.
                  </p>
                </v-container>
              </v-card-text>
            </v-window-item>

            <v-window-item :value="2" class="no-transition">
              <v-card-text>
                <v-container>
                  <p>
                    Our data sample includes a very large range of velocity values, but most of the data points are clustered in one or more tall towers of dots between 9,000 to 13,000 km/s. 
                  </p>
                  <p>
                    Let's take a closer look at this cluster of measurements. 
                  </p>
                  <p>
                    Click <v-icon>mdi-select-search</v-icon> in the toolbar to activate the zoom tool.
                  </p>                    
                  <p>
                    Then click and drag across the cluster of velocity measurements to zoom in.
                  </p>
                </v-container>
              </v-card-text>
            </v-window-item>

            <v-window-item :value="3" class="no-transition">
              <v-card-text>
                <v-container>
                  <p>
                    You should see that the tall towers of dots have split into smaller towers. If not, zoom in closer by clicking and dragging again, or click <v-icon>mdi-cached</v-icon> to reset the view and try again.
                  </p>
                  <p>
                    This happens because each tower of dots represents a <strong>range</strong> of velocity values. When you zoomed in, the data were rebinned across smaller velocity ranges.
                  </p>
                  <p>
                    That's all you need to know about dot plots for now. Click done to continue.  
                  </p>                      
                </v-container>
              </v-card-text>
            </v-window-item>  
          </v-col>
          <v-col
            cols="12"
            lg="7"
          >
           <jupyter-widget :widget="dotplot_viewer"/>
          </v-col>
        </v-row>
      </v-window>
      
      <v-divider></v-divider>

      <v-card-actions
        class="justify-space-between"
      >
        <v-btn
          :disabled="step === 0"
          class="black--text"
          color="accent"
          depressed
          @click="step--"
        >
          Back
        </v-btn>
        <v-spacer></v-spacer>
        <v-item-group
          v-model="step"
          class="text-center"
          mandatory
        >
          <v-item
            v-for="n in length"
            :key="`btn-${n}`"
            v-slot="{ active, toggle }"
          >
            <v-btn
              :input-value="active"
              icon
              @click="toggle"
            >
              <v-icon>mdi-record</v-icon>
            </v-btn>
          </v-item>
        </v-item-group>
        <v-spacer></v-spacer>
          <v-btn
          v-if="step < length-1"
          color="accent"
          class="black--text"
          depressed
          @click="() => { step++; }"
        >
          {{ step < length-1 ? 'next' : '' }}
        </v-btn>
        <v-btn
          v-if = "step == length-1"
          color="accent"
          class="black--text"
          depressed
          @click="() => { $emit('close'); dialog = false; step = 0; finished = true }"
        >
          Done
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  
  watch: {
    step(newStep) {
      this.maxStepCompleted = newStep;

      if (newStep == 1) {
        this.activateMeasuringTool();
      }

      if (newStep == 2) {
        this.activate_zoom_tool();
        this.home_add_line();
      }

      if (newStep == 3) {
        this.activate_selector();
        this.home_add_previous_line()
      }
    },
  },

  methods: {
    closeDialog() {
        this.$emit('close');
        this.dialog = false;
        if (this.step == this.length - 1) {
          this.step = 0;
      }
    }
  }

  
};

</script>

<style scoped>
.no-transition {
  transition: none;
}

.row {
  width: 100%;
  margin-left: 0 !important;
  margin-right: 0 !important;
}
</style>
