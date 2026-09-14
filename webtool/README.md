# webtool — 로컬 렌더 웹 툴

SketchUp 캡처를 올리고, 스타일 팩 + 옵션으로 프롬프트를 미리 보고, 렌더하고, 결과의 일부 영역을 마스크로 수정하는 단일 페이지 도구. Python 3 표준 라이브러리만 사용하고, 외부 CDN 없이 오프라인에서 동작한다.

## 실행

```bash
python3 webtool/server.py                 # http://127.0.0.1:8765
python3 webtool/server.py --port 9000     # 포트 변경
python3 webtool/server.py --root ~/other  # 다른 워크스페이스 루트 (기본: webtool/의 부모)
python3 webtool/server.py --stub          # scripts/ 대신 webtool/stubs/ 사용 (오프라인 UI 테스트)
```

127.0.0.1에만 바인딩한다. 종료는 Ctrl+C.

## 구성

| 파일 | 역할 |
|------|------|
| `server.py` | HTTP 서버 + JSON API. `scripts/prompt_compose.py`, `scripts/render.py`를 subprocess로 호출 |
| `static/index.html` `app.js` `style.css` | 단일 페이지 UI (빌드 없음) |
| `stubs/prompt_compose.py` `stubs/render.py` | 파이프라인 인터페이스를 흉내내는 스텁. `--stub`일 때만 사용. 렌더는 입력 이미지를 1초 후 복사 |

## API

| Method | Path | 입력 | 출력 |
|--------|------|------|------|
| GET | `/api/packs` | — | `[{id, name, mood, sample, slots}]` — `assets/stylepacks/*/pack.json`. 폴더 없으면 `[]` |
| POST | `/api/upload` | JSON `{project, shot, data(base64 또는 data URL), ext?}` 또는 multipart `project, shot, file` | `{path, url, size}` → `assets/captures/<P>/<S>/capture.<ext>` (샷당 1장, 덮어씀) |
| POST | `/api/compose` | `{pack, options}` | `{prompt}` — `prompt_compose.py --pack --option k=v … --print` |
| POST | `/api/render` | `{project, shot, pack, options, backend(gpt\|grok), aspect}` | render.py의 마지막 JSON 줄 + `url`, `log` |
| POST | `/api/fix` | `{project, shot, base, mask_png_base64, instruction, backend}` | 같은 JSON 형태 + `mask` (저장된 마스크 경로) |
| GET | `/api/revisions?project=&shot=` | — | `{project, shot, capture, revisions:[{revision, url, meta, masks}]}` |
| POST | `/api/pack/save` | `{id, name, options}` | `{id: "custom-<id>", path}` → `assets/stylepacks/custom-<id>/pack.json` |
| GET | `/`, `/app.js`, `/style.css` | — | 정적 파일 (`webtool/static/`) |
| GET | `/renders/…`, `/assets/…` | — | 워크스페이스 파일 읽기 전용 (경로 탈출 차단) |

오류는 항상 JSON `{error, …}`: 400 입력 오류 · 404 없음 · 502 스크립트 실패(`stderr` 포함) · 503 스크립트 파일 없음(`expected_path`) · 504 타임아웃.

**렌더 실행 모델**: 동기. `/api/render`, `/api/fix`는 스크립트가 끝날 때까지 응답을 기다린다(타임아웃 600초). 서버는 스레드 기반이라 대기 중에도 다른 요청은 처리된다. 잡 큐·폴링은 없다.

## 옵션 어휘

`app.js` 상단 `OPTIONS` 상수 한 곳에 있다. 정본은 `20-knowledge/stylepacks/OPTIONS.md`이며 바뀌면 이 상수를 맞춘다.

`prompt_compose.py`로 넘어가는 형태:
- 셀렉트: `mood=…`, `lighting=…`, `season_weather=…`, `camera=…`, `materials=…`, `post=…` (빈 값 = 팩 기본값, 전송 안 함)
- 엔투라지 토글: 켜진 것만 모아 `entourage=people,cars`
- keep_fixed: 줄바꿈을 `; `로 합쳐 `keep_fixed=a; b`
- aspect: `auto`가 아니면 `--aspect W:H` 플래그로 별도 전달

## 마스크 규약

- 내부 표준: **8-bit grayscale PNG, 255 = 수정 영역, 0 = 유지**, 픽셀 크기 = 기준 렌더의 원본 크기.
- 브라우저는 표시 배율과 무관하게 `naturalWidth × naturalHeight` 오프스크린 캔버스에 스트로크를 기록하고, 내보낼 때 0/255로 이진화한다. 캔버스가 만드는 PNG는 RGBA이므로 서버가 `png_to_gray()`로 진짜 L 채널 PNG로 재인코딩해 `renders/<P>/<S>/<base>/mask_<n>.png`에 저장한다.
- 벤더별 변환(grok의 alpha0=edit 등)은 `scripts/mask_convert.py` 담당이며 여기서는 하지 않는다.

## 한계

- **gpt 백엔드는 마스크 입력이 없다.** Fix는 항상 grok으로 보낸다(UI에서 고정).
- 렌더는 동기 호출이라 브라우저 탭을 닫으면 결과 확인은 리비전 탭 새로고침으로 해야 한다(스크립트 자체는 끝까지 실행됨).
- 팩 저장은 UI 옵션만 기록한다. 실제 팩의 자유 문장 슬롯(`shot_type`, 상세 재질 목록 등)은 원본 팩(`source_template`)에서 상속한다.

## 문제 해결

| 증상 | 원인 / 조치 |
|------|-------------|
| 프롬프트 미리보기에 "프롬프트 스크립트가 아직 없습니다" (503) | `scripts/prompt_compose.py`가 없음. 응답의 `expected_path` 확인 |
| 502 `script failed` + traceback | 스크립트 자체 오류. `stderr`를 읽는다. 흔한 것: 없는 pack id, 라우터 키 미설정 |
| 렌더 버튼 비활성 | 팩 미선택 또는 캡처 미업로드. 프로젝트/샷을 바꾸면 그 샷의 캡처를 다시 불러온다 |
| Fix 모드 토글이 안 켜짐 | 리비전이 없음. 먼저 렌더 |
| 단축키 B/E/Z 무반응 | 텍스트 입력란에 포커스가 있음. 캔버스나 빈 곳을 클릭 |
| 팩 카드에 "샘플 없음" | `pack.json`의 `samples[0]`이 팩 폴더 기준 상대경로로 존재해야 함 |
| 포트 충돌 | `--port` 변경 |
