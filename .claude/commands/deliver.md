---
description: "납품 묶음 생성, 컨택트시트 제작, 최종 렌더 정리, 비용 요약, 납품 재생성 요청에 사용합니다. '납품 묶어줘', '컨택트시트 만들어', '최종본 정리해줘', '이번 프로젝트 비용 얼마 들었어?', '납품 다시 만들어' 같은 요청에 대응합니다. 단, 승인 단계 기록은 /approve, 렌더 자체 수정은 /render·/fix를 사용합니다."
---

# /deliver

Standard. approval 단계 리비전을 모아 `50-output/<project>/`에 컨택트시트와 최종본 포인터, meta.json usage 합계를 만든다. `renders/`는 git 밖이므로 납품본은 **복사**해 50-output에 둔다(50-output도 대용량이면 외부 스토리지 동기화).

## 사용법

```text
/deliver <project> [--latest] [--stage approval|client]
```

## 실행 흐름

### Step 1: 대상 리비전 확정

```bash
python3 scripts/revision.py list --project <P>
```

- 기본은 `approval` 단계 리비전. 일부 샷이 미승인이면 목록을 보여주고 (a) 미승인 샷 제외 (b) `--stage client`로 낮춰 포함 (c) 중단 중 고르게 한다. `--latest`는 단계 무시하고 최신 리비전(내부 검토용 시트).

### Step 2: 컨택트시트

```bash
python3 scripts/contact_sheet.py --project <P> [--latest]
```

- 산출물 `50-output/<P>/contact_sheet_<date>.jpg`. 각 타일에 샷 id·리비전·팩 id가 찍힌다.

### Step 3: 최종본 복사와 포인터

- 각 대상 리비전의 `render.*`를 `50-output/<P>/final/<shot>_<Rnn>.<ext>`로 복사한다.
- `50-output/<P>/manifest.json`에 샷 → 리비전 → 원본 경로(`renders/...`) → sha256 → 팩 id/version → 백엔드를 기록한다.

### Step 4: 비용 요약

- 대상 리비전 + 그 샷의 모든 이전 리비전 meta.json에서 `usage`를 모아 백엔드별 호출 수·소요 합계·`cost_in_usd_ticks` 합계를 낸다. 두 경로 모두 구독이라 **실과금 0**임을 명시하고, ticks는 참고치로만 적는다.
- `40-reports/cost/<P>_<date>.md`에 저장하고 요약을 출력한다.

### Step 5: 점검

- [ ] 납품본에 `70-private/` 자료가 섞이지 않았다
- [ ] `renders/`를 git add 하지 않았다 (`git status`로 확인)
- [ ] 컨택트시트에 미승인 리비전이 들어가지 않았다(`--latest`가 아닐 때)

## 출력 형식

```markdown
# /deliver — {project} ({date})

컨택트시트: 50-output/P01/contact_sheet_20260914.jpg (샷 4)
최종본: 50-output/P01/final/ (S01_R03.png, S02_R02.jpg, ...)
manifest: 50-output/P01/manifest.json

비용 요약 (40-reports/cost/P01_20260914.md)
| 백엔드 | 호출 | 소요 합계 | cost_in_usd_ticks 합계 | 실과금 |
|---|---|---|---|---|
| gpt (pumasi) | 6 | 9m 50s | n/a | 0 |
| grok (router) | 5 | 1m 22s | 3,500,000,000 | 0 (구독) |

제외된 샷: 없음
```

## 트리거 경계

should-trigger:

- "납품 묶어줘"
- "컨택트시트 만들어"
- "최종본 정리해줘"
- "이번 프로젝트 비용 얼마 들었어?"
- "납품 다시 만들어" / "시트 갱신"
- "내부 검토용 시트 뽑아줘"(`--latest`)

NOT-trigger:

- "승인 처리해줘" → `/approve`
- "이 샷 다시 렌더" → `/render`, "부분 수정" → `/fix`
- "PDF로 묶어줘" → v1 범위 밖(JPG + 컨택트시트). 필요하면 `/specify`로 기능 명세

## 참조

- `scripts/contact_sheet.py`, `scripts/revision.py` (wp-a)
- `20-knowledge/backends.md` — usage 필드 해석
- `.gitignore` — `renders/` 제외 규칙
