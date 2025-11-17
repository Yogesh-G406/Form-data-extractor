import { useState, useRef } from 'react'
import axios from 'axios'
import './FileUpload.css'

const FileUpload = ({ onUploadSuccess, onUploadError, loading, setLoading }) => {
  const [preview, setPreview] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (file) => {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
    
    if (!validTypes.includes(file.type)) {
      onUploadError('Please upload a JPG, PNG, or PDF file')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      onUploadError('File size must be less than 10MB')
      return
    }

    setSelectedFile(file)
    
    if (file.type !== 'application/pdf') {
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreview(reader.result)
      }
      reader.readAsDataURL(file)
    } else {
      setPreview(null)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      onUploadError('Please select a file first')
      return
    }

    setLoading(true)
    setUploadProgress(0)
    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          setUploadProgress(percentCompleted)
        },
      })

      onUploadSuccess(response.data)
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to process image'
      onUploadError(errorMessage)
    } finally {
      setLoading(false)
      setUploadProgress(0)
    }
  }

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="upload-container">
      {!selectedFile ? (
        <div 
          className={`dropzone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.pdf"
            onChange={handleChange}
            style={{ display: 'none' }}
          />
          
          <div className="dropzone-content">
            <svg className="upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <h3>Drop your handwritten image here</h3>
            <p>or</p>
            <button onClick={handleButtonClick} className="btn-primary">
              Browse Files
            </button>
            <p className="file-info">Supported: JPG, PNG, PDF (max 10MB)</p>
          </div>
        </div>
      ) : (
        <div className="preview-container">
          {preview && (
            <div className="image-preview">
              <img src={preview} alt="Preview" />
            </div>
          )}
          
          <div className="file-info-box">
            <p className="filename">📄 {selectedFile.name}</p>
            <p className="filesize">{(selectedFile.size / 1024).toFixed(2)} KB</p>
          </div>

          {loading && (
            <div className="progress-container">
              <div className="progress-label">
                {uploadProgress < 100 ? (
                  <>Uploading... {uploadProgress}%</>
                ) : (
                  <>Processing image...</>
                )}
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          <div className="button-group">
            <button 
              onClick={handleUpload} 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  {uploadProgress < 100 ? 'Uploading...' : 'Processing...'}
                </>
              ) : (
                '✨ Extract Text'
              )}
            </button>
            <button 
              onClick={() => {
                setSelectedFile(null)
                setPreview(null)
                setUploadProgress(0)
              }} 
              className="btn-secondary"
              disabled={loading}
            >
              Choose Different File
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUpload
