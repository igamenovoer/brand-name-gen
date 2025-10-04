# Roadmap

This document tracks what’s complete and what’s next for the Brand Name Gen project.

## Checklist

Completed
- [x] Scaffold repo, context directory, and AGENTS.md
- [x] Initialize PyPI-style package (src layout), MkDocs docs, and CI
- [x] Configure cross‑platform metadata and Pixi tasks (lint/typecheck/test/docs)
- [x] Implement domain availability (.com via RDAP)
  - [x] API: `brand_name_gen.domain_check`, service `domain_checker`
  - [x] CLI: `brand-name-gen-cli check-www` (JSON + human)
- [x] Implement Android app title “uniqueness” checks
  - [x] API: `brand_name_gen.title_check` (AppFollow + Play), service `title_checker`
  - [x] CLI: `brand-name-gen-cli check-android appfollow|playstore`
- [x] Add hints/tasks for RDAP, AppFollow, and title checks under `context/`

Next
- [ ] Integrate DataForSEO Google SERP API for exact‑match ranking validation
  - [ ] Add optional dependency group for `dataforseo-client`; env config
  - [ ] Implement sync API `google_rank.py` (Pydantic models + requests/SDK)
  - [ ] Add CLI: `brand-name-gen-cli check-google-rank` (JSON + human)
  - [ ] Add Pixi task, examples, and docs section “Google Ranking Checks”
  - [ ] Unit tests with mocked SDK responses; no live calls in CI
  - [ ] Optional: aggregate AppFollow/Play/Google signals into a single report

Notes
- DataForSEO is paid; keep disabled by default, require env creds.
- Ranking is locale-sensitive; accept location/language/device parameters.
- Prefer exact‑phrase matching with optional relaxed rules (normalize/hyphen/space).

Acceptance Criteria
- [ ] API returns structured rankings with `top_position` and `top_hit_matches` per rules
- [ ] CLI prints JSON and human output; non‑zero exit on auth/HTTP errors
- [ ] mypy passes and tests green; docs updated with minimal examples
