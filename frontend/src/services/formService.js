import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const formService = {
  createForm: async (formName, data) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/forms`, {
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
      const response = await axios.get(`${API_BASE_URL}/forms`)
      return response.data
    } catch (error) {
      throw error.response?.data?.detail || error.message
    }
  },

  getFormById: async (id) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/forms/${id}`)
      return response.data
    } catch (error) {
      throw error.response?.data?.detail || error.message
    }
  },

  updateForm: async (id, updates) => {
    try {
      const response = await axios.put(`${API_BASE_URL}/forms/${id}`, updates)
      return response.data
    } catch (error) {
      throw error.response?.data?.detail || error.message
    }
  },

  deleteForm: async (id) => {
    try {
      const response = await axios.delete(`${API_BASE_URL}/forms/${id}`)
      return response.data
    } catch (error) {
      throw error.response?.data?.detail || error.message
    }
  }
}

export default formService
