<!-- this state.marker = 'two_his2' -->
<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Student Histogram vs. Class Histogram"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
    :can-advance="(state) => state.two_hist3_response"
    :state="state"
  >
    <div
      class="mb-4"
    >
      Now try comparing the 50%, 68%, and 95% confidence ranges between the two histograms. (The switches will display the same percentage range on both histograms.)
      <v-container
        class="px-0"
        fluid
      >
        <p>What do you notice about the relationship between the histograms? </p>
        <mc-radiogroup
          :radio-options="[
            'All confidence ranges are narrower for the students than the classes.',
            'All confidence ranges are broader for the students than the classes.',
            'Some of the confidence ranges are narrower for the students and some are broader.'
          ]"
          :feedbacks="[
            'Not quite. Look at the percentage confidence ranges reported for each histogram. Try again.',
            'That’s right. The student histogram consistently has a larger confidence range for all percentages.',
            'Not quite. Look at the percentage confidence ranges reported for each histogram. Try again.',
          ]"
          :correct-answers="[1]"
          :wrong-answers='[0,2]'
          @select="(state) => { if (state.correct) { $emit('ready'); } }"
          score-tag="histogram-percent-range"
        >
        </mc-radiogroup>
      </v-container>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
  props: ['state']
}
</script>
