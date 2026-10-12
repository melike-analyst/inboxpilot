"""Send sample messages to the n8n webhook (or straight to the API).

Usage:
  python scripts/send_samples.py                     # n8n webhook (default)
  python scripts/send_samples.py http://localhost:8000/triage
"""
import sys

import httpx

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5678/webhook/inbound"

SAMPLES = [
    {"source": "email", "sender": "ayse@example.com", "subject": "Invoice problem",
     "message": "I was charged twice this month. Please refund the extra payment."},
    {"source": "web", "sender": "john@example.com", "subject": "Cannot login",
     "message": "URGENT: login is not working and our team is blocked."},
    {"source": "telegram", "sender": "mehmet", "subject": None,
     "message": "Kurumsal plan için fiyat teklifi alabilir miyim?"},
    {"source": "web", "sender": "sara@example.com", "subject": "Thanks",
     "message": "Thanks, the new dashboard is great!"},
    {"source": "email", "sender": "tom@example.com", "subject": "Terrible experience",
     "message": "This is the worst support I have seen. I am very disappointed."},
]

for s in SAMPLES:
    r = httpx.post(URL, json=s, timeout=30)
    d = r.json()
    print(f"[{r.status_code}] {d.get('priority', '?'):>6} | {d.get('category', '?'):<9} | {d.get('summary', '')[:60]}")
