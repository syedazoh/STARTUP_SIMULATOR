import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchAgents = createAsyncThunk('agents/fetchAgents', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/agents`)
  return response.data
}, { condition: (_, { getState }) => !getState().agents?.isRefreshing })

const agentsSlice = createSlice({
  name: 'agents',
  initialState: {
    statuses: {},
    loadStatus: 'idle',
    error: null,
    hasSnapshot: false,
    isRefreshing: false,
    requestId: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAgents.pending, (state, action) => {
        state.requestId = action.meta.requestId
        state.isRefreshing = true
        state.loadStatus = state.hasSnapshot ? 'succeeded' : 'loading'
      })
      .addCase(fetchAgents.fulfilled, (state, action) => {
        if (state.requestId !== action.meta.requestId) return
        state.hasSnapshot = true
        state.isRefreshing = false
        state.error = null
        state.loadStatus = 'succeeded'
        state.statuses = action.payload
      })
      .addCase(fetchAgents.rejected, (state, action) => {
        if (state.requestId !== action.meta.requestId) return
        state.isRefreshing = false
        state.loadStatus = state.hasSnapshot ? 'succeeded' : 'failed'
        state.error = action.error.message
      })
  },
})

export default agentsSlice.reducer
