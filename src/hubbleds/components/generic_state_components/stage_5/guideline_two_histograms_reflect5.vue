<template>
  <scaffold-alert
    title-text="Select Best Value"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
    :state="state"
  >
    <div
      class="mb-4"
    >
      <p>
        The smoother, less clustered distribution for the All Students data tells us that an age value measured by one student has more uncertainty than an age value measured by a single class.
      </p>
      <p>
        Explain why you think this might be true.
      </p>

          <free-response
            outlined
            auto-grow
            rows="2"
            label="My Reasoning"
            tag="unc-range-change-reasoning"
          ></free-response>
    </div>
    <v-btn
      color="secondary lighten-1"
      @click="state.uncertainty_hint_dialog = true"
    >
      hint
      <v-dialog
        v-model="state.uncertainty_hint_dialog"
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
              Hint
            </v-toolbar-title>
            <v-spacer></v-spacer>
            <span
              @click="
                () => {
                  $emit('close');
                  state.uncertainty_hint_dialog = false;
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
              Recall that each student used 5 galaxies to measure the age of the universe, while each class used ~100-150 galaxies. Why might this lead to a smaller uncertainty for a single class compared with a single student?
            </p>
          </div>
        </v-card>
      </v-dialog>
    </v-btn>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
