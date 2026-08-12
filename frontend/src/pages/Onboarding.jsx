import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { createBusiness } from '../store/slices/businessSlice'
import { saveBusinessProfile } from '../store/slices/businessProfileSlice'
import ErrorBanner from '../components/ErrorBanner'
import { STATUS } from '../theme/palette'

const BUSINESS_DEFAULTS = {
  companyName: '',
  industry: '',
  startingBudget: 100000,
  startingCustomerBase: 1000,
  startingHeadcount: 50,
  startingResources: 10000,
}

// Mirrors BusinessProfileIn on the backend (business_profile_schemas.py) — this
// is the canonical context object every agent's prompt draws from, so the
// wizard captures it up front rather than leaving agents to work from just a
// company name and industry.
const PROFILE_DEFAULTS = {
  brand: { voiceTone: '', missionStatement: '', targetAudience: '', competitors: '' },
  product: { description: '', pricingModel: '', pricePoints: '' },
  marketing: { activeChannels: '', postingFrequency: '', contentDos: '', contentDonts: '' },
  finance: { monthlyBudgetCap: '', currency: 'USD', spendCategories: '' },
  operations: { supportHours: '', escalationPolicy: '' },
}

const toList = (raw) =>
  raw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

function toProfilePayload(profile) {
  return {
    brand: {
      voice_tone: profile.brand.voiceTone,
      mission_statement: profile.brand.missionStatement,
      target_audience: profile.brand.targetAudience,
      competitors: toList(profile.brand.competitors),
    },
    product: {
      description: profile.product.description,
      pricing_model: profile.product.pricingModel,
      price_points: toList(profile.product.pricePoints).map(Number).filter((n) => !Number.isNaN(n)),
    },
    marketing: {
      active_channels: toList(profile.marketing.activeChannels),
      posting_frequency: profile.marketing.postingFrequency,
      content_dos: toList(profile.marketing.contentDos),
      content_donts: toList(profile.marketing.contentDonts),
    },
    finance: {
      monthly_budget_cap: Number(profile.finance.monthlyBudgetCap) || 0,
      currency: profile.finance.currency || 'USD',
      spend_categories: toList(profile.finance.spendCategories),
    },
    operations: {
      support_hours: profile.operations.supportHours,
      escalation_policy: profile.operations.escalationPolicy,
    },
  }
}

function Onboarding() {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { status: businessStatus, error: businessError } = useSelector((state) => state.business)
  const { status: profileStatus, error: profileError } = useSelector((state) => state.businessProfile)

  const [step, setStep] = useState(1)
  const [business, setBusiness] = useState(BUSINESS_DEFAULTS)
  const [profile, setProfile] = useState(PROFILE_DEFAULTS)
  const [businessId, setBusinessId] = useState(null)

  const updateBusiness = (field) => (e) => {
    const raw = e.target.value
    const isNumeric = field !== 'companyName' && field !== 'industry'
    setBusiness((prev) => ({ ...prev, [field]: isNumeric ? Number(raw) : raw }))
  }

  const updateProfile = (section, field) => (e) => {
    const value = e.target.value
    setProfile((prev) => ({ ...prev, [section]: { ...prev[section], [field]: value } }))
  }

  const handleCreateBusiness = async (e) => {
    e.preventDefault()
    const result = await dispatch(
      createBusiness({
        company_name: business.companyName,
        industry: business.industry,
        starting_budget: business.startingBudget,
        starting_customer_base: business.startingCustomerBase,
        starting_headcount: business.startingHeadcount,
        starting_resources: business.startingResources,
      }),
    )
    if (createBusiness.fulfilled.match(result)) {
      setBusinessId(result.payload.id)
      setStep(2)
    }
  }

  const goToDashboard = () => navigate(`/b/${businessId}/dashboard`)

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    const result = await dispatch(saveBusinessProfile({ businessId, profile: toProfilePayload(profile) }))
    if (saveBusinessProfile.fulfilled.match(result)) {
      goToDashboard()
    }
  }

  if (step === 2) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-2xl bg-white rounded-lg shadow p-6">
          <h1 className="text-xl font-bold text-gray-900 mb-1">Tell your agents about the business</h1>
          <p className="text-sm text-gray-500 mb-6">
            Optional, but the more context you give here, the less generic your agents' decisions will be.
            You can edit this later. Separate list values with commas.
          </p>

          <form onSubmit={handleSaveProfile} className="space-y-6">
            <fieldset className="space-y-3">
              <legend className="text-sm font-semibold text-gray-800">Brand</legend>
              <div className="grid grid-cols-2 gap-4">
                <input
                  placeholder="Voice / tone (e.g. playful, direct)"
                  value={profile.brand.voiceTone}
                  onChange={updateProfile('brand', 'voiceTone')}
                  className="border rounded px-3 py-2 text-sm"
                />
                <input
                  placeholder="Target audience"
                  value={profile.brand.targetAudience}
                  onChange={updateProfile('brand', 'targetAudience')}
                  className="border rounded px-3 py-2 text-sm"
                />
              </div>
              <input
                placeholder="Mission statement"
                value={profile.brand.missionStatement}
                onChange={updateProfile('brand', 'missionStatement')}
                className="w-full border rounded px-3 py-2 text-sm"
              />
              <input
                placeholder="Competitors (comma-separated)"
                value={profile.brand.competitors}
                onChange={updateProfile('brand', 'competitors')}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </fieldset>

            <fieldset className="space-y-3">
              <legend className="text-sm font-semibold text-gray-800">Product</legend>
              <input
                placeholder="Description"
                value={profile.product.description}
                onChange={updateProfile('product', 'description')}
                className="w-full border rounded px-3 py-2 text-sm"
              />
              <div className="grid grid-cols-2 gap-4">
                <input
                  placeholder="Pricing model (e.g. subscription)"
                  value={profile.product.pricingModel}
                  onChange={updateProfile('product', 'pricingModel')}
                  className="border rounded px-3 py-2 text-sm"
                />
                <input
                  placeholder="Price points (comma-separated)"
                  value={profile.product.pricePoints}
                  onChange={updateProfile('product', 'pricePoints')}
                  className="border rounded px-3 py-2 text-sm"
                />
              </div>
            </fieldset>

            <fieldset className="space-y-3">
              <legend className="text-sm font-semibold text-gray-800">Marketing</legend>
              <div className="grid grid-cols-2 gap-4">
                <input
                  placeholder="Active channels (e.g. instagram, twitter)"
                  value={profile.marketing.activeChannels}
                  onChange={updateProfile('marketing', 'activeChannels')}
                  className="border rounded px-3 py-2 text-sm"
                />
                <input
                  placeholder="Posting frequency"
                  value={profile.marketing.postingFrequency}
                  onChange={updateProfile('marketing', 'postingFrequency')}
                  className="border rounded px-3 py-2 text-sm"
                />
                <input
                  placeholder="Content do's (comma-separated)"
                  value={profile.marketing.contentDos}
                  onChange={updateProfile('marketing', 'contentDos')}
                  className="border rounded px-3 py-2 text-sm"
                />
                <input
                  placeholder="Content don'ts (comma-separated)"
                  value={profile.marketing.contentDonts}
                  onChange={updateProfile('marketing', 'contentDonts')}
                  className="border rounded px-3 py-2 text-sm"
                />
              </div>
            </fieldset>

            <fieldset className="space-y-3">
              <legend className="text-sm font-semibold text-gray-800">Finance</legend>
              <div className="grid grid-cols-3 gap-4">
                <input
                  type="number"
                  min="0"
                  placeholder="Monthly budget cap"
                  value={profile.finance.monthlyBudgetCap}
                  onChange={updateProfile('finance', 'monthlyBudgetCap')}
                  className="border rounded px-3 py-2 text-sm"
                />
                <input
                  placeholder="Currency"
                  value={profile.finance.currency}
                  onChange={updateProfile('finance', 'currency')}
                  className="border rounded px-3 py-2 text-sm"
                />
                <input
                  placeholder="Spend categories (comma-separated)"
                  value={profile.finance.spendCategories}
                  onChange={updateProfile('finance', 'spendCategories')}
                  className="border rounded px-3 py-2 text-sm"
                />
              </div>
            </fieldset>

            <fieldset className="space-y-3">
              <legend className="text-sm font-semibold text-gray-800">Operations</legend>
              <div className="grid grid-cols-2 gap-4">
                <input
                  placeholder="Support hours"
                  value={profile.operations.supportHours}
                  onChange={updateProfile('operations', 'supportHours')}
                  className="border rounded px-3 py-2 text-sm"
                />
                <input
                  placeholder="Escalation policy"
                  value={profile.operations.escalationPolicy}
                  onChange={updateProfile('operations', 'escalationPolicy')}
                  className="border rounded px-3 py-2 text-sm"
                />
              </div>
            </fieldset>

            <ErrorBanner message={profileError} />

            <div className="flex gap-3">
              <button
                type="button"
                onClick={goToDashboard}
                className="flex-1 py-2 rounded text-sm font-medium border text-gray-600"
              >
                Skip for now
              </button>
              <button
                type="submit"
                disabled={profileStatus === 'loading'}
                className="flex-1 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
                style={{ backgroundColor: STATUS.good }}
              >
                {profileStatus === 'loading' ? 'Saving…' : 'Save and continue'}
              </button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg bg-white rounded-lg shadow p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-1">Set up your business</h1>
        <p className="text-sm text-gray-500 mb-6">
          These starting values configure your Finance, Marketing, HR, and Operations agents.
          Defaults are fine if you're not sure — you can create more businesses later.
        </p>

        <form onSubmit={handleCreateBusiness} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1" htmlFor="companyName">Company name</label>
            <input
              id="companyName"
              required
              value={business.companyName}
              onChange={updateBusiness('companyName')}
              className="w-full border rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1" htmlFor="industry">Industry</label>
            <input
              id="industry"
              required
              value={business.industry}
              onChange={updateBusiness('industry')}
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
                value={business.startingBudget}
                onChange={updateBusiness('startingBudget')}
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
                value={business.startingCustomerBase}
                onChange={updateBusiness('startingCustomerBase')}
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
                value={business.startingHeadcount}
                onChange={updateBusiness('startingHeadcount')}
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
                value={business.startingResources}
                onChange={updateBusiness('startingResources')}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
          </div>

          <ErrorBanner message={businessError} />

          <button
            type="submit"
            disabled={businessStatus === 'loading'}
            className="w-full py-2 rounded text-white text-sm font-medium disabled:opacity-50"
            style={{ backgroundColor: STATUS.good }}
          >
            {businessStatus === 'loading' ? 'Creating…' : 'Next: add business context'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Onboarding
