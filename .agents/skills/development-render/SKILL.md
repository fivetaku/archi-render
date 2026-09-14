---
name: development-render
description: "샷 전체 렌더 실행, 팩 적용 재렌더, 옵션 바꿔 다시 렌더, 백엔드 전환, 전체 샷 일괄 렌더 요청에 사용합니다. '렌더 돌려줘', 'S01 다시 렌더', '전부 골든아워로', '재질만 바꿔서 다시', 'grok으로 빨리 뽑아줘' 같은 요청에 대응합니다. 단, 마스크로 일부 영역만 고치는 것은 $development-fix, 새 팩이 필요하면 $development-stylepack, 캡처 인입은 $development-intake를 사용합니다."
---

# render Workflow

Codex-compatible mirror of `.claude/commands/render.md`.

Invoke explicitly with `$development-render` followed by the workflow arguments.
Claude per-command tool controls are not enforced by this skill; Codex sandbox and approval settings remain separate.

# $development-render

Lite. 캡처 + 팩 + 옵션으로 프롬프트를 조립해 `scripts/render.py`로 전체 샷을 렌더하고 새 리비전(Rnn)을 만든다. 기본 백엔드는 **gpt**(pumasi `imagen.sh --ref`), 폴백은 **grok**(insane-router). 비용은 두 경로 모두 0.

## 사용법

```text
$development-render <project> <shot|all> --pack <id> [--option k=v ...] [--backend gpt|grok] [--aspect W:H]
```

## 실행 흐름

### Step 1: 입력 확인

- `assets/captures/<project>/manifest.json`이 없으면 `$development-intake`로 보낸다.
- `--pack`이 없으면 `$development-stylepack list`를 짧게 보여주고 하나를 고르게 한다. 존재하지 않는 팩 id면 중단.
- manifest에 해상도 WARN이 있는 샷은 "진행하되 grok 폴백 시 1024급"이라고 한 줄 알린다. 차단하지 않는다.

### Step 2: 프롬프트 조립 (미리보기)

```bash
python3 scripts/prompt_compose.py --pack <id> [--option k=v ...] --print
```

- 결과를 보여주고, 사용자가 확정한 색·요소가 있으면 `--option`으로 넣는다(예 `--option fixed_colors="columns white"`). 기하 잠금 꼬리(geometry_lock)가 빠져 있으면 실패로 보고 팩을 점검한다.
- 프롬프트를 손으로 고쳐 쓰지 않는다. 바꿀 것은 옵션 또는 팩이다 (Pack Before Prompt).

### Step 3: 렌더 실행

```bash
python3 scripts/render.py --input assets/captures/<P>/<S>/capture.png --project <P> --shot <S> --pack <id> [--option k=v ...] [--backend gpt|grok] [--aspect W:H]
```

- `all`이면 manifest의 샷을 순차 실행한다(gpt는 1~2분/장 — 샷 수×2분을 미리 알린다).
- `--backend` 규칙: 기본 gpt. 사용자가 속도를 우선하거나 gpt 호출이 실패하면 `--backend grok`으로 재시도하고 meta.json에 폴백 사유를 남긴다.
- `--aspect`는 manifest의 비율을 기본으로 넘긴다. gpt 출력은 입력 비율을 근사하므로 정확한 픽셀 크기를 약속하지 않는다.
- grok 결과의 **임시 URL은 스크립트가 즉시 다운로드**한다. `renders/<P>/<S>/Rnn/render.*` 파일이 없으면 성공으로 보고하지 않는다.

### Step 4: 결과 확인과 기록

- 산출물: `renders/<P>/<S>/Rnn/{render.*, prompt.txt, meta.json}`. `renders/`는 .gitignore 대상 — 커밋하지 않는다.
- meta.json의 `backend`, `pack.id/version`, `usage`, `input_sha256`이 채워졌는지 확인한다.
- 다음: `$development-qa <P> <S>`(경보 확인) → 문제 영역은 `$development-fix`, 통과면 `$development-approve`.

## 출력 형식

```markdown
# $development-render 결과 — {project}/{shot}

| 샷 | 리비전 | 백엔드 | 팩 | 소요 | 출력 | usage |
|---|---|---|---|---|---|---|
| S01_entrance | R00 | gpt | overcast-photoreal@1.0.0 | 1m42s | renders/P01/S01_entrance/R00/render.png (1448×1086) | n/a (구독) |
| S02_side | R00 | grok (폴백: gpt timeout) | overcast-photoreal@1.0.0 | 16s | .../R00/render.jpg (1024×768) | cost_in_usd_ticks 700000000 (실과금 0) |

프롬프트: renders/P01/S01_entrance/R00/prompt.txt
다음: $development-qa P01 all → $development-fix 또는 $development-approve
```

## 트리거 경계

should-trigger:

- "렌더 돌려줘" / "S01 렌더"
- "전부 다시 렌더해줘"
- "골든아워 팩으로 바꿔서 다시"
- "재질 옵션만 바꿔서 재렌더"
- "grok으로 빨리 뽑아줘"
- "16:9로 뽑아줘"
- "이어서 나머지 샷 렌더"

NOT-trigger:

- "창문만 아치로 바꿔줘" / "이 부분만 고쳐" → `$development-fix`
- "새 스타일 만들어줘" → `$development-stylepack new`
- "캡처 들여와줘" → `$development-intake`
- "기하가 맞는지 봐줘" → `$development-qa`
- "OpenAI 키로 직접 돌려" → 정책 금지 (`20-knowledge/backends.md`), 라우터·pumasi 경로만

## 참조

- `scripts/render.py`, `scripts/prompt_compose.py` (wp-a 담당)
- `20-knowledge/backends.md` — 백엔드 능력·라우팅 규칙·프롬프트 계약
- `20-knowledge/stylepacks/OPTIONS.md` — `--option` 어휘
- `20-knowledge/kb-link.md` — (예약) 프로젝트 카드에서 재질 읽기
