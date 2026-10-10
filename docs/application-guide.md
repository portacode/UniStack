# Build on the provided application shell

The starter has an overview, assistant, branded sign-in/out, responsive site
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

## Add a product page

1. Add a view in your application and a normal URL, e.g. `/documents/`.
2. Extend `core/base.html`, supply `page_title` in the view context, and put
   content inside `{% block content %}`. Add the route to `SITE_NAVIGATION`.
3. Use `data-nav` on internal links that can use enhanced navigation. Leave
   login, logout, downloads, external URLs and links needing a full reload alone.
4. Optional JavaScript goes in a separate ES module, referenced with
   `{% block main_attributes %}data-page-module="{% static 'myapp/documents.js' %}"{% endblock %}`.
   Export `mount(main)` and scope selectors to `main`. Return a cleanup function.
   Scripts inside page content are intentionally not evaluated on navigation.
5. Use the shared `.button.primary`, `.button.secondary`, `.button.quiet`,
   `.page-content`, and brand variables. Add feature styles to a stylesheet
   loaded by the base template; page-local head blocks are only loaded on a
   full page visit. Do not require navigation to inject scripts/styles.

Use normal Django forms with CSRF protection, meaningful validation, empty
states and success/error feedback. Paginate data on the server; lazy page
modules are not a substitute for paginating large lists. Render image assets
with dimensions and `loading="lazy"` when below the fold.

## First-build acceptance

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
