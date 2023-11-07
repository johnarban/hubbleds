<!-- this state.marker = 'two_his1' -->
<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Student Histogram vs. Class Histogram"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
    :state="state"
  >
    <div
      class="mb-4"
    >
      <p>
        Another data set to explore are the age values measured by All Students who have completed this Data Story. 
      </p>
      <p>
        Notice how the All Students histogram (top) differs from the All Classes histogram (bottom).
      </p>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
  props: ['state']
}
</script>
