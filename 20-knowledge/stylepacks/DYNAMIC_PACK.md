# 동적 팩 합성 (Dynamic Pack) — 맞는 팩이 없을 때

> 기본 5팩(overcast-photoreal · golden-hour · dusk-cinematic · midday-concrete · aerial-drone)이 요청을 덮지 못하면
> 슬롯을 즉석 편집하지 말고 **같은 스키마의 `custom-<slug>` 팩을 합성해 저장**한다. 이유: 즉석 편집은 사이드카에
> 남지 않아 재현이 안 되고, 두 번째 요청에서 같은 룩을 다시 못 만든다.

## 1. 언제 합성하는가

`/render`나 웹툴 옵션이 들어왔을 때 다음 중 하나면 합성 경로로 간다.

- 요청이 README §3의 6축 중 **3축 이상**에서 가장 가까운 기본 팩과 다르다 (예: 야간 + 눈 + 상업가로 = 광원·계절·엔투라지 3축).
- `mood`가 clay / watercolor / diagram 등 사진 계열이 아니다 (기본 5팩은 모두 photoreal/cinematic).
- 사용자가 레퍼런스 이미지를 첨부하며 "이 느낌으로"라고 했고 그 느낌이 기존 팩 이름으로 설명되지 않는다.

1~2축만 다르면 합성하지 않고 옵션 덮어쓰기(README §6)로 처리한다.

## 2. 절차 (5단계)

```
① 분석   요청문·첨부 레퍼런스에서 6축 값을 뽑는다. 빠진 축은 묻지 말고 §4 디폴트로 채우고 "가정:"으로 선언.
② 정규화 뽑은 값을 OPTIONS.md 어휘로 매핑한다 ("해질녘" → dusk, "비 온 뒤" → rain, "사람 많이" → people on).
③ 최근접 기본 팩 선택   6축 일치 수가 가장 많은 팩을 base로 잡는다 (동률이면 광원 축이 같은 쪽).
④ 합성   base 팩을 복사해 달라진 축의 슬롯을 OPTIONS.md 문장으로 바꾸고, 축에 없는 요청(예: 눈 쌓인 캐노피)은
         Specificity Gate를 통과하는 문장으로 직접 쓴다. 모든 필드를 채운다 — 비워두는 필드는 keep_fixed·references만 허용.
⑤ 저장   assets/stylepacks/custom-<slug>/pack.yaml + pack.json (동일 내용), samples/는 첫 렌더 성공 후 채움.
         changelog 첫 줄: {date, note: "synthesized from <base-id> for <request 요약>"}.
```

slug 규칙: 영문 소문자·하이픈, 광원-계절-대상 순 (예: `custom-night-snow-retail-street`). 20자 넘으면 대상을 줄인다.

## 3. 합성 시 반드시 지키는 것

### Specificity Gate (README §4와 동일 기준)
- lighting: 방향 + 경도 + 색온도 3속성. "야경 조명" → "sodium-free 3000K LED storefront light spilling 4 m onto snow, sky #0B1526 with no stars, no moon".
- materials: 재질명 + 표면 상태. "벽돌" → "dark clinker brick with recessed grey mortar joints, dry".
- entourage: 개수 + 위치. "사람들" → "six pedestrians in winter coats on the far sidewalk, none in front of the entrance".
- post: 그레이딩 이름 + 화이트밸런스 + 비네팅 여부.

### 아키비즈 클리셰 변환표
| 요청·초안에 등장하면 | 이렇게 바꾼다 |
|---|---|
| tilt-shift, 미니어처 느낌 | perspective "straight vertical uprights, no keystoning" + negative "tilt-shift miniature blur" |
| vibrant, 화려한 색 | 구체 팔레트: hex 2개 이상 또는 색온도 (예: "#E8742A / #1B2A49") |
| 주변에 건물 좀 채워서 | 거부. negative "extra buildings" 유지. 배경은 "neighbouring buildings kept exactly as drawn" |
| 떠 있는·추가된 볼륨, 층 추가 | 거부. lock 문장이 이미 금지 — 요청자에게 SketchUp에서 모델을 고쳐 재캡처 안내 |
| 8k, masterpiece, ultra detailed | 삭제 |
| dramatic HDR | "high dynamic range with no clipped highlights, no halos at horizon" |
| lens flare, god rays, 렌즈 플레어 | 기본 negative에 둔다. 사용자가 명시 요청할 때만 lighting 문장 끝에 1구절 |
| 눈·비를 "atmospheric" 으로만 | 적설 두께·표면 위치·젖음 상태를 쓴다 ("3 cm fresh snow on horizontal surfaces only, wet dark asphalt where ploughed") |

### 금지
- 기본 팩 파일을 직접 고쳐서 임시 룩을 만들지 않는다 (기본 팩의 version/changelog는 승격 절차로만 바뀐다).
- `custom-` 팩에 `samples/`를 다른 팩 결과나 레퍼런스 이미지로 채우지 않는다.

## 4. 빠진 축의 디폴트

| 축 | 디폴트 |
|---|---|
| camera | 입력 캡처의 시점 유지 (eye_level 35mm 가정) |
| season_weather | 광원이 night/dusk면 clear dry; 그 외 late spring dry |
| entourage | people on(sparse 2), cars off, vegetation on, furniture as drawn |
| post | neutral (cinematic mood일 때만 teal_orange) |
| aspect | 입력 이미지 비율 |

## 5. 승격 (custom → named pack)

`custom-<slug>`는 **서로 다른 샷에서 2회** 렌더가 승인(approve 단계 internal 이상)되면 이름 있는 팩으로 승격한다.

1. `custom-` 접두어를 떼고 6축이 드러나는 id로 바꾼다 (`night-snow-retail`).
2. `version: 1.0.0`, `changelog`에 "promoted from custom-<slug> after 2 approved renders (<shot ids>)" 추가.
3. 첫 승인 렌더를 `samples/sample-01.png`로 복사.
4. README §3 좌표표에 행 추가. 옛 `custom-` 디렉토리는 `90-archive/stylepacks/`로 이동.

1회만 쓰이고 30일 지난 `custom-` 팩은 wrap 시 아카이브 후보로 보고한다.

## 6. 작업 예시 — "야간 눈 내리는 상업가로"

**요청**: "이 가로 상가 캡처를 야간, 눈 오는 날 분위기로. 간판 불 켜지고 사람 좀 있게."

① 분석 → 광원 night, 계절 snow(winter), 엔투라지 people on / cars 미언급, 재질 미언급(캡처 재질 유지), 후처리 미언급, 카메라 eye level.
② 정규화 → lighting=night, season_weather=snow, entourage=people on, cars off(디폴트), post=neutral(디폴트).
③ 최근접 → 광원이 어두운 쪽인 `dusk-cinematic`과 2축(카메라·후처리) 차이, 나머지 4축 다름 → 3축 이상이므로 합성. base = dusk-cinematic (광원 축이 가장 가깝다).
④ 합성 결과 `assets/stylepacks/custom-night-snow-retail/pack.yaml`:

```yaml
id: custom-night-snow-retail
version: 0.1.0
name: 야간 · 적설 · 상업가로 (합성)
mood: photoreal
slots:
  shot_type: eye-level exterior view along THIS retail street, photorealistic night photograph
  materials:
    - storefront facades kept in the drawn materials, 3 cm of fresh snow on every horizontal ledge and awning top
    - wet dark asphalt with tyre tracks, snow banked 20 cm at the kerb
    - glass shopfronts with warm interiors and light condensation at the edges
  camera: {lens_mm: 35, height: "eye level, 1.6 m", perspective: "straight vertical uprights, no keystoning"}
  lighting: "sky #0B1526 with no stars or moon, illuminated shop signs and 3000K interior light spilling 4 m onto the snow, one cool 4000K street lamp per 15 m, soft shadowless snow surfaces"
  season_weather: "midwinter, light snowfall visible as small flakes only within 5 m of the camera, no fog"
  entourage:
    - six pedestrians in dark winter coats on the far sidewalk, none in front of the entrance
    - no cars
    - existing street trees bare with snow on branches
  post: "neutral grading, white balance 3800K so snow reads slightly cool and shop light warm, no vignetting"
negative: extra buildings, changed roof shape, added floors, added or removed openings, snowstorm whiteout, lens flare, HDR halos, tilt-shift miniature blur, text or watermark
geometry_lock: Keep the roof shape, the window and door positions, the count of openings and every sign text exactly as drawn; only materials, lighting, sky, vegetation detail and entourage may change.
keep_fixed: [the sign texts as drawn]
references: []
backends:
  gpt-image: {path: pumasi --ref, aspect_hint: "3:2"}
  grok-imagine-image-2.0: {endpoint: /images/edits, mask_polarity: alpha0_edit}
samples: []
changelog:
  - {date: 2026-09-14, note: "synthesized from dusk-cinematic for '야간 눈 내리는 상업가로' (axes changed: lighting, season, entourage, post)"}
```

⑤ 저장 후 `python3 scripts/prompt_compose.py --pack custom-night-snow-retail --option aspect=3:2`로 프롬프트를 뽑아 렌더. 2회 승인되면 §5로 `night-snow-retail`로 승격.
