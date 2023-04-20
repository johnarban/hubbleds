<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Choose a Row"
    @back="() => { state.marker_backward = 1; }"
    @next="() => { state.marker_forward = 1; }"
    :can-advance="(state) => state.spec_viewer_reached"
    :state="state"
  >
  <template #before-next>
      Select the example galaxy from your table.
    </template>  
  <div class="mb-4">
      <p>
      For the moment, we have replaced the galaxies in your table with the example galaxy.
      </p>
      <p>
      Click the row containing the example galaxy to select it.
      </p>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
  props: ['state']
}
</script>
