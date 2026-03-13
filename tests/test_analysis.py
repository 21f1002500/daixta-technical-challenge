from app.analysis import compute_summary
from app.models import Transaction, FinancialSummary
from app.risk_flags import detect_risk_flags
from app.readiness import classify_readiness, RiskFlag


def make_txn(id, amount, type, desc=""):
    return Transaction(id=id, date="2025-01-15", amount=amount, type=type, description=desc)


# --- summary calculations ---

def test_summary_basic():
    txns = [
        make_txn("1", 5000, "credit"),
        make_txn("2", 3000, "credit"),
        make_txn("3", -1200, "debit"),
        make_txn("4", -800, "debit"),
    ]
    s = compute_summary(txns)

    assert s.total_inflow == 8000.0
    assert s.total_outflow == 2000.0
    assert s.net_cash_flow == 6000.0
    assert s.inflow_count == 2
    assert s.outflow_count == 2
    assert s.largest_inflow == 5000.0
    assert s.largest_outflow == 1200.0
    assert s.average_transaction_value == 2500.0


def test_all_credits():
    s = compute_summary([make_txn("1", 1000, "credit"), make_txn("2", 2000, "credit")])
    assert s.total_outflow == 0.0
    assert s.largest_outflow == 0.0
    assert s.net_cash_flow == 3000.0


def test_all_debits():
    s = compute_summary([make_txn("1", -500, "debit"), make_txn("2", -300, "debit")])
    assert s.total_inflow == 0.0
    assert s.net_cash_flow == -800.0


def test_rounding():
    txns = [
        make_txn("1", 100.333, "credit"),
        make_txn("2", 100.336, "credit"),
        make_txn("3", -50.111, "debit"),
    ]
    s = compute_summary(txns)
    assert s.total_inflow == 200.67
    assert s.total_outflow == 50.11


# --- risk flags ---

def test_nsf_detected():
    txns = [make_txn("1", -50, "debit", "NSF fee")]
    summary = compute_summary([make_txn("x", 5000, "credit"), make_txn("y", 3000, "credit")] + txns)
    flags = detect_risk_flags([make_txn("x", 5000, "credit")] + txns, summary)
    names = [f.flag for f in flags]
    assert "nsf_activity_detected" in names


def test_nsf_not_triggered_on_normal_desc():
    txns = [make_txn("1", 5000, "credit"), make_txn("2", 3000, "credit"), make_txn("3", -50, "debit", "Coffee")]
    flags = detect_risk_flags(txns, compute_summary(txns))
    names = [f.flag for f in flags]
    assert "nsf_activity_detected" not in names


def test_large_outflow_flag():
    txns = [make_txn("1", 2000, "credit"), make_txn("2", 1500, "credit"), make_txn("3", -2500, "debit")]
    flags = detect_risk_flags(txns, compute_summary(txns))
    names = [f.flag for f in flags]
    assert "large_single_outflow" in names


def test_negative_cashflow_flag():
    txns = [make_txn("1", 500, "credit"), make_txn("2", 500, "credit"), make_txn("3", -2000, "debit")]
    flags = detect_risk_flags(txns, compute_summary(txns))
    names = [f.flag for f in flags]
    assert "negative_net_cash_flow" in names


# --- readiness ---

def test_strong_readiness():
    summary = FinancialSummary(
        total_inflow=10000, total_outflow=3000, net_cash_flow=7000,
        inflow_count=5, outflow_count=3, largest_inflow=4000,
        largest_outflow=1500, average_transaction_value=1625,
    )
    assert classify_readiness(summary, []) == "strong"


def test_structured_readiness():
    summary = FinancialSummary(
        total_inflow=5000, total_outflow=6000, net_cash_flow=-1000,
        inflow_count=3, outflow_count=4, largest_inflow=2000,
        largest_outflow=2000, average_transaction_value=1571,
    )
    # negative cf (-30) + 1 flag (-15) = 55 -> structured
    assert classify_readiness(summary, [RiskFlag(flag="x", detail="x")]) == "structured"


def test_requires_clarification():
    summary = FinancialSummary(
        total_inflow=500, total_outflow=3000, net_cash_flow=-2500,
        inflow_count=1, outflow_count=4, largest_inflow=500,
        largest_outflow=2000, average_transaction_value=700,
    )
    flags = [RiskFlag(flag="a", detail="a"), RiskFlag(flag="b", detail="b"), RiskFlag(flag="c", detail="c")]
    # 100 - 30 - 45 - 10 = 15 -> requires_clarification
    assert classify_readiness(summary, flags) == "requires_clarification"
