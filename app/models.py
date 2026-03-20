from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Policy(db.Model):
    __tablename__ = "policies"
    id = db.Column(db.String(20), primary_key=True)
    agent = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(20), nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.String(500), nullable=False)
    tx_hash = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    id = db.Column(db.String(20), primary_key=True)
    recipient = db.Column(db.String(100), nullable=False)
    policy = db.Column(db.String(20))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    hash = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "action": self.action,
            "text": self.text,
            "time": self.time,
        }


class WalletState(db.Model):
    __tablename__ = "wallet_state"
    id = db.Column(db.Integer, primary_key=True)
    connected = db.Column(db.Boolean, default=False)
    address = db.Column(db.String(100))
