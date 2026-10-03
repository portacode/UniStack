# UniStack

A reusable Django project with UniCom messaging, UniBot AI bots, and UniCRM.
Docker Compose runs PostgreSQL, Redis, the ASGI web application, and a bot worker.
The AI demo uses UniCom's polished chat sidebar, mobile composer, attachments,
and streamed Markdown replies, using the same upstream pins as `meena-erian/unistack`.
UniCom and UniBot are public Git submodules pinned to compatible Responses API
commits. Deployment initializes all submodules recursively.

## Deploy with Portacode

[![Deploy with Portacode](https://img.shields.io/badge/Deploy_with-Portacode-176b3a?style=for-the-badge)](https://portacode.com/dashboard/?portafile=data%3Atext%2Fyaml%3Bcharset%3Dutf-8%2Csource_template%253A%2520ubuntu%250Aname%253A%2520UniStack%250Ahostname%253A%2520unistack%250Ausername%253A%2520root%250Arequires_codex_connection%253A%2520true%250Aresources%253A%250A%2520%2520disk_gib%253A%252012%250A%2520%2520ram_mib%253A%25203072%250A%2520%2520cpus%253A%25202%250Aproject_paths%253A%250A%2520%2520-%2520%252Fopt%252FUniStack%250Ainputs%253A%250A%2520%2520-%2520id%253A%2520django_superuser_username%250A%2520%2520%2520%2520type%253A%2520text%250A%2520%2520%2520%2520label%253A%2520Django%2520admin%2520username%250A%2520%2520%2520%2520required%253A%2520true%250A%2520%2520%2520%2520default%253A%2520admin%250A%2520%2520%2520%2520description%253A%2520Username%2520for%2520the%2520initial%2520Django%2520superuser.%250A%2520%2520-%2520id%253A%2520django_superuser_email%250A%2520%2520%2520%2520type%253A%2520email%250A%2520%2520%2520%2520label%253A%2520Django%2520admin%2520email%250A%2520%2520%2520%2520required%253A%2520true%250A%2520%2520%2520%2520description%253A%2520Email%2520address%2520for%2520the%2520initial%2520Django%2520superuser.%250A%2520%2520-%2520id%253A%2520django_superuser_password%250A%2520%2520%2520%2520type%253A%2520secret%250A%2520%2520%2520%2520label%253A%2520Django%2520admin%2520password%250A%2520%2520%2520%2520required%253A%2520true%250A%2520%2520%2520%2520description%253A%2520Password%2520for%2520the%2520initial%2520Django%2520superuser.%250Aautomation_task%253A%250A%2520%2520task_name%253A%2520Deploy%2520UniStack%250A%2520%2520instructions%253A%250A%2520%2520%2520%2520-%2520run%253A%2520docker%2520compose%2520version%250A%2520%2520%2520%2520-%2520run%253A%2520portacode%2520github-setup%250A%2520%2520%2520%2520-%2520run%253A%2520git%2520clone%2520--recurse-submodules%2520https%253A%252F%252Fgithub.com%252Fportacode%252FUniStack.git%2520%252Fopt%252FUniStack%250A%2520%2520%2520%2520-%2520run%253A%2520cd%2520%252Fopt%252FUniStack%2520%2526%2526%2520.%252Fscripts%252Fdeploy.sh%250A%2520%2520%2520%2520-%2520run%253A%2520cd%2520%252Fopt%252FUniStack%2520%2526%2526%2520docker%2520compose%2520exec%2520-T%2520web%2520python%2520scripts%252Fensure_superuser.py%250A%2520%2520%2520%2520-%2520wait_for%253A%2520https%253A%252F%252F%255Bexposed%253A8000%255D%252Fhealth%252F%250A%2520%2520%2520%2520%2520%2520timeout%253A%25201200%250A%2520%2520expose_ports%253A%250A%2520%2520%2520%2520-%25208000%250A%2520%2520on_success%253A%2520notify%250A%2520%2520on_failure%253A%2520suggest_fixes%250A)

The Ubuntu template already supplies Docker, Compose, npm, Playwright, and the
local Responses API. Deployment does not reinstall them. The embedded Portafile
requests admin credentials, clones into `/opt/UniStack`, builds the stack, waits
for readiness, and creates the administrator. UniStack itself currently requires
GitHub access; its two public submodules do not. Regenerate this button with
`python3 scripts/update_deploy_button.py` after editing `portafile.yaml`.
The documented public-repository variant is generated with
`python3 scripts/update_deploy_button.py --public` once the repository and its
raw YAML are anonymously readable. Do not use that variant while UniStack is private.

## Deploy in three steps

On a paired Portacode Ubuntu device with Docker access, Git, and Python 3:

```bash
git clone --recurse-submodules https://github.com/portacode/UniStack.git
cd UniStack
./scripts/deploy.sh
```

The script generates `.env` secrets once, initializes pinned submodules, builds,
checks the configured local AI model, migrates, synchronizes the demo bot/channel, collects static files, and waits for a healthy web service before the
worker starts. Re-running preserves secrets, database data, and uploaded files.
Create an administrator with `docker compose exec web python manage.py createsuperuser`.
Open `http://localhost:8000/` for the demo. Sign in with your administrator
credentials to start a conversation in WebChat, or open the app sections in Django
admin. `/health/` reports readiness.

Portacode automatically supplies the public URL during template deployment.
`PORTACODE_PRIMARY_PUBLIC_URL` and `PORTACODE_PRIMARY_PUBLIC_HOST` are also read
at container startup to configure the origin, allowed host, and CSRF origin.
For a manual public deployment, set `DJANGO_PUBLIC_ORIGIN`,
`DJANGO_ALLOWED_HOSTS`, and `DJANGO_CSRF_TRUSTED_ORIGINS` in `.env` and rerun the
script. Keep `.env` private and back it up alongside the database and media volume:
its encryption key is needed to decrypt stored credentials.

## Local AI

Web and worker use Linux host networking to reach the device-local Responses API
at `http://127.0.0.1:61789/v1`. No external OpenAI key is needed. The default bot
template delegates to `core.integrations.bot.reply` and uses `PORTACODE_LLM_MODEL`.
Override `PORTACODE_RESPONSES_BASE_URL`, `PORTACODE_RESPONSES_API_KEY`, and
`PORTACODE_LLM_MODEL` in `.env` if necessary. `PORTACODE_REASONING_EFFORT` defaults
to `none`; set a value supported by your selected model. Calls consume the connected account's
AI balance. Startup checks the local `/models` endpoint and stops with an actionable
error when the configured model is unavailable. `PORTACODE_RESPONSE_TIMEOUT`
defaults to 90 seconds; `UNISTACK_MAX_TOOL_CALLS` defaults to eight per turn,
including child requests. Existing custom bot code is preserved; use the same
delegation as `templates/unibot/default_bot.py` to opt into this integration.

Add tool definitions under `data/definitions/tools/` and list their names in the
source bot's `bot_tools`. Deployment runs upstream `sync_tools_and_bots` before
activating **UniStack WebChat**. Tool results are persisted by UniCom and a queued
child request continues the reply. The project adapter reuses public upstream
Responses code; see `VENDORED_APPS.md` for its pinned provenance.

Each provider attempt has a durable `ModelInvocation` record with its request,
response ID, outcome, and reported token usage. **Usage** shows conversation
totals; Django admin exposes the individual records as read-only. Missing usage
stays unknown. Monetary charges remain in Portacode rather than using guessed
prices. A failed or incomplete stream retains its partial text and failed status.
**Retry reply** requeues a failed turn only when it has made no tool calls;
completed turns and turns with tool side effects require a new message.

`POST /api/ai/respond/` accepts `{ "prompt": "Hello", "chat_id": "optional existing chat" }`
and returns HTTP 202 with the persisted message, chat, request, and polling URL.
It uses the same authenticated UniCom queue as the composer. Poll the returned
`messages_url` for the streamed reply. `GET /api/ai/usage/?chat_id=…` and
`POST /api/ai/retry/` are restricted to the conversation's account; POST requests
require the session's CSRF token.

Host-installed npm and Playwright remain available for development/browser tests;
they are not automatically installed inside the application image. Docker Desktop
host networking is not the target deployment environment.

## Project structure

- `config/`: project settings, URL routing, and ASGI configuration.
- `core/`: project-owned views and landing page; extend your application here.
- `apps/unicom`, `apps/unibot`: clean upstream submodules; no build-time patches.
- `apps/unicrm`: retained CRM snapshot.
- `templates/`: project-level template overrides, including the default AI bot.
- `data/definitions/`: the streaming demo bot and optional tool definitions.
- `scripts/deploy.sh`: repeatable deployment entry point.

See `VENDORED_APPS.md` for exact source provenance and branch choices. Submodule
updates should be reviewed and tested together; deployment never follows moving
branch tips with `--remote`.

## Demo walkthrough

1. Click **Deploy with Portacode**, connect Codex if prompted, and choose your admin credentials.
2. Wait for deployment to finish, then open the exposed port 8000 URL.
3. Sign in from the landing page and send a message in the chat composer.
   Replies stream through the actual UniCom message / UniBot worker pipeline;
   conversations survive a page reload. Use the sidebar to start another chat.
4. Explore the UniCom, UniCRM, and UniBot admin sections. Provider channels are
   optional and require your own credentials; no messages are sent automatically.

The chat and its HTTP APIs require authentication and CSRF protection. The UI
uses the upstream polling projection every second, matching the reference demo's
WebSocket-independent integration. Redis and ASGI routing remain available for
other WebSocket integrations. Lit is loaded from jsDelivr, so browsers need access
to that CDN. The default bot uses the local Responses API. See the [Portacode CI/CD reference](https://portacode.com/portacode-cicd-intro/)
for template fields and the documented README deploy-button format.

## Operations

Verify a running deployment with the committed browser acceptance test:

```bash
docker compose exec web python manage.py test core --noinput
python3 scripts/browser_acceptance.py --artifacts /tmp/unistack-acceptance
```

The browser test needs host Python Playwright, Chromium, and Pillow. It creates
and removes a temporary administrator and test conversations, consumes the local
AI balance, and checks intermediate streaming, persisted reloads, mobile layout,
image understanding, and the usage ledger. Screenshots stay in the chosen
artifact directory. Deterministic Django tests cover tool continuation, provider
failures, manual retries, and ownership without making AI calls.

```bash
docker compose ps
docker compose logs --tail=100 web worker
docker compose exec web python manage.py check
docker compose down  # preserves named data volumes
```

PostgreSQL listens only on host loopback port 5433 (`DB_PORT` is configurable).
Redis uses loopback port 6381 (`REDIS_PORT` is configurable). Web uses port 8000. Choose a device where those ports are available.
Do not use `docker compose down -v` unless deliberately deleting stored data.
