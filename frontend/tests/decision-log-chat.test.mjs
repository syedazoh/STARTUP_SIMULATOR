import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import React from 'react'
import { transformWithEsbuild } from 'vite'

async function component(file, api, initial = {}) {
  const state = [], effects = []
  let hook = 0
  const overrides = {
    react: { default: React, useState: value => {
      const i = hook++
      if (!(i in state)) state[i] = i in initial ? initial[i] : value
      return [state[i], v => { state[i] = typeof v === 'function' ? v(state[i]) : v }]
    }, useEffect: effect => effects.push(effect), useRef: () => ({ current: null }) },
    'react-router-dom': { useParams: () => ({ businessId: 'business-1' }) },
    '../api/client': { default: api }, '../theme/palette': { STATUS: { good: 'green' } },
    './ErrorBanner': { default: 'error-banner' },
  }
  const source = await readFile(new URL(`../src/${file}`, import.meta.url), 'utf8')
  const { code } = await transformWithEsbuild("import React from 'react';\n" + source, file, { loader: 'jsx', jsx: 'transform' })
  const context = vm.createContext({ console })
  const mod = new vm.SourceTextModule(code, { context })
  await mod.link(specifier => {
    const values = overrides[specifier]
    if (!values) throw new Error(`Unexpected dependency: ${specifier}`)
    return new vm.SyntheticModule(Object.keys(values), function () {
      for (const [key, value] of Object.entries(values)) this.setExport(key, value)
    }, { context })
  })
  await mod.evaluate()
  const render = () => { hook = 0; effects.length = 0; return mod.namespace.default({ businessId: 'business-1', agentKey: 'marketing', agentLabel: 'Marketing' }) }
  const tree = render()
  return { state, effects, render, tree }
}
function find(tree, predicate) {
  if (!tree || typeof tree !== 'object') return null
  if (predicate(tree)) return tree
  for (const child of React.Children.toArray(tree.props?.children)) {
    const match = find(child, predicate)
    if (match) return match
  }
  return null
}
const flush = () => new Promise(resolve => setImmediate(resolve))

test('decision history uses the backend route and retains manual entries', async () => {
  const urls = []
  const ui = await component('pages/DecisionLog.jsx', { get: async url => {
    urls.push(url)
    return { data: url.endsWith('simulation-runs') ? [] : [
      { tick: null, event_type: 'budget_request', timestamp: '2026-01-01', data: {} },
      { tick: 1, event_type: 'budget_request', timestamp: '2026-01-01', data: {} },
    ] }
  } })
  ui.effects[0]()
  ui.effects[1]()
  await flush()
  assert.equal(urls[0], '/api/businesses/business-1/simulation/simulation-runs')
  assert.equal(ui.state[0].length, 2)
  assert.ok(find(ui.render(), e => e.type === 'span' && e.props.children === 'Manual event'))
})

test('history errors are visible and stale history responses are ignored', async () => {
  let resolve
  const ui = await component('pages/DecisionLog.jsx', { get: () => new Promise(r => { resolve = r }) }, { 3: false })
  const cleanup = ui.effects[0]()
  cleanup()
  resolve({ data: [{ run_id: 'stale' }] })
  await flush()
  assert.equal(ui.state[1].length, 0)
  const failed = await component('pages/DecisionLog.jsx', { get: async () => { throw new Error('404') } }, { 3: false })
  failed.effects[0]()
  await flush()
  assert.ok(find(failed.render(), e => e.props.role === 'alert'))
})

test('HTTP-success chat with an AI failure shows an error banner', async () => {
  const message = 'The AI request limit has been reached. Retry after 60 seconds.'
  const ui = await component('components/ChatPanel.jsx', { post: async () => ({ data: {
    ai_error: 'rate_limit', task: null,
    thread: { messages: [{ role: 'agent', content: message, created_at: '2026-01-01' }] },
  } }) }, { 1: 'Plan a campaign' })
  await find(ui.tree, e => e.type === 'form').props.onSubmit({ preventDefault() {} })
  assert.equal(ui.state[3], message)
  assert.equal(ui.state[4], null)
  assert.ok(find(ui.render(), e => e.type === 'error-banner' && e.props.message === message))
})
