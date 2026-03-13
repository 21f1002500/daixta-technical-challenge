from app.models import FinancialSummary, RiskFlag


def classify_readiness(summary: FinancialSummary, risk_flags: list[RiskFlag]) -> str:
    """
    Start at 100 points and deduct:
      -30 for negative cash flow
      -15 per risk flag
      -10 for < 2 inflow transactions

    >= 70 = strong, >= 40 = structured, below that = requires_clarification
    """
    score = 100

    if summary.net_cash_flow < 0:
        score -= 30

    score -= len(risk_flags) * 15

    if summary.inflow_count < 2:
        score -= 10

    if score >= 70:
        return "strong"
    elif score >= 40:
        return "structured"
    else:
        return "requires_clarification"
