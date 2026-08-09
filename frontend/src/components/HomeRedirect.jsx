import { useSelector } from 'react-redux'
import { Navigate } from 'react-router-dom'

// Landing point once auth + business existence are confirmed by the parent
// route guards — sends the user to their active (or first) business's dashboard.
function HomeRedirect() {
  const { items, activeBusinessId } = useSelector((state) => state.business)
  const targetId = activeBusinessId || items[0]?.id
  return <Navigate to={`/b/${targetId}/dashboard`} replace />
}

export default HomeRedirect
