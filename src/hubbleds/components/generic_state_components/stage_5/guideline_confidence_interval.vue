<template>
  <scaffold-alert
    title-text="Confidence Interval"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
  >
    <div
      class="mb-4"
    >
    <p>
      Other values that were measured by your classmates&mdash;besides the most likely age you just identified&mdash;are also possible. 
    </p>
    <p>
      To account for this, you should specify a likely range of possible age values, or <strong>confidence interval.
    </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
