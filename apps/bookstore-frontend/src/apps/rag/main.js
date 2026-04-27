import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
import '../../shared/theme.css'
import App from './App.vue'
import { createRagRouter } from './router'

const app = createApp(App)
app.use(createPinia())
app.use(createRagRouter())
app.mount('#app')
