# External Source Contract v1 (Frozen)

**status: frozen (route=B import contract)**
**frozen_at: 2026-10-10T22:30:00+08:00**
**owner: main-agent**
**supersedes: experiments/source-bridge/fixtures/upstream-owner-excerpts.json (kept as derivation source)**
**applies_to: imported synthetic samples; live cross-App not yet verified end-to-end on RC2 host**

## Scope

This contract defines the minimal, frozen wire format that an external source (independent App, file import, or offline consumer) must produce so that DailyFlow adoption layer (`08_time_protocol.splash`) can verify, deduplicate, attach identity, and project without trusting payload-side `app_id` claims.

The contract does NOT assume live cross-App transport. It is the v1 stable specification that all evidence under `build/semifinal-202610/source-bridge/contracts-r2/` is bound to, and that `experiments/source-bridge/fixtures/probes/*.json` will be validated against.

## Identity

Every record carries:

```jsonc
{
  "source_app": "<string, must equal an allowed source identity>",
  "source_module": "<string, optional; module within source>",
  "source_record_id": "<string, stable across revisions>",
  "source_revision": <int, monotonically non-decreasing per record>,
  "deleted_at": "<ISO-8601 UTC, optional tombstone; mutually exclusive with content>",
  "content_hash": "<hex sha256 of canonical content body, hex 64 chars>"
}
```

Rules:

- `source_app` must be from the `allowed_source_apps` allow-list (configurable, default allows only `dailyflow` and explicitly provisioned synthetic identifiers such as `synthetic-climbing`, `synthetic-concert`).
- `source_record_id` is opaque to DailyFlow but **must be stable** across revisions of the same record.
- `source_revision` is required and must be ≥1.
- `content_hash` is the SHA-256 over the canonicalized content body. Equal `source_record_id` + `content_hash` is idempotent.
- `deleted_at` and a content body are mutually exclusive.

## Content envelope

```jsonc
{
  "kind": "<enum: expense | event_fact | event_plan | post | image | media_link>",
  "occurred_at": "<ISO-8601 Asia/Shanghai local, date-only YYYY-MM-DD or datetime>",
  "ended_at": "<optional; same shape; required for open-ended events>",
  "open_end": false,
  "title": "<≤80 chars>",
  "body": "<plain text>",
  "media": [
    { "kind": "image", "media_id": "<opaque>", "mime": "image/png", "size_bytes": <int>, "license": "<spdx or 'syn'>" }
  ],
  "tags": ["<user tag>"],
  "amount_minor": <int, minor units; -1 means absent; non-negative for kind=expense>,
  "currency": "<ISO-4217, 'CNY' default>",
  "source_meta": { "<free key: <string|int|bool>>" }
}
```

Rules:

- `kind=expense` requires non-negative `amount_minor` and sets `currency` if non-CNY.
- `kind=event_plan` may have open-ended duration (`open_end=true` and `ended_at` absent).
- `media` items are references (`media_id` looked up through a separate, host-mediated resource path; this v1 does NOT transfer bytes).
- `body` is plain text; no markdown, no HTML, no instructions.

## Wire envelope

```jsonc
{
  "contract_version": 1,
  "source_app": "...",
  "source_module": "...",
  "fetched_at": "<ISO-8601 UTC>",
  "snapshot_revision": <int>,
  "records": [/* envelope per record */],
  "tombstones": [/* envelope per record, deleted only */],
  "page": <int>,
  "page_size": <int>,
  "has_more": <bool>
}
```

Rules:

- A wire envelope is one page. `has_more=true` ⇒ caller can request next page with the same `snapshot_revision`.
- A `snapshot_revision` increase ⇒ re-fetch required; do NOT use cached envelopes from previous snapshot.
- Tombstones belong on a separate collection; do not embed inside `records`.

## Import endpoint behavior (DailyFlow adoption layer)

When imported into DailyFlow (route=B), the adoption layer MUST:

1. Reject any record whose `source_app` is not on the allow-list.
2. Reject any record whose `content_hash` cannot be recomputed (i.e., malformed).
3. Treat `source_record_id` + `source_revision` as the dedupe key.
4. Upsert only when `source_revision` strictly increases OR `content_hash` changes.
5. Mark records with `deleted_at` as tombstoned without overwriting prior content (history preserved).
6. NOT accept `amount_minor` rewritten or substituted by model output. Amounts are facts from source; model never produces them.
7. Emit a `source_meta.imported_at` field at ingest time (DailyFlow local).
8. Store `source_app` literally as imported; the existing `time_event_valid` rejecting non-`dailyflow` is **bypassed for this contract** under an explicit `--allow-external-sources` flag at the importer CLI; production `time_event_valid` continues to reject unmapped sources.

## Out of scope for v1

- Cross-App live authorization transport (route=A): unverified on RC2 live host; see `docs/SOURCE_BRIDGE_PROBE.md`.
- Image byte transfer: `media_id` is only an opaque reference; resource negotiation is host-mediated.
- Recurring events: not supported.
- Multi-currency aggregation: not implemented; UI shows each currency separately.
- Trust delegation: source identity cannot grant DailyFlow new abilities.

## Compatibility check

The `experiments/source-bridge/fixtures/probes/identity.json`, `probes/revision.json`, `probes/tombstone.json`, `probes/dedupe.json`, `probes/page.json` MUST round-trip through `tools/test_source_bridge_contract.py` (v1 contract) and produce the same SHA256 as the offline evidence at `build/semifinal-202610/source-bridge/contracts-r2/tests.log`.

If a future consumer needs change, create v2 (separate document), do NOT mutate this v1 file. The contract change log belongs in `execution-state.json` capability/contract versions.
