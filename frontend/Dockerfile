FROM node:22-bookworm-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
# Optional extra trust root for dev machines behind TLS-inspecting antivirus/proxies
# (e.g. Avast, Zscaler). Empty by default and harmless; fill locally, never commit real content.
COPY docker-ca/extra-ca.crt* /usr/local/share/ca-certificates/
RUN find /usr/local/share/ca-certificates -name '*.example' -delete && update-ca-certificates
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
COPY package*.json ./
# Use the lockfile and install native optional dependencies for this container's
# architecture. .dockerignore prevents host node_modules from overwriting them.
RUN npm ci --include=optional
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
