## 기여의 형식 예시

아래 코드 블록은 형식만 보여준다. 설명은 실제 사례에 맞게 작성하고 관련된 근거 ID를 인용한다.
예시의 설명을 그대로 복사하지 않는다.

```json
[
  {
    "kind": "evidence_gap",
    "description": "검증 결과가 없습니다.",
    "evidence_refs": []
  },
  {
    "kind": "investigation_priority",
    "description": "원천 데이터의 완전성을 먼저 확인하세요.",
    "evidence_refs": [],
    "priority": "high"
  },
  {
    "kind": "remediation_critique",
    "description": "백필 전에 원인을 확인하세요.",
    "evidence_refs": []
  },
  {
    "kind": "material_uncertainty",
    "description": "원인은 확인되지 않았습니다.",
    "evidence_refs": []
  }
]
```

설명은 간결하게 쓴다. 코드 펜스는 예시 표시에만 사용하며 응답에는 붙이지 않는다.
