import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

const canRefresh = (_, { getState }) => !getState().events?.isRefreshing

export const fetchEvents = createAsyncThunk('events/fetchEvents', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/events`, {
    params: { limit: 100 },
  })
  return response.data
}, { condition: canRefresh })

// Only the Boardroom includes durable CEO handoffs and decision-log activity.
export const fetchBoardroomEvents = createAsyncThunk('events/fetchBoardroomEvents', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/events/boardroom`, {
    params: { limit: 100 },
  })
  return response.data
}, { condition: canRefresh })

const pending = (state, action) => {
  state.requestId = action.meta.requestId
  state.isRefreshing = true
  state.loadStatus = state.hasSnapshot ? 'succeeded' : 'loading'
}
const fulfilled = (state, action) => {
  if (state.requestId !== action.meta.requestId) return
  state.hasSnapshot = true
  state.isRefreshing = false
  state.error = null
  state.loadStatus = 'succeeded'
  state.items = action.payload
}
const rejected = (state, action) => {
  if (state.requestId !== action.meta.requestId) return
  state.isRefreshing = false
  state.loadStatus = state.hasSnapshot ? 'succeeded' : 'failed'
  state.error = action.error.message
}

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
      .addCase(fetchEvents.pending, pending)
      .addCase(fetchEvents.fulfilled, fulfilled)
      .addCase(fetchEvents.rejected, rejected)
      .addCase(fetchBoardroomEvents.pending, pending)
      .addCase(fetchBoardroomEvents.fulfilled, fulfilled)
      .addCase(fetchBoardroomEvents.rejected, rejected)
  },
})

export default eventsSlice.reducer
