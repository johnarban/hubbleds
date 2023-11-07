<template>
  <scaffold-alert
    title-text="Most Likely Value"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
  >
    <div
      class="mb-4"
    >
      <p>
        Click the switches to display each quantity as a vertical line in the histogram. 
      </p>
      <p>
        Click <v-icon>mdi-help-circle-outline</v-icon> to learn more about each quantity.
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
