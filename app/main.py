from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analysis import compute_summary
from app.models import AnalyzeRequest, AnalyzeResponse
from app.readiness import classify_readiness
from app.risk_flags import detect_risk_flags

app = FastAPI(
    title="Financial Analysis Service",
    version="1.0.0",
)

# wide open CORS for now — would lock down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze-file", response_model=AnalyzeResponse)
def analyze_file(payload: AnalyzeRequest):
    summary = compute_summary(payload.transactions)
    flags = detect_risk_flags(payload.transactions, summary)
    readiness = classify_readiness(summary, flags)

    return AnalyzeResponse(
        summary=summary,
        risk_flags=flags,
        readiness=readiness,
    )
