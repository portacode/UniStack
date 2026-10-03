# Development and maintenance

These notes are for maintainers. The deploy button handles initial setup.

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

## Maintaining the deployment template

Edit `portafile.yaml` and regenerate the embedded deploy button with
`python3 scripts/update_deploy_button.py`. The template clones into
`~/.unistack-template`, then `scripts/create_project.py` moves each submodule's
Git history into the child directory, removes only the parent Git history, and
renames the folder to the requested slug (default `my-project`). It refuses
existing destinations and invalid slugs. `.template-origin.json` records the
original template and app commits. UniCRM remains a bundled snapshot.

The final automation command prints the completed project's absolute path and
uses `register_project: true` to mark it as a Portacode project after deployment.
Do not add top-level `project_paths`: that would register a folder during
provisioning, before the clone and rename. This post-command action requires a
Portacode service with `register_project` support; it uses the successful command
result and does not require a separate device connection.

Run `python3 scripts/test_create_project.py` to verify that detaching and renaming
preserves child and nested-submodule histories and does not overwrite folders.
