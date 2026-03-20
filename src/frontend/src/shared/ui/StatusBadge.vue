<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  tone: {
    type: String,
    default: 'neutral',
  },
})

const badgeClass = computed(() => `status-badge status-badge--${props.tone}`)
</script>

<template>
  <span :class="badgeClass">{{ label }}</span>
</template>
