<template>
  <scaffold-alert
    title-text="Most Likely Values"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
  >
    <div
      class="mb-4"
    >
      <p>
        When scientists measure an unknown quantity, they use the available data to determine: 
        <ol>
          <li>the measured value they think is <strong>most likely</strong>, and </li>
          <li>the most plausible range of measured values (called the <strong>confidence interval</strong>). </li> 
        </ol>
      </p>
      <p>
        Let's explore how to do this for your class's measurements.
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
