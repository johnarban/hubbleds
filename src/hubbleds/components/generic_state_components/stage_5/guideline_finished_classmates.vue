<template>
  <scaffold-alert
    title-text="Finished Classmates"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
  >
    <div
    >
      <p>
        Note: "Your class" refers to you and the {{ state.class_data_size - 1 }} others who have completed their measurements (and might not represent your entire class). To avoid confusion, we will <strong>not</strong> add new measurements as they come in, so you may obtain different results from classmates who complete their measurements after you.
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
