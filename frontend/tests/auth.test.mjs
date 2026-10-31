import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import toolkit from '@reduxjs/toolkit'

async function authModule(post) {
  const tokens = []
  const context = vm.createContext({})
  const redux = new vm.SyntheticModule(['createAsyncThunk', 'createSlice'], function () {
    this.setExport('createAsyncThunk', toolkit.createAsyncThunk)
    this.setExport('createSlice', toolkit.createSlice)
  }, { context })
  const client = new vm.SyntheticModule(
    ['default', 'clearAccessToken', 'endSession', 'refreshSession', 'setAccessToken'],
    function () {
      this.setExport('default', { post })
      this.setExport('clearAccessToken', () => {})
      this.setExport('endSession', async () => {})
      this.setExport('refreshSession', async () => ({ access_token: 'restored' }))
      this.setExport('setAccessToken', (token) => tokens.push(token))
    }, { context })
  const source = await readFile(new URL('../src/store/slices/authSlice.js', import.meta.url), 'utf8')
  const module = new vm.SourceTextModule(source, { context })
  await module.link((specifier) => specifier === '@reduxjs/toolkit' ? redux : client)
  await module.evaluate()
  const auth = module.namespace
  const store = toolkit.configureStore({ reducer: { auth: auth.default } })
  return { auth, store, tokens }
}

const credentials = { email: 'owner@example.test', password: 'test-password-123' }
const failure = (detail) => ({ response: { data: { detail } } })

test('registration still creates the account then automatically signs in', async () => {
  const calls = []
  const { auth, store, tokens } = await authModule(async (url, body) => {
    calls.push({ url, body })
    return { data: url.endsWith('/register') ? { id: 'owner' } : { access_token: 'access' } }
  })
  const result = await store.dispatch(auth.register(credentials))
  assert.equal(auth.register.fulfilled.match(result), true)
  assert.deepEqual(calls.map((call) => call.url), ['/api/auth/register', '/api/auth/login'])
  assert.equal(calls[1].body.password, credentials.password)
  assert.deepEqual(tokens, ['access'])
  assert.equal(store.getState().auth.token, 'access')
})

test('an account created before failed automatic login is distinguished from failed registration', async () => {
  const { auth, store, tokens } = await authModule(async (url) => {
    if (url.endsWith('/register')) return { data: { id: 'owner' } }
    throw failure('Invalid login origin')
  })
  const result = await store.dispatch(auth.register(credentials))
  assert.equal(auth.register.rejected.match(result), true)
  assert.equal(result.payload.accountCreated, true)
  assert.equal(result.payload.message, 'Invalid login origin')
  assert.equal(store.getState().auth.error, 'Invalid login origin')
  assert.equal(store.getState().auth.token, null)
  assert.deepEqual(tokens, [])
})

test('duplicate signup error clears before login and login calls only its own endpoint', async () => {
  const calls = []
  const { auth, store } = await authModule(async (url) => {
    calls.push(url)
    if (url.endsWith('/register')) throw failure('Email already registered')
    return { data: { access_token: 'signed-in' } }
  })
  await store.dispatch(auth.register(credentials))
  assert.equal(store.getState().auth.error, 'Email already registered')
  assert.deepEqual(calls, ['/api/auth/register'])
  store.dispatch(auth.clearAuthError())
  assert.equal(store.getState().auth.error, null)
  const result = await store.dispatch(auth.login(credentials))
  assert.equal(auth.login.fulfilled.match(result), true)
  assert.deepEqual(calls, ['/api/auth/register', '/api/auth/login'])
  assert.equal(store.getState().auth.error, null)
})

test('failed login reports its own error after leaving registration', async () => {
  const { auth, store } = await authModule(async (url) => {
    throw failure(url.endsWith('/register') ? 'Email already registered' : 'Invalid email or password')
  })
  await store.dispatch(auth.register(credentials))
  store.dispatch(auth.clearAuthError())
  await store.dispatch(auth.login(credentials))
  assert.equal(store.getState().auth.error, 'Invalid email or password')
})

test('clearing screen feedback preserves the authenticated session', async () => {
  const { auth, store } = await authModule(async () => ({ data: { access_token: 'access' } }))
  await store.dispatch(auth.login(credentials))
  store.dispatch(auth.clearAuthError())
  assert.equal(store.getState().auth.token, 'access')
})
