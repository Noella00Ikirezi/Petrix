import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-charts': ['recharts'],
          'vendor-query': ['@tanstack/react-query'],
          'vendor-ui': ['lucide-react'],
        },
      },
    },
  },
  server: {
    port: 5173,
    host: true,
    allowedHosts: ['petrix.noellahome.org', 'localhost', '3.255.126.244'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    watch: {
      ignored: ['**/Dockerfile', '**/Dockerfile.*', '**/*.md', '**/Makefile', '**/.env*'],
    },
  },
});
