import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import React from 'react'
import * as router from 'react-router-dom'
import { transformWithEsbuild } from 'vite'

async function loadJSX(path, overrides = {}) {
  const source = await readFile(new URL(path, import.meta.url), 'utf8')
  const { code } = await transformWithEsbuild("import React from 'react';\n" + source, path, {
    loader: 'jsx', jsx: 'transform',
  })
  const context = vm.createContext({})
  const module = new vm.SourceTextModule(code, { context })
  await module.link((specifier) => {
    let exports = overrides[specifier]
    if (!exports) {
      if (specifier === 'react') exports = { default: React, useEffect: () => {} }
      else if (specifier === 'react-router-dom') exports = router
      else if (specifier === 'react-redux') exports = { useDispatch: () => () => {}, useSelector: () => ({}) }
      else if (specifier.endsWith('/palette')) exports = { STATUS: { good: 'green' } }
      else if (specifier.endsWith('/api/client')) exports = { clearAccessToken() {}, setOnToken() {}, setOnUnauthorized() {} }
      else if (specifier.endsWith('/authSlice')) exports = { clearAuth() {}, tokenRefreshed() {} }
      else exports = { default: function Stub() { return null } }
    }
    return new vm.SyntheticModule(Object.keys(exports), function () {
      for (const [key, value] of Object.entries(exports)) this.setExport(key, value)
    }, { context })
  })
  await module.evaluate()
  return module.namespace.default
}

function childWithType(element, type) {
  for (const child of React.Children.toArray(element.props?.children)) {
    if (child.type === type) return child
    const nested = child.props?.children && childWithType(child, type)
    if (nested) return nested
  }
}

test('public homepage and authenticated entry have distinct route matches', async () => {
  const App = await loadJSX('../src/App.jsx')
  const routesElement = childWithType(App(), router.Routes)
  const routes = router.createRoutesFromElements(routesElement.props.children)
  const home = router.matchRoutes(routes, '/')
  const app = router.matchRoutes(routes, '/app')
  assert.equal(home.at(-1).route.path, '/')
  assert.equal(app.at(-1).route.path, '/app')
  assert.equal(home.length, 2)
  assert.equal(app.length, 3) // ProtectedRoute -> RequireBusiness -> HomeRedirect
  assert.notEqual(home[0].route, app[0].route)
})

test('authenticated homepage enters the protected app before user profile loads', async () => {
  const Landing = await loadJSX('../src/pages/Landing.jsx', {
    'react-redux': { useSelector: (select) => select({ auth: { token: 'access', user: null } }) },
  })
  const result = Landing()
  assert.equal(result.type, router.Navigate)
  assert.equal(result.props.to, '/app')
  assert.equal(result.props.replace, true)
})

test('successful sign-in navigates to the protected entry instead of the public homepage', async () => {
  const navigations = []
  const login = () => ({ type: 'test/login' })
  login.fulfilled = { match: () => true }
  const Login = await loadJSX('../src/pages/Login.jsx', {
    react: { default: React, useEffect() {}, useState: (value) => [value, () => {}] },
    'react-redux': { useDispatch: () => async () => ({ type: 'auth/login/fulfilled' }),
      useSelector: () => ({ status: 'idle', error: null }) },
    'react-router-dom': { ...router, useNavigate: () => (...args) => navigations.push(args),
      useLocation: () => ({ state: null }) },
    '../store/slices/authSlice': { login, clearAuthError() {} },
  })
  const form = childWithType(Login(), 'form')
  await form.props.onSubmit({ preventDefault() {} })
  assert.equal(navigations.length, 1)
  assert.equal(navigations[0][0], '/app')
  assert.equal(navigations[0][1].replace, true)
})
