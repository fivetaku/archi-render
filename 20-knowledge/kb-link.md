# kb-link — `~/archi-kb` 프로젝트 카드 연결 (예약, 읽기 전용)

> **상태: 스텁.** `~/archi-kb`는 아직 없다. 이 문서는 나중에 `/render`가 프로젝트 카드에서 재질·용도를 읽어
> 프롬프트 슬롯을 자동 채우게 될 때의 계약을 미리 고정해 둔 것이다. 지금은 아무 스크립트도 이 파일을 읽지 않는다.
> 과외 동선 3~4주차(`10-planning/curriculum.md`)에서 활성화한다.

## 원칙

- **읽기 전용.** archi-render는 archi-kb를 조회만 한다. 카드 수정은 archi-kb 워크스페이스에서 한다 (One Workspace, One Agent).
- **없으면 조용히 건너뛴다.** 카드가 없거나 필드가 비어도 `/render`는 실패하지 않고 스타일팩 기본값으로 진행한다. 카드는 보조 입력이다.
- **PII·클라이언트 정보는 오지 않는다.** 카드에서 읽는 것은 재질·용도·법규 요약 같은 설계 사실이다. 발주처·연락처·도면 원본은 `70-private/`에만 있다.

## 예상 카드 위치와 필드

```
~/archi-kb/projects/<project>/card.yaml
```

```yaml
project: P01            # archi-render의 <project> id와 동일
name: "○○ 카페 신축"
use: cafe               # residential|office|cafe|retail|public|mixed — entourage·lighting 기본값 선택에 사용
site: {region: "KR", climate: "temperate", orientation: "S"}
materials:              # /render가 materials 슬롯을 채울 때 우선 사용 (스타일팩 재질보다 우선)
  facade: ["white stucco", "dark standing-seam metal roof"]
  ground: ["grey concrete pavers"]
  glazing: "clear low-e glass, dark frames"
fixed_colors:           # 프롬프트에 "(keep them white)"로 박히는 확정 색
  - {element: "columns", color: "white"}
permit:                 # /brief·/permit(archi-kb 커맨드)가 채우는 요약. archi-render는 표시만
  status: draft|submitted|approved
  notes: "..."
shots:                  # 선택. 씬 이름 ↔ 설명 매핑
  S01_entrance: "주출입구 아이레벨"
updated: 2026-09-14
```

## `/render`가 읽는 순서 (활성화 후)

1. `--option k=v`로 사용자가 직접 준 값
2. 카드 `materials.*`, `fixed_colors`
3. 스타일팩 `pack.yaml` 슬롯 기본값

즉 사용자 옵션 > 카드 > 팩. 카드 값이 들어가면 `meta.json.sources.kb_card`에 카드 경로와 `updated`를 기록해 추적한다.

## 활성화 체크리스트 (나중에)

- [ ] `~/archi-kb` 생성 (knowledge-base 아키타입, `--preset ontology` 또는 `asset-library`)
- [ ] `card.yaml` 스키마를 archi-kb 쪽 정본으로 확정하고 이 문서는 포인터로 축소
- [ ] `scripts/prompt_compose.py`에 `--kb-card <path>` 옵션 추가 (scripts 담당)
- [ ] `/render` 커맨드 Step 2에 카드 조회 단계 추가
