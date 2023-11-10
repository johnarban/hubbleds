<template>
  <scaffold-alert
    title-text="Measurement Comparison"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
    :state="state"
  >
    <div
      class="mb-4"
    >
      <p>
        Below is the distribution of angular size measurements for this galaxy. Notice the angular size measurements also tend to group around more than one value.
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
 props: ['state']
}
</script>
