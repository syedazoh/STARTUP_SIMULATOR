import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchEvents = createAsyncThunk('events/fetchEvents', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/events`, {
    params: { limit: 100 },
  })
  return response.data
})

const eventsSlice = createSlice({
  name: 'events',
  initialState: {
    items: [],
    loadStatus: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchEvents.pending, (state) => {
        state.loadStatus = 'loading'
      })
      .addCase(fetchEvents.fulfilled, (state, action) => {
        state.loadStatus = 'succeeded'
        state.items = action.payload
      })
      .addCase(fetchEvents.rejected, (state, action) => {
        state.loadStatus = 'failed'
        state.error = action.error.message
      })
  },
})

export default eventsSlice.reducer
