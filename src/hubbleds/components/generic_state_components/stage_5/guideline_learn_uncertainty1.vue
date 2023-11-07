<!-- this state.marker = 'lea_unc1' -->
<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Learn About Uncertainty"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
    :can-advance="(state) => state.uncertainty_dialog_complete"
    :state="state"
  >
   
    <template #before-next>
      Click <span style="background-color: #02838f; border-radius : 5px; padding: 3px; color:white!important;">UNCERTAINTY TUTORIAL</span> button.
    </template>

    <div
      class="mb-4"
    >
      <p>
        Before we go further, let's explore in more detail <strong>why</strong> different students may have obtained different age values for the universe.
      </p>
      <p>
        Scientists explain this using a concept called <strong>uncertainty</strong>. Click the <span style="background-color: #02838f; border-radius : 5px; padding: 3px; color:white!important;">UNCERTAINTY TUTORIAL</span> button to learn about this important concept for interpreting data.
      </p>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
  props: ['state']
}
</script>
