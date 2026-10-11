# 워크스페이스 설계 입력 명세 — 건축 AI 렌더 워크스페이스 (Phase 1~3 인터뷰 입력)

> 이 문서는 Workspace_Builder의 Phase 1(컨텍스트)·Phase 2(아키타입)·Phase 3(상세 설계)에 그대로 투입하기 위한 결정·제안·미결 목록이다.

> **2026-10-11 갱신 주의**: 이 문서는 기준일 시점 기록이다. 그 뒤 바뀐 사실 — SketchUp 2026.2가 이 맥에 설치돼 `-RubyStartup`으로 자동 실행 가능, grok 출력은 1152×864(4:3) 고정, 전체 렌더는 gpt만(grok 자동 폴백 없음), 수강생 Codex 앱은 `$development-image`로 렌더. 현행 정본은 `20-knowledge/backends.md`·`capture-protocol.md`.
> "사실"은 `01_full_report.md`의 검증 주장 `(clm 번호)`을 인용하고, "제안"은 설계 판단임을 명시한다. 미확정 사항은 §9에 모아 인터뷰 질문으로 넘긴다.

---

## 1. 한 줄 정의

**입력**: 사용자 PC의 SketchUp에서 씬(샷)별로 내보낸 캡처 이미지 폴더(+ 선택: 카메라 JSON, 레퍼런스 이미지).
**출력**: 샷별 스타일팩 적용 렌더(리비전 관리) + 영역 수정 반복 + 납품 컨택트시트.
**에이전트 역할**: 렌더 디렉터 — 캡처 규약 점검 → 스타일팩 선택/생성 → 백엔드 호출 → 기하 QA 경보 → 영역 수정 루프 → 리비전·승인 기록.

---

## 2. 확정 전제 (사실 기반, 재질문 금지)

| # | 전제 | 근거 |
|---|---|---|
| P1 | SketchUp 헤드리스 자동화는 불가. 사용자가 SketchUp에서 1회 트리거(플러그인 버튼 또는 시작 스크립트)해 폴더를 덤프한다 | clm_001 |
| P2 | 이 맥에 SketchUp 없음(Blender만). 워크스페이스는 "폴더 인입" 구조 | clm_092 |
| P3 | 0원 기본 백엔드는 insane‑router `x-ai/grok-imagine-image-2.0` `/images/edits` — img2img·RGBA 마스크 인페인팅 실측 통과 | clm_088, clm_089, clm_091 |
| P4 | 라우터 경유 gpt‑image 편집·마스크 불가(501). Gemini 이미지 모델은 라우터에 없음 | clm_087, clm_091 |
| P5 | pumasi:image(Codex `image_gen`/Grok)는 `--image=` 스타일 앵커 첨부만 가능, 마스크 없음 → 스타일팩 예시 이미지 생성·무드보드 용도로만 | pumasi imagen.sh 실측(README E 표) |
| P6 | SketchUp 네이티브 뎁스맵 없음 → 캡처 규약은 클레이/모노크롬 + Scene 잠금 + 2000px 이상 | clm_026 |
| P7 | 마스크 극성은 벤더별 상이(알파 0=편집 / 흰색=재생성 / 검정=수정). 내부 표준 마스크 1개 + 벤더 변환층 | clm_022, clm_047, clm_048 |
| P8 | AI 렌더 산출물은 git LFS 밖(.gitignore + 외부 스토리지), 원본 캡처·스타일팩만 git 추적 | clm_008 |
| P9 | 리비전은 R00/R01 자동 태그 + clay→internal→client→approval 단계 폴더 | clm_009 |
| P10 | 비용은 API usage 필드(xAI `cost_in_usd_ticks` 등)를 사이드카 JSON에 그대로 적재 | clm_005 |

---

## 3. 아키타입 추천 (Phase 2 입력)

**추천: `development` (subtype `automation`)** — 이유: 스크립트 층(백엔드 래퍼·마스크 변환·QA·컨택트시트)이 핵심이고, 이미지 자산 폴더와 코드 폴더 분리가 필요하며, 선례(`~/insane-3d`, development/automation, dual runtime, guard+wrap)와 운영 패턴이 같다.
**차선: `knowledge-base` preset `asset-library`** — 스타일팩과 참고 이미지 모음이 중심이라면. 단 이 경우 스크립트 층은 `--scripts-layer`로 추가해야 한다.
**variant 참고**: `--data-isolation 70-private`(클라이언트 설계 원본 격리, fail‑closed)는 실제 프로젝트 도면이 들어오면 켤 것.

---

## 4. 폴더 제안 (Phase 3 입력)

```
~/insane-render/                      # 이름은 인터뷰에서 확정
├── CLAUDE.md / AGENTS.md              # dual runtime
├── 10-planning/                       # 프로젝트별 샷 리스트·브리프
├── 20-knowledge/                      # 이 리서치 KB(01·02 문서 요약), 백엔드 규격 카드, 캡처 규약
├── 30-docs/                           # 운영 매뉴얼(SketchUp 플러그인 설치·트리거 절차)
├── 40-reports/                        # QA 리포트·비용 리포트
├── 50-output/                         # 납품본(컨택트시트·최종 렌더 포인터) — LFS 밖
├── 90-archive/
├── assets/
│   ├── stylepacks/<pack-id>/pack.yaml + refs/*.jpg + samples/*.jpg   # git 추적
│   └── captures/<project>/<shot>/capture.png + camera.json           # git 추적(원본)
├── renders/<project>/<shot>/R00..Rnn/render.jpg + meta.json + mask_*.png   # .gitignore, 외부 스토리지 동기화
├── scripts/
│   ├── render.py          # 백엔드 라우팅(grok edit 기본) + 사이드카 meta.json + 임시 URL 즉시 다운로드
│   ├── mask_convert.py    # 내부 표준 마스크 → 벤더 극성/포맷 변환
│   ├── qa_geometry.py     # 캡처 vs 렌더 엣지 IoU/SSIM 경보(게이트 아님)
│   ├── contact_sheet.py   # PIL montage
│   ├── revision.py        # R00/R01 태그·승인 단계 이동
│   └── sketchup/export_scenes.rb   # 사용자 PC용 Ruby: 씬별 write_image + camera.json
├── webtool/               # 로컬 마스킹 웹툴(§6)
└── _meta/                 # changelog·deviations·orchestration
```

---

## 5. 커맨드 초안 (Pushy description은 생성 시 작성)

| 커맨드 | 티어 | 역할 | 근거/주의 |
|---|---|---|---|
| `/intake <project>` | standard | 캡처 폴더 인입, 규약 점검(해상도≥2000px·클레이 스타일·씬 이름·camera.json 유무), 샷 목록 생성 | P1, P6 |
| `/stylepack new|edit|list` | standard | 스타일팩 생성·편집(슬롯 프롬프트 + 레퍼런스 + 모델 파라미터 + 버전), pumasi:image로 샘플 이미지 생성 | §7 스키마, clm_020 |
| `/render <shot|all> --pack <id> [--mode edit|controlnet]` | lite | 백엔드 호출, R태그 부여, meta.json·비용 기록, 컨택트시트 갱신 | P3, P10 |
| `/fix <shot> [--mask <file>|--web]` | standard | 마스킹 웹툴 열기 또는 마스크 파일 받아 영역 재생성, 새 리비전 생성 | P7, clm_089, clm_054 |
| `/qa <shot|all>` | standard | 엣지 IoU/SSIM 경보, 창·문 개수 등 구조 체크(사람 판정 보조), 리포트 | clm_067, §8 미확정(오라클 비판) |
| `/consistency <project>` | full | 샷 간 재질·색 일관성 점검(색 히스토그램·CLIP/DINO 유사도 참고치), 시드/레퍼런스 고정 재렌더 제안 | clm_030, (미확정·부록 #018번) |
| `/approve <shot> <stage>` | lite | clay→internal→client→approval 단계 이동, 승인 기록 | P9 |
| `/deliver <project>` | standard | 납품 컨택트시트·최종본 포인터·비용 합계 | P8 |
| `/wrap` | lite | 세션 정리(생성기 표준) | — |

---

## 6. 마스킹 웹툴 사양 (제안)

- **형태**: 로컬 정적 웹앱(Vite + React), `webtool/` 안. 파이썬 `http.server` 또는 `npm run dev`로 실행. 원본 렌더를 열고 브러시/라쏘/직사각형으로 영역 표시 → 영역별 지시문 입력 → `regions.json` + `mask_<n>.png` 저장.
- **캔버스**: react‑canvas‑masker(undo/redo·zoom·dataURL) 기반 (clm_053). 원본 좌표계 그대로 1:1 마스크(백엔드 요구 "원본과 동일 크기") — 표시용 스케일과 저장용 해상도 분리.
- **내부 표준 마스크**: 8비트 그레이 PNG, 255 = 편집 영역. 벤더 변환: grok/OpenAI → RGBA 알파 0 = 편집 (clm_022, 실측 clm_089); FLUX Fill → 흰색 = 재생성 (clm_047); Stability `mode=mask` (clm_046).
- **선택 기능**: SAM2 클릭 선택 — 실현 가능하나 입력 1024² 고정·출력 256² 마스크·WebGPU 실험적 (clm_052). v1에서는 제외하고 v2 후보로.
- **품질 기본값**: 마스크 팽창(8~16px) + 페더(4~8px) 후 전송, 결과는 새 리비전으로 저장 (clm_054).
- **regions.json 스키마**:
```json
{"shot":"P01_S03","base_revision":"R02","regions":[{"id":1,"mask":"mask_1.png","instruction":"1층 창을 목재 프레임 아치창으로","strength":"replace|refine|touch"}]}
```

---

## 7. 스타일팩 스키마 (제안, `assets/stylepacks/<id>/pack.yaml`)

```yaml
id: kr-residential-overcast-v1
version: 1.0.0
name: 주거 외관 · 흐린 낮 · 사진사실
mood: photoreal            # photoreal|cinematic|painterly|watercolor|diagram|collage|clay  (clm_012)
slots:                     # 6~7개 이하 유지 (clm_020)
  shot_type: "eye-level exterior elevation"
  materials: ["white stucco", "dark standing-seam metal roof"]
  camera: {lens_mm: 35, height: "eye level", perspective: "architectural, straight uprights"}   # 원근 표현 어휘는 미확정·부록 #011번 참고
  lighting: "overcast soft daylight"           # golden_hour|overcast|night|blue_hour (clm_010)
  season_weather: "late spring, light greenery"
  entourage: ["two pedestrians", "no cars"]
  post: "neutral color grading, no vignetting"
negative: "extra buildings, changed roof shape, added floors, text, watermark"
geometry_lock: "Keep the exact geometry, window and door positions, roof shape and count of openings."
references:                # 레퍼런스 이미지 층 (Nano Banana Pro는 최대 14장 — clm_019)
  - refs/ref01.jpg
  - refs/ref02.jpg
backends:
  grok-imagine-image-2.0: {endpoint: /images/edits, mask_polarity: alpha0_edit}
  flux-fill: {mask_polarity: white_regen}
  controlnet: {preprocessor: mlsd, strength: 0.8}     # 직선 건축은 MLSD (clm_066, clm_067)
samples: [samples/s01.jpg]    # pumasi:image 또는 실제 렌더에서 채움
changelog:
  - {date: 2026-09-11, note: "초판"}
```

단순 프리셋 선례(텍스트 층만, 미확정·부록 #016번)를 넘어 위처럼 references/backends/samples/version을 더한다. 재현 강도 단계: 슬롯 프롬프트 → 다중 레퍼런스 → (필요 시) Style LoRA (clm_017).

---

## 8. 게이트·품질 규칙 (제안)

1. **인입 게이트**: 해상도·스타일·씬 이름·camera.json 검사 실패 시 렌더 금지(규약 위반은 재캡처 요청).
2. **기하 경보**: `qa_geometry.py` IoU/SSIM 임계 미달 시 경고 표시 + 사람 판정 필수. 절대 게이트로 쓰지 않음(오라클 비판 (미확정·부록 #006번), 실측 지붕 드리프트 clm_088).
3. **결과 보존**: 임시 URL(imgen.x.ai) 즉시 다운로드 후 meta.json(프롬프트·팩 id·버전·모델·파라미터·usage 비용·입력 해시) 기록 (clm_005).
4. **키 규율**: 라우터 소비자 키만(`insane-router-key-<프로젝트>`, `insane-router-connect`로 발급). OpenAI/Google 원본 키 직접 호출 금지(CLAUDE.md 규칙).
5. **저장소**: `renders/`는 .gitignore, 원본 캡처·스타일팩은 git (clm_008).
6. **변경 이력**: `_meta/changelog.md` 정본 + CLAUDE.md 최근 3행(생성기 표준).

---

## 9. 인터뷰에서 확정할 미결 (Phase 1~3 질문 후보)

| # | 질문 | 왜 갈리는가 | 디폴트(답 없으면) |
|---|---|---|---|
| Q1 | 워크스페이스 이름·설치 위치 | 레지스트리 등재 | `~/insane-render` |
| Q2 | 기하 정밀 모드(ControlNet 로컬/클라우드) 포함 여부 | 로컬 GPU 유무, civitai‑comfy‑nodes 같은 클라우드 노드(clm_068) 사용 의향 | v1은 grok 편집 단일 백엔드, ControlNet은 `--mode controlnet` 스텁만 |
| Q3 | gpt‑image/Gemini 편집 백엔드를 별도 키로 추가할지 | 라우터 불가(clm_087). 종량 과금·CLAUDE.md 확인 규칙 | 추가하지 않음 |
| Q4 | 사용자 PC의 SketchUp 버전·OS | 2026.2 require 예외 전파(clm_061, clm_062)로 Ruby 스크립트 방어 코딩 범위 결정 | 2025~2026, Windows 가정 |
| Q5 | 클라이언트 도면 격리 필요 여부 | `--data-isolation` 켤지 | 켬(70-private) |
| Q6 | 웹툴 v1 범위: 브러시만 vs SAM 클릭 포함 | SAM2 브라우저 제약(clm_052) | 브러시+라쏘만 |
| Q7 | 스타일팩 초기 세트 수와 무드 | 레퍼런스 이미지 확보 필요 | 3팩(주거 외관 흐린날 / 상업 야간 / 클레이 매싱) |
| Q8 | 납품 형식 | 컨택트시트 PDF? 개별 JPG? | JPG + 컨택트시트 PNG |

---

## 10. 다음 단계

1. Phase 0 감사에서 이 세션을 "과거 결정"으로 인용하고 §2 전제는 재질문하지 않는다.
2. Phase 1~3 인터뷰는 §9 8문항을 AskUserQuestion 최대 4문항×2회로.
3. 생성: `python3 scripts/generate_workspace.py <name> development --target-runtime dual --scripts-layer --guard-hook --wrap-command [--data-isolation 70-private] --output-dir $HOME`
4. 생성 후 `assets/stylepacks/`에 §7 스키마 3팩 시드, `scripts/render.py`에 실측 curl 호출(README E2·E3)을 이식, 첫 실제 SketchUp 캡처로 지붕 드리프트 재검증(미확정·부록 #090번) 해소).
