import { configureStore } from '@reduxjs/toolkit'
import adminReducer from './slices/adminSlice'
import agentsReducer from './slices/agentsSlice'
import authReducer from './slices/authSlice'
import businessReducer from './slices/businessSlice'
import businessProfileReducer from './slices/businessProfileSlice'
import chatReducer from './slices/chatSlice'
import credentialsReducer from './slices/credentialsSlice'
import eventsReducer from './slices/eventsSlice'
import profileReducer from './slices/profileSlice'
import simulationReducer from './slices/simulationSlice'
import tasksReducer from './slices/tasksSlice'

const store = configureStore({
  reducer: {
    admin: adminReducer,
    auth: authReducer,
    business: businessReducer,
    businessProfile: businessProfileReducer,
    agents: agentsReducer,
    chat: chatReducer,
    credentials: credentialsReducer,
    events: eventsReducer,
    profile: profileReducer,
    simulation: simulationReducer,
    tasks: tasksReducer,
  },
})

export default store
