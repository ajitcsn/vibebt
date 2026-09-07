import { defineConfig } from 'vite';

// Development mirrors production: the browser talks to its own origin and
// Vite forwards API calls to the separately running daily-data service.
const apiTarget = process.env.VIBEBT_API_TARGET || 'http://127.0.0.1:8765';

export default defineConfig({
  server: {
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
      '/health': { target: apiTarget, changeOrigin: true },
    },
  },
});
