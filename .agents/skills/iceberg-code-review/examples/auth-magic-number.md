---
title: 'auth-magic-number'
description: 'Hardcoded 86400 seconds used for token expiration.'
type: 'code-review-finding'
severity: 'nit'
status: 'open'
---

- Location: [`src/auth/login.py:82`](/src/auth/login.py#L82)

## Summary

Token expiration time is hardcoded as `86400`.

## Observation

- `86400` appears directly in `jwt.encode()` payload
- No comments explain the value
- Value is repeated in test files

## Impact

- Hard to read intent (1 day)
- Refactoring requires multiple file changes
- High risk of typos in future updates

## Recommendation

1. Extract `86400` to `TOKEN_EXPIRATION_SECONDS`.
2. Place constant in `src/auth/constants.py`.
3. Use constant in both production and test code.

## Verification

- [ ] `TOKEN_EXPIRATION_SECONDS` used in `login.py`
- [ ] Test files updated to use the constant
- [ ] Existing tests pass
