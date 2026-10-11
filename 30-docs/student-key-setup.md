# 수강생 PC에서 마스크 수정(grok) 쓰기 — 키 설정 안내

웹툴에서 칠한 곳만 다시 그리는 **영역 수정(Fix)** 기능은 렌더 키가 있어야 돌아갑니다. 강사 PC는 키 보관함(tikeytaka)에서 키를 자동으로 읽지만, 수강생 PC에는 키 보관함이 없습니다. 그래서 강사에게 받은 키를 레포 폴더의 `.env` 파일 한 줄에 넣어 씁니다.

전체 렌더(gpt, Codex `$development-image`)에는 이 키가 필요 없습니다. 키는 마스크 수정에만 씁니다.

## 준비물

- 내려받은 `archi-render` 폴더(README의 "내려받기" 참고). 이전에 받았다면 **2026-10-11 이후 버전으로 다시 받아야** 합니다. 그 전 버전은 `.env`를 읽지 못합니다.
- 강사에게 받은 키 한 줄 (`sk-ir-`로 시작)
- 파이썬 3 (맥은 대부분 기본 설치)

## 1. 도구 설치 (처음 한 번)

맥 터미널:

```bash
python3 -m pip install --user pillow certifi
```

- `pillow`는 마스크 이미지 처리용, `certifi`는 HTTPS 인증서용입니다.
- certifi가 없으면 python.org에서 설치한 파이썬은 `CERTIFICATE_VERIFY_FAILED` 오류로 막힙니다. 이때는 위 명령을 다시 하거나, `응용 프로그램 > Python 3.x > Install Certificates.command`를 두 번 눌러 실행합니다.

## 2. `.env` 파일 만들기

레포 폴더 안에 `.env.example` 파일이 있습니다. 이것을 복사해 이름을 `.env`로 바꾸고 키를 붙여넣습니다.

### 방법 A — 터미널 (가장 확실)

```bash
cd ~/Desktop/archi-render          # 내려받은 폴더 위치로 바꾸세요
cp .env.example .env
open -e .env                       # 텍스트 편집기로 열림
```

편집기에서 `INSANE_ROUTER_KEY=` 바로 뒤에 키를 붙여넣고 저장합니다. 결과는 아래 한 줄 모양이어야 합니다(따옴표·띄어쓰기 없이).

```
INSANE_ROUTER_KEY=sk-ir-xxxxxxxxxxxxxxxx
```

### 방법 B — Codex에게 시키기

Codex에서 이 폴더를 연 채로 "`.env.example`을 `.env`로 복사해 줘"라고만 합니다. 키 값은 채팅에 붙이지 말고, 만들어진 `.env`를 방법 A처럼 직접 열어 붙여넣습니다.

### 파인더에서 `.env`가 안 보일 때

점(`.`)으로 시작하는 파일은 숨김 파일입니다. 파인더에서 `Cmd + Shift + .`을 누르면 보입니다.

## 3. 웹툴 다시 켜고 시험

```bash
cd ~/Desktop/archi-render
python3 webtool/server.py
```

브라우저에서 http://127.0.0.1:8765 를 엽니다. 렌더 결과에 브러시로 고칠 곳을 칠하고 지시문을 쓴 뒤 **영역 수정 (grok)** 을 누릅니다. 보통 15초 안팎이면 새 리비전(R01, R02 …)이 생깁니다.

`.env`를 고쳤으면 웹툴을 껐다가(터미널에서 `Ctrl + C`) 다시 켜야 반영됩니다.

## 키 읽는 순서

`scripts/render.py`는 아래 순서로 키를 찾고, 먼저 찾은 것을 씁니다.

1. 환경변수 `INSANE_ROUTER_KEY` (터미널에서 `export INSANE_ROUTER_KEY=...` 한 경우)
2. 레포 폴더의 `.env`
3. 강사 PC의 키 보관함(tikeytaka)

주소는 기본값 `https://router.axwith.com/api/v1`을 씁니다. 바꿀 일은 없습니다.

## 오류가 날 때

| 화면에 나온 말 | 뜻 | 할 일 |
|---|---|---|
| `라우터 키가 없습니다` | `.env`가 없거나 키 줄이 비어 있음 | 2단계를 다시. 파일 이름이 `.env.txt`가 아닌지 확인 |
| `router HTTP 401` | 키가 틀렸거나 잘림 | 키를 다시 복사해 붙여넣기(앞뒤 공백 없이) |
| `router HTTP 403` `model not allowed` | 이 키로 쓸 수 없는 모델 | 수강생 키는 grok 이미지 수정 전용입니다. 강사에게 문의 |
| `router HTTP 429` | 오늘 사용 한도를 다 씀 | 다음 날 다시 하거나 강사에게 문의 |
| `CERTIFICATE_VERIFY_FAILED` | 파이썬 인증서 없음 | 1단계의 certifi 설치 또는 Install Certificates |

## 지켜 주세요

- 키는 **수강생 공용**입니다. 하루 300회, 분당 20회까지 모두가 나눠 씁니다. 같은 수정을 반복해서 누르지 마세요.
- 키를 단톡방·블로그·GitHub 등에 올리지 마세요. `.env`는 git에 올라가지 않도록 이미 막혀 있습니다(`.gitignore`). ZIP으로 폴더를 남에게 넘길 때는 `.env`를 지우고 넘기세요.
- 키가 새어 나가면 강사가 키를 폐기하고 새로 나눠 드립니다.

## 미검증

- 윈도우 PC에서 웹툴을 돌려 본 적은 아직 없습니다. 윈도우는 `python` 또는 `py` 명령을 쓰고, 메모장으로 `.env`를 저장할 때 "파일 형식: 모든 파일"을 골라야 `.env.txt`가 되지 않습니다.
