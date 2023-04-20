<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto angsize_alert"
    max-width="800"
    elevation="6"
    title-text="Estimate Age of Universe"
    @back="state.marker = 'age_uni3'"
    @next="state.marker = 'you_age1'"
  >
    <div
      class="mb-4"
      v-intersect="(entries, _observer, intersecting) => { if (intersecting) { MathJax.typesetPromise(entries.map(entry => entry.target)) }}"
    >
      <p class="mb-4">
        You entered:
      </p>
      <v-card
        class="JaxEquation pa-3 entered-card"
        color="info lighten-1"
        elevation="0"
      >
        {{ youEnteredMJax(state.hypgal_distance, state.hypgal_velocity) }}
      </v-card>    
      <p class="mt-4">
        Dividing through gives an estimated age of the universe from your dataset:
      </p>
      <div
        class="JaxEquation my-8 est-age"
      >
        {{ estAgeMJax(state.hypgal_distance, state.hypgal_velocity) }}
      </div>
      <v-divider role="presentation" class="mt-3"></v-divider>
      <v-card
        outlined
        class="legend mt-8"
        color="info"
      >
        <v-container>
          <v-row
            no-gutters
          >
            <v-col>
              <div
                class="JaxEquation"
              >
                $$ t \text{ (in Gyr)}= {{ Math.round(state.age_const) }}  \times \frac{d \text{ (in Mpc)}}{v \text{ (in km/s)}} $$
              </div>
            </v-col>
          </v-row>
          <v-divider></v-divider>
          <v-row
            no-gutters
            class="my-1"
          >
            <v-col
            >
              \(t\)
            </v-col>
            <v-col
              cols="10"
            >
              age of the universe, in Gyr. (1 Gyr = 1 billion years)
            </v-col>
          </v-row>
          <v-row
            no-gutters
            class="my-1"
          >
            <v-col
              cols="2"
            >
              \(d\)
            </v-col>
            <v-col
              cols="10"
            >
              distance the galaxy has traveled (distance to the galaxy, in Mpc)
            </v-col>
          </v-row>
          <v-row
            no-gutters
            class="my-1"
          >
            <v-col
              cols="2"
            >
              \(v\)
            </v-col>
            <v-col
              cols="10"
            >
              velocity of the galaxy (in km/s)
            </v-col>
          </v-row>
        </v-container>
      </v-card>
    </div>
  </scaffold-alert> 
</template>

<style>

.JaxEquation .MathJax {
  margin: 16px auto !important;
}

mjx-mfrac {
  margin: 0 4px !important;
}

mjx-mstyle {
  border-radius: 5px;
}

.angsize_alert .v-alert {
  font-size: 16px !important;
}

.v-application .legend {
  border: 1px solid white !important;
  max-width: 300px;
  margin: 0 auto 0;
  font-size: 15px !important;
}

#gal_ang_size {
  color:  black;
  font-size: 18px;
  font-family: "Roboto", Arial, Helvetica, sans-serif;
  padding: 3px;
}

</style>

<script>
module.exports = {
  props: ['state'],
  data() {
    return {
      enteredJax: this.youEnteredMJax(this.state.hypgal_distance, this.state.hypgal_velocity),
      ageJax: this.estAgeMJax(this.state.hypgal_distance, this.state.hypgal_velocity)
    }
  },
  methods: {
    youEnteredMJax(distance, velocity) {
      return `$$ t = ${Math.round(this.state.age_const)}  \\times \\frac{\\textcolor{black}{\\colorbox{#FFAB91}{ ${distance.toFixed(0)} } } \\text{ Mpc} } { \\textcolor{black}{\\colorbox{#FFAB91}{ ${velocity.toFixed(0)} } }  \\text{ km/s} }  \\text{   Gyr}$$`
    },
    estAgeMJax(distance, velocity) {
      return `$$ D = ${Math.round(this.state.age_const * distance / velocity).toFixed(0)} \\text{ Gyr} $$`;
    },
    removeMathJax(container) {
      container.querySelectorAll("mjx-container").forEach(el => container.remove(el));
    },
    resetMathJax(containers, newJax) {
      containers.forEach((container, index) => {
        container.textContent = newJax[index];
        this.removeMathJax(container);
      });
      MathJax.typesetPromise(containers);
    },
    resetAllMathJax(distance, velocity) {
      const containers = [".entered-card", ".est-age"].map(sel => this.$el.querySelector(sel));
      const newJax = [this.youEnteredMJax(distance, velocity), this.estAgeMJax(distance, velocity)];
      this.resetMathJax(containers, newJax);
    }
  },
  watch: {
    'state.hypgal_distance': {
      handler(distance) {
        this.resetAllMathJax(distance, this.state.hypgal_velocity);
      }
    },
    'state.hypgal_velocity': {
      handler(velocity) {
        this.resetAllMathJax(this.state.hypgal_distance, velocity);
      }
    }
  }
}
</script>
