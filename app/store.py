"""DB-backed store — wraps SQLAlchemy models with helper functions.

All functions must be called within a Flask app context.
Seed data is inserted once on first run via seed_if_empty().
"""
import uuid
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------

def get_policies():
    from models import Policy
    return [p.to_dict() for p in Policy.query.order_by(Policy.created_at.desc()).all()]


def add_policy(id, agent, token, budget, purpose, tx_hash):
    from models import db, Policy
    p = Policy(id=id, agent=agent, token=token, budget=budget, purpose=purpose, tx_hash=tx_hash)
    db.session.add(p)
    db.session.commit()
    logger.info("Policy added: %s", id)
    return p.to_dict()


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def get_transactions(limit=None):
    from models import Transaction
    q = Transaction.query.order_by(Transaction.created_at.desc())
    if limit:
        q = q.limit(limit)
    return [t.to_dict() for t in q.all()]


def new_tx(recipient, policy, amount, status):
    from models import db, Transaction
    tx = Transaction(
        id=f"TX-{uuid.uuid4().hex[:8].upper()}",
        recipient=recipient,
        policy=policy,
        amount=amount,
        status=status,
        hash=f"0x{uuid.uuid4().hex}{uuid.uuid4().hex}",
    )
    db.session.add(tx)
    db.session.commit()
    logger.info("Transaction added: %s", tx.id)
    return tx.to_dict()


# ---------------------------------------------------------------------------
# Activity
# ---------------------------------------------------------------------------

def get_activity(limit=None):
    from models import ActivityLog
    q = ActivityLog.query.order_by(ActivityLog.created_at.desc())
    if limit:
        q = q.limit(limit)
    return [a.to_dict() for a in q.all()]


def add_activity(action, text):
    from models import db, ActivityLog
    entry = ActivityLog(
        action=action,
        text=text,
        time=datetime.utcnow().strftime("%H:%M:%S UTC"),
    )
    db.session.add(entry)
    db.session.commit()


# ---------------------------------------------------------------------------
# Payment Intents
# ---------------------------------------------------------------------------

def save_intent(task: str, result: dict):
    from models import db, PaymentIntent
    record = PaymentIntent(
        task=task,
        recipient=result.get("recipient"),
        amount=result.get("amount"),
        purpose=result.get("purpose"),
        mode=result.get("mode", "live"),
        error=result.get("error"),
    )
    db.session.add(record)
    db.session.commit()
    return record.to_dict()


# ---------------------------------------------------------------------------
# Wallet
# ---------------------------------------------------------------------------

def get_wallet():
    from models import db, WalletState
    w = db.session.get(WalletState, 1)
    if w is None:
        return {"connected": False, "address": None}
    return {"connected": w.connected, "address": w.address}


def set_wallet(connected, address):
    from models import db, WalletState
    w = db.session.get(WalletState, 1)
    if w is None:
        w = WalletState(id=1, connected=connected, address=address)
        db.session.add(w)
    else:
        w.connected = connected
        w.address = address
    db.session.commit()


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_if_empty():
    from models import db, Policy, Transaction, ActivityLog
    if Policy.query.count() > 0:
        return

    logger.info("Seeding initial demo data...")

    for p in [
        Policy(id="POL-101", agent="0xAgent001", token="USDC", budget=10000,
               purpose="SaaS vendor payments", tx_hash="0xdemo0001"),
        Policy(id="POL-102", agent="0xAgent002", token="ETH", budget=25000,
               purpose="Infrastructure payments", tx_hash="0xdemo0002"),
        Policy(id="POL-103", agent="0xAgent003", token="DAI", budget=5000,
               purpose="Contractor disbursements", tx_hash="0xdemo0003"),
    ]:
        db.session.add(p)

    now = datetime.utcnow()
    for t in [
        Transaction(id="TX-A1B2C3", recipient="AWS", policy="POL-102", amount=4200,
                    status="Completed", hash="0x4a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b",
                    created_at=now - timedelta(days=6)),
        Transaction(id="TX-D4E5F6", recipient="Stripe", policy="POL-101", amount=1800,
                    status="Completed", hash="0x7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a",
                    created_at=now - timedelta(days=5)),
        Transaction(id="TX-G7H8I9", recipient="GitHub", policy="POL-101", amount=420,
                    status="Completed", hash="0x2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f",
                    created_at=now - timedelta(days=4)),
        Transaction(id="TX-J1K2L3", recipient="Contractor A", policy="POL-103", amount=3500,
                    status="Pending", hash="0x9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e",
                    created_at=now - timedelta(days=3)),
        Transaction(id="TX-M4N5O6", recipient="Datadog", policy="POL-102", amount=890,
                    status="Completed", hash="0x5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d",
                    created_at=now - timedelta(days=2)),
        Transaction(id="TX-P7Q8R9", recipient="Twilio", policy="POL-101", amount=210,
                    status="Declined", hash="0x1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c",
                    created_at=now - timedelta(days=2)),
        Transaction(id="TX-S1T2U3", recipient="Vercel", policy="POL-102", amount=650,
                    status="Completed", hash="0x6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a",
                    created_at=now - timedelta(days=1)),
        Transaction(id="TX-V4W5X6", recipient="Contractor B", policy="POL-103", amount=1200,
                    status="Completed", hash="0x3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
                    created_at=now),
    ]:
        db.session.add(t)

    for a in [
        ActivityLog(action="Policy Created", text="POL-103 created for agent 0xAgent003",
                    time="09:12:04 UTC"),
        ActivityLog(action="Payment Executed", text="TX-V4W5X6 sent $1200 to Contractor B",
                    time="09:08:31 UTC"),
        ActivityLog(action="Policy Created", text="POL-102 created for agent 0xAgent002",
                    time="08:55:10 UTC"),
        ActivityLog(action="Payment Rejected", text="TX-P7Q8R9 declined — limit exceeded",
                    time="08:40:22 UTC"),
        ActivityLog(action="Wallet Connected", text="Wallet 0xA91F73C2 connected",
                    time="08:30:00 UTC"),
        ActivityLog(action="Policy Created", text="POL-101 created for agent 0xAgent001",
                    time="08:25:44 UTC"),
        ActivityLog(action="Payment Executed", text="TX-A1B2C3 sent $4200 to AWS",
                    time="08:20:15 UTC"),
    ]:
        db.session.add(a)

    db.session.commit()
    logger.info("Seed data inserted.")
