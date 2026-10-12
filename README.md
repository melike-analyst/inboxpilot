**AI-powered message triage and alert automation** built with n8n, a FastAPI "AI agent" service, and a small web dashboard.

Incoming messages (website form, email, Telegram, any webhook) are classified by category, priority, and sentiment. The system writes a short summary, drafts a reply using a knowledge base (RAG), stores everything, and sends an instant alert to your phone for urgent cases.

```
                        ┌──────────────────────────── n8n ─────────────────────────────┐
 Website form ─┐        │                                                               │
 Email / bot  ─┼─POST──▶│ Webhook ─▶ AI Triage ─▶ High/Urgent? ─yes─▶ Telegram alert ─┐ │
 Any system   ─┘        │                │                      └─no──────────────────┴▶ Respond
                        │                ▼                                               │
                        │        FastAPI AI service                                      │
                        │  (RAG over knowledge base + LLM or rule fallback + SQLite)    │
                        │                                                               │
                        │ Weekday 09:00 ─▶ Get stats ─▶ Build digest ─▶ Telegram digest │
                        └───────────────────────────────────────────────────────────────┘
                                         ▲
                              Web dashboard (http://localhost:8000)
```

## Features

- **AI agent service (FastAPI):** structured triage with an LLM through any OpenAI-compatible API (OpenAI, Groq, OpenRouter, Ollama, LM Studio).
- **Works without an API key:** if no key is set, or the LLM call fails or returns invalid JSON, a rule-based fallback (English + Turkish keywords) keeps the pipeline running.
- **RAG:** a lightweight TF-IDF retriever finds relevant knowledge base chunks (`knowledge_base/*.md`) and passes them to the LLM, so replies follow your own policies.
- **n8n orchestration:** webhook intake, branching on priority, Telegram alerts (mobile push), and a scheduled daily digest.
- **Web dashboard:** live stats, ticket table with priority filter, reply drafts, and a form to test messages. It is responsive, so it works on phones.
- **Persistence:** SQLite, with no extra database to install.
- **Tested:** pytest suite and a GitHub Actions workflow.
- **Prompt-injection aware:** customer text is passed as data, and LLM output is validated against allowed values.

## Tech stack

Python 3.12 · FastAPI · Pydantic · SQLite · httpx · n8n · Docker Compose · HTML/CSS/vanilla JS · pytest · GitHub Actions

## Quick start

Requirements: Docker and Docker Compose.

```bash
git clone <your-repo-url> inboxpilot && cd inboxpilot
cp .env.example .env          # optional: add LLM key / Telegram settings
docker compose up -d --build
```

| Service   | URL                    |
|-----------|------------------------|
| Dashboard | http://localhost:8000  |
| API docs  | http://localhost:8000/docs |
| n8n       | http://localhost:5678  |

### Import the n8n workflow

Option A, in the UI: open n8n, then **Workflows → Import from file** and choose `n8n/workflows/inboxpilot.json`.

Option B, from the CLI:

```bash
docker compose exec n8n n8n import:workflow --input=/workflows/inboxpilot.json
```

Then open the workflow and switch **Active** on. The webhook is now available at `http://localhost:5678/webhook/inbound`.

### Try it

```bash
pip install httpx
python scripts/send_samples.py
```

Or with curl:

```bash
curl -X POST http://localhost:5678/webhook/inbound \
  -H "Content-Type: application/json" \
  -d '{"source":"web","sender":"ali@example.com","message":"URGENT: login is not working"}'
```

Example response:

```json
{
  "id": 2,
  "category": "technical",
  "priority": "urgent",
  "sentiment": "neutral",
  "summary": "URGENT: login is not working",
  "suggested_reply": "Hi ali, ...",
  "kb_sources": ["account.md"],
  "provider": "rules",
  "needs_alert": true
}
```

## Configuration

All settings are environment variables (see `.env.example`).

| Variable | Description | Default |
|---|---|---|
| `LLM_API_KEY` | Enables LLM mode. Empty means rule-based mode | empty |
| `LLM_BASE_URL` | OpenAI-compatible endpoint | `https://api.openai.com/v1` |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Enables phone alerts and the daily digest | empty |
| `TIMEZONE` | Schedule timezone | `Europe/Istanbul` |

Telegram setup: create a bot with `@BotFather`, send it any message, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat.id`. Without these values the workflow still runs, and the alert steps simply fail silently (`continueOnFail`).

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/triage` | Classify a message and store the ticket |
| `GET` | `/tickets?priority=high&limit=50` | List tickets |
| `GET` | `/stats` | Counts by category, priority, sentiment |
| `GET` | `/health` | Status, LLM mode, knowledge base size |

## Project structure

```
inboxpilot/
├── api/
│   ├── app/
│   │   ├── main.py        # routes and orchestration
│   │   ├── llm.py         # LLM call + output validation
│   │   ├── rules.py       # offline fallback classifier
│   │   ├── kb.py          # TF-IDF retrieval (RAG)
│   │   ├── db.py          # SQLite storage
│   │   ├── schemas.py     # Pydantic models
│   │   └── static/index.html   # dashboard
│   ├── tests/test_api.py
│   ├── Dockerfile
│   └── requirements.txt
├── n8n/workflows/inboxpilot.json
├── knowledge_base/        # your policies and FAQs (markdown)
├── scripts/send_samples.py
├── docker-compose.yml
└── .env.example
```

## Run without Docker

```bash
cd api
pip install -r requirements.txt
DB_PATH=../data/inboxpilot.db KB_DIR=../knowledge_base uvicorn app.main:app --reload
python -m pytest -q
```

## Customize

- **Your own knowledge:** drop `.md` files into `knowledge_base/`. Use `#` headings to split topics, then restart the API.
- **New channels:** point any tool (Typeform, Google Forms, Zapier, a Telegram bot) at the n8n webhook.
- **More actions in n8n:** add nodes after "High or urgent?" for Slack, email, Google Sheets, Notion, or a CRM.
- **Bigger scale:** replace SQLite with PostgreSQL and `kb.py` with a vector database (Qdrant or pgvector).

## Security notes

- Never commit `.env`. It is already in `.gitignore`.
- The API has no authentication. Do not expose port 8000 or the webhook publicly without adding an API key or a reverse proxy.
- Messages are stored in plain text in SQLite. Avoid sending sensitive personal data.

## Roadmap

- [ ] API key authentication
- [ ] Human approval step before sending replies
- [ ] Vector search with embeddings
- [ ] Evaluation set to measure classification accuracy
- [ ] Multi-language reply tests

## License

MIT
