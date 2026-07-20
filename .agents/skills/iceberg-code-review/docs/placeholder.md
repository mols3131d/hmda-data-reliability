# Placeholder 규칙

Template에서 LLM이 작성할 값을 `{{이름}}`으로 표시한다.

## 문법

```text
{{이름}}
```

- 허용 문자: 영문, 한글, underscore(`_`)
- 이름은 한 글자 이상
- 공백, 숫자, 하이픈, 줄바꿈은 허용하지 않음

정규식:

```regex
{{[A-Za-z가-힣_]+}}
```

## 예시

인식:

```text
{{title}}
{{file_path}}
{{제목}}
{{리뷰_결과}}
```

제외:

```text
{{}}
{{ title }}
{{title-slug}}
{{123}}
`{{` ... `}}`
```

Parser는 Markdown 문맥을 해석하지 않는다. Inline code나 code block 안의 유효한 placeholder도 계산한다.

## 검사 함수

- `count_placeholders(path)`: 남은 placeholder 개수
- `has_no_placeholders(path)`: 개수가 0이면 `True`
