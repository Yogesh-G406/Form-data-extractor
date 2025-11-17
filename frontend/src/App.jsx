import { useState } from 'react'
import FileUpload from './components/FileUpload'
import ResultDisplay from './components/ResultDisplay'
import './App.css'

function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleUploadSuccess = (data) => {
    setResult(data)
    setError(null)
  }

  const handleUploadError = (err) => {
    setError(err)
    setResult(null)
  }

  const handleReset = () => {
    setResult(null)
    setError(null)
  }

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>🖊️ Handwriting Extraction AI</h1>
          <p>Upload handwritten images and extract text using AI vision technology</p>
        </header>

        <div className="main-content">
          {!result && !error && (
            <FileUpload 
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
              loading={loading}
              setLoading={setLoading}
            />
          )}

          {error && (
            <div className="error-container">
              <div className="error-message">
                <h2>⚠️ Oops! Something went wrong</h2>
                <p>{error}</p>
                <button onClick={handleReset} className="btn-primary">
                  🔄 Try Again
                </button>
              </div>
            </div>
          )}

          {result && !error && (
            <ResultDisplay 
              result={result}
              onReset={handleReset}
            />
          )}
        </div>

        <footer className="footer">
          <p>Powered by LangChain, Langfuse, and GPT-4 Vision</p>
        </footer>
      </div>
    </div>
  )
}

export default App
