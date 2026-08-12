import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const saveBusinessProfile = createAsyncThunk(
  'businessProfile/save',
  async ({ businessId, profile }) => {
    const response = await apiClient.post(`/api/businesses/${businessId}/profile`, profile)
    return response.data
  },
)

const businessProfileSlice = createSlice({
  name: 'businessProfile',
  initialState: {
    status: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(saveBusinessProfile.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(saveBusinessProfile.fulfilled, (state) => {
        state.status = 'succeeded'
      })
      .addCase(saveBusinessProfile.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
  },
})

export default businessProfileSlice.reducer
