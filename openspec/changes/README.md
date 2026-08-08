# OpenSpec Changes

`openspec/changes/`는 진행 중인 OpenSpec Change와 완료된 archive를 저장한다.

## 이름 규칙

Change ID는 다음 형식을 사용한다.

```text
<domain>[-<subdomain>][-<capability>]-<short-title>[-<extensions>]
```

- domain을 첫 segment로 두어 관련 Change가 함께 정렬되게 한다.
- subdomain과 capability는 분류에 필요할 때만 사용한다.
- short-title은 이번 Change의 구체적인 의도나 결과를 짧게 표현한다.
- extensions는 추가 구분이 필요할 때만 사용한다.
- lowercase kebab-case를 사용한다.

예시:

```text
hmda-data-ingestion-add-parquet-support
reliability-incident-detection-reduce-core-scope
orchestration-pipeline-simplify-runtime
```

## 범위

Change는 하나의 검토 가능한 변경 목적을 가진다. 여러 domain에 영향을 주더라도 변경의 주된 결과를 소유하는 domain을 기준으로 이름을 정한다.

Spec과 공통된 작성 규칙은 [`../config.yaml`](../config.yaml)을 따른다.
