<template>
  <scaffold-alert
    title-text="Select Best Value"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
  >
    <div
      class="mb-4"
    >
    <p>
      Some possibilities are the range that encompass the inner 50%, 68%, or 95% of all measurements.
    </p>
    <p>
      Click the switches to display each percentage range in the histogram. Data points outside the percentage range will be grayed out. 
    </p>
    <p>
      Click <v-icon>mdi-help-circle-outline</v-icon> to learn more about how the percentage ranges are determined.
    </p>

    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
