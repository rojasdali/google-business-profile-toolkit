---
type: system
title: GBP CLI
created: 2026-10-03
updated: 2026-10-03
aliases: [gbp-cli]
tags: [cli, tools, gbp]
---

# GBP CLI

## Summary
The unified command-line entrypoint (`gbp`) providing zero-scratch operational commands for location discovery, post publishing, review management, special hours, and performance metrics.

## Key Facts
- Subcommands include: `status`, `locations`, `posts`, `reviews`, `hours`, `performance`, and `audit`.
- Supports both rich terminal output and machine-readable `--json` formatting.
- Replaces throwaway scratch scripts for Google Business Profile operational adjustments.

## Relationships
- [[gbp-toolkit]] — Command dispatch and CLI interface
- [[gbp-client]] — Connects to Google My Business API
- [[zero-repeat-hashing]] — Enforced on post creation
- [[nap-consistency]] — Audited via `gbp audit`
- [[holiday-hours-automation]] — Configured via `gbp hours`

## For AI
- **Type**: system
- **Confidence**: high
- **Last verified**: 2026-10-03
