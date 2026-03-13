from app.models import FinancialSummary, Transaction


def compute_summary(transactions: list[Transaction]) -> FinancialSummary:
    inflows = []
    outflows = []

    for t in transactions:
        if t.type == "credit":
            inflows.append(abs(t.amount))
        else:
            outflows.append(abs(t.amount))

    total_in = sum(inflows)
    total_out = sum(outflows)

    return FinancialSummary(
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        net_cash_flow=round(total_in - total_out, 2),
        inflow_count=len(inflows),
        outflow_count=len(outflows),
        largest_inflow=round(max(inflows), 2) if inflows else 0.0,
        largest_outflow=round(max(outflows), 2) if outflows else 0.0,
        average_transaction_value=round(
            (total_in + total_out) / len(transactions), 2
        ),
    )
