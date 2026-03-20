import './assets/main.css'

import { createApp } from 'vue'

import App from './App.vue'
import router from './app/router'
import { initializeSessionStore } from './app/session-store'

const app = createApp(App)

app.use(router)

initializeSessionStore()

app.mount('#app')
