<template>
  <scaffold-alert
    title-text="Identify Your Confidence Interval"
    ref="scaffold"
    @back="state.marker_backward = 1"
    @next="() => {
      if (revealIter < 1) {
        revealIter = revealIter + 1;
      }
      else {
        state.marker_forward = 1;
        state.trend_line_drawn = false;
        state.best_fit_clicked = false;
      }
    }"
  >
    <div
      class="mb-4"
    >
      <p>
        After comparing different percentage ranges for your class's age measurements in the histogram, enter your responses below.
      </p>
      <v-row
      >
        <v-col
          cols="12"
          lg="9"
        >
          3. The range of age values for the universe that I am most confident in based on my class’s data set: 
        </v-col>
        <v-col>
          <v-btn
            color="secondary lighten-1"
            @click="state.age_calc_state.hint2_dialog = true"
          >
            hint
            <v-dialog
              v-model="state.age_calc_state.hint2_dialog"
              persistent
              max-width="600px">
              <v-card
                class="mx-auto"
              >
                <v-toolbar
                  color="secondary"
                  dense
                  dark
                >
                  <v-toolbar-title
                    class="text-h6 text-uppercase font-weight-regular"
                  >
                    Hint #2
                  </v-toolbar-title>
                  <v-spacer></v-spacer>
                  <span
                    @click="
                      () => {
                        $emit('close');
                        state.age_calc_state.hint2_dialog = false;
                      }
                    "
                  >
                    <v-btn icon>
                      <v-icon> mdi-close </v-icon>
                    </v-btn>
                  </span>
                </v-toolbar>
                <div class="pa-6">
                  <p>
                    The range you pick will have a tradeoff between how likely it is that the “true” value actually lies within the range you choose vs. having a narrow enough range that your measurement is actually useful. A very large range is more likely to include the "true" value, but may be so nonspecific that it is not useful. A narrow range has more specificity but may not include the "true" value.
                  </p>
                  <p>
                    Different people will feel more or less comfortable with the different sides of this tradeoff, and there isn’t really a right or wrong answer as long as you justify why you chose what you did.
                  </p>
                  <p>
                    If you are feeling really stuck, feel free to discuss this with a classmate or your instructor.
                  </p>
                </div>
              </v-card>
            </v-dialog>
          </v-btn>
        </v-col>
      </v-row>
      <v-row
        v-if="revealIter >= 0"
      >
        <v-col
          cols="12"
          lg="3">
          <free-response
            outlined
            rows="1"
            label="Likely Low Age"
            tag="likely-low-age"
          ></free-response>
        </v-col>
        <v-col
          lg="2">
          Gyr
        </v-col>
              <v-col
          cols="12"
          lg="3">
          <free-response
            outlined
            rows="1"
            label="Likely High Age"
            tag="likely-high-age"
          ></free-response>
        </v-col>
        <v-col
          lg="2">
          Gyr
        </v-col>
      </v-row>

      <v-row
        v-if="revealIter >= 1"
      >
        <v-col>
          4. Explain why you chose your values using information from the histogram or other viewers:
        </v-col>
      </v-row>
      <v-row
        v-if="revealIter >= 1"
      >
        <v-col>
          <free-response
            outlined
            auto-grow
            rows="2"
            label="My Reasoning"
            tag="my-reasoning-2"
          ></free-response>
        </v-col>
      </v-row>


    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
  props: ['state'],
  data() {
    return {
      revealIter: 0
    }
  },
  watch: {
    revealIter(_value) {
      const scaffold = this.$refs.scaffold;
      this.$nextTick(() => {
        scaffold.$refs.next.$el.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      });
    }
  }
}
</script>

