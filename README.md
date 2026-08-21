# UniStack

UniStack is a one-click, general-purpose Django project with three reusable apps baked in:

- **Unicom** for email, Telegram, WhatsApp, internal messaging, and web chat.
- **Unicrm** for contacts, companies, segments, mailing lists, and campaigns.
- **Unibot** for tool-using AI bots and encrypted integration credentials.

It deploys Django, PostgreSQL, Gunicorn/ASGI, and a Unibot worker with Docker Compose. AI uses the Portacode device's local, OpenAI-compatible **Responses API** at `127.0.0.1:61789/v1`; no external OpenAI key is required. Calls consume the connected Portacode account's AI balance, and model availability may change over time.

## Deploy with Portacode

[![Deploy with Portacode](https://img.shields.io/badge/Deploy_with-Portacode-176b3a?style=for-the-badge)](https://portacode.com/dashboard/?portafile=data%3Atext%2Fyaml%3Bcharset%3Dutf-8%2Csource_template%253A%2520ubuntu%253C%253D24.04%252C%2520ubuntu-22.04%250Aname%253A%2520UniStack%250Ahostname%253A%2520unistack%250Ausername%253A%2520root%250Arequires_codex_connection%253A%2520true%250Aresources%253A%250A%2520%2520disk_gib%253A%252012%250A%2520%2520ram_mib%253A%25203072%250A%2520%2520cpus%253A%25202%250Aproject_paths%253A%250A%2520%2520-%2520%252Fopt%252FUniStack%250Aautomation_task%253A%250A%2520%2520task_name%253A%2520Deploy%2520UniStack%250A%2520%2520inputs%253A%250A%2520%2520%2520%2520-%2520id%253A%2520django_superuser_username%250A%2520%2520%2520%2520%2520%2520type%253A%2520text%250A%2520%2520%2520%2520%2520%2520label%253A%2520Django%2520admin%2520username%250A%2520%2520%2520%2520%2520%2520required%253A%2520true%250A%2520%2520%2520%2520%2520%2520default%253A%2520admin%250A%2520%2520%2520%2520%2520%2520persist_environment%253A%2520true%250A%2520%2520%2520%2520%2520%2520description%253A%2520Username%2520for%2520the%2520initial%2520Django%2520superuser.%250A%2520%2520%2520%2520-%2520id%253A%2520django_superuser_email%250A%2520%2520%2520%2520%2520%2520type%253A%2520text%250A%2520%2520%2520%2520%2520%2520label%253A%2520Django%2520admin%2520email%250A%2520%2520%2520%2520%2520%2520required%253A%2520true%250A%2520%2520%2520%2520%2520%2520persist_environment%253A%2520true%250A%2520%2520%2520%2520%2520%2520description%253A%2520Email%2520address%2520for%2520the%2520initial%2520Django%2520superuser.%250A%2520%2520%2520%2520-%2520id%253A%2520django_superuser_password%250A%2520%2520%2520%2520%2520%2520type%253A%2520secret%250A%2520%2520%2520%2520%2520%2520label%253A%2520Django%2520admin%2520password%250A%2520%2520%2520%2520%2520%2520required%253A%2520true%250A%2520%2520%2520%2520%2520%2520persist_environment%253A%2520true%250A%2520%2520%2520%2520%2520%2520description%253A%2520Password%2520for%2520the%2520initial%2520Django%2520superuser.%250A%2520%2520instructions%253A%250A%2520%2520%2520%2520-%2520run%253A%2520sudo%2520apt-get%2520update%250A%2520%2520%2520%2520-%2520run%253A%2520sudo%2520apt-get%2520install%2520-y%2520ca-certificates%2520curl%2520git%250A%2520%2520%2520%2520-%2520run%253A%2520curl%2520-fsSL%2520https%253A%252F%252Fget.docker.com%2520%257C%2520sudo%2520sh%250A%2520%2520%2520%2520-%2520run%253A%2520sudo%2520systemctl%2520enable%2520--now%2520docker%250A%2520%2520%2520%2520-%2520run%253A%2520sudo%2520docker%2520compose%2520version%250A%2520%2520%2520%2520-%2520run%253A%2520portacode%2520github-setup%250A%2520%2520%2520%2520-%2520run%253A%2520git%2520clone%2520https%253A%252F%252Fgithub.com%252Fportacode%252FUniStack.git%2520%252Fopt%252FUniStack%250A%2520%2520%2520%2520-%2520run%253A%2520cd%2520%252Fopt%252FUniStack%2520%2526%2526%2520cp%2520.env.example%2520.env%2520%2526%2526%2520python3%2520scripts%252Fconfigure_env.py%2520.env%250A%2520%2520%2520%2520-%2520run%253A%2520cd%2520%252Fopt%252FUniStack%2520%2526%2526%2520sudo%2520docker%2520compose%2520up%2520-d%2520--build%250A%2520%2520%2520%2520-%2520run%253A%2520cd%2520%252Fopt%252FUniStack%2520%2526%2526%2520sudo%2520docker%2520compose%2520exec%2520-T%2520web%2520python%2520scripts%252Fensure_superuser.py%250A%2520%2520%2520%2520-%2520wait_for%253A%2520https%253A%252F%252F%255Bexposed%253A8000%255D%252Fhealth%252F%250A%2520%2520%2520%2520%2520%2520timeout%253A%25201200%250A%2520%2520expose_ports%253A%250A%2520%2520%2520%2520-%25208000%250A%2520%2520on_success%253A%2520notify%250A%2520%2520on_failure%253A%2520suggest_fixes%250A)

The button embeds the Portafile in its dashboard URL because this repository is private; an anonymous `raw.githubusercontent.com` URL cannot load it. Deployment still requires scoped GitHub access to `portacode/UniStack` so the new device can clone the project.

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
