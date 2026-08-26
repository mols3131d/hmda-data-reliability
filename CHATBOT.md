# Harness Compatibility

Root `CHATBOT.md`는 chatbot harness에서 누락되는 repository context와 Agent Asset loading을 보정한다. Repository state와 GitHub object를 읽거나 변경할 때는 GitHub plugin으로 live state를 확인한다.

`Always` 항목을 먼저 읽고, 이후 현재 GitHub 작업에 해당하는 항목만 추가로 읽는다.

| When | References | Purpose |
| --- | --- | --- |
| Always | [`AGENTS.md`](AGENTS.md), [`.agents/route/ROUTE.md`](.agents/route/ROUTE.md) | repository guidance와 Agent Asset routing |
| Git/GitHub task | [`docs/development/vcs-git/README.md`](docs/development/vcs-git/README.md) | Git/GitHub workflow entry |
| Branch | [`branch.md`](docs/development/vcs-git/branch.md) | branch 생성·운영 기준 |
| Commit | [`commit.md`](docs/development/vcs-git/commit.md), [`.gitmessage`](.gitmessage) | commit 기준과 message format |
| Pull Request | [`pull-request.md`](docs/development/vcs-git/pull-request.md), [`pull-request.md` template](.github/templates/pull-request.md) | Pull Request workflow와 description format |
| Pull Request review | [`pull-request-review.md`](docs/development/vcs-git/pull-request-review.md), [`pull-request-review.md` template](.github/templates/pull-request-review.md) | review 기준과 body format |
| Template metadata | [`.github/templates/README.md`](.github/templates/README.md) | template 공통 규칙과 optional metadata |
