import { defineConfig, loadEnv } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => {
  // 載入環境變數
  const env = loadEnv(mode, '.', '');
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8000';
  const wsUrl = env.VITE_WS_URL || 'ws://localhost:8000/ws';

  // 從 URL 中提取 target
  const apiTarget = apiBaseUrl;
  const wsTarget = wsUrl.replace('/ws', '');

  return {
    plugins: [tailwindcss(), svelte()],
    server: {
      port: 3000,
      host: true,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/ws': {
          target: wsTarget,
          ws: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['svelte', 'chart.js'],
          },
        },
      },
    },
    esbuild: {
      sourcemap: true, // ✅ 有時開發中這也可確保 map 保留
    },
  };
});
