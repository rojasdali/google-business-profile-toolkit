---
type: entity
title: GBP Client
created: 2026-10-03
updated: 2026-10-03
aliases: [gbp-client]
tags: [api, client, oauth]
---

# GBP Client

## Summary
The primary HTTP client wrapping Google Business Profile REST APIs across `mybusinessaccountmanagement`, `mybusinessbusinessinformation`, and `mybusiness` endpoints.

## Key Facts
- Manages automatic OAuth2 token refreshes and expired session recovery.
- Serializes API responses into structured domain dataclasses.
- Handles pagination and quota management across multi-location accounts.

## Relationships
- [[gbp-toolkit]] — Core communication layer
- [[gbp-cli]] — Instantiated by CLI subcommands

## For AI
- **Type**: entity
- **Confidence**: high
- **Last verified**: 2026-10-03
