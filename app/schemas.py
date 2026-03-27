from pydantic import BaseModel, field_validator

VALID_TOKENS = {"ETH", "USDC", "DAI", "USDT", "WBTC"}


class PolicyCreate(BaseModel):
    agent: str
    token: str = "ETH"
    totalBudget: int
    perTxLimit: int
    validFrom: int = 0
    validUntil: int = 0
    purpose: str

    @field_validator("agent")
    @classmethod
    def agent_nonempty(cls, v):
        if not v or not v.strip():
            raise ValueError("agent address is required")
        return v.strip()

    @field_validator("token")
    @classmethod
    def token_valid(cls, v):
        if v.upper() not in VALID_TOKENS and not v.startswith("0x"):
            raise ValueError(
                f"token must be one of {sorted(VALID_TOKENS)} or a contract address (0x...)"
            )
        return v

    @field_validator("totalBudget")
    @classmethod
    def budget_positive(cls, v):
        if v <= 0:
            raise ValueError("totalBudget must be positive")
        return v

    @field_validator("perTxLimit")
    @classmethod
    def per_tx_positive(cls, v):
        if v <= 0:
            raise ValueError("perTxLimit must be positive")
        return v

    @field_validator("purpose")
    @classmethod
    def purpose_nonempty(cls, v):
        if not v or not v.strip():
            raise ValueError("purpose is required")
        return v.strip()


class PaymentIntentRequest(BaseModel):
    task: str

    @field_validator("task")
    @classmethod
    def task_nonempty(cls, v):
        if not v or not v.strip():
            raise ValueError("task description is required")
        return v.strip()


class SwapQuoteRequest(BaseModel):
    tokenIn: str = "ETH"
    tokenOut: str = "USDC"
    amountUSD: float

    @field_validator("tokenIn", "tokenOut")
    @classmethod
    def token_valid(cls, v):
        if v.upper() not in VALID_TOKENS:
            raise ValueError(f"token must be one of {sorted(VALID_TOKENS)}")
        return v.upper()

    @field_validator("amountUSD")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("amountUSD must be positive")
        return v


class PaymentExecuteRequest(BaseModel):
    policy_id: str
    recipient: str
    amount: float
    purpose: str = ""

    @field_validator("policy_id")
    @classmethod
    def policy_id_nonempty(cls, v):
        if not v or not v.strip():
            raise ValueError("policy_id is required")
        return v.strip()

    @field_validator("recipient")
    @classmethod
    def recipient_nonempty(cls, v):
        if not v or not v.strip():
            raise ValueError("recipient is required")
        return v.strip()

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class WalletConnectRequest(BaseModel):
    address: str = ""

    @field_validator("address")
    @classmethod
    def address_strip(cls, v):
        return (v or "").strip()
