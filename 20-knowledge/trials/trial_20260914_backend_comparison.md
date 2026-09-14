# 실도면 트라이얼 — 2026-09-14

입력 4장(카페 스케치 1153px, 카페 주차장 뷰 2560→2048px, 단지 배치도 300px, 놀이터 656px) + 스타일 레퍼런스(테슬라 노을 사진, 프롬프트로만 반영).

## 백엔드 2종 비교
| 경로 | 호출 | 소요 | 결과 |
|---|---|---|---|
| insane-router `x-ai/grok-imagine-image-2.0` `/images/edits` | curl multipart, image= | 12~18s | 레이아웃·재질 반영 양호. 저해상 입력도 통과. 천막 색 변경·가로수 소실 등 소폭 드리프트. 마스크 인페인팅 지원(E3 실측) |
| gpt-image via pumasi `imagen.sh --ref <source>` (Codex image_gen) | 프롬프트 파일 + `--ref` | 약 1~2분/장 | 재질 질감·조명·유리 반사·식생 사실성 뚜렷히 우세. 기하·간판·인물 위치 보존 우수. 출력 비율은 입력 비율 근사(1448×1086 등). **마스크 입력 없음**(레퍼런스 첨부만) |

## 설계 함의 (02 문서 P3·P5 보정)
- 1차 렌더(전체 샷): **gpt-image(pumasi --ref)** 를 기본으로 승격. 품질 우위가 크고 구독 경로라 비용 0.
- 영역 수정(마스크): grok 편집 API 유지 — gpt 경로는 마스크가 없음. 즉 "전체는 gpt, 부분 수정은 grok" 2단 구성. 또는 gpt로 재생성 시 프롬프트에 "only change X" 지시로 근사.
- 프롬프트 계약: "Use the attached SketchUp image as the exact source. Keep geometry/camera/positions… Do not add or remove…" 고정 꼬리 + 재질·조명·엔투라지 슬롯. 색 확정 요소는 "(keep them white)"처럼 명시.

파일: `*_gpt.png`(gpt), `*.jpg`(grok), `contact_sheet_grok_vs_gpt.jpg`(3열 비교, 데스크톱 복사본 `render_trial_grok_vs_gpt_20260914.jpg`), `gpt/*.prompt.txt`(사용 프롬프트).
