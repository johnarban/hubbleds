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
    :can-advance="(state) => state.two_hist3a_response"
    :state="state"
  >
    <div
      class="mb-4"
    >
      Perhaps even more important than the range of ages is <strong>how those ages are distributed</strong>. If most of the measurements are bunched closely together, that gives us more confidence than
      if they are spread across a large range of values or are bunched around multiple values. As with the dot plots you saw earlier, more <strong>consensus</strong> in measurements generally gives us more <strong>confidence</strong> in a result.
      <v-container
        class="px-0"
        fluid
      >
        <p>How would you describe the distribution of age measurements for these histograms?</p>
        <mc-radiogroup
          :radio-options="[
            'The distribution for the student and class age measurements look similar to each other.',
            'The distribution for the student measurements are more concentrated around a central value than the class measurements.',
            'The distribution for the class measurements are more concentrated around a central value than the student measurements.'
          ]"
          :feedbacks="[
            'Not quite. One histogram looks more like a spike, while the other looks more like a bell. Which is which?',
            'Not quite. One histogram looks more like a spike, while the other looks more like a bell. Which is which?',
            'That\'s right. The student histogram looks more like a bell, while the class histogram looks more like a spike, so there is more consensus within the class age measurements.',
          ]"
          :correct-answers="[2]"
          :wrong-answers='[0,1]'
          @select="(state) => { if (state.correct) { $emit('ready'); } }"
          score-tag="histogram-distribution"
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
