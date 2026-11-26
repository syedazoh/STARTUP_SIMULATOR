import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

// pending_approval, needs_changes, and awaiting_asset are all still
// actionable by the owner — the first two via approve/reject/request
// changes, the last via uploading a file (Phase 4). Fetched unfiltered and
// narrowed here since the API only takes one status value per call.
const ACTIONABLE_STATUSES = new Set(['pending_approval', 'needs_changes', 'awaiting_asset', 'pending_ceo_review', 'needs_revision', 'ceo_reviewing'])

export const fetchPendingTasks = createAsyncThunk('tasks/fetchPending', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/tasks`, { params: { actionable: true } })
  return response.data.filter((task) => ACTIONABLE_STATUSES.has(task.status))
})

function taskError(error, fallback) {
  const status = error.response?.status
  if (status === 401) return 'Your session expired. Sign in again before reviewing this task.'
  if (status === 403) return 'You do not have permission to update this task.'
  if (status === 429) return 'Too many requests. Wait briefly, then refresh before retrying.'
  const detail = error.response?.data?.detail
  if ([400, 404, 409, 422].includes(status) && typeof detail === 'string' && detail.trim()) {
    return detail.slice(0, 600)
  }
  return fallback
}

export const approveTask = createAsyncThunk('tasks/approve', async (task, { rejectWithValue }) => {
  const taskId = typeof task === 'string' ? task : task.taskId
  try {
    const response = await apiClient.post(`/api/tasks/${taskId}/approve`, { expected_fingerprint: typeof task === 'string' ? undefined : task.expectedFingerprint })
    return response.data
  } catch (error) {
    return rejectWithValue(taskError(error, 'Could not approve the task. Check the backend connection and refresh its current status before retrying.'))
  }
})

export const rejectTask = createAsyncThunk('tasks/reject', async ({ taskId, ownerFeedback }, { rejectWithValue }) => {
  try {
    const response = await apiClient.post(`/api/tasks/${taskId}/reject`, { owner_feedback: ownerFeedback })
    return response.data
  } catch (error) {
    return rejectWithValue(taskError(error, 'Could not reject the task. Check the backend connection and refresh before retrying.'))
  }
})

export const requestTaskChanges = createAsyncThunk(
  'tasks/requestChanges',
  async ({ taskId, ownerFeedback, expectedFingerprint }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(`/api/tasks/${taskId}/request-changes`, {
        owner_feedback: ownerFeedback,
        expected_fingerprint: expectedFingerprint,
      })
      return response.data
    } catch (error) {
      return rejectWithValue(taskError(error, 'Could not request a revision. Your task may still be processing; refresh before retrying.'))
    }
  },
)

// Upload doesn't always clear the task out of the queue — a rejected/reshoot
// verdict leaves it awaiting_asset again — so this doesn't touch `items`
// itself; the caller re-dispatches fetchPendingTasks to pick up whatever
// status the task landed on.
export const uploadTaskAsset = createAsyncThunk(
  'tasks/uploadAsset',
  async ({ taskId, mediaType, file }) => {
    const formData = new FormData()
    formData.append('media_type', mediaType)
    formData.append('file', file)
    const response = await apiClient.post(`/api/tasks/${taskId}/assets`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
)

function removeTask(state, taskId) {
  state.items = state.items.filter((t) => t.id !== taskId)
}

const tasksSlice = createSlice({
  name: 'tasks',
  initialState: {
    items: [],
    status: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchPendingTasks.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(fetchPendingTasks.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.items = action.payload
      })
      .addCase(fetchPendingTasks.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
      .addCase(approveTask.fulfilled, (state, action) => removeTask(state, action.payload.id))
      .addCase(rejectTask.fulfilled, (state, action) => removeTask(state, action.payload.id))
      .addCase(requestTaskChanges.fulfilled, (state, action) => {
        const index = state.items.findIndex(task => task.id === action.payload.id)
        if (ACTIONABLE_STATUSES.has(action.payload.status)) {
          if (index === -1) state.items.push(action.payload)
          else state.items[index] = action.payload
        } else removeTask(state, action.payload.id)
      })
  },
})

export default tasksSlice.reducer
