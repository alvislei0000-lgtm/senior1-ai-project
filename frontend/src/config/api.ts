// API 配置
const isProduction = import.meta.env.PROD;
const isDevelopment = import.meta.env.DEV;

// 在開發環境使用本地後端，在生產環境使用環境變數或預設URL
export const API_BASE_URL = isDevelopment
  ? '' // 開發環境使用相對路徑，讓Vite代理處理
  : (import.meta.env.VITE_API_BASE_URL || '');

// 如果你在 Railway 上部署，環境變數會自動設定
// 如果使用其他服務，請在部署平台設定 VITE_API_BASE_URL 環境變數
// 例如:
// Railway: https://your-project.up.railway.app
// Render: https://your-service.onrender.com
// Heroku: https://your-app.herokuapp.com