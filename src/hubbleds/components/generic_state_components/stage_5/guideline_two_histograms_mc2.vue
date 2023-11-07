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
    :can-advance="(state) => state.two_hist_response"
    :state="state"
  >
    <div
      class="mb-4"
    >
      <v-container
        class="px-0"
        fluid
      >
        <p>In comparing the All Students and All Classes histogram, which spans a larger range of ages?</p>
        <mc-radiogroup
          :radio-options="[
            'The histogram of student measurements.',
            'The histogram of class measurements.',
            'The student and class histograms are the same.'
          ]"
          :feedbacks="[
            'That’s right. The student histogram has a larger range.',
            'Not quite. Look at the x-axis for each histogram. Where does the range of values start and end for each histogram? Try again.',
            'Not quite. Look at the x-axis for each histogram. Where does the range of values start and end for each histogram? Try again.'
          ]"
          :correct-answers="[0]"
          :wrong-answers='[1,2]'
          @select="(state) => { if (state.correct) { $emit('ready'); } }"
          score-tag="histogram-range"
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
