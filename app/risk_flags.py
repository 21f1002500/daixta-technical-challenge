from app.models import FinancialSummary, RiskFlag, Transaction

# stuff that shows up in descriptions when payments bounce
NSF_KEYWORDS = ["nsf", "insufficient funds", "returned", "bounced"]


def detect_risk_flags(transactions: list[Transaction], summary: FinancialSummary) -> list[RiskFlag]:
    flags = []

    # check for NSF / bounced payment language
    for txn in transactions:
        desc = txn.description.lower()
        if any(kw in desc for kw in NSF_KEYWORDS):
            flags.append(RiskFlag(
                flag="nsf_activity_detected",
                detail=f"Transaction '{txn.id}' looks NSF-related ('{txn.description}')",
            ))
            break  # one is enough

    # single outflow > 50% of total inflow
    if summary.total_inflow > 0:
        for txn in transactions:
            if txn.type == "debit" and abs(txn.amount) > summary.total_inflow * 0.5:
                flags.append(RiskFlag(
                    flag="large_single_outflow",
                    detail=f"Outflow of {abs(txn.amount):.2f} on '{txn.id}' exceeds 50% of total inflow ({summary.total_inflow:.2f})",
                ))
                break

    # spending more than earning
    if summary.net_cash_flow < 0:
        flags.append(RiskFlag(
            flag="negative_net_cash_flow",
            detail=f"Net cash flow is {summary.net_cash_flow:.2f}",
        ))

    # one big expense dominates
    if summary.total_outflow > 0:
        ratio = summary.largest_outflow / summary.total_outflow
        if ratio > 0.40:
            flags.append(RiskFlag(
                flag="high_expense_concentration",
                detail=f"Largest outflow ({summary.largest_outflow:.2f}) is {ratio * 100:.1f}% of all outflows",
            ))

    # too few income sources to be confident
    if summary.inflow_count < 2:
        flags.append(RiskFlag(
            flag="low_inflow_frequency",
            detail=f"Only {summary.inflow_count} inflow transaction(s), need at least 2",
        ))

    return flags
