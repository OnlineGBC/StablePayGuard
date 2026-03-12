# Codex PayRails Agent Architecture

## Overview

Codex PayRails Agent is a Flask-based control dashboard for AI-managed payment operations. The current implementation is a single-service web application with a dynamic frontend and lightweight API layer.

## Current Architecture

```text
Browser UI
  ├─ HTML / CSS / JavaScript
  └─ Fetch API calls
          │
          ▼
Flask Application
  ├─ Routes
  ├─ Policy creation logic
  ├─ Wallet connection simulation
  ├─ Dashboard aggregation
  └─ Chart data endpoints
          │
          ▼
In-Memory Data Store
  ├─ POLICIES
  ├─ TRANSACTIONS
  ├─ ACTIVITY
  └─ WALLET
```

## Core Components

### 1. Frontend
Responsibilities:
- render dashboard
- call backend endpoints
- update KPI counters
- draw charts
- display transaction rows
- show wallet state

### 2. Flask Backend
Responsibilities:
- expose JSON APIs
- create policies
- aggregate dashboard metrics
- simulate wallet connectivity
- maintain activity log

### 3. Data Model
Current in-memory objects:
- policies
- transactions
- activity events
- wallet state

## Proposed Future Architecture

```text
Client Browser
      │
      ▼
NGINX / API Gateway
      │
      ▼
Flask API Service
      ├─ Auth module
      ├─ Policy engine
      ├─ Analytics module
      └─ Payment orchestration
              │
              ├─ PostgreSQL
              ├─ Redis cache
              ├─ Blockchain RPC
              └─ Banking / payment APIs
```

## Design Goals

- professional operator experience
- clear transaction visibility
- policy-driven controls
- easy transition from demo to production
- future AI-agent orchestration support

## Security Considerations

- store secrets outside code
- validate all request payloads
- add authentication before multi-user deployment
- add rate limiting and audit logs
- require signed wallet interactions for real payment rails

## Suggested Next Technical Steps

1. Replace in-memory storage with SQLite or PostgreSQL
2. Split Flask routes into modular blueprints
3. Add authentication
4. Add real wallet integration
5. Add background jobs for analytics and polling
