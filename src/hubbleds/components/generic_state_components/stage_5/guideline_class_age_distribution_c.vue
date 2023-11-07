<template>
  <scaffold-alert
    title-text="Class Age Distribution"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
  >
    <div
      class="mb-4"
    >
      <p>
        Here is a histogram showing the age values measured by all classes so far.
      </p>
      <p>
        You can use this histogram to identify a most likely age and confidence interval based on this larger data set, like you did earlier with your class's data. 
      </p>
      <p>
        Explore the mean, median, and mode, and the different inner percentage ranges for the All Classes dataset. 
      </p>
    </div>
  </scaffold-alert>
</template>

<style>
  .JaxEquation .MathJax {
    margin: 3px auto !important;
  }
</style>

<script>
module.exports = {
  props: ['state']
}
</script>
