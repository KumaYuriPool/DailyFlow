# DailyFlow agent handoff

## Latest delivered state — 2026-10-03 (takes precedence over historical sections)

Version 0.3.0 keeps the single Splash app and the user's no-Shell/Rust-change boundary. User authorized parallel agents and completing the record-to-Flow product loop. Read `docs/AGENT_FLOW_ACCEPTANCE.md` first, then current `USER_GUIDE.md` and the 0.3.0 additive section of `DATA_PROTOCOL.md`.

Actual full-desktop `model.complete` testing made 3 real Provider requests: cat food CNY45 created the pet-care Flow; duplicate send did not add a record; ambiguous cat litter triggered clarification; CNY26 follow-up reused the Flow, totaling CNY71. Evidence: `build/agent-flow-r1/real-model2/report.json` and `cleanup.json`. Provider profile unchanged. This is app-internal model-to-business execution, NOT verified Shell Agent tool calling. The old Shell binary lacks the new script-tool bridge; no test kernel is configured. Keep these boundaries explicit.

Business tests use real bridge-enabled card-host tool calls (32); conversation state-machine tests inject model outputs (12 integration assertions + 1 restart), and must be described separately from real Provider testing. Shared `business_save` handles validation, optimistic revision checks, source/Flow/receipt atomic candidate persistence, historical v1 compatibility and private query filtering. Splash treats `ok` as a keyword: use quoted object keys and `result["ok"]`. Do not bypass business tools by writing state files directly.

Automatic request receipts are capped at 128 and never evicted; new automatic writes then fail while manual create/edit remains possible. Conversation drafts do not survive restart. Restoring an old backup rolls receipts back, so do not blindly replay unknown requests made after the backup. Two data roots remain independent: `run-dailyflow-ai.cmd` uses complete desktop plus existing Provider and `.local-state/desktop/`; old `run-dailyflow.cmd`/`.ps1` uses card-host without model service and `.local-state/dailyflow/`. No automatic migration or real-data tests.

For reproducible business regression, use `python -X utf8 tools/test_business_flow.py --bundle bundle --output build/<new-directory> --binary ../OctoSense-App-Hub/target/release/card-host.exe`. Output must be new; the script copies the bundle before stamping and closes only its own processes. Preserve source data, historical evidence, existing Hub Cargo.lock and Windows runtime patch. Do not commit, push or publish without authorization.


## Current authorization and scope

On 2026-10-02 the user explicitly requested renaming the product, local directories, app IDs and references to **DailyFlow**. The local repository is now `D:\Life\AgenticApp\DailyFlow`; the former document repository and app directory have been consolidated here. See `docs/RENAMING.md` for the mapping and verification.

The latest product direction is a calendar-led time Flow system with a common event protocol, business module entry points, cards, reminders and Agent operations. Read `docs/PRODUCT_VISION_ROADMAP.md`, `docs/HANDOFF.md`, `README.md` and `BRIEF.md`. Communicate with the user in Chinese.

The user's latest instruction on 2026-10-02 explicitly authorizes developing and running the single-app time Flow validation MVP in a new development chat. This supersedes earlier planning-only restrictions. Read `docs/IMPLEMENTATION_HANDOFF.md` for scope and actual acceptance criteria. Evolve `bundle/` (ID `dailyflow`) into the unified app, preserving prior code/data and the four reference apps. Implementation, necessary fixes and testing are authorized; committing, pushing and publishing are not requested. Preserve existing changes and user data.

## Project and environment

- Hard constraint confirmed by the user on 2026-10-02: implement DailyFlow only as an OctoScript/Splash script app. Do not extend or modify the Shell, host services, runtime or other Rust layers to implement product features. Existing exposed and granted host APIs may be used after verification. Missing APIs are platform dependencies, not authorization to add native services or background helpers. Preserve the pre-existing Windows rendering patch without expanding it.
- Keep the event protocol and module interfaces in the app layer. A Shell-level time service is outside the current scope. If a feature cannot be delivered through script and existing APIs, narrow or defer it and explain the limitation.

- Four current bundles live under `apps/dailyflow-{calendar,expense,diary,period}/bundle/`. The calendar is a prototype; the other three are placeholders.
- The historical single bundle lives in `bundle/` with ID `dailyflow`. Its previous data namespace has been renamed to `.local-state/dailyflow/` without changing record contents.
- App-specific data uses `apps/<app>/.local-state/<app>/`. Do not put local data, build output, logs or credentials into bundles or Git.
- Read `../agent.md` for Windows setup and actual verification. Preserve the local Makepad Windows rendering patch and the existing App Hub Cargo.lock changes. Do not reset runtime repositories.
- `../my-notes` is a separate reference demo.
- Gate checks do not prove visual quality, complete functionality or publication. Preserve historical evidence; do not rewrite old logs or screenshots to claim new tests.

## Future development

The unified implementation is now `bundle/main.splash` version 0.2.0. Read `docs/MVP_ACCEPTANCE_REPORT.md`, `docs/DATA_PROTOCOL.md` and `docs/USER_GUIDE.md` before extending it. Use isolated `--app-data` for tests. The app catches storage/validation errors and prevents timers writing before successful loading; preserve these protections. Real model calls in the tested Windows card-host returned no service. Do not claim AI, AppCard/glance, closed-app wakeups or seven-day use as completed.

Verify model, AppCard, glance, app-tool routing and background scheduling separately in the installed Windows host. Newer local OctoSense source contains capabilities absent from older documentation, but source inspection is not runtime verification. Keep the user's rule: automatically save clear facts and ask about ambiguous ones.

Update project documentation and `../agent.md` after meaningful progress. Signing, publisher identity and publishing remain separate work. The remote repository must only be changed to a new URL after its existence and rename have been verified.
