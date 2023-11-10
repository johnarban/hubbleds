<!-- # multiple choice -->
<template>
  <guideline-professional-data
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    prev-marker="pro_dat8"
    next-marker="sto_fin1"
    v-slot:default="{ allowAdvancing }"
    :state="state"
    :index="9"
  >
    <div
      class="mb-4"
    >
      <p>
        Why do you think scientists' measurements of the age of the universe have changed with time?
      </p>
      <v-container
        class="px-0"
        fluid
      >
        <mc-radiogroup
          :radio-options="[
              'Scientists do not really know how to measure the age of the universe.',
              'Scientists measure different ages because the universe is always getting older.',
              'The measured age of the universe can change based on new and better data.'
          ]"
          :feedbacks="[
            'It is possible to measure the age of the universe, though it can be difficult to do so.',
            'The universe is always getting older, but scientists measure the age of the universe on scales of billions of years, far greater than time between recent measurements.',
            'Correct! Improved data and technology allow scientists to measure the age of the universe more precisely and with less bias.'
          ]"
          :correct-answers="[2]"
          :neutral-answers='[0,1]'
          @select="(status) => { if (status.correct) { allowAdvancing(); } }"
          score-tag="pro-dat9"
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
