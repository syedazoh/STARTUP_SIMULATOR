import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient, { clearAccessToken, endSession, refreshSession, setAccessToken } from '../../api/client'

function errorMessage(error) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join('. ')
  return error.response ? 'Unable to sign in. Please try again.' : 'Cannot reach the server. Check your connection.'
}

export const login = createAsyncThunk('auth/login', async ({ email, password }, { rejectWithValue }) => {
  try {
    const { data } = await apiClient.post('/api/auth/login', { email, password })
    setAccessToken(data.access_token)
    return data
  } catch (error) { return rejectWithValue(errorMessage(error)) }
})
export const register = createAsyncThunk('auth/register', async ({ email, password }, { rejectWithValue }) => {
  try {
    await apiClient.post('/api/auth/register', { email, password })
  } catch (error) { return rejectWithValue(errorMessage(error)) }
  try {
    const { data } = await apiClient.post('/api/auth/login', { email, password })
    setAccessToken(data.access_token)
    return data
  } catch (error) {
    // The account exists even if automatic sign-in fails. Do not ask the user
    // to submit registration again; send them to the dedicated login screen.
    return rejectWithValue({ accountCreated: true, message: errorMessage(error) })
  }
})
export const restoreSession = createAsyncThunk('auth/restore', () => refreshSession())
export const fetchMe = createAsyncThunk('auth/fetchMe', async () => (await apiClient.get('/api/auth/me')).data)
export const logout = createAsyncThunk('auth/logout', async (_, { rejectWithValue }) => {
  try { await endSession() }
  catch { return rejectWithValue('Could not confirm server logout. Please retry.') }
})

const initialState = { token: null, user: null, initialized: false, status: 'idle', error: null }
const authSlice = createSlice({
  name: 'auth', initialState,
  reducers: {
    clearAuthError: (state) => { state.error = null },
    clearAuth: (state) => { state.token = null; state.user = null; state.initialized = true },
    tokenRefreshed: (state, action) => { state.token = action.payload; state.initialized = true },
  },
  extraReducers: (builder) => {
    for (const thunk of [login, register, restoreSession]) {
      builder.addCase(thunk.pending, (state) => { state.status = 'loading'; state.error = null })
      builder.addCase(thunk.fulfilled, (state, action) => {
        state.token = action.payload.access_token
        state.user = null
        state.initialized = true
        state.status = 'succeeded'
      })
      builder.addCase(thunk.rejected, (state, action) => {
        state.initialized = true
        state.status = 'failed'
        state.error = thunk === restoreSession ? null : action.payload?.message || action.payload
      })
    }
    builder.addCase(fetchMe.fulfilled, (state, action) => { state.user = action.payload })
    builder.addCase(logout.fulfilled, () => ({ ...initialState, initialized: true }))
    builder.addCase(logout.rejected, (state, action) => { state.error = action.payload })
  },
})
export const { clearAuth, clearAuthError, tokenRefreshed } = authSlice.actions
export { clearAccessToken }
export default authSlice.reducer
