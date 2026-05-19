# Backend Dockerfile for Fennec AI (OSS).
#
# This image runs ONLY the Python agent + FastAPI server. All pentest
# tools (nmap, sqlmap, gobuster, nuclei, etc.) live in the sibling Kali
# container that this process spawns via the mounted Docker socket
# (EXECUTION_MODE=docker, default). The backend container itself stays
# slim: a Python runtime + a curl/git for healthcheck and any pip
# packages that need git to install.
#
# If you want a self-contained image where tools run inside this same
# container (EXECUTION_MODE=local), see linux/Dockerfile for the full
# Kali recipe — you'd want to base off that instead of python:3.11-slim.

FROM python:3.11-slim

WORKDIR /app

# Minimal runtime: curl for the healthcheck, git for any pip packages
# that pull from VCS, ca-certificates for TLS.
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl \
        git \
        ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
