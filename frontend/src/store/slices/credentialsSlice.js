import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchCredentials = createAsyncThunk(
  'credentials/fetchCredentials',
  async ({ businessId }, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(`/api/businesses/${businessId}/credentials`)
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch credentials')
    }
  }
)

export const connectCredential = createAsyncThunk(
  'credentials/connectCredential',
  async ({ businessId, provider, accessToken, scopes }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(`/api/businesses/${businessId}/credentials/${provider}/connect`, {
        access_token: accessToken,
        scopes: scopes || [],
      })
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to connect account')
    }
  }
)

export const revokeCredential = createAsyncThunk(
  'credentials/revokeCredential',
  async ({ businessId, provider }, { rejectWithValue }) => {
    try {
      await apiClient.delete(`/api/businesses/${businessId}/credentials/${provider}`)
      return provider
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to revoke credential')
    }
  }
)

const credentialsSlice = createSlice({
  name: 'credentials',
  initialState: {
    connections: {},
    status: 'idle',
    error: null,
  },
  reducers: {
    clearCredentials: (state) => {
      state.connections = {}
      state.status = 'idle'
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCredentials.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchCredentials.fulfilled, (state, action) => {
        state.status = 'succeeded'
        const byProvider = Object.fromEntries(action.payload.map((c) => [c.provider, c]))
        state.connections = byProvider
      })
      .addCase(fetchCredentials.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.payload
      })
      .addCase(connectCredential.fulfilled, (state, action) => {
        state.connections[action.payload.provider] = action.payload
      })
      .addCase(revokeCredential.fulfilled, (state, action) => {
        delete state.connections[action.payload]
      })
  },
})

export const { clearCredentials } = credentialsSlice.actions
export default credentialsSlice.reducer