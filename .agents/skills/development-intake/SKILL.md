---
name: development-intake
description: "SketchUp 캡처 폴더 인입, 캡처 규약 점검, 샷 목록 생성, 재캡처 판정, 프로젝트 등록 요청에 사용합니다. '캡처 들여와줘', '이 폴더 인입해줘', '샷 목록 만들어줘', '규약 맞는지 봐줘', '다시 인입해줘' 같은 요청에 대응합니다. 단, 렌더 실행은 $development-render, 스타일팩 선택·생성은 $development-stylepack, 클라이언트 도면 원본 보관은 70-private 규칙을 따릅니다."
---

# intake Workflow

Codex-compatible mirror of `.claude/commands/intake.md`.

Invoke explicitly with `$development-intake` followed by the workflow arguments.
Claude per-command tool controls are not enforced by this skill; Codex sandbox and approval settings remain separate.

# $development-intake

Standard. SketchUp에서 내보낸 캡처 폴더를 `assets/captures/<project>/`로 인입하고 `20-knowledge/capture-protocol.md` 규약을 검사해 샷 목록(`manifest.json`)을 만든다. **경고는 차단이 아니다** — 사용자가 알고 진행할 수 있게 판정만 보여준다.

## 사용법

```text
$development-intake <project> [<source-folder>]
```

`<source-folder>`를 생략하면 `assets/captures/<project>/`에 이미 놓인 파일을 검사한다.

## 실행 흐름

### Step 1: 폴더 위치 확인

- 소스 폴더가 `assets/captures/<project>/` 밖이면 복사한다(이동 아님). 원본 CAD·실도면·계약 자료가 섞여 있으면 **캡처만** 복사하고 나머지는 `70-private/<project>/`로 안내한다. 70-private 밖으로 꺼내지 않는다.
- `<shot>/capture.png` 구조가 아니면(예: 씬 이름 그대로의 png 나열) 씬 이름을 slug화해 `<shot>/capture.png`로 rename을 제안하고 승인 후 적용한다.

### Step 2: 규약 검사 (샷별)

`20-knowledge/capture-protocol.md` C1~C8을 샷마다 판정한다. 이미지 메타는 Python(PIL 또는 stdlib)로 읽는다.

| 검사 | 판정 |
|---|---|
| 긴 변 ≥ 2000px | 미달 → **WARN** (차단 아님). 값과 함께 "저해상은 grok 폴백에서 1024로 업스케일됨"을 안내 |
| 종횡비 | 씬별 비율을 표시. 16:9/4:3/3:2/1:1 밖이면 INFO — `$development-render --aspect W:H`로 전달할 값을 적어 둔다 |
| 클레이/모노크롬·그림자 On | 색 채도·텍스처 흔적이 높으면 WARN + 재캡처 권고 |
| 씬 이름 | slug 규칙(`S01_entrance`) 불일치 → WARN + rename 제안 |
| camera.json | 있으면 필드 파싱해 manifest에 복사, 없으면 INFO ("선택 항목") |
| 배경 | 하늘 그라데이션·워터마크 의심 → WARN |

### Step 3: manifest 작성

`assets/captures/<project>/manifest.json`:

```json
{
  "project": "P01",
  "intake_at": "2026-09-14T20:30:00+09:00",
  "shots": [
    {"shot": "S01_entrance", "capture": "S01_entrance/capture.png", "size": [2560, 1440],
     "aspect": "16:9", "sha256": "...", "camera": {"...": "..."} , "checks": {"resolution": "pass", "style": "warn", "scene_name": "pass"}}
  ]
}
```

같은 project를 다시 인입하면 해시가 바뀐 샷만 갱신하고 나머지는 유지한다(멱등).

### Step 4: 보고와 다음 단계

- 샷 수, WARN 수, 재캡처 권고 샷을 표로 보여준다.
- 다음: `$development-stylepack list`로 팩 선택 → `$development-render <project> <shot|all> --pack <id>`.

## 출력 형식

```markdown
# $development-intake 결과 — {project}

| 샷 | 크기 | 비율 | 스타일 | 씬 이름 | camera.json | 판정 |
|---|---|---|---|---|---|---|
| S01_entrance | 2560×1440 | 16:9 | pass | pass | 있음 | OK |
| S02_side | 1600×1200 | 4:3 | warn | pass | 없음 | WARN (해상도) |

재캡처 권고: S02_side (긴 변 1600px < 2000px — 진행 가능하나 grok 폴백 품질 저하)
manifest: assets/captures/{project}/manifest.json
다음: $development-stylepack list → $development-render {project} all --pack overcast-photoreal
```

## 트리거 경계

should-trigger:

- "캡처 폴더 들여와줘"
- "SketchUp에서 뽑은 거 인입해줘"
- "샷 목록 만들어줘"
- "규약 맞는지 봐줘"
- "해상도 확인해줘"
- "씬 이름 정리해줘"
- "다시 인입해줘" / "샷 추가됐어"

NOT-trigger:

- "렌더 돌려줘" → `$development-render`
- "팩 골라줘" / "새 스타일 만들어줘" → `$development-stylepack`
- "도면 원본 보관해줘" → `70-private/<project>/`에 두고 `meta.md`만 작성 (커맨드 없음)
- "SketchUp에서 어떻게 내보내?" → `30-docs/`·`scripts/sketchup/export_scenes.rb` 안내 (실행은 사용자 PC)

## 참조

- `20-knowledge/capture-protocol.md` — 규약 정본 C1~C8
- `scripts/sketchup/export_scenes.rb` — 사용자 PC용 export 스크립트
- `70-private/README.md` — 클라이언트 원본 격리 규칙
