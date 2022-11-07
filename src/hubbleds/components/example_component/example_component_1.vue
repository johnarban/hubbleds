<!-- # multiple choice -->
<template>
  <v-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
  >
    <h3
      class="mb-4"
    >
      <span style="color:red"> Example Component 1</span>
    </h3>
    <div
      class="mb-4"
    >
      This is just an example question. The next button will only appear if the correct answer is given. 
      <v-container
        class="px-0"
        fluid
      >
        <mc-radiogroup
          :radio-options="[
            'option 1 (correct)',
            'option 2 (neutral)',
            'option 3 (wrong)',
          ]"
          :feedbacks="[
            'feedback 1',
            'feedback 2',
            'feedback 3',
          ]"
          :correct-answers="[0]"
          :neutral-answers='[1]'
          :selected-callback="(option) => { if (option.correct) { can_advance = true };  }"
          score-tag="example_tag1"
        >
        </mc-radiogroup>
      </v-container>
    </div>
    
    <v-divider
      class="my-4"
    >
    </v-divider>

    <v-row
      align="center"
      no-gutters
    >
        <v-btn
          class="black--text"
          color="accent"
          elevation="2"
          @click="
              () => {
                state.marker = 'ex_com1';
              }
            "
        >
          back
        </v-btn>
      <v-spacer></v-spacer>
      <v-col
        cols="6"
        class="shrink"
        v-if="!can_advance"
      >
        <div
          style="font-size: 16px;"
        >
          Choose a response.
        </div>
      </v-col>
      <v-col
        class="shrink"
        v-if="can_advance"
      >
        <v-btn
          class="black--text"
          color="accent"
          elevation="2"
          @click="
              () => {
                state.marker = 'ex_com2';
              }
            "
        >
          next
        </v-btn>
      </v-col>
    </v-row>
  </v-alert>
</template>
