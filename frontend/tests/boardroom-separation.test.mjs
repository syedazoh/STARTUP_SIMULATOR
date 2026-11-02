import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const app = readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8')
const dashboard = readFileSync(new URL('../src/pages/Dashboard.jsx', import.meta.url), 'utf8')
test('boardroom route renders dedicated page instead of Dashboard', () => {
  assert.match(app, /import Boardroom from '\.\/pages\/Boardroom'/)
  assert.match(app, /path="\/b\/:businessId\/boardroom" element={<Boardroom \/>}/)
  assert.doesNotMatch(app, /Dashboard initialBoardroom/)
})
test('command center no longer embeds full boardroom', () => {
  assert.doesNotMatch(dashboard, /<Boardroom3D/)
  assert.doesNotMatch(dashboard, /initialBoardroom/)
})
