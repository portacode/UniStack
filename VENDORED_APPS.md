# Application provenance

UniCom and UniBot use the exact public versions deployed by
`meena-erian/unistack`, on `feature/opt-in-responses-api`:

- UniCom: `59b2c91a2c4005f96ecfb96b27f89db6fb081208` — Render each streamed word immediately.
- UniBot: `b2efe05853ca279668a858b17f5dca20c23969be` — Normalize multimodal content for Responses API.
- UniCRM: retained snapshot `4146d88a153c231bec0bd47445d5c467384626e2`.

Deployment recursively initializes the commits recorded by Git; it never follows
moving branch tips. Neither upstream submodule is patched.

The chat shell and source-defined bot follow `meena-erian/unistack`'s integration.
UniCom provides the conversation sidebar, Markdown, attachments, mobile composer,
and incremental text rendering. UniBot uses its Responses streaming API with the
upstream WebChatMessageStreamSink. UniStack adds project-level authentication,
CSRF protection, automatic channel setup, and the local client/model configuration.

## Upgrade from the previous pins

The previous pins were UniCom `3a9df4a` and UniBot `c0caf8b`, from
`fix/tool-batch-continuation`. That lineage includes automatic request retries and
email backfill functionality absent from the selected UI branches. The switch
does not retain those features, and its streaming API uses `event_sink` and
`responses_options` instead of `stream_event_sink` and `native_responses_tools`.
Review custom bot code using those old options before upgrading.

UniStack's compatibility migration retains existing retry columns and email
backfill tables and records, adding database defaults for the two non-null legacy
columns so new requests can be inserted by the selected upstream models. It does
not delete old data or reverse applied upstream migrations. The old migration
records remain in the database; fresh installs use the selected upstream schema.
Take a database backup before switching an existing deployment. The retained
legacy data is not exposed by these upstream app versions.

`data/definitions/bots/unistack.py` is synchronized during deployment. Other
stored custom bots are not overwritten unless their names also appear in the
source definitions directory. The default template uses the same streaming
configuration for new bots and non-streaming Responses for non-WebChat messages.
