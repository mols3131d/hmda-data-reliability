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

- `find_user()` failure returns immediately
- Password hash check takes ~100ms
- Attackers can enumerate users by response time

## Impact

- Allows brute-force enumeration of registered accounts
- Elevates risk for targeted phishing

## Recommendation

1. Perform dummy hash calculation if `user is None`.
2. Ensure both success and failure paths take identical time.
3. Use constant-time string comparison for hashes.

## Verification

- [ ] Missing user response time matches valid user
- [ ] Invalid password response time matches valid user
- [ ] Unit tests verify constant-time execution
