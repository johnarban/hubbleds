<template>
  <scaffold-alert
    title-text="Select Best Value"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
    :can-advance="(state) => state.two_hist4_response"
    :state="state"
  >
    <div
      class="mb-4"
    >
      <p>
        Based on the histogram and percentage ranges you explored, what can you conclude about the amount of uncertainty present in the age of the universe as measured by any one student compared with the age measured by any one class? 
        
      </p>
        <mc-radiogroup
          :radio-options="[
            'The uncertainty in the age measured by one student is the same as the uncertainty in the age measured by one class.',
            'The uncertainty in the age measured by one student is smaller than the uncertainty in the age measured by one class.',
            'The uncertainty in the age measured by one student is larger than the uncertainty in the age measured by one class.'
          ]"
          :feedbacks="['Not quite. Different ranges (and inner percentage ranges) in a distribution usually indicates different levels of uncertainty in a measurement. Try again.',
              'Not quite. Generally, the larger the range (and inner percentage range) of a distribution, the more uncertainty there is in a measurement. Try again.',
              'Correct. Generally, the smaller the range (and inner percentage ranges) of a distribution, the less uncertainty there is in a measurement.']"
          :incorrect-answers="[0,1]"
          :correct-answers="[2]"
          :neutral-answers="[]"
          @select="(state) => { if (state.correct) { $emit('ready'); } }"
          score-tag="unc-range-change"
        >
        </mc-radiogroup>
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
