import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  plugins: [react()],
  server: {
    proxy: {
      '^/api': {
        target: 'http://0.0.0.0:8000',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    }
  }
});
