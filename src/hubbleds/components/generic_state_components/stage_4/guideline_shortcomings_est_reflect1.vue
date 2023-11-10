<template>
  <scaffold-alert
    title-text="Shortcomings in Your Estimate"
    @back="
      state.marker = 'you_age1';
    "
    @next="
      state.marker = 'sho_est2';
    "
  >
    <div
      class="mb-4"
    >
      <p>
        Part of the scientific process is probing at potential weaknesses in your measurement, including the overall methods and execution. Try to identify some shortcomings in the approach this data story takes in the measurement of the age of the universe to this point or any difficulties you had with the process. (What are some reasons you or someone else might question your result?)
      </p>
      <free-response
        outlined
        auto-grow
        rows="2"
        label="Shortcoming #1"
        tag="shortcoming-1"
      ></free-response>
      <free-response
        outlined
        auto-grow
        rows="2"
        label="Shortcoming #2"
        tag="shortcoming-2"
      ></free-response>
      <free-response
        outlined
        auto-grow
        rows="2"
        label="Other Shortcomings"
        hint="(if you can think of any more)"
        tag="other-shortcomings"
        allow-empty="true"
      ></free-response>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
  props: ['state']
}
</script>
