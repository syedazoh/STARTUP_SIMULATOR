import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchAdminBusinesses = createAsyncThunk(
  'admin/fetchAdminBusinesses',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get('/api/admin/businesses')
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch businesses')
    }
  }
)

export const fetchAdminBusinessDetail = createAsyncThunk(
  'admin/fetchAdminBusinessDetail',
  async ({ businessId }, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(`/api/admin/businesses/${businessId}`)
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch business detail')
    }
  }
)

export const fetchAdminSystemHealth = createAsyncThunk(
  'admin/fetchAdminSystemHealth',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get('/api/admin/system-health')
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch system health')
    }
  }
)

export const fetchAdminAuditLogs = createAsyncThunk(
  'admin/fetchAdminAuditLogs',
  async ({ businessId, limit = 100 }, { rejectWithValue }) => {
    try {
      const params = new URLSearchParams()
      if (businessId) params.append('business_id', businessId)
      params.append('limit', limit.toString())
      const response = await apiClient.get(`/api/admin/audit-logs?${params}`)
      return response.data
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch audit logs')
    }
  }
)

const adminSlice = createSlice({
  name: 'admin',
  initialState: {
    businesses: [],
    selectedBusiness: null,
    systemHealth: null,
    auditLogs: [],
    status: 'idle',
    error: null,
  },
  reducers: {
    clearAdminState: (state) => {
      state.businesses = []
      state.selectedBusiness = null
      state.systemHealth = null
      state.auditLogs = []
      state.status = 'idle'
      state.error = null
    },
    clearSelectedBusiness: (state) => {
      state.selectedBusiness = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAdminBusinesses.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchAdminBusinesses.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.businesses = action.payload
      })
      .addCase(fetchAdminBusinesses.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.payload
      })
      .addCase(fetchAdminBusinessDetail.fulfilled, (state, action) => {
        state.selectedBusiness = action.payload
      })
      .addCase(fetchAdminSystemHealth.fulfilled, (state, action) => {
        state.systemHealth = action.payload
      })
      .addCase(fetchAdminAuditLogs.fulfilled, (state, action) => {
        state.auditLogs = action.payload
      })
  },
})

export const { clearAdminState, clearSelectedBusiness } = adminSlice.actions
export default adminSlice.reducer