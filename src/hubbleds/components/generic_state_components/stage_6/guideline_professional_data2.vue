<template>
  <guideline-professional-data
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    prev-marker="pro_dat1"
    next-marker="pro_dat4"
    :state="state"
    v-slot:default="{ allowAdvancing }"
    :index="2"
  >
    <div
      class="mb-4"
    >
    <p>Is your age estimate higher than or lower than Hubble's age estimate?</p>
      <v-container
        class="px-0"
        fluid
      >
        <mc-radiogroup
          :radio-options="[
            'Our class got a higher age estimate than Hubble',
            'Our class got a lower age estimate than Hubble.'
          ]"
          :feedbacks="[
            'Correct! Because the slope of the trend in our data is shallower than the trend in Hubble\'s data, our age estimate must be higher ',
            'Remember, the slope of the trend in our data is shallower than the trend in Hubble\'s data, so our age estimate must be higher.'
          ]"
          :correct-answers="[0]"
          @select="(status) => { if (status.correct) { allowAdvancing(); } }"
          score-tag="pro-dat2"
        >
        </mc-radiogroup>
      </v-container>
    </div>
  </guideline-professional-data>
</template>

<script>
module.exports = {
 props: ['state']
}
</script>



