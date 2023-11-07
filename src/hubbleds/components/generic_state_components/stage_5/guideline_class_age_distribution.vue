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
        First, it is helpful to visualize the data in a different way. 
      </p>
      <p>
        This is a <strong>histogram</strong>, which displays the distribution of your classmates' age estimates for the universe. The <strong>range</strong> of age values is shown on the <strong>x-axis</strong>, and the number <strong>count</strong> of students who measured that value for the age of the universe is shown on the <strong>y-axis</strong>.
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
