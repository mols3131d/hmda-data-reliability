---
title: 'auth-legacy-support'
description: 'Legacy MD5 hashing fallback remains active.'
type: 'code-review-finding'
severity: 'question'
status: 'open'
---

- Location: [`src/auth/config.py:15`](/src/auth/config.py#L15)

## Summary

MD5 fallback is active but may be deprecated.

## Observation

- `ALLOW_LEGACY_MD5` is set to `True`
- V1 API sunset occurred last month
- MD5 is insecure for password hashing

## Impact

- Maintains insecure code path
- Increases maintenance surface
- Risk of downgrade attacks

## Recommendation

1. Confirm if V1 clients still require this fallback.
2. If not, delete `ALLOW_LEGACY_MD5` and related logic.
3. If yes, add `TODO` with removal date.

## Verification

- [ ] Product team confirms client requirements
- [ ] Unused code deleted if no longer needed
- [ ] Removal tracked in issue tracker if deferred
