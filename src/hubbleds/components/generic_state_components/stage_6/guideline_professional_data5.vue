<template>
  <guideline-professional-data
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    prev-marker="pro_dat4"
    next-marker="pro_dat6"
    v-slot:default="{ allowAdvancing }"
    :state="state"
    :index="5"
  >
    <div
      class="mb-4"
    >
    <p>
      Now let's consider more modern data from 2001, shown in lime green. 
      This data is from the HST Key Project, led by astronomer Wendy Freedman, who used data from the Hubble Space Telescope to measure a quantity known as the <strong>Hubble constant</strong>
      (which is the inverse of the age value you calculated).
    </p>
    <p> 
      Whose data has the least amount of random uncertainty? (It might help to use the magnifying glass tool to zoom in on the x and y axes).
    </p>
      <v-container
        class="px-0"
        fluid
      >
        <mc-radiogroup
          :radio-options="[
            'Our class',
            'Edwin Hubble',
            'HST Key Project'
          ]"
          :feedbacks="[
            'Try again. ',
            'Try again. ',
            'Correct! The HST Key Project data has the least amount of random uncertainty.'
          ]"
          :correct-answers="[2]"
          :neutral-answers='[0,1]'
          @select="(status) => { if (status.correct) { allowAdvancing(); } }"
          score-tag="pro-dat5"
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
