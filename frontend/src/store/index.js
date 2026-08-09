import { configureStore } from '@reduxjs/toolkit'
import agentsReducer from './slices/agentsSlice'
import authReducer from './slices/authSlice'
import businessReducer from './slices/businessSlice'
import eventsReducer from './slices/eventsSlice'
import simulationReducer from './slices/simulationSlice'

const store = configureStore({
  reducer: {
    auth: authReducer,
    business: businessReducer,
    agents: agentsReducer,
    events: eventsReducer,
    simulation: simulationReducer,
  },
})

export default store
