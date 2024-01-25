<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Angular Size Measurement"
    @back="state.marker = 'ang_siz3'"
    @next="state.marker = 'ang_siz5'"
    :can-advance="(state) => state.n_meas > 0"
    :state="state"
  >
    <template #before-next>
      <span v-if="!state.bad_angsize">
        Measure angular size of galaxy
      </span>
      <span v-if="state.bad_angsize">
        <strong>Remeasure angular size</strong>
        <br/>
      </span>
    </template>

    <div
      class="mb-4"
    >
    <p>
        Click on one edge of your galaxy to mark the ruler's starting point.
      </p>
      <p>
        Move the cursor to the other edge of your galaxy and click again.
      </p>
      <p>
        If you want to adjust your measurement, you can click on the ends of the green line and move them to a new location.
      </p>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
 props: ['state']
}
</script>
