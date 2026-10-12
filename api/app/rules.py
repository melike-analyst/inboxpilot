"""Rule-based fallback. Used when no LLM key is set or the LLM call fails.
Keeps the whole pipeline working offline and makes tests deterministic."""

CATEGORY_WORDS = {
    "billing": ["invoice", "refund", "charge", "payment", "bill", "receipt",
                "fatura", "ödeme", "iade", "ücret"],
    "technical": ["error", "bug", "crash", "not working", "doesn't work", "login", "password",
                  "broken", "hata", "çalışmıyor", "giriş", "şifre"],
    "sales": ["price", "pricing", "quote", "demo", "plan", "enterprise", "fiyat", "teklif"],
    "complaint": ["terrible", "worst", "unacceptable", "angry", "complaint", "disappointed",
                  "şikayet", "rezalet", "memnun değil"],
}
URGENT = ["urgent", "asap", "immediately", "outage", "acil", "hemen", "production down"]
HIGH = ["refund", "cannot", "can't", "broken", "not working", "charged twice", "iade",
        "çalışmıyor", "hata", "unacceptable", "rezalet"]
NEG = ["terrible", "worst", "angry", "disappointed", "unacceptable", "broken", "bad",
       "rezalet", "kötü", "şikayet", "berbat"]
POS = ["thanks", "thank you", "great", "love", "awesome", "perfect", "teşekkür", "harika", "süper"]


def _count(text: str, words: list[str]) -> int:
    return sum(1 for w in words if w in text)


def classify(message: str, subject: "str | None" = None) -> dict:
    text = f"{subject or ''} {message}".lower()

    scores = {cat: _count(text, words) for cat, words in CATEGORY_WORDS.items()}
    best = max(scores, key=scores.get)
    category = best if scores[best] > 0 else "general"

    if _count(text, URGENT):
        priority = "urgent"
    elif category == "complaint" or _count(text, HIGH):
        priority = "high"
    elif category in ("sales", "billing", "technical"):
        priority = "medium"
    else:
        priority = "low"

    neg, pos = _count(text, NEG), _count(text, POS)
    sentiment = "negative" if neg > pos else "positive" if pos > neg else "neutral"

    summary = " ".join(message.split())
    if len(summary) > 140:
        summary = summary[:137] + "..."

    return {"category": category, "priority": priority, "sentiment": sentiment,
            "summary": summary}


def draft_reply(sender: "str | None", category: str, kb_hits: list[dict]) -> str:
    name = sender.split("@")[0] if sender else "there"
    lines = [f"Hi {name},", "", "Thanks for reaching out."]
    if kb_hits:
        snippet = kb_hits[0]["text"].split("\n", 1)[-1].strip()
        lines += ["", snippet[:400]]
    else:
        lines += ["", f"We received your {category} request and a team member will reply soon."]
    lines += ["", "Best regards,", "Support Team"]
    return "\n".join(lines)
