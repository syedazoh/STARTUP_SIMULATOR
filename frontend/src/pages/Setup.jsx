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

const STEPS = [
  'Company',
  'Starting numbers',
  'Brand',
  'Product & Marketing',
  'Finance & Ops',
  'Review',
]

const STEP_META = {
  1: {
    title: 'Tell us about your company',
    subtitle: 'These details configure your Finance, Marketing, HR, and Operations agents.',
  },
  2: {
    title: 'Set your starting numbers',
    subtitle: 'Defaults are fine if you are not sure — you can create more businesses later.',
  },
  3: {
    title: 'Describe your brand',
    subtitle: 'Optional, but the more context you give here, the less generic your agents’ decisions will be. You can edit this later.',
  },
  4: {
    title: 'Product and marketing context',
    subtitle: 'Optional. Separate list values with commas.',
  },
  5: {
    title: 'Finance and operations context',
    subtitle: 'Optional. Set spending guardrails and support expectations.',
  },
  6: {
    title: 'Review and finish',
    subtitle: 'Confirm your setup, then launch your business.',
  },
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

function SummaryBlock({ title, items }) {
  return (
    <div className="bg-gray-50 rounded p-4">
      <h3 className="text-sm font-semibold text-gray-800 mb-2">{title}</h3>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1">
        {items.map(([label, value]) => (
          <div key={label} className="text-sm">
            <dt className="text-xs text-gray-500">{label}</dt>
            <dd className="text-gray-900 break-words">{value || '—'}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

function Setup() {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { status: businessStatus, error: businessError } = useSelector((state) => state.business)
  const { status: profileStatus, error: profileError } = useSelector((state) => state.businessProfile)

  const [step, setStep] = useState(1)
  const [business, setBusiness] = useState(BUSINESS_DEFAULTS)
  const [profile, setProfile] = useState(PROFILE_DEFAULTS)
  const [businessId, setBusinessId] = useState(null)

  const inputClass = 'w-full border rounded px-3 py-2 text-sm'
  const meta = STEP_META[step]
  const totalSteps = STEPS.length

  const updateBusiness = (field) => (e) => {
    const raw = e.target.value
    const isNumeric = field !== 'companyName' && field !== 'industry'
    setBusiness((prev) => ({ ...prev, [field]: isNumeric ? Number(raw) : raw }))
  }

  const updateProfile = (section, field) => (e) => {
    const value = e.target.value
    setProfile((prev) => ({ ...prev, [section]: { ...prev[section], [field]: value } }))
  }

  const goToDashboard = () => navigate(`/b/${businessId}/dashboard`)

  const handleNext = async (e) => {
    e.preventDefault()
    if (step < 2 || businessId) {
      setStep((s) => s + 1)
      return
    }
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
      setStep((s) => s + 1)
    }
  }

  const handleFinish = async (e) => {
    e.preventDefault()
    const result = await dispatch(saveBusinessProfile({ businessId, profile: toProfilePayload(profile) }))
    if (saveBusinessProfile.fulfilled.match(result)) {
      goToDashboard()
    }
  }

  const label = ({ text, htmlFor }) => (
    <label className="block text-xs text-gray-500 mb-1" htmlFor={htmlFor}>
      {text}
    </label>
  )

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-4">
            <div>
              {label({ text: 'Company name', htmlFor: 'companyName' })}
              <input
                id="companyName"
                required
                value={business.companyName}
                onChange={updateBusiness('companyName')}
                className={inputClass}
              />
            </div>
            <div>
              {label({ text: 'Industry', htmlFor: 'industry' })}
              <input
                id="industry"
                required
                value={business.industry}
                onChange={updateBusiness('industry')}
                placeholder="e.g. SaaS, Retail, Fintech"
                className={inputClass}
              />
            </div>
          </div>
        )

      case 2:
        return (
          <div className="grid grid-cols-2 gap-4">
            <div>
              {label({ text: 'Starting budget ($)', htmlFor: 'startingBudget' })}
              <input
                id="startingBudget"
                type="number"
                min="0"
                value={business.startingBudget}
                onChange={updateBusiness('startingBudget')}
                className={inputClass}
              />
            </div>
            <div>
              {label({ text: 'Starting customers', htmlFor: 'startingCustomerBase' })}
              <input
                id="startingCustomerBase"
                type="number"
                min="0"
                value={business.startingCustomerBase}
                onChange={updateBusiness('startingCustomerBase')}
                className={inputClass}
              />
            </div>
            <div>
              {label({ text: 'Starting headcount', htmlFor: 'startingHeadcount' })}
              <input
                id="startingHeadcount"
                type="number"
                min="0"
                value={business.startingHeadcount}
                onChange={updateBusiness('startingHeadcount')}
                className={inputClass}
              />
            </div>
            <div>
              {label({ text: 'Starting resources', htmlFor: 'startingResources' })}
              <input
                id="startingResources"
                type="number"
                min="0"
                value={business.startingResources}
                onChange={updateBusiness('startingResources')}
                className={inputClass}
              />
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <input
                placeholder="Voice / tone (e.g. playful, direct)"
                value={profile.brand.voiceTone}
                onChange={updateProfile('brand', 'voiceTone')}
                className={inputClass}
              />
              <input
                placeholder="Target audience"
                value={profile.brand.targetAudience}
                onChange={updateProfile('brand', 'targetAudience')}
                className={inputClass}
              />
            </div>
            <input
              placeholder="Mission statement"
              value={profile.brand.missionStatement}
              onChange={updateProfile('brand', 'missionStatement')}
              className={inputClass}
            />
            <input
              placeholder="Competitors (comma-separated)"
              value={profile.brand.competitors}
              onChange={updateProfile('brand', 'competitors')}
              className={inputClass}
            />
          </div>
        )

      case 4:
        return (
          <div className="space-y-6">
            <fieldset className="space-y-3">
              <legend className="text-sm font-semibold text-gray-800">Product</legend>
              <input
                placeholder="Description"
                value={profile.product.description}
                onChange={updateProfile('product', 'description')}
                className={inputClass}
              />
              <div className="grid grid-cols-2 gap-4">
                <input
                  placeholder="Pricing model (e.g. subscription)"
                  value={profile.product.pricingModel}
                  onChange={updateProfile('product', 'pricingModel')}
                  className={inputClass}
                />
                <input
                  placeholder="Price points (comma-separated)"
                  value={profile.product.pricePoints}
                  onChange={updateProfile('product', 'pricePoints')}
                  className={inputClass}
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
                  className={inputClass}
                />
                <input
                  placeholder="Posting frequency"
                  value={profile.marketing.postingFrequency}
                  onChange={updateProfile('marketing', 'postingFrequency')}
                  className={inputClass}
                />
                <input
                  placeholder="Content do's (comma-separated)"
                  value={profile.marketing.contentDos}
                  onChange={updateProfile('marketing', 'contentDos')}
                  className={inputClass}
                />
                <input
                  placeholder="Content don'ts (comma-separated)"
                  value={profile.marketing.contentDonts}
                  onChange={updateProfile('marketing', 'contentDonts')}
                  className={inputClass}
                />
              </div>
            </fieldset>
          </div>
        )

      case 5:
        return (
          <div className="space-y-6">
            <fieldset className="space-y-3">
              <legend className="text-sm font-semibold text-gray-800">Finance</legend>
              <div className="grid grid-cols-3 gap-4">
                <input
                  type="number"
                  min="0"
                  placeholder="Monthly budget cap"
                  value={profile.finance.monthlyBudgetCap}
                  onChange={updateProfile('finance', 'monthlyBudgetCap')}
                  className={inputClass}
                />
                <input
                  placeholder="Currency"
                  value={profile.finance.currency}
                  onChange={updateProfile('finance', 'currency')}
                  className={inputClass}
                />
                <input
                  placeholder="Spend categories (comma-separated)"
                  value={profile.finance.spendCategories}
                  onChange={updateProfile('finance', 'spendCategories')}
                  className={inputClass}
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
                  className={inputClass}
                />
                <input
                  placeholder="Escalation policy"
                  value={profile.operations.escalationPolicy}
                  onChange={updateProfile('operations', 'escalationPolicy')}
                  className={inputClass}
                />
              </div>
            </fieldset>
          </div>
        )

      case 6:
        return (
          <div className="space-y-4">
            <SummaryBlock
              title="Company"
              items={[
                ['Name', business.companyName],
                ['Industry', business.industry],
              ]}
            />
            <SummaryBlock
              title="Starting numbers"
              items={[
                ['Budget ($)', business.startingBudget],
                ['Customers', business.startingCustomerBase],
                ['Headcount', business.startingHeadcount],
                ['Resources', business.startingResources],
              ]}
            />
            <SummaryBlock
              title="Brand"
              items={[
                ['Voice / tone', profile.brand.voiceTone],
                ['Mission statement', profile.brand.missionStatement],
                ['Target audience', profile.brand.targetAudience],
                ['Competitors', profile.brand.competitors],
              ]}
            />
            <SummaryBlock
              title="Product & Marketing"
              items={[
                ['Product description', profile.product.description],
                ['Pricing model', profile.product.pricingModel],
                ['Price points', profile.product.pricePoints],
                ['Channels', profile.marketing.activeChannels],
                ['Posting frequency', profile.marketing.postingFrequency],
                ["Do's", profile.marketing.contentDos],
                ["Don'ts", profile.marketing.contentDonts],
              ]}
            />
            <SummaryBlock
              title="Finance & Operations"
              items={[
                ['Monthly budget cap', profile.finance.monthlyBudgetCap],
                ['Currency', profile.finance.currency],
                ['Spend categories', profile.finance.spendCategories],
                ['Support hours', profile.operations.supportHours],
                ['Escalation policy', profile.operations.escalationPolicy],
              ]}
            />
          </div>
        )

      default:
        return null
    }
  }

  const isCreating = step === 2 && businessStatus === 'loading'
  const isFinishing = step === 6 && profileStatus === 'loading'

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-2xl bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-6">
          {STEPS.map((stepLabel, i) => {
            const n = i + 1
            const active = n === step
            const done = n < step
            return (
              <div key={stepLabel} className="flex flex-1 items-center">
                <div className="flex flex-col items-center">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold text-white"
                    style={{
                      backgroundColor: done || active ? STATUS.good : undefined,
                      color: done || active ? '#fff' : undefined,
                      ...(done || active ? {} : { backgroundColor: '#e5e7eb', color: '#6b7280' }),
                    }}
                  >
                    {n}
                  </div>
                  <span
                    className={`text-[10px] mt-1 ${active ? 'text-gray-900 font-medium' : 'text-gray-400'}`}
                  >
                    {stepLabel}
                  </span>
                </div>
                {n < totalSteps ? (
                  <div
                    className="flex-1 h-px mx-2"
                    style={{ backgroundColor: n < step ? STATUS.good : '#e5e7eb' }}
                  />
                ) : null}
              </div>
            )
          })}
        </div>

        <h1 className="text-xl font-bold text-gray-900 mb-1">{meta.title}</h1>
        <p className="text-sm text-gray-500 mb-6">{meta.subtitle}</p>

        <form onSubmit={step === 6 ? handleFinish : handleNext}>
          {renderStep()}

          {(step === 2 || step === 6) && <ErrorBanner message={step === 2 ? businessError : profileError} />}

          <div className="flex gap-3 mt-8">
            {step > 1 ? (
              <button
                type="button"
                onClick={() => setStep((s) => s - 1)}
                className="flex-1 py-2 rounded text-sm font-medium border text-gray-600"
              >
                Back
              </button>
            ) : (
              <div className="flex-1" />
            )}
            <button
              type="submit"
              disabled={isCreating || isFinishing}
              className="flex-1 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
              style={{ backgroundColor: STATUS.good }}
            >
              {step === 6
                ? isFinishing
                  ? 'Finishing…'
                  : 'Finish setup'
                : isCreating
                  ? 'Creating…'
                  : step === totalSteps - 1
                    ? 'Review setup'
                    : 'Continue'}
            </button>
          </div>

          {step > 2 && step < 6 && (
            <div className="text-center mt-4">
              <button
                type="button"
                onClick={goToDashboard}
                className="text-xs text-gray-500 underline"
              >
                Skip profile setup and go to dashboard
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}

export default Setup
