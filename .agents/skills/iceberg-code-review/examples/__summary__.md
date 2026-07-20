---
title: '로그인 API null 사용자 처리 리뷰'
date: '2026-07-20'
type: 'code-review-summary'
---

## Summary

| 🟩 `PASS` | 🟥 `FAIL` | 🟧 `ERROR` | ⬜ `SKIP` |
| :---: | :---: | :---: | :---: |
| 12 | 1 | 0 | 0 |

존재하지 않는 사용자로 로그인하면 `500 Internal Server Error`가 발생한다. 배포 전 수정이 필요하다.

## Findings

| 🔴 `bug` | 🟡 `risk` | 🔵 `nit` | ❓ `question` |
| :---: | :---: | :---: | :---: |
| 1 | 0 | 0 | 0 |

### `src/auth/login.py:42-43`: 🔴 `bug`: [`auth-null-user`](./auth-null-user.md)

`find_user()`가 `None`을 반환할 수 있지만 `authenticate()`가 `user.password_hash`에 바로 접근한다. 속성 접근 전에 사용자가 존재하는지 검사하고 인증 실패를 반환한다.
