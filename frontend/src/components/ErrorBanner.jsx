import { STATUS } from '../theme/palette'

function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div
      className="text-sm px-3 py-2 rounded border"
      style={{ color: STATUS.critical, borderColor: STATUS.critical, backgroundColor: '#fef2f2' }}
    >
      {message}
    </div>
  )
}

export default ErrorBanner
