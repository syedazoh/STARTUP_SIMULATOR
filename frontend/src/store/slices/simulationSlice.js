import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchSimulationStatus = createAsyncThunk('simulation/fetchStatus', async (businessId) => {
  const response = await apiClient.get(`/api/businesses/${businessId}/simulation/status`)
  return response.data
})

export const startSimulation = createAsyncThunk(
  'simulation/start',
  async ({ businessId, ticks, durationSeconds, minInterval, maxInterval }) => {
    const response = await apiClient.post(`/api/businesses/${businessId}/simulation/start`, {
      ticks: ticks ?? null,
      duration_seconds: durationSeconds ?? null,
      min_interval: minInterval ?? 0.5,
      max_interval: maxInterval ?? 2.0,
    })
    return response.data
  },
)

export const stopSimulation = createAsyncThunk('simulation/stop', async (businessId) => {
  const response = await apiClient.post(`/api/businesses/${businessId}/simulation/stop`)
  return response.data
})

export const pauseSimulation = createAsyncThunk('simulation/pause', async (businessId) => {
  const response = await apiClient.post(`/api/businesses/${businessId}/simulation/pause`)
  return response.data
})

export const resumeSimulation = createAsyncThunk('simulation/resume', async (businessId) => {
  const response = await apiClient.post(`/api/businesses/${businessId}/simulation/resume`)
  return response.data
})

export const fetchRunSummary = createAsyncThunk(
  'simulation/fetchSummary',
  async ({ businessId, runId }) => {
    const response = await apiClient.get(
      `/api/businesses/${businessId}/simulation/runs/${runId}/summary`,
    )
    return response.data
  },
)

const simulationSlice = createSlice({
  name: 'simulation',
  initialState: {
    isRunning: false,
    isPaused: false,
    tickCount: 0,
    decisionLogSize: 0,
    runId: null,
    summary: null,
    error: null,
  },
  reducers: {
    clearSummary: (state) => {
      state.summary = null
    },
    resetSimulationState: (state) => {
      state.isRunning = false
      state.isPaused = false
      state.tickCount = 0
      state.decisionLogSize = 0
      state.runId = null
      state.summary = null
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchSimulationStatus.fulfilled, (state, action) => {
        state.isRunning = action.payload.is_running
        state.isPaused = action.payload.is_paused
        state.tickCount = action.payload.tick_count
        state.decisionLogSize = action.payload.decision_log_size
        state.runId = action.payload.run_id
      })
      .addCase(startSimulation.fulfilled, (state, action) => {
        state.isRunning = true
        state.isPaused = false
        state.runId = action.payload.run_id
        state.summary = null
      })
      .addCase(startSimulation.rejected, (state, action) => {
        state.error = action.error.message
      })
      .addCase(stopSimulation.fulfilled, (state) => {
        state.isRunning = false
        state.isPaused = false
      })
      .addCase(stopSimulation.rejected, (state, action) => {
        state.error = action.error.message
      })
      .addCase(pauseSimulation.fulfilled, (state) => {
        state.isPaused = true
      })
      .addCase(resumeSimulation.fulfilled, (state) => {
        state.isPaused = false
      })
      .addCase(fetchRunSummary.fulfilled, (state, action) => {
        state.summary = action.payload
      })
  },
})

export const { clearSummary, resetSimulationState } = simulationSlice.actions
export default simulationSlice.reducer
