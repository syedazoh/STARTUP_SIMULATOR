FROM node:18-alpine
WORKDIR /app
# Optional extra trust root for dev machines behind TLS-inspecting antivirus/proxies
# (e.g. Avast, Zscaler). Empty by default and harmless; fill locally, never commit real content.
COPY docker-ca/extra-ca.crt* /usr/local/share/ca-certificates/
RUN cd /usr/local/share/ca-certificates && \
    [ -f extra-ca.crt ] || cp extra-ca.crt.example extra-ca.crt && \
    rm -f extra-ca.crt.example && \
    if [ -s extra-ca.crt ]; then \
        sed -i 's/https:/http:/' /etc/apk/repositories && \
        apk add --no-cache ca-certificates && \
        sed -i 's/http:/https:/' /etc/apk/repositories && \
        update-ca-certificates; \
    fi
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/extra-ca.crt
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]