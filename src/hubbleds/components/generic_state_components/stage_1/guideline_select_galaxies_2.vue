<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Select Your Galaxies"
    @back="() => { state.marker_backward = 1; }"
    :can-advance="(_state) => false"
    :state="state"
  >

    <template #before-next>
      <div>
        <div
          v-if="state.gals_total < 5 && state.gals_total > 0"
          style="font-size: 16px;"
        >
        <strong>Select</strong> {{ 5 - state.gals_total }} <span v-if="state.gals_total > 0">more</span> <span v-if="state.gals_total < 4">galaxies</span><span v-if="state.gals_total == 4">galaxy</span>.
        </div>
        <div
          v-if="state.gals_total == 0 && !state.gal_selected"
          style="font-size: 16px;"
        >
        <strong>Click</strong> on any green dot.
        </div>
        <div
          v-if="state.gals_total == 0 && state.gal_selected"
          style="font-size: 16px;"
        >
          <strong>Click</strong> <v-btn icon dark x-small disabled class="mx-1 black--text" elevation="2" style="background-color: #00E676;"><v-icon style="color:black!important;">mdi-plus</v-icon></v-btn> to add galaxy or <v-btn icon dark x-small disabled class="mx-1 black--text" elevation="2" style="background-color: #00E676;"><v-icon style="color:black!important;">mdi-cached</v-icon></v-btn> to choose another
        </div>
      </div>
    </template>

    <div
      v-if="state.gals_total == 0 && !state.gal_selected"
      class="mb-4"
    >
      <p>
        The green dots in the Cosmic Sky Viewer mark the locations of galaxies you can collect data for. 
      </p>
      <p>
        Pan around the sky and click on one of these dots to select that galaxy.
      </p>
    </div>
    <div
      v-if="state.gals_total < 5 && state.gal_selected"
    >
      <p>
        If this galaxy looks good to you, click <v-btn icon dark x-small disabled class="mx-1 black--text" elevation="2" style="background-color: #00E676;"><v-icon style="color:black!important;">mdi-plus</v-icon></v-btn> to add it to your data set.
      </p>
      <p>
        If you’d rather look for another galaxy, click <v-btn icon dark x-small disabled class="mx-1 black--text" elevation="2" style="background-color: #00E676;"><v-icon style="color:black!important;">mdi-cached</v-icon></v-btn> to reset the view and choose a different green dot.
      </p>
    </div>
  </scaffold-alert>
</template>

<script>
module.exports = {
 props: ['state']
}
</script>
