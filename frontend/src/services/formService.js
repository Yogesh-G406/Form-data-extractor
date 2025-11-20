import axios from 'axios'

const formService = {
  createForm: async (formName, data) => {
    try {
      const response = await axios.post('/api/forms', {
        form_name: formName,
        data: typeof data === 'string' ? data : JSON.stringify(data)
      })
      return response.data
    } catch (error) {
      throw error.response?.data?.detail || error.message
    }
  },

  getAllForms: async () => {
    try {
      const response = await axios.get('/api/forms')
      return response.data
    } catch (error) {
      throw error.response?.data?.detail || error.message
    }
  },

  getFormById: async (id) => {
    try {
      const response = await axios.get(`/api/forms/${id}`)
      return response.data
    } catch (error) {
      throw error.response?.data?.detail || error.message
    }
  },

  updateForm: async (id, updates) => {
    try {
      const response = await axios.put(`/api/forms/${id}`, updates)
      return response.data
    } catch (error) {
      throw error.response?.data?.detail || error.message
    }
  },

  deleteForm: async (id) => {
    try {
      const response = await axios.delete(`/api/forms/${id}`)
      return response.data
    } catch (error) {
      throw error.response?.data?.detail || error.message
    }
  }
}

export default formService
