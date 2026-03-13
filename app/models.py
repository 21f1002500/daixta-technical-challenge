from pydantic import BaseModel, Field


class Transaction(BaseModel):
    id: str
    date: str  # ISO 8601
    amount: float  # positive for credits, negative for debits
    description: str = ""
    type: str = Field(..., pattern="^(credit|debit)$")


class AnalyzeRequest(BaseModel):
    transactions: list[Transaction] = Field(..., min_length=1)


class FinancialSummary(BaseModel):
    total_inflow: float
    total_outflow: float
    net_cash_flow: float
    inflow_count: int
    outflow_count: int
    largest_inflow: float
    largest_outflow: float
    average_transaction_value: float


class RiskFlag(BaseModel):
    flag: str
    detail: str


class AnalyzeResponse(BaseModel):
    summary: FinancialSummary
    risk_flags: list[RiskFlag]
    readiness: str
