# Daily — agent handoff

## Current authorization and scope

The user explicitly confirmed the product spelling **Daily** on 2026-10-01, superseding the original Daliy name. The local directory remains Daliy. It is a calendar-centered personal life-recording app with diary, bookkeeping and menstrual-record modules. Conversational bookkeeping is a key entry point. The user confirmed: automatically save clear facts, ask about ambiguous ones.

Initialization and product planning are complete. The latest instruction authorizes summarizing, evaluating and optimizing the idea and creating a product plan. Do not implement UI, accounting, categorization, AI calls, or storage until the user explicitly asks to start development. Proposed defaults in the plan are not confirmed requirements.

Read README.md, BRIEF.md and docs/PRODUCT_PLAN.md first. Communicate with the user in Chinese. Update these records and the workspace's ../agent.md after meaningful authorized progress.

## Environment context

- Local project: D:\Life\AgenticApp\Daliy.
- For verified Windows setup and commands, read ../agent.md if available. That workspace record includes the existing Makepad Windows rendering patch; preserve it.
- ../my-notes is a separate reference demo, not this product's implementation.
- Planned app ID: daily, following the user's README correction. No manifest or program has been generated yet.
- bundle/.gitkeep is only a directory placeholder; remove it when assembling a real app bundle. It is not a valid submission asset.
- There is no runnable Daily application or verified application test. Signing, publisher identity and publishing have not been established in this work.
- At the start of this planning turn, main tracked origin/main and HEAD was cf40e03 (fix:拼写错误), with a clean working tree. Preserve the user's committed spelling correction. This turn adds documentation only; no commit or push was requested.

## When development is authorized later

Use documented APIs and recheck current upstream sources. The local Design Flow AI document lags newer upstream facts: OctoSense PR #95 merged model.complete on 2026-09-28. That is a candidate for structured extraction, but the local standalone card-host has not been verified to provide it. See the product plan's sourced capability section. Do not confuse one-shot model calls, system assistant access, and the still-planned full per-app Agent lifecycle. Verify the actual Windows host and permissions before selecting the integration.

Only the actual bundle is submitted to App Hub. Keep local data, credentials, build output and review material outside the bundle and Git. Preserve user data and sibling repositories; do not reset the runtime to discard the local Windows fix.
