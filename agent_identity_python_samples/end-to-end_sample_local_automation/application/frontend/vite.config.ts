import { defineConfig } from 'vite'
import { resolve } from 'path'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    open: true,
    proxy: {
      '/chat': {
        target: 'http://localhost:8090',
        changeOrigin: true
      },
      '/callback_for_oauth': {
        target: 'http://localhost:8090',
        changeOrigin: true
      },
      '/auth': {
        target: 'http://localhost:8090',
        changeOrigin: true
      }
    }
  },

  resolve: {
    alias: {
      lodash: resolve(__dirname, 'node_modules/lodash-es')
    }
  },

  preview: {
    port: 5173
  },

  build: {
    target: 'ES2022',
    outDir: 'dist', 
    assetsDir: 'assets',

    // 关闭 SourceMap（关闭压缩后构建产物可读）
    sourcemap: false,

    minify: true,

    rollupOptions: {
      external: ['mermaid']
    }
  }
})
