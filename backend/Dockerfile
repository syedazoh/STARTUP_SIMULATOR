FROM python:3.11-slim
WORKDIR /app
RUN --mount=type=secret,id=build_ca,mode=0444 \
    sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources && \
    task_apt_ca=""; if [ -r /run/secrets/build_ca ]; then task_apt_ca="-o Acquire::https::CaInfo=/run/secrets/build_ca"; fi; \
    apt-get $task_apt_ca update && apt-get $task_apt_ca install -y gcc ca-certificates && rm -rf /var/lib/apt/lists/*
# Optional extra trust root for dev machines behind TLS-inspecting antivirus/proxies
# (e.g. Avast, Zscaler). Empty by default and harmless; fill locally, never commit real content.
COPY docker-ca/extra-ca.crt* /usr/local/share/ca-certificates/
RUN find /usr/local/share/ca-certificates -name '*.example' -delete && update-ca-certificates
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt
COPY requirements.txt .
# sentence-transformers pulls in torch; the default PyPI Linux wheel bundles CUDA
# runtime deps (~2GB+), which can time out on slow links. Install the much smaller
# CPU-only build first so the requirements.txt install below reuses it.
RUN --mount=type=secret,id=build_ca,mode=0444 \
    if [ -r /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca REQUESTS_CA_BUNDLE=/run/secrets/build_ca SSL_CERT_FILE=/run/secrets/build_ca; fi; \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN --mount=type=secret,id=build_ca,mode=0444 \
    if [ -r /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca REQUESTS_CA_BUNDLE=/run/secrets/build_ca SSL_CERT_FILE=/run/secrets/build_ca; fi; \
    pip install --no-cache-dir -r requirements.txt
ARG PRELOAD_MODELS=1
RUN if [ "$PRELOAD_MODELS" = "1" ]; then python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"; fi
COPY . .
RUN if [ "$PRELOAD_MODELS" = "1" ]; then PYTHONPATH=. python scripts/warm_knowledge_models.py; fi
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]