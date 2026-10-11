# 4주 과외 동선 — archi-render → archi-kb 연계

> 사용자(건축 실무자)가 이 워크스페이스로 렌더 디렉팅을 익히고, 3주차부터 지식 베이스를 붙여
> "렌더가 프로젝트 사실을 읽는" 상태까지 가는 동선. 한 주에 한 결과물. 강의가 아니라 실제 프로젝트 1개로 진행한다.
>
> 명령 표기는 Codex 기준(`$development-<이름>`)이다. Claude Code에서는 같은 명령을 `/<이름>`으로 쓴다. 1회차(2026-10-11)는 수강생 PC에 렌더 백엔드가 없어 intake·stylepack까지만 직접 하고, render·fix는 강사 화면 시연으로 본다.

| 주 | 목표 | 하는 일 | 결과물 | 완료 기준 |
|---|---|---|---|---|
| 1 | **렌더 한 바퀴** | SketchUp에서 `export_scenes.rb`로 씬 3~5개 덤프 → `$development-intake` → `$development-stylepack list`에서 팩 선택 → `$development-render` → `$development-qa` → `$development-approve internal` | 프로젝트 1개, 샷 3개 이상 R00 렌더 + 컨택트시트 | 캡처 규약 위반 0, meta.json에 usage 기록, `renders/`가 git에 안 올라감 확인 |
| 2 | **수정 루프와 팩 만들기** | 웹툴(`webtool/server.py`)에서 브러시 마스크 → `$development-fix` 2회 이상 → `$development-stylepack new`로 `custom-<slug>` 1개 합성(Specificity Gate 통과) → 그 팩으로 재렌더 → `$development-approve client` | R01~R03 리비전, custom 팩 1개, client 단계 샷 1개 | fix가 마스크 밖을 바꾸지 않았음을 눈으로 판정, 팩 스키마 전 필드 채움 |
| 3 | **KB 인입 + 브리프/허가** | `~/archi-kb` 생성(workspace-builder, knowledge-base) → 프로젝트 카드 1장(용도·재질·확정 색·허가 상태) 작성 → 브리프·허가 요약 카드로 정리 | archi-kb 카드 1장, `20-knowledge/kb-link.md`의 스키마와 일치 | 카드 필드가 kb-link 예상 스키마와 일치, PII가 카드에 없음 |
| 4 | **연결 렌더 + 납품** | `prompt_compose.py --kb-card`(scripts 담당 추가) 연동 → 카드 재질로 `$development-render` → `$development-qa` → `$development-approve approval` → `$development-deliver` | 카드 기반 렌더 세트 + 납품 컨택트시트 + 비용 요약 | 옵션>카드>팩 우선순위가 meta.json.sources에 남음, 납품본이 `50-output/<P>/`에 있음 |

## 각 주의 함정

- 1주: 컬러 텍스처가 켜진 캡처로 시작하면 재질 슬롯이 무시된다 — 클레이부터.
- 2주: "전체 다시"를 `$development-fix`로 하려는 습관 → `$development-render`. 반대로 "창 하나만"을 `$development-render`로 하면 나머지가 흔들린다 → `$development-fix`.
- 3주: 카드에 발주처·연락처를 쓰지 않는다. 그건 `70-private/`.
- 4주: QA IoU를 게이트로 쓰지 않는다. 경보는 사람이 본다.

## 이후 (선택)

- `$development-consistency` (샷 간 재질·색 일관성) — 02 설계 문서에 있으나 v1 미도입. 2주차 이후 필요가 확인되면 커맨드 추가.
- ControlNet 정밀 모드 — 로컬 GPU 또는 클라우드 노드 결정 후.
