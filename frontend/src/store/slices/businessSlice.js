import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

const ACTIVE_BUSINESS_STORAGE_KEY = 'simulator_active_business'

export const fetchBusinesses = createAsyncThunk('business/fetchAll', async () => {
  const response = await apiClient.get('/api/businesses')
  return response.data
})

export const createBusiness = createAsyncThunk('business/create', async (payload) => {
  const response = await apiClient.post('/api/businesses', payload)
  return response.data
})

const businessSlice = createSlice({
  name: 'business',
  initialState: {
    items: [],
    activeBusinessId: localStorage.getItem(ACTIVE_BUSINESS_STORAGE_KEY),
    status: 'idle',
    error: null,
  },
  reducers: {
    setActiveBusiness: (state, action) => {
      state.activeBusinessId = action.payload
      localStorage.setItem(ACTIVE_BUSINESS_STORAGE_KEY, action.payload)
    },
    clearBusinesses: (state) => {
      state.items = []
      state.activeBusinessId = null
      localStorage.removeItem(ACTIVE_BUSINESS_STORAGE_KEY)
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchBusinesses.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(fetchBusinesses.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.items = action.payload
        const stillValid = state.items.some((b) => b.id === state.activeBusinessId)
        if (!stillValid && state.items.length > 0) {
          state.activeBusinessId = state.items[0].id
          localStorage.setItem(ACTIVE_BUSINESS_STORAGE_KEY, state.items[0].id)
        }
      })
      .addCase(fetchBusinesses.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
      .addCase(createBusiness.fulfilled, (state, action) => {
        state.items.push(action.payload)
        state.activeBusinessId = action.payload.id
        localStorage.setItem(ACTIVE_BUSINESS_STORAGE_KEY, action.payload.id)
      })
  },
})

export const { setActiveBusiness, clearBusinesses } = businessSlice.actions
export default businessSlice.reducer
