<script setup>
import { RouterView } from 'vue-router'

import AppHeader from '@/widgets/app/AppHeader.vue'
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <div class="app-view">
      <RouterView />
    </div>
  </div>
</template>
