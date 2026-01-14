import React from 'react'

type Props = {
  children: React.ReactNode
}

type State = {
  hasError: boolean
  message?: string
  stack?: string
}

export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: unknown): State {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    }
  }

  componentDidCatch(error: unknown) {
    // eslint-disable-next-line no-console
    console.error('App crashed:', error)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24, color: '#111' }}>
          <div style={{ background: 'rgba(255,255,255,0.95)', borderRadius: 16, padding: 20 }}>
            <h2 style={{ marginBottom: 8 }}>前端發生錯誤，導致畫面未渲染</h2>
            <div style={{ marginBottom: 12, color: '#444' }}>
              請打開瀏覽器 DevTools → Console，把錯誤訊息貼給我（或截圖）。
            </div>
            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0 }}>
              {this.state.message}
              {this.state.stack ? `\n\n${this.state.stack}` : ''}
            </pre>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}










