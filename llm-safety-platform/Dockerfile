FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt psycopg[binary]>=3.1

COPY app ./app
COPY configs ./configs
COPY console ./console
COPY migrations ./migrations
COPY workers ./workers

ENV SAFETY_SCANNER_MODE=shim
ENV SAFETY_OIDC_DISABLED=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
# Gateway default; moderation worker overrides command in compose
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
