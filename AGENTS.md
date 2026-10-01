# DailyFlow agent handoff

## Current authorization and scope

On 2026-10-02 the user explicitly requested renaming the product, local directories, app IDs and references to **DailyFlow**. The local repository is now `D:\Life\AgenticApp\DailyFlow`; the former document repository and app directory have been consolidated here. See `docs/RENAMING.md` for the mapping and verification.

The latest product direction is a calendar-led time Flow system with a common event protocol, business module entry points, cards, reminders and Agent operations. Read `docs/PRODUCT_VISION_ROADMAP.md`, `docs/HANDOFF.md`, `README.md` and `BRIEF.md`. Communicate with the user in Chinese.

The rename is authorized; it does not authorize implementing the roadmap, merging the four apps into one functional app, publishing, committing or pushing. A single-app protocol validation is proposed, not implemented. Preserve existing changes and user data.

## Project and environment

- Four current bundles live under `apps/dailyflow-{calendar,expense,diary,period}/bundle/`. The calendar is a prototype; the other three are placeholders.
- The historical single bundle lives in `bundle/` with ID `dailyflow`. Its previous data namespace has been renamed to `.local-state/dailyflow/` without changing record contents.
- App-specific data uses `apps/<app>/.local-state/<app>/`. Do not put local data, build output, logs or credentials into bundles or Git.
- Read `../agent.md` for Windows setup and actual verification. Preserve the local Makepad Windows rendering patch and the existing App Hub Cargo.lock changes. Do not reset runtime repositories.
- `../my-notes` is a separate reference demo.
- Gate checks do not prove visual quality, complete functionality or publication. Preserve historical evidence; do not rewrite old logs or screenshots to claim new tests.

## Future development

Verify model, AppCard, glance, app-tool routing and background scheduling separately in the installed Windows host. Newer local OctoSense source contains capabilities absent from older documentation, but source inspection is not runtime verification. Keep the user's rule: automatically save clear facts and ask about ambiguous ones.

Update project documentation and `../agent.md` after meaningful progress. Signing, publisher identity and publishing remain separate work. The remote repository must only be changed to a new URL after its existence and rename have been verified.
