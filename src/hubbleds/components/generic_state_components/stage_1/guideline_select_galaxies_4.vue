<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    header-text="Example Galaxy"
    @back="() => { state.marker = 'sel_gal3'; }"
    @next="() => { state.marker = 'cho_row1'; }"
    :can-advance="(state) => state.gals_total === 5"
    :state="state"
  >


    <div>
      <p>
        We'll start with an example galaxy so that we can learn how to make good measurements. 
      </p>
      <p>
        Everyone will measure a velocity for the same galaxy.
      </p>
    </div>
  

  </scaffold-alert>
</template>

<script>
module.exports = {
  props: ['state']
}
</script>
