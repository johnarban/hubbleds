<template>
  <scaffold-alert
    title-text="Check Measurement"
    @back="() => { state.marker_backward = 1; }"
    @next="() => { state.marker_forward = 1; }"
    :can-advance="(state) => state.dot_seq8_q"
    :state="state"
  >
    <template #before-next>
      Choose a response
    </template>
    <div>
      <p>
        Based on this graph do you think there is <strong>consensus</strong> on the velocity of this galaxy?
      </p>
      <mc-radiogroup 
          :radio-options="[
            'Yes',
            'No',
            'I am not sure',
            ]"
            :feedbacks="[
            'Try again. Make sure you zoom in to where most of the data points are and see if they are clustered around more than one velocity value.',
            'Correct. When we exclude outliers, we see that measurements are clustered around more than one velocity value.',
            'Consider only the range of values that excludes outliers. If measurements are clustered around a single velocity value, there is consensus. If they are clustered around multiple values, there is not consensus.'
            ]" 
          :correct-answers="[1]"
          :neutral-answers="[0, 2]"
          @select="(opt) => { if (opt.correct) { console.log('correct'); $emit('ready'); } }"
          score-tag="vel_meas_consensus">
            >
          </mc-radiogroup>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
 props: ['state']
}
</script>
