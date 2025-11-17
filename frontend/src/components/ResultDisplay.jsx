import { useState } from 'react'
import './ResultDisplay.css'

const ResultDisplay = ({ result, onReset }) => {
  const [copied, setCopied] = useState(false)
  const [expandedKeys, setExpandedKeys] = useState(new Set())
  const [showRawJson, setShowRawJson] = useState(false)
  const [viewMode, setViewMode] = useState('json')

  const handleCopy = async () => {
    try {
      const jsonString = JSON.stringify(result.extracted_data, null, 2)
      await navigator.clipboard.writeText(jsonString)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch (err) {
      console.error('Failed to copy:', err)
      alert('Failed to copy to clipboard')
    }
  }

  const downloadJSON = () => {
    try {
      const jsonString = JSON.stringify(result.extracted_data, null, 2)
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${result.filename.replace(/\.[^/.]+$/, '')}_extracted.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download:', err)
      alert('Failed to download JSON')
    }
  }

  const flattenDict = (obj, parentKey = '', sep = '_') => {
    const items = []
    Object.entries(obj).forEach(([k, v]) => {
      const newKey = parentKey ? `${parentKey}${sep}${k}` : k
      if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
        items.push(...Object.entries(flattenDict(v, newKey, sep)))
      } else if (Array.isArray(v)) {
        items.push([newKey, JSON.stringify(v)])
      } else {
        items.push([newKey, v])
      }
    })
    return Object.fromEntries(items)
  }

  const getTableData = () => {
    if (Array.isArray(result.extracted_data)) {
      return result.extracted_data.map(item => 
        typeof item === 'object' ? flattenDict(item) : { value: item }
      )
    } else if (typeof result.extracted_data === 'object') {
      return [flattenDict(result.extracted_data)]
    }
    return [{ value: result.extracted_data }]
  }

  const downloadCSV = () => {
    try {
      const tableData = getTableData()
      if (tableData.length === 0) {
        alert('No data to download')
        return
      }
      
      const allKeys = []
      tableData.forEach(row => {
        Object.keys(row).forEach(key => {
          if (!allKeys.includes(key)) allKeys.push(key)
        })
      })

      const csvContent = [
        allKeys.map(key => `"${key}"`).join(','),
        ...tableData.map(row =>
          allKeys.map(key => {
            const value = row[key] ?? ''
            const stringValue = String(value)
            return `"${stringValue.replace(/"/g, '""')}"`
          }).join(',')
        )
      ].join('\n')

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${result.filename.replace(/\.[^/.]+$/, '')}_extracted.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download:', err)
      alert('Failed to download CSV')
    }
  }

  const renderTable = () => {
    const tableData = getTableData()
    if (tableData.length === 0) {
      return <p>No data to display</p>
    }

    const allKeys = []
    tableData.forEach(row => {
      Object.keys(row).forEach(key => {
        if (!allKeys.includes(key)) allKeys.push(key)
      })
    })

    return (
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {allKeys.map(key => (
                <th key={key}>{key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.map((row, index) => (
              <tr key={index}>
                {allKeys.map(key => (
                  <td key={`${index}-${key}`}>{row[key] ?? ''}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  const toggleExpandKey = (key) => {
    const newExpanded = new Set(expandedKeys)
    if (newExpanded.has(key)) {
      newExpanded.delete(key)
    } else {
      newExpanded.add(key)
    }
    setExpandedKeys(newExpanded)
  }

  const renderJSON = (data, level = 0) => {
    if (data === null) return <span className="json-null">null</span>
    if (typeof data === 'boolean') return <span className="json-boolean">{data.toString()}</span>
    if (typeof data === 'number') return <span className="json-number">{data}</span>
    if (typeof data === 'string') return <span className="json-string">"{data}"</span>

    if (Array.isArray(data)) {
      if (data.length === 0) return <span className="json-bracket">[]</span>
      return (
        <div className="json-array">
          <span className="json-bracket">[</span>
          <div className="json-content" style={{ marginLeft: `${(level + 1) * 20}px` }}>
            {data.map((item, index) => (
              <div key={index} className="json-item">
                {renderJSON(item, level + 1)}
                {index < data.length - 1 && <span className="json-comma">,</span>}
              </div>
            ))}
          </div>
          <span className="json-bracket">]</span>
        </div>
      )
    }

    if (typeof data === 'object') {
      const keys = Object.keys(data)
      if (keys.length === 0) return <span className="json-bracket">{'{}'}</span>
      return (
        <div className="json-object">
          <span className="json-bracket">{'{'}</span>
          <div className="json-content" style={{ marginLeft: `${(level + 1) * 20}px` }}>
            {keys.map((key, index) => (
              <div key={key} className="json-item">
                <span className="json-key">"{key}"</span>
                <span className="json-colon">: </span>
                {renderJSON(data[key], level + 1)}
                {index < keys.length - 1 && <span className="json-comma">,</span>}
              </div>
            ))}
          </div>
          <span className="json-bracket">{'}'}</span>
        </div>
      )
    }

    return <span>{String(data)}</span>
  }

  return (
    <div className="result-container">
      <div className="result-header">
        <h2>✅ Extraction Complete</h2>
        <p className="filename">File: {result.filename}</p>
      </div>

      <div className="json-display">
        <div className="json-header">
          <h3>📊 Extraction Results</h3>
          <div className="json-actions">
            <div className="view-buttons">
              <button 
                onClick={() => setViewMode('json')} 
                className={`btn-view ${viewMode === 'json' ? 'active' : ''}`}
                title="View as JSON"
              >
                📄 JSON View
              </button>
              <button 
                onClick={() => setViewMode('table')} 
                className={`btn-view ${viewMode === 'table' ? 'active' : ''}`}
                title="View as Table"
              >
                📋 Table View
              </button>
            </div>
            <div className="download-buttons">
              {viewMode === 'json' && (
                <>
                  <button onClick={() => setShowRawJson(!showRawJson)} className="btn-toggle-view" title="Toggle between formatted and raw JSON">
                    {showRawJson ? '🎨 Formatted' : '📄 Raw JSON'}
                  </button>
                  <button onClick={handleCopy} className={`btn-copy ${copied ? 'copied' : ''}`}>
                    {copied ? '✅ Copied!' : '📋 Copy'}
                  </button>
                </>
              )}
              <button onClick={downloadJSON} className="btn-download" title="Download as JSON file">
                ⬇️ Download JSON
              </button>
              <button onClick={downloadCSV} className="btn-download" title="Download as CSV file">
                ⬇️ Download CSV
              </button>
            </div>
          </div>
        </div>
        <div className="json-viewer">
          {viewMode === 'table' ? (
            renderTable()
          ) : showRawJson ? (
            <pre className="raw-json">{JSON.stringify(result.extracted_data, null, 2)}</pre>
          ) : (
            renderJSON(result.extracted_data)
          )}
        </div>
      </div>

      <div className="result-actions">
        <button onClick={onReset} className="btn-primary">
          ⬆️ Upload Another Image
        </button>
      </div>

      <div className="info-box">
        <p>💡 <strong>Note:</strong> This AI extracts only what it can read from the handwriting. If some text is unclear or illegible, it may be marked as "unreadable" or omitted.</p>
      </div>
    </div>
  )
}

export default ResultDisplay
