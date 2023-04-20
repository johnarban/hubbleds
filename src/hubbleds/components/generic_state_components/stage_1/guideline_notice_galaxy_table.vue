<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Table Data"
    @back="() => { state.marker_backward = 1; }"
    @next="() => { state.marker_forward = 1; }"
  >
    <div
      class="mb-4"
    >
      <p>
        Notice that your table now has a row for your selected galaxy, and the marker on your galaxy has changed from green to yellow.
      </p>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
 props: ['state']
}
</script>
