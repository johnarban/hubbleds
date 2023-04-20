<!-- # multiple choice -->
<template>
  <scaffold-alert
    color="info"
    class="mb-4 mx-auto"
    max-width="800"
    elevation="6"
    @back="retreat()"
    @next="advance()"
    :allow-back="allowBack"
    :can-advance="(state) => autoAdvance || state.max_prodata_index > index"
    :state="state"
  >
    <template #before-next>
      Choose a response.
    </template>
    <slot
      :advance="advance"
      :allow-advancing="allowAdvancing"
    ></slot>
  </scaffold-alert>
</template>

<script>
module.exports = {
  props: {
    state: {
      type: Object,
      required: true
    },
    index: {
      type: Number,
      required: true
    },
    prevMarker: {
      type: String,
      default: '',
    },
    nextMarker: {
      type: String,
      default: ''
    },
    allowBack: {
      type: Boolean,
      default: true
    },
    autoAdvance: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    retreat() {
      this.state.marker = this.prevMarker;
    },
    allowAdvancing() {
      this.state.max_prodata_index = Math.max(this.state.max_prodata_index, this.index + 1);
    },
    advance() {
      this.allowAdvancing();
      this.state.marker = this.nextMarker;
    }
  }
}
</script>
