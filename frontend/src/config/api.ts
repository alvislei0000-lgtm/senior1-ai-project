// frontend/src/config/api.ts

// 判斷是否為開發環境
const isDevelopment = window.location.hostname === 'localhost';

// 關鍵修復：在 Render 生產環境使用相對路徑 ""，避免跨網域 (CORS) 問題
export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8000' 
  : ''; 

// 導出其他可能的配置
export const API_TIMEOUT = 15000;
