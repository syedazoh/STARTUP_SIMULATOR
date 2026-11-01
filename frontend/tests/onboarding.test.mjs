import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import React from 'react'
import { transformWithEsbuild } from 'vite'
import { toProfilePayload } from '../src/utils/profilePayload.js'

async function setupForm(step, existingId = null) {
  const calls = [], navigations = []
  const business = { companyName: 'Back-edited name', industry: 'Software', startingBudget: 2345,
    startingCustomerBase: 12, startingHeadcount: 1, startingResources: 10 }
  let hook = 0
  const create = (payload) => ({ kind: 'create', payload })
  create.fulfilled = { match: (r) => r.type === 'created' }
  const save = (payload) => ({ kind: 'save', payload })
  save.fulfilled = { match: (r) => r.type === 'saved' }
  const overrides = {
    react: { default: React, useState: (initial) => {
      const values = [step, business, initial, existingId]
      const value = values[hook++]
      return [value, () => {}]
    } },
    'react-redux': { useDispatch: () => async (action) => {
      calls.push(action)
      return action.kind === 'create' ? { type: 'created', payload: { id: 'created-business' } } : { type: 'saved' }
    }, useSelector: (select) => select({ business: { status: 'idle' }, businessProfile: { status: 'idle' } }) },
    'react-router-dom': { useNavigate: () => (p) => navigations.push(p) },
    '../store/slices/businessSlice': { createBusiness: create },
    '../store/slices/businessProfileSlice': { saveBusinessProfile: save },
    '../utils/profilePayload': { toProfilePayload },
    '../theme/palette': { STATUS: { good: 'green' } },
  }
  const source = await readFile(new URL('../src/pages/Setup.jsx', import.meta.url), 'utf8')
  const { code } = await transformWithEsbuild("import React from 'react';\n" + source, 'Setup.jsx', { loader: 'jsx', jsx: 'transform' })
  const context = vm.createContext({})
  const mod = new vm.SourceTextModule(code, { context })
  await mod.link((specifier) => {
    const exports = overrides[specifier] || { default: () => null }
    return new vm.SyntheticModule(Object.keys(exports), function () {
      for (const [k, v] of Object.entries(exports)) this.setExport(k, v)
    }, { context })
  })
  await mod.evaluate()
  function findForm(e) {
    if (e.type === 'form') return e
    for (const child of React.Children.toArray(e.props?.children)) {
      const found = child.props && findForm(child)
      if (found) return found
    }
  }
  return { form: findForm(mod.namespace.default()), calls, navigations }
}

test('advancing before final review creates no persisted business', async () => {
  const { form, calls } = await setupForm(2)
  await form.props.onSubmit({ preventDefault() {} })
  assert.equal(calls.length, 0)
})

test('final submit saves the latest edited numbers and uses the returned business id', async () => {
  const { form, calls, navigations } = await setupForm(6)
  await form.props.onSubmit({ preventDefault() {} })
  assert.equal(calls[0].payload.company_name, 'Back-edited name')
  assert.equal(calls[0].payload.starting_budget, 2345)
  assert.equal(calls[1].payload.businessId, 'created-business')
  assert.deepEqual(navigations, ['/b/created-business/dashboard'])
})

test('profile retry reuses the business instead of creating a duplicate', async () => {
  const { form, calls, navigations } = await setupForm(6, 'already-created')
  await form.props.onSubmit({ preventDefault() {} })
  assert.equal(calls.length, 1)
  assert.equal(calls[0].kind, 'save')
  assert.equal(calls[0].payload.businessId, 'already-created')
  assert.deepEqual(navigations, ['/b/already-created/dashboard'])
})
