<template>
  <scaffold-alert
      class="mb-4 mx-auto"
      color="info"
      elevation="6"
      max-width="800"
      title-text="Velocity Calculation"
      :can-advance="(state) => state.velocities_total === 5"
      next-text="stage 2"
      :state="state"
      @back="() => { state.marker_backward = 1; }"
      @next="() => { state.completed = true; }"
  >
    <template #before-next>
      Click <v-btn icon tile dark x-small disabled class="mx-1" elevation="2" style="background-color: #0277BD; border-radius: 5px;"><v-icon style="color:white!important;">mdi-run-fast</v-icon></v-btn> button
    </template>

    <div
        v-if="state.velocities_total < 5"
        class="mb-4"
    >
      <p>
        Since you've already seen how to use the Doppler equation, click the
        <v-btn icon tile dark x-small disabled class="mx-1" elevation="2" style="background-color: #0277BD; border-radius: 5px;"><v-icon style="color:white!important;">mdi-run-fast</v-icon></v-btn>
        icon in the table header to have the velocities of your galaxies calculated.
      </p>
    </div>
    <div
        v-if="state.velocities_total === 5"
        class="mb-4"
    >
      <p>Great work! You have completed Stage 1. Proceed to Stage 2.</p>
    </div>
  </scaffold-alert>
</template>


<style>

.JaxEquation .MathJax {
  margin: 16px auto !important;
}

</style>

<script>
module.exports = {
  props: ['state']
}
</script>
