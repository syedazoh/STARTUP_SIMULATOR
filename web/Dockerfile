# Repository-root context; web owns runtime dependencies. No Vite install needed.
FROM node:24-alpine AS dependencies
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN --mount=type=secret,id=build_ca \
    if [ -r /run/secrets/build_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/build_ca; fi; \
    npm ci --ignore-scripts

FROM node:24-alpine AS builder
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app
COPY --from=dependencies /app/web/node_modules ./web/node_modules
COPY web ./web
COPY frontend/tests/studio.test.mjs ./frontend/tests/studio.test.mjs
COPY frontend/src/studio ./frontend/src/studio
COPY frontend/src/landing ./frontend/src/landing
COPY frontend/src/onboarding ./frontend/src/onboarding
COPY frontend/src/appearance ./frontend/src/appearance
COPY frontend/src/config/agentConfig.js ./frontend/src/config/agentConfig.js
COPY frontend/src/components/boardroom ./frontend/src/components/boardroom
WORKDIR /app/web
RUN npm test && npm run build && npm run typecheck

FROM node:24-alpine AS runtime
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=builder --chown=node:node /app/web/.next/standalone ./
COPY --from=builder --chown=node:node /app/web/.next/static ./web/.next/static
COPY --from=builder --chown=node:node /app/web/public ./web/public
USER node
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=4s --start-period=20s --retries=3 CMD node -e "fetch('http://127.0.0.1:3000/login').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"
CMD ["node", "web/server.js"]
