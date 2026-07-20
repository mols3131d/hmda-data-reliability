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

**[Missing] Null guard**: Missing check for `None` user in `authenticate()`.

- `find_user(email)` returns `User | None`
- Unregistered email triggers `AttributeError`, causing `500`

## Impact

**[Security] Attribute error leaks user**: Dereference of `None` causes internal error instead of proper authorization failure.

- Unregistered email can trigger server error
- Unregistered email returns `500`, wrong password returns `401`. Exposes user existence.

## Recommendation

**[Add] Null check**: Add check `user is None` before credentials access.

- Return `401` for unregistered email.
- Perform dummy hash check for unregistered email to prevent timing attack.

## Verification

**[Run] Authentication test**: Verify response codes and times for registered/unregistered logins.

- Unregistered email: `401`, no `AttributeError`
- Correct credentials: Authenticates successfully
