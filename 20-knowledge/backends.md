# 백엔드 능력 카드 (2026-09-14 실측 기준)

> `/render`·`/fix`가 백엔드를 고를 때 읽는 정본. 실측 출처는 `20-knowledge/trials/` 두 문서.
> 여기 없는 능력은 "있다"고 가정하지 않는다. 바뀌면 이 카드와 `_meta/changelog.md`를 함께 고친다.

## 요약 표

| 항목 | gpt-image (pumasi `imagen.sh --ref`) | grok-imagine-image-2.0 (insane-router `/images/edits`) |
|---|---|---|
| 역할 | **전체 샷 1차 렌더 기본값** | **영역 수정(마스크) 전용** (전체 렌더는 사용자가 지명할 때만) |
| 호출 경로 | `~/.claude/plugins/.../pumasi/.../imagen.sh --ref <capture>` (Codex `image_gen`, 구독) | `POST $insane-router-url/images/edits`, `Authorization: Bearer $<ARCHI_RENDER_ROUTER_KEY_SERVICE, 기본 insane-router-key-aside>`, multipart `image=` (+`mask=`) |
| 실과금 | 0 (구독 한계비용) | 0 (구독 경로, `usage.cost_in_usd_ticks`는 참고치로 meta.json에 그대로 적재) |
| img2img | 예 (`--ref` 스타일/소스 앵커 첨부) | 예 (`image=`) |
| 마스크 인페인팅 | **없음** — 프롬프트 "only change X"로 근사만 가능 | **있음** — RGBA PNG, 알파 0 = 편집 영역, 원본과 동일 해상도 (E3 실측) |
| 소요 | 약 1~2분/장 | 12~18초 (음영 매싱 입력은 30초대) |
| 출력 해상도 | 요청 비율을 따름 (16:9 → 1672×941, 2026-10-11 실측). 고정 크기 아님 | **1152×864(4:3) 고정** — 16:9 입력은 좌우가 잘린다(2026-10-11 실측: demo-house 2000×1125 → 1152×864) |
| 결과 전달 | 로컬 파일 | **임시 URL(imgen.x.ai)** — 즉시 다운로드해 `renders/…/render.*`로 보존. URL을 meta.json에만 남기고 파일을 안 받으면 유실 |
| 기하 보존 | 우수 (간판·인물·개구부 위치 유지) | 양호하되 소폭 드리프트 (천막 색, 가로수 소실, 선화 입력에서 박공→모임지붕) |
| 재질·조명 사실성 | 뚜렷히 우세 (유리 반사·식생) | 양호 |
| 저해상 입력 | 권장 안 함 (규약 ≥2000px) | 300~700px도 통과하나 품질 낮음 |

## 못 쓰는 경로 (실측 실패·정책 금지)

| 경로 | 상태 | 근거 |
|---|---|---|
| 라우터 `openai/gpt-image-2` `/images/edits` | **HTTP 501** `image edits only supported for x-ai/*` — 편집·마스크 불가, 생성만 가능 | E1 실측 |
| Gemini 이미지 모델 (라우터) | 라우터 모델 목록에 없음 | `GET $URL/models` 실측 (2026-09-11) |
| `api.openai.com` 직접 호출 (볼트 `openai-api-key`) | **정책 금지** — 종량 과금, 라우터 예산 밖 | 전역 CLAUDE.md 2026-09-08 규칙 |
| Google/Gemini 원본 키 직접 호출 | **정책 금지** — 동일 사유 | 동일 |
| Hunyuan/로컬 ControlNet | v1 미도입. `--mode controlnet`은 스텁 개념만 | 02 설계 문서 Q2 디폴트 |

## 라우팅 규칙 (스크립트가 따르는 것)

1. `/render` 기본 `--backend gpt`. gpt가 실패하면 원인을 보고하고 grok으로 자동 재시도하지 않는다(오너 결정 2026-10-11). grok 전체 렌더는 사용자가 지명할 때만. 렌더 키가 없는 수강생 Codex 앱은 `$development-image`(Codex 내장 이미지 도구 = 같은 gpt-image)로 렌더하고 `scripts/attach_render.py`로 기록한다.
2. `/fix`는 **grok만**. 사용자가 "gpt로 부분 수정"을 요청하면 마스크가 없음을 설명하고, 대안으로 `keep_fixed` 재렌더(gpt에 "수정된 영역 외 변경 금지" 꼬리 프롬프트 + 이전 리비전을 `--ref`로)를 제안한다.
3. 두 백엔드 모두 결과를 `renders/<P>/<S>/Rnn/`에 `render.*` + `prompt.txt` + `meta.json`으로 남긴다. grok의 임시 URL은 다운로드 전에는 성공으로 치지 않는다.
4. 키는 라우터 소비자 키만. render.py 기본은 `insane-router-key-aside`(볼트에 `insane-router-key-archi-render`는 아직 없음 — 2026-10-11 확인). 전용 키를 `insane-router-connect`로 발급하면 `ARCHI_RENDER_ROUTER_KEY_SERVICE`로 바꾼다. `insane-router-admin-key`는 Bearer로 쓰지 않는다(401이 정상).
5. URL에 `/v1`을 덧붙이지 않는다 (`insane-router-url`이 이미 `/api/v1`).

## 프롬프트 계약 (두 백엔드 공통 꼬리)

```
Use the attached SketchUp image as the exact source. Keep the geometry, camera, window/door
positions and count of openings exactly. Do not add or remove buildings, floors or openings.
```

색이 확정된 요소는 "(keep them white)"처럼 프롬프트에 명시한다. 슬롯은 6~7개를 넘기지 않는다 (`20-knowledge/stylepacks/OPTIONS.md`).

## 마스크 극성 (벤더 변환층)

| 벤더 | 편집 영역 표기 | 비고 |
|---|---|---|
| grok-imagine (라우터) / OpenAI gpt-image edit | **RGBA 알파 0 = 편집** | 이 워크스페이스의 유일한 활성 경로. 웹툴이 이 형식으로 저장 |
| FLUX.1 Fill | 흑백 마스크: **흰색 = 재생성**, 검정 = 보존 (또는 알파 투명 = 재생성) | 미도입, 변환층 참고용 |
| Stability inpaint | `mode=mask`(파일/알파) 또는 `mode=search`(프롬프트 탐지) | 미도입 |
| Midjourney Vary Region | UI 선택 영역 = 재생성 | API 없음 |

내부 표준은 8비트 그레이 PNG, 255 = 편집 영역. 전송 전 팽창 8~16px + 페더 4~8px (clm_054). 마스크 해상도는 기준 렌더와 1:1.
