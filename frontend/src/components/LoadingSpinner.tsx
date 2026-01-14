import './LoadingSpinner.css'

interface LoadingSpinnerProps {
  message?: string
}

function LoadingSpinner({ message = '載入中...' }: LoadingSpinnerProps) {
  return (
    <div className="loading-spinner-container">
      <div className="loading-spinner">
        <div className="spinner-ring"></div>
        <div className="spinner-ring"></div>
        <div className="spinner-ring"></div>
      </div>
      <p className="loading-message">{message}</p>
    </div>
  )
}

export default LoadingSpinner


