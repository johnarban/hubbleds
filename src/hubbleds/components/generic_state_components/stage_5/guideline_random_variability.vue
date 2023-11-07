<template>
  <scaffold-alert
    title-text="Random Variability"
    @next="state.marker_forward = 1"
    :allow-back="false"
  >
    <div
      class="mb-4"
    >
      <p>
        Due to the shortcomings you just considered, your age estimate may or may not reflect the "true" age of the universe, especially since you have a pretty small sample of only 5 galaxies. It might help to explore data from your classmates and others who have completed this Data Story.  
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
