import { useState, useEffect } from 'react'
import formService from '../services/formService'
import './FormManager.css'

const FormManager = () => {
  const [forms, setForms] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [viewingData, setViewingData] = useState(null)
  const [editValues, setEditValues] = useState({})
  const [showAddForm, setShowAddForm] = useState(false)
  const [newForm, setNewForm] = useState({ form_name: '', data: '' })

  useEffect(() => {
    fetchForms()
  }, [])

  const fetchForms = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await formService.getAllForms()
      setForms(data)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleAddForm = async (e) => {
    e.preventDefault()
    if (!newForm.form_name || !newForm.data) {
      setError('Form name and data are required')
      return
    }

    let validatedData = newForm.data
    try {
      const parsedData = JSON.parse(newForm.data)
      validatedData = JSON.stringify(parsedData)
    } catch (e) {
      setError('Invalid JSON format. Please check your data.')
      return
    }

    try {
      setLoading(true)
      const result = await formService.createForm(newForm.form_name, validatedData)
      setForms([...forms, result])
      setNewForm({ form_name: '', data: '' })
      setShowAddForm(false)
      setError(null)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (form) => {
    setEditingId(form.id)
    let formattedData = form.data
    try {
      const parsedData = typeof form.data === 'string' ? JSON.parse(form.data) : form.data
      formattedData = JSON.stringify(parsedData, null, 2)
    } catch (e) {
      formattedData = form.data
    }
    setEditValues({
      form_name: form.form_name,
      data: formattedData
    })
    setShowEditModal(true)
  }

  const handleSaveEdit = async () => {
    if (!editValues.form_name || !editValues.data) {
      setError('Form name and data are required')
      return
    }

    let validatedData = editValues.data
    try {
      const parsedData = JSON.parse(editValues.data)
      validatedData = JSON.stringify(parsedData)
    } catch (e) {
      setError('Invalid JSON format. Please check your data.')
      return
    }

    try {
      setLoading(true)
      const updated = await formService.updateForm(editingId, { form_name: editValues.form_name, data: validatedData })
      setForms(forms.map(f => f.id === editingId ? updated : f))
      setShowEditModal(false)
      setEditingId(null)
      setEditValues({})
      setError(null)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this form?')) {
      try {
        setLoading(true)
        await formService.deleteForm(id)
        setForms(forms.filter(f => f.id !== id))
        setError(null)
      } catch (err) {
        setError(String(err))
      } finally {
        setLoading(false)
      }
    }
  }

  const handleCancel = () => {
    setEditingId(null)
    setEditValues({})
    setShowAddForm(false)
  }

  const closeEditModal = () => {
    setShowEditModal(false)
    setEditingId(null)
    setEditValues({})
  }

  const handleView = (form) => {
    let formattedData = form.data
    try {
      const parsedData = typeof form.data === 'string' ? JSON.parse(form.data) : form.data
      formattedData = JSON.stringify(parsedData, null, 2)
    } catch (e) {
      formattedData = form.data
    }
    setViewingData({
      form_name: form.form_name,
      data: formattedData
    })
    setShowViewModal(true)
  }

  const closeViewModal = () => {
    setShowViewModal(false)
    setViewingData(null)
  }

  return (
    <div className="form-manager">
      <div className="manager-header">
        <h2>📋 Form Database</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="btn-add-form"
          disabled={loading}
        >
          {showAddForm ? '✕ Cancel' : '➕ Add New Form'}
        </button>
      </div>

      {error && (
        <div className="error-alert">
          <p>{error}</p>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {showAddForm && (
        <form onSubmit={handleAddForm} className="add-form">
          <div className="form-group">
            <label htmlFor="form-name">Form Name:</label>
            <input
              id="form-name"
              type="text"
              value={newForm.form_name}
              onChange={(e) => setNewForm({...newForm, form_name: e.target.value})}
              placeholder="Enter form name"
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="form-data">Form Data (JSON):</label>
            <textarea
              id="form-data"
              value={newForm.data}
              onChange={(e) => setNewForm({...newForm, data: e.target.value})}
              placeholder="Enter form data"
              rows="4"
              disabled={loading}
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-save" disabled={loading}>
              {loading ? '⏳ Saving...' : '💾 Save Form'}
            </button>
            <button type="button" onClick={handleCancel} className="btn-cancel">
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading && !showAddForm && <p className="loading">Loading forms...</p>}

      {forms.length === 0 ? (
        <p className="no-forms">No forms found. Create one to get started!</p>
      ) : (
        <div className="forms-table-wrapper">
          <table className="forms-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Form Name</th>
                <th>Data</th>
                <th>Created At</th>
                <th>Updated At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {forms.map((form) => (
                <tr key={form.id}>
                  <td>{form.id}</td>
                  <td>{form.form_name}</td>
                  <td className="data-cell">
                    <div className="data-preview">{form.data.substring(0, 50)}...</div>
                  </td>
                  <td>{new Date(form.created_at).toLocaleDateString()}</td>
                  <td>{new Date(form.updated_at).toLocaleDateString()}</td>
                  <td className="actions-cell">
                    <button
                      onClick={() => handleView(form)}
                      className="btn-action btn-view"
                      title="View"
                      disabled={loading}
                    >
                      👁️
                    </button>
                    <button
                      onClick={() => handleEdit(form)}
                      className="btn-action btn-edit"
                      title="Edit"
                      disabled={loading}
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => handleDelete(form.id)}
                      className="btn-action btn-delete"
                      title="Delete"
                      disabled={loading}
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showEditModal && (
        <div className="modal-overlay" onClick={closeEditModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Edit Form</h3>
              <button className="modal-close" onClick={closeEditModal}>✕</button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="edit-form-name">Form Name:</label>
                <input
                  id="edit-form-name"
                  type="text"
                  value={editValues.form_name || ''}
                  onChange={(e) => setEditValues({...editValues, form_name: e.target.value})}
                  placeholder="Enter form name"
                  disabled={loading}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="edit-form-data">Form Data (JSON):</label>
                <textarea
                  id="edit-form-data"
                  value={editValues.data || ''}
                  onChange={(e) => setEditValues({...editValues, data: e.target.value})}
                  placeholder="Enter form data"
                  rows="10"
                  disabled={loading}
                  className="modal-textarea"
                />
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                onClick={handleSaveEdit} 
                className="btn-save"
                disabled={loading}
              >
                {loading ? '⏳ Saving...' : '💾 Save Changes'}
              </button>
              <button 
                onClick={closeEditModal} 
                className="btn-cancel"
                disabled={loading}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {showViewModal && viewingData && (
        <div className="modal-overlay" onClick={closeViewModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>View Form</h3>
              <button className="modal-close" onClick={closeViewModal}>✕</button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label>Form Name:</label>
                <div className="view-field">{viewingData.form_name}</div>
              </div>
              
              <div className="form-group">
                <label>Form Data (JSON):</label>
                <pre className="view-field view-data">{viewingData.data}</pre>
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                onClick={closeViewModal} 
                className="btn-cancel"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default FormManager
