---
type: concept
title: Zero Repeat Hashing
created: 2026-10-03
updated: 2026-10-03
aliases: [zero-repeat-hashing]
tags: [dedup, hashing, posts]
---

# Zero Repeat Hashing

## Summary
The policy and algorithmic mechanism preventing repetitive marketing posts on Google Business Profiles by maintaining SHA-256 hash histories of published copy and media.

## Key Facts
- Hashes combined summary text, CTA URL, and media source bytes.
- Prevents algorithmic down-ranking or spam penalties caused by identical repeated updates.
- Rejects new posts if their semantic or binary hash matches the recent 90-day history.

## Relationships
- [[gbp-toolkit]] — Core publication guardrail
- [[gbp-cli]] — Verified during `gbp posts create`

## For AI
- **Type**: concept
- **Confidence**: high
- **Last verified**: 2026-10-03
