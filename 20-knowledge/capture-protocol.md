# 캡처 규약 (SketchUp → assets/captures)

> `/intake`가 검사하는 항목의 정본. SketchUp에서 `scripts/sketchup/export_scenes.rb`를 1회 실행해 폴더를 덤프하고,
> 그 폴더를 이 워크스페이스로 옮기는 "폴더 인입" 구조다. 2026-10-11부터 이 맥에도 SketchUp 2026.2가 설치돼 있고,
> `open -a "/Applications/SketchUp 2026/SketchUp.app" --args -RubyStartup <script.rb>`로 실행할 수 있다(모델 창이 열린 뒤 스크립트가 돈다 — 첫 실행은 Trimble 로그인 필요).
> 자동 생성 예시: `scripts/sketchup/examples/build_demo_house.rb` → `assets/captures/demo-house/`.

## 왜 규약이 필요한가

SketchUp에는 네이티브 뎁스맵 export가 없다 (clm_026). 백엔드가 기하를 읽을 단서는 캡처 이미지의 면 음영과 윤곽뿐이다.
실측(E2·E4)에서 선화만 준 입력은 박공지붕이 모임지붕으로 드리프트했고, 면 음영이 애매한 매싱도 같은 문제를 보였다.
그래서 캡처는 "AI가 기하를 오독할 여지를 줄이는 방향"으로 고정한다.

## 필수 규약 (export_scenes.rb 기본값과 일치)

| # | 항목 | 값 | /intake 판정 |
|---|---|---|---|
| C1 | 스타일 | **클레이/모노크롬** (Monochrome 또는 흰 재질 + 면 음영). 텍스처·색 재질 끄기 | 위반 시 경고 + 재캡처 권고 |
| C2 | 그림자 | **On**. 태양 각도는 씬마다 고정 | 위반 시 경고 |
| C3 | 씬 잠금 | Scene(카메라) 저장·잠금. 같은 씬은 리비전 사이에 카메라가 바뀌지 않는다 | 씬 이름 누락 시 경고 |
| C4 | 해상도 | **긴 변 2000px 이상** PNG. 4000px 초과는 불필요 | 미달 시 **경고(차단 아님)** — 사용자가 알고 진행 가능 |
| C5 | 종횡비 | 씬별 고정. 납품 비율(16:9, 4:3, 3:2, 1:1 등)로 export 시점에 맞춘다. **export_scenes.rb는 화면(뷰포트) 비율을 그대로 쓰므로** 내보내기 전에 SketchUp 창 크기를 납품 비율에 맞춘다 — 울트라와이드 모니터 전체 화면이면 2000×479처럼 나온다(2026-10-11 실측) | 비표준 비율은 정보 표시, `--aspect`로 전달 |
| C6 | 파일명 | `<project>/<shot>/capture.png`. shot은 씬 이름을 slug화 (예 `S01_entrance`) | 규칙 불일치 시 rename 제안 |
| C7 | camera.json | **선택**. `{fov, eye, target, up, aspect, scene}` — 있으면 meta.json에 복사 | 없어도 진행 |
| C8 | 배경 | 단색(흰/회색). 하늘 그라데이션·워터마크 끄기 | 위반 시 경고 |

## 폴더 셰이프

```
assets/captures/<project>/
├── manifest.json            # /intake가 생성: 샷 목록·판정·해시
└── <shot>/
    ├── capture.png          # 필수
    ├── camera.json          # 선택
    └── notes.md             # 선택 (사용자 메모: 확정 재질·색)
```

`assets/captures/`는 git 추적(사람이 만든 원본). 클라이언트 실도면·CAD·계약 자료는 여기 넣지 않고 `70-private/<project>/`에 둔다(fail-closed, `meta.md`만 추적).

## 재캡처 트리거

- QA 경보가 같은 샷에서 반복될 때(지붕·개구부 드리프트) → 면 음영 강화·태양 각도 조정 후 재캡처.
- 리비전 간 카메라가 달라졌을 때 → Scene 잠금 확인 후 재캡처. 카메라가 다르면 R태그를 이어가지 않고 새 shot으로 등록한다.
