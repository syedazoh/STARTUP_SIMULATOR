import { useSelector } from 'react-redux'
import { useNavigate, useParams } from 'react-router-dom'

// Swaps the `:businessId` URL segment via navigation rather than a Redux-only
// write — keeps the active business bookmarkable/shareable and avoids stale
// closures in the dashboard/agent pages' polling effects.
function BusinessSwitcher() {
  const navigate = useNavigate()
  const { businessId } = useParams()
  const { items } = useSelector((state) => state.business)

  const handleChange = (e) => {
    const newId = e.target.value
    const path = window.location.pathname.replace(`/b/${businessId}`, `/b/${newId}`)
    navigate(path)
  }

  if (items.length === 0) return null

  return (
    <select
      value={businessId}
      onChange={handleChange}
      className="w-full text-sm border rounded px-2 py-1.5 bg-white"
    >
      {items.map((b) => (
        <option key={b.id} value={b.id}>
          {b.company_name}
        </option>
      ))}
    </select>
  )
}

export default BusinessSwitcher
