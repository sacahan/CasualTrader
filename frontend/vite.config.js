import { defineConfig, loadEnv } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig(({ mode }) => {
  // 載入環境變數
  const env = loadEnv(mode, '.', '');
  const port = parseInt(env.VITE_PORT) || 3000;
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8000';
  const wsUrl = env.VITE_WS_URL || 'ws://localhost:8000/ws';

  // 從 URL 中提取 target
  const apiTarget = apiBaseUrl;
  const wsTarget = wsUrl.replace('/ws', '');

  return {
    plugins: [svelte()],
    server: {
      port,
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
