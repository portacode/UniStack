# Building an application from this template

This is a project-agnostic application foundation. Deliver the requested product,
not a UniStack demo. Read `docs/application-guide.md` before customization.

- Preserve `core/templates/core/base.html`, the responsive navigation and page
  module lifecycle. Extend the shell for product pages instead of replacing it.
- Set `branding.json` once. Website, sign-in and assistant share its name, logo
  and colors. Never scatter branding values through templates or upstream apps.
- Replace the overview content with the requested product's real primary flow.
  Do not leave starter cards, sample metrics, marketing banners or fake actions.
- Add normal Django routes and entries to `SITE_NAVIGATION`. Use page modules
  for lazy feature initialization, returning cleanup functions for listeners,
  timers and in-flight work. Keep forms functional after direct navigation.
- Keep `apps/unicom` and `apps/unibot` unchanged; integrate through public APIs
  and CSS custom properties. Keep account isolation and CSRF checks intact.
- For document apps, enforce ownership on every list, detail, download, search
  and AI retrieval operation. Never put private documents in public static files.
- Implement actual persistence and AI tools. A conversational mock or canned
  summary does not satisfy an AI-assisted product request.
- Run Django checks and affected tests, then test the deployed site at desktop
  and phone sizes: navigation/back/reload, authentication, primary CRUD flow,
  upload/download, search, real AI response, errors, and cross-account isolation.
  Review screenshots and browser errors before reporting completion.
- Do not deploy changes by restarting the host Portacode service. Use the
  project's `scripts/deploy.sh` for application rebuilds.
