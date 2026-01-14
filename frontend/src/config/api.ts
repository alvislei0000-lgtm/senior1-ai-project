// frontend/src/config/api.ts
const isDevelopment = window.location.hostname === 'localhost';

// 確保開頭有一個 "/"，這非常重要
export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8000' 
  : '';
