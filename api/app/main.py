import logging
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse

from . import db, rules
from .kb import get_kb
from .llm import llm_enabled, triage_with_llm
from .schemas import InboundMessage, TriageResult

log = logging.getLogger("inboxpilot")
app = FastAPI(title="InboxPilot API", version="1.0.0")
STATIC = Path(__file__).parent / "static"


@app.get("/health")
def health():
    return {"status": "ok", "llm_enabled": llm_enabled(), "kb_chunks": len(get_kb().chunks)}


@app.post("/triage", response_model=TriageResult)
def triage(msg: InboundMessage):
    hits = get_kb().search(f"{msg.subject or ''} {msg.message}")
    provider, result = "rules", None

    if llm_enabled():
        try:
            result, provider = triage_with_llm(msg.message, msg.subject, hits), "llm"
        except Exception as exc:  # network error, bad JSON, invalid values...
            log.warning("LLM failed, using rules fallback: %s", exc)

    if result is None:
        result = rules.classify(msg.message, msg.subject)
        result["suggested_reply"] = rules.draft_reply(msg.sender, result["category"], hits)

    sources = [h["source"] for h in hits]
    ticket_id = db.insert_ticket({
        "source": msg.source, "sender": msg.sender, "subject": msg.subject,
        "message": msg.message, "category": result["category"],
        "priority": result["priority"], "sentiment": result["sentiment"],
        "summary": result["summary"], "suggested_reply": result["suggested_reply"],
        "kb_sources": ",".join(sources), "provider": provider,
    })
    return TriageResult(
        id=ticket_id, kb_sources=sources, provider=provider,
        needs_alert=result["priority"] in ("high", "urgent"),
        category=result["category"], priority=result["priority"],
        sentiment=result["sentiment"], summary=result["summary"],
        suggested_reply=result["suggested_reply"],
    )


@app.get("/tickets")
def tickets(limit: int = Query(50, le=200), priority: "str | None" = None):
    return db.list_tickets(limit, priority)


@app.get("/stats")
def stats():
    return db.stats()


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC / "index.html")
