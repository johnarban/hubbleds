<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    @back="() => { state.marker = 'dot_seq12'; }"
    @next="() => { state.marker_forward = 1; }"
    :can-advance="(state) => state.obswaves_total >= 5"
    :title-text="state.obswaves_total < 5 ? 'Repeat for Remaining Galaxies' : 'Nice Work'
    "
    :state="state"
  >
    <template #before-next>
      <span v-if="!state.has_bad_velocities && !state.has_multiple_bad_velocities">
        Measure wavelength<span v-if="state.obswaves_total < 4">s</span> for {{ 5 - state.obswaves_total }} more <span v-if="state.obswaves_total < 4">galaxies</span><span v-if="state.obswaves_total == 4">galaxy</span>.
      </span>
      <span v-if="state.has_bad_velocities || state.has_multiple_bad_velocities">
        <strong>Remeasure observed wavelength</strong>
        <br />
      </span>
    </template>

<!-- If there are no bad measurements and measurements are not complete -->
    <div
      v-if="!state.has_bad_velocities && !state.has_multiple_bad_velocities"
    >
      <div
        class="mb-4"
        v-if="state.obswaves_total == 0"
      >
        Now that you've seen how to measure spectral wavelengths, let's return to the 5 galaxies you selected earlier.
      </div>
      <div
        class="mb-4"
        v-if="state.obswaves_total > 0 && state.obswaves_total < 5"
      >
        Continue measuring spectral wavelengths for your galaxies.
      </div>
      <div
        v-if="state.obswaves_total < 5"
      >
        Click on each galaxy in your table and repeat the spectral line wavelength measurement for each of them.
      </div>
    </div>

    <!-- If there are any bad measurements -->
    <div
      v-if="state.has_bad_velocities || state.has_multiple_bad_velocities"
    >
      <p>
        Your measured wavelength value is not within the expected range. Please try again.
      </p>
      <p>
        Align the vertical measuring tool to the <strong><span style="color:#ff665e; background-color: white; border-radius : 5px; padding: 3px">{{ state.galaxy.element }} (observed)</span></strong> marker and click.
      </p>
      <p>
        Ask your instructor if you are not sure where this is.
      </p>
    </div>
    <!-- If measurements are complete and there are no bad measurements -->
    <div
      v-if="state.obswaves_total >= 5 &&!state.has_bad_velocities && !state.has_multiple_bad_velocities"
    >
      <p>
        You have measured the spectral line wavelengths for all of your galaxies.
      </p>
      <p>
        You can continue to refine your measurements, or, if you are satisfied with your measurements, you can move on.
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
 props: ['state']
}
</script>
