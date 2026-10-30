import { test } from 'node:test'
import assert from 'node:assert/strict'
import http from 'node:http'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

test('Vite proxies API paths, refresh cookies, and health checks to the configured backend', async () => {
  let received
  const backend = http.createServer((request, response) => {
    received = { path: request.url, method: request.method, cookie: request.headers.cookie }
    response.setHeader('Content-Type', 'application/json')
    response.setHeader('Set-Cookie', 'simulator_refresh=rotated; HttpOnly; Path=/api/auth; SameSite=Strict')
    response.end(JSON.stringify({ mongo: 'connected' }))
  })
  await new Promise((resolve) => backend.listen(0, '127.0.0.1', resolve))
  const previous = process.env.API_PROXY_TARGET
  process.env.API_PROXY_TARGET = `http://127.0.0.1:${backend.address().port}`
  let frontend
  try {
    frontend = await createServer({
      configFile: fileURLToPath(new URL('../vite.config.js', import.meta.url)),
      server: { host: '127.0.0.1', port: 0, strictPort: false, watch: { usePolling: false } },
      logLevel: 'silent',
    })
    await frontend.listen()
    const origin = `http://127.0.0.1:${frontend.httpServer.address().port}`
    assert.equal((await fetch(origin)).status, 200)
    const css = await fetch(`${origin}/src/index.css`)
    assert.equal(css.status, 200, 'Vite must compile the actual app stylesheet')
    assert.match(await css.text(), /--tw-/, 'Tailwind must generate CSS, not leave unresolved directives')
    const health = await fetch(`${origin}/api/health`)
    assert.equal(health.status, 200)
    assert.equal((await health.json()).mongo, 'connected')
    assert.equal(received.path, '/api/health')
    const refresh = await fetch(`${origin}/api/auth/refresh`, {
      method: 'POST', headers: { Cookie: 'simulator_refresh=original', 'X-Requested-With': 'XMLHttpRequest' },
    })
    assert.equal(refresh.status, 200)
    assert.equal(received.path, '/api/auth/refresh')
    assert.equal(received.method, 'POST')
    assert.equal(received.cookie, 'simulator_refresh=original')
    assert.match(refresh.headers.get('set-cookie'), /simulator_refresh=rotated/)
  } finally {
    if (previous === undefined) delete process.env.API_PROXY_TARGET
    else process.env.API_PROXY_TARGET = previous
    await frontend?.close()
    await new Promise((resolve) => backend.close(resolve))
  }
})
