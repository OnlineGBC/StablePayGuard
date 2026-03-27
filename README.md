# StablePayGuard

![Python](https://img.shields.io/badge/python-3.10-blue)
![Flask](https://img.shields.io/badge/flask-3.x-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Slither](https://img.shields.io/badge/slither-0%20high%2F0%20medium-brightgreen)
![Solidity](https://img.shields.io/badge/solidity-0.8.28-blue)

**Intelligent Spend Management for the AI-Driven Enterprise**

StablePayGuard replaces manual Accounts Payable workflows with AI agents that execute payments automatically within policy guardrails enforced on-chain. Finance teams set the rules once; agents handle the rest.

---

## Live App

**URL:** https://stablepayguard-684704256193.us-east1.run.app
**Login:** password stored in Google Secret Manager (`ADMIN_PASSWORD`)

---

## Prerequisites

| Requirement | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| Git | Clone repo |
| `.env` file | Secrets for local dev (see below) |
| PostgreSQL *(optional)* | Production-grade DB; SQLite used automatically if not set |
| Docker Desktop *(optional)* | Easiest way to run PostgreSQL locally |
| gcloud CLI *(optional)* | Cloud Run deployment only |

---

## Local Setup — Minimal (SQLite, no Docker)

Runs immediately with no database infrastructure. SQLite is used automatically when `DATABASE_URL` is not set.

```bash
git clone https://github.com/OnlineGBC/StablePayGuard.git
cd StablePayGuard
pip install -r requirements.txt
cp .env.example .env        # fill in your API keys — comment out DATABASE_URL for SQLite mode
python app/app.py
```

Open **http://localhost:5000** and log in with your `ADMIN_PASSWORD`.

---

## Local Setup — Full Stack (PostgreSQL via Docker)

```bash
git clone https://github.com/OnlineGBC/StablePayGuard.git
cd StablePayGuard
cp .env.example .env        # fill in your API keys
docker compose up           # starts PostgreSQL + Flask app together on port 5000
```

To run only the database container and the app natively:

```bash
docker compose up db -d     # PostgreSQL in background
python app/app.py           # Flask against it
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values. On Cloud Run, all secrets are stored in Google Secret Manager — not in `.env`.

| Variable | Required locally | Description |
|---|---|---|
| `DATABASE_URL` | No | PostgreSQL connection string. Omit or comment out for SQLite. |
| `SECRET_KEY` | Yes (prod) | Flask session signing key — any long random string. |
| `ADMIN_PASSWORD` | Yes | Dashboard login password. |
| `SYNTH_API_KEY` | Recommended | Anthropic API key for AI payment intent parsing (primary provider). |
| `OPENAI_API_KEY` | Optional | OpenAI key — fallback if Anthropic unavailable. |
| `RPC_URL` | Optional | Infura/Alchemy Sepolia RPC endpoint for on-chain policy enforcement. |
| `PRIVATE_KEY` | Optional | Ethereum wallet private key for signing on-chain transactions. |
| `POLICY_CONTRACT` | Optional | Deployed `PolicyManager.sol` address on Sepolia. |
| `OWNER_WALLET` | Optional | Ethereum wallet address of the contract owner. |
| `FLASK_ENV` | Optional | Set to `development` for debug logging. |
| `PORT` | Optional | HTTP port (default `5000` locally, `8080` on Cloud Run). |

If `RPC_URL` and `POLICY_CONTRACT` are not set, the app runs in **demo mode** — all blockchain operations are simulated with placeholder hashes. The dashboard, policies, payments, and AI parsing all work identically in demo mode.

---

## Running Tests

Unit tests (no database required):

```bash
python -m pytest tests/test_validation.py tests/test_agent_service.py tests/test_policy_service.py -v
```

Full suite (requires PostgreSQL — CI spins one up automatically):

```bash
python -m pytest tests/ -v
```

---

## API Reference

### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/login` | — | Login with `{"password": "..."}` |
| POST | `/api/auth/logout` | — | Clear session |
| GET | `/api/auth/status` | — | Returns `{"authenticated": bool}` |

### Dashboard
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/dashboard` | — | KPIs, recent transactions, activity feed, wallet state, policies with remaining budgets |
| GET | `/api/charts/payments` | — | Last 7 days of completed payment volume grouped by day of week |
| GET | `/api/contract/status` | — | Web3 connection and contract load status |

### Policies
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/policies` | — | List all policies |
| POST | `/api/policies` | ✓ | Create policy: `agent`, `token`, `totalBudget`, `perTxLimit`, `purpose` |
| GET | `/api/policies/<id>` | — | Policy detail — live from contract if connected, DB otherwise |
| POST | `/api/policies/<id>/deactivate` | ✓ | Deactivate policy on-chain (or demo mode fallback) |

### Payments & Transactions
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/payment-intent` | ✓ | Parse plain-English task into structured payment JSON via AI |
| POST | `/api/payment` | ✓ | Execute payment: `policy_id`, `recipient`, `amount`, `purpose` |
| GET | `/api/transactions` | — | Transaction ledger with filters: `?status=`, `?policy=`, `?limit=`, `?offset=` |

### Tokens
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/token/price/<symbol>` | — | Live USD price — ETH, USDC, DAI, USDT, WBTC (60s cache) |
| POST | `/api/token/quote` | — | Swap quote: `tokenIn`, `tokenOut`, `amountUSD` |
| GET | `/api/token/prices` | — | All five token prices in one call |

### Wallet
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/wallet/connect` | ✓ | Connect wallet: `{"address": "0x..."}` or omit for owner wallet |

---

## Project Structure

```
StablePayGuard/
├── app/
│   ├── app.py                   # Flask entry point, dashboard + chart routes
│   ├── models.py                # SQLAlchemy ORM models (Policy, Transaction, ActivityLog, PaymentIntent, WalletState)
│   ├── schemas.py               # Pydantic request validation schemas
│   ├── store.py                 # DB helper functions and seed data
│   ├── extensions.py            # Flask-Limiter setup
│   ├── utils.py                 # login_required decorator, validate_request helper
│   ├── secrets.py               # Secret loader: GCP Secret Manager on Cloud Run, .env locally
│   ├── routes/
│   │   ├── auth.py              # Login / logout / status
│   │   ├── policies.py          # Policy CRUD + deactivation
│   │   ├── payments.py          # Payment intent parsing, execution, transaction listing
│   │   ├── uniswap.py           # Token price and swap quote
│   │   └── wallet.py            # Wallet connection
│   ├── services/
│   │   ├── agent_service.py     # AI payment intent parsing (Anthropic → OpenAI → demo)
│   │   ├── policy_service.py    # On-chain policy creation and deactivation
│   │   ├── uniswap_service.py   # Uniswap v3 Subgraph price feeds with 60s cache
│   │   └── web3_service.py      # Web3 connection and contract interface
│   └── templates/
│       └── dashboard.html       # Single-page dashboard UI
├── contracts/
│   ├── src/PolicyManager.sol    # Solidity smart contract
│   ├── abi/PolicyManager.json   # Contract ABI
│   ├── audit/slither_report.md  # Slither security audit results
│   └── deployment.json          # Deployed contract addresses
├── tests/
│   ├── test_api.py              # Integration tests (requires PostgreSQL)
│   ├── test_agent_service.py    # AI service unit tests
│   ├── test_policy_service.py   # Policy service unit tests
│   └── test_validation.py       # Schema validation unit tests
├── scripts/deploy.py            # Contract deployment script
├── .github/workflows/
│   ├── tests.yml                # CI: pytest on every push to app/ or tests/
│   └── audit.yml                # CI: Slither audit on contract changes
├── .env.example                 # Environment variable template
├── Dockerfile                   # Cloud Run container (gunicorn)
├── docker-compose.yml           # Local full-stack: app + PostgreSQL
└── requirements.txt
```

---

## Smart Contract

**PolicyManager.sol** deployed to Sepolia testnet at
`0x16229C14aAa18C7bC069f5b9092f5Af8884f3781`

Enforces spending rules on-chain: an AI agent cannot execute a payment that exceeds its policy budget, per-transaction limit, or validity window. The backend operates in demo mode when no RPC connection is configured — no contract interaction needed to use the dashboard.

Security audit: [Slither v0.11.5](contracts/audit/slither_report.md) — **0 high, 0 medium findings.**

---

## Cloud Run Deployment

Authenticate and set project:

```bash
gcloud auth login
gcloud config set project stablepayguard
```

Deploy (Cloud Build rebuilds the Docker image and deploys a new revision):

```bash
gcloud run deploy stablepayguard \
  --source . \
  --region us-east1 \
  --project stablepayguard \
  --quiet
```

Secrets are injected at runtime from Google Secret Manager via `--update-secrets`. Do not pass them as `--set-env-vars`. See [`StablePayGuard_Manual.docx`](StablePayGuard_Manual.docx) for the full infrastructure reference including Secret Manager setup, Cloud SQL, and rollback procedures.

---

## Architecture

```
Browser (HTML / CSS / JS)
        │  REST API
        ▼
Flask Backend  ──  Gunicorn (Cloud Run) / dev server (local)
  ├── 5 route blueprints (auth, policies, payments, uniswap, wallet)
  ├── 4 service modules  (agent, policy, uniswap, web3)
  ├── Pydantic validation + Flask-Limiter rate limiting
  └── secrets.py  →  GCP Secret Manager (Cloud Run) / .env (local)
        │
        ├── PostgreSQL  ──  Cloud SQL (GCP) / SQLite (local fallback)
        │
        ├── Ethereum Sepolia  ──  PolicyManager.sol
        │       via Infura RPC
        │
        └── Uniswap v3 Subgraph  ──  live token prices (60s cache)
```

---

## Roadmap

| Phase | Status | Scope |
|---|---|---|
| 1 — Core Platform | ✅ Complete | Policy engine, AI parsing, dashboard, on-chain enforcement, security audit |
| 2 — Multi-user Auth | Planned | JWT tokens, role-based access, multi-user dashboards |
| 3 — Real Payment Rails | Planned | USDC transfers, bank APIs, escrow |
| 4 — AI Agent Platform | Planned | Anomaly detection, spending predictions, agent orchestration |

---

## License

MIT License — Copyright (c) 2026 StablePayGuard
