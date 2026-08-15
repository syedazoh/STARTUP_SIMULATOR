import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchChatThread = createAsyncThunk(
  'chat/fetchChatThread',
  async ({ businessId, agentKey }, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(`/api/businesses/${businessId}/agents/${agentKey}/chat`)
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch chat')
    }
  }
)

export const sendChatMessage = createAsyncThunk(
  'chat/sendChatMessage',
  async ({ businessId, agentKey, content }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(`/api/businesses/${businessId}/agents/${agentKey}/chat`, { content })
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to send message')
    }
  }
)

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    threads: {},
    status: 'idle',
    error: null,
    lastTask: null,
  },
  reducers: {
    clearThread: (state, action) => {
      delete state.threads[action.payload]
    },
    clearAllThreads: (state) => {
      state.threads = {}
      state.lastTask = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchChatThread.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchChatThread.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.threads[action.payload.agent] = action.payload
      })
      .addCase(fetchChatThread.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.payload
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        const { thread, task } = action.payload
        state.threads[thread.agent] = thread
        state.lastTask = task
      })
  },
})

export const { clearThread, clearAllThreads } = chatSlice.actions
export default chatSlice.reducer