FROM python:3.12-slim-bookworm

# ── Install Microsoft ODBC Driver 18 for SQL Server ──────────
# The prod.list expects key at /usr/share/keyrings/microsoft-prod.gpg
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl gnupg2 apt-transport-https ca-certificates \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list \
        | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
        unixodbc \
        unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify driver registered
RUN odbcinst -q -d

# ── Python dependencies ──────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "TSS_Sync_Portal_Dashboard_v1_3.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
