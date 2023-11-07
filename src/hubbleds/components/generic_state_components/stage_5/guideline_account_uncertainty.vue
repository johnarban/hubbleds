<!-- this state.marker = 'acc_unc1' -->
<template>
  <scaffold-alert
    title-text="Accounting for Uncertainty"
    next-text="stage 6"
    @back="state.marker_backward = 1"
    @next="() => {$emit('stage_complete');}"
  >
    <div
      class="mb-4"
    >
      <p>
        Everything we just discussed refers to random uncertainties.
      </p>
      <p>
        Recall from the Uncertainty Tutorial that there is also something called systematic uncertainty, where if you have any bias in your methods or assumptions, your whole range of measured ages would be slightly too high or too low.
      </p>
      <p>
        Figuring out and accounting for all the sources of systematic uncertainty is one of the most difficult and most important tasks in a scientific experiment. With our limited time, we will note that our age measurements might be affected by systematic uncertainty and leave it at that.
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
