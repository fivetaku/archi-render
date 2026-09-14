# 건축 설계 → SketchUp 샷 캡처 → AI 렌더 워크스페이스 설계용 KB 리서치 — 본문

> 세션: `arch_ai_render_workspace_20260911_1735` · 기준일 2026-09-11 · 소스 327건 · 핵심 주장 92건(verified 63 / unresolved 25 / refuted 4)
> 본문의 단정 문장은 `(clm 번호)`로 표기된 **검증 통과 주장**만 근거로 한다. 미확정·반증 주장은 §8~§9와 `03_appendix_unresolved_refuted.md`에만 나온다.
> 실행 검증(run-confirmed) 6건은 `artifacts/exec_tests/README.md`에 재현 절차·응답·결과 이미지가 있다.

---

## 1. 서론 — 질문과 방법

**질문.** 건축 설계 후 SketchUp 3D 모델을 샷(scene)별로 캡처한 이미지를 입력으로, (1) 원하는 스타일의 사진급 렌더를 기하를 보존하며 만들고, (2) 결과의 특정 영역만 표시해 고치고, (3) "이 느낌"을 재사용 가능한 스타일팩으로 자산화하는 흐름을 Claude Code 에이전트 워크스페이스로 만들려면 무엇을 알아야 하는가.

**방법.** 5축 팬아웃(파이프라인·마스킹/웹툴·스타일팩·서비스 벤치마크·워크스페이스 운영) + 확장 6건 + 미확정 55건 교차검증(8그룹) + 로컬 실행 검증 6건. WebSearch 총 135회(세션 캡 200), 에이전트 19개. 모든 ��심 주장은 claim ledger → `validate_ledger.py` 게이트(독립 조직 2개·1차 소스·반증 검색·표면 다양성)를 통과한 것만 본문에 단정형으로 썼다.

**보고서 유형.** Generic 5섹션을 주제에 맞게 변형: 서론 / 파이프라인 지형 / 영역 수정 / 스타일팩 / 시장 벤치마크 / 운영 사실 / 결론.

---

## 2. 파이프라인 지형 — 캡처를 기하 보존 렌더로 바꾸는 세 계열

### 2.1 세 계열의 성격

| 계열 | 대표 | 기하 보존 | 스타일 자유도 | 실행 형태 | 비용 |
|---|---|---|---|---|---|
| ① ControlNet 조건화 (SD/SDXL/FLUX) | FLUX ControlNet‑Union‑Pro, xinsir SDXL Union, ComfyUI | 강함(강도 0.7~0.9) | 높음 | 로컬 GPU 또는 클라우드 노드 | 오픈웨이트 무료 / 클라우드 크레딧 |
| ② 편집형 멀티모달 모델 | Gemini 이미지(Nano Banana 계열), gpt‑image‑1.5/2, FLUX.1 Kontext, Qwen‑Image‑Edit, grok‑imagine‑image‑2.0 | 중~강(모델별, 프롬프트 의존) | 매우 높음 | API 1콜 | 건당 과금 또는 구독 |
| ③ img2img denoise 조절 | SD img2img | 약함(저 denoise에서만) | 중 | 로컬 | 무료 |

- ControlNet 강도는 통상 0.7~0.9로 두며 0.9 이상은 경직, 0.5~0.6은 설계 이탈 위험이 있고, Depth는 공간관계 보존에, Canny는 파사드·단면 보존에 상대적으로 유리하다 (clm_067).
- 건축 직선 보존에는 Canny보다 MLSD가 유리하고, LineArt는 곡선 평면도용이며, Canny는 치수선·해칭까지 잡으므로 CAD 단계에서 주석을 제거해야 한다 (clm_066).
- FLUX 전용 ControlNet Union(InstantX·Shakker‑Labs)은 canny/tile/depth/blur/pose/gray/low‑quality 7모드만 있고 lineart가 없다. 반면 xinsir SDXL Union은 별도 모델로 lineart 포함 10종 이상을 지원하므로 두 계열을 혼동하면 안 된다 (clm_024).
- Midjourney는 명시적 기하 고정 장치가 없어(`--iw` 참조만) 무드보드·컨셉 단계용이고, 기존 설계 형태를 보존하는 단계에는 ControlNet 파이프라인이 맞다 (clm_069). 오픈소스 ComfyUI 파이프라인은 다수 출처가 "컨셉 단계용, 최종 납품 대체는 미흡"으로 평가하며 UX가 노드 그래프 수준으로 로우레벨이다 (clm_070).

### 2.2 편집형 모델 사실 (2026‑09 기준)

- **OpenAI gpt‑image**: edit API의 mask는 알파 0 영역이 편집 대상, PNG 4MB 미만·원본과 동일 해상도. gpt‑image‑1은 2026‑10‑23, gpt‑image‑1‑mini/1.5/chatgpt‑image‑latest는 2026‑12‑01 지원 종료 예정. gpt‑image‑2는 16 배수 임의 해상도(최대 3840×2160, 종횡비 1:3~3:1)를 받되 2560×1440 초과는 experimental (clm_022). 단, 공식 가이드가 "마스킹은 프롬프트 기반이라 경계를 정확히 따르지 않을 수 있다"고 명시하고 커뮤니티에도 마스크 무시 보고가 다수다 (clm_044).
- **Google Gemini 이미지**: Gemini 2.5 Flash Image("Nano Banana")는 레거시이며 Nano Banana 2 Lite(`gemini-3.1-flash-lite-image`, 2026‑06‑30 발표)로 대체 권고. 편집은 다중 턴(`previous_interaction_id`)으로 스타일·조명·구도를 이어간다 (clm_023). 픽셀 마스크 업로드 없이 자연어로 영역을 지정하는 시맨틱 인페인팅이 1차 방식이다 (clm_045). Nano Banana Pro(Gemini 3 Pro Image)는 최대 14장 레퍼런스를 받아 캐릭터 5명·오브젝트 14개 일관성을 유지한다는 비교가 있다 (clm_019).
- **FLUX.1 Kontext(BFL)**: 크레딧 과금, pro 4크레딧($0.04)·max 8크레딧($0.08), 1크레딧=$0.01. dev는 비상업 오픈웨이트 (clm_021).
- **Qwen‑Image‑Edit**: 20B MMDiT, 2509/2511 업데이트로 정체성·텍스트 일관성 개선, 2026‑02 Qwen‑Image 2.0은 Apache 2.0 (clm_028). 로컬 무료 구동 가능한 유일한 대형 편집 모델 후보다.
- **업스케일**: Real‑ESRGAN API는 이미지당 약 $0.002~0.005, GAN 특성상 디테일을 환각하므로 최종 폴리싱 용도로만 (clm_029).

### 2.3 SketchUp 캡처 측 제약

- SketchUp에는 네이티브 뎁스맵 export가 없다. 실무 대안은 Monochrome/클레이 스타일 + Scene 잠금 + 2000px 이상 PNG export이며, 2025는 생성형 PBR(Normal/AO), 2026.1부터 자체 AI Render가 Web/iPad까지 확장됐다 (clm_026).
- SketchUp→Blender Collada 임포트는 단위가 항상 Imperial로 강제되는 버그(T33437)와 구멍 있는 폴리곤 면 누락(T34552)이 Blender 트래커에 열려 있다 (clm_084). 커뮤니티 컨센서스는 네이티브 3D Z‑depth가 AI 단안 깊이추정보다 가장자리·오클루전 정확도에서 우월하되, 원본 모델이 없을 때만 AI 추정이 대안이라는 것이다 (clm_086).
- 다중 샷 재질 일관성은 IP‑Adapter(+InstantStyle)+LoRA 조합이 쓰이지만 MV‑Adapter 논문이 멀티뷰 LoRA와 스타일 LoRA가 직교하지 않음을 지적하고, 실무자도 IPAdapter만으로는 동일 객체의 다른 뷰가 불충분하다고 보고한다 (clm_030).

### 2.4 로컬 실행 검증 — 우리 환경에서 실제로 되는 것

- insane‑router `/models`의 이미지 출력 모델은 openai/gpt‑image, gpt‑image‑1.5, gpt‑image‑2(입력 text만), x‑ai/grok‑imagine‑image, ‑image‑2.0(입력 text+image), ‑image‑quality이며 pricing은 전부 0(구독 경로). Gemini 이미지 모델은 목록에 없다 (clm_091).
- `/images/edits`는 openai/gpt‑image‑2를 HTTP 501로 거부한다("image edits only supported for x‑ai/*"). 라우터 경유 gpt‑image는 생성만 가능하다 (clm_087).
- `x-ai/grok-imagine-image-2.0` 편집은 512px 선화 파사드를 17.7초에 1024×1024 사진급 렌더로 바꾸며 창 2개·문·벽 비례를 보존했다. 박공 지붕은 모임지붕형으로 드리프트했다 (clm_088).
- 같은 모델은 RGBA 마스크(알파 0 = 편집)를 받아 마스크 영역만 재생성했다. 왼쪽 창만 아치창이 되고 나머지 선화는 유지됐고, 512px 입력이 1024px로 자동 업스케일됐다 (clm_089).
- 이 맥에는 SketchUp이 없고 Blender.app만 있다. 캡처 자동화는 이 맥에서 실측 불가하며 워크스페이스는 사용자 PC의 SketchUp이 내보낸 이미지 폴더를 입력으로 받는 구조가 기본이다 (clm_092).

> 함의: **0원 기본 백엔드 = 라우터 x‑ai grok‑imagine‑image‑2.0 편집 API**(img2img + 마스크 모두 실측). gpt‑image·Gemini 편집은 라우터로 불가하므로, 필요 시 별도 키/서비스 결정이 필요하다(§7 결정 포인트).

---

## 3. 영역 수정 — 마스크 규격과 브라우저 마스킹 웹툴

### 3.1 벤더별 마스크 규격은 세 갈래

| 방식 | 벤더 | 규격 |
|---|---|---|
| (a) 픽셀 마스크(사용자가 그림) | OpenAI gpt‑image, Stability, FLUX.1 Fill, grok‑imagine(실측), Midjourney Editor | 알파 또는 흑백, 원본과 동일 크기 |
| (b) 시맨틱(자연어) | Google Gemini 이미지 계열 | 마스크 없음, 프롬프트로 영역 지정 |
| (c) 캔버스 배치형 아웃페인팅 | 다수 | 픽셀 오프셋 |

이 세 갈래 분류는 2026 기준 컨센서스다 (clm_048). 세부:
- Stability `/v2beta/stable-image/edit/inpaint`는 `mode=mask`(마스크 파일 또는 알파) 와 `mode=search`(`search_prompt`만으로 자동 탐지) 두 경로 (clm_046).
- FLUX.1 Fill은 (1) 원본+별도 흑백 마스크(검정=보존, 흰색=재생성) 또는 (2) 알파 포함 단일 PNG/WebP(투명=재생성) 두 방식, 필드는 prompt/image/mask/steps/guidance/output_format/safety_tolerance (clm_047).
- Ideogram 3.0의 캐릭터 레퍼런스 마스크는 인페인트 마스크와 별개 파라미터(그레이스케일, 1개만) (clm_058). Ideogram 인페인트 마스크 자체의 극성(검정=수정)은 미확정으로 남았다(§8).
- **극성이 벤더마다 다르다**(알파 0 = 편집 vs 흰색 = 재생성 vs 검정 = 수정). 웹툴은 내부 표준 마스크 1개를 유지하고 벤더별 변환 레이어를 두어야 한다.

### 3.2 참고할 로컬 UI와 UX 패턴

- IOPaint(구 lama‑cleaner, Apache 2.0)는 `pip install iopaint` 후 `iopaint start --model=lama --device=cpu --port=8080`으로 즉시 웹UI, Erase/Replace/Draw Text/Outpaint 제공 (clm_049).
- ComfyUI는 LoadImage 우클릭 MaskEditor → VAE Encode(for Inpainting)이 기본이고, "Only Masked" 크롭+컨텍스트 패딩은 커스텀 노드(InpaintCropImproved, Crop By Mask)로 구현된다 (clm_050).
- Krita AI Diffusion은 마스크 주변 컨텍스트를 함께 태우고 Settings > Diffusion > Selection Padding으로 크기를 조절하며 커스텀 컨텍스트 마스크를 저장·재사용한다. 2026‑08 v1.53.0에 세그멘테이션 컨트롤 레이어 추가 (clm_051). 브라우저 웹툴이 가장 직접 참고할 UX다.
- 품질 파이프라인 컨센서스: 마스크 팽창 → 경계 페더링 → 컨텍스트 크롭 후 다중 패스(마지막은 낮은 denoise) → 구조 보존 필요 시 ControlNet 병행. denoise는 완전 교체 0.7~1.0, 리파인 0.4~0.6, 미세조정 0.2~0.3 (clm_054).

### 3.3 브라우저 구현 재료

- 마스크 브러시 React 컴포넌트: react‑canvas‑masker(react‑mask‑editor 포크, undo/redo·zoom·dataURL 콜백·기존 마스크 재로드)와 원본 react‑mask‑editor(1비트 흑백) (clm_053).
- SAM2 클릭 세그멘테이션은 브라우저에서 실현 가능: Labelbox sam2‑web(onnxruntime‑web, 인코더 서버/디코더 브라우저), lucasgelfond/webgpu‑sam2(완전 클라이언트, WebGPU·dev build onnxruntime 필요, 입력 1024×1024 고정·출력 256×256) (clm_052). 좌표 재매핑·업스케일 로직이 필수다.
- 피드백 마크업: Annotorious(BSD‑3)·marker.js(v2 오픈소스, v3 유료)가 실사용 가능하지만 archviz용 "핀 코멘트+버전 비교+승인 게이트" 오픈소스 완제품은 없다 (clm_007).

---

## 4. 스타일팩 — 차원, 재현 기법, 스키마 근거

### 4.1 스타일을 이루는 차원

- 핵심 차원: 조명·시간대(golden hour/overcast/night/blue hour), 날씨·계절·식생, 카메라(렌즈mm·아이레벨·조리개), 엔투라지(인물·차량·주변), 후처리(색보정·필름룩), 렌더 무드 (clm_010).
- 무드 유형: 사진사실(PBR), 영화적, 회화적, 수채화(초기 컨셉), 다이어그램(axonometric·색코딩), 콜라주, 화이트박스/클레이(매싱 검토) — 단계별로 혼용된다 (clm_012).
- 실무 렌더러의 명명 체계를 스키마 용어로 차용할 수 있다: Enscape Visual Settings는 Main/Image/Atmosphere/Sky/Output 5탭, Atmosphere에 Fog Intensity·Fog Height·Clouds (clm_078); Style Mode 드롭다운은 White/Polystyrol/Light View/Sketch(Pen·Pencil·Colored Pencil)/Watercolor, 2025 4.13.0에 Selective White Mode·Invert Appearance 추가 (clm_079); Settings Presets로 전체를 .json으로 저장·불러오기 (clm_080). V‑Ray Physical Camera의 White Balance는 색조만 반영하고 밝기는 무시한다 (clm_081).
- 구조화 프롬프트 권장 레이어: [샷타입]+[건물+재질 1~2]+[카메라: 렌즈·높이·각도]+[시간대/광량]+[엔투라지 1~2]+[출력 비율], 슬롯이 6~7개를 넘으면 충돌한다는 경험칙 (clm_020).

### 4.2 재현 기법 비교

| 기법 | 일관성 | 비용/난이도 | 비고 |
|---|---|---|---|
| 슬롯 프롬프트 템플릿 | 약 | 최저 | 모든 백엔드 공통, 스타일팩의 기본층 |
| 다중 레퍼런스 입력(Nano Banana Pro 14장 등) | 중~강 | 낮음, API 콜 | 학습 불필요 (clm_019) |
| Midjourney `--sref`/`--sw` | 중 | 낮음 | 색·질감·조명만 전이, `--sw` 0~1000(기본 100), style code는 블랙박스 (clm_013) |
| IP‑Adapter(Plus) | 중~강 | 중 | SD1.5/SDXL 검증(CLIP‑I 0.828), FLUX는 별도 어댑터·다른 워크플로우 (clm_014) |
| FLUX Redux | 중~강 | 중 | SigLIP→T5 정렬, ComfyUI StyleModelApply, 다중 레퍼런스 체이닝 (clm_015) |
| Style LoRA 학습 | 강 | 최고 | 15~60장(BFL은 40장 초과 시 희석 경고), lr 1e‑4~2e‑4, rank 16~64, 24GB GPU 1~3h, 클라우드 $0.3~2 (clm_017) |

### 4.3 스키마 근거

기존 SD UI의 단순 스타일 프리셋 선례(텍스트 층만 있음, 미확정·부록 #016번)를 넘어 archviz 스타일팩은 레퍼런스 이미지 배열·모델별 파라미터·예시 결과·버전을 더한 확장 스키마가 필요하다. 구체 제안은 `02_workspace_design_inputs.md` §4.

---

## 5. 시장 벤치마크 — 상용 도구가 이미 하는 것

### 5.1 두 계열 + 렌더러 내장형

- **모델 인식형 플러그인**: Veras는 geometry override 슬라이더, Render Selection(영역 재생성), Render Same Seed(다샷 일관성)를 제공한다 (clm_032). 재질 지정은 프롬프트 기반이라 스펙 보장은 안 되고, Arko AI는 기하 충실도 중간, Vizcom은 스케치→렌더 강점 (clm_027). ArkoAI 실측은 "SketchUp Diffusion과 Veras 사이"이며 평지붕 파라펫이 난간으로 바뀌는 식의 드리프트가 보고된다 (clm_074). PromeAI가 뷰포트 조건화 아키텍처인지는 근거가 없다 (clm_075).
- **Veras의 2026 전환**: 2026‑02 Veras 4.0 Render Engine 7은 Google Gemini 3 Pro Image(Nano Banana Pro)를 그대로 채택했고, Chaos가 "Veras v7과 독립형 Nano Banana Pro는 동일 기반 모델"이라고 명시한다 (clm_072). 구엔진(RE6 이하)은 제3자가 ControlNet 유사로 묘사하지만 공식 명시는 없는 블랙박스다 (clm_073). RE7 도입 시 쿼터제 상위 티어(Creative Boost)가 생기고 구엔진은 무제한으로 남았으며, 당시 Named $59/월(연 $29/월)·Floating·Student 가격표는 2026‑05‑27 Chaos Credits 개편으로 구가격이 됐다 (clm_076, clm_031).
- **렌더러 내장 AI**: Chaos AI Enhancer는 인물·식생·대면적 텍스처만 향상, 최소 512px, Enscape 2048², V‑Ray/Corona 4096² 한도, Chaos Credits 소비 (clm_041).
- **가격이 확정된 곳**: Rendair 학생 €7.60/월, Pro €39/월(1,500크레딧, 상업 라이선스) (clm_037). 그 외 다수 도구의 가격은 1차 소스 미도달 또는 충돌로 미확정(§8 목록), Vizcom 가격 주장은 반증됨(§9).

### 5.2 차용할 UX 패턴

1. geometry override(창의성) 슬라이더 — 우리 파이프라인에서는 ControlNet 강도 또는 편집 모델 프롬프트 강도로 매핑.
2. Render Selection — 마스크 인페인팅 커맨드.
3. Same Seed — 시드 고정 다샷 일관성(실사용 백엔드의 seed 지원은 미확정, §8).
4. "모델 캡처 기반"과 "손스케치 입력형"을 별 모드로 분리.

---

## 6. 워크스페이스 운영 사실 — 자동화·비용·QA·리비전

- **SketchUp 자동화 한계**: Ruby API에 헤드리스 배치 모드가 없다. `-RubyStartup`으로 시작 스크립트는 가능하지만 GUI가 항상 떠 있어야 하고 macOS에서 터미널 포커스 시 멈추는 결함이 있다 (clm_001). 따라서 "사용자 1회 트리거 → 폴더 덤프 → 워크스페이스가 폴더를 소비"가 기본 아키텍처다.
- **export API**: `View#write_image`는 filename/width/height/antialias/compression과 해시 옵션 transparent·scale_factor, 반환 boolean, 포맷 png/jpg/jpeg/gif/bmp/tif (clm_002). 종횡비 불일치 해상도에서 이미지 손상 리그레션 보고는 단일 출처라 미확정(§8)이지만 방어 코드는 넣을 가치가 있다.
- **2026.2 Ruby 변경**: `Sketchup.load/require`가 파일 미발견 시 LoadError를 raise하도록 바뀌었고 (clm_061), 확장이 직접 rescue하지 않으면 로드 실패 시 확장 전체가 죽을 수 있는 breaking change다 (clm_062). `.rbs` 건너뛰기는 2023.0부터의 기존 사양 (clm_064).
- **비용 기록**: xAI·OpenRouter 등은 usage 객체에 USD 비용(xAI `cost_in_usd_ticks`)을 직접 반환하므로 사이드카 JSON에 그대로 적재할 수 있다 (clm_005). 실측에서도 grok 응답 usage에 `cost_in_usd_ticks: 700000000`이 왔다(구독 경로라 실과금 0).
- **리비전·자산**: 업계는 수동 파일명 ��신 R00/R01 자동 태그와 clay→internal→client‑facing→approval 단계형 파이프라인으로 이동 중이다 (clm_009). Git LFS는 사람이 만든 원본에만 쓰고 AI 생성 산출물은 .gitignore + 외부 스토리지로 분리하는 것이 권장 관행 (clm_008).
- **클라우드 ControlNet**: civitai‑comfy‑nodes는 로컬 GPU 없이 canny·mlsd·depthAnything·zoeDepth 등 프리프로세서를 서버사이드로 돌리고 ControlNet 체이닝을 지원한다(2026‑06‑18 활성) (clm_068).

---

## 7. 결론과 설계 결정 포인트

1. **백엔드 기본값은 라우터 grok‑imagine‑image‑2.0 편집 API**(img2img·마스크 실측, 0원). ControlNet 로컬 파이프라인은 "기하 정밀 모드"로 2순위, gpt‑image/Gemini 편집은 라우터 불가라 별도 결정 필요 (clm_087, clm_088, clm_089, clm_091).
2. **입력은 SketchUp이 내보낸 폴더**. 헤드리스 불가·로컬 SketchUp 부재로 완전 자동화는 설계 대상이 아니다 (clm_001, clm_092). 캡처 규약: 클레이/모노크롬 + Scene 잠금 + 2000px 이상 (clm_026).
3. **기하 드리프트는 실제 위험**. 실측에서 지붕 형태가 바뀌었고 상용 도구(ArkoAI)도 파라펫 드리프트를 보인다 (clm_088, clm_074). 엣지 비교 QA는 경보용으로, 최종 판정은 사람이.
4. **마스크는 내부 표준 1개 + 벤더 변환층**. 극성이 벤더마다 다르다 (clm_047, clm_022, clm_048).
5. **스타일팩은 슬롯 프롬프트 층 + 레퍼런스 이미지 층 + 모델별 파라미터 층 + 버전**. 재현 강도는 프롬프트 → 다중 레퍼런스 → LoRA 순으로 단계 상승 (clm_020, clm_019, clm_017).
6. **시장은 범용 멀티모달 모델 위 도메인 래퍼로 이동**(Veras→Gemini). 자체 diffusion 파이프라인보다 "최신 모델 + 우리 도메인 래퍼(캡처 규약·스타일팩·마스크·리비전)"가 유지비 면에서 유리하다 (clm_072).

### Confidence
- 높음(run‑confirmed 5건 + 공식 문서 다중 확인): 라우터 능력·제약, OpenAI/BFL/Stability 마스크 규격, SketchUp API 사실, Veras 엔진 전환.
- 중간(doc‑confirmed, 2차 소스 비중 큼): 스타일 재현 기법 비교, UX 패턴, 인페인팅 품질 파이프라인.
- 낮음/미확정: 상용 도구 가격(대부분 §8), 임베딩 기반 일관성 측정법, Ideogram 규격, seed 지원.

---

## 8. 미확정 (Unresolved) — 본문 단정 금지, 25건

독립 출처 부족·1차 소스 미도달·충돌 미해소로 남은 주장. 전체 목록과 사유는 `03_appendix_unresolved_refuted.md`. 설계에 영향이 큰 것만 요약:
- write_image 종횡비 불일치 손상 리그레션 (clm_003), 카메라 JSON 직렬화 패턴·2026.0 Page 수정 undoable (clm_004) — 공식 문서 1조직만 확인.
- tilt‑shift 단어 오독 팁 (clm_011), Fooocus 스타일 스키마 (clm_016), DINO 스타일 지표 (clm_018), denoise 범위 (clm_025).
- LookX (clm_033)·ArkoAI (clm_034)·mnml.ai (clm_035)·PromeAI (clm_036)·MyArchitectAI (clm_038)·D5 (clm_040) 가격·기능 — 공식 페이지 재확인 전 인용 금지.
- Ideogram 인페인트 엔드포인트·마스크 극성·용량 (clm_055, clm_056, clm_057, clm_059).
- Blender Z‑pass 절차 (clm_083), ComfyUI 건축 튜토리얼 (clm_065), V‑Ray 노출 3모드 (clm_077), Chaos AI Upscaler (clm_042), OpenAI mask 재서술 (clm_043), 2026.2 require 예외 전파 (clm_060), Ruby 3.4 예고 (clm_063), Canny‑SSIM 오라클 비판 (clm_006), 음영 매싱 지붕 드리프트 실험 (clm_090).

## 9. 반증 (Refuted) — 4건

- Vizcom 가격 구조 주장 (clm_039): 공식 pricing은 Starter 무료 800크레딧 / Education / Professional $49 / Enterprise. "Pro $18~29·Studio" 티어는 존재하지 않음.
- AIA 62%·RIBA 73% 채택 수치 (clm_071): 오귀속. 인용 금지.
- "ComfyUI 아키비즈 기본 경로가 AI 깊이추정" (clm_082): 원문은 네이티브 depth export가 기본, AI 추정은 보조.
- "FBX export는 서드파티 플러그인 필요" (clm_085): FBX export는 Pro/Studio 네이티브 기능(무료 웹판 제외).

---

## 10. 부록 — 전체 주장 소스 색인 (Verified·Unresolved·Refuted)

모든 핵심 주장 92건의 상태와 근거 소스 id. 상태가 unresolved/refuted인 행은 본문 근거가 아니다. 상세는 `../sources/bibliography.md`.

| 주장 | 상태 | 근거 소스 |
|---|---|---|
| clm_001 | verified | src_008([forums.sketchup.com](https://forums.sketchup.com/t/opening-and-closing-sketchup-using-command-line-prompts/188794)), src_009([sketchucation.com](https://community.sketchucation.com/topic/121859/sketchup-command-line-rubystartup)), src_006([help.sketchup.com](https://help.sketchup.com/en/sketchup/developing-tools-sketchup-ruby-api-and-console)) |
| clm_002 | verified | src_001([ruby.sketchup.com](https://ruby.sketchup.com/Sketchup/View.html)), src_004([ruby.sketchup.com](https://ruby.sketchup.com/file.exporter_options.html)), src_227([community.sketchucation.com](https://community.sketchucation.com/topic/123530/image-export-independent-width-height-resolution)), src_229([github.com](https://github.com/SketchUp/api-issue-tracker/issues/545)), src_224([forums.sketchup.com](https://forums.sketchup.com/t/code-example-saving-iso-views-to-png-image-files/56762)) |
| clm_003 | unresolved | src_007([forums.sketchup.com](https://forums.sketchup.com/t/write-image-corruption/343838)), src_221([forums.sketchup.com](https://forums.sketchup.com/t/2026-issues/340821)), src_222([forums.sketchup.com](https://forums.sketchup.com/t/artifacts/345540)), src_223([forums.sketchup.com](https://forums.sketchup.com/t/view-write-image-png-file-quality-is-not-great/225648)) |
| clm_004 | unresolved | src_010([forums.sketchup.com](https://forums.sketchup.com/t/how-can-i-save-and-restore-the-camera/241655)), src_002([ruby.sketchup.com](https://ruby.sketchup.com/Sketchup/Camera.html)), src_003([ruby.sketchup.com](https://ruby.sketchup.com/Sketchup/Page.html)), src_219([help.sketchup.com](https://help.sketchup.com/en/release-notes/sketchup-desktop-20260)) |
| clm_005 | verified | src_013([openrouter.ai](https://openrouter.ai/blog/announcements/image-api/)), src_014([docs.x.ai](https://docs.x.ai/developers/cost-tracking)) |
| clm_006 | unresolved | src_016([arxiv.org](https://arxiv.org/html/2608.00083)), src_018([arxiv.org](https://arxiv.org/pdf/2601.16645)), src_320([arxiv.org](https://arxiv.org/pdf/2511.04753)) |
| clm_007 | verified | src_023([annotorious.dev](https://annotorious.dev/)), src_025([github.com](https://github.com/ailon/markerjs3)), src_020([archvizreview.com](https://www.archvizreview.com/)) |
| clm_008 | verified | src_028([docs.gitlab.com](https://docs.gitlab.com/topics/git/lfs/)), src_029([learn.github.com](https://learn.github.com/well-architected/architecture/recommendations/scaling-git-repositories/when-to-use-git-lfs/)), src_030([grizzlypeaksoftware.com](https://www.grizzlypeaksoftware.com/library/managing-large-files-in-git-lfs-and-alternatives-5es04krf)) |
| clm_009 | verified | src_020([archvizreview.com](https://www.archvizreview.com/)), src_021([diversion.dev](https://www.diversion.dev/architectural-visualization)) |
| clm_010 | verified | src_031([ronenbekerman.com](https://www.ronenbekerman.com/showcase/the-golden-hour-by-michael-khoo/)), src_032([goldenstudio.org](https://goldenstudio.org/architectural-rendering-styles)), src_062([blog.chaos.com](https://blog.chaos.com/ai-architecture-prompts)) |
| clm_011 | unresolved | src_061([prompt-architects.com](https://www.prompt-architects.com/blog/283-30-ai-prompts-for-architectural-rendering-and-visualisation)), src_033([archigpt.ai](https://www.archigpt.ai/blogs/architectural-rendering-prompts)), src_231([aipromptlibrary.app](https://www.aipromptlibrary.app/blog/miniature-world-ai-prompts)), src_232([zsky.ai](https://zsky.ai/blog/ai-camera-angle-prompts)) |
| clm_012 | verified | src_032([goldenstudio.org](https://goldenstudio.org/architectural-rendering-styles)), src_063([myarchitectai.com](https://www.myarchitectai.com/blog/rendering-styles)), src_065([losangelesrendering.com](https://losangelesrendering.com/blog/rendering-styles-guide)) |
| clm_013 | verified | src_034([midlibrary.io](https://midlibrary.io/midguide/midjourney-style-reference-sref-for-photographers)), src_035([prompt-architects.com](https://prompt-architects.com/blog/214-style-references-in-midjourney-sref-explained)), src_036([aikizi.com](https://aikizi.com/learn/blog/midjourney-style-codes-explained)), src_236([docs.midjourney.com](https://docs.midjourney.com/hc/en-us/articles/32180011136653-Style-Reference)), src_233([styleref.io](https://styleref.io/blog/midjourney-style-reference)), src_234([promptsref.com](https://promptsref.com/guide/How-to-Use-Style-Reference-and-Style-Reference-Codes)), src_235([everestx.com](https://www.everestx.com/tutorials/midjourney/midjourney-style-references-sref-codes)), src_237([midlibrary.io](https://midlibrary.io/midguide/deep-dive-into-midjourney-sref-codes)) |
| clm_014 | verified | src_037([getimg.ai](https://getimg.ai/guides/guide-to-ip-adapters)), src_038([huggingface.co](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)), src_040([huggingface.co](https://huggingface.co/InstantX/FLUX.1-dev-IP-Adapter/commits/28c20b99063062217ed54fdfb0320e7208f07425)), src_238([arxiv.org](https://arxiv.org/pdf/2308.06721)), src_239([openlaboratory.com](https://openlaboratory.com/models/control-sdxl-ipadapter/)) |
| clm_015 | verified | src_041([runware.ai](https://runware.ai/docs/en/image-inference/flux-tools)), src_042([comfy.org](https://comfy.org/workflows/flux_redux_model_example-52dd3f09bb59/)), src_044([arxiv.org](https://arxiv.org/pdf/2506.15742)) |
| clm_016 | unresolved | src_045([github.com](https://github.com/lllyasviel/Fooocus/blob/main/modules/sdxl_styles.py)), src_046([github.com](https://github.com/lllyasviel/Fooocus/blob/main/sdxl_styles/sdxl_styles_fooocus.json)), src_048([github.com](https://github.com/DisasterofPuppets/SDXL-CSV-to-JSON/)) |
| clm_017 | verified | src_049([aiofm.info](https://aiofm.info/en/guides/lora-complete-guide)), src_050([sanj.dev](https://sanj.dev/post/lora-training-requirements-guide/)), src_051([localaimaster.com](https://localaimaster.com/blog/image-lora-training-local-guide)), src_240([runcomfy.com](https://www.runcomfy.com/trainer/ai-toolkit/flux-2-dev-lora-training)), src_241([docs.bfl.ml](https://docs.bfl.ml/flux_2/flux2_klein_training_example)), src_242([blog.fal.ai](https://blog.fal.ai/training-flux-2-loras)), src_243([apatero.com](https://apatero.com/blog/how-to-train-flux-2-lora-complete-fine-tuning-guide-2025)) |
| clm_018 | unresolved | src_052([arxiv.org](https://arxiv.org/pdf/2511.13002)), src_053([arxiv.org](https://arxiv.org/pdf/2504.06144)), src_054([arxiv.org](https://arxiv.org/pdf/2501.02064)), src_056([arxiv.org](https://arxiv.org/html/2605.22469)), src_244([arxiv.org](https://arxiv.org/pdf/2406.16855)) |
| clm_019 | verified | src_057([ai.google.dev](https://ai.google.dev/gemini-api/docs/image-generation)), src_058([deepmind.google](https://deepmind.google/models/gemini-image/pro/)), src_059([help.apiyi.com](https://help.apiyi.com/en/nano-banana-vs-gpt-image-2-multi-reference-editing-en.html)) |
| clm_020 | verified | src_061([prompt-architects.com](https://www.prompt-architects.com/blog/283-30-ai-prompts-for-architectural-rendering-and-visualisation)), src_060([dualview.ai](https://www.dualview.ai/blog/guides/json-prompts-ai-image.html)) |
| clm_021 | verified | src_075([docs.bfl.ml](https://docs.bfl.ml/quick_start/pricing)), src_076([bfl.ai](https://bfl.ai/pricing)), src_077([together.ai](https://www.together.ai/models/flux-1-kontext-pro)) |
| clm_022 | verified | src_072([developers.openai.com](https://developers.openai.com/api/reference/python/resources/images/methods/edit)), src_073([developers.openai.com](https://developers.openai.com/api/docs/models/gpt-image-1)), src_293([developers.openai.com](https://developers.openai.com/api/docs/deprecations)), src_294([therouter.ai](https://therouter.ai/news/openai-legacy-model-deprecation-wave-july-october-2026/)), src_295([kingy.ai](https://kingy.ai/ai-launch-tracker/older-openai-gpt-image-models-will-leave-the-api-december-1/)), src_296([llmlatency.dev](https://llmlatency.dev/migrate/openai-gpt-image-1)), src_297([docs.apiyi.com](https://docs.apiyi.com/en/news/gpt-image-2-launch)), src_298([framia.converge.ai](https://framia.converge.ai/page/en-US/news/gpt-image-2-resolution)), src_299([yingtu.ai](https://yingtu.ai/en/blog/gpt-image-2-4k-image-generation)), src_300([en.wikipedia.org](https://en.wikipedia.org/wiki/GPT_Image)) |
| clm_023 | verified | src_057([ai.google.dev](https://ai.google.dev/gemini-api/docs/image-generation)), src_070([blog.google](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-omni-flash-nano-banana-2-lite/)) |
| clm_024 | verified | src_066([huggingface.co](https://huggingface.co/Shakker-Labs/FLUX.1-dev-ControlNet-Union-Pro)), src_067([huggingface.co](https://huggingface.co/InstantX/FLUX.1-dev-Controlnet-Union/discussions/11)), src_069([insiderllm.com](https://insiderllm.com/guides/controlnet-guide-beginners/)), src_311([huggingface.co](https://huggingface.co/InstantX/FLUX.1-dev-Controlnet-Union-alpha)), src_312([huggingface.co](https://huggingface.co/xinsir/controlnet-union-sdxl-1.0)), src_313([openlaboratory.com](https://openlaboratory.com/models/control-sd15-mlsd/)) |
| clm_025 | unresolved | src_082([stable-diffusion-art.com](https://stable-diffusion-art.com/denoising-strength/)), src_083([stable-diffusion-art.com](https://stable-diffusion-art.com/depth-to-image/)) |
| clm_026 | verified | src_080([community.sketchucation.com](https://community.sketchucation.com/topic/97647/depth-maps-from-su)), src_081([help.sketchup.com](https://help.sketchup.com/en/release-notes/sketchup-desktop-20250)) |
| clm_027 | verified | src_088([justnecessary.substack.com](https://justnecessary.substack.com/p/ai-rendering-for-sketchup-2026-an-52a)), src_089([d5render.com](https://www.d5render.com/posts/best-ai-sketchup-plugins-2026)) |
| clm_028 | verified | src_078([github.com](https://github.com/QwenLM/Qwen-Image)), src_079([build.nvidia.com](https://build.nvidia.com/qwen/qwen-image-edit)) |
| clm_029 | verified | src_084([modelslab.com](https://modelslab.com/real-esrgan)), src_085([wavespeed.ai](https://wavespeed.ai/docs/docs-api/wavespeed-ai/real-esrgan)), src_314([arxiv.org](https://arxiv.org/abs/2107.10833)), src_315([openaccess.thecvf.com](https://openaccess.thecvf.com/content/ICCV2021W/AIM/papers/Wang_Real-ESRGAN_Training_Real-World_Blind_Super-Resolution_With_Pure_Synthetic_Data_ICCVW_2021_paper.pdf)), src_316([pricepertoken.com](https://pricepertoken.com/fal-ai-pricing)) |
| clm_030 | verified | src_086([arxiv.org](https://arxiv.org/pdf/2412.03632)), src_038([huggingface.co](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)), src_087([comfyui.org](https://comfyui.org/en/stable-diffusion-xl-architecture-visuals)) |
| clm_031 | verified | src_090([evolvelab.io](https://www.evolvelab.io/veras)), src_098([bimtoolshub.com](https://bimtoolshub.com/veras-by-evolvelab)), src_278([rendershop.ai](https://rendershop.ai/veras-review)), src_279([chaos.com](https://www.chaos.com/veras)), src_266([blog.chaos.com](https://blog.chaos.com/chaos-credits)), src_280([digitalproduction.com](https://digitalproduction.com/2026/05/29/chaos-puts-veras-everywhere/)), src_281([chaos.com](https://www.chaos.com/press/veras-ai-architecture-enscape-vray-corona)), src_282([support.chaos.com](https://support.chaos.com/hc/en-us/articles/46887808239633-When-do-the-new-prices-take-effect)) |
| clm_032 | verified | src_090([evolvelab.io](https://www.evolvelab.io/veras)), src_278([rendershop.ai](https://rendershop.ai/veras-review)) |
| clm_033 | unresolved | src_101([toolsforhumans.ai](https://www.toolsforhumans.ai/ai-tools/lookx-ai)), src_099([myarchitectai.com](https://www.myarchitectai.com/blog/sketchup-ai-rendering)), src_283([lookx.ai](https://www.lookx.ai/price.html)), src_284([lookx.ai](https://lookx.ai/)) |
| clm_034 | unresolved | src_102([sourceforge.net](https://sourceforge.net/software/product/ArkoAI/)), src_103([rendero.ai](https://www.rendero.ai/rendero-vs-arkoai)), src_285([aicreativeblog.com](https://aicreativeblog.com/how-to-use-arko-ai-rendering-guide/)), src_286([arko.ai](https://www.arko.ai/pricing)), src_287([promeai.pro](https://www.promeai.pro/blog/2024/08/29/arko-ai/)) |
| clm_035 | unresolved | src_105([therundown.ai](https://www.therundown.ai/tools/mnmlai)), src_091([mnml.ai](https://mnml.ai/ai-rendering-software)), src_288([mnml.ai](https://mnml.ai/pricing)), src_289([rendershop.ai](https://rendershop.ai/mnml-ai-review)), src_290([toolsforhumans.ai](https://www.toolsforhumans.ai/ai-tools/mnml-ai)) |
| clm_036 | unresolved | src_106([therundown.ai](https://www.therundown.ai/tools/promeai)), src_107([dupple.com](https://dupple.com/tools/promeai)), src_248([aihungry.com](https://aihungry.com/tools/promeai/pricing)), src_321([autogpt.net](https://autogpt.net/ai-tool/promeai/)), src_322([bestfreeaitools.io](https://bestfreeaitools.io/ai-tools/promeai-review/)), src_323([www.techjockey.com](https://www.techjockey.com/detail/promeai)) |
| clm_037 | verified | src_110([rendershop.ai](https://rendershop.ai/rendair-ai-review)), src_111([smartaiforwork.com](https://www.smartaiforwork.com/tools/rendair-ai)), src_247([rendair.ai](https://rendair.ai/faq/understanding-rendair-ai-plans-and-pricing-tiers)), src_109([tooliverse.ai](https://tooliverse.ai/tools/rendair)), src_324([www.colormango.com](https://www.colormango.com/product/rendair-ai_160270.html)) |
| clm_038 | unresolved | src_113([softwareadvice.com](https://www.softwareadvice.com/product/517301-MyArchitectAI/)), src_114([getapp.com](https://www.getapp.com/emerging-technology-software/a/myarchitectai/)), src_245([myarchitectai.com](https://www.myarchitectai.com/pricing)), src_252([navgood.com](https://www.navgood.com/en/tool-details/myarchitectai-4f7de)) |
| clm_039 | refuted | src_117([toolradar.com](https://toolradar.com/tools/vizcom)), src_118([archpulse.co](https://www.archpulse.co/blog/vizcom-review)), src_246([vizcom.com](https://vizcom.com/pricing)) |
| clm_040 | unresolved | src_120([capterra.com](https://www.capterra.com/p/10005615/D5-Render/)), src_095([d5render.com](https://www.d5render.com/posts/render-pricing-d5-plans)), src_122([myarchitectai.com](https://www.myarchitectai.com/blog/d5-render-pricing)), src_121([g2.com](https://www.g2.com/products/d5-render/pricing)), src_253([visualizee.ai](https://visualizee.ai/blog/d5-render-pricing)), src_325([checkthat.ai](https://checkthat.ai/brands/d5-render/pricing)), src_326([www.archivinci.com](https://www.archivinci.com/blogs/d5-render-pricing-2026)) |
| clm_041 | verified | src_092([blog.chaos.com](https://blog.chaos.com/introducing-chaos-ai-enhancer)), src_094([chaos.com](https://www.chaos.com/enscape/features)), src_262([chaos.com](https://www.chaos.com/credits)), src_263([design8.freshdesk.com](https://design8.freshdesk.com/en/support/solutions/articles/47001301980-chaos-credit-system)), src_264([nti-group.com](https://www.nti-group.com/uk/products/other-products/chaos/credits/)) |
| clm_042 | unresolved | src_093([blog.chaos.com](https://blog.chaos.com/chaos-ai-upscaler)), src_265([chaos.com](https://www.chaos.com/get-more)), src_266([blog.chaos.com](https://blog.chaos.com/chaos-credits)) |
| clm_043 | unresolved | src_072([developers.openai.com](https://developers.openai.com/api/reference/python/resources/images/methods/edit)), src_124([cookbook.openai.com](https://cookbook.openai.com/examples/generate_images_with_gpt_image)) |
| clm_044 | verified | src_123([developers.openai.com](https://developers.openai.com/api/docs/guides/image-generation)), src_125([community.openai.com](https://community.openai.com/t/help-with-images-edit-mask-not-constraining-edit-to-specific-area/1351283)), src_301([docs.apiyi.com](https://docs.apiyi.com/en/api-capabilities/gpt-image-2/mask-editing)), src_302([community.openai.com](https://community.openai.com/t/gpt-image-2-masking-issue/1379510)) |
| clm_045 | verified | src_126([cloud.google.com](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana)), src_058([deepmind.google](https://deepmind.google/models/gemini-image/pro/)), src_303([developers.googleblog.com](https://developers.googleblog.com/introducing-gemini-2-5-flash-image/)), src_304([blog.google](https://blog.google/innovation-and-ai/technology/developers-tools/build-with-nano-banana-2/)), src_305([docs.cloud.google.com](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/samples/generativeaionvertexai-imagen-edit-image-inpainting-insert-mask)), src_306([higgsfield.ai](https://higgsfield.ai/blog/Top-Editing-Tool-in-2025-Nano-Banana-Pro-Inpaint)), src_307([fal.ai](https://fal.ai/models/fal-ai/gemini-3-pro-image-preview/edit)) |
| clm_046 | verified | src_128([stabilityai.apidog.io](https://stabilityai.apidog.io/api-6070379)), src_129([kb.stability.ai](https://kb.stability.ai/knowledge-base/inpainting-via-api-or-brand-studio)), src_257([github.com](https://github.com/MaxiDonkey/DelphiStabilityAI)), src_258([preview-api.stability.ai](https://preview-api.stability.ai/docs)) |
| clm_047 | verified | src_131([docs.bfl.ml](https://docs.bfl.ml/flux_1_fill)), src_135([github.com](https://github.com/black-forest-labs/flux/blob/main/docs/fill.md)), src_134([huggingface.co](https://huggingface.co/black-forest-labs/FLUX.1-Fill-dev)), src_256([comfyui-wiki.com](https://comfyui-wiki.com/en/tutorial/advanced/image/flux/flux-1-dev-fill)) |
| clm_048 | verified | src_130([prompt-architects.com](https://prompt-architects.com/blog/460-inpainting-and-outpainting-prompt-techniques)), src_308([docs.midjourney.com](https://docs.midjourney.com/hc/en-us/articles/32794723105549-Vary-Region)), src_309([medium.com](https://medium.com/@lvntblsn/the-future-of-imaging-is-here-exploring-midjourneys-brand-new-vary-region-20-brand-new-prompts-ba325a114650)), src_310([cometapi.com](https://www.cometapi.com/how-to-use-midjourney-to-modify-a-masked-image/)) |
| clm_049 | verified | src_137([github.com](https://github.com/ClothingAI/lama-cleaner)), src_136([github.com](https://github.com/Sanster/IOPaint)), src_267([github.com](https://github.com/Sanster/IOPaint/discussions/420)), src_268([pypi.org](https://pypi.org/project/lama-cleaner/0.32.0/)) |
| clm_050 | verified | src_138([docs.comfy.org](https://docs.comfy.org/tutorials/basic/inpaint)), src_140([comfyai.run](https://comfyai.run/documentation/InpaintCropImproved)) |
| clm_051 | verified | src_150([github.com](https://github.com/Acly/krita-ai-diffusion/wiki/Inpainting)), src_152([docs.interstice.cloud](https://docs.interstice.cloud/selections/)) |
| clm_052 | verified | src_142([labelbox.com](https://labelbox.com/blog/bringing-ai-to-the-browser-sam2-for-interactive-image-segmentation/)), src_144([github.com](https://github.com/lucasgelfond/webgpu-sam2)), src_143([github.com](https://github.com/Labelbox/sam2-web)), src_269([github.com](https://github.com/geronimi73/next-sam)), src_146([github.com](https://github.com/sunu/SAM-in-Browser)), src_145([medium.com](https://medium.com/@geronimo7/in-browser-image-segmentation-with-segment-anything-model-2-c72680170d92)) |
| clm_053 | verified | src_147([github.com](https://github.com/3rChuss/react-canvas-masker)), src_148([github.com](https://github.com/la-voliere/react-mask-editor)), src_270([registry.npmjs.org](https://registry.npmjs.org/react-canvas-masker)), src_271([registry.npmjs.org](https://registry.npmjs.org/react-mask-editor)) |
| clm_054 | verified | src_155([apatero.com](https://www.apatero.com/blog/comfyui-inpainting-advanced-techniques-guide-2026)), src_153([stable-diffusion-art.com](https://stable-diffusion-art.com/inpainting/)) |
| clm_055 | unresolved | src_156([developer.ideogram.ai](https://developer.ideogram.ai/api-reference/api-reference/edit-v3)), src_157([developer.ideogram.ai](https://developer.ideogram.ai/ideogram-api/api-overview)), src_159([fal.ai](https://fal.ai/models/fal-ai/ideogram/v3/edit/api)) |
| clm_056 | unresolved | src_156([developer.ideogram.ai](https://developer.ideogram.ai/api-reference/api-reference/edit-v3)), src_159([fal.ai](https://fal.ai/models/fal-ai/ideogram/v3/edit/api)) |
| clm_057 | unresolved | src_156([developer.ideogram.ai](https://developer.ideogram.ai/api-reference/api-reference/edit-v3)), src_159([fal.ai](https://fal.ai/models/fal-ai/ideogram/v3/edit/api)) |
| clm_058 | verified | src_156([developer.ideogram.ai](https://developer.ideogram.ai/api-reference/api-reference/edit-v3)), src_255([fal.ai](https://fal.ai/models/fal-ai/ideogram/character/edit/api)) |
| clm_059 | unresolved | src_157([developer.ideogram.ai](https://developer.ideogram.ai/ideogram-api/api-overview)), src_160([fal.ai](https://fal.ai/models/fal-ai/ideogram/v2/edit/api)) |
| clm_060 | unresolved | src_167([ruby.sketchup.com](https://ruby.sketchup.com/file.ReleaseNotes.html)), src_169([help.sketchup.com](https://help.sketchup.com/en/current-release-notes)), src_170([help.sketchup.com](https://help.sketchup.com/en/sketchup-desktop-20262)) |
| clm_061 | verified | src_167([ruby.sketchup.com](https://ruby.sketchup.com/file.ReleaseNotes.html)), src_168([github.com](https://github.com/SketchUp/ruby-api-stubs/blob/main/pages/ReleaseNotes.md)), src_170([help.sketchup.com](https://help.sketchup.com/en/sketchup-desktop-20262)) |
| clm_062 | verified | src_167([ruby.sketchup.com](https://ruby.sketchup.com/file.ReleaseNotes.html)), src_173([forums.sketchup.com](https://forums.sketchup.com/t/2026-issues/340821/72)), src_228([community.sketchucation.com](https://community.sketchucation.com/topic/164553/sketchucation-tools-5.0.../66?lang=en-US)) |
| clm_063 | unresolved | src_172([forums.sketchup.com](https://forums.sketchup.com/t/important-upcoming-ruby-update/348793)) |
| clm_064 | verified | src_168([github.com](https://github.com/SketchUp/ruby-api-stubs/blob/main/pages/ReleaseNotes.md)), src_175([ruby.sketchup.com](https://ruby.sketchup.com/file.extension_requirements.html)) |
| clm_065 | unresolved | src_176([docs.comfy.org](https://docs.comfy.org/tutorials/controlnet/depth-controlnet)) |
| clm_066 | verified | src_177([archigenai.com](https://archigenai.com/comfyui-floor-plan-to-3d-render-architects-2026.html)), src_180([archgyan.com](https://archgyan.com/stable-diffusion-architectural-rendering-open-source/)) |
| clm_067 | verified | src_179([stable-diffusion-art.com](https://stable-diffusion-art.com/controlnet/)), src_181([agentbus.sh](https://agentbus.sh/posts/how-to-build-ai-architectural-rendering-with-controlnet-and-stable-diffusion/)) |
| clm_068 | verified | src_184([github.com](https://github.com/civitai/civitai-comfy-nodes)), src_186([runcomfy.com](https://www.runcomfy.com/comfyui-nodes/civitai-comfy-nodes/civitai-control-net)) |
| clm_069 | verified | src_182([archgyan.com](https://www.archgyan.com/harnessing-midjourney-architectural-concept-design/)), src_183([educasium.com](https://educasium.com/en/blog/midjourney-architecture-rendus)) |
| clm_070 | verified | src_181([agentbus.sh](https://agentbus.sh/posts/how-to-build-ai-architectural-rendering-with-controlnet-and-stable-diffusion/)), src_180([archgyan.com](https://archgyan.com/stable-diffusion-architectural-rendering-open-source/)) |
| clm_071 | refuted | src_183([educasium.com](https://educasium.com/en/blog/midjourney-architecture-rendus)), src_249([aia.org](https://www.aia.org/about-aia/press/new-research-explores-perceptions-and-opportunities-artificial-intelligence)), src_251([toffu.co](https://toffu.co/blogs/news/riba-ai-report-2025-59-of-architecture-practices-now-use-ai)), src_250([rendershop.ai](https://rendershop.ai/blog/how-many-architects-use-ai)), src_327([www.scribd.com](https://www.scribd.com/document/906795445/Riba-Ai-Report-2025-Finalpdf)) |
| clm_072 | verified | src_187([blog.chaos.com](https://blog.chaos.com/veras-4.0)), src_188([blog.chaos.com](https://blog.chaos.com/veras-v7-vs-standalone-nano-banana)), src_189([forum.evolvelab.io](https://forum.evolvelab.io/t/veras-release-4-0-nano-banana/11184)), src_190([architosh.com](https://architosh.com/2026/02/chaos-releases-veras-4-0-with-nano-banana-pro/)) |
| clm_073 | verified | src_088([justnecessary.substack.com](https://justnecessary.substack.com/p/ai-rendering-for-sketchup-2026-an-52a)), src_089([d5render.com](https://www.d5render.com/posts/best-ai-sketchup-plugins-2026)), src_192([aitoolsbakery.com](https://aitoolsbakery.com/blog/veras-review/)), src_214([forums.sketchup.com](https://forums.sketchup.com/t/ai-renderings-with-evolvelab-veras/227899)), src_215([evolvelab.io](https://www.evolvelab.io/post/veras-1-9-next-level-rendering-with-the-features-you-ve-been-asking-for)) |
| clm_074 | verified | src_089([d5render.com](https://www.d5render.com/posts/best-ai-sketchup-plugins-2026)), src_088([justnecessary.substack.com](https://justnecessary.substack.com/p/ai-rendering-for-sketchup-2026-an-52a)) |
| clm_075 | verified | src_193([educasium.com](https://educasium.com/en/blog/comparatif-logiciels-ia-architecture)), src_291([gendo.ai](https://www.gendo.ai/blog/top-10-ai-rendering-software-architects-2026)), src_292([promeai.pro](https://www.promeai.pro/architecture-sketch-transformation)) |
| clm_076 | verified | src_090([evolvelab.io](https://www.evolvelab.io/veras)), src_187([blog.chaos.com](https://blog.chaos.com/veras-4.0)), src_279([chaos.com](https://www.chaos.com/veras)), src_280([digitalproduction.com](https://digitalproduction.com/2026/05/29/chaos-puts-veras-everywhere/)), src_282([support.chaos.com](https://support.chaos.com/hc/en-us/articles/46887808239633-When-do-the-new-prices-take-effect)) |
| clm_077 | unresolved | src_195([documentation.chaos.com](https://documentation.chaos.com/space/VMAYA/111739026/Physical+camera+Attributes)), src_196([documentation.chaos.com](https://docs.chaos.com/display/CWVRAYMAX/Physical+Camera)), src_273([forums.chaos.com](https://forums.chaos.com/forum/v-ray-for-3ds-max-forums/v-ray-for-3ds-max-general/60783-default-exposure-value-of-vrayphysicalcamera-when-exposure-is-disabled)) |
| clm_078 | verified | src_197([documentation.chaos.com](https://documentation.chaos.com/display/EVECTORWORKS)), src_200([blog.chaos.com](https://blog.chaos.com/enscape-for-sketchup-get-started)), src_201([myarchitectai.com](https://www.myarchitectai.com/blog/enscape-rendering-settings)) |
| clm_079 | verified | src_198([documentation.chaos.com](https://documentation.chaos.com/space/ESKETCHUP/127964922/Rendering+Styles)), src_199([documentation.chaos.com](https://docs.chaos.com/display/EArchiCAD/Rendering+Styles)), src_276([forum.enscape3d.com](https://forum.enscape3d.com/index.php?thread%2F30696-enscape-4-13-0-released%2F=)), src_275([documentation.chaos.com](https://documentation.chaos.com/space/ERN/219086878/4.13.0+Windows)), src_277([blog.chaos.com](https://blog.chaos.com/artistic-visual-modes)) |
| clm_080 | verified | src_197([documentation.chaos.com](https://documentation.chaos.com/display/EVECTORWORKS)), src_201([myarchitectai.com](https://www.myarchitectai.com/blog/enscape-rendering-settings)) |
| clm_081 | verified | src_195([documentation.chaos.com](https://documentation.chaos.com/space/VMAYA/111739026/Physical+camera+Attributes)), src_272([docs.chaos.com](https://docs.chaos.com/display/VRAY3SOFTIMAGE/V-Ray+Physical+Camera)), src_274([forums.cgarchitect.com](https://forums.cgarchitect.com/topic/21729-white-balance-in-rendering/)) |
| clm_082 | refuted | src_177([archigenai.com](https://archigenai.com/comfyui-floor-plan-to-3d-render-architects-2026.html)), src_208([depth-anything.github.io](https://depth-anything.github.io/)) |
| clm_083 | unresolved | src_205([docs.blender.org](https://docs.blender.org/manual/en/latest/render/layers/passes.html)), src_206([developer.blender.org](https://developer.blender.org/docs/features/eevee/render_passes/)), src_317([developer.blender.org](https://developer.blender.org/T72461)), src_318([projects.blender.org](https://projects.blender.org/blender/blender/pulls/109687)), src_319([docs.blender.org](https://docs.blender.org/manual/en/3.6/render/layers/passes.html)) |
| clm_084 | verified | src_203([developer.blender.org](https://developer.blender.org/T33437)), src_204([developer.blender.org](https://developer.blender.org/T34552)), src_202([katsbits.com](https://www.katsbits.com/codex/sketchup-import/)), src_216([homestyler.com](https://www.homestyler.com/article/trends/how-to-seamlessly-transfer-d-models-to-blender)) |
| clm_085 | refuted | src_202([katsbits.com](https://www.katsbits.com/codex/sketchup-import/)), src_212([kitchendemy.com](https://kitchendemy.com/can-sketchup-files-export-into-blender/)), src_216([homestyler.com](https://www.homestyler.com/article/trends/how-to-seamlessly-transfer-d-models-to-blender)), src_220([help.sketchup.com](https://help.sketchup.com/en/sketchup/exporting-fbx-files)), src_230([cadinterop.com](https://www.cadinterop.com/en/formats/mesh/sketchup.html)), src_225([forums.sketchup.com](https://forums.sketchup.com/t/export-not-working/179474)), src_226([forums.sketchup.com](https://forums.sketchup.com/t/sketchup-free-cannot-export/245037)) |
| clm_086 | verified | src_213([huggingface.co](https://huggingface.co/spaces/radames/stable-diffusion-depth2img/discussions/73)), src_208([depth-anything.github.io](https://depth-anything.github.io/)) |
| clm_087 | verified | src_217([router.axwith.com](https://router.axwith.com/api/v1/models)), src_218([router.axwith.com](https://router.axwith.com/api/v1/images/edits)) |
| clm_088 | verified | src_217([router.axwith.com](https://router.axwith.com/api/v1/models)), src_218([router.axwith.com](https://router.axwith.com/api/v1/images/edits)) |
| clm_089 | verified | src_217([router.axwith.com](https://router.axwith.com/api/v1/models)), src_218([router.axwith.com](https://router.axwith.com/api/v1/images/edits)) |
| clm_090 | unresolved | src_217([router.axwith.com](https://router.axwith.com/api/v1/models)), src_218([router.axwith.com](https://router.axwith.com/api/v1/images/edits)) |
| clm_091 | verified | src_217([router.axwith.com](https://router.axwith.com/api/v1/models)), src_218([router.axwith.com](https://router.axwith.com/api/v1/images/edits)) |
| clm_092 | verified | src_217([router.axwith.com](https://router.axwith.com/api/v1/models)), src_218([router.axwith.com](https://router.axwith.com/api/v1/images/edits)) |
