# Skills CLI

Skills CLI는 **외부 non-Rulesync Agent Asset**을 가져오거나 갱신할 때, Rulesync로 직접 관리하는 것보다 더 효율적인 경우에만 사용한다.

설치된 asset과 source 상태는 [`skills-lock.json`](../../skills-lock.json)과 Skills CLI가 소유한다. 이 문서에는 그 내용을 복제하지 않는다.

## Boundary

- Repository-owned Agent Asset은 Rulesync를 기본 canonical source로 유지한다.
- 외부 asset의 upstream source는 계속 authority이며, 설치된 copy를 별도 local source처럼 직접 수정하지 않는다.
- 장기적인 local modification이나 cross-harness projection이 필요하면 Skills CLI copy를 patch하기보다 Rulesync 또는 별도 canonical source로 전환하는 편을 우선 검토한다.
