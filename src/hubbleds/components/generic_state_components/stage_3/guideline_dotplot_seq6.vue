<template>
  <scaffold-alert
    title-text="Second Measurement Comparison"
    @back="state.marker = 'dot_seq5c'"
    @next="state.marker = 'dot_seq7'"
    :can-advance="(state) => state.dot_seq6_q"
    :state="state"
    >
      <template #before-next>
        Choose a response
      </template>
    
    <div class="mb-4">
      <p>
        In the upper graph we show the distribution of first measurements as you saw earlier.
      </p>
      <p>
        In the lower graph, we show the distribution of second distance measurements. Yours are again marked in red-orange.
      </p>
      <p>
        Based on these two histograms, which set of measurements shows better consensus on the distance to the galaxy?
      </p>
      <mc-radiogroup
        :radio-options="[
          'The first set of measurements',
          'The second set of measurements',
          'I am not sure',
          ]"
        :feedbacks="[
          'Not quite. Consider which dot plot has measurements that cluster around fewer common values.',
          'Correct. The second set of measurements clusters around fewer common values',
          'Consider which dot plot has measurements that cluster around fewer common values.'
          ]"
        :correct-answers="[1]"
        :neutral-answers="[0, 2]"
        @select="(opt) => { if (opt.correct) { console.log('correct'); $emit('ready') } }"
        score-tag="ange_meas_consensus_2">
      </mc-radiogroup>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
