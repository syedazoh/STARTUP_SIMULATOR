import { createAsyncThunk, createSlice, isAnyOf } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchEvents = createAsyncThunk('events/fetchEvents', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/events`, {
    params: { limit: 100 },
  })
  return response.data
}, { condition: (_, { getState }) => !getState().events?.isRefreshing })

// Boardroom includes durable CEO assignments, reports and decision-log activity.
export const fetchBoardroomEvents = createAsyncThunk('events/fetchBoardroomEvents', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/events/boardroom`, {
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
      .addMatcher(isAnyOf(fetchEvents.pending, fetchBoardroomEvents.pending), (state, action) => {
        state.requestId = action.meta.requestId
        state.isRefreshing = true
        state.loadStatus = state.hasSnapshot ? 'succeeded' : 'loading'
      })
      .addMatcher(isAnyOf(fetchEvents.fulfilled, fetchBoardroomEvents.fulfilled), (state, action) => {
        if (state.requestId !== action.meta.requestId) return
        state.hasSnapshot = true
        state.isRefreshing = false
        state.error = null
        state.loadStatus = 'succeeded'
        state.items = action.payload
      })
      .addMatcher(isAnyOf(fetchEvents.rejected, fetchBoardroomEvents.rejected), (state, action) => {
        if (state.requestId !== action.meta.requestId) return
        state.isRefreshing = false
        state.loadStatus = state.hasSnapshot ? 'succeeded' : 'failed'
        state.error = action.error.message
      })
  },
})

export default eventsSlice.reducer
