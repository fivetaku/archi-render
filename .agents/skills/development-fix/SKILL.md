---
name: development-fix
description: "렌더의 일부 영역만 마스크로 수정, 창·문·재질·식생 부분 교체, 웹툴 마스크 반영, 수정 반복 요청에 사용합니다. '1층 창만 아치로', '이 부분만 고쳐', '마스크 그렸어 반영해줘', '지붕 색만 바꿔', '한 번 더 수정' 같은 요청에 대응합니다. 단, 샷 전체를 다시 뽑는 것은 $development-render, 수정 결과의 기하 점검은 $development-qa를 사용합니다."
---

# fix Workflow

Codex-compatible mirror of `.claude/commands/fix.md`.

Invoke explicitly with `$development-fix` followed by the workflow arguments.
Claude per-command tool controls are not enforced by this skill; Codex sandbox and approval settings remain separate.

# $development-fix

Standard. 기준 리비전(Rnn) 위에 마스크 영역만 재생성해 새 리비전을 만든다. 백엔드는 **grok만**(insane-router `/images/edits`, RGBA 알파 0 = 편집). gpt 경로는 마스크가 없다 (Fix Don't Regenerate).

> 주의: grok 출력은 1152×864(4:3) 고정이다. 16:9 기준 렌더(gpt R)를 고치면 새 리비전의 비율이 바뀌고 좌우가 잘려, "마스크 밖은 그대로"를 눈으로 대조하기 어렵다. 실행 전에 이 점을 한 줄 알리고, 결과를 기준 렌더와 같은 크기로 나란히 보여 준다.

## 사용법

```text
$development-fix <project> <shot> --base Rnn --mask <png> --instruction "..."
$development-fix <project> <shot> --base Rnn --web          # 웹툴에서 마스크 그리기
```

## 실행 흐름

### Step 1: 기준 리비전과 마스크 확보

- `--base`가 없으면 그 샷의 최신 리비전으로 진행하고, 어느 리비전을 기준으로 했는지 한 줄 알린다.
- 마스크가 없거나 `--web`이면 `python3 webtool/server.py`를 안내한다(http://127.0.0.1:8765 — 렌더 열기 → 브러시 → 저장). 웹툴이 저장하는 마스크는 기준 렌더와 **1:1 해상도**의 RGBA PNG(알파 0 = 편집)다.
- 사용자가 준 마스크가 흑백(흰=편집)이면 벤더 극성표(`20-knowledge/backends.md` § 마스크 극성)에 따라 RGBA 알파로 변환한 뒤 보낸다. 크기가 기준 렌더와 다르면 중단하고 다시 받는다.

### Step 2: 지시문 정리

- `--instruction`은 **무엇을 무엇으로**만 쓴다. 예: "Replace only the ground-floor windows with arched wooden-frame windows. Keep everything else unchanged."
- 팩의 재질 어휘(`OPTIONS.md`)를 재사용한다. "예쁘게" 같은 비특정 표현은 구체 재질·색으로 바꿔 묻는다.

### Step 3: 실행

```bash
python3 scripts/render.py fix --project <P> --shot <S> --base Rnn --mask <png> --instruction "..." --backend grok
```

- 산출물: `renders/<P>/<S>/R(nn+1)/{render.*, prompt.txt, meta.json}` — meta.json에 `base_revision`, `mask` 경로, `instruction`이 남는다.
- grok 임시 URL은 스크립트가 즉시 다운로드한다. 파일이 없으면 실패다.
- 소요 12~18초. 결과를 기준 리비전과 나란히 보여준다.

### Step 4: "gpt로 고쳐줘"를 요청받았을 때

gpt(pumasi `--ref`)에는 마스크 입력이 없음을 한 줄로 설명하고 두 갈래를 제시한다:

1. **(추천) grok으로 마스크 수정** — 영역 밖은 그대로.
2. **keep_fixed 재렌더** — `$development-render ... --backend gpt --option keep_fixed="<이미 승인된 요소 목록>"`로 이전 리비전을 `--ref`로 넘기고 "only change X" 꼬리를 붙여 전체를 다시 뽑는다. 영역 밖도 미세하게 흔들릴 수 있음을 고지한다. 라우터 키가 없는 PC(수강생 Codex 앱)에서는 1번이 불가하므로 이 갈래를 `$development-image` 렌더 모드로 수행한다(기준 렌더를 입력 이미지로, "only change X" 지시).

### Step 5: 다음

- `$development-qa <P> <S>`로 경보 확인. 마스크 밖이 바뀌었는지는 사람이 본다.
- 만족하면 `$development-approve`.

## 출력 형식

```markdown
# $development-fix 결과 — {project}/{shot}

기준: R02 → 새 리비전: R03 (grok, 15s)
마스크: renders/P01/S01_entrance/R03/mask.png (2560×1440, alpha0=edit, 팽창 12px/페더 6px)
지시: Replace only the ground-floor windows with arched wooden-frame windows. Keep everything else unchanged.
출력: renders/P01/S01_entrance/R03/render.jpg
usage: cost_in_usd_ticks 700000000 (실과금 0)

다음: $development-qa P01 S01_entrance → $development-approve P01 S01_entrance R03 internal
```

## 트리거 경계

should-trigger:

- "1층 창만 아치창으로 바꿔줘"
- "이 부분만 고쳐"
- "마스크 그렸어, 반영해줘"
- "지붕 색만 바꿔"
- "사람 지워줘" / "나무 추가해줘"(영역 지정 가능할 때)
- "한 번 더 수정" / "R03 기준으로 다시"
- "웹툴 열어줘"

NOT-trigger:

- "전체 다시 뽑아줘" / "팩 바꿔서 다시" → `$development-render`
- "기하 틀어졌는지 봐줘" → `$development-qa`
- "gpt로 고쳐줘" → 마스크 없음 설명 후 grok 또는 keep_fixed 재렌더(Step 4)
- "카메라 바꿔줘" → 캡처 단계 (SketchUp 재캡처 → `$development-intake`)

## 참조

- `scripts/render.py fix` (wp-a), `webtool/server.py` (wp-c)
- `20-knowledge/backends.md` — grok 마스크 규격·극성 변환·팽창/페더 기본값
- `20-knowledge/research/01_full_report.md` §3 — 마스크 규격 근거 (clm_022, 047, 048, 054)
