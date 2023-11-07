<template>
  <scaffold-alert
    @back="() => { state.marker_backward = 1; }"
    @next="() => { $emit('stage_complete'); }"
    :can-advance="(state) => !(state.has_bad_velocities || state.has_multiple_bad_velocities)"
    next-text="stage 2"
    :state="state"
  >
  <template #before-next>
      Remeasure the wavelength.
    </template>
    <div>
      <p>Great work! You have completed Stage 1. Proceed to Stage 2.</p>
    </div>
    <v-card
      v-if="state.has_bad_velocities || state.has_multiple_bad_velocities"
      color="warning"
      >
      <v-card-text>
        <strong>Warning:</strong>You seem to have some bad measurements. Please review your measurements and try again. If you don't see an issue, ask your teacher for help.
      </v-card-text>
    </v-card>
  </scaffold-alert>
</template>


<script>
module.exports = {
 props: ['state']
}
</script>
