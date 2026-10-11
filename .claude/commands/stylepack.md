---
description: "스타일팩 목록 조회, 팩 선택 추천, 새 팩 합성(custom-<slug>), 기존 팩 편집, 샘플 이미지 생성 요청에 사용합니다. '어떤 스타일 있어?', '노을 느낌으로 팩 만들어줘', '이 레퍼런스 사진 스타일로', '팩 재질 바꿔줘', '샘플 뽑아봐' 같은 요청에 대응합니다. 단, 팩을 골라 실제 렌더를 돌리는 것은 /render, 이미 렌더된 결과의 부분 수정은 /fix를 사용합니다."
---

# /stylepack

Standard. `assets/stylepacks/<id>/pack.yaml`을 조회·선택·합성·편집한다. 팩은 프롬프트보다 먼저다 (Pack Before Prompt) — 렌더마다 프롬프트를 손으로 쓰지 않고 팩 슬롯 + 옵션으로 조립한다.

## 사용법

```text
/stylepack list
/stylepack show <id>
/stylepack new <slug> [--from <base-id>] [--ref <image>] [--sample]
/stylepack edit <id> <field>=<value> ...
```

## 실행 흐름

### Step 1: 목록·선택 (`list`, `show`)

- `assets/stylepacks/*/pack.yaml|json`을 읽어 id·name·mood·lighting·용도 한 줄을 표로 보여준다. 기본 5팩: `overcast-photoreal`, `golden-hour`, `dusk-cinematic`, `midday-concrete`, `aerial-drone`.
- 사용자가 용도만 말하면("주거 외관, 차분하게") 가장 가까운 팩을 "(추천)"으로 첫 줄에 놓는다.
- `show <id>`는 슬롯 전체 + `scripts/prompt_compose.py --pack <id> --print` 결과를 함께 보여준다.

### Step 2: 새 팩 합성 (`new`) — 동적 팩 규칙

`20-knowledge/stylepacks/DYNAMIC_PACK.md`의 절차를 따른다:

1. **분석** — 사용자의 서술(또는 `--ref` 레퍼런스 이미지)을 6개 스타일 차원으로 분해한다: 조명·시간대 / 날씨·계절·식생 / 카메라 / 엔투라지 / 후처리 / 렌더 무드. 레퍼런스 이미지는 프롬프트 어휘로만 반영한다(백엔드에 스타일 이미지를 직접 첨부하지 않음 — gpt `--ref`는 소스 캡처 자리).
2. **가장 가까운 기본 팩 선택** — 5팩 중 6차원이 가장 많이 겹치는 것을 base로 잡는다(`--from`으로 강제 가능).
3. **`custom-<slug>` 합성** — base를 복사하고 달라진 슬롯만 덮어써 **전체 스키마를 채운다**(id·version·name·mood·slots 6~7개·negative·geometry_lock·backends·samples·changelog). 빈 필드를 남기지 않는다. 어휘는 `20-knowledge/stylepacks/OPTIONS.md`의 옵션 어휘만 쓴다.
4. **Specificity Gate** — 합성된 팩이 base와 최소 2개 차원에서 구체적으로 다른지, 슬롯 문구가 "nice", "beautiful" 같은 비특정 형용사 없이 재질·광원·렌즈 값을 담는지 확인한다. 통과 못 하면 사용자에게 어느 차원을 더 정할지 묻고, base 그대로 쓰기를 대안으로 제시한다.
5. 저장: `assets/stylepacks/custom-<slug>/pack.yaml` + `changelog` 초판 항목.

### Step 3: 샘플 생성 (`--sample` 또는 "샘플 뽑아봐")

- `pumasi:image`(Claude Code) 또는 `$development-image` 일반 그림 모드(Codex)로 팩 프롬프트(`prompt_compose.py --pack custom-<slug> --print`) 기반 무드 샘플 1장을 생성해 `assets/stylepacks/custom-<slug>/samples/s01.png`에 저장한다. 실제 캡처가 있으면 샘플 대신 `/render` 1샷을 권한다(샘플은 무드 확인용, 기하 검증 아님).
- `api.openai.com`·Google 키를 직접 호출하지 않는다.

### Step 4: 편집 (`edit`)

- `field=value`를 적용하고 `version`을 patch 올린 뒤 `changelog`에 한 줄 추가한다. 기본 5팩을 편집할 때는 먼저 `custom-<slug>`로 분기할지 묻는다(기본 팩은 공유 기준선).

## 출력 형식

```markdown
# /stylepack {subcommand}

| id | name | mood | lighting | 용도 |
|---|---|---|---|---|
| overcast-photoreal (추천) | 흐린 낮 사진사실 | photoreal | overcast | 주거·외관 기본 |
| ... |

(new일 때)
합성: custom-{slug} ← base {base-id}
달라진 차원: 조명(golden hour → dusk blue hour), 후처리(neutral → warm film)
Specificity Gate: pass
저장: assets/stylepacks/custom-{slug}/pack.yaml
다음: /render {project} {shot} --pack custom-{slug}
```

## 트리거 경계

should-trigger:

- "어떤 스타일 있어?" / "팩 목록"
- "이 프로젝트에 맞는 팩 추천해줘"
- "노을 느낌으로 팩 만들어줘"
- "이 레퍼런스 사진 스타일로 팩 만들어"
- "팩 재질을 벽돌로 바꿔줘"
- "샘플 이미지 뽑아봐"
- "팩 버전 올려줘"

NOT-trigger:

- "이 팩으로 렌더 돌려줘" → `/render`
- "창문만 바꿔줘" → `/fix`
- "옵션 어휘가 뭐 있어?" → `20-knowledge/stylepacks/OPTIONS.md` 안내
- "이미지 만들어줘"(팩 샘플이 아닌 일반 이미지) → Claude Code는 pumasi:image, Codex는 `$development-image`

## 참조

- `assets/stylepacks/<id>/pack.yaml` — 팩 정본 (wp-b 담당)
- `20-knowledge/stylepacks/DYNAMIC_PACK.md` — custom-<slug> 규칙
- `20-knowledge/stylepacks/OPTIONS.md` — 옵션 어휘
- `scripts/prompt_compose.py --pack <id> [--option k=v] --print`
- `20-knowledge/research/01_full_report.md` §4 — 6개 스타일 차원 근거
