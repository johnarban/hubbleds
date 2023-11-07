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
        Listed above are 3 quantities that scientists might calculate from a distribution to determine the <strong>most likely value</strong>.
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
