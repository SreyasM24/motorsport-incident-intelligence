# Development and Production Setup Guide

This guide details the procedure for deploying and developing the Motorsport Incident Intelligence (MII) platform across local, native, and containerized environments.

---

## 1. Prerequisites

Ensure your host system meets the following minimum requirements:

| Tool | Minimum Version | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11 | 3.12 / 3.13 | Required for backend services |
| **Node.js** | 20.0 | 22.0 LTS | Required for frontend builds |
| **npm** | 10.0 | Latest | Package manager for frontend |
| **PostgreSQL** | 16.0 | 16 Alpine | Relational database engine |
| **Docker Engine** | 24.0+ | Latest | Required for containerized runtime |
| **Docker Compose** | 2.20+ | Latest | Multi-service orchestration |

---

## 2. Quick Start: Docker Compose

Docker Compose is the recommended path for running the entire system in an isolated, production-like setup.

### Step 1: Clone and Configure
```bash
git clone https://github.com/SreyasM24/motorsport-incident-intelligence.git
cd motorsport-incident-intelligence

# Copy environment template
cp .env.example .env
```

### Step 2: Build and Run
```bash
docker compose up --build -d
```

### Step 3: Validate Containers
```bash
docker compose ps
```

All three services (`mii_postgres`, `mii_backend`, `mii_frontend`) should show state `Up (healthy)`.

---

## 3. Local Native Setup (Development)

### Backend Setup

```bash
cd backend

# 1. Create a dedicated virtual environment
python -m venv .venv

# 2. Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Set environment variables
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/motorsport_intelligence"
export FASTF1_CACHE_DIR="data/cache/fastf1"

# 5. Apply database schema migrations
alembic upgrade head

# 6. Seed initial test and reference data
python -m app.seeds.seed_all

# 7. Start the FastAPI development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend documentation will be accessible at `http://localhost:8000/docs`.

### Frontend Setup

```bash
# Return to repository root
cd ..

# 1. Install frontend dependencies
npm install

# 2. Verify TypeScript types and linting
npm run lint

# 3. Start Vite development server
npm run dev
```

Frontend application will be accessible at `http://localhost:5173`.

---

## 4. Configuration Parameters (.env)

The application is configured via environment variables. See [`.env.example`](../.env.example) for defaults:

```ini
# Application Mode
APP_NAME="Motorsport Incident Intelligence API"
APP_VERSION="1.0.0"
ENVIRONMENT="production" # 'development' | 'production'
DEBUG=false
API_V1_PREFIX="/api/v1"
LOG_LEVEL="INFO"

# Database Connection (PostgreSQL 16 with psycopg3)
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/motorsport_intelligence"

# Performance & Caching
DOSSIER_CACHE_TTL_SECONDS=3600
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_EXPENSIVE_PER_MINUTE=30

# Ingestion Parameters
TELEMETRY_ANALYSIS_HZ=25
TELEMETRY_MAX_INTERPOLATION_GAP_MS=1000
FASTF1_CACHE_DIR="data/cache/fastf1"
OPENF1_BASE_URL="https://api.openf1.org/v1"

# CORS Allowed Origins
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://localhost:80,http://localhost"
```

---

## 5. Verification Checklist

After installation, verify that the services operate correctly:

```bash
# 1. API Health Check
curl -s http://localhost:8000/health | jq .
# Expected output: {"status":"healthy","database":"connected",...}

# 2. Run Backend Test Suite
cd backend
python -m pytest -v

# 3. Test Frontend Production Build
cd ..
npm run build
```
