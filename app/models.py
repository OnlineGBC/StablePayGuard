from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


# Enable FK enforcement for SQLite (PostgreSQL enforces them automatically)
@event.listens_for(Engine, "connect")
def _set_sqlite_fk_pragma(dbapi_connection, _):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Policy(db.Model):
    __tablename__ = "policies"
    id = db.Column(db.String(20), primary_key=True)
    agent = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(20), nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.String(500), nullable=False)
    tx_hash = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "agent": self.agent,
            "token": self.token,
            "budget": self.budget,
            "purpose": self.purpose,
            "tx_hash": self.tx_hash,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('Completed', 'Pending', 'Declined')",
            name="ck_tx_status",
        ),
    )
    id = db.Column(db.String(20), primary_key=True)
    recipient = db.Column(db.String(100), nullable=False)
    policy = db.Column(
        db.String(20),
        db.ForeignKey("policies.id", ondelete="SET NULL"),
        index=True,
    )
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    hash = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "recipient": self.recipient,
            "policy": self.policy,
            "amount": self.amount,
            "status": self.status,
            "hash": self.hash,
        }


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    time = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "action": self.action,
            "text": self.text,
            "time": self.time,
        }


class PaymentIntent(db.Model):
    __tablename__ = "payment_intents"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task = db.Column(db.String(500), nullable=False)
    recipient = db.Column(db.String(100))
    amount = db.Column(db.Float)
    purpose = db.Column(db.String(500))
    mode = db.Column(db.String(20), default="live")
    error = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "task": self.task,
            "recipient": self.recipient,
            "amount": self.amount,
            "purpose": self.purpose,
            "mode": self.mode,
            "error": self.error,
        }


class WalletState(db.Model):
    __tablename__ = "wallet_state"
    id = db.Column(db.Integer, primary_key=True)
    connected = db.Column(db.Boolean, default=False)
    address = db.Column(db.String(100))
