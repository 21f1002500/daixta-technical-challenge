# Financial Analysis Service

A small FastAPI service that takes a list of financial transactions and spits out a summary with risk flags and a readiness classification. Built for the daixta take-home challenge.

## Getting started

### Docker

```bash
docker compose up --build
```

That's it — the API is at `http://localhost:8000`.

### Run locally

You'll need Python 3.11+.

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Usage

### `POST /analyze-file`

```bash
curl -X POST http://localhost:8000/analyze-file \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      {"id": "t1", "date": "2025-01-01", "amount": 5000,   "description": "Salary",    "type": "credit"},
      {"id": "t2", "date": "2025-01-03", "amount": 3000,   "description": "Freelance", "type": "credit"},
      {"id": "t3", "date": "2025-01-05", "amount": -1200,  "description": "Rent",      "type": "debit"},
      {"id": "t4", "date": "2025-01-07", "amount": -150,   "description": "Utilities", "type": "debit"},
      {"id": "t5", "date": "2025-01-10", "amount": -75.50, "description": "Groceries", "type": "debit"}
    ]
  }'
```

Response:

```json
{
  "summary": {
    "total_inflow": 8000.0,
    "total_outflow": 1425.5,
    "net_cash_flow": 6574.5,
    "inflow_count": 2,
    "outflow_count": 3,
    "largest_inflow": 5000.0,
    "largest_outflow": 1200.0,
    "average_transaction_value": 1885.1
  },
  "risk_flags": [],
  "readiness": "strong"
}
```

### `GET /health`

Just returns `{"status": "healthy"}` — useful for health checks on k8s or whatever you're running.

### Interactive docs

FastAPI gives you Swagger for free:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Tests

```bash
pytest tests/ -v
```

## Project layout

```
app/
├── main.py          # FastAPI app + endpoints
├── models.py        # Pydantic schemas
├── analysis.py      # Number crunching
├── risk_flags.py    # Risk flag rules
└── readiness.py     # Readiness scoring
tests/
├── test_analysis.py # Unit tests for logic
└── test_api.py      # Integration tests for the endpoint
```

## Assumptions

- **Transaction direction** comes from the `type` field (`credit` = money in, `debit` = money out). I take `abs()` of the amount internally, so it doesn't matter if debits come in as negative — they're handled either way.
- **Single currency.** No currency conversion happening here. Everything's assumed to be in the same currency.
- **Dates are stored but not used yet.** They're in the schema for when you want to do time-series stuff, but the current analysis treats the whole batch as one snapshot.
- **Payload fits in memory.** Fine for a take-home. In prod you'd want streaming or pagination for large datasets.

## Risk flags

I went with five straightforward rules. Each one either fires or it doesn't — no severity levels, just boolean flags with an explanation.

| Flag | What triggers it |
|------|-----------------|
| `nsf_activity_detected` | Description contains "NSF", "insufficient funds", "returned", or "bounced" |
| `large_single_outflow` | A single debit > 50% of total inflow |
| `negative_net_cash_flow` | You're spending more than you're earning |
| `high_expense_concentration` | Biggest debit is > 40% of total outflow |
| `low_inflow_frequency` | Fewer than 2 credit transactions — not enough data |
n 
These are simple keyword/threshold checks. A productiosystem would probably use something smarter (anomaly detection, categorisation, etc.) but for the scope of this exercise they get the job done.

## Readiness classification

I used a points-based system. You start at 100 and lose points for bad signals:

| Signal | Penalty |
|--------|---------|
| Negative net cash flow | -30 |
| Each risk flag | -15 |
| Less than 2 inflows | -10 |

Then I map the score to a band:

| Score | Band | What it means |
|-------|------|---------------|
| >= 70 | `strong` | Looks good for lending |
| 40-69 | `structured` | Some yellow flags, but workable |
| < 40 | `requires_clarification` | Too many issues, needs a human to look at it |

I went with this approach because it's transparent — you can trace exactly why someone got a particular band. The thresholds are somewhat arbitrary (they'd need tuning with real data), but the structure is sound and easy to extend.

## If I had four more hours

1. **Time-series analysis.** Right now I'm treating all transactions as one flat batch. With more time I'd parse dates and compute things like monthly burn rate, income regularity, and trend direction. Those tell you way more about lending readiness than a single snapshot.

2. **Transaction categorisation.** I'd tag transactions as rent, groceries, subscriptions, payroll, etc. using keyword matching as a first pass. This makes the "high expense concentration" flag much more meaningful — "80% of spending is rent" is a different story than "80% of spending is gambling."

3. **Persistent storage.** Throw in Postgres and let people compare their financials over time. "Your net cash flow improved 12% since last month" is a lot more useful than a one-shot analysis.

4. **Config-driven risk rules.** The 50%, 40% thresholds are hardcoded right now. I'd move them to a config file so ops can tune them without deploying code. Maybe even a simple admin UI.

5. **Observability.** Structured logging, OpenTelemetry traces, basic Prometheus metrics. You need this stuff before anything touches real money.

6. **Auth & rate limiting.** At minimum API key auth and per-client rate limits. Not glamorous but necessary.
