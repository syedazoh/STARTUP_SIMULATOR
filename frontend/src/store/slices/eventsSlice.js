import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchEvents = createAsyncThunk('events/fetchEvents', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/events`, {
    params: { limit: 100 },
  })
  return response.data
}, { condition: (_, { getState }) => !getState().events?.isRefreshing })

const eventsSlice = createSlice({
  name: 'events',
  initialState: {
    items: [],
    loadStatus: 'idle',
    error: null,
    hasSnapshot: false,
    isRefreshing: false,
    requestId: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchEvents.pending, (state, action) => {
        state.requestId = action.meta.requestId
        state.isRefreshing = true
        state.loadStatus = state.hasSnapshot ? 'succeeded' : 'loading'
      })
      .addCase(fetchEvents.fulfilled, (state, action) => {
        if (state.requestId !== action.meta.requestId) return
        state.hasSnapshot = true
        state.isRefreshing = false
        state.error = null
        state.loadStatus = 'succeeded'
        state.items = action.payload
      })
      .addCase(fetchEvents.rejected, (state, action) => {
        if (state.requestId !== action.meta.requestId) return
        state.isRefreshing = false
        state.loadStatus = state.hasSnapshot ? 'succeeded' : 'failed'
        state.error = action.error.message
      })
  },
})

export default eventsSlice.reducer
