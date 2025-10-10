import './app.css';
import App from './App.svelte';
import { mount } from 'svelte';
import { initializeModels } from './stores/models.js';

// 初始化 AI 模型數據
initializeModels();

const app = mount(App, {
  target: document.getElementById('app'),
});

export default app;
