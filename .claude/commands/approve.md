---
description: "리비전 승인 단계 이동(clay → internal → client → approval), 승인 현황 조회, 승인 되돌리기, 어느 리비전이 어디까지 갔는지 확인 요청에 사용합니다. 'R03 내부 승인', '클라이언트 보낼 버전으로 올려', '최종 승인 처리', '지금 어디까지 승인됐어?', '승인 취소' 같은 요청에 대응합니다. 단, 납품 묶음 생성은 /deliver, 품질 점검은 /qa를 사용합니다."
---

# /approve

Lite. `scripts/revision.py`로 리비전에 승인 단계를 기록한다. 단계는 `clay → internal → client → approval` 순서이며 건너뛰지 않는다. 승인은 사람의 판정 기록이다 — `/qa` 점수로 자동 승인하지 않는다.

## 사용법

```text
/approve <project> <shot> <Rnn> <clay|internal|client|approval>
/approve <project> list
```

## 실행 흐름

### Step 1: 현황 확인

```bash
python3 scripts/revision.py list --project <P>
```

- 샷별 리비전과 현재 단계를 표로 보여준다. 대상 리비전의 `render.*`가 존재하는지 확인한다(파일 없는 리비전은 승인 불가).

### Step 2: 단계 규칙 확인

| 단계 | 의미 | 선행 조건 |
|---|---|---|
| clay | 캡처·매싱 확인용. 렌더 전 또는 R00 | 없음 |
| internal | 팀 내부 검토 통과 | `/qa` 리포트 존재(WARN 있어도 사람이 봤으면 가능) |
| client | 클라이언트에게 보내는 버전 | internal 기록 |
| approval | 클라이언트 최종 승인 | client 기록 + 사용자가 승인 사실을 명시 |

- 단계를 건너뛰려 하면 중간 단계를 함께 기록할지 묻는다.
- 같은 샷에서 더 높은 단계에 이미 다른 리비전이 있으면(예 R02 client, 지금 R03 client) 교체인지 병행인지 확인한다.

### Step 3: 기록

```bash
python3 scripts/revision.py approve --project <P> --shot <S> --revision Rnn --stage <stage>
```

- meta.json의 `approvals[]`에 `{stage, at, by}`가 추가된다. 되돌리기는 새 항목(`revoked`)으로 남기고 기존 기록을 지우지 않는다.

### Step 4: 다음

- approval에 도달한 샷이 프로젝트의 전부이면 `/deliver <P>`를 권한다.

## 출력 형식

```markdown
# /approve — {project}

| 샷 | 리비전 | 단계 | 기록 |
|---|---|---|---|
| S01_entrance | R03 | client | 2026-09-14 20:40 |
| S02_side | R01 | internal | 2026-09-14 20:41 |

다음: S02_side /qa 후 client 승인 → 전 샷 approval 시 /deliver P01
```

## 트리거 경계

should-trigger:

- "R03 내부 승인"
- "클라이언트 보낼 버전으로 올려줘"
- "최종 승인 처리해줘"
- "지금 어디까지 승인됐어?"
- "승인 취소" / "R02로 되돌려"
- "승인 현황 보여줘"

NOT-trigger:

- "납품 묶어줘" → `/deliver`
- "기하 확인해줘" → `/qa`
- "다시 렌더" → `/render`
- "QA 점수 넘었으니 승인" → 사람 판정 없이 승인하지 않는다

## 참조

- `scripts/revision.py` (wp-a)
- `20-knowledge/research/01_full_report.md` §6 — R00/R01 태그 + 단계형 파이프라인 근거 (clm_009)
