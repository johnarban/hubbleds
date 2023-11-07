<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    title-text="Hubble's Expanding Universe"
    @back="state.marker = 'rel_vel1'"
    @next="state.marker = 'tre_lin1'"
    :can-advance="(state) => state.hubble_dialog_opened"
    :state="state"
  >
    <template #before-next>
      Click <span style="background-color: #02838f; border-radius : 5px; padding: 3px; color:white!important;">HUBBLE'S DISCOVERY</span> button.
    </template>
    
    <div
      class="mb-4"
    >
      <p>
        The relationship between your galaxies’ velocity and distance is the same as what Hubble found: galaxies at a greater distance away are moving away from us at a higher velocity.
      </p>
      <p>
       Click the <span style="background-color: #02838f; border-radius : 5px; padding: 3px;color:white!important;">HUBBLE'S DISCOVERY</span> button to learn what was significant about this result.
      </p>
    </div>
  </scaffold-alert>
</template>


<script>
module.exports = {
  props: ['state']
}
</script>
