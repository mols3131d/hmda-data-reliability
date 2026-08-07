# Inbox Branch

`inbox` branch는 `inbox/`의 non-canonical artifact를 지속적으로 저장하기 위한 장기 유지 branch다.

일반 작업 branch의 변경 단위와 naming 규칙을 artifact마다 반복하지 않기 위한 제한된 예외다.

## Scope

`inbox` branch에서 일상적으로 변경할 수 있는 범위는 다음과 같다.

```text
inbox/YYYY-MM-DD/**
inbox/archive/**
```

다음 운영 자산은 `inbox` branch에서 임의로 변경하지 않는다.

```text
inbox/AGENTS.md
inbox/README.md
inbox/_guidelines/**
inbox/_templates/**
```

이 운영 자산은 일반 작업 branch와 Pull Request를 통해 `main`에서 관리한다.

## Rules

- `inbox`는 공유하는 장기 유지 branch이며 일반 `[<actor>/]<type>/<topic>` naming 규칙의 예외다.
- source code, tests, OpenSpec, canonical docs 또는 다른 project artifact를 변경하지 않는다.
- routine inbox artifact는 `inbox` branch에 저장하고 `main`으로 전달하기 위한 Pull Request를 만들지 않는다.
- `main`의 최신 운영 규칙이 필요하면 history를 rewrite하지 않고 `main`의 변경을 반영한다.
- `inbox` branch 전체를 `main`에 merge하지 않는다.

## Promotion

Inbox content가 채택되면 최신 `main`에서 일반 작업 branch를 만들고 필요한 결론이나 변경만 owning artifact에 다시 작성한다.

Inbox file이나 `inbox` branch 자체를 canonical artifact로 승격하지 않는다.
