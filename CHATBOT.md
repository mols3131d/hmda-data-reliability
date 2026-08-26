# Harness Compatibility

Root `CHATBOT.md`는 chatbot harness에서 누락되는 repository context와 Agent Asset loading을 보정한다. Repository state와 GitHub object를 읽거나 변경할 때는 GitHub plugin을 기본 interface로 사용하고 live state를 확인한다.

`Always` 항목을 먼저 읽고, 이후 현재 GitHub 작업에 해당하는 항목만 추가로 읽는다.

| When | Document | Purpose |
| --- | --- | --- |
| Always | [`AGENTS.md`](AGENTS.md) | repository guidance와 required project context |
| Always | [`.agents/route/ROUTE.md`](.agents/route/ROUTE.md) | Agent Asset routing |
| Git/GitHub task | [`docs/development/vcs-git/README.md`](docs/development/vcs-git/README.md) | branch, commit, Pull Request와 review workflow entry |
| Commit | [`.gitmessage`](.gitmessage) | commit message format |
| GitHub template | [`.github/templates/README.md`](.github/templates/README.md) | template 공통 규칙과 metadata |
| Pull Request | [`.github/templates/pull-request.md`](.github/templates/pull-request.md) | Pull Request description format |
| Pull Request review | [`.github/templates/pull-request-review.md`](.github/templates/pull-request-review.md) | Pull Request review format |
