# Deployment Runbook (AWS EC2)

There is no Terraform/IaC in this repo yet — this is a documented manual setup,
time-boxed for the FYP. Automating it with Terraform is a reasonable stretch
goal if time remains, but isn't required to demo a working deployment.

## One-time EC2 setup

1. Launch an EC2 instance — **t3.small or larger** (Mongo + Chroma + the backend's
   in-memory sentence-transformers model can OOM a t2.micro). Ubuntu 22.04 LTS is
   a safe default AMI.
2. Point a DNS `A` record at the instance's public IP (e.g. `app.example.com`).
   `APP_DOMAIN` below must match it exactly — Caddy obtains its certificate for
   that name via an ACME challenge, which won't succeed otherwise.
3. Security group: allow inbound `22` (SSH, restrict to your IP), `80`, and `443`.
   Port 80 is needed for Let's Encrypt's HTTP-01 challenge and the HTTPS redirect;
   port 443 carries all traffic. **Do not open `8000`** — the API is not published
   to the host at all (see "TLS termination" below), so there's no cleartext path
   to it.
4. SSH in and install Docker + the Compose plugin:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   sudo apt-get install -y docker-compose-plugin
   ```
   Log out/in for the group change to take effect.
5. Create a deploy directory and pull just the two files the host actually needs:
   ```bash
   mkdir -p ~/startup-simulator && cd ~/startup-simulator
   curl -o docker-compose.prod.yml https://raw.githubusercontent.com/<org>/<repo>/main/docker-compose.prod.yml
   ```
6. Create `.env` in that same directory (never committed — `.gitignore` already
   excludes `.env*`). Generate the two secret values first; the backend refuses to
   start without them:
   ```bash
   # JWT signing key — anyone holding this plus a user id can mint a valid token
   openssl rand -hex 32

   # Credential-vault envelope key — anyone holding this plus a user's wrapped
   # data key can recover that user's stored provider tokens
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   Then:
   ```
   APP_DOMAIN=app.example.com
   ACME_EMAIL=you@example.com
   ALLOWED_ORIGINS=https://app.example.com
   GROQ_API_KEY=your-real-groq-key
   GROQ_MODEL=llama-3.3-70b-versatile
   MONGO_ROOT_USERNAME=admin
   MONGO_ROOT_PASSWORD=<generate a strong one>
   SECRET_KEY=<the openssl rand -hex 32 output>
   CREDENTIAL_MASTER_KEY=<the Fernet.generate_key output>
   BACKEND_IMAGE=<account-id>.dkr.ecr.<region>.amazonaws.com/startup-simulator-backend:latest
   FRONTEND_IMAGE=<account-id>.dkr.ecr.<region>.amazonaws.com/startup-simulator-frontend:latest
   CADDY_IMAGE=<account-id>.dkr.ecr.<region>.amazonaws.com/startup-simulator-caddy:latest
   ```
   `chmod 600 .env`.
   > Both secret values are **required** — `docker-compose.prod.yml` uses `${VAR:?...}`
   > so Compose refuses to start rather than letting the backend fall back to the
   > in-repo defaults (which `backend/app/config.py` rejects when `DEBUG=false`).
7. Authenticate Docker on the host to your ECR registry once (Jenkins re-auths on
   every deploy, but you'll want this for the first manual pull too):
   ```bash
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
   ```
8. Create the ECR repositories (`startup-simulator-backend`, `startup-simulator-frontend`,
   `startup-simulator-caddy`) if they don't exist yet.

## TLS termination

`caddy` is the stack's only public ingress. It serves HTTPS on 443, redirects
port 80 to HTTPS, obtains and renews its own Let's Encrypt certificate, and
routes `/api/*` to the backend and everything else to the frontend's nginx — so
the API and the frontend bundle share one origin and no service is reachable
over cleartext HTTP.

`docker/caddy/Caddyfile` is baked into the `startup-simulator-caddy` image rather
than mounted from the host, so the TLS config always matches the commit that was
built.

The first `up -d` can fail the ACME challenge if the DNS record hasn't propagated
yet. Re-run `docker compose -f docker-compose.prod.yml logs caddy` to see the
reason; uncommenting the `acme_ca` staging line in the Caddyfile is a reasonable
way to iterate without burning rate limit while getting DNS sorted.

## Deploying

Either via Jenkins (`Jenkinsfile` at repo root — see its header comment for the
required credentials/env vars), or manually from the EC2 host:

```bash
cd ~/startup-simulator
../CODSOFT/scripts/deploy.sh   # or copy scripts/deploy.sh alongside docker-compose.prod.yml
```

Verify:
```bash
curl https://app.example.com/health
# -> {"status":"healthy","mongo":"connected","service":"startup-simulator-backend"}
curl -I https://app.example.com/
# -> HTTP/2 200
curl -I http://app.example.com/
# -> HTTP/1.1 308 (redirects to https)
```
A direct request to port 8000 should fail — nothing is published there.

## Rollback

Images are tagged with the short git commit SHA in addition to `latest`. To roll
back, set `BACKEND_IMAGE`/`FRONTEND_IMAGE`/`CADDY_IMAGE` in `.env` to the previous SHA tag and
re-run `docker compose -f docker-compose.prod.yml up -d`.

## Secrets

- `SECRET_KEY`, `CREDENTIAL_MASTER_KEY`, `GROQ_API_KEY`, and Mongo credentials live
  only in the EC2 host's `.env` (never committed) and in Jenkins' credential store
  for the pipeline's own AWS/SSH access.
- Never put real keys in `.env.example` files — see `backend/.env.example` for the
  placeholder pattern this repo follows.
- `SECRET_KEY` and `CREDENTIAL_MASTER_KEY` are not interchangeable: rotating
  `SECRET_KEY` invalidates every issued JWT (users just log in again), but rotating
  `CREDENTIAL_MASTER_KEY` without rewrapping the stored user data keys locks every
  user out of their connected accounts. To rotate it safely, run the rewrap first
  so the keys move under the new master key, then change the env var:
  ```python
  # from the backend/ directory with the venv active, replacing the old fallback:
  from app.core.crypto import rewrap_user_keys
  from app.database.mongodb import connect_to_mongo, get_database

  await connect_to_mongo()
  count = await rewrap_user_keys(get_database(), "<old-master-key>", "<new-master-key>")
  print(f"rewrapped {count} user data keys")
  ```
- The in-repo default values for these keys exist only so local dev runs out of the
  box. They are published in git history and must never be what a deployment runs
  on — which is why `config.py` fails startup when `DEBUG=false` and either is still
  the default, and why `docker-compose.prod.yml` makes both env vars required.
