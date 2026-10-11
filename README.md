# archi-render — Archi Render Director

## 수강생 빠른 시작 (Codex)

1. Codex 앱에서 이 폴더를 엽니다.
2. 첫 질문: "이 폴더는 뭐 하는 곳이야?"
3. 내 캡처 넣기: `$development-intake 내프로젝트 ~/Downloads/캡처폴더` (또는 "이 폴더 인입해 줘")
4. 스타일 둘러보기: `$development-stylepack list` (또는 "스타일팩 뭐 있어?")
5. 렌더는 1회차에 강사 화면에서 봅니다. 각자 PC 렌더는 설정을 마친 뒤 2회차부터 합니다.

아래 빠른 시작은 강사 PC(렌더 백엔드 설치) 기준입니다. `/intake` 같은 슬래시 표기는 Claude Code 문법이고, Codex에서는 `$development-intake`처럼 씁니다.

> SketchUp 클레이 캡처 → 스타일팩 AI 렌더 → 마스크 영역 수정 → 기하 QA 경보 → 리비전 승인 → 납품. 비용 0 백엔드(gpt-image via pumasi, grok via insane-router)만 쓴다.

이 워크스페이스는 Workspace_Builder가 `Development Agent` 아키타입(structure.json v2.0.0, dual runtime, guard hook, wrap, 70-private 격리, scripts-layer)으로 생성한 뒤 렌더 디렉터로 커스텀했습니다.

## 강사 빠른 시작 (Claude Code 또는 Codex, 렌더 키가 있는 PC)

1. **SketchUp (맥·윈도우)** — `scripts/sketchup/export_scenes.rb`를 실행해 씬별 `capture.png`(클레이, 그림자 On, 긴 변 ≥2000px)를 덤프한다. 규약: `20-knowledge/capture-protocol.md`.
2. **인입** — 폴더를 이 맥으로 옮기고 워크스페이스에서:
   ```bash
   claude          # 또는 codex
   > /intake P01 ~/Downloads/P01_captures
   ```
   또는 웹툴에 드롭: `python3 webtool/server.py` → http://127.0.0.1:8765 (캡처 드롭 → 옵션 → 프롬프트 → 렌더 → 브러시 마스크 → fix → 팩 저장).
3. **렌더** — `> /stylepack list` 로 팩을 고르고 `> /render P01 all --pack overcast-photoreal`.
4. **점검·수정** — `> /qa P01 all` (경보는 참고, 판정은 사람) → 문제 영역은 웹툴에서 마스크 → `> /fix P01 S01 --base R00 --mask ... --instruction "..."`.
5. **승인·납품** — `> /approve P01 S01 R01 internal` … `approval` → `> /deliver P01` → `50-output/P01/`.

마스크 수정(grok)은 라우터 키가 필요하다. render.py 기본 키는 `insane-router-key-aside`이며, 전용 키를 `insane-router-connect` 스킬로 발급하면 `ARCHI_RENDER_ROUTER_KEY_SERVICE`로 지정한다. OpenAI/Google 원본 키는 쓰지 않는다.

## 문서

- [CLAUDE.md](./CLAUDE.md) — 정본 instruction surface (12섹션)
- [AGENTS.md](./AGENTS.md) — Codex 포인터 + 커맨드→스킬 매핑
- [20-knowledge/backends.md](./20-knowledge/backends.md) — 백엔드 능력 카드·마스크 극성
- [20-knowledge/capture-protocol.md](./20-knowledge/capture-protocol.md) — 캡처 규약 C1~C8
- [20-knowledge/stylepacks/](./20-knowledge/stylepacks/) — 동적 팩 규칙·옵션 어휘
- [20-knowledge/research/](./20-knowledge/research/) · [20-knowledge/trials/](./20-knowledge/trials/) — 리서치·실측 근거
- [10-planning/curriculum.md](./10-planning/curriculum.md) — 4주 과외 동선 (render → KB → 연결 렌더)
- [_meta/deviations.md](./_meta/deviations.md) — 템플릿 대비 일탈 기록
- [_meta/changelog.md](./_meta/changelog.md) — 변경 이력 정본
- [_meta/HARNESS_STATUS.md](./_meta/HARNESS_STATUS.md) — 훅 생성·등록과 실제 발동 증거의 구분

훅 상태 확인: `python3 -B _meta/harness-status.py`.
정적 점검 통과는 실제 활성화 증명이 아니며, 런타임 발동 확인 전에는 `unverified`입니다.

## 저장소 규칙

- `renders/`는 git 밖(.gitignore). 캡처·팩·스크립트·meta 포인터만 추적.
- 클라이언트 도면·계약 원본은 `70-private/<project>/` (payload 미추적, `meta.md`만).
