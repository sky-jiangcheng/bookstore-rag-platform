import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
import '../../shared/theme.css'
import App from './App.vue'
import { createCatalogRouter } from './router'

const app = createApp(App)
app.use(createPinia())
app.use(createCatalogRouter())
app.mount('#app')
