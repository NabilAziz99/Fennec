# Backend Dockerfile for Fennec AI
# Runs the Python agent AND hosts the pentest tools that agents invoke
# via the `terminal` tool (agents shell out inside this same container).
FROM python:3.11-slim

WORKDIR /app

# ---------------------------------------------------------------------------
# System dependencies — pentest tools + runtime essentials
# ---------------------------------------------------------------------------
# Debian bookworm has most of what we need via apt. We deliberately avoid the
# full Kali base (too big, too slow to pull) and install only what agents
# actually call today. Go-based tools (ffuf/nuclei/naabu/katana) can be added
# later if benchmarks show recon needs them.
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        # Core runtime
        curl \
        wget \
        git \
        jq \
        ca-certificates \
        # Network
        nmap \
        netcat-openbsd \
        dnsutils \
        whois \
        # Web recon / exploitation
        nikto \
        gobuster \
        dirb \
        sqlmap \
        whatweb \
        wfuzz \
        # Password / hash tooling
        hydra \
        john \
        # Wordlists
        seclists \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Python dependencies
# ---------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Extra pentest helpers available via pip (easier than apt on bookworm):
#   dirsearch – Python directory brute-forcer (used as ffuf/gobuster fallback)
#   wafw00f   – WAF fingerprinter
#   arjun     – HTTP parameter discovery
RUN pip install --no-cache-dir dirsearch wafw00f arjun

# ---------------------------------------------------------------------------
# Application code
# ---------------------------------------------------------------------------
COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
