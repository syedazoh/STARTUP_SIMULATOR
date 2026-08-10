FROM node:18-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
# Optional extra trust root for dev machines behind TLS-inspecting antivirus/proxies
# (e.g. Avast, Zscaler). Empty by default and harmless; fill locally, never commit real content.
COPY docker-ca/extra-ca.crt* /usr/local/share/ca-certificates/
RUN find /usr/local/share/ca-certificates -name '*.example' -delete && update-ca-certificates
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
COPY package*.json ./
# npm ci false-positives "Missing @esbuild/... from lock file" here: rollup (a
# transitive vite dependency) ships its own internal `overrides` block pinning
# esbuild for its own tooling, which trips npm ci's stricter lockfile
# validation. npm install resolves the same, already-in-sync lockfile correctly.
RUN npm install
# npm intermittently skips installing rollup's own platform-specific native
# binary even though it's in the lockfile (npm/cli#4828), crashing vite at
# runtime with "Cannot find module @rollup/rollup-linux-x64-*". Force it.
RUN npm install --no-save @rollup/rollup-linux-x64-gnu
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]