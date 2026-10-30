import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import axios from 'axios'

async function clientModule() {
  const instances = []
  const removed = []
  const context = vm.createContext({
    localStorage: { removeItem: (key) => removed.push(key) },
    navigator: {}, window: { location: { origin: 'https://example.test' } },
  })
  const dependency = new vm.SyntheticModule(['default'], function () {
    this.setExport('default', { create(options) {
      const client = axios.create(options)
      instances.push(client)
      return client
    } })
  }, { context })
  const source = await readFile(new URL('../src/api/client.js', import.meta.url), 'utf8')
  const module = new vm.SourceTextModule(source, {
    context, initializeImportMeta: (meta) => { meta.env = { PROD: true } },
  })
  await module.link(() => dependency)
  await module.evaluate()
  return { exports: module.namespace, instances, removed }
}

const response = (config, data = {}) => ({ config, data, status: 200, headers: {}, statusText: 'OK' })
const unauthorized = (config) => Promise.reject(new axios.AxiosError('Unauthorized', 'ERR_BAD_REQUEST', config, null,
  { config, data: {}, status: 401, headers: {}, statusText: 'Unauthorized' }))

test('bearer tokens remain in memory and legacy storage is removed', async () => {
  const { exports: api, instances: [client], removed } = await clientModule()
  assert.deepEqual(removed, ['simulator_token'])
  assert.equal(client.defaults.baseURL, 'https://example.test')
  api.setAccessToken('memory-token')
  client.defaults.adapter = async (config) => {
    assert.equal(config.headers.Authorization, 'Bearer memory-token')
    assert.equal(config.withCredentials, true)
    return response(config)
  }
  await client.get('/api/businesses')
})

test('simultaneous 401 responses share a refresh and retry with the new token', async () => {
  const { exports: api, instances: [client, session] } = await clientModule()
  let refreshes = 0
  session.defaults.adapter = async (config) => {
    refreshes++
    await new Promise((resolve) => setTimeout(resolve, 10))
    return response(config, { access_token: 'new-token' })
  }
  client.defaults.adapter = (config) => config.headers.Authorization === 'Bearer new-token'
    ? Promise.resolve(response(config)) : unauthorized(config)
  api.setAccessToken('expired')
  await Promise.all([client.get('/api/a'), client.get('/api/b')])
  assert.equal(refreshes, 1)
})

test('login errors retain their backend response without refreshing', async () => {
  const { instances: [client, session] } = await clientModule()
  session.defaults.adapter = () => { throw new Error('Must not refresh a login failure') }
  client.defaults.adapter = unauthorized
  await assert.rejects(client.post('/api/auth/login'), (error) => error.response.status === 401)
})

test('failed refresh signs out without a retry loop', async () => {
  const { exports: api, instances: [client, session] } = await clientModule()
  let signedOut = 0
  let refreshes = 0
  api.setOnUnauthorized(() => signedOut++)
  client.defaults.adapter = unauthorized
  session.defaults.adapter = (config) => { refreshes++; return unauthorized(config) }
  await assert.rejects(client.get('/api/businesses'))
  assert.equal(refreshes, 1)
  assert.equal(signedOut, 1)
})

test('logout prevents an in-flight refresh from restoring a bearer token', async () => {
  const { exports: api, instances: [, session] } = await clientModule()
  let release
  let started
  const entered = new Promise((resolve) => { started = resolve })
  session.defaults.adapter = async (config) => {
    if (config.url === '/api/auth/logout') return response(config)
    started()
    await new Promise((resolve) => { release = resolve })
    return response(config, { access_token: 'stale-token' })
  }
  const restoring = api.refreshSession()
  await entered
  await api.endSession()
  release()
  await assert.rejects(restoring, /Session changed/)
})
