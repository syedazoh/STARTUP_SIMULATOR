import { configureStore } from '@reduxjs/toolkit'
import agentsReducer from './slices/agentsSlice'
import authReducer from './slices/authSlice'
import businessReducer from './slices/businessSlice'
import businessProfileReducer from './slices/businessProfileSlice'
import eventsReducer from './slices/eventsSlice'
import simulationReducer from './slices/simulationSlice'
import tasksReducer from './slices/tasksSlice'

const store = configureStore({
  reducer: {
    auth: authReducer,
    business: businessReducer,
    businessProfile: businessProfileReducer,
    agents: agentsReducer,
    events: eventsReducer,
    simulation: simulationReducer,
    tasks: tasksReducer,
  },
})

export default store
