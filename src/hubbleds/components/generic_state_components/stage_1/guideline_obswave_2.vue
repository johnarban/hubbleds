<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Observed Wavelength"
    @back="() => { state.marker_backward = 1; }"
    @next="() => { state.marker_forward = 1; }"
    :can-advance="(state) => state.zoom_tool_activated"
    :state="state"
  >
    <template #before-next>
      Click <v-btn icon tile dark x-small disabled class="mx-1" elevation="2" style="background-color: #0277BD; border-radius: 5px;"><v-icon style="color:white!important;">mdi-select-search</v-icon></v-btn> to activate tool. Click and drag across the red <strong>{{ state.galaxy.element }} </strong> marker to zoom in.
    </template>

    <div
      class="mb-4"
    >
      <p
        v-if=!state.zoom_tool_activated>  
        To improve the precision in your measurement, zoom in to the wavelength range around the {{ state.galaxy.element }} line using the <v-btn icon tile dark x-small disabled class="mx-1" elevation="2" style="background-color: #0277BD; border-radius: 5px;"><v-icon style="color:white!important;">mdi-select-search</v-icon></v-btn>  icon in the toolbar.
      </p>
      <p
        v-if=state.zoom_tool_activated>  
        If you accidentally zoom in too far or in the wrong spot, you can click <v-btn icon tile dark x-small disabled class="mx-1" elevation="2" style="background-color: #0277BD; border-radius: 5px;"><v-icon style="color:white!important;">mdi-cached</v-icon></v-btn> to reset the view to the full range of wavelengths.
      </p>
      <p>
        <strong>Tip:</strong> You can re-measure the wavelength as many times as you like. 
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
 props: ['state']
}
</script>
