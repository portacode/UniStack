# Build on the provided application shell

The starter has a marketing home, full-height assistant, branded signup and sign-in/out, responsive site
navigation, active links, browser back/forward support, loading/error states,
keyboard focus handling and optional page modules. The overview does not load
Lit or chat code. Opening the assistant dynamically loads the shared UniCom UI.
All links remain ordinary server-rendered Django URLs without JavaScript.

## One brand

Deployment accepts `brand_name`, `brand_tagline`, optional `brand_logo` (PNG,
JPEG or WebP up to 5 MiB), `brand_primary` and `brand_accent`. Portacode delivers
the upload as a local file path in `BRAND_LOGO`; `scripts/configure_branding.py`
copies it into project static assets before the Docker build. Values are stored
in `branding.json`, with an initial-letter fallback when no logo is supplied.
Blank optional inputs preserve saved values on redeployment. To remove a logo,
set `logo` to an empty string in that file and redeploy.

`core.branding.context` exposes the shared `brand` object. The shell sets CSS
custom properties, including automatically chosen light/dark foregrounds.
`core/site.css` maps these into UniCom's documented custom properties. The
assistant identity and favicon reuse the logo. No edits to upstream apps are
needed. The default AI identity also uses the project name. For custom behavior,
edit the project-owned bot adapter and tool definitions.
Deployment also synchronizes the UniCom bot sender's display name and its
existing outgoing message labels. Changing the brand therefore updates chat
history as well as the website; the internal channel ID stays stable.

## Add a product page

1. Add a view in your application and a normal URL, e.g. `/documents/`.
2. Extend `core/page.html`, supply `page_title` in the view context, and put
   content inside `{% block page_content %}`. It supplies the page heading,
   spacing, messages and an optional `page_actions` block inside the shared shell.
   Add the route to `SITE_NAVIGATION`; the same entries appear on chat and auth pages.
3. Use `data-nav` on internal links that can use enhanced navigation. Leave
   login, logout, downloads, external URLs and links needing a full reload alone.
4. Optional JavaScript goes in a separate ES module. Set `page_module` in the
   view context to `myapp/documents.js` when using `core/page.html`.
   Export `mount(main)` and scope selectors to `main`. Return a cleanup function.
   Scripts inside page content are intentionally not evaluated on navigation.
5. Use the shared `.button.primary`, `.button.secondary`, `.button.quiet`,
   `.page-content`, and brand variables. Register feature CSS in `SITE_STYLESHEETS`
   so it is available after navigating from any page. Scope it to a feature
   container (e.g. `.documents`) so it cannot restyle the navbar or assistant.

For a custom page layout, extend `core/base.html` and replace its `content` and
`main_attributes` blocks. Keep the outer shell. For custom navigation icons,
use an `icon_template` containing an SVG with class `nav-symbol`, `viewBox`,
`aria-hidden="true"` and `currentColor`. Do not create a second mobile navbar.

Example product page:

```django
{% extends 'core/page.html' %}
{% block page_actions %}<a class="button primary" href="/documents/new/" data-nav>Add document</a>{% endblock %}
{% block page_content %}<div class="documents">Your product content and forms</div>{% endblock %}
```

Configure its routes in the normal Django URLconf and its navigation in settings:

```python
SITE_NAVIGATION = [
    {"label": "Home", "url": "/", "icon": "overview"},
    {"label": "Documents", "mobile_label": "Files", "url": "/documents/",
     "icon": "documents", "authenticated": True},
    {"label": "Add document", "mobile_label": "Add", "url": "/documents/new/",
     "icon": "upload", "authenticated": True},
    {"label": "Assistant", "url": "/assistant/", "icon": "assistant"},
]
SITE_STYLESHEETS = ["documents/documents.css"]
```

Labels, order, icons, routes and mobile labels are customizable in one place.
In a stylesheet registered in `SITE_STYLESHEETS`, adjust `--sidebar-width`,
`--nav-item-radius` and `--mobile-nav-height` to change the shared navigation's
geometry; brand colors continue to come from `branding.json`. The mobile bar's
safe-area padding and the assistant's available height follow the same variables.
Only the most specific matching destination is active, so Add does not also
highlight Documents. Use `exact: True` for overview routes and `match: ["/other/"]`
to associate other detail routes with a destination. `full_reload: True` opts a
destination out of enhanced navigation for pages requiring a full reload.
`authenticated` controls visibility, not authorization: protect the Django view
as well. Keep mobile labels short; the full label remains the accessible name.

`check_site` validates the same shell and navigation on public destinations,
marketing, authentication and chat. It fails on a missing/replaced shell or a
separate navigation definition. It also discovers static routes in installed
project apps, so omitting a product page from navigation does not hide a second
shell. Parameterized detail routes still need product-specific tests. Before delivery, run
`docker compose exec -T web python manage.py check_site --username <test-account>`
to include private product routes using an existing test account. It signs in a
temporary test-client session and signs out afterward, without creating a user.
The deployment preflight runs the public checks before replacing the live app.

### Product presentation

Replace `marketing.json` with the actual product's headline, description,
features and closing call to action. Also update the section headings and
illustration labels in `core/templates/core/home.html` and the story in
`core/templates/registration/auth_base.html`. The supplied copy and decorative
product preview are placeholders; do not present them as proof of features or
invent customer logos, testimonials or usage statistics. Keep `/` public for
marketing and place private workflows on their own routes.

`SITE_NAVIGATION` drives both layouts: a left sidebar on large screens and
bottom tabs at mobile widths when 1–5 entries are visible. Six or more use a
menu. Add `authenticated: True` to account-only entries. Nested URLs inherit
their parent item's active state. Built-in icons include `overview`,
`assistant`, `documents`, `upload` and `settings`; extend `nav-icon.html` for
more. Keep the list focused on primary destinations; use in-page navigation
for secondary actions.

The assistant fills the remaining viewport after app navigation. Put optional
app-specific context in its compact toolbar, not an extra full page header.
Page transitions and chat initialization use skeletons with reduced-motion
support. `chat-theme.js` supplies scoped CSS to the pinned UniCom components'
open shadow roots, including subsequent history loads and send states. It
does not change component methods, transport, data or upstream files. Verify
this adapter when updating the UniCom submodule.

The `/media/` route serves only authorized chat attachments. For private
documents, use a view that looks up the document by both its ID and the current
user before returning `FileResponse`. Do not add a generic authenticated media
fallback: sign-in does not authorize someone else's files. Test raw storage
URLs as well as document URLs using a second account and an anonymous browser.
Existing integrations that previously relied on generic non-chat media serving
must add an explicit download route with their own access rules.

Use normal Django forms with CSRF protection, meaningful validation, empty
states and success/error feedback. Paginate data on the server; lazy page
modules are not a substitute for paginating large lists. Render image assets
with dimensions and `loading="lazy"` when below the fold.

## First-build acceptance

### Guest access and conversion

The deployment form's **Let visitors try AI chat before signing up** switch
sets `UNISTACK_ALLOW_ANONYMOUS_CHAT`. Enabled: visitors can start immediately,
then use `/accounts/signup/` or sign in to keep their conversations. Disabled:
the assistant requires an account. This controls chat access, not permission
to application data. Keep private document retrieval separately authorized.

The built-in signup uses Django password validation and automatic login.
Use `UNISTACK_ALLOW_SIGNUP=false` (also a deployment input) for an invite-only
app. Keep the signup route: it returns 404 and shared pages hide its links.
Do not delete the route or place the public marketing/auth pages behind login.
Both signup and login transfer conversations and attachments from the current
browser's guest session into the account, including queued requests. Other
guest sessions remain isolated. Signup does not verify email ownership; add
email verification before using an address as a trusted identity or invitation.
Preserve the login signal and session middleware when adding custom signup.

### Container development loop

The running containers use the built image, not source edits in the project
folder. After adding dependencies, build the image once. Then validate edits
through a source mount without repeatedly replacing the running app:

```sh
./scripts/check.sh --startapp documents  # Once, for a new Django app
# Register documents in INSTALLED_APPS, implement models/views and navigation.
./scripts/check.sh --migrations documents
./scripts/check.sh
./scripts/deploy.sh
```

Generate migrations with Django, including its index names; never hand-write
them. Add the new app label to `makemigrations` when appropriate. Run containers
as the checkout's owner when necessary to avoid root-owned generated files.
Once checks pass, use `./scripts/deploy.sh` to rebuild and wait for healthy
services, then run the live UI tests. Routine source edits do not require
`docker compose down` or `up --force-recreate` for the whole stack.
The check script checks memory headroom, bounds execution to five minutes,
and removes its own temporary container on exit. It runs checks, migration
drift detection and tests against edited source. Pass app/test labels to scope
tests (without labels it discovers all project tests, including new apps).
It also renders the public/auth pages in all signup/chat access combinations.
Deployment checks missing migrations before replacing app services and
creates the initial administrator automatically. Do not recreate the
deployment setup or run raw Compose commands for
routine edits. Use Compose directly only for a diagnosed infrastructure issue
or rebuilding an image after changing dependencies.

### Ground the actual chat UI

Put application context in `core/integrations/context.py`'s
`build_system_instruction(message, request)`. The bot adapter calls this hook
for both the native UniCom composer and the optional HTTP AI endpoint.
The native composer posts to `/unicom/webchat/send/`; it does **not** post to
`/api/ai/respond/`. Adding retrieval only to the latter leaves the actual UI
ungrounded. Do not patch or replace the shared chat component to work around it.

The hook receives persisted UniCom models, not a Django HTTP request. For a
signed-in WebChat message, `message.user_id` identifies the sender; validate the
request's account ownership and scope every document query to that identity.
Do not use a user ID supplied in message text or JSON as an authorization source.
Keep extracted text bounded, clearly labeled as untrusted source material, and
include citation identifiers. Retrieve current authorized data on each turn so
deleted documents stop appearing in newly supplied context. Test through the
visible composer, including a second account with different private documents.

### Product workflows

For an AI-assisted DMS, the main navigation should lead to Documents, Upload and
Assistant (and other requested real features). The first build must support:
upload a document, see it in the list, search, open its details, download the
original, ask a grounded question with a source reference, and delete it with
confirmation. Empty accounts must have a useful upload action. Failed uploads
and unsupported files need explicit messages. AI tools must scope retrieval to
the authenticated account; chat access alone does not authorize document access.

Verify at 1440×900 and 390×844, including open mobile menus, the chat composer,
long filenames, validation errors and the primary action without horizontal
scrolling. Check browser console/network failures, keyboard focus, back/forward,
direct URLs and refresh. Use the provided `scripts/browser_site_acceptance.py`
for the foundation and `scripts/browser_acceptance.py` for actual AI streaming,
attachments and history, then add the product-specific flow checks.
Run the foundation browser suite on a test instance with guest chat and signup
enabled; it exercises both forms and the composer. Keep production access
settings appropriate to the product, and test its authenticated flows separately.
