# Run the complete app locally with Docker Desktop

Use Docker Desktop with **Linux containers**. Run these PowerShell commands from the repository root, the folder containing `frontend`, `backend`, and `docker`.

## First start

```powershell
# Create this file only if it does not already exist; keep existing real keys.
if (!(Test-Path docker/.env)) { Copy-Item docker/.env.example docker/.env }

docker compose --env-file docker/.env -f docker/docker-compose.yml up --build --renew-anon-volumes
```

Open **http://localhost:5173** after the frontend starts. API docs are at **http://localhost:8000/docs**.

The first backend build installs CPU PyTorch and downloads an embedding model, so it can take considerably longer than the frontend build. The frontend waits until the backend and MongoDB are healthy. Check backend logs if it is waiting.

`GROQ_API_KEY` in `docker/.env` is optional for starting the app, authentication and deterministic simulation fallbacks. Configure a real key to use AI responses and CEO plan generation. A placeholder key does not enable AI. To connect third-party accounts, also set a generated `CREDENTIAL_MASTER_KEY` and a random `SECRET_KEY` in `docker/.env`; the public development encryption key intentionally cannot store real provider credentials.

Docker settings come from **docker/.env** and the Compose service environment. A `frontend/.env` value cannot override the Docker API proxy settings supplied by Compose. Never put `http://backend:8000` in a browser-facing `VITE_API_URL`: only containers can resolve `backend`.

## Verify wiring

In another terminal at the repository root:

```powershell
docker compose --env-file docker/.env -f docker/docker-compose.yml ps
Invoke-RestMethod http://localhost:5173/api/health
```

All three services should be healthy. The health response should contain `mongo: connected`. `ai_configured: false` means the Groq key is missing or still a placeholder; it does not mean the frontend or database is disconnected.

Sign up, sign in, create a business, and refresh the browser. The session should remain available through the refresh cookie. Logging out revokes the server-side session.

| Connection | Address used |
| --- | --- |
| Browser → frontend | `http://localhost:5173` |
| Browser → API | `/api/...` on that same frontend origin |
| Vite → backend inside Docker | `http://backend:8000` |
| Backend → database inside Docker | `mongodb://mongo:27017` |
| Vite → backend without Docker | `http://localhost:8000` |

## If the frontend still fails

Collect the actual error:

```powershell
docker compose --env-file docker/.env -f docker/docker-compose.yml logs --tail 100 frontend backend mongo
```

| Symptom | Check |
| --- | --- |
| Missing Rollup/esbuild binary, invalid executable, or native module errors | Rebuild and renew the frontend dependency volume with the commands below. Host `node_modules` is excluded from the image. |
| Frontend waits without starting | Check MongoDB/backend health and backend build logs. A waiting container can be a backend problem. |
| Port 5173/8000 already allocated | Stop the other app/container using that port; Vite now fails explicitly instead of moving to an unexposed port. |
| `ECONNREFUSED` from the Vite proxy | Compose must supply `API_PROXY_TARGET=http://backend:8000`; start the complete stack rather than the frontend alone. |
| TLS certificate errors during npm/pip/model downloads | Follow the local `docker-ca/extra-ca.crt.example` guidance for your organization's trust root. Do not disable certificate verification. |
| Backend cannot parse `ALLOWED_ORIGINS` | Update to the fixed code, which accepts both CSV and JSON lists. |

For stale frontend dependencies:

```powershell
docker compose --env-file docker/.env -f docker/docker-compose.yml build --no-cache frontend
docker compose --env-file docker/.env -f docker/docker-compose.yml up --build --renew-anon-volumes
```

`--renew-anon-volumes` refreshes the frontend's anonymous dependency volume. MongoDB uses a **named** volume, which this flag preserves. Avoid `down -v` unless you deliberately want to erase local database data.

For detached operation, add `-d` to `up`. Stop without deleting database data with:

```powershell
docker compose --env-file docker/.env -f docker/docker-compose.yml down
```

## Production is separate

`docker-compose.prod.yml` uses the built frontend, backend, MongoDB and Caddy on one HTTPS origin. It also waits for MongoDB readiness. It requires production secrets, images and a configured domain; do not use it as the local development startup command. Deployment remains opt-in through Jenkins.

## Verification limits

The fixes were checked with clean Linux npm installation, frontend tests/build/lint, backend tests, official Compose schema validation, and an HTTP smoke test through Vite to FastAPI. The smoke test used the development in-memory database because this verification environment has no Docker daemon or live MongoDB service. A Docker Desktop build/start and real MongoDB persistence still need confirmation on a machine that can run containers.

Frontend CI additionally builds the development Docker image and checks its HTTP server and Docker-DNS API proxy against a clearly labelled backend stub. That check validates the frontend container; it does not replace a complete FastAPI/MongoDB Compose test.
