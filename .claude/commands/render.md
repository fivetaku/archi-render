---
description: "샷 전체 렌더 실행, 팩 적용 재렌더, 옵션 바꿔 다시 렌더, 백엔드 전환, 전체 샷 일괄 렌더 요청에 사용합니다. '렌더 돌려줘', 'S01 다시 렌더', '전부 골든아워로', '재질만 바꿔서 다시', 'grok으로 빨리 뽑아줘' 같은 요청에 대응합니다. 단, 마스크로 일부 영역만 고치는 것은 /fix, 새 팩이 필요하면 /stylepack, 캡처 인입은 /intake를 사용합니다."
---

# /render

Lite. 캡처 + 팩 + 옵션으로 프롬프트를 조립해 `scripts/render.py`로 전체 샷을 렌더하고 새 리비전(Rnn)을 만든다. 기본 백엔드는 **gpt**(pumasi `imagen.sh --ref`, 구독 — 한계비용 0)이다. grok은 사용자가 이름을 대고 요청할 때만 쓴다 — 출력이 1152×864(4:3)로 고정이라 16:9 캡처는 좌우가 잘린다. **이 PC에 pumasi가 없으면**(수강생 Codex 앱 — render.py가 `[렌더 불가]`로 끝남) `$development-image`의 렌더 모드(Codex 내장 이미지 도구)로 같은 리비전 기록을 남긴다.

## 사용법

```text
/render <project> <shot|all> --pack <id> [--option k=v ...] [--backend gpt|grok] [--aspect W:H]
```

## 실행 흐름

### Step 1: 입력 확인

- `assets/captures/<project>/manifest.json`이 없으면 `/intake`로 보낸다.
- `--pack`이 없으면 분위기를 번호 선택지로 묻는다(AGENTS.md "질문 방식" 예시: 1 흐린 날·추천 / 2 골든아워 / 3 저녁 시네마틱 / 4 한낮 콘크리트 / 5 항공 조감 / 6 직접 말하기, 샘플 그림 경로 함께). 존재하지 않는 팩 id면 중단.
- manifest에 해상도 WARN이 있는 샷은 "진행하되 저해상 캡처는 렌더 디테일이 떨어질 수 있다"고 한 줄 알린다. 차단하지 않는다.

### Step 2: 프롬프트 조립 (미리보기)

```bash
python3 scripts/prompt_compose.py --pack <id> [--option k=v ...] --print
```

- 결과를 보여주고, 사용자가 확정한 색·요소가 있으면 `--option keep_fixed="the columns white; the sign text Cafe"`로 넣는다. 기하 잠금 꼬리(geometry_lock)가 빠져 있으면 실패로 보고 팩을 점검한다.
- 프롬프트를 손으로 고쳐 쓰지 않는다. 바꿀 것은 옵션 또는 팩이다 (Pack Before Prompt).
- 문장 단위로 확인하려면 `--json`(lock/slots/keeps/tail). 슬롯은 7문장 캡 — 옵션을 아무리 많이 줘도 관련 축이 한 문장으로 합류하므로 넘치지 않는다.

**`--option` 어휘** (정본 `20-knowledge/stylepacks/OPTIONS.md`, 기계용 `python3 scripts/prompt_compose.py --list-options`). 우선권: 명시 옵션 > 팩 슬롯 > 프리셋 기본.

| 합류 문장 | 키 | 값 |
|---|---|---|
| shot | `mood` | photoreal · cinematic · clay · watercolor · diagram |
| | `camera` | eye_level · elevated · drone · interior |
| | `lens_mm` / `camera_height_m` / `tilt` | 정수 / 실수 / level · slight_up · slight_down (프리셋 필드만 덮어씀) |
| materials | `materials` | white_stucco_oak · board_formed_concrete · brick_dark_metal · timber_glass · clay_massing · 자유 리스트 |
| lighting | `lighting` | overcast · midday · golden_hour · dusk · night · blue_hour · dawn · morning_side · afternoon_backlit · night_signs_only · night_full |
| | `sky` | clear · scattered_cumulus · overcast · dramatic · haze (lighting·season의 하늘 절을 대체) |
| | `interior_lights` | off · partial · all_on |
| season | `season_weather` | spring · summer · autumn · winter · rain · snow · early_spring_blossom · monsoon_rain · late_autumn · heavy_snow · haze · fog |
| | `vegetation_age` | young · mature · lush |
| entourage | `entourage` | `people:on,cars:off,vegetation:on,furniture:on` |
| | `people_density` / `people_activity` | none · sparse · moderate · busy / walking · standing_talking · seated · mixed (people on일 때만) |
| | `car_density` / `car_type` | none · few · full / passenger · mixed_commercial · bicycles_only |
| context | `context` | as_drawn(기본, 암묵) · urban_dense · suburban · rural · waterfront · forest |
| | `material_wear` | new · lived_in · weathered |
| grading | `tone` | editorial_magazine · real_estate_ad · competition_panel · documentary |
| | `post` | neutral · teal_orange · warm_film · bw |
| 캡 밖 | `keep_fixed` / `references` / `aspect` | `;` 구분 문장 / 이미지 경로(gpt 경로에 추가 `--ref`) / 4:3 · 16:9 · 3:2 · 1:1 · 2:1 · auto |

### Step 3: 렌더 실행

```bash
python3 scripts/render.py --input assets/captures/<P>/<S>/capture.png --project <P> --shot <S> --pack <id> [--option k=v ...] [--backend gpt|grok] [--aspect W:H]
```

- `all`이면 manifest의 샷을 순차 실행한다(gpt는 1~2분/장 — 샷 수×2분을 미리 알린다).
- `--backend` 규칙: 기본 gpt. gpt 호출이 실패해도 grok으로 자동 재시도하지 않고 실패 원인(REASON 줄)을 보고한다(오너 결정 2026-10-11: 전체 렌더는 Codex/gpt). 사용자가 grok을 지명할 때만 `--backend grok`으로 돌리고, 4:3 고정 출력을 미리 알린다.
- `--aspect`를 생략하면 render.py가 캡처 비율에 가장 가까운 값을 쓴다(팩의 aspect_hint는 캡처 비율을 덮지 않는다). gpt 출력은 입력 비율을 근사하므로 정확한 픽셀 크기를 약속하지 않는다.
- grok 결과의 **임시 URL은 스크립트가 즉시 다운로드**한다. `renders/<P>/<S>/Rnn/render.*` 파일이 없으면 성공으로 보고하지 않는다.

### Step 4: 결과 확인과 기록

- 산출물: `renders/<P>/<S>/Rnn/{render.*, prompt.txt, meta.json}`. `renders/`는 .gitignore 대상 — 커밋하지 않는다.
- meta.json의 `backend`, `pack.id/version`, `usage`, `input_sha256`이 채워졌는지 확인한다.
- 다음: `/qa <P> <S>`(경보 확인) → 문제 영역은 `/fix`, 통과면 `/approve`.

## 출력 형식

```markdown
# /render 결과 — {project}/{shot}

| 샷 | 리비전 | 백엔드 | 팩 | 소요 | 출력 | usage |
|---|---|---|---|---|---|---|
| S01_entrance | R00 | gpt | overcast-photoreal@1.0.0 | 35s | renders/P01/S01_entrance/R00/render.png (1672×941, 16:9) | n/a (구독) |
| S02_side | R00 | grok (사용자 지정) | overcast-photoreal@1.0.0 | 16s | .../R00/render.jpg (1152×864, 4:3 고정) | cost_in_usd_ticks 700000000 (실과금 0) |

프롬프트: renders/P01/S01_entrance/R00/prompt.txt
다음: /qa P01 all → /fix 또는 /approve
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

- "창문만 아치로 바꿔줘" / "이 부분만 고쳐" → `/fix`
- "새 스타일 만들어줘" → `/stylepack new`
- "캡처 들여와줘" → `/intake`
- "기하가 맞는지 봐줘" → `/qa`
- "OpenAI 키로 직접 돌려" → 정책 금지 (`20-knowledge/backends.md`), 라우터·pumasi 경로만

## 참조

- `scripts/render.py`, `scripts/prompt_compose.py` (wp-a 담당)
- `20-knowledge/backends.md` — 백엔드 능력·라우팅 규칙·프롬프트 계약
- `20-knowledge/stylepacks/OPTIONS.md` — `--option` 어휘
- `20-knowledge/kb-link.md` — (예약) 프로젝트 카드에서 재질 읽기
