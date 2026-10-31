import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

// pending_approval, needs_changes, and awaiting_asset are all still
// actionable by the owner — the first two via approve/reject/request
// changes, the last via uploading a file (Phase 4). Fetched unfiltered and
// narrowed here since the API only takes one status value per call.
const ACTIONABLE_STATUSES = new Set(['pending_approval', 'needs_changes', 'awaiting_asset', 'pending_ceo_review', 'needs_revision', 'ceo_reviewing'])

export const fetchPendingTasks = createAsyncThunk('tasks/fetchPending', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/tasks`)
  return response.data.filter((task) => ACTIONABLE_STATUSES.has(task.status))
})

export const approveTask = createAsyncThunk('tasks/approve', async (taskId) => {
  const response = await apiClient.post(`/api/tasks/${taskId}/approve`)
  return response.data
})

export const rejectTask = createAsyncThunk('tasks/reject', async ({ taskId, ownerFeedback }) => {
  const response = await apiClient.post(`/api/tasks/${taskId}/reject`, { owner_feedback: ownerFeedback })
  return response.data
})

export const requestTaskChanges = createAsyncThunk(
  'tasks/requestChanges',
  async ({ taskId, ownerFeedback }) => {
    const response = await apiClient.post(`/api/tasks/${taskId}/request-changes`, {
      owner_feedback: ownerFeedback,
    })
    return response.data
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
      .addCase(requestTaskChanges.fulfilled, (state, action) => removeTask(state, action.payload.id))
  },
})

export default tasksSlice.reducer
