# Building an application from this template

This is a project-agnostic application foundation. Deliver the requested product,
not a UniStack demo. Read `docs/application-guide.md` before customization.

- Preserve `core/templates/core/base.html`, the responsive navigation and page
  module lifecycle. Extend the shell for product pages instead of replacing it.
- Set `branding.json` once. Website, sign-in and assistant share its name, logo
  and colors. Never scatter branding values through templates or upstream apps.
- Keep `/` as the product marketing home. Replace `marketing.json`, the
  feature headings/illustration in `core/templates/core/home.html` and the
  auth story with accurate product marketing. Never leave generic starter
  copy or invent customers, testimonials, compliance or performance claims.
  Put the product's primary app flow on its own route and navigation entry.
- Add normal Django routes and entries to `SITE_NAVIGATION`. Use page modules
  for lazy feature initialization, returning cleanup functions for listeners,
  timers and in-flight work. Keep forms functional after direct navigation.
- Keep `apps/unicom` and `apps/unibot` unchanged; integrate through public APIs
  and CSS custom properties. Keep account isolation and CSRF checks intact.
- For document apps, enforce ownership on every list, detail, download, search
  and AI retrieval operation. Never put private documents in public static files.
- Implement actual persistence and AI tools. A conversational mock or canned
  summary does not satisfy an AI-assisted product request.
- Add retrieval/instructions through `core/integrations/context.py`, which is
  shared by the native UniCom composer and HTTP API. Changing only
  `/api/ai/respond/` does not change the visible chat's behavior.
- Run Django checks and affected tests, then test the deployed site at desktop
  and phone sizes: navigation/back/reload, authentication, primary CRUD flow,
  upload/download, search, real AI response, errors, and cross-account isolation.
  Review screenshots and browser errors before reporting completion.
- Generate migrations with Django against a source-mounted container; do not
  hand-write migration files or index names. Check migration drift before
  deploying. See the container development loop in `docs/application-guide.md`.
- Scaffold new apps with `./scripts/check.sh --startapp documents`, register
  the app in settings, then use `./scripts/check.sh --migrations documents`.
  Both commands write to the project, not a disposable container. Never
  generate migrations with `docker compose exec` against the built image.
- Keep login, signup and assistant URLs. Use `UNISTACK_ALLOW_SIGNUP=false`
  for invite-only apps and `UNISTACK_ALLOW_ANONYMOUS_CHAT=false` for private
  chat. Shared templates already hide unavailable signup actions. Do not
  remove auth routes or replace the shell to implement access policy.
- Extend the existing assistant through its shared context hook. Do not build
  a parallel composer/Markdown renderer for document questions. Preserve the
  full-height chat layout, skeleton theme and responsive navigation. Up to
  five visible entries become mobile bottom tabs; more use the mobile menu.
- Test source changes in a one-off container before rebuilding the live app.
  Use `./scripts/check.sh` (or `./scripts/check.sh --migrations core` to
  generate migrations), then `./scripts/deploy.sh`. Do not reimplement setup
  or repeatedly issue manual Compose commands for routine customization.
  Recreate only changed services; repeatedly forcing the entire Compose stack
  to recreate interrupts the database and makes browser verification unreliable.
- Do not deploy changes by restarting the host Portacode service. Use the
  project's `scripts/deploy.sh` for application rebuilds.
