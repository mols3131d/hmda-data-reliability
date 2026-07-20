---
title: 'auth-legacy-support'
description: 'Legacy MD5 hashing fallback remains active.'
type: 'code-review-finding'
severity: 'q'
status: 'open'
---

- Location: [`src/auth/config.py:15`](/src/auth/config.py#L15)

## Summary

MD5 fallback is active but may be deprecated.

## Observation

**[Architecture] Active fallback**: MD5 fallback is still enabled despite modern standards.

- `ALLOW_LEGACY_MD5` is set to `True`
- MD5 is insecure for password hashing

## Impact

**[Security] Legacy vulnerability**: Insecure MD5 hashing pathway remains open to attackers.

- Maintains insecure code path
- Risk of downgrade attacks

## Recommendation

**[Confirm] Requirement status**: Verify if any active clients still require this MD5 fallback.

- If not, delete `ALLOW_LEGACY_MD5` and related logic.
- If yes, add `TODO` with removal date.

## Verification

**[Verify] Requirement decision**: Document decision and confirm removal path or client alignment.

- Product team confirms client requirements
- Unused code deleted if no longer needed
