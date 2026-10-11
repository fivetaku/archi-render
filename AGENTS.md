# archi-render — Archi Render Director

## 처음 오신 분께 — 이 폴더는 무엇인가요

> "이 폴더는 뭐 하는 곳이야?" 같은 질문에는 아래 내용을 개발 용어 없이 쉬운 한국어로 답한다.

- SketchUp에서 뽑은 클레이 캡처를 AI 렌더 시안으로 바꾸는 건축 렌더 작업 공간입니다.
- 렌더 하나는 일곱 단계로 나갑니다: 인입 → 스타일 고르기 → 렌더 → 검수 → 수정 → 승인 → 납품. 단계 이름을 몰라도 한글로 시키면 됩니다.
- 캡처의 층수, 창 위치, 지붕 같은 형태는 바꾸지 않고 재질과 빛만 입힙니다. 고칠 부분은 웹 도구에서 브러시로 칠해 그곳만 고칩니다.
- 시안은 `renders/` 아래 R00, R01 … 으로 쌓이고, 어떤 스타일로 무엇을 고쳤는지가 함께 기록됩니다.
- 수강생 PC에서도 Codex에 들어 있는 이미지 도구로 렌더할 수 있습니다(`$development-image`). 칠한 곳만 고치는 마스크 수정은 렌더 키가 있는 강사 PC에서 합니다. 흐름만 볼 때는 `scripts/render.py ... --dry-run` 또는 `python3 webtool/server.py --stub`을 씁니다.

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
