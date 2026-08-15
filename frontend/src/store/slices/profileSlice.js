import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchBusinessProfile = createAsyncThunk(
  'profile/fetchBusinessProfile',
  async ({ businessId }, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(`/api/businesses/${businessId}/profile`)
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch profile')
    }
  }
)

export const upsertBusinessProfile = createAsyncThunk(
  'profile/upsertBusinessProfile',
  async ({ businessId, profile }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(`/api/businesses/${businessId}/profile`, profile)
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to save profile')
    }
  }
)

export const addProfileContext = createAsyncThunk(
  'profile/addProfileContext',
  async ({ businessId, label, text }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(`/api/businesses/${businessId}/profile/context`, { label, text })
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to add context')
    }
  }
)

const profileSlice = createSlice({
  name: 'profile',
  initialState: {
    profile: null,
    status: 'idle',
    error: null,
  },
  reducers: {
    clearProfile: (state) => {
      state.profile = null
      state.status = 'idle'
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchBusinessProfile.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchBusinessProfile.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.profile = action.payload
      })
      .addCase(fetchBusinessProfile.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.payload
      })
      .addCase(upsertBusinessProfile.fulfilled, (state, action) => {
        state.profile = action.payload
      })
      .addCase(addProfileContext.fulfilled, (state, action) => {
        state.profile = action.payload
      })
  },
})

export const { clearProfile } = profileSlice.actions
export default profileSlice.reducer