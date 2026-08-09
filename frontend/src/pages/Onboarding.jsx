import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { createBusiness } from '../store/slices/businessSlice'
import ErrorBanner from '../components/ErrorBanner'
import { STATUS } from '../theme/palette'

const DEFAULTS = {
  companyName: '',
  industry: '',
  startingBudget: 100000,
  startingCustomerBase: 1000,
  startingHeadcount: 50,
  startingResources: 10000,
}

function Onboarding() {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { status, error } = useSelector((state) => state.business)
  const [form, setForm] = useState(DEFAULTS)

  const update = (field) => (e) => {
    const raw = e.target.value
    const isNumeric = field !== 'companyName' && field !== 'industry'
    setForm((prev) => ({ ...prev, [field]: isNumeric ? Number(raw) : raw }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await dispatch(
      createBusiness({
        company_name: form.companyName,
        industry: form.industry,
        starting_budget: form.startingBudget,
        starting_customer_base: form.startingCustomerBase,
        starting_headcount: form.startingHeadcount,
        starting_resources: form.startingResources,
      }),
    )
    if (createBusiness.fulfilled.match(result)) {
      navigate(`/b/${result.payload.id}/dashboard`)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg bg-white rounded-lg shadow p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-1">Set up your business</h1>
        <p className="text-sm text-gray-500 mb-6">
          These starting values configure your Finance, Marketing, HR, and Operations agents.
          Defaults are fine if you're not sure — you can create more businesses later.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1" htmlFor="companyName">Company name</label>
            <input
              id="companyName"
              required
              value={form.companyName}
              onChange={update('companyName')}
              className="w-full border rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1" htmlFor="industry">Industry</label>
            <input
              id="industry"
              required
              value={form.industry}
              onChange={update('industry')}
              placeholder="e.g. SaaS, Retail, Fintech"
              className="w-full border rounded px-3 py-2 text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1" htmlFor="startingBudget">
                Starting budget ($)
              </label>
              <input
                id="startingBudget"
                type="number"
                min="0"
                value={form.startingBudget}
                onChange={update('startingBudget')}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1" htmlFor="startingCustomerBase">
                Starting customers
              </label>
              <input
                id="startingCustomerBase"
                type="number"
                min="0"
                value={form.startingCustomerBase}
                onChange={update('startingCustomerBase')}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1" htmlFor="startingHeadcount">
                Starting headcount
              </label>
              <input
                id="startingHeadcount"
                type="number"
                min="0"
                value={form.startingHeadcount}
                onChange={update('startingHeadcount')}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1" htmlFor="startingResources">
                Starting resources
              </label>
              <input
                id="startingResources"
                type="number"
                min="0"
                value={form.startingResources}
                onChange={update('startingResources')}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
          </div>

          <ErrorBanner message={error} />

          <button
            type="submit"
            disabled={status === 'loading'}
            className="w-full py-2 rounded text-white text-sm font-medium disabled:opacity-50"
            style={{ backgroundColor: STATUS.good }}
          >
            {status === 'loading' ? 'Creating…' : 'Create business'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Onboarding
