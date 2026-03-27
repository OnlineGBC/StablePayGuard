# StablePayGuard — Complete User and Technical Manual

---

## Table of Contents

1. [What Is StablePayGuard?](#1-what-is-stablepayguard)
2. [Who Benefits and How](#2-who-benefits-and-how)
3. [Where the Code Lives](#3-where-the-code-lives)
4. [Prerequisites](#4-prerequisites)
5. [Running Locally](#5-running-locally)
6. [Accessing the Live App](#6-accessing-the-live-app)
7. [Usage Guide](#7-usage-guide)
   - 7.1 [Logging In](#71-logging-in)
   - 7.2 [Dashboard](#72-dashboard)
   - 7.3 [Creating a Policy](#73-creating-a-policy)
   - 7.4 [Submitting a Payment Intent](#74-submitting-a-payment-intent)
   - 7.5 [Connecting a Wallet](#75-connecting-a-wallet)
   - 7.6 [Viewing Policies](#76-viewing-policies)
8. [Demo Mode vs. Live Blockchain Mode](#8-demo-mode-vs-live-blockchain-mode)
9. [Environment Variables](#9-environment-variables)
10. [Changing the Admin Password](#10-changing-the-admin-password)
11. [Connecting a Real AI Key](#11-connecting-a-real-ai-key)
12. [Infrastructure on Google Cloud](#12-infrastructure-on-google-cloud)
13. [Redeploying the App](#13-redeploying-the-app)
14. [Viewing Logs](#14-viewing-logs)
15. [Codebase Overview](#15-codebase-overview)
    - 15.1 [Directory Structure](#151-directory-structure)
    - 15.2 [Backend Components](#152-backend-components)
    - 15.3 [Frontend](#153-frontend)
    - 15.4 [Smart Contract](#154-smart-contract)
    - 15.5 [Tests](#155-tests)
    - 15.6 [CI/CD](#156-cicd)
16. [Going Live on the Blockchain](#16-going-live-on-the-blockchain)
17. [Security](#17-security)
18. [Troubleshooting](#18-troubleshooting)
19. [Known Limitations](#19-known-limitations)

---

## 1. What Is StablePayGuard?

StablePayGuard is a web-based control panel for managing and enforcing AI-driven payment rules. In plain terms:

> Imagine you have an AI assistant that is allowed to make payments on your behalf — paying cloud hosting bills, vendor invoices, software subscriptions. Without controls in place, the AI could overspend, pay the wrong recipient, or act outside its authorised scope. StablePayGuard solves this by letting you define strict spending rules ("policies") that every payment must pass before it goes through.

A **policy** answers questions like:
- Which AI agent is allowed to spend?
- In which token (e.g. USDC, ETH, DAI)?
- What is the total budget for this agent?
- What is the maximum it can spend in a single transaction?
- What is the stated purpose (e.g. "cloud infrastructure", "vendor payments")?

When a payment is attempted, it is checked against the matching policy. If it exceeds any limit, it is rejected automatically.

StablePayGuard also includes an **AI payment intent parser**: you type a natural-language instruction such as *"Pay AWS $200 for cloud hosting"* and the system converts it into a structured payment record — recipient, amount, token, purpose — ready for policy enforcement.

---

## 2. Who Benefits and How

### Businesses operating AI agents
Any organisation that uses AI to automate payments, procurement, or financial operations benefits from having a policy layer. StablePayGuard gives finance and ops teams visibility and control without needing to understand the underlying AI code.

| Participant | Role | Benefit |
|---|---|---|
| **Finance / Ops Manager** | Sets spending policies | Ensures AI agents never exceed budget or act outside authorised scope |
| **AI Agent** | Submits payment intents | Gets a clear decision (approved / rejected) with a reason, enabling automated retry or escalation |
| **Developer / Admin** | Deploys and maintains the system | Has a structured API, persistent database, and audit trail rather than ad-hoc scripts |
| **Auditor / Compliance** | Reviews transaction history | Full log of every payment attempt, approval, and rejection with timestamps |
| **Blockchain / DeFi operator** | Uses on-chain enforcement | Policies are optionally enforced on the Ethereum blockchain (Sepolia testnet), making them tamper-proof |

---

## 3. Where the Code Lives

### Local machine
The source code lives at:
```
C:\Users\raja\CodexPayRailsAgent\
```
This is a Git repository. All code changes are committed and pushed from here.

### GitHub
The repository is hosted at:
```
https://github.com/OnlineGBC/CryptoPayRailsAgent
```
This is the source of truth for all deployments. Cloud builds pull from a local push via `gcloud run deploy --source .` (which uploads sources directly to Google Cloud Build — it does not pull from GitHub automatically).

### Google Cloud — Project: `stablepayguard`

| Component | Location |
|---|---|
| **Cloud Run service** | `us-east1` region, service name `stablepayguard` |
| **Container image** | Artifact Registry: `us-east1-docker.pkg.dev/stablepayguard/cloud-run-source-deploy/stablepayguard` |
| **Cloud SQL database** | Instance `stablepayguard-db`, Postgres 15, region `us-east1` |
| **Database name** | `stablepayguard` |
| **Live URL** | `https://stablepayguard-684704256193.us-east1.run.app` |

---

## 4. Prerequisites

### To run locally
| Requirement | Purpose |
|---|---|
| Python 3.10+ | Runs the Flask application |
| PostgreSQL 15+ (or Docker) | Required database — SQLite is not supported |
| `pip` | Installs Python dependencies |
| Git | Clones the repository |

### To deploy to Google Cloud
| Requirement | Purpose |
|---|---|
| Google Cloud SDK (`gcloud`) | Deploys to Cloud Run, manages Cloud SQL |
| A GCP account with billing enabled | Cloud Run and Cloud SQL incur costs |
| Docker (optional) | Only needed to build/test the container locally |

### Optional (for full functionality)
| Requirement | Purpose |
|---|---|
| Anthropic API key (`SYNTH_API_KEY`) | Powers the AI payment intent parser |
| OpenAI API key (`OPENAI_API_KEY`) | Fallback AI provider |
| Infura / Alchemy RPC URL | Connects to Ethereum blockchain |
| Ethereum private key | Signs on-chain policy transactions |

---

## 5. Running Locally

### Option A — Docker Compose (recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/OnlineGBC/CryptoPayRailsAgent
   cd CryptoPayRailsAgent
   ```

2. Copy the example environment file and fill in your values:
   ```bash
   cp .env.example .env
   ```

3. Start the database and web service:
   ```bash
   docker-compose up
   ```

4. Open `http://localhost:5000` in your browser.

Docker Compose starts a Postgres 15 container (`stablepayguard-db`) and the Flask web container (`stablepayguard`). Data persists in a Docker volume (`postgres_data`) across restarts.

---

### Option B — Manual (no Docker)

1. Start a local PostgreSQL instance and create the database and user:
   ```sql
   CREATE USER stablepayguard WITH PASSWORD 'stablepayguard';
   CREATE DATABASE stablepayguard OWNER stablepayguard;
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root (see [Section 9](#9-environment-variables) for all variables):
   ```
   DATABASE_URL=postgresql://stablepayguard:stablepayguard@localhost:5432/stablepayguard
   SECRET_KEY=any-random-string
   ADMIN_PASSWORD=demo
   ```

4. Run the app:
   ```bash
   cd app
   python app.py
   ```

5. Open `http://localhost:5000`.

---

## 6. Accessing the Live App

The live deployment is at:

```
https://stablepayguard-684704256193.us-east1.run.app
```

**Login credentials:**
- Username: *(none — single user system)*
- Password: `demo`

To change the password, see [Section 10](#10-changing-the-admin-password).

---

## 7. Usage Guide

### 7.1 Logging In

[SCREENSHOT: Login screen showing the StablePayGuard logo and password field]

When you open the app, a login overlay appears. Enter the admin password (`demo` by default) and click **Sign In**. The overlay disappears and the dashboard loads.

If the password is wrong, a red error message appears below the input field.

---

### 7.2 Dashboard

[SCREENSHOT: Dashboard with KPI cards, activity feed, and transaction table]

The dashboard is the home screen. It shows:

| Section | What it shows |
|---|---|
| **KPI cards** | Total policies, total payments, total payment volume (USD), approval rate (%) |
| **Payment Chart** | Bar chart of payment volume by day of the week |
| **Recent Transactions** | Last 10 transactions with status badges (Completed / Pending / Declined) |
| **Activity Feed** | Last 10 system events (policy created, payment executed, wallet connected) |
| **Wallet status** | Whether a wallet is connected and its address |

All data refreshes when the page loads. To see updated numbers after an action, navigate away and back, or refresh the page.

---

### 7.3 Creating a Policy

[SCREENSHOT: Policy creation form with fields filled in]

1. Click **Policies** in the left sidebar.
2. Fill in the **Create New Policy** form:

| Field | Description | Example |
|---|---|---|
| **Agent Address** | Ethereum address of the AI agent being authorised | `0xAgentABC123` |
| **Token** | Token the agent is allowed to spend | `USDC` |
| **Total Budget** | Maximum lifetime spend for this policy | `5000` |
| **Per-Tx Limit** | Maximum spend per single transaction | `500` |
| **Valid From** | Unix timestamp when the policy starts (0 = now) | `0` |
| **Valid Until** | Unix timestamp when the policy expires (0 = no expiry) | `0` |
| **Purpose** | Human-readable description of what payments are for | `vendor payments` |

3. Click **Create Policy**.
4. A success message shows the Policy ID and transaction hash.
5. The Dashboard KPI counter for Policies increments by 1.

**Validation rules:**
- Agent address cannot be empty
- Total budget must be greater than 0
- Purpose cannot be empty
- Per-tx limit cannot exceed total budget

If any rule is violated, a `400 Bad Request` response is returned with a field-level error message.

---

### 7.4 Submitting a Payment Intent

[SCREENSHOT: Payment intent form with a natural-language task entered]

1. Click **Payments** in the sidebar.
2. In the **Payment Intent** panel, type a natural-language task:
   - *"Pay AWS $200 for cloud hosting"*
   - *"Send $50 USDC to Stripe for subscription fees"*
   - *"Transfer 100 DAI to vendor 0xABC for consulting"*
3. Click **Generate Intent**.
4. The AI parses the text and returns a structured result:

```json
{
  "recipient": "AWS",
  "amount": 200,
  "token": "USDC",
  "purpose": "cloud hosting"
}
```

5. The intent is stored in the database and appears in the transaction feed on the Dashboard.

**Note:** In demo mode (no AI API key configured), a pre-built demo response is returned. See [Section 11](#11-connecting-a-real-ai-key) to enable live AI parsing.

---

### 7.5 Connecting a Wallet

[SCREENSHOT: Wallet connect panel]

1. Click the **Connect Wallet** button in the top bar, or navigate to the **Wallet** section.
2. Optionally enter a valid Ethereum address (e.g. `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`). If left blank, a demo address is used.
3. Click **Connect**.
4. The top bar updates to show the connected address.
5. The Dashboard wallet panel shows `connected: true`.

**Validation:** The address must be a valid Ethereum address (42 characters, starting with `0x`, valid hex). Invalid addresses return a `400` error.

---

### 7.6 Viewing Policies

1. Click **Policies** in the sidebar.
2. The policy list shows all created policies with:
   - Policy ID
   - Agent address
   - Token
   - Total budget
   - Remaining budget (total minus all completed transactions against this policy)
   - Spent amount
   - Purpose

Remaining budget is calculated live from the transaction database each time the dashboard loads.

---

## 8. Demo Mode vs. Live Blockchain Mode

StablePayGuard runs in one of two modes:

### Demo Mode (default)
- No Ethereum RPC connection required
- Policy creation returns a fake transaction hash prefixed with `demo-`
- Payment enforcement is simulated in the database only
- The `/api/contract/status` endpoint returns `"mode": "demo"`
- All data persists to PostgreSQL — policies, transactions, and activity logs all work normally

### Live Blockchain Mode
- Requires `RPC_URL`, `PRIVATE_KEY`, and `POLICY_CONTRACT` environment variables
- Policy creation submits a real transaction to the Ethereum blockchain (Sepolia testnet)
- The smart contract enforces per-transaction limits on-chain
- Transaction hash is a real Ethereum tx hash viewable on Etherscan
- The `/api/contract/status` endpoint returns `"mode": "live"`

To switch from demo to live, see [Section 16](#16-going-live-on-the-blockchain).

---

## 9. Environment Variables

All configuration is done via environment variables. For local development, put these in a `.env` file in the project root.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | — | PostgreSQL connection string. Format: `postgresql://user:password@host:port/dbname` |
| `SECRET_KEY` | **Yes** | — | Flask session secret. Use a long random string in production |
| `ADMIN_PASSWORD` | **Yes** | — | Password for the single admin login |
| `SYNTH_API_KEY` | No | — | Anthropic API key (primary AI provider for payment intent parsing) |
| `OPENAI_API_KEY` | No | — | OpenAI API key (fallback AI provider) |
| `RPC_URL` | No | — | Ethereum RPC endpoint (e.g. Infura Sepolia URL). Required for live blockchain mode |
| `PRIVATE_KEY` | No | — | Ethereum wallet private key for signing on-chain transactions |
| `POLICY_CONTRACT` | No | — | Deployed PolicyManager contract address |
| `OWNER_WALLET` | No | — | Ethereum address of the contract owner |
| `SEED_DATA` | No | `false` | Set to `true` to seed demo transactions and policies on first startup |
| `PORT` | No | `5000` | Port the app listens on (Cloud Run sets this automatically to `8080`) |
| `FLASK_ENV` | No | `production` | Set to `development` for debug mode locally |

---

## 10. Changing the Admin Password

### On Cloud Run
```bash
gcloud run services update stablepayguard \
  --region us-east1 \
  --project stablepayguard \
  --update-env-vars "ADMIN_PASSWORD=yournewpassword"
```

This triggers a new revision. The URL stays the same.

### Locally
Update `ADMIN_PASSWORD` in your `.env` file and restart the app.

---

## 11. Connecting a Real AI Key

Without an AI key, the payment intent parser returns a canned demo response. To enable live AI parsing:

### Using Anthropic (recommended)
1. Obtain an API key from [console.anthropic.com](https://console.anthropic.com)
2. Set the environment variable:
   ```bash
   gcloud run services update stablepayguard \
     --region us-east1 \
     --project stablepayguard \
     --update-env-vars "SYNTH_API_KEY=sk-ant-your-key-here"
   ```
3. The app uses `claude-haiku-4-5-20251001` for fast, cost-effective parsing.

### Using OpenAI (fallback)
```bash
gcloud run services update stablepayguard \
  --region us-east1 \
  --project stablepayguard \
  --update-env-vars "OPENAI_API_KEY=sk-your-openai-key"
```

The fallback chain is: `SYNTH_API_KEY` → `OPENAI_API_KEY` → demo response.

---

## 12. Infrastructure on Google Cloud

### GCP Project
- **Project ID:** `stablepayguard`
- **Project Name:** StablePayGuard
- **Billing account:** Same as `fednowrtppayrails` (`01D45F-38C7C5-24A487`)
- **Region:** `us-east1`

### Cloud Run
- **Service name:** `stablepayguard`
- **URL:** `https://stablepayguard-684704256193.us-east1.run.app`
- **Concurrency:** 8 threads per instance, 1 worker
- **Authentication:** Public (unauthenticated requests allowed — app-level auth via session)
- **Cloud SQL connection:** Unix socket via `stablepayguard:us-east1:stablepayguard-db`

### Cloud SQL
- **Instance name:** `stablepayguard-db`
- **Database version:** PostgreSQL 15
- **Tier:** `db-f1-micro` (1 shared vCPU, 614 MB RAM — suitable for development/demo)
- **Region:** `us-east1-b`
- **Database:** `stablepayguard`
- **User:** `stablepayguard`
- **Connection name:** `stablepayguard:us-east1:stablepayguard-db`

### Artifact Registry
- **Repository:** `cloud-run-source-deploy`
- **Image path:** `us-east1-docker.pkg.dev/stablepayguard/cloud-run-source-deploy/stablepayguard`

### APIs Enabled
- Cloud Run API
- Cloud SQL Admin API
- Cloud Build API
- Artifact Registry API
- Secret Manager API

---

## 13. Redeploying the App

After making code changes locally:

```bash
gcloud run deploy stablepayguard \
  --source . \
  --region us-east1 \
  --project stablepayguard \
  --quiet
```

This triggers Cloud Build to rebuild the Docker image and deploy a new revision. Existing environment variables are preserved unless you pass `--set-env-vars` or `--update-env-vars`.

**To update env vars without changing code:**
```bash
gcloud run services update stablepayguard \
  --region us-east1 \
  --project stablepayguard \
  --update-env-vars "KEY=value"
```

**To roll back to a previous revision:**
```bash
gcloud run services update-traffic stablepayguard \
  --region us-east1 \
  --project stablepayguard \
  --to-revisions REVISION_NAME=100
```

List available revisions:
```bash
gcloud run revisions list --service stablepayguard \
  --region us-east1 \
  --project stablepayguard
```

---

## 14. Viewing Logs

### Real-time logs (Cloud Run)
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=stablepayguard" \
  --project stablepayguard \
  --limit 50 \
  --format="value(timestamp,textPayload)"
```

### Errors only
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=stablepayguard AND severity>=ERROR" \
  --project stablepayguard \
  --limit 20
```

### From the Console
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Select project `stablepayguard`
3. Navigate to **Cloud Run** → **stablepayguard** → **Logs** tab

---

## 15. Codebase Overview

### 15.1 Directory Structure

```
CryptoPayRailsAgent/
├── app/                        # All application code
│   ├── app.py                  # Flask app entry point, dashboard API, blueprint registration
│   ├── models.py               # SQLAlchemy database models
│   ├── store.py                # Database access layer (CRUD functions)
│   ├── schemas.py              # Pydantic request validation schemas
│   ├── extensions.py           # Flask-Limiter rate limiter instance
│   ├── utils.py                # login_required decorator, validate_request helper
│   ├── routes/
│   │   ├── auth.py             # POST /api/auth/login, logout, status
│   │   ├── policies.py         # GET/POST /api/policies
│   │   ├── payments.py         # POST /api/payment-intent
│   │   ├── uniswap.py          # GET /api/token/price, POST /api/token/quote
│   │   └── wallet.py           # POST /api/wallet/connect
│   ├── services/
│   │   ├── agent_service.py    # AI payment intent parsing (Anthropic → OpenAI → demo)
│   │   ├── policy_service.py   # Policy creation, on-chain reads
│   │   └── web3_service.py     # Web3 connection, contract loading, approve_payment()
│   └── templates/
│       └── dashboard.html      # Single-page frontend (HTML + CSS + JS)
├── contracts/
│   ├── src/
│   │   └── PolicyManager.sol   # Solidity smart contract
│   └── abi/
│       └── PolicyManager.json  # Contract ABI (loaded by web3_service.py)
├── tests/
│   ├── test_api.py             # 33 integration tests (Flask test client + PostgreSQL)
│   ├── test_validation.py      # 21 Pydantic schema unit tests
│   ├── test_policy_service.py  # 6 unit tests (mocked Web3)
│   └── test_agent_service.py   # 6 unit tests (mocked Anthropic/OpenAI)
├── .github/
│   └── workflows/
│       ├── tests.yml           # pytest CI (runs on push/PR, spins up Postgres service)
│       └── audit.yml           # Slither + Mythril smart contract security audit CI
├── Dockerfile                  # Container definition (Python 3.10-slim, gunicorn)
├── docker-compose.yml          # Local dev: Postgres + web service
├── requirements.txt            # Python dependencies
├── .env.example                # Template for environment variables
├── README.md                   # Project overview
├── ARCHITECTURE.md             # Architecture notes
└── MANUAL.md                   # This document
```

---

### 15.2 Backend Components

#### `app.py` — Entry point
- Initialises Flask, SQLAlchemy, Flask-Limiter
- Registers all route blueprints
- Creates database tables on startup (`db.create_all()`)
- Seeds demo data if `SEED_DATA=true`
- Serves the dashboard page and the following APIs:
  - `GET /api/dashboard` — aggregated KPIs, transactions, activity, wallet, policies with remaining budgets
  - `GET /api/charts/payments` — 7-day payment chart data
  - `GET /api/contract/status` — Web3 connection status

#### `models.py` — Database models

| Model | Table | Key Fields |
|---|---|---|
| `Policy` | `policy` | `id`, `agent`, `token`, `total_budget`, `per_tx_limit`, `purpose`, `created_at` |
| `Transaction` | `transaction` | `id`, `tx_id`, `amount`, `status`, `policy_id`, `created_at` |
| `ActivityLog` | `activity_log` | `id`, `action`, `text`, `time` |
| `PaymentIntent` | `payment_intent` | `id`, `task`, `result_json`, `created_at` |
| `WalletState` | `wallet_state` | `id`, `connected`, `address`, `network`, `balance` |

#### `store.py` — Data access layer
Wraps all database operations in simple functions called by routes:
- `get_policies()`, `add_policy()` — policy CRUD
- `get_transactions()`, `new_tx()` — transaction CRUD
- `get_activity()`, `add_activity()` — activity log
- `get_wallet()`, `set_wallet()` — wallet state
- `save_intent()` — persist a payment intent
- `seed_if_empty()` — populate demo data on first run

#### `schemas.py` — Request validation (Pydantic v2)

| Schema | Used by | Validates |
|---|---|---|
| `PolicyCreate` | `POST /api/policies` | agent, token, totalBudget (>0), perTxLimit, purpose (non-empty) |
| `PaymentIntentRequest` | `POST /api/payment-intent` | task (non-empty string) |
| `SwapQuoteRequest` | `POST /api/token/quote` | tokenIn, tokenOut (known symbols), amountUSD (>0) |
| `WalletConnectRequest` | `POST /api/wallet/connect` | address (valid Ethereum address or empty) |

#### `services/agent_service.py` — AI intent parser
Fallback chain:
1. If `SYNTH_API_KEY` set → calls Anthropic (`claude-haiku-4-5-20251001`) with a structured prompt
2. Else if `OPENAI_API_KEY` set → calls OpenAI (`gpt-3.5-turbo`)
3. Else → returns a hardcoded demo response

Returns a dict: `{"recipient": ..., "amount": ..., "token": ..., "purpose": ...}`

#### `services/policy_service.py` — Policy management
- `create_policy()` — generates a unique 8-char uppercase hex policy ID, attempts on-chain tx if Web3 available, falls back to demo hash
- `get_policy_on_chain()` — reads policy state from the smart contract (or returns DB record in demo mode)

#### `services/web3_service.py` — Blockchain connection
- Initialises Web3 provider from `RPC_URL`
- Loads the `PolicyManager` contract from `contracts/abi/PolicyManager.json`
- `approve_payment(policy_id, amount)` — calls `approvePayment()` on the contract

#### `extensions.py` — Rate limiting
- Default limits: `100 requests/day`, `10 requests/minute` per IP
- Payment intent endpoint: `10 requests/minute`
- Tests are exempted via `@limiter.request_filter` when `TESTING=True`

#### `utils.py` — Shared utilities
- `@login_required` — decorator that returns `401` if `session["authenticated"]` is not `True`
- `validate_request(schema, data)` — runs Pydantic validation, returns `(parsed_obj, None)` on success or `(None, (error_dict, 400))` on failure

---

### 15.3 Frontend

The entire UI is a single file: `app/templates/dashboard.html`.

**Key design decisions:**
- No JavaScript framework — plain JS with `fetch()`
- All DOM manipulation uses `createElement` and `textContent` (never `innerHTML`) to prevent XSS
- Login overlay rendered on page load; removed after successful `/api/auth/login` call
- Single-page navigation: sidebar links toggle CSS `display` on sections, no page reloads
- Error toasts appear bottom-right for API failures
- Loading spinners on buttons during async calls

**Sections rendered client-side:**
- `dashboard` — KPI cards, chart, transactions table, activity feed
- `policies` — policy creation form + policy list table
- `payments` — payment intent input form
- `agents` — placeholder section
- `settings` — placeholder section

---

### 15.4 Smart Contract

File: `contracts/src/PolicyManager.sol`

The `PolicyManager` Solidity contract enforces payment policies on the Ethereum blockchain.

**Key functions:**

| Function | Visibility | Description |
|---|---|---|
| `createPolicy(agent, token, totalBudget, perTxLimit, validFrom, validUntil, purpose)` | `onlyOwner` | Registers a new policy on-chain |
| `approvePayment(policyId, amount)` | `onlyOwner` | Checks amount against policy limits; reverts if exceeded |
| `getPolicy(policyId)` | `view` | Returns policy details and remaining budget |

The contract uses `mapping(bytes32 => Policy)` keyed by a hashed policy ID. All amounts are in token units (uint256). The `onlyOwner` modifier ensures only the deploying wallet can create policies or approve payments.

The ABI is at `contracts/abi/PolicyManager.json` and is loaded by `web3_service.py` at startup.

---

### 15.5 Tests

Run the full test suite (requires a local PostgreSQL instance with `stablepayguard_test` database):

```bash
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

| File | Tests | What they cover |
|---|---|---|
| `test_api.py` | 33 | All HTTP endpoints, auth, validation, persistence, remaining budget |
| `test_validation.py` | 21 | Pydantic schemas — valid inputs, invalid inputs, edge cases |
| `test_policy_service.py` | 6 | `create_policy()` in demo mode and with mocked Web3 failure |
| `test_agent_service.py` | 6 | `generate_payment_intent()` with mocked Anthropic and OpenAI |

**Setting up the test database locally:**
```bash
psql -U postgres -c "CREATE USER stablepayguard WITH PASSWORD 'stablepayguard';"
psql -U postgres -c "CREATE DATABASE stablepayguard_test OWNER stablepayguard;"
```

---

### 15.6 CI/CD

#### `.github/workflows/tests.yml`
Runs on every push or pull request touching `app/`, `tests/`, or `requirements.txt`:
1. Spins up a Postgres 16 service container
2. Installs Python 3.11 and dependencies
3. Runs `pytest tests/ -v --cov=app`

#### `.github/workflows/audit.yml`
Runs Slither and Mythril static analysis on the smart contract:
- **Slither** — checks for common Solidity vulnerabilities (reentrancy, integer overflow, etc.)
- **Mythril** — symbolic execution to find deeper security issues

---

## 16. Going Live on the Blockchain

To switch from demo mode to live on-chain enforcement on the Ethereum Sepolia testnet:

### Step 1 — Get an RPC endpoint
Sign up at [infura.io](https://infura.io) or [alchemy.com](https://alchemy.com). Create a Sepolia project and copy the RPC URL:
```
https://sepolia.infura.io/v3/YOUR_PROJECT_ID
```

### Step 2 — Prepare a wallet
You need an Ethereum wallet with Sepolia ETH (free from a Sepolia faucet). Export the private key. **Never use a wallet holding real funds.**

### Step 3 — Deploy the smart contract
```bash
cd contracts
# Install Foundry or Hardhat, then:
forge create src/PolicyManager.sol:PolicyManager \
  --rpc-url $RPC_URL \
  --private-key $PRIVATE_KEY
```
Note the deployed contract address.

### Step 4 — Update Cloud Run environment variables
```bash
gcloud run services update stablepayguard \
  --region us-east1 \
  --project stablepayguard \
  --update-env-vars "RPC_URL=https://sepolia.infura.io/v3/YOUR_ID,PRIVATE_KEY=0xyourkey,POLICY_CONTRACT=0xDeployedAddress,OWNER_WALLET=0xYourWalletAddress"
```

### Step 5 — Verify
Visit `/api/contract/status`. It should now return:
```json
{"mode": "live", "web3_connected": true, "contract_loaded": true}
```

Policy creation will now submit real Sepolia transactions, viewable at `https://sepolia.etherscan.io`.

---

## 17. Security

### What is protected
| Endpoint | Auth required |
|---|---|
| `POST /api/policies` | Yes |
| `POST /api/payment-intent` | Yes |
| `POST /api/wallet/connect` | Yes |
| `GET /api/policies` | Yes |
| `GET /api/dashboard` | No (public read) |
| `GET /api/charts/payments` | No |
| `GET /api/contract/status` | No |
| `GET /` | No |

Authentication is session-based. The session cookie is signed with `SECRET_KEY`. Sessions expire when the browser closes.

### Rate limiting
- All endpoints: 100 requests/day, 10 requests/minute per IP
- Payment intent endpoint: additionally capped at 10 requests/minute
- Rate limiting is disabled during automated tests

### Input validation
All state-modifying endpoints validate request bodies via Pydantic before processing. Invalid or missing fields return `400 Bad Request` with field-level error details.

### XSS prevention
All user-supplied data rendered in the dashboard is inserted via `textContent` (not `innerHTML`), preventing cross-site scripting.

### What should be hardened before production use
- Replace single-user password auth with a proper identity provider (OAuth, SSO)
- Store `SECRET_KEY` and `ADMIN_PASSWORD` in Google Secret Manager rather than as plain env vars
- Enable Cloud SQL private IP (VPC) instead of the Cloud SQL Auth Proxy socket
- Add HTTPS-only enforcement and security headers (HSTS, CSP)
- Implement per-user audit logging
- Rotate the `PRIVATE_KEY` to a hardware wallet or KMS-managed key before handling real funds

---

## 18. Troubleshooting

### 503 Service Unavailable on Cloud Run
The container is crashing on startup. Check the logs:
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=stablepayguard AND severity>=ERROR" \
  --project stablepayguard --limit 10
```
Common causes:
- `DATABASE_URL` not set or wrong — check env vars
- Cloud SQL instance not running — check `gcloud sql instances describe stablepayguard-db --project stablepayguard`
- Import error in Python code — check the full traceback in logs

### Login not working
- Verify `ADMIN_PASSWORD` env var is set correctly
- Check that `SECRET_KEY` is set (sessions won't persist without it)
- Try in a private/incognito window to rule out stale session cookies

### Database connection refused (local)
- Ensure PostgreSQL is running: `pg_isready -h localhost`
- Verify the `DATABASE_URL` matches your local Postgres user/password/dbname
- If using Docker Compose, ensure the `db` service is healthy before the `web` service starts

### Payment intent returns demo response
- No AI API key is configured — set `SYNTH_API_KEY` or `OPENAI_API_KEY`
- Check logs for API key errors if you have set a key

### Policy creation succeeds but mode stays "demo"
- `RPC_URL`, `PRIVATE_KEY`, and `POLICY_CONTRACT` must all be set for live mode
- Check `/api/contract/status` — it shows exactly which components are connected

### Tests failing with database connection error
- Create the test database: `createdb -U stablepayguard stablepayguard_test`
- Ensure the test `DATABASE_URL` in `tests/test_api.py` matches your local Postgres credentials

---

## 19. Known Limitations

| Limitation | Detail |
|---|---|
| **Single user only** | There is one admin account with one shared password. No user roles, no per-user policies. |
| **Demo AI in free tier** | Without an Anthropic or OpenAI key, payment intent parsing returns a static demo response. |
| **No email or webhook alerts** | There is no notification system for rejected payments or policy breaches. |
| **No audit log export** | The activity feed is viewable in the UI only. There is no CSV/PDF export. |
| **No policy editing or deletion** | Policies can be created but not modified or deactivated through the UI. |
| **db-f1-micro Cloud SQL tier** | The deployed instance uses the smallest available tier — not suitable for production load. |
| **Sepolia testnet only** | The smart contract integration targets Ethereum Sepolia. Mainnet or other chains require redeployment and ABI changes. |
| **No MetaMask / browser wallet** | Wallet connection accepts a manually typed address only. There is no WalletConnect or MetaMask integration. |
| **Single region** | The app and database are both in `us-east1`. There is no multi-region failover. |
