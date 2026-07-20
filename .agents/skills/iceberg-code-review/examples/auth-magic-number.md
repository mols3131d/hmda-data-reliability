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

**[Style] Hardcoded value**: Value `86400` is written directly in code.

- `86400` appears directly in `jwt.encode()` payload
- No comments explain the value

## Impact

**[Maintenance] Repeated magic number**: Hardcoded token duration requires multiple edits to change.

- Hard to read intent (1 day)
- Refactoring requires multiple file changes

## Recommendation

**[Extract] Constant definition**: Extract value to a named constant `TOKEN_EXPIRATION_SECONDS`.

- Place constant in `src/auth/constants.py`.
- Use constant in both production and test code.

## Verification

**[Verify] Code structure**: Verify the constant is defined and referenced in logic and tests.

- `TOKEN_EXPIRATION_SECONDS` used in `login.py`
- Test files updated to use the constant
