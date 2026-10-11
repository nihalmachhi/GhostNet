FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY ghostnet ./ghostnet
COPY rules ./rules
RUN pip install --no-cache-dir . && mkdir -p /app/data && chown -R 65534:65534 /app/data
ENV PYTHONDONTWRITEBYTECODE=1
