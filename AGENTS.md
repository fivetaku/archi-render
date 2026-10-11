# archi-render — Archi Render Director

## 처음 오신 분께 — 이 폴더는 무엇인가요

> "이 폴더는 뭐 하는 곳이야?" 같은 질문에는 아래 내용을 개발 용어 없이 쉬운 한국어로 답한다.

- SketchUp에서 뽑은 클레이 캡처를 AI 렌더 시안으로 바꾸는 건축 렌더 작업 공간입니다.
- 렌더 하나는 일곱 단계로 나갑니다: 인입 → 스타일 고르기 → 렌더 → 검수 → 수정 → 승인 → 납품. 단계 이름을 몰라도 한글로 시키면 됩니다.
- 캡처의 층수, 창 위치, 지붕 같은 형태는 바꾸지 않고 재질과 빛만 입힙니다. 고칠 부분은 웹 도구에서 브러시로 칠해 그곳만 고칩니다.
- 시안은 `renders/` 아래 R00, R01 … 으로 쌓이고, 어떤 스타일로 무엇을 고쳤는지가 함께 기록됩니다.
- 수강생 PC에서도 Codex에 들어 있는 이미지 도구로 렌더할 수 있습니다(`$development-image`). 칠한 곳만 고치는 마스크 수정은 렌더 키가 있는 강사 PC에서 합니다. 흐름만 볼 때는 `scripts/render.py ... --dry-run` 또는 `python3 webtool/server.py --stub`을 씁니다.

## 질문 방식 (Codex에는 선택 카드가 없다)

결정이 필요하면 채팅에 **번호 선택지**로 묻는다. 사용자는 숫자만 답하면 된다.

```text
질문: 어떤 분위기로 렌더할까요? (숫자로 답해 주세요)
1. 흐린 날 사진 같은 느낌 — 부드러운 빛, 그림자 약함 (처음이면 추천)
2. 해 질 녘 골든아워 — 따뜻한 주황빛, 긴 그림자
3. 저녁 시네마틱 — 실내등 켜짐, 하늘은 남색
4. 한낮 콘크리트 — 선명한 그림자, 재질 강조
5. 직접 말하기
```

- 렌더 분위기·수정 내용처럼 **설계자의 취향이 걸린 선택은 사용자만 줄 수 있는 입력**으로 본다. 요청에 없으면 기본값으로 진행하지 말고 묻는다.
- 묻는 응답에서는 작업을 시작하지 않고 질문만 보낸 뒤 멈춘다. 답을 받은 다음에 진행한다.
- 한 번에 1개, 많아도 2개까지만 묻는다. 요청에 이미 답이 있으면 묻지 않는다.
- 선택지는 2~5개 + "직접 말하기". 처음이면 추천 1개를 표시한다.
- 비교 그림이 있으면 경로를 같이 보여 준다(예: `assets/stylepacks/<팩>/samples/sample-01.png`).
- 사용자가 "알아서"·"아무거나"라고 하면 추천 선택지로 진행하고, 무엇을 골랐는지 한 줄로 알린다.

## 말로 설명하기 어려운 수정

"여기를 좀 이렇게"처럼 말로 짚기 어려운 수정은 아래 셋 중 하나를 권한다.

1. **웹 도구에서 칠하기** — `python3 webtool/server.py` → http://127.0.0.1:8765 → 렌더 열기 → Fix 모드 → 브러시로 고칠 곳만 칠하고 한 줄 지시. 칠한 곳만 바뀐다(강사 PC, 라우터 키 필요).
2. **표시한 그림 첨부** — 렌더를 미리보기 앱 등에서 열어 고칠 곳에 동그라미·화살표를 그리고 저장해 Codex 채팅에 첨부한다. "빨간 동그라미 친 곳만 바꿔 줘"라고 쓰면, 표시는 위치를 알려 주는 용도로만 쓰고 원본 렌더를 기준으로 다시 만든다(`$development-image`).
3. **참고 사진 첨부** — 원하는 재질·분위기 사진을 첨부하고 "이 사진의 외벽 느낌으로"라고 쓴다.

말로 할 때는 자주 쓰는 수정 종류를 번호로 보여 주고 고르게 한다: 1 재질 바꾸기 · 2 창·문 모양 · 3 색 · 4 나무·사람·차 넣거나 빼기 · 5 하늘·시간대 · 6 직접 말하기.

> SketchUp 클레이 캡처를 스타일팩 기반 AI 렌더로 바꾸고, 마스크 영역 수정·기하 QA 경보·리비전 승인·납품까지 지휘하는 렌더 디렉터 워크스페이스입니다 (development/automation subtype).

**target runtime**: Codex (AGENTS.md 기준). 정본 instruction surface는 `CLAUDE.md`.

---

## 운영 규칙 (포인터)

- 이 워크스페이스의 정체성·원칙·워크플로우·커맨드·품질 규칙은 **`CLAUDE.md` 전문을 그대로 적용**한다.
  Codex는 이 파일을 읽은 뒤 반드시 `CLAUDE.md`를 읽고 따른다.
- 규칙 수정은 `CLAUDE.md`에만 한다. 이 파일에는 규칙을 추가하지 않는다 (두 surface 간 drift 방지).
- `CLAUDE.md`의 Claude Code 전용 표현은 Codex 등가물로 읽는다:
  `.claude/commands/{name}.md` 커맨드 → `.agents/skills/` repo skill,
  `Task 위임`/`.claude/agents/*.md` → `.codex/agents/*.toml`.
- 이미지 생성(렌더·팩 샘플·일반 그림)은 Codex에서 `$development-image`(Codex 내장 이미지 도구)를 쓴다. 묻지 않고 기본값으로 진행한다. `api.openai.com` 직접 호출 금지는 Codex에서도 동일하다.

## Codex 등가물 (커맨드 → 스킬)

| CLAUDE.md 커맨드 | Codex 호출 | 스킬 정본 |
|---|---|---|
| `/intake` | `$development-intake <project> [<folder>]` | `.agents/skills/development-intake/SKILL.md` |
| `/stylepack` | `$development-stylepack list\|show\|new\|edit` | `.agents/skills/development-stylepack/SKILL.md` |
| `/render` | `$development-render <P> <S\|all> --pack <id> ...` | `.agents/skills/development-render/SKILL.md` |
| `/fix` | `$development-fix <P> <S> --base Rnn --mask <png> --instruction "..."` | `.agents/skills/development-fix/SKILL.md` |
| `/qa` | `$development-qa <P> <S\|all>` | `.agents/skills/development-qa/SKILL.md` |
| `/approve` | `$development-approve <P> <S> Rnn <stage>` | `.agents/skills/development-approve/SKILL.md` |
| `/deliver` | `$development-deliver <P>` | `.agents/skills/development-deliver/SKILL.md` |
| (Claude는 pumasi:image) | `$development-image <P> <S>` 또는 "이미지 만들어줘" | `.agents/skills/development-image/SKILL.md` |
| `/wrap` | `$development-wrap` | `.agents/skills/development-wrap/SKILL.md` |
| `/specify` `/design` `/implement` `/test` `/review` | `$development-specify` 등 | `.agents/skills/development-{specify,design,implement,test,review}/SKILL.md` |

## Codex Runtime Notes

- Command-style workflows are mirrored as repo skills under `.agents/skills/`.
- Invoke a mirrored `/command` as `$<archetype>-<command> <arguments>` using its SKILL.md name; Claude argument macros are not native Codex substitutions.
- Skill agents/openai.yaml controls implicit invocation only; Claude per-command tool controls are not equivalent to Codex sandbox or approval settings.
- Project-local Codex settings live in `.codex/config.toml`.
- Runtime-ready custom agents live in `.codex/agents/*.toml` and are registered in `.codex/config.toml`.
- The stable spawn tool does not inject a registered role automatically; delegation messages must require the child to read its role TOML first.
- Project hooks live in `.codex/hooks.json` and run only after project hook trust approval.
