# PLC Data Visualization Pipeline

**Phase:** 1 (Local MVP)  
**Goal:** Collect PLC data on local PC, store in PostgreSQL/TimescaleDB, display in searchable React table UI

## Architecture
- **Edge Collector:** Raspberry Pi running Python async OPC UA client
- **Backend:** FastAPI + PostgreSQL + TimescaleDB (local)
- **Frontend:** React 18 + TanStack Table
- **Protocols:** OPC UA (primary), fallback to Modbus TCP

## Project Inputs
- **PLC Protocol:** OPC UA (or Modbus TCP)
- **Tag Count:** 50–100 tags
- **Sampling Rate:** 1 Hz average
- **Retention:** 90 days local, 1 year cloud (Phase 3)
- **Backend Location:** Local PC

## Quick Start (will be completed during implementation)
