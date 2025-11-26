import { useState, useEffect } from 'react'
import FileUpload from './components/FileUpload'
import ResultDisplay from './components/ResultDisplay'
import FormManager from './components/FormManager'
import { useTracking } from './hooks/useTracking'
import './App.css'

function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('upload')
  const { trackNavigation, trackEvent, trackError } = useTracking()

  // Track page load
  useEffect(() => {
    trackEvent('page_load', {
      initial_tab: activeTab,
    })
  }, [])

  const handleUploadSuccess = (data) => {
    setResult(data)
    setError(null)

    // Track successful upload
    trackEvent('upload_success', {
      filename: data.filename,
      fields_extracted: Object.keys(data.extracted_data || {}).length,
    })
  }

  const handleUploadError = (err) => {
    setError(err)
    setResult(null)

    // Track upload error
    trackError(new Error(err), {
      context: 'file_upload',
    })
  }

  const handleReset = () => {
    setResult(null)
    setError(null)

    // Track reset action
    trackEvent('reset_upload', {
      previous_result: result ? 'had_result' : 'no_result',
    })
  }

  const handleTabChange = (newTab) => {
    // Track navigation
    trackNavigation(activeTab, newTab, {
      action: 'tab_change',
    })

    setActiveTab(newTab)
  }

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>🖊️ Handwriting Extraction AI</h1>
          <p>Upload handwritten images and extract text using AI vision technology</p>
        </header>

        <div className="tab-navigation">
          <button
            className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => handleTabChange('upload')}
          >
            ⬆️ Upload & Extract
          </button>
          <button
            className={`tab-btn ${activeTab === 'forms' ? 'active' : ''}`}
            onClick={() => handleTabChange('forms')}
          >
            📋 Manage Forms
          </button>
        </div>

        <div className="main-content">
          {activeTab === 'upload' && (
            <>
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
                  onNavigateToForms={() => handleTabChange('forms')}
                />
              )}
            </>
          )}

          {activeTab === 'forms' && (
            <FormManager />
          )}
        </div>


      </div>
    </div>
  )
}

export default App
