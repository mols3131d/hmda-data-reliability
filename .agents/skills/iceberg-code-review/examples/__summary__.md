---
title: 'Login API null user handling review'
date: '2026-07-20'
type: 'code-review-summary'
---

## Summary

| 🟩 `PASS` | 🟥 `FAIL` | 🟧 `ERROR` | ⬜ `SKIP` |
| :---: | :---: | :---: | :---: |
| 12 | 1 | 0 | 0 |

Login with non-existent user causes `500 Internal Server Error`. Must fix before deploy.

## Findings

| 🔴 `bug` | 🟡 `risk` | 🔵 `nit` | ❓ `question` |
| :---: | :---: | :---: | :---: |
| 1 | 1 | 1 | 1 |

---

### 🔴 [`auth-null-user`](./auth-null-user.md)

[`src/auth/login.py:42-43`](./auth-null-user.md)

- **Missing null guard**: `authenticate()` accesses `user.password_hash` without null guard.

  ---> **Add check**: Check `user is None`, return auth failure.

---

### 🟡 [`auth-timing-attack`](./auth-timing-attack.md)

[`src/auth/login.py:65`](./auth-timing-attack.md)

- **Vulnerable timing**: Early return on missing user leaks account existence.

  ---> **Equalize time**: Run dummy hash check for missing users.

---

### 🔵 [`auth-magic-number`](./auth-magic-number.md)

[`src/auth/login.py:82`](./auth-magic-number.md)

- **Magic number**: `86400` used directly for token expiration.

  ---> **Extract constant**: Define `TOKEN_EXPIRATION_SECONDS = 86400`.

---

### ❓ [`auth-legacy-support`](./auth-legacy-support.md)

[`src/auth/config.py:15`](./auth-legacy-support.md)

- **Unclear intent**: Legacy MD5 fallback remains active.

  ---> **Confirm requirement**: Is this still needed for v1 clients?

---
