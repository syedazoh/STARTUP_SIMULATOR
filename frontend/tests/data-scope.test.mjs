import { test } from 'node:test'
import assert from 'node:assert/strict'
import toolkit from '@reduxjs/toolkit'
import { createDataScopeMiddleware } from '../src/store/dataScope.js'

function storeFixture() {
  return toolkit.configureStore({
    reducer: (state = { business: { activeBusinessId: 'A' }, rows: [] }, action) => {
      if (action.type === 'business/setActiveBusiness') return { ...state, business: { activeBusinessId: action.payload } }
      if (['app/resetBusinessData', 'app/resetSessionData'].includes(action.type)) return { ...state, rows: [] }
      if (action.type === 'rows/load/fulfilled') return { ...state, rows: action.payload }
      return state
    },
    middleware: (base) => base().concat(createDataScopeMiddleware()),
  })
}
const pending = (id) => ({ type: 'rows/load/pending', meta: { requestId: id, requestStatus: 'pending' } })
const fulfilled = (id, payload) => ({ type: 'rows/load/fulfilled', payload, meta: { requestId: id, requestStatus: 'fulfilled' } })

test('late response cannot repopulate data after changing businesses', () => {
  const store = storeFixture()
  store.dispatch(pending('A-request'))
  store.dispatch({ type: 'business/setActiveBusiness', payload: 'B' })
  store.dispatch(pending('B-request'))
  store.dispatch(fulfilled('B-request', ['B-data']))
  store.dispatch(fulfilled('A-request', ['A-data']))
  assert.deepEqual(store.getState().rows, ['B-data'])
})

test('logout clears data and rejects in-flight results from the old account', () => {
  const store = storeFixture()
  store.dispatch(pending('initial'))
  store.dispatch(fulfilled('initial', ['private']))
  store.dispatch(pending('late'))
  store.dispatch({ type: 'auth/logout/pending', meta: { requestId: 'logout', requestStatus: 'pending' } })
  store.dispatch(fulfilled('late', ['private']))
  assert.deepEqual(store.getState().rows, [])
})

test('ordinary asynchronous results still reach the reducers', () => {
  const store = storeFixture()
  store.dispatch(pending('current'))
  store.dispatch(fulfilled('current', ['current-data']))
  assert.deepEqual(store.getState().rows, ['current-data'])
})

test('creating a business invalidates prior business responses after accepting creation', () => {
  const store = storeFixture()
  store.dispatch(pending('old'))
  store.dispatch({ type: 'business/create/pending', meta: { requestId: 'create', requestStatus: 'pending' } })
  store.dispatch({ type: 'business/create/fulfilled', payload: { id: 'new' }, meta: { requestId: 'create', requestStatus: 'fulfilled' } })
  store.dispatch(fulfilled('old', ['old-data']))
  assert.deepEqual(store.getState().rows, [])
})
