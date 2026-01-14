# 故障排除指南

## 如果只看到紫色背景，看不到內容

### 可能的原因和解決方案：

1. **檢查瀏覽器控制台**
   - 按 F12 打開開發者工具
   - 查看 Console 標籤是否有錯誤
   - 查看 Network 標籤確認 CSS 和 JS 文件是否正確載入

2. **清除快取並重新載入**
   - 按 Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac) 強制重新載入
   - 或清除瀏覽器快取

3. **確認開發伺服器正在運行**
   ```bash
   cd frontend
   npm run dev
   ```
   應該看到類似：`Local: http://localhost:5173/`

4. **檢查依賴是否安裝**
   ```bash
   cd frontend
   npm install
   ```

5. **檢查 React 組件是否正確渲染**
   - 在瀏覽器開發者工具中，檢查 Elements/Inspector
   - 確認 `<div id="root">` 內有內容
   - 確認 `.app-header` 和 `.app-main` 元素存在

6. **如果仍然只看到紫色背景**
   - 可能是 CSS 沒有正確載入
   - 檢查 Network 標籤，確認 `App.css` 和 `index.css` 已載入
   - 檢查是否有 CSS 錯誤

### 快速測試

在瀏覽器控制台執行：
```javascript
document.querySelector('.app-header')
```
如果返回 `null`，表示 React 沒有正確渲染。

### 重新安裝依賴

如果問題持續，嘗試：
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```


