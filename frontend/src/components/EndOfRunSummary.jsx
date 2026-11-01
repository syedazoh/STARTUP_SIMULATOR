import { STATUS } from '../theme/palette'

function EndOfRunSummary({ summary }) {
  if (!summary) return null

  return (
    <div className="bg-white rounded-lg shadow p-5 border-l-4" style={{ borderColor: STATUS.good }}>
      <h3 className="text-sm font-semibold text-gray-500 uppercase mb-1">Strategic Retrospective</h3>
      <p className="text-lg font-semibold text-gray-900 mb-3">{summary.headline}</p>
      {summary.created_at && <p className="text-xs text-gray-500 mb-3">Recorded at {new Date(summary.created_at).toLocaleString()}. Pending tasks may change after this snapshot.</p>}

      {summary.key_decisions?.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs font-semibold text-gray-500 uppercase mb-1">Key Decisions</h4>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-0.5">
            {summary.key_decisions.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {summary.risks?.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs font-semibold uppercase mb-1" style={{ color: STATUS.serious }}>Risks</h4>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-0.5">
            {summary.risks.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-1">Recommendation</h4>
        <p className="text-sm text-gray-700">{summary.recommendation}</p>
      </div>
    </div>
  )
}

export default EndOfRunSummary
