// Converts between the flat, comma-joined-string form shape used by the
// onboarding wizard (Setup.jsx) and the post-onboarding profile edit page
// (BusinessProfile.jsx), and the nested API shape BusinessProfileIn expects
// (backend/app/models/business_profile_schemas.py).

export const toList = (raw) =>
  (raw || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

export function toProfilePayload(profile) {
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

export const PROFILE_FORM_DEFAULTS = {
  brand: { voiceTone: '', missionStatement: '', targetAudience: '', competitors: '' },
  product: { description: '', pricingModel: '', pricePoints: '' },
  marketing: { activeChannels: '', postingFrequency: '', contentDos: '', contentDonts: '' },
  finance: { monthlyBudgetCap: '', currency: 'USD', spendCategories: '' },
  operations: { supportHours: '', escalationPolicy: '' },
}

// Inverse of toProfilePayload — prefills the edit form from a
// BusinessProfileOut response.
export function fromProfilePayload(data) {
  if (!data) return PROFILE_FORM_DEFAULTS
  return {
    brand: {
      voiceTone: data.brand?.voice_tone || '',
      missionStatement: data.brand?.mission_statement || '',
      targetAudience: data.brand?.target_audience || '',
      competitors: (data.brand?.competitors || []).join(', '),
    },
    product: {
      description: data.product?.description || '',
      pricingModel: data.product?.pricing_model || '',
      pricePoints: (data.product?.price_points || []).join(', '),
    },
    marketing: {
      activeChannels: (data.marketing?.active_channels || []).join(', '),
      postingFrequency: data.marketing?.posting_frequency || '',
      contentDos: (data.marketing?.content_dos || []).join(', '),
      contentDonts: (data.marketing?.content_donts || []).join(', '),
    },
    finance: {
      monthlyBudgetCap: data.finance?.monthly_budget_cap ?? '',
      currency: data.finance?.currency || 'USD',
      spendCategories: (data.finance?.spend_categories || []).join(', '),
    },
    operations: {
      supportHours: data.operations?.support_hours || '',
      escalationPolicy: data.operations?.escalation_policy || '',
    },
  }
}
