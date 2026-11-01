// Drop async results issued before an account/business boundary. This also
// guards mutations whose responses arrive after their original page unmounts.
export function createDataScopeMiddleware() {
  let generation = 0
  const requests = new Map()
  return ({ dispatch, getState }) => (next) => (action) => {
    const sessionBoundary = ['auth/logout/pending', 'auth/login/pending', 'auth/register/pending', 'auth/clearAuth'].includes(action.type)
    const boundary = sessionBoundary
      || (action.type === 'business/setActiveBusiness' && action.payload !== getState().business.activeBusinessId)
    if (boundary) {
      generation += 1
      requests.clear()
      dispatch({ type: sessionBoundary ? 'app/resetSessionData' : 'app/resetBusinessData' })
    }
    const id = action.meta?.requestId
    if (id && action.meta.requestStatus === 'pending') requests.set(id, generation)
    if (id && ['fulfilled', 'rejected'].includes(action.meta.requestStatus)) {
      const issued = requests.get(id)
      requests.delete(id)
      if (issued !== generation) return action
    }
    // Creation changes activeBusinessId in its reducer, before Layout can
    // announce the new route. Invalidate prior data after accepting this result.
    if (action.type === 'business/create/fulfilled') {
      generation += 1
      requests.clear()
      dispatch({ type: 'app/resetBusinessData' })
    }
    return next(action)
  }
}
