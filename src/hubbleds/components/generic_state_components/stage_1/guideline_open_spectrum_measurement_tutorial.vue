<template>
  <scaffold-alert
    title-text="Choose a Row"
    @back="() => { state.marker = 'dop_cal5'; }"
    @next="() => { if (state.marker === 'osm_tut') {state.marker = 'smt_tut';} else if (state.marker === 'smt_tut') {state.marker = 'rem_gal1';} }"
    :next-text="state.marker === 'osm_tut' ? 'Open Comparison' : 'Next'"
  >

  <div class="mb-4">
    Now that you have measured the velocity of the example galaxy, 
    let's compare it with existing measurements in our database!
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
  props: ['state']
}
</script>
