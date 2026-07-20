---
title: 'auth-timing-attack'
description: 'Early return on missing user creates timing side-channel.'
type: 'code-review-finding'
severity: 'risk'
status: 'open'
---

- Location: [`src/auth/login.py:65`](/src/auth/login.py#L65)

## Summary

Early return leaks account existence via timing difference.

## Observation

**[Performance] Early return timing**: Login execution ends early when user is missing, skipping password hash comparison.

- `find_user()` failure returns immediately
- Password hash check takes ~100ms

## Impact

**[Security] Account enumeration risk**: Attackers can enumerate users by measuring response times.

- Allows brute-force enumeration of registered accounts
- Elevates risk for targeted phishing

## Recommendation

**[Run] Dummy hash check**: Perform dummy hash calculation if `user is None` to match duration.

- Ensure both success and failure paths take identical time.
- Use constant-time string comparison for hashes.

## Verification

**[Verify] Timing equality**: Test and measure execution time differences between valid and invalid usernames.

- Missing user response time matches valid user
- Invalid password response time matches valid user
