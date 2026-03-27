# StablePayGuard Architecture

## Overview

StablePayGuard is a Flask-based control platform for AI-managed payment operations. It consists of a Python backend, a PostgreSQL database (SQLite in local dev), a single-page dashboard UI, and a Solidity smart contract deployed to Ethereum Sepolia testnet.

---

## Current Architecture

```
Browser (HTML / CSS / JS)
        │
        │  REST API (JSON)
        ▼
┌─────────────────────────────────────────┐
│           Flask Backend                 │
│                                         │
│  secrets.py ──► GCP Secret Manager     │
│                 (.env locally)          │
│                                         │
│  5 Route Blueprints                     │
│    auth       → login / logout          │
│    policies   → CRUD + deactivation     │
│    payments   → intent / execute / list │
│    uniswap    → token prices            │
│    wallet     → connect                 │
│                                         │
│  4 Service Modules                      │
│    agent_service    → AI parsing        │
│    policy_service   → on-chain ops      │
│    uniswap_service  → price feeds       │
│    web3_service     → contract i/face   │
│                                         │
│  Cross-cutting                          │
│    schemas.py    → Pydantic validation  │
│    utils.py      → auth decorator       │
│    extensions.py → rate limiting        │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
PostgreSQL          Ethereum Sepolia
(Cloud SQL /        PolicyManager.sol
 SQLite locally)    via Infura RPC
                         │
                    Uniswap v3
                    Subgraph
                    (price feeds)
```

---

## Component Details

### Flask Application (`app/app.py`)

Entry point. Responsibilities:
- Call `load_secrets()` to populate `os.environ` from GCP Secret Manager (Cloud Run) or `.env` (local)
- Configure SQLAlchemy with `DATABASE_URL` (falls back to SQLite if not set)
- Register 5 blueprints
- Run `db.create_all()` and seed demo data on first run
- Serve dashboard page (`GET /`)
- Expose dashboard API, chart API, and contract status API

### Secret Loader (`app/secrets.py`)

Detects environment via `K_SERVICE` env var (set automatically by Cloud Run):
- **Cloud Run:** fetches secrets from GCP Secret Manager for any not already injected via `--update-secrets`
- **Local:** calls `python-dotenv` `load_dotenv()` to read `.env` file

### Database Layer

**Models** (`app/models.py`):
| Table | Key Columns | Notes |
|---|---|---|
| `policies` | id (PK), agent, token, budget, purpose, tx_hash | indexed on created_at |
| `transactions` | id (PK), recipient, policy (FK→policies), amount, status, hash | indexed on policy, created_at; status CHECK constraint |
| `activity_logs` | id, action, text, time | indexed on created_at |
| `payment_intents` | id, task, recipient, amount, purpose, mode, error | indexed on created_at |
| `wallet_state` | id (singleton=1), connected, address | — |

Foreign key enforcement: SQLite uses a `PRAGMA foreign_keys=ON` event listener; PostgreSQL enforces automatically.

**Store** (`app/store.py`): thin wrapper functions over SQLAlchemy queries. All functions require a Flask app context.

### Route Blueprints

| Blueprint | Prefix | Auth required |
|---|---|---|
| `auth_bp` | `/api/auth/` | No (login endpoint is open; others manage session) |
| `policies_bp` | `/api/policies` | POST and deactivate require login |
| `payments_bp` | `/api/payment*`, `/api/transactions` | POST endpoints require login |
| `uniswap_bp` | `/api/token/` | No |
| `wallet_bp` | `/api/wallet/` | Yes |

Rate limits (Flask-Limiter):
- Default: 100/day, 10/minute
- Login: 5/minute, 20/hour
- Payment intent: 10/minute
- Payment execution: 20/minute

### Service Modules

**agent_service.py** — AI payment intent parsing
1. Try Anthropic (`SYNTH_API_KEY`) → claude-haiku-4-5
2. Fallback to OpenAI (`OPENAI_API_KEY`) → gpt-4o-mini
3. Fallback to demo mode (random realistic amount)

Validates parsed JSON has `recipient`, `amount` (numeric), and `purpose` fields before returning.

**policy_service.py** — On-chain policy management
- `create_policy()`: calls `contract.functions.createPolicy()` if Web3 connected; returns demo hash otherwise
- `deactivate_policy()`: calls `contract.functions.deactivatePolicy()` if connected; demo otherwise
- `get_policy_on_chain()`: reads live state from contract; falls back to DB record

**uniswap_service.py** — Token price feeds
- Queries Uniswap v3 Subgraph (The Graph) via GraphQL
- Stablecoins (USDC, DAI, USDT) hardcoded to $1.00
- ETH and WBTC calculated from pool `derivedETH` × `ethPriceUSD`
- 60-second in-memory TTL cache per symbol

**web3_service.py** — Web3 and contract interface
- Initialises `Web3.HTTPProvider(RPC_URL)` on startup
- Loads `PolicyManager.json` ABI from `contracts/abi/`
- `approve_payment()`: builds, signs, and sends `approvePayment` transaction

### Smart Contract (`contracts/src/PolicyManager.sol`)

Solidity 0.8.28, deployed to Sepolia at `0x16229C14aAa18C7bC069f5b9092f5Af8884f3781`.

Key functions:
| Function | Access | Description |
|---|---|---|
| `createPolicy(...)` | owner only | Register a new spending policy |
| `approvePayment(id, amount)` | policy agent | Validate and record a payment; reverts if rules violated |
| `deactivatePolicy(id)` | owner only | Immediately disable a policy |
| `getPolicy(id)` | anyone | Read full policy state |
| `remainingBudget(id)` | anyone | `totalBudget - spentAmount` |

Audit: Slither v0.11.5 — 0 high, 0 medium issues.

---

## Data Flow: Payment Execution

```
POST /api/payment
  {policy_id, recipient, amount, purpose}
        │
        ▼
  Pydantic validation (PaymentExecuteRequest)
        │
        ▼
  DB: policy exists?  ──No──► 404
        │ Yes
        ▼
  DB: remaining budget >= amount?  ──No──► 422 + activity log
        │ Yes
        ▼
  web3_service.approve_payment()
    ├── Connected: on-chain tx, returns real hash
    └── Not connected: skip (demo hash from store)
        │
        ▼
  store.new_tx() → persist transaction
        │
        ▼
  store.add_activity() → activity log
        │
        ▼
  201 {tx_id, hash, mode: "live"|"demo"}
```

---

## Data Flow: Secret Loading

```
App starts (app.py)
        │
        ▼
  load_secrets()
        │
        ├── K_SERVICE set? (Cloud Run)
        │     │ Yes
        │     └── GCP Secret Manager
        │           fetch each secret not already in os.environ
        │           (--update-secrets may have already injected some)
        │
        └── K_SERVICE not set? (local)
              └── load_dotenv() → reads .env file
        │
        ▼
  os.environ populated
  app initialization continues
```

---

## Deployment Architecture (Cloud Run)

```
Developer machine
        │  git push / gcloud run deploy --source .
        ▼
Cloud Build
        │  builds Docker image (Dockerfile)
        ▼
Artifact Registry
        │  stores image
        ▼
Cloud Run (us-east1)
  Service: stablepayguard
  Image:   python:3.10-slim + gunicorn
  Secrets: mounted from Secret Manager
  DB:      Cloud SQL PostgreSQL (via DATABASE_URL env var)
  Port:    8080
```

Gunicorn command (from Dockerfile):
```
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 60 --chdir /app/app app:app
```

---

## CI/CD

**tests.yml** — triggers on push to `app/**`, `tests/**`, `requirements.txt`:
1. Spin up PostgreSQL 16 service container
2. Install Python 3.11 + dependencies
3. Run `pytest tests/ -v --cov=app`

**audit.yml** — triggers on changes to `contracts/src/`:
1. Run Slither static analysis (`--fail-medium`)
2. Run Mythril symbolic execution

---

## Security Controls

| Control | Implementation |
|---|---|
| Authentication | Session-based; `login_required` decorator on all write endpoints |
| Rate limiting | Flask-Limiter; login capped at 5/min to block brute force |
| Input validation | Pydantic schemas on all POST request bodies |
| Secrets management | GCP Secret Manager on Cloud Run; `.env` local only (gitignored) |
| DB integrity | FK constraints, CHECK constraint on status, indexes on query columns |
| Contract access | `onlyOwner` modifier on create/deactivate; agent address validated on approvePayment |
| HTTPS | Enforced by Cloud Run (terminates TLS at load balancer) |
