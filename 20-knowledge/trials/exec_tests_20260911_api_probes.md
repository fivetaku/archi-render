# 실행 검증 (executable claims) — 2026-09-11 17:5x KST

환경: macOS Darwin 25.4, curl, Python 3 + Pillow 12.3.0. 라우터 `https://router.axwith.com/api/v1` (볼트 `insane-router-url`), 소비자 키 `insane-router-key-aside`.

| # | 테스트 | 명령 요지 | 결과 |
|---|---|---|---|
| E1 | `POST /images/edits` model=openai/gpt-image-2 + image | multipart image=sketch_facade.png | **HTTP 501** `image edits only supported for x-ai/* (got openai)` — 라우터 경유 gpt-image 편집 불가 (생성만 가능) |
| E2 | `POST /images/edits` model=x-ai/grok-imagine-image-2.0 + image (마스크 없음) | 프롬프트 "line sketch → photorealistic render, keep geometry" | **HTTP 200, 17.7s**, `data[0].url` (imgen.x.ai 임시 URL, JPEG 1024×1024, 206KB). 창 2·문 위치·벽 비례 보존. **지붕이 박공(gable)→모임지붕(hip) 형태로 드리프트** — 선화 입력만으로는 지붕 기하가 불안정 |
| E3 | 같은 모델 + image + mask(알파 0 = 편집 영역, 왼쪽 창) | 프롬프트 "Replace only the left window with arched window" | **HTTP 200, 18.5s**, 마스크 영역(왼쪽 창)만 아치창으로 교체, 나머지 선화 그대로 유지 → **마스크 인페인팅 동작 확인**. 입력 512px → 출력 1024px 자동 업스케일. `usage.cost_in_usd_ticks: 700000000` (구독 경로라 실과금 0) |

파일: `sketch_facade.png`(입력), `mask_left_window.png`(RGBA, 투명=편집), `edit_grok_noMask.jpg`, `edit_grok_mask.jpg`, 응답 JSON 2건.

함의: (1) 워크스페이스의 0원 기본 백엔드는 라우터 x-ai grok-imagine-image-2.0 편집 API. (2) gpt-image 편집(마스크 포함)은 라우터 경유 불가 → 필요하면 pumasi:image(Codex image_gen, `--image=` 레퍼런스 첨부만 가능, 마스크 없음)로 스타일 앵커 생성만. (3) 기하 보존은 선화만으로 불충분 → SketchUp에서 그림자·면 음영이 있는 캡처(또는 depth)를 함께 주거나 프롬프트에 지붕 형태를 명시하는 규칙이 필요. (4) 결과 URL은 임시라 즉시 다운로드해 로컬 보존 필수.

| E4 | 같은 모델 + 음영 매싱 입력(`shaded_massing.png`, 768px, 지붕·측벽 면 음영, 프롬프트에 "gable roof" 명시) | 31.4s, 200 | 창 2·문·측벽 각도·재질 지시(백색 스터코·스탠딩심 금속 지붕·오크 문) 모두 반영, 1024×1024. **지붕은 여전히 모임지붕(hip)형으로 해석** — 단, 입력 그림 자체의 지붕면 표현이 애매했음(정면 삼각면이 hip으로 읽힐 수 있음). 결론: 지붕 같은 상부 기하는 프롬프트 명시만으로 보장되지 않으며, 입력 캡처의 면 표현이 명확해야 한다(SketchUp 실제 캡처는 이 실험보다 명확할 것이나 검증 필요) |
