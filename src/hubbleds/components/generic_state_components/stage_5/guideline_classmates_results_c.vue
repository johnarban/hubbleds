<template>
  <scaffold-alert
    title-text="Classmates' Data"
    @back="state.marker_backward = 1"
    @next="state.marker_forward = 1"
  >
    <div
      class="mb-4"
    >
      <p>
        Now let’s look at age estimates of the universe from other classes who have already completed this data story.
      </p>
      <p>
        Your class's graph is highlighted in blue.
      </p>
      <p>
        Use the slider to scan through the age estimates that each participating class measured. 
      </p>
      <p>
        To exclude outliers, click <v-btn icon tile dark x-small disabled class="mx-1" elevation="2" style="background-color: #0277BD; border-radius: 5px;"><v-icon style="color:white!important;">mdi-select-search</v-icon></v-btn> to zoom in to a smaller velocity or distance range.
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
