---
description: "렌더와 캡처의 기하 일치 경보, 창·문·지붕 드리프트 점검, 리비전 간 비교, QA 리포트 작성, 재점검 요청에 사용합니다. '기하 맞는지 봐줘', '지붕 바뀐 거 아냐?', '창 개수 확인해줘', 'R02랑 R03 비교해줘', 'QA 다시' 같은 요청에 대응합니다. 단, 문제 영역 수정은 /fix, 코드 테스트는 /test를 사용합니다. 점수는 경보이지 게이트가 아닙니다."
---

# /qa

Standard. `scripts/qa_geometry.py`로 캡처 대비 렌더의 엣지 IoU·SSIM 참고치를 내고, 사람이 볼 체크리스트와 함께 리포트를 쓴다. **advisory only** — 임계 미달은 "보라"는 신호이지 차단이 아니다 (Human Judges Geometry).

## 사용법

```text
/qa <project> <shot|all> [--revision Rnn] [--threshold 0.35]
```

## 실행 흐름

### Step 1: 대상 확정

- `--revision`이 없으면 최신 리비전. `all`이면 프로젝트의 모든 샷 최신 리비전.
- 캡처 경로는 manifest에서, 렌더는 `renders/<P>/<S>/Rnn/render.*`.

### Step 2: 자동 참고치

```bash
python3 scripts/qa_geometry.py --capture assets/captures/<P>/<S>/capture.png --render renders/<P>/<S>/Rnn/render.* [--threshold 0.35]
```

- IoU(엣지)·SSIM·해상도/비율 차이를 받는다. 임계(기본 0.35) 미달은 **WARN**으로 표시한다. 절대 "FAIL"이라 쓰지 않는다.
- gpt 출력은 입력 비율을 근사하므로 크기 차이 자체는 경보 사유가 아니다. 리사이즈 후 비교했음을 리포트에 적는다.

### Step 3: 사람 판정 체크리스트

캡처와 렌더를 나란히 보여주고 아래를 사용자와 함께 판정한다(에이전트가 대신 "통과"를 선언하지 않는다):

- [ ] 지붕 형태(박공/모임/평)와 경사 방향이 같다 — E2·E4 실측에서 가장 자주 드리프트한 항목
- [ ] 창·문 개수와 위치, 층수가 같다
- [ ] 카메라·소실점이 같다 (기울어짐·시점 이동 없음)
- [ ] 건물이 추가·삭제되지 않았다
- [ ] 확정 색(fixed_colors)이 유지됐다
- [ ] 마스크 수정(`/fix`) 결과라면 마스크 밖이 그대로다

### Step 4: 리포트

`40-reports/qa/<project>_<shot>_Rnn.md`에 참고치 + 체크리스트 결과 + 권고(`/fix` 대상 영역 또는 재캡처)를 기록한다. `all`이면 `40-reports/qa/<project>_<date>.md` 한 장으로 묶는다.

## 출력 형식

```markdown
# /qa — {project}/{shot} {Rnn}

| 지표 | 값 | 임계 | 표시 |
|---|---|---|---|
| edge IoU | 0.31 | 0.35 | WARN (참고치) |
| SSIM | 0.62 | — | info |
| 크기 | 2560×1440 vs 1448×1086 | — | 리사이즈 비교 |

사람 판정:
- 지붕: 박공 유지 ✓
- 창 개수: 캡처 6 / 렌더 6 ✓
- 좌측 가로수 소실 — 의도 아님 → /fix 대상

권고: /fix P01 S01_entrance --base R00 --web (가로수 영역)
리포트: 40-reports/qa/P01_S01_entrance_R00.md
```

## 트리거 경계

should-trigger:

- "기하 맞는지 봐줘"
- "지붕 바뀐 거 아냐?"
- "창 개수 확인해줘"
- "R02랑 R03 비교해줘"
- "QA 리포트 써줘" / "QA 다시"
- "전 샷 점검해줘"

NOT-trigger:

- "이 부분 고쳐줘" → `/fix`
- "스크립트 테스트 돌려줘" → `/test` (qa_geometry.py 자체 검증은 `--selftest`)
- "승인 처리해줘" → `/approve`
- "IoU 0.35 넘었으니 자동 승인" → 하지 않는다. 점수는 게이트가 아니다

## 참조

- `scripts/qa_geometry.py` (wp-a) — advisory 지표
- `20-knowledge/capture-protocol.md` — 재캡처 트리거
- `20-knowledge/research/01_full_report.md` §6, 부록 #006 — "IoU를 게이트로 쓰지 말라"는 근거
