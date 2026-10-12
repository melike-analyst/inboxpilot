import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["KB_DIR"] = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base")
os.environ.pop("LLM_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app import rules  # noqa: E402
from app.kb import KnowledgeBase  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/health").json()
    assert r["status"] == "ok" and r["kb_chunks"] > 0 and r["llm_enabled"] is False


def test_urgent_technical_alerts():
    r = client.post("/triage", json={"sender": "ali@example.com",
                                     "message": "URGENT: login is not working, production is blocked"})
    body = r.json()
    assert r.status_code == 200
    assert body["category"] == "technical" and body["priority"] == "urgent"
    assert body["needs_alert"] is True and body["provider"] == "rules"


def test_billing_uses_knowledge_base():
    body = client.post("/triage", json={"message": "I was charged twice, I want a refund"}).json()
    assert body["category"] == "billing"
    assert "refunds.md" in body["kb_sources"]


def test_turkish_message():
    body = client.post("/triage", json={"message": "Faturamda hata var, iade istiyorum"}).json()
    assert body["category"] == "billing" and body["priority"] == "high"


def test_low_priority_not_alerted():
    body = client.post("/triage", json={"message": "Thanks, great service!"}).json()
    assert body["priority"] == "low" and body["needs_alert"] is False
    assert body["sentiment"] == "positive"


def test_validation():
    assert client.post("/triage", json={"message": ""}).status_code == 422


def test_tickets_and_stats():
    assert len(client.get("/tickets").json()) >= 4
    s = client.get("/stats").json()
    assert s["total"] >= 4 and "billing" in s["by_category"]


def test_kb_search_ranks_relevant_doc():
    kb = KnowledgeBase(os.environ["KB_DIR"])
    assert kb.search("reset my password")[0]["source"] == "account.md"


def test_rules_summary_truncates():
    assert len(rules.classify("x" * 500)["summary"]) <= 140
