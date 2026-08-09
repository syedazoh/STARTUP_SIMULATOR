FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc ca-certificates && rm -rf /var/lib/apt/lists/*
# Optional extra trust root for dev machines behind TLS-inspecting antivirus/proxies
# (e.g. Avast, Zscaler). Empty by default and harmless; fill locally, never commit real content.
COPY docker-ca/extra-ca.crt* /usr/local/share/ca-certificates/
RUN find /usr/local/share/ca-certificates -name '*.example' -delete && update-ca-certificates
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]