import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchAgents = createAsyncThunk('agents/fetchAgents', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/agents`)
  return response.data
})

const agentsSlice = createSlice({
  name: 'agents',
  initialState: {
    statuses: {},
    loadStatus: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAgents.pending, (state) => {
        state.loadStatus = 'loading'
      })
      .addCase(fetchAgents.fulfilled, (state, action) => {
        state.loadStatus = 'succeeded'
        state.statuses = action.payload
      })
      .addCase(fetchAgents.rejected, (state, action) => {
        state.loadStatus = 'failed'
        state.error = action.error.message
      })
  },
})

export default agentsSlice.reducer
