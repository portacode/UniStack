# UniStack

Start your own Django project with a polished AI chat, messaging, and CRM.
The demo includes streamed Markdown replies, conversation history, image
attachments, a mobile composer, and per-conversation AI usage.

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
