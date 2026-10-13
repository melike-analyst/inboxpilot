# Sharing a live demo (free options)

Pick the option that fits. They can be combined.

| Option | Cost | Always on? | Shows | Setup |
|---|---|---|---|---|
| A. GitHub Pages (static demo) | Free | Yes | Dashboard + triage in the browser (simulated) | 3 min |
| B. Local app + Cloudflare quick tunnel | Free | Only while your PC is on | The real app (FastAPI + dashboard) | 5 min |
| C. Free container host (Render free instance, Cloud Run) | Free tier | Sleeps when idle | The real API + dashboard | 10-15 min |
| D. Screen recording of the n8n workflow | Free | Forever | n8n + Telegram + dashboard together | 15 min |

> n8n itself needs more memory than most free container tiers offer, so show n8n through
> option D (recording) or a local screen share. Do not expose the n8n editor to the internet.

## A. GitHub Pages (recommended for a permanent link)

1. Push the repo to GitHub (public).
2. Open `docs/index.html` and replace `YOUR-USERNAME` in the source-code link.
3. GitHub repo -> **Settings -> Pages -> Build and deployment**: Source = *Deploy from a branch*,
   Branch = `main`, Folder = `/docs`. Save.
4. After about a minute the demo is at `https://<username>.github.io/<repo>/`.

`docs/demo-shim.js` replaces the API calls with an in-browser copy of the rule engine, so the page
needs no server. It is clearly labelled as a static demo.

## B. Run locally and share a temporary public link

```bash
docker compose up -d --build
# install cloudflared once: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
cloudflared tunnel --url http://localhost:8000
```

The command prints a random `https://<words>.trycloudflare.com` address. Send it to the person you
are presenting to. Stop the command (Ctrl+C) when finished.

Rules for a public tunnel:
- Tunnel **only port 8000** (dashboard + API), never 5678 (the n8n editor).
- Leave `LLM_API_KEY` empty while the link is public, otherwise strangers can spend your credits.
- The link changes every time and works only while your computer and the command are running.

## C. Free container host

The root `Dockerfile` builds a single container that honors `$PORT` and fills the dashboard with demo
data on start (`DEMO_SEED=1`). Data is stored in `/tmp`, so it resets on restart, which is fine for a demo.

**Render:** New -> Web Service -> connect the GitHub repo -> Language: Docker -> choose the **Free**
instance type -> Create. No environment variables are required. A free instance sleeps after
about 15 minutes without traffic, so the first request after a pause takes around a minute.
Plans change often; if the Free type is not offered for your account, use option A or B.

**Google Cloud Run:** has a monthly free allowance but needs a billing account (card).

Note: Hugging Face Docker Spaces now require a paid plan. Only *Static* Spaces are free.

## D. Record the n8n workflow (best way to show n8n)

1. `docker compose up -d --build`, open http://localhost:5678, import `n8n/workflows/inboxpilot.json`.
2. For Telegram: set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`, then
   `docker compose up -d` again.
3. Start a screen recorder (Windows: Win+G; macOS: Cmd+Shift+5; or the free OBS Studio).
4. Suggested 60-90 second script:
   1. Show the workflow canvas and name the nodes (webhook -> AI triage -> branch -> alert).
   2. Click **Execute workflow** (the webhook waits for a test call at `/webhook-test/inbound`).
   3. Run `python scripts/send_samples.py http://localhost:5678/webhook-test/inbound`
      (a test URL accepts one call per click; use the production URL after activating the workflow).
   4. Show the green nodes and the JSON output of **AI Triage**.
   5. Open the dashboard at http://localhost:8000 and show the new ticket.
   6. Show the Telegram alert on your phone.
5. Upload to YouTube (unlisted) or add the file as a GIF/MP4 link in the README.

A ready-made diagram of the workflow is in `docs/images/n8n-workflow.png`.
