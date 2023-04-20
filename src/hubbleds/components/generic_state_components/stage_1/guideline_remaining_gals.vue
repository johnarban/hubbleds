<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    @back="() => { state.marker_backward = 1; }"
    @next="() => { state.marker_forward = 1; }"
    :can-advance="(state) => state.obswaves_total >= 5"
    :title-text="state.obswaves_total < 5 ? 'Repeat for Remaining Galaxies' : 'Nice Work'
    "
    :state="state"
  >
    <template #before-next>
      Measure wavelength<span v-if="state.obswaves_total < 4">s</span> for {{ 5 - state.obswaves_total }} more <span v-if="state.obswaves_total < 4">galaxies</span><span v-if="state.obswaves_total == 4">galaxy</span>.
    </template>

    <div
      class="mb-4"
      v-if="state.obswaves_total < 5"
    >
      <p>
        Now that you've seen how to measure spectral wavelengths, let's return to the 5 galaxies you selected earlier.
      </p>
      <p>
        Click on each galaxy in your table and repeat the spectral line wavelength measurement for each of them.
      </p>
    </div>
    <div
      class="mb-4"
      v-if="state.obswaves_total >= 5"
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
