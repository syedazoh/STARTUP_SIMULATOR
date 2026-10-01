import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useParams } from 'react-router-dom'
import { addProfileContext, fetchBusinessProfile, upsertBusinessProfile } from '../store/slices/profileSlice'
import ErrorBanner from '../components/ErrorBanner'
import { STATUS } from '../theme/palette'
import { fromProfilePayload, toProfilePayload, PROFILE_FORM_DEFAULTS } from '../utils/profilePayload'

const inputClass = 'w-full border rounded px-3 py-2 text-sm'

function BusinessProfile() {
  const { businessId } = useParams()
  const dispatch = useDispatch()
  const { profile, status, error } = useSelector((state) => state.profile)

  const [form, setForm] = useState(PROFILE_FORM_DEFAULTS)
  const [saved, setSaved] = useState(false)
  const [noteLabel, setNoteLabel] = useState('')
  const [noteText, setNoteText] = useState('')
  const [prevProfile, setPrevProfile] = useState(profile)
  if (profile !== prevProfile) {
    setPrevProfile(profile)
    if (profile) setForm(fromProfilePayload(profile))
  }

  useEffect(() => {
    dispatch(fetchBusinessProfile({ businessId }))
  }, [dispatch, businessId])

  const updateField = (section, field) => (e) => {
    const value = e.target.value
    setForm((prev) => ({ ...prev, [section]: { ...prev[section], [field]: value } }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaved(false)
    const result = await dispatch(upsertBusinessProfile({ businessId, profile: toProfilePayload(form) }))
    if (upsertBusinessProfile.fulfilled.match(result)) {
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    }
  }

  const handleAddNote = async (e) => {
    e.preventDefault()
    if (!noteLabel.trim() || !noteText.trim()) return
    const result = await dispatch(addProfileContext({ businessId, label: noteLabel, text: noteText }))
    if (addProfileContext.fulfilled.match(result)) {
      setNoteLabel('')
      setNoteText('')
    }
  }

  if (status === 'loading' && !profile) {
    return <div className="max-w-3xl mx-auto px-4 py-6 text-sm text-gray-400">Loading…</div>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Business Profile</h1>
          <p className="text-sm text-gray-500 mt-1">
            The brand voice, product, and guardrails your agents draw on for every decision — edit
            it any time and the changes apply to the next agent prompt.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-gray-800 mb-2">Brand</legend>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="brand-voice-tone">
                  Voice / tone
                </label>
                <input
                  id="brand-voice-tone"
                  value={form.brand.voiceTone}
                  onChange={updateField('brand', 'voiceTone')}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="brand-target-audience">
                  Target audience
                </label>
                <input
                  id="brand-target-audience"
                  value={form.brand.targetAudience}
                  onChange={updateField('brand', 'targetAudience')}
                  className={inputClass}
                />
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1" htmlFor="brand-mission">
                Mission statement
              </label>
              <input
                id="brand-mission"
                value={form.brand.missionStatement}
                onChange={updateField('brand', 'missionStatement')}
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1" htmlFor="brand-competitors">
                Competitors (comma-separated)
              </label>
              <input
                id="brand-competitors"
                value={form.brand.competitors}
                onChange={updateField('brand', 'competitors')}
                className={inputClass}
              />
            </div>
          </fieldset>

          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-gray-800 mb-2">Product</legend>
            <div>
              <label className="block text-xs text-gray-500 mb-1" htmlFor="product-description">
                Description
              </label>
              <input
                id="product-description"
                value={form.product.description}
                onChange={updateField('product', 'description')}
                className={inputClass}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="product-pricing-model">
                  Pricing model
                </label>
                <input
                  id="product-pricing-model"
                  value={form.product.pricingModel}
                  onChange={updateField('product', 'pricingModel')}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="product-price-points">
                  Price points (comma-separated)
                </label>
                <input
                  id="product-price-points"
                  value={form.product.pricePoints}
                  onChange={updateField('product', 'pricePoints')}
                  className={inputClass}
                />
              </div>
            </div>
          </fieldset>

          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-gray-800 mb-2">Marketing</legend>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="marketing-channels">
                  Active channels
                </label>
                <input
                  id="marketing-channels"
                  value={form.marketing.activeChannels}
                  onChange={updateField('marketing', 'activeChannels')}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="marketing-frequency">
                  Posting frequency
                </label>
                <input
                  id="marketing-frequency"
                  value={form.marketing.postingFrequency}
                  onChange={updateField('marketing', 'postingFrequency')}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="marketing-dos">
                  Content do&apos;s (comma-separated)
                </label>
                <input
                  id="marketing-dos"
                  value={form.marketing.contentDos}
                  onChange={updateField('marketing', 'contentDos')}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="marketing-donts">
                  Content don&apos;ts (comma-separated)
                </label>
                <input
                  id="marketing-donts"
                  value={form.marketing.contentDonts}
                  onChange={updateField('marketing', 'contentDonts')}
                  className={inputClass}
                />
              </div>
            </div>
          </fieldset>

          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-gray-800 mb-2">Finance</legend>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="finance-budget-cap">
                  Monthly budget cap
                </label>
                <input
                  id="finance-budget-cap"
                  type="number"
                  min="0"
                  value={form.finance.monthlyBudgetCap}
                  onChange={updateField('finance', 'monthlyBudgetCap')}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="finance-currency">
                  Currency
                </label>
                <input
                  id="finance-currency"
                  value={form.finance.currency}
                  onChange={updateField('finance', 'currency')}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="finance-spend-categories">
                  Spend categories (comma-separated)
                </label>
                <input
                  id="finance-spend-categories"
                  value={form.finance.spendCategories}
                  onChange={updateField('finance', 'spendCategories')}
                  className={inputClass}
                />
              </div>
            </div>
          </fieldset>

          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-gray-800 mb-2">Operations</legend>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="ops-support-hours">
                  Support hours
                </label>
                <input
                  id="ops-support-hours"
                  value={form.operations.supportHours}
                  onChange={updateField('operations', 'supportHours')}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1" htmlFor="ops-escalation-policy">
                  Escalation policy
                </label>
                <input
                  id="ops-escalation-policy"
                  value={form.operations.escalationPolicy}
                  onChange={updateField('operations', 'escalationPolicy')}
                  className={inputClass}
                />
              </div>
            </div>
          </fieldset>

          <ErrorBanner message={error} />

          <button
            type="submit"
            disabled={status === 'loading'}
            className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
            style={{ backgroundColor: STATUS.good }}
          >
            {status === 'loading' ? 'Saving…' : saved ? 'Saved ✓' : 'Save profile'}
          </button>
        </form>

        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Custom context notes</h3>
            <p className="text-xs text-gray-400 mt-1">
              Freeform notes injected into every agent&apos;s prompt alongside the fields above.
            </p>
          </div>

          {profile?.custom_context?.length > 0 ? (
            <div className="space-y-2">
              {profile.custom_context.map((note, i) => (
                <div key={i} className="border-l-2 pl-3 py-1" style={{ borderColor: STATUS.good }}>
                  <div className="text-sm font-medium text-gray-900">{note.label}</div>
                  <p className="text-sm text-gray-600">{note.text}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">No notes yet.</p>
          )}

          <form onSubmit={handleAddNote} className="flex gap-2">
            <div className="flex-1">
              <label className="sr-only" htmlFor="note-label">
                Note label
              </label>
              <input
                id="note-label"
                value={noteLabel}
                onChange={(e) => setNoteLabel(e.target.value)}
                placeholder="Label"
                className={inputClass}
              />
            </div>
            <div className="flex-[2]">
              <label className="sr-only" htmlFor="note-text">
                Note text
              </label>
              <input
                id="note-text"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Note"
                className={inputClass}
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 rounded text-white text-sm font-medium"
              style={{ backgroundColor: STATUS.good }}
            >
              Add
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}

export default BusinessProfile
