import { combineReducers, configureStore } from '@reduxjs/toolkit'
import { createDataScopeMiddleware } from './dataScope'
import agentsReducer from './slices/agentsSlice'
import authReducer from './slices/authSlice'
import businessReducer from './slices/businessSlice'
import businessProfileReducer from './slices/businessProfileSlice'
import eventsReducer from './slices/eventsSlice'
import profileReducer from './slices/profileSlice'
import simulationReducer from './slices/simulationSlice'
import tasksReducer from './slices/tasksSlice'

const reducers = {
    auth: authReducer,
    business: businessReducer,
    businessProfile: businessProfileReducer,
    agents: agentsReducer,
    events: eventsReducer,
    profile: profileReducer,
    simulation: simulationReducer,
    tasks: tasksReducer,
}
const combined = combineReducers(reducers)
const store = configureStore({
  reducer: (state, action) => {
    if (action.type === 'app/resetSessionData' && state) state = { auth: state.auth }
    if (action.type === 'app/resetBusinessData' && state) {
      state = { auth: state.auth, business: state.business }
    }
    return combined(state, action)
  },
  middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(createDataScopeMiddleware()),
})

export default store
