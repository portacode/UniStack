# UniStack

Build a custom AI application on Django with a working chat UI, Python bots and
tools, persistent messaging, and CRM. UniStack combines **UniCom**, **UniBot**, and
**UniCRM** in a deployable project you can extend with your own models, workflows,
integrations, and frontend.

Use it as a foundation for customer assistants, internal copilots, or agents that
act through your APIs. It includes account/session-level conversation isolation;
see [tenant isolation and access](#tenant-isolation-and-access) for the exact scope.

[![Deploy with Portacode](https://img.shields.io/badge/Deploy_with-Portacode-176b3a?style=for-the-badge)](https://portacode.com/dashboard/?portafile=https%3A%2F%2Fraw.githubusercontent.com%2Fportacode%2FUniStack%2Fmain%2Fportafile.yaml)

**Click the button, choose an optional project name and chat access, and enter your
admin credentials.** Portacode provisions the environment and deploys everything
automatically. When it finishes, open the app link and start chatting.
The local Portacode AI connection is configured for you.

**Anonymous visitors can access AI chat** is enabled by default. Each visitor gets
their own session and saved conversations; signing in transfers that session's
chat history to their account. Turn the option off to require sign-in before
chatting. AI usage, including guest messages, uses your connected Portacode balance.

Your project lives in your home directory under the name you chose, or
`my-project` if you leave the name blank. It is marked as a Portacode project
after the folder has been renamed and deployment has succeeded. The template's
Git history is removed so you can connect your own repository later; the
upstream app repositories retain their history.

## What is included

| Area | Capabilities |
| --- | --- |
| AI chat | Streamed Markdown replies, saved conversations and sidebar, image attachments, mobile composer, and conversation history supplied to the model. |
| Custom agents | Python bot handlers, per-bot tool selection, structured tool arguments, persisted tool calls/results, and queued continuation after tools respond. The demo starts with no tools enabled. |
| Usage and failures | Per-conversation token usage and per-attempt model records in Django admin. Incomplete streams retain partial replies; eligible failed turns can be retried when no tools have run. |
| Messaging — UniCom | Accounts, channels, chat memberships, messages, attachments, and background requests. WebChat is configured on deployment; Email, Telegram, and WhatsApp integrations require provider setup. |
| Bot framework — UniBot | Source-defined bots/tools synchronized into the database, Django admin management, and account-scoped encrypted credentials with credential setup flows. |
| CRM — UniCRM | Companies, contacts, mailing lists, subscriptions, programmable segments, communication templates, campaigns, and delivery/engagement views. Campaign delivery needs channel and scheduler configuration. |
| Application stack | Django, PostgreSQL, Redis, Docker Compose web/worker services, persistent database/media volumes, and a health endpoint. The supplied deployment targets a Linux Portacode device. |

The default AI connection uses the device-local Portacode Responses API and your
connected balance, without a separate OpenAI API key. Model, endpoint, reasoning
effort, and timeout are configurable. External messaging providers and other
integrations use their own credentials.

## Tenant isolation and access

UniStack provides **application-level account and conversation boundaries** in a
shared database. These are useful building blocks for a multi-user AI application:

- **Chat ownership:** WebChat uses account/chat membership. Each signed-in user
  has a WebChat account; anonymous visitors have separate browser-session accounts.
  Existing-chat writes, history, AI usage, and retry actions enforce account access.
- **Chat attachments:** Access follows conversation membership, with staff access
  for administrative inspection. Guest history transfers to the user's account on
  login; clearing guest cookies loses access to that session's history.
- **Integration credentials:** UniBot stores encrypted credentials by account and
  credential key. Its credential helper looks them up for the current account;
  bot/tool execution receives the request's account context.
- **Access policy:** Deployment can allow guest chat or require sign-in. Chat POST
  endpoints enforce CSRF protection. The demo includes admin login; public signup
  and customer onboarding are application features you add.

**Company-level tenant isolation needs additional application design.** The
template does not configure separate schemas/databases per tenant or an
organization membership/role system. CRM data and non-chat media do not inherit
WebChat's conversation boundaries; non-chat media is available to signed-in users.
Custom tools must authorize access to their own data and external services using
the account context. Add tenant scoping for your models, retrieval indexes, files,
and jobs when building a shared SaaS application.

Existing [chat access tests](core/test_chat_access.py) and
[AI integration tests](core/test_ai_integration.py) cover cross-account/session
access checks, attachments, usage, retries, and attempts to write to another
account's chat.

## Customize your AI application

| Change | Starting point |
| --- | --- |
| Bot behavior and routing | [Source bot](data/definitions/bots/unistack.py): replace or extend the Python message handler; add more bot definitions for different workflows. |
| Instructions and model context | [AI adapter](core/integrations/bot.py): customize the system instruction, conversation-history selection, and response handling. |
| Actions and integrations | Add Python tool definitions under `data/definitions/tools/` and name them in the bot's `bot_tools`. Tools can call your APIs, query authorized data, or return files. Deployment synchronizes definitions with `sync_tools_and_bots`. |
| Model and runtime limits | Configure `PORTACODE_LLM_MODEL`, `PORTACODE_REASONING_EFFORT`, `PORTACODE_RESPONSES_BASE_URL`, `PORTACODE_RESPONSE_TIMEOUT`, and `UNISTACK_MAX_TOOL_CALLS`. |
| Product UI and business data | Extend `core/`, project templates, and `config/`; add Django models, views, permissions, and routes alongside the reusable apps. |
| A separate frontend | Use `POST /api/ai/respond/` to queue a prompt, poll the returned messages URL, and use `/api/ai/usage/` and `/api/ai/retry/` with the same session access rules. |

Document ingestion, vector search/RAG, tenant billing, and model training or
fine-tuning are extensions you build or integrate. UniStack supplies the chat,
agent execution, persistence, and application structure for those workflows.

## See the demo

Desktop chat with Markdown replies and a conversation sidebar:

![UniStack desktop WebChat](docs/screenshots/webchat-desktop.png)

The same conversation on mobile:

<img src="docs/screenshots/webchat-mobile.png" alt="UniStack mobile WebChat" width="320">

Conversations and streamed replies persist through reloads. Attach an image
to ask about it, select **Usage** to see reported tokens, or open **Admin**
to explore UniCom, UniBot, and UniCRM.

## Build your project

- `core/`: your application features and project integration.
- `config/`: Django settings and routing.
- `data/definitions/`: source-defined bots and tools, synced on deployment.
- `apps/`: the reusable messaging, bot, and CRM apps.

For development and maintenance, see [the technical notes](docs/development.md).
Exact upstream versions are recorded in [application provenance](VENDORED_APPS.md).
