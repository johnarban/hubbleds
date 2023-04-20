<template>
  <guideline-professional-data
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Professional Data"
    prev-marker="pro_dat0"
    next-marker="pro_dat2"
    :state="state"
    v-slot:default="{ allowAdvancing }"
    :index="1"
  >
    <div
      class="mb-4"
    >
    <p>
      Edwin Hubble's own data from 1929 is shown in purple. (Your class's data is shown in blue).
    </p>

    <p>
      Does your class's age estimate agree with Hubble's age estimate? It might help to display the best fit lines.
    </p>

    <v-container
        class="px-0"
        fluid
      >
        <mc-radiogroup
          :radio-options="[
            'Yes',
            'No',
            'I\'m not sure',
          ]"
          :feedbacks="['Remember, the slope of the line is related to the age measurement from this data. Are the slopes the same?','Correct. The best fit lines for our data and Edwin Hubble\'s data have very different slopes.','The slope of the line is related to the age measurement from this data. Are the slopes the same?']"
          :incorrect-answers="[0]"
          :correct-answers="[1]"
          :neutral-answers="[2]"
          @select="(status) => { if (status.correct) { allowAdvancing(); } }"
          score-tag="pro-dat1"
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
