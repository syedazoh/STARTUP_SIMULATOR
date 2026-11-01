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

## Bounded requests and rejected structured responses

All configured Groq calls share one queue on the backend event loop, across
businesses, departments and model temperatures. The supported deployment is still
one backend process. There is one active AI request, at most 16 admitted requests,
a 30-second overall deadline (including queueing), and at most two provider
attempts. SDK retries are disabled so agent graphs cannot multiply this budget.
`AI_MIN_REQUEST_INTERVAL_SECONDS` defaults to 2; provider `Retry-After` takes
precedence. Long cooldowns return an unavailable result without waiting or
sending an early retry. Rate limits can still be reached through token/daily
quotas or other applications sharing the provider account.

Replies use Groq JSON object mode with the full output schema in a system
instruction and Pydantic validation before any action can be requested. They do
not use function calling merely to format a chat reply. This also accommodates
CEO plans with open-ended action payloads. Invalid output cannot create a task.

Safe diagnostics now distinguish `invalid_request`, `structured_output` and
`context_length` from a generic invalid response. Logs retain only known provider
error codes and known parameter names; they never include provider error
messages, failed generations, prompts, headers or credentials. Unknown codes are
omitted. Chat displays an error banner even when the HTTP request itself succeeds;
a CEO fallback is marked as an unavailable AI review rather than a successful
review. Do not automatically repeat an unchanged 400/401/403/404 request.

The supplied marketing-chat 400 log did not include its provider reason, so its
exact cause cannot be proven retrospectively. The explicit format fixes the
function-calling output path, and future rejected requests expose safe diagnostic
categories and allowlisted fields. Live account success must still be checked
locally with `python ../scripts/check_ai.py`; do not post credentials or raw
provider responses.

References: [Groq structured outputs and JSON object mode](https://console.groq.com/docs/structured-outputs)
and [Groq Retry-After headers](https://console.groq.com/docs/rate-limits).

## Local decision history

The history page requests `/api/businesses/{id}/simulation/simulation-runs`.
Manual events with a null/missing tick remain visible beside simulated events.
The in-memory store sorts nulls before values in ascending order (after them in
descending order), instead of comparing `None` with an integer. A run-history
load failure is shown separately from the decision log.
