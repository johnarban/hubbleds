<!-- # multiple choice -->
<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    header-text="Congratulations!"
    @back="state.marker = 'pro_dat9'"
    :can-advance="(_state) => false"
  >
    <div
      class="mb-4"
    >
    <p>
      You have completed the Hubble Data Story with {{ story_state.total_score}} <v-icon>mdi-piggy-bank</v-icon> points. Nice work!
    </p>
    <p>
      You may be wondering "So what's the <strong>right</strong> answer?"
    </p>
    <p>
      <strong>There is no right answer.</strong> The Universe doesn’t come with an answer key. There are only results which you may have more or less confidence in.
    </p>
    <p>
      Science is always moving forward and there is always more humans can learn about our universe. Follow NASA to learn what new discoveries are being made by HST's successor, the James Webb Space Telescope!
    </p>
  </scaffold-alert>
</template>

<script>
module.exports = {
 props: ['state', 'story_state']
}
</script>
