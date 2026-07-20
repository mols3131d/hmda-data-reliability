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
| 1 | 0 | 0 | 0 |

### `src/auth/login.py:42-43`: 🔴 `bug`: [`auth-null-user`](./auth-null-user.md)

`find_user()` returns `None`. `authenticate()` directly accesses `user.password_hash`. Need null check before property access to return auth failure.
