import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'
import './theme-enhancements.css'
import './liquid-glass.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

const rootEl = document.getElementById('root')
if (!rootEl) {
  throw new Error('找不到 #root，無法掛載 React')
}

// 全域錯誤 fallback：避免只剩背景顏色卻不知道發生什麼事
const showFatal = (title: string, err: unknown) => {
  // eslint-disable-next-line no-console
  console.error(title, err)
  const msg = err instanceof Error ? `${err.message}\n\n${err.stack || ''}` : String(err)
  rootEl.innerHTML = `
    <div style="padding:24px;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;color:#111;">
      <div style="background:rgba(255,255,255,0.95);border-radius:16px;padding:20px;">
        <h2 style="margin:0 0 8px 0;">${title}</h2>
        <div style="margin:0 0 12px 0;color:#444;">請打開 DevTools → Console，把錯誤貼給我。</div>
        <pre style="white-space:pre-wrap;word-break:break-word;margin:0;">${msg}</pre>
      </div>
    </div>
  `
}

window.addEventListener('error', (e) => showFatal('前端發生未捕捉錯誤（error）', (e as any).error || e))
window.addEventListener('unhandledrejection', (e) => showFatal('前端發生未處理 Promise 錯誤（unhandledrejection）', (e as any).reason || e))

try {
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>
      </ErrorBoundary>
    </React.StrictMode>,
  )
} catch (e) {
  showFatal('React 初始化失敗', e)
}


