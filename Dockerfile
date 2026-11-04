FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:${PATH}"
COPY --from=builder /install /usr/local
WORKDIR /app
RUN mkdir -p /app/data && chown -R 65534:65534 /app
USER 65534:65534
EXPOSE 8001
HEALTHCHECK --interval=20s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=2)"
CMD ["uvicorn", "ghostnet.admin_api.main:create_admin_app", "--factory", "--host", "0.0.0.0", "--port", "8001"]
