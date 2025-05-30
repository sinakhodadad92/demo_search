# ----------------------------------------------------------------------------
# ssoar-search-backend/backend/Dockerfile
# ----------------------------------------------------------------------------
FROM python:3.12-slim

# 1) install system dependencies including curl for healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# 2) Copy & install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) Copy the Django project and management script
COPY . .

# 4) Ensure our entrypoint is executable
RUN chmod +x ./entrypoint.sh

# 5) Run entrypoint (waits for ES, migrations, bulk‐index, then gunicorn)
ENTRYPOINT ["./entrypoint.sh"]