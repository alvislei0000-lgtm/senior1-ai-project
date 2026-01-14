// frontend/src/config/api.ts

// 判斷是否為開發環境
const isDevelopment = window.location.hostname === 'localhost';

/**
 * 關鍵：在生產環境 (Render) 必須為空字串 ""
 * 這樣請求會變成相對路徑 (例如 "/api/hardware")
 * 不會觸發 CORS 阻擋，也不會因為網域多一個 '1' 而失效
 */
export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8000' 
  : ''; 

export const API_TIMEOUT = 15000;
