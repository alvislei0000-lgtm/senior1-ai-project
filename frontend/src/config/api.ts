const isDevelopment = window.location.hostname === 'localhost';

/**
 * 生產環境設為空字串 ''，瀏覽器會自動請求同網域路徑
 * 確保請求開頭帶有 /，例如 fetch("/api/hardware")
 */
export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8000' 
  : ''; 

export const API_TIMEOUT = 15000;
