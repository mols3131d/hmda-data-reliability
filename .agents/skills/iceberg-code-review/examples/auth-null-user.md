---
title: 'auth-null-user'
description: 'None 사용자 역참조로 로그인 API가 500을 반환한다.'
type: 'code-review-finding'
severity: 'bug'
status: 'open'
---

- Location: [`src/auth/login.py:42-43`](/src/auth/login.py#L42)

## Summary

`authenticate()`가 존재하지 않는 사용자를 역참조해 `500`을 반환한다. 기대 응답은 `401`이다.

## Observation

- `find_user(email)` 반환형: `User | None`
- `authenticate()`는 null guard 없이 `user.password_hash` 접근
- 미등록 이메일 입력 시 `AttributeError` 발생 후 `500` 반환

## Impact

- 누구나 미등록 이메일로 서버 오류 유발 가능
- 미등록 이메일은 `500`, 잘못된 비밀번호는 `401`이므로 계정 존재 여부 노출

## Recommendation

1. `user.password_hash` 접근 전에 `user is None` 검사.
2. 미등록 이메일과 잘못된 비밀번호에 동일한 `401` 응답 사용.
3. 미등록 이메일에도 dummy hash 검증을 수행해 timing 차이 축소.

## Verification

- [ ] 미등록 이메일: `401`, `AttributeError` 없음
- [ ] 잘못된 비밀번호: 동일한 status와 response body
- [ ] 올바른 인증 정보: 기존 성공 응답 유지
- [ ] 두 실패 경로: 동일한 hash 검증 단계 실행
