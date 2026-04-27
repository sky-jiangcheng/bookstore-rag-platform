import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        axios: resolve(__dirname, 'node_modules/axios/index.js'),
        'element-plus': resolve(__dirname, 'node_modules/element-plus'),
      },
    },
    server: {
      proxy: {
        '/api': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true
        }
      }
    },
    build: {
      rollupOptions: {
        input: {
          main: resolve(__dirname, 'index.html'),
          auth: resolve(__dirname, 'auth.html'),
          rag: resolve(__dirname, 'rag.html'),
          catalog: resolve(__dirname, 'catalog.html')
        },
        output: {
          entryFileNames: 'assets/[name].js',
          chunkFileNames: 'assets/[name]-[hash].js',
          assetFileNames: 'assets/[name]-[hash][extname]',
          manualChunks(id) {
            if (!id.includes('node_modules')) {
              return
            }

            if (id.includes('element-plus')) {
              return 'element-plus'
            }

            if (id.includes('@element-plus/icons-vue')) {
              return 'element-plus-icons'
            }

            if (id.includes('vue-router')) {
              return 'vue-router'
            }

            if (id.includes('pinia')) {
              return 'pinia'
            }

            if (id.includes('axios')) {
              return 'axios'
            }

            return 'vendor'
          }
        }
      },
      outDir: 'dist'
    }
  }
})
