# UniStack

UniStack is a one-click, general-purpose Django project with three reusable apps baked in:

- **Unicom** for email, Telegram, WhatsApp, internal messaging, and web chat.
- **Unicrm** for contacts, companies, segments, mailing lists, and campaigns.
- **Unibot** for tool-using AI bots and encrypted integration credentials.

It deploys Django, PostgreSQL, Gunicorn/ASGI, and a Unibot worker with Docker Compose. AI uses the Portacode device's local, OpenAI-compatible **Responses API** at `127.0.0.1:61789/v1`; no external OpenAI key is required. Calls consume the connected Portacode account's AI balance, and model availability may change over time.

## Deploy with Portacode

Open this repository from your connected GitHub account in the Portacode dashboard and deploy its `portafile.yaml`. The private repository requires the device's scoped GitHub connection.

The template requests 2 CPUs, 3 GiB RAM, 12 GiB disk, exposes port 8000, creates `/opt/UniStack`, and waits for `/health/`.

## Local deployment on a paired Portacode device

```bash
cp .env.example .env
python3 scripts/configure_env.py .env
docker compose up -d --build
```

Create an administrator:

```bash
docker compose exec web python manage.py createsuperuser
```

Open `http://localhost:8000/`. Test the Responses API bridge with:

```bash
curl -X POST http://localhost:8000/api/ai/respond/ \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Say hello from UniStack in one sentence."}'
```

The web and worker services intentionally use host networking on Linux so the Portacode Responses listener remains local-only and reachable at `127.0.0.1`. PostgreSQL is bound only to host loopback on port 5433.

## Source provenance

The vendored app snapshots are taken from the standalone Unicom, Unicrm, and Unibot repositories used by Portacode. Snapshot commit IDs are recorded in `VENDORED_APPS.md`.

