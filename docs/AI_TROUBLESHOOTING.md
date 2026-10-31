# Diagnose AI chat and summary fallbacks

A completed simulation or HTTP 200 chat response does not prove a model call succeeded. The application can return deterministic simulation results and store a readable fallback reply when AI is unavailable. New responses explain missing credentials, rejected credentials, model access, rate limits, connection failures, or invalid output. Server logs include only the error category, status and exception type, not provider bodies or prompts.

## Native VS Code / Git Bash setup

When running Uvicorn from `backend/`, settings read **backend/.env**. The Docker file `docker/.env` is not loaded by native Uvicorn.

In `backend/.env`, configure:

```dotenv
GROQ_API_KEY=<your real Groq key, kept private>
GROQ_MODEL=openai/gpt-oss-120b
```

Groq retired `llama-3.3-70b-versatile` for free/developer accounts on August 16, 2026; committed-spend enterprise accounts were exempt. The default is now Groq's recommended `openai/gpt-oss-120b` replacement. An existing `.env` or exported environment variable still overrides the new default and must be updated explicitly. The model runs on **Groq** and still needs a **Groq key**, despite the `openai/` model-name prefix.

From `backend/` with the virtual environment active:

```bash
python ../scripts/check_ai.py
```

This sends one small structured-output probe (which may use provider quota) and prints only safe diagnostic information. It times out after 30 seconds. Share its category/message if it fails; do not share your key or .env contents. If the model shown is unexpectedly old, check whether your terminal has an exported `GROQ_MODEL` overriding the file.

After changing `.env`, fully stop Uvicorn with Ctrl+C and start it again:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then test Finance chat with `What is our current budget?` and run a short simulation for a new summary. Existing saved fallback messages will not be rewritten automatically.

## Interpret the result

| Category | Check |
| --- | --- |
| `not_configured` | Real Groq key in the .env read by this process |
| `authentication` | Key validity and whether it has been revoked |
| `permission_denied` | Groq account/project permissions |
| `model_unavailable` | Model ID and account access; migrate retired models |
| `rate_limit` | Quota/rate limits; wait before another request |
| `connection` | Server connectivity, proxy and certificate configuration |
| `provider_error` | Provider availability; retry later |
| `invalid_response` | Structured-output compatibility/validation; report this category for investigation |

## Database is a separate issue

`MongoDB unavailable ... using in-memory fallback` means MongoDB is not reachable. Restarting the backend clears fallback users, businesses and sessions. Start/configure MongoDB for persistence; fixing the Groq model does not connect MongoDB. A Hugging Face warning about unauthenticated embedding downloads is also separate from Groq authentication.

## Docker setup

Set the key and model in `docker/.env`, then recreate the backend so it receives the new environment. Backend source fixes require pulling and rebuilding the image too:

```bash
docker compose --env-file docker/.env -f docker/docker-compose.yml up -d --build --force-recreate backend
```

## Source and verification limits

- [Groq model deprecations](https://console.groq.com/docs/deprecations)
- [Groq supported models](https://console.groq.com/docs/models)

Unit/API tests exercise failure categories with fake provider errors and assert that secrets never enter replies or logs. A real account/key must pass the diagnostic before live AI functionality is considered verified.
