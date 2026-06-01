# PLC Data Visualization Pipeline

**Phase:** 1 (Local MVP)  
**Goal:** Collect PLC data on local PC, store in PostgreSQL/TimescaleDB, display in searchable React table UI

## Architecture
- **Edge Collector:** Raspberry Pi running Python async OPC UA client
- **Backend:** FastAPI + PostgreSQL + TimescaleDB (local)
- **Frontend:** React 18 + TanStack Table
- **Protocols:** Modbus TCP

## Project Inputs
- **PLC Protocol:** Modbus TCP
- **Tag Count:** 50–100 tags
- **Sampling Rate:** 1 Hz average
- **Retention:** 90 days local, 1 year cloud (Phase 3)
- **Backend Location:** Local PC

## Quick Start (Docker-only backend)

Use Docker Compose to start the stack and run backend scripts from inside the backend container. Do not run backend scripts from the local Windows venv.

Start the services:

docker compose up -d --build

docker compose ps

docker compose logs -f backend

Run demo data seeding inside the backend container:

docker compose exec backend python scripts/seed_dev_data.py

If you need to run another backend script, run it inside the backend container, for example:

docker compose exec backend python seed_sync.py

docker compose exec backend python scripts/seed_sync.py
