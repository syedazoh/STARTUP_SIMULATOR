import { useState } from 'react'
import { useDispatch } from 'react-redux'
import { fetchPendingTasks, uploadTaskAsset } from '../store/slices/tasksSlice'
import { STATUS } from '../theme/palette'

const VERDICT_COLOR = {
  approved: STATUS.good,
  rejected: STATUS.critical,
  reshoot_requested: STATUS.warning,
}

function AssetUploadCard({ businessId, task }) {
  const dispatch = useDispatch()
  const [mediaType, setMediaType] = useState('image')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [lastReview, setLastReview] = useState(null)

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) return
    setUploading(true)
    const result = await dispatch(uploadTaskAsset({ taskId: task.id, mediaType, file }))
    if (uploadTaskAsset.fulfilled.match(result)) {
      setLastReview(result.payload.agent_review)
      setFile(null)
    }
    setUploading(false)
    dispatch(fetchPendingTasks(businessId))
  }

  return (
    <div className="space-y-2">
      {lastReview && (
        <div className="text-xs rounded border-l-2 pl-2 py-1" style={{ borderColor: VERDICT_COLOR[lastReview.verdict] }}>
          <span className="font-medium" style={{ color: VERDICT_COLOR[lastReview.verdict] }}>
            {lastReview.verdict?.replace(/_/g, ' ')}
          </span>
          {lastReview.notes && <span className="text-gray-500"> — {lastReview.notes}</span>}
        </div>
      )}
      <form onSubmit={handleUpload} className="flex items-center gap-2">
        <select
          value={mediaType}
          onChange={(e) => setMediaType(e.target.value)}
          className="border rounded px-2 py-1 text-xs"
        >
          <option value="image">Image</option>
          <option value="video">Video</option>
        </select>
        <input
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="flex-1 text-xs"
        />
        <button
          type="submit"
          disabled={uploading || !file}
          className="px-3 py-1 rounded text-white text-xs font-medium disabled:opacity-50"
          style={{ backgroundColor: STATUS.good }}
        >
          {uploading ? 'Uploading…' : 'Upload'}
        </button>
      </form>
    </div>
  )
}

export default AssetUploadCard
