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
| `dawn` | first light 10 minutes after sunrise, sun at 3 degrees elevation camera-right, 2800K, pale pink-grey sky, very long soft shadows stretching left, interior lights on at 2700K |
| `morning_side` | morning sun from camera-right at 30 degrees elevation, 4500K, crisp medium-length shadows raking across the facade to reveal texture, clear sky, interior lights off |
| `afternoon_backlit` | afternoon sun behind the building at 35 degrees elevation, 5000K, facade in open shade with a bright rim of light on roof edges and parapets, shadows stretching toward the camera, no lens flare |
| `night_signs_only` | night, sky #0B1526 with no stars or moon, all interior lights off with glazing reading dark, only sign lights at 3000K and low pathway bollards at 3000K, one cool 4000K street lamp per 15 m, soft shadowless ground |
| `night_full` | night, sky #0B1526 with no stars or moon, every interior light on at 2700K glowing through all glazing, sign lights at 3000K, one cool 4000K street lamp per 15 m, soft shadowless ground |

`sky`·`interior_lights` 옵션이 함께 오면 lighting 문장 **하나**로 합쳐진다 (아래 sky 절 참조).

## season_weather → `slots.season_weather`

| 값 | 주입 문장 |
|---|---|
| `spring` | late spring, fresh mid-green foliage, dry ground, thin high cloud |
| `summer` | early summer, clear sky with a few soft white cumulus, saturated green foliage, dry ground |
| `autumn` | mid autumn, amber and rust foliage on deciduous trees, a few fallen leaves at kerbs, dry ground, clear air |
| `winter` | midwinter, bare deciduous branches, pale low-contrast sky, dry cold ground, no snow |
| `rain` | after rain, puddled and wet-look ground with mirror reflections of lights and sky, dark saturated paving, dramatic broken clouds, no falling rain visible |
| `snow` | midwinter, 3 cm fresh snow on horizontal surfaces only, wet dark asphalt where ploughed, bare branches with snow, light snowfall visible only near the camera |
| `early_spring_blossom` | early spring, cherry and magnolia trees in full pale-pink blossom with a few petals on the paving, lawns just turning green, dry ground, thin high cloud |
| `monsoon_rain` | monsoon downpour, heavy rain falling in visible grey streaks, water sheeting down the glass, gutters overflowing, puddled dark paving with rippled reflections, low uniform grey sky |
| `late_autumn` | late autumn, mostly bare deciduous branches with a few dry brown leaves left, thick leaf litter at kerbs and lawn edges, low pale sun, dry ground |
| `heavy_snow` | midwinter, heavy snowfall, 15 cm of fresh snow on every horizontal surface and roof, flakes falling across the whole frame, snow-laden branches, flat white overcast sky |
| `haze` | fine-dust haze, distant buildings low-contrast and desaturated fading toward the horizon, sky uniform pale grey-beige, soft diffuse light, near facades at full contrast |
| `fog` | dense morning fog, visibility about 80 m, background dissolving to white, soft shadowless light, wet dark paving, drops on railings |

## vegetation_age → season 문장에 합류 (`Season and weather: {season}; {vegetation}`)

| 값 | 주입 어구 |
|---|---|
| `young` | newly planted 2 m saplings with timber stakes and ties, thin open canopies, bare mulch beds |
| `mature` | mature trees with 8 to 10 m canopies casting broad soft shade, established clipped shrubs |
| `lush` | lush planting with a dense understory of ferns and grasses, climbers on walls and pergolas, mature 8 to 10 m canopies |

## sky → lighting 문장에 합류 (하늘 우선권)

| 값 | 주입 어구 |
|---|---|
| `clear` | clear cloudless sky |
| `scattered_cumulus` | sky with scattered soft white cumulus covering about a third of it |
| `overcast` | uniformly overcast grey-white sky with no visible sun disc |
| `dramatic` | towering cumulonimbus with dark grey bases and sunlit white tops, sun breaking through gaps in distinct shafts |
| `haze` | hazy pale grey-beige sky with no cloud detail and a low-contrast horizon |

**우선권 규칙**: `sky`가 주어지면 lighting 문장과 season 문장에서 `sky/cloud/cumulus`를 담은 쉼표 절을 **제거**하고 sky 어구가 그 자리를 대신한다. 즉 하늘 묘사는 `sky > lighting의 하늘 절 > season_weather의 하늘 절` 순. 태양 방향·색온도·그림자(lighting의 나머지)는 그대로 남는다. `season_weather=haze`와 `sky=haze`는 같은 하늘을 말하므로 둘 다 쓸 필요 없다 — season 쪽은 지상 대비, sky 쪽은 하늘만.

## interior_lights → lighting 문장에 합류

| 값 | 주입 어구 |
|---|---|
| `off` | all interior lights off, glazing reflecting the sky only |
| `partial` | interior lights on at 2700K in about half the rooms, the rest dark |
| `all_on` | every interior light on at 2700K glowing through all glazing |

주어지면 lighting 텍스트의 기존 `interior lights …` 절을 제거하고 이 어구가 대신한다 (`night_signs_only`의 "all interior lights off"도 덮어씀).

## camera → `slots.camera` (+ shot_type 접두 문구)

| 값 | camera 객체 | shot_type 접두 |
|---|---|---|
| `eye_level` | `{lens_mm: 35, height: "eye level, 1.6 m", perspective: "straight vertical uprights, no keystoning, horizon at one-third height"}` | eye-level exterior view of THIS building |
| `elevated` | `{lens_mm: 24, height: "elevated, 3 m", perspective: "straight vertical uprights, wide field of view"}` | slightly elevated exterior view of THIS building |
| `drone` | `{lens_mm: 24, height: "drone, 40 to 60 m", perspective: "high oblique 45 to 60 degrees down, no lens distortion, site fills the frame"}` | aerial drone photograph of THIS site from the same angle |
| `interior` | `{lens_mm: 24, height: "1.4 m", perspective: "straight vertical uprights, one-point or two-point perspective as drawn"}` | interior view of THIS room from THIS camera position |

카메라 옵션은 캡처된 시점을 바꾸지 못한다 (lock이 우선). 어긋나는 값이면 렌더 전에 경고하고 캡처 시점에 맞는 값으로 되돌린다.

### 카메라 필드 개별 덮어쓰기 — `lens_mm` · `camera_height_m` · `tilt`

프리셋(또는 팩 camera 객체)의 해당 필드만 바꾼다. shot 문장 하나에 합류한다 (`…; camera 50mm lens, 2.5 m camera height, …`).

| 키 | 형 | 효과 |
|---|---|---|
| `lens_mm` | 정수 (예 `24`, `35`, `50`, `85`) | `camera.lens_mm` 교체 |
| `camera_height_m` | 실수 (예 `1.6`, `2.5`, `45`) | `camera.height` → "{n} m" |
| `tilt` | `level` \| `slight_up` \| `slight_down` | `camera.perspective` 교체 |

| tilt 값 | 주입 어구 |
|---|---|
| `level` | camera level, straight vertical uprights, no keystoning |
| `slight_up` | camera pitched up about 5 degrees, verticals converging slightly toward the top |
| `slight_down` | camera pitched down about 5 degrees, horizon in the upper third of the frame |

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

### people_density · people_activity · car_density · car_type → entourage 문장에 합류

네 키는 entourage 문장 **하나**에 합쳐진다. people 두 키는 entourage 목록의 people 항목(팩 자유 항목 "two people seated…" 포함)을 교체하고, car 두 키는 cars 항목을 교체한다. 항목이 없으면 덧붙인다.

- `people_density`·`people_activity`는 **people 토글이 on일 때만** 적용된다. 목록에 "no people"("no added people" 포함)이 있으면 무시한다.
- `car_density`는 명시 옵션이므로 "no cars" 항목도 덮어쓴다(`none`이면 "no cars"로). `car_type`만 단독으로 왔고 cars가 off면 무시한다. `bicycles_only`는 density보다 우선한다.
- 조합 문장 예: `busy`+`mixed` → "a busy crowd of fifteen or more people in groups of three to five in a mix of walking, standing in conversation and sitting, realistic everyday clothing".

| people_density | 주입 어구 |
|---|---|
| `none` | no people |
| `sparse` | one or two people |
| `moderate` | five to eight people spread across the drawn walkways and entrance |
| `busy` | a busy crowd of fifteen or more people in groups of three to five |

| people_activity | 주입 어구 |
|---|---|
| `walking` | walking along the drawn paths, mid-stride |
| `standing_talking` | standing in pairs talking, turned toward each other |
| `seated` | seated on the drawn benches, steps and terraces |
| `mixed` | in a mix of walking, standing in conversation and sitting |

| car_density | 주입 어구 |
|---|---|
| `none` | no cars |
| `few` | one to three cars parked in the drawn bays with the remaining bays empty |
| `full` | a car in every drawn parking bay |

| car_type | 주입 어구 |
|---|---|
| `passenger` | passenger cars only, sedans and compact SUVs in white, grey and black |
| `mixed_commercial` | a mix of passenger cars and one delivery van or small box truck |
| `bicycles_only` | bicycles only in the drawn racks, no motor vehicles |

## context · material_wear → `Context:` 문장 (둘 중 하나라도 있을 때만 생성)

| context | 주입 어구 |
|---|---|
| `as_drawn` (기본) | Do not add surroundings beyond what is drawn |
| `urban_dense` | dense urban surroundings, 5 to 8 storey neighbouring buildings tight to the site boundary, street with kerbs, lamp posts and parked cars beyond the site |
| `suburban` | suburban surroundings, two-storey houses with front gardens set back across the street, hedges and evenly spaced street trees |
| `rural` | rural surroundings, open fields and a low tree line at the horizon, gravel access track, no neighbouring buildings |
| `waterfront` | waterfront setting, calm water along one edge of the site with a timber boardwalk and mirror reflections of the building |
| `forest` | forest surroundings, dense pine and deciduous trees 15 to 20 m tall closing in at the site edge, dappled light on the ground |

| material_wear | 주입 어구 |
|---|---|
| `new` | all materials brand new, clean and unweathered, crisp edges and unmarked paving |
| `lived_in` | materials lightly lived-in, faint staining under window sills, gentle patina on metal, clean glass |
| `weathered` | weathered materials, dark streaking below sills and copings, moss and algae at grade, faded chalky paint and rust bloom on steel fixings |

- `context`를 명시하지 않고 `material_wear`만 주면 `as_drawn` 어구가 앞에 붙는다 ("Context: Do not add surroundings beyond what is drawn; materials lightly lived-in, …").
- 둘 다 없으면 Context 문장 자체를 만들지 않는다 (기본 `as_drawn`은 **암묵**: 잠금 문장과 `negative`의 "extra buildings"가 이미 막고 있으므로 슬롯을 쓰지 않는다). `context=as_drawn`을 명시하면 문장을 낸다.
- `context≠as_drawn`은 팩 `negative`의 "extra buildings"와 긴장한다 — 잠금은 "buildings on the site", context는 "surroundings beyond the site"로 읽히지만, 결과에 부지 안 건물이 늘면 `keep_fixed`로 고정한다.

## tone → grading 문장에 합류 (`Post-processing: {tone}; {post}`)

tone은 **사진 관용구** 문장, post는 그레이딩 문장이다. 둘이 한 문장으로 합쳐진다.

| 값 | 주입 어구 |
|---|---|
| `editorial_magazine` | editorial architecture-magazine photograph, single considered frame, restrained composition, true-to-life color |
| `real_estate_ad` | real-estate listing photograph, brightly and evenly exposed, open shadows, clean blue sky, entrance clearly readable |
| `competition_panel` | competition-panel render, slightly desaturated palette, clean edges, uncluttered foreground, emphasis on the building silhouette |
| `documentary` | documentary photograph, available light only, no staging, natural imperfections and everyday clutter kept |

## post → `slots.post`

| 값 | 주입 문장 |
|---|---|
| `neutral` | neutral color grading, white balance matched to the light source, no vignetting, no added contrast or saturation |
| `teal_orange` | cinematic grading with teal shadows and warm amber highlights, mild contrast lift, high dynamic range with no clipped windows, no vignetting |
| `warm_film` | warm film-like grading, slightly lifted blacks, gentle highlight roll-off, fine grain, no vignetting |
| `bw` | black and white, medium contrast, full tonal range from paper white to deep black without clipping, no toning |

## keep_fixed → `keep_fixed[]` (자유 문장, `;` 구분)

입력 예: `keep_fixed=the canopies white; the sign text "Cafe"`. 각 항목은 "Keep …" 문장으로 주입된다. 색이 확정된 요소, 간판 문구, 바꾸면 안 되는 마감은 여기에 쓴다 (트라이얼 "(keep them white)" 패턴).

## references → 꼬리 문장 (캡 밖)

`references=refs/a.jpg,refs/b.jpg` (옵션, cwd 기준) 또는 팩 `references[]`(팩 폴더 기준). 비어 있지 않으면 keep_fixed 뒤에 고정 문장 **"Match the attached reference images for materials and mood."** 를 붙이고, `render.py`가 gpt 경로에서 각 파일을 추가 `--ref`로 imagen.sh에 넘긴다 (없는 파일은 경고 후 건너뜀). grok 경로는 첨부하지 않는다.

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

기계가 읽는 정본은 `python3 scripts/prompt_compose.py --list-options` (JSON: `options{key→{type,values,merged_into…}}`, `values{key→[…]}`, `free{key→type}`). 웹툴은 이 출력으로 패널을 만든다.

```
# 합류 문장             키                옵션 값
shot                    mood              photoreal|cinematic|clay|watercolor|diagram
                        camera            eye_level|elevated|drone|interior
                        lens_mm           정수        (camera.lens_mm 덮어쓰기)
                        camera_height_m   실수        (camera.height 덮어쓰기)
                        tilt              level|slight_up|slight_down
materials               materials         white_stucco_oak|board_formed_concrete|brick_dark_metal|timber_glass|clay_massing | 자유 리스트
lighting                lighting          overcast|midday|golden_hour|dusk|night|blue_hour|dawn|morning_side|afternoon_backlit|night_signs_only|night_full
                        sky               clear|scattered_cumulus|overcast|dramatic|haze   (lighting·season의 하늘 절을 대체)
                        interior_lights   off|partial|all_on
season                  season_weather    spring|summer|autumn|winter|rain|snow|early_spring_blossom|monsoon_rain|late_autumn|heavy_snow|haze|fog
                        vegetation_age    young|mature|lush
entourage               entourage         people,cars,vegetation,furniture (각 on|off)
                        people_density    none|sparse|moderate|busy        (people on일 때만)
                        people_activity   walking|standing_talking|seated|mixed   (people on일 때만)
                        car_density       none|few|full
                        car_type          passenger|mixed_commercial|bicycles_only
context                 context           as_drawn|urban_dense|suburban|rural|waterfront|forest
                        material_wear     new|lived_in|weathered
grading                 tone              editorial_magazine|real_estate_ad|competition_panel|documentary
                        post              neutral|teal_orange|warm_film|bw
(캡 밖)                 keep_fixed        자유 문장 ; 구분
                        references        이미지 경로 , 구분
                        aspect            4:3|16:9|3:2|1:1|2:1|auto
```

우선권: **명시 옵션 > 팩 슬롯(`slots.<key>` 또는 팩 최상위 `<key>`) > 프리셋 기본**. 팩에 `people_density: sparse`처럼 새 키를 슬롯으로 둘 수 있다.
