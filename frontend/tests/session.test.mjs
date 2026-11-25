import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import axios from 'axios'

async function clientModule(storageBlocked = false) {
  const instances = []
  const removed = []
  const context = vm.createContext({
    localStorage: { removeItem: (key) => removed.push(key) },
    navigator: {}, window: { location: { origin: 'https://example.test' } },
  })
  if (storageBlocked) Object.defineProperty(context, 'localStorage', { get() { throw new Error('Storage disabled') } })
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
  assert.equal(refreshes, 2) // One native attempt, one verified main-session bridge; no loop.
  assert.equal(signedOut, 1)
})

test('logout prevents an in-flight refresh from restoring a bearer token', async () => {
  const { exports: api, instances: [, session] } = await clientModule()
  let release
  let started
  const entered = new Promise((resolve) => { started = resolve })
  session.defaults.adapter = async (config) => {
    if (config.url === '/api/auth/legacy-logout') return response(config)
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

// Regression: private/storage-blocked browsers must still load the public app.
test('disabled browser storage does not prevent client initialization or create a bearer token', async () => {
  const { instances: [client] } = await clientModule(true)
  client.defaults.adapter = config => {
    assert.equal(config.headers.Authorization, undefined)
    return Promise.resolve(response(config))
  }
  await client.get('/public-status')
})


test('missing native refresh restores the verified main session without another password',async()=>{
 const {exports:api,instances:[client,session]}=await clientModule();const paths=[];
 session.defaults.adapter=config=>{paths.push(config.url);return config.url==='/api/auth/refresh'?unauthorized(config):Promise.resolve(response(config,{access_token:'bridged-token'}))};
 client.defaults.adapter=config=>{assert.equal(config.headers.Authorization,'Bearer bridged-token');return Promise.resolve(response(config))};
 await api.refreshSession();await client.get('/api/businesses');assert.deepEqual(paths,['/api/auth/refresh','/api/auth/legacy-session']);
});

test('identity lookup carries the active bearer; credential endpoints do not',async()=>{
 const {exports:api,instances:[client]}=await clientModule();api.setAccessToken('identity-token');
 const seen=[];client.defaults.adapter=config=>{seen.push([config.url,config.headers.Authorization]);return Promise.resolve(response(config))};
 await client.get('/api/auth/me');await client.post('/api/auth/login',{email:'fixture@example.com',password:'fixture-password'});await client.post('/api/auth/register',{email:'fixture@example.com',password:'fixture-password'});
 assert.deepEqual(seen,[['/api/auth/me','Bearer identity-token'],['/api/auth/login',undefined],['/api/auth/register',undefined]]);
});
