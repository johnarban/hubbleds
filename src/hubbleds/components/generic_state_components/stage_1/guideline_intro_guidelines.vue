<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Introducing the Guidelines"
    @next="state.marker_forward = 1"
    :allow-back="false"
  >
    <template #back-content>
      <div>
        Open menu to return to earlier stages.<br>
        (Open/close menu with <v-btn icon tile dark x-small disabled class="mx-1" elevation="2" style="background-color: #172c4d; border-radius: 5px;"><v-icon style="color:white!important;">mdi-menu</v-icon></v-btn> above)
      </div>
    </template>
    <div
      class="mb-4"
    >
      <p>
        <strong>These orange boxes will guide you as you move through the story.</strong>
      </p>
      <p>
        The information in the boxes will suggest what you should focus on, or what you should do next.
      </p>
      <p>
        The images, tables, or graph where the guideline suggests action will also be highlighted with an <strong>orange outline</strong>.
      </p>
    </div>
    
  </scaffold-alert>
</template>


<script>
module.exports = {
 props: ['state']
}
</script>
