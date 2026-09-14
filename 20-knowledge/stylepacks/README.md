# 스타일팩 (Style Packs) — 구성 규칙

> 스타일팩은 "한 장의 렌더가 어떻게 보여야 하는가"를 슬롯 단위로 고정한 재사용 프리셋이다.
> 정본 위치: `assets/stylepacks/<id>/pack.yaml` (+ 동일 내용 `pack.json` 미러). 스키마는 설계 문서 §7
> (`20-knowledge/research/…02_workspace_design_inputs.md`)을 따르고, 모든 팩은 2026-09-14 실도면 트라이얼에서
> 실제로 통과한 프롬프트를 distill한 것이다.

## 1. 팩 한 개의 구조

| 필드 | 뜻 | 비고 |
|---|---|---|
| `id` / `version` / `name` | 케밥케이스 id, semver, 한국어 이름 | `custom-<slug>`는 합성 팩 (DYNAMIC_PACK.md) |
| `mood` | photoreal \| cinematic \| clay \| watercolor \| diagram | OPTIONS.md의 mood 어휘와 동일 |
| `slots.shot_type` | 샷 종류 + "THIS building" 고정 어구 | 1문장 |
| `slots.materials[]` | 재질 목록 — 팩 기본값이며 샷마다 가장 자주 덮어쓰는 슬롯 | 항목당 명사구 |
| `slots.camera` | `{lens_mm, height, perspective}` | perspective는 항상 "straight vertical uprights" 계열 |
| `slots.lighting` | 방향 + 고도 + 색온도 + 그림자 성질 | 1문장, 속성 3개 이상 |
| `slots.season_weather` | 계절 + 하늘 + 지면 상태 | 1문장 |
| `slots.entourage[]` | 허용 엔투라지 **만** 열거 ("no cars" 같은 금지도 여기) | 사람·차·식생·가구 |
| `slots.post` | 그레이딩·화이트밸런스·비네팅 | 1문장 |
| `negative` | "Avoid:" 꼬리에 들어가는 금지 목록 | 기하 변조·HDR 헤일로·틸트시프트·텍스트 |
| `geometry_lock` | 팩별 **추가** 잠금 (지붕·개구부 수·간판 텍스트) | 공통 잠금은 `prompts/geometry_lock.txt` |
| `keep_fixed[]` | 색·요소 고정 지시 ("the canopies white") | 기본 빈 배열, 샷 옵션이 채움 |
| `references[]` | `refs/` 아래 레퍼런스 이미지 경로 | 빈 배열 허용 |
| `backends` | `gpt-image {path: "pumasi --ref", aspect_hint}`, `grok-imagine-image-2.0 {endpoint: /images/edits, mask_polarity: alpha0_edit}` | 전체 샷 = gpt, 영역 수정 = grok |
| `samples[]` | `samples/sample-01.png` — 이 팩으로 실제 나온 결과 | 팩 카드 미리보기 |
| `changelog[]` | `{date, note}` 누적 | 합성 팩은 첫 줄에 "synthesized" 명시 |

## 2. 프롬프트 합성 순서 (10부)

`scripts/prompt_compose.py`가 아래 순서로 한 문단을 만든다. 순서는 트라이얼에서 검증된 것이므로 바꾸지 않는다.

```
 1. source lock      prompts/geometry_lock.txt 전문 + 팩 geometry_lock (추가 잠금)
 2. mood / shot      "Produce a {mood words} architectural render of this exact scene, {shot_type}." + Camera
 3. materials        "Materials: a, b, c."
 4. lighting         "Lighting: …"
 5. season           "Season and weather: …"
 6. entourage        "Entourage: …"  ← 팩·옵션이 허용한 항목만. 허용 목록 밖은 버린다
 7. post             "Post-processing: …"
 8. keep_fixed       "Keep the canopies white." (항목마다 1문장)
 9. Avoid            "Avoid: {negative}."
10. aspect           "Aspect ratio 4:3."
```

- **슬롯 캡**: 2~7번을 합쳐 **7문장 이하**. 넘치면 뒤에서부터 잘린다 → 재질 목록을 늘리지 말고 항목을 고른다.
- 1·8·9·10은 캡 밖이다 (잠금과 금지는 절대 잘리지 않는다).
- 실측 근거: 트라이얼 7장 모두 이 골격(lock → 재질 → 조명 → 엔투라지 → 렌즈 → 비율)으로 기하 보존이 우수했다
  (`20-knowledge/trials/` 참조). gpt-image 경로는 마스크가 없으므로 "only change X" 지시를 keep_fixed로 넣어 근사한다.

## 3. 6가지 스타일 차원

팩을 비교·검색할 때 쓰는 축. 새 팩은 이 6축에서 기존 팩과 최소 2축 이상 달라야 존재 의미가 있다.

| 축 | 값 예 | 대응 슬롯 |
|---|---|---|
| 1. 시각 (shot / camera) | eye_level 35mm · elevated 24mm · drone 45° | `shot_type`, `camera` |
| 2. 재질 팔레트 | white_stucco_oak · board_formed_concrete | `materials` |
| 3. 광원 | overcast · midday · golden_hour · dusk · night · blue_hour | `lighting` |
| 4. 계절·기상 | late spring dry · after rain puddles · snow | `season_weather` |
| 5. 엔투라지 밀도 | none · sparse(2 people) · populated · cars in bays | `entourage` |
| 6. 후처리 룩 | neutral · teal_orange · warm_film · bw | `post`, `mood` |

기본 5팩의 좌표:

| 팩 | 시각 | 재질 | 광원 | 계절 | 엔투라지 | 후처리 |
|---|---|---|---|---|---|---|
| overcast-photoreal | eye 35 | stucco/oak/black steel | overcast | late spring | 2 people, no cars | neutral |
| golden-hour | eye 35 | stucco/oak/black steel | golden hour, sun left 10° | late summer clear | 2 people, no cars | gentle warm |
| dusk-cinematic | elevated 24 | board-formed concrete, wet asphalt | dusk, sun below horizon | autumn after rain | people as drawn | teal-orange |
| midday-concrete | elevated 24 | board-formed concrete, asphalt | zenith 5500K | early summer clear | people as drawn | neutral HDR |
| aerial-drone | drone 24, 45-60° | roofs/paving/lawn/asphalt | late afternoon 25° | late spring clear | cars in bays only | neutral, white bg kept |

## 4. Specificity Gate (슬롯 값 검문)

모든 슬롯 값은 "렌더러가 그대로 실행할 수 있는가"로 검문한다. 통과 못 하면 팩에 넣지 않는다.

| 거부 (generic) | 승인 (concrete) |
|---|---|
| "professional lighting", "beautiful light" | "warm low sun from camera-left at 10° elevation, 3200K, long soft-edged shadows" |
| "high quality", "8k", "masterpiece" | (삭제 — 백엔드 기술 파라미터가 담당) |
| "modern materials" | "board-formed concrete with visible plank grain and tie holes" |
| "vibrant sunset" | "sky graded deep blue #1B2A49 at zenith to burnt orange #E8742A at horizon" |
| "some people" | "two seated people on the balcony in muted clothing" |
| "nice background" | "plain white background kept as in the source" |

검문 기준: lighting은 방향·경도(hard/soft)·색온도 3속성 이상, materials는 재질명 + 표면 상태(grain/weathering/finish), entourage는 개수 + 위치, post는 화이트밸런스 또는 그레이딩 이름 + 비네팅 여부.

## 5. 아키비즈 클리셰 금지

| 금지어 | 대체 |
|---|---|
| "tilt-shift", "miniature look" | "straight vertical uprights, no keystoning" (perspective) / "no tilt-shift miniature blur" (negative) |
| "vibrant", "dramatic colors" | 구체 팔레트 (hex 2개 이상 또는 색온도) |
| "add some context buildings" | 금지. `negative`에 "extra buildings" 고정 |
| "HDR look" | "high dynamic range with no clipped highlights, no halos at horizon" |
| "lens flare", "god rays" | 기본 금지. 사용자가 명시 요청할 때만 옵션으로 |
| "photorealistic 8k render" | mood 어휘 "photorealistic architectural photograph" 한 번만 |
| 유리에 "reflections everywhere" | "glass storefront with sky reflections and visible interior" |

## 6. 옵션 → 슬롯 덮어쓰기 규칙

웹툴 옵션 패널과 `/render --option k=v`는 같은 어휘(OPTIONS.md)를 쓰고, 다음 규칙으로 팩 슬롯을 덮어쓴다.

1. **옵션 값이 있으면 슬롯을 통째로 교체**한다 (병합하지 않는다). 예: `lighting=golden_hour`는 팩의 lighting 문장을 OPTIONS.md의 golden_hour 문장으로 바꾼다.
2. `materials`·`entourage`는 리스트 교체. 프리셋 이름(`board_formed_concrete`)이면 OPTIONS.md의 리스트로 펼친 뒤 교체.
3. `entourage` 토글은 허용 목록이다. 토글이 꺼진 항목은 "no cars"처럼 **부정형으로 슬롯에 남긴다** (모델이 임의로 추가하는 것을 막는 효과가 트라이얼에서 확인됨).
4. `keep_fixed`는 옵션이 있으면 옵션만, 없으면 팩 기본값. `;`로 여러 항목.
5. `aspect`는 옵션 > 팩 `backends.gpt-image.aspect_hint` > 입력 이미지 비율 순으로 결정.
6. `mood`를 `clay`/`watercolor`/`diagram`으로 바꾸면 `materials`와 `post`는 OPTIONS.md의 해당 mood 기본 문장으로 함께 바뀐다 (사진 재질 문장을 클레이 무드에 남기면 모순).
7. 옵션 조합이 기존 팩 어느 것과도 3축 이상 다르면 팩을 덮어쓰지 말고 **DYNAMIC_PACK.md 절차로 `custom-<slug>`를 합성**한다.
8. 덮어쓴 결과는 렌더 사이드카 `meta.json`에 `pack_id`, `pack_version`, `options`로 기록되어 재현 가능해야 한다.

## 7. 파일 규율

- `pack.yaml`과 `pack.json`은 항상 같은 내용. 편집은 yaml에서 하고 미러는
  `python3 -c "import yaml,json,sys;json.dump(yaml.safe_load(open(sys.argv[1])),open(sys.argv[1][:-5]+'.json','w'),ensure_ascii=False,indent=2)" assets/stylepacks/<id>/pack.yaml`.
- 슬롯을 바꾸면 `version` patch 올리고 `changelog`에 한 줄. 무드·광원 축이 바뀌면 minor.
- `samples/`는 이 팩으로 실제 렌더된 결과만 (합성 이미지·타 팩 결과 금지). `refs/`는 사용자 레퍼런스.
- 렌더 산출물(`renders/`)은 git 밖. 팩·refs·samples는 git 추적.
