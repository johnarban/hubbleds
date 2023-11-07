<template>
  <v-dialog
      v-model="state.mmm_dialog"
      persistent
      max-width="1000px"
  >
    <template v-slot:activator="{ on, attrs }">
      <v-btn
        class="my-2"
        block
        color="secondary"
        elevation="2"
        id="mmm-button"
        @click.stop="() => { 
          state.mmm_dialog = true; 
          state.mmm_dialog_opened = true
          }"
      >
        Mean, Median, Mode
      </v-btn>
    </template>
    <v-card
      class="mx-auto"
      ref="content"
    >
      <v-toolbar
        color="secondary"
        dense
        dark
      >
        <v-toolbar-title
          class="text-h6 text-uppercase font-weight-regular"
        >
          {{ state.mmm_state.titles[state.mmm_state.step] }}
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <speech-synthesizer
          :root="() => this.$refs.content.$el"
          :selectors="['div.v-toolbar__title', 'div.v-card__text.black--text', 'h3', 'p']"
          />
        <v-btn
          icon
          @click="() => { 
          state.mmm_dialog = false;
          state.mmm_dialog_complete = (state.mmm_state.step == (state.mmm_state.length-1) );
          }"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-toolbar>

        <v-window
          v-model="state.mmm_state.step"
          style="height: 70vh;"
          class="overflow-auto"
        >

        <v-window-item :value="0" class="no-transition">
          <v-card-text>
            <v-container>
              <v-row
              >
                <v-col 
                  cols="6"
                  style="align-content:center!important; justify-content:center!important" 
                >
                  <div class="ma-4">
                    <p>
                      The <strong>MODE</strong> is the <em>most</em> commonly measured value
                    </p>
                    
                  </div>
                </v-col>
                <v-col
                  cols="6"
                >
                  <div>
                    <p>
                      Image of distribution  with median pointed out
                    </p>
                    <v-img
                      class="mb-4 mx-a mt-n3 image-fit"
                      alt="Cartoon image of the Universe and a birthday cake with a question mark candle."
                      src="./mode.png"
                    ></v-img>
                    <div>
                      <cite class="text-center mt-2 grey--text">
                        <p>
                      Image of distribution  with mode pointed out
                    </p>
                      </cite>
                    </div>
                  </div>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
        </v-window-item>
        <v-window-item :value="1" class="no-transition">
          <v-card-text>
            <v-container>
              <v-row
              >
                <v-col 
                  cols="6"
                  style="align-content:center!important; justify-content:center!important" 
                >
                  <div class="ma-4">
                    <p>
                      The <strong>MEAN</strong> is the average of all values in the dataset. 
                    </p>
                    
                  </div>
                </v-col>
                <v-col
                  cols="6"
                >
                  <div>
                    <p>
                      Image of distribution  with mode pointed out
                    </p>
                    <v-img
                      class="mb-4 mx-a mt-n3 image-fit"
                      alt="Cartoon image of the Universe and a birthday cake with a question mark candle."
                      src="./mean.png"
                    ></v-img>
                    <div>
                      <cite class="text-center mt-2 grey--text">
                        <p>
                      Image of distribution  with mode pointed out
                    </p>
                      </cite>
                    </div>
                  </div>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
        </v-window-item>
        
        <v-window-item :value="2" class="no-transition">
          <v-card-text>
            <v-container>
              <v-row
              >
                <v-col 
                  cols="6"
                  style="align-content:center!important; justify-content:center!important" 
                >
                  <div class="ma-4">
                    <p>
                      The <strong>MEDIAN</strong> is the middle of the dataset. Half the dataset has a smaller value; half has a larger value.
                    </p>
                    
                  </div>
                </v-col>
                <v-col
                  cols="6"
                >
                  <div>
                    <p>
                      Image of distribution  with median pointed out
                    </p>
                    <v-img
                      class="mb-4 mx-a mt-n3 image-fit"
                      alt="Cartoon image of the Universe and a birthday cake with a question mark candle."
                      src="./median.png"
                    ></v-img>
                    <div>
                      <cite class="text-center mt-2 grey--text">
                        <p>
                      Image of distribution  with mode pointed out
                    </p>
                      </cite>
                    </div>
                  </div>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
        </v-window-item>
      </v-window> 
      <v-divider></v-divider>

      <v-card-actions
        class="justify-space-between"
      >
        <v-btn
          :disabled="state.mmm_state.step === 0"
          class="black--text"
          color="accent"
          depressed
          @click="state.mmm_state.step--"
        >
          Back
        </v-btn>
        <v-spacer></v-spacer>
        <v-item-group
          v-model="state.mmm_state.step"
          class="text-center"
          mandatory
        >
          <v-item
            v-for="n in state.mmm_state.length"
            :key="`btn-${n}`"
            v-slot="{ active, toggle }"
          >
            <v-btn
              :input-value="active"
              icon
              @click="toggle"
            >
              <v-icon>mdi-record</v-icon>
            </v-btn>
          </v-item>
        </v-item-group>
        <v-spacer></v-spacer>
          <v-btn
          v-if="state.mmm_state.step < state.mmm_state.length-1"
          color="accent"
          class="black--text"
          depressed
          @click="() => { state.mmm_state.step++; console.log(state.mmm_state.step) }"
        >
          {{ state.mmm_state.step < state.mmm_state.length-1 ? 'next' : '' }}
        </v-btn>
        <v-btn
          v-if = "state.mmm_state.step == state.mmm_state.length-1"
          color="accent"
          class="black--text"
          depressed
          @click="() => { $emit('close'); state.mmm_dialog = false; state.mmm_state.step = 0; state.mmm_dialog_complete = true }"
        >
          Done
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>


<script>
module.exports = {
  props: ['state'],
};
</script>
