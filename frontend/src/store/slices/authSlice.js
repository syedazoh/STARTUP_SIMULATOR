import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient, { TOKEN_STORAGE_KEY } from '../../api/client'

export const register = createAsyncThunk('auth/register', async ({ email, password }) => {
  await apiClient.post('/api/auth/register', { email, password })
  const loginResponse = await apiClient.post('/api/auth/login', { email, password })
  return loginResponse.data
})

export const login = createAsyncThunk('auth/login', async ({ email, password }) => {
  const response = await apiClient.post('/api/auth/login', { email, password })
  return response.data
})

export const fetchMe = createAsyncThunk('auth/fetchMe', async () => {
  const response = await apiClient.get('/api/auth/me')
  return response.data
})

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    token: localStorage.getItem(TOKEN_STORAGE_KEY),
    user: null,
    status: 'idle',
    error: null,
  },
  reducers: {
    logout: (state) => {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      state.token = null
      state.user = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(register.fulfilled, (state, action) => {
        state.token = action.payload.access_token
        localStorage.setItem(TOKEN_STORAGE_KEY, action.payload.access_token)
        state.status = 'succeeded'
      })
      .addCase(login.fulfilled, (state, action) => {
        state.token = action.payload.access_token
        localStorage.setItem(TOKEN_STORAGE_KEY, action.payload.access_token)
        state.status = 'succeeded'
        state.error = null
      })
      .addCase(login.rejected, (state, action) => {
        state.status = 'failed'
        state.error = 'Invalid email or password'
      })
      .addCase(register.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
      .addCase(fetchMe.fulfilled, (state, action) => {
        state.user = action.payload
      })
  },
})

export const { logout } = authSlice.actions
export default authSlice.reducer
