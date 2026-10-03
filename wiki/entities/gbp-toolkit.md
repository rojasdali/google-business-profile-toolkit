---
type: entity
title: GBP Toolkit
created: 2026-10-03
updated: 2026-10-03
aliases: [gbp-toolkit]
tags: [toolkit, gbp, google-business-profile, local-seo]
---

# GBP Toolkit

## Summary
The `google-business-profile-toolkit` is an agnostic, modular Python library and CLI for Google Business Profile automation, review monitoring, zero-repeat posting, and holiday hours.

## Key Facts
- Connects using OAuth2 refresh tokens against official Google My Business APIs.
- Strictly adheres to clean architecture: all modules < 120 lines and cyclomatic complexity <= 10.
- Implements safety guardrails including zero-repeat content hashing and NAP validation.

## Relationships
- [[gbp-client]] — API client managing endpoint requests and token refreshing
- [[zero-repeat-hashing]] — Content deduping and hashing engine
- [[nap-consistency]] — Name, address, and phone number audit model
- [[holiday-hours-automation]] — Special hour scheduling and holiday coverage
- [[gbp-cli]] — Command-line interface for local profile operations

## For AI
- **Type**: entity
- **Confidence**: high
- **Last verified**: 2026-10-03
