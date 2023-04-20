<template>
  <guideline-professional-data
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    header-text="Professional Data"
    next-marker="pro_dat1"
    :allow-back="false"
    :auto-advance="true"
    :state="state"
    :index="0"
  >
    <div
      class="mb-4"
    >
      Let's now turn to professional astronomers' data and see how that compares to your class's data.
    </div>
  </guideline-professional-data>
</template>

<script>
module.exports = {
 props: ['state']
}
</script>


