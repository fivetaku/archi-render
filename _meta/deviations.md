# Template Deviation Log

이 파일은 워크스페이스가 `20-archetypes/development` 템플릿과 어떻게 다른지를 기록합니다.
Quick Path 생성에서는 "기본 템플릿 유지"가 기본 기록이고,
Custom Path에서는 사용자가 명시적으로 동의한 변경 사항만 기록합니다.

## Reflected Harness Metadata (생성 시점)

| 항목 | 값 | 출처 |
|------|----|------|
| target runtime | Claude Code + Codex (CLAUDE.md + AGENTS.md) | Workspace_Builder |
| harness_type | basic | 18-HARNESS_CONCEPTS.md |
| state_model | enabled=True, path=_meta | _meta 위치 |
| doctor_checks | structure, instructions, commands, security, harness-contract | validator 권장 묶음 |

## Deviation Table

| 날짜 | 아키타입 | 일탈 사유 | 영향 |
|------|----------|-----------|------|
| 2026-09-14 | development | 기본 템플릿 유지 (structure.json v2.0.0, generator MVP+harness-metadata) | 영향 없음 |
| 2026-09-14 | development | Custom Path: 렌더 파이프라인 커맨드 7종 추가 (intake/stylepack/render/fix/qa/approve/deliver, Claude `.claude/commands` + Codex `.agents/skills/development-*` 양쪽), 기본 5종 + wrap 유지 (사용자 동의, 02 설계 문서 §5) | 커맨드 추가 |
| 2026-09-14 | development | Custom Path: assets/stylepacks·assets/captures·renders·webtool 폴더 추가 (비넘버링, dev subtype "도구가 소비하는 경로" 규칙). renders/는 .gitignore 대상 | 구조 추가 |
| 2026-09-14 | development | 스타일팩 기본 5종(overcast-photoreal/golden-hour/dusk-cinematic/midday-concrete/aerial-drone) + 동적 `custom-<slug>` 규칙(20-knowledge/stylepacks/DYNAMIC_PACK.md, Specificity Gate) — 02 문서 Q7 디폴트 3팩에서 5팩으로 확장 | 자산 시드 |
| 2026-09-14 | development | 백엔드 정책: 전체 샷 = gpt-image(pumasi imagen.sh --ref, 마스크 없음), 영역 수정 = grok(insane-router /images/edits, RGBA alpha0=edit). 02 문서 P3(grok 단일)에서 2026-09-14 트라이얼 결과로 2단 구성 변경. OpenAI/Google 원본 키 직접 호출 금지 | 정책 |
| 2026-09-14 | development | 지식 베이스 시드: RESEARCH/arch_ai_render_workspace_20260911_1735 outputs 01·02 → 20-knowledge/research, 트라이얼 README 2건 → 20-knowledge/trials, backends.md·capture-protocol.md·kb-link.md(archi-kb 예약 스텁) 작성, 10-planning/curriculum.md 4주 동선 | KB 초기화 |
| 2026-09-14 | development | --data-isolation 70-private 적용 (02 문서 Q5 디폴트 "켬"): 클라이언트 도면·계약 원본은 payload 미추적, meta.md만 | 격리 on |
| 2026-09-14 | development | 미적용: --recovery(비가역 외부 자원 없음 — 두 백엔드 모두 구독·0원, 실패는 재실행으로 복구), --onboarding-hook(1인 운영, 배포용 아님). 종량 과금 백엔드 도입 시 recovery 재검토 | 영향 없음 |
| 2026-09-14 | development | 생성 직후 E2E 실동(demo-cafe): grok 렌더 17.7s·마스크 fix 13.1s·gpt 렌더 74.9s 통과. 발견 결함 2건 수정 — ① 라우터 앞 Cloudflare가 Python 기본 UA를 1010(403)으로 차단 → render.py에 User-Agent 명시, 실패 시 빈 리비전 폴더 삭제 ② qa_geometry 엣지 IoU 0.35 임계가 사진사실 렌더에서 과도 경보(IoU 0.18/구조점수 0.75) → 임계 0.25 + 구조점수<0.7 동시 조건으로 완화 | 스크립트 수정, 게이트 아님 |
| 2026-09-15 | development | 스타일 옵션 축 확장(오너 지적: 계절·시간대·인구 밀도 등 변수 부족): 14축 추가/확장(lighting +5, season +6, people_density/activity, car_density/type, vegetation_age, sky, context, material_wear, interior_lights, tone, lens_mm/camera_height_m/tilt, references) — 7문장 슬롯 상한 유지를 위해 축 병합 규칙(사람·차→엔투라지 1문장, 하늘+실내등→조명, 식생→계절, 맥락+마모→Context, 톤+후보정→그레이딩) 도입. `prompt_compose.py --list-options`가 어휘 정본을 JSON으로 노출, 웹툴 패널은 이를 동적으로 렌더(접이식 7섹션·초기화·무작위 변주·슬롯 카운터). 실측: 야간 전면점등+busy+도심 / 폭설+sparse+어린나무 변주 grok 렌더 반영 확인 | OPTIONS.md·컴포저·selftest·웹툴 |
