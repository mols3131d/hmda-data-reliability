---
title: 'auth-null-user'
description: 'None user dereference causes 500 error in login API.'
type: 'code-review-finding'
severity: 'bug'
status: 'open'
---

- Location: [`src/auth/login.py:42-43`](/src/auth/login.py#L42)

## Summary

`authenticate()` dereferences missing user, returns `500`. Expected `401`.

## Observation

- `find_user(email)` returns `User | None`
- `authenticate()` accesses `user.password_hash` without null guard
- Unregistered email triggers `AttributeError`, causing `500`

## Impact

- Unregistered email can trigger server error
- Unregistered email returns `500`, wrong password returns `401`. Exposes user existence.

## Recommendation

1. Check `user is None` before accessing `user.password_hash`.
2. Return `401` for both unregistered email and wrong password.
3. Perform dummy hash check for unregistered email to prevent timing attack.

## Verification

- [ ] Unregistered email: `401`, no `AttributeError`
- [ ] Wrong password: Same status and response body
- [ ] Correct credentials: Authenticates successfully
- [ ] Both failures: Similar timing
