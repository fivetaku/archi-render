# 옵션 패널 어휘 (OPTIONS) — 웹툴과 /render 공용

> 웹툴 옵션 패널과 `/render --option k=v`는 이 파일의 키·값만 쓴다. 각 값 옆의 **주입 문장**이 팩 슬롯을 통째로
> 교체한다 (README §6). 문장은 모두 Specificity Gate 통과 형태로 고정되어 있으므로 UI는 값 이름만 다루면 된다.

## mood → `mood` (+ clay/watercolor/diagram은 materials·post 동반 교체)

| 값 | mood 어구 | 동반 교체 |
|---|---|---|
| `photoreal` | photorealistic architectural photograph | — |
| `cinematic` | cinematic, photorealistic architectural photograph | post 기본을 teal_orange로 |
| `clay` | clay-model white massing render | materials → ["uniform matte white clay on every surface", "light grey ground plane", "clear glass shown as pale grey tinted panes"]; post → "neutral, soft ambient occlusion in corners, no color grading, no vignetting" |
| `watercolor` | loose architectural watercolor illustration | materials → ["washes of the drawn materials with visible paper grain and pigment bleed at edges", "pencil underdrawing showing through"]; post → "warm off-white paper, no photographic grading" |
| `diagram` | clean axonometric-style diagram render | materials → ["flat white surfaces with thin 1 px dark grey edge lines", "one accent color #FF6B35 only on the element under discussion"]; post → "flat lighting, pure white background, no shadows, no grading" |

## lighting → `slots.lighting`

| 값 | 주입 문장 |
|---|---|
| `overcast` | soft overcast daylight from a uniformly bright grey-white sky, no direct sun, low-contrast ambient shadows under overhangs only |
| `midday` | high sun near zenith, 5500K, hard short shadows directly below overhangs, strong texture read on facades |
| `golden_hour` | warm low sun from camera-left at 10 degrees elevation, 3200K, long soft-edged shadows stretching right, sunlit planes amber and shaded planes cool blue-grey, interior lights on at 2700K |
| `dusk` | sun just below the horizon camera-left, sky graded deep blue #1B2A49 at zenith to burnt orange #E8742A at horizon with lit cloud undersides, interior lights on at 2700K spilling onto the ground, long soft shadows |
| `night` | sky #0B1526 with no stars or moon, interior and sign lights at 3000K as the only warm sources, one cool 4000K street lamp per 15 m, soft shadowless ground |
| `blue_hour` | 15 minutes after sunset, even cobalt sky #274B8F, no direct light, interior lights on at 2700K balanced to the sky, facades in soft cool shadow |

## season_weather → `slots.season_weather`

| 값 | 주입 문장 |
|---|---|
| `spring` | late spring, fresh mid-green foliage, dry ground, thin high cloud |
| `summer` | early summer, clear sky with a few soft white cumulus, saturated green foliage, dry ground |
| `autumn` | mid autumn, amber and rust foliage on deciduous trees, a few fallen leaves at kerbs, dry ground, clear air |
| `winter` | midwinter, bare deciduous branches, pale low-contrast sky, dry cold ground, no snow |
| `rain` | after rain, puddled and wet-look ground with mirror reflections of lights and sky, dark saturated paving, dramatic broken clouds, no falling rain visible |
| `snow` | midwinter, 3 cm fresh snow on horizontal surfaces only, wet dark asphalt where ploughed, bare branches with snow, light snowfall visible only near the camera |

## camera → `slots.camera` (+ shot_type 접두 문구)

| 값 | camera 객체 | shot_type 접두 |
|---|---|---|
| `eye_level` | `{lens_mm: 35, height: "eye level, 1.6 m", perspective: "straight vertical uprights, no keystoning, horizon at one-third height"}` | eye-level exterior view of THIS building |
| `elevated` | `{lens_mm: 24, height: "elevated, 3 m", perspective: "straight vertical uprights, wide field of view"}` | slightly elevated exterior view of THIS building |
| `drone` | `{lens_mm: 24, height: "drone, 40 to 60 m", perspective: "high oblique 45 to 60 degrees down, no lens distortion, site fills the frame"}` | aerial drone photograph of THIS site from the same angle |
| `interior` | `{lens_mm: 24, height: "1.4 m", perspective: "straight vertical uprights, one-point or two-point perspective as drawn"}` | interior view of THIS room from THIS camera position |

카메라 옵션은 캡처된 시점을 바꾸지 못한다 (lock이 우선). 어긋나는 값이면 렌더 전에 경고하고 캡처 시점에 맞는 값으로 되돌린다.

## materials 프리셋 → `slots.materials` (리스트 교체)

| 값 | 주입 리스트 |
|---|---|
| `white_stucco_oak` | white fine-textured stucco; dark anodized aluminum window frames; warm oak deck boards; black powder-coated steel railings; clear low-iron glass |
| `board_formed_concrete` | board-formed concrete with visible plank grain, tie-hole grid and light weathering streaks; exposed smooth concrete side walls; glass storefront with sky reflections and visible interior; asphalt with crisp painted white lines |
| `brick_dark_metal` | dark clinker brick with recessed grey mortar joints; black standing-seam metal roof and fascia; dark bronze anodized window frames; clear glass |
| `timber_glass` | vertical larch cladding weathered to silver-grey; exposed glulam beams; floor-to-ceiling clear glass with slim black frames; light concrete plinth |
| `clay_massing` | uniform matte white clay on every surface; light grey ground plane; clear glass shown as pale grey tinted panes |

프리셋 대신 자유 리스트(`materials=a,b,c`)도 허용하되 항목마다 재질명 + 표면 상태를 요구한다.

## entourage 토글 → `slots.entourage` (허용 목록 + 부정형)

| 토글 | on 문장 | off 문장 |
|---|---|---|
| `people` | people kept in the drawn positions with realistic clothing; if none drawn, two people near the entrance | no people |
| `cars` | real cars only in the drawn parking bays or lanes | no cars |
| `vegetation` | realistic trees, hedges and planting in the drawn positions with seasonally correct foliage | vegetation exactly as drawn, no added planting |
| `furniture` | realistic outdoor furniture in the drawn positions, interior furniture visible through glass | no added furniture |

토글 4개는 항상 4문구를 만든다 (off도 부정형으로 남긴다). 순서: people, cars, vegetation, furniture.

## post → `slots.post`

| 값 | 주입 문장 |
|---|---|
| `neutral` | neutral color grading, white balance matched to the light source, no vignetting, no added contrast or saturation |
| `teal_orange` | cinematic grading with teal shadows and warm amber highlights, mild contrast lift, high dynamic range with no clipped windows, no vignetting |
| `warm_film` | warm film-like grading, slightly lifted blacks, gentle highlight roll-off, fine grain, no vignetting |
| `bw` | black and white, medium contrast, full tonal range from paper white to deep black without clipping, no toning |

## keep_fixed → `keep_fixed[]` (자유 문장, `;` 구분)

입력 예: `keep_fixed=the canopies white; the sign text "Cafe"`. 각 항목은 "Keep …" 문장으로 주입된다. 색이 확정된 요소, 간판 문구, 바꾸면 안 되는 마감은 여기에 쓴다 (트라이얼 "(keep them white)" 패턴).

## aspect → 프롬프트 꼬리 "Aspect ratio N:M."

| 값 | 용도 |
|---|---|
| `4:3` | 카페·주거 정면/사분면 (overcast-photoreal, golden-hour 기본) |
| `16:9` | 넓은 외관·주차장 포함 샷 (dusk-cinematic, midday-concrete 기본) |
| `3:2` | 가로 스트리트뷰 |
| `1:1` | 배치도·조감 (aerial-drone 기본) |
| `2:1` | 파노라마·공원 |
| `auto` | 입력 캡처 비율 그대로 (gpt-image 경로는 입력 비율을 근사함) |

## 키 요약 (구현 참조)

```
mood            photoreal|cinematic|clay|watercolor|diagram
lighting        overcast|midday|golden_hour|dusk|night|blue_hour
season_weather  spring|summer|autumn|winter|rain|snow
camera          eye_level|elevated|drone|interior
materials       white_stucco_oak|board_formed_concrete|brick_dark_metal|timber_glass|clay_massing | 자유 리스트
entourage       people,cars,vegetation,furniture (각 on|off)
post            neutral|teal_orange|warm_film|bw
keep_fixed      자유 문장 ; 구분
aspect          4:3|16:9|3:2|1:1|2:1|auto
```
