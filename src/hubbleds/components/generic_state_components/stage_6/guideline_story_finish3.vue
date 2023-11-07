<template>
  <scaffold-alert
    @back="state.marker_backward = 1"
    :can-advance="(_state) => false"
  >
    <div
      class="mb-4"
    >
    <p>
      Thank you so much for pilot testing the Hubble Data Story. Please complete this final survey.
    </p>
            <v-btn
              block
              class="black--text"
              color="accent"
              elevation="2"
              target="_blank"
              href='https://harvard.az1.qualtrics.com/jfe/form/SV_08L8G4zPV0O5JVc'
            >
              <strong>survey</strong>
            </v-btn>
  </scaffold-alert>
</template>

<script>
module.exports = {
 props: ['state']
}
</script>
