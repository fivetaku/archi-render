# archi-render Changelog (정본)

> 이 워크스페이스 변경이력의 단일 정본. CLAUDE.md `## 변경 이력`에는 최근 3행만 유지하고
> 전체 이력은 여기에 누적한다. 핵심 메타파일(CLAUDE.md, 커맨드, 룰) 수정 시 한 줄 추가.

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-09-14 | 워크스페이스 생성 (development v2.0.0) | 전체 | workspace-builder generator |
| 2026-09-14 | 렌더 파이프라인 커맨드 7종 추가 (intake·stylepack·render·fix·qa·approve·deliver), Claude 커맨드 + Codex 스킬 미러 | .claude/commands, .agents/skills | Custom Path — 02 설계 문서 §5 |
| 2026-09-14 | CLAUDE.md 12섹션을 Archi Render Director로 커스텀 (정체성·6원칙·폴더·워크플로우·커맨드·Scale·트리거·프레임워크·산출물·품질), AGENTS.md 커맨드→스킬 매핑표, README 퀵스타트 | CLAUDE.md, AGENTS.md, README.md | 생성기 기본 development 표면을 도메인 표면으로 |
| 2026-09-14 | 지식 베이스 시드: research 01·02, trials 2건, backends.md·capture-protocol.md·kb-link.md, 10-planning/curriculum.md | 20-knowledge, 10-planning | 리서치·2026-09-14 트라이얼 결정(gpt 전체/grok 수정) 이관 |
| 2026-09-14 | Deviation Table 7행 추가 (커맨드·폴더·팩·백엔드 정책·KB·70-private·미적용 옵션) | _meta/deviations.md | Custom Path 기록 의무 |
| 2026-09-14 | E2E 실동 검증 후 render.py UA 헤더·실패 정리, qa_geometry 경보 조건 완화. demo-cafe 프로젝트(S01 grok+fix, S02 gpt) 산출 | scripts/render.py, scripts/qa_geometry.py | 실측 결함 수정 |
