---
name: development-image
description: "Codex 내장 이미지 도구로 그림을 만듭니다. 렌더 백엔드(pumasi·라우터 키)가 없는 PC에서 SketchUp 캡처를 AI 렌더로 바꾸거나, 스타일 팩 샘플·발표용 그림·참고 이미지를 만들 때 사용합니다. '이 캡처 렌더해줘', '내 PC에서 렌더해볼래', '코덱스로 렌더', '이미지 만들어줘', '그림 하나 뽑아줘', '팩 샘플 만들어줘' 같은 요청에 대응합니다. 단, 칠한 곳만 고치는 마스크 수정은 $development-fix, 강사 PC의 렌더 스크립트 실행은 $development-render를 사용합니다."
---

# $development-image — Codex 내장 이미지 도구로 그리기

이 스킬은 Codex에 들어 있는 이미지 생성 도구(gpt-image)만 씁니다. 다른 백엔드(grok, API 키 직접 호출)는 쓰지 않습니다.
pumasi 이미지 스킬의 절차를 이 폴더에 맞게 줄인 것입니다.

## 원칙

1. **모르는 것만 번호로 묻습니다.** 이 사용자는 Codex를 처음 쓰는 건축 실무자입니다. Codex에는 선택 카드가 없으므로 AGENTS.md의 "질문 방식"대로 채팅에 번호 선택지를 보여 주고 숫자로 답하게 합니다. 렌더에서 묻는 것은 **분위기(팩) 하나뿐**이고, 요청에 이미 있으면 묻지 않습니다. 비율·저장 위치는 묻지 않고 기본값을 씁니다. "알아서"라고 하면 추천으로 진행하고 무엇을 골랐는지 알립니다.
2. **API 키를 찾거나 쓰지 않습니다.** 환경변수·설정 파일에서 OpenAI·xAI 키를 읽어 이미지 API를 직접 부르는 일은 금지입니다.
3. **후처리 금지.** 만든 이미지를 자르거나 다시 저장(재인코딩)하지 않습니다. 원본 그대로 복사합니다.
4. **형태는 캡처를 따릅니다.** 렌더 모드에서는 층수·창 개수와 위치·지붕 모양을 바꾸지 않고 재질·빛·하늘·식생·사람만 입힙니다.
5. **끝에 쉬운 말로 보고합니다.** 개발 용어 없이: 무엇을 만들었는지, 어디에 저장했는지, 다음에 해 볼 것 하나.

## 모드 고르기

| 요청 | 모드 |
|---|---|
| 캡처(SketchUp 화면)를 렌더로 바꿔 달라 | **A. 렌더** |
| 그 밖의 그림 (팩 샘플, 발표용 이미지, 분위기 참고 등) | **B. 일반 그림** |

## A. 렌더 — 캡처를 AI 렌더로

분위기는 설계자의 취향이라 **사용자만 줄 수 있는 입력**입니다. 요청에 분위기·시간대·스타일이 없으면 **이미지를 만들기 전에 번호 질문만 보내고 이번 응답을 끝냅니다**(답을 받은 다음 응답에서 생성 — 리비전도 그때 만듭니다): 1 흐린 날 사진 느낌(`overcast-photoreal`, 추천) · 2 골든아워(`golden-hour`) · 3 저녁 시네마틱(`dusk-cinematic`) · 4 한낮 콘크리트(`midday-concrete`) · 5 항공 조감(`aerial-drone`) · 6 직접 말하기. 샘플 그림은 `assets/stylepacks/<팩>/samples/sample-01.png`. 비율은 묻지 않고 캡처 비율(16:9·4:3·3:2·1:1 중 가장 가까운 것)을 씁니다.

1. **캡처 찾기.** `assets/captures/<프로젝트>/<샷>/capture.png`. 사용자가 다른 폴더를 주면 먼저 `$development-intake`로 들여옵니다.
2. **리비전과 프롬프트 만들기** (이미지는 아직 만들지 않음):
   ```bash
   python3 scripts/render.py --input assets/captures/<P>/<S>/capture.png --project <P> --shot <S> --pack <팩> [--option k=v ...] --aspect <W:H> --dry-run
   ```
   출력의 `dir`가 새 리비전 폴더(`renders/<P>/<S>/Rnn`)이고, 그 안의 `prompt.txt`가 렌더 프롬프트입니다.
3. **이미지 생성.** Codex 이미지 도구에 **캡처 파일을 입력 이미지로 첨부**하고, `prompt.txt` 내용을 그대로 프롬프트로 씁니다. 끝에 한 줄을 덧붙입니다: `Output aspect ratio <W:H>. Keep the exact camera, geometry, roof shape and every window and door position of the attached image.`
4. **리비전에 붙이기.**
   ```bash
   python3 scripts/attach_render.py --dir renders/<P>/<S>/Rnn --latest-codex
   ```
   생성 이미지 경로를 알면 `--file <경로>`로 줍니다. 결과는 `renders/<P>/<S>/Rnn/render.png`, `meta.json`에 기록이 남습니다.
5. **확인.** 캡처와 렌더를 나란히 보여 주고, 지붕·창 개수·문 위치가 같은지 눈으로 봐 달라고 한 줄 덧붙입니다. 자동 점검은 `$development-qa <P> <S>`.

다시 뽑기: "다른 분위기로"는 팩만 바꿔 1번부터 다시 합니다(새 리비전이 생깁니다).

**표시한 그림으로 고치기**: 사용자가 렌더 위에 동그라미·화살표를 그려 첨부하면, 수정 지시를 한 줄로 확인("빨간 표시 부분의 난간을 검은 철제로 — 맞나요? 1 네 / 2 직접 고치기")한 뒤 **표시 없는 원본 렌더**를 입력 이미지로, 표시한 그림은 위치 참고용으로 함께 첨부해 다시 만듭니다. 프롬프트 끝에 `Change only the area marked in the second image; keep everything else identical to the first image. Do not draw the marks.`를 붙입니다. 결과는 새 리비전으로 저장합니다. "창 하나만 바꿔"처럼 부분 수정은 이 스킬로 하지 않고 `$development-fix`를 안내합니다. 이 PC에 마스크 수정 환경이 없으면 "전체를 다시 뽑되 바꿀 것만 말한다"로 대신하고, 나머지도 조금 흔들릴 수 있다고 알립니다.

## B. 일반 그림

기본값: 비율 16:9(발표·배경), 프로필·아이콘은 1:1, 세로 포스터는 2:3.

1. 요청을 한 장면으로 정리해 영어 프롬프트를 씁니다(200~400단어): 피사체·구도·빛·재질·카메라·분위기·피할 것. 글자가 들어가야 하면 그 문구를 따옴표로 묶어 그대로 넣습니다(이미지 도구가 한글도 직접 씁니다. 글자를 빼고 나중에 합성하지 않습니다).
2. 프롬프트를 `.imagen/prompt-<YYYYMMDD-HHMMSS>.md`에 저장하고 이미지 도구로 생성합니다.
3. 저장: `images/<YYYY-MM-DD>/<영문-슬러그>-<NN>.png` (같은 이름이 있으면 번호를 올림). 생성 원본은 `~/.codex/generated_images/` 아래 가장 최근 파일을 그대로 복사합니다.
4. 팩 샘플이면 저장 위치를 `assets/stylepacks/<팩>/samples/`로 하고, 프롬프트는 `python3 scripts/prompt_compose.py --pack <팩> --print` 결과를 씁니다.

## 출력 형식

```text
렌더를 만들었습니다 — demo-house / S02_corner / R03
- 스타일: 골든아워 (따뜻한 저녁빛), 비율 16:9
- 파일: renders/demo-house/S02_corner/R03/render.png (1672×941)
- 지붕 모양과 창 위치가 캡처와 같은지 한 번 봐 주세요.
다음에 해 볼 것: "흐린 날 느낌으로 다시" 라고 말해 보세요.
```

## 안 되는 경우

- 이미지 도구가 없다고 나오면: ChatGPT 무료 요금제는 이미지 생성이 안 될 수 있습니다. 요금제를 확인해 달라고 쉬운 말로 안내합니다.
- Pillow 오류가 나면: `python3 -m pip install --user pillow`를 한 번 실행하도록 안내합니다.
- `attach_render.py`가 이미지를 못 찾으면: 생성 이미지를 직접 저장한 경로를 `--file`로 넘깁니다.

## 트리거 경계

should-trigger: "이 캡처 렌더해줘", "내 컴퓨터에서 렌더해 볼래", "코덱스로 렌더", "이미지 만들어줘", "골든아워 팩 샘플 뽑아줘"
should-not-trigger: "2층 난간만 고쳐줘"($development-fix), "캡처 폴더 들여와줘"($development-intake), "어떤 스타일 있어?"($development-stylepack)

## 참조

- `scripts/render.py --dry-run` — 리비전·프롬프트·meta 기록
- `scripts/attach_render.py` — 생성 이미지를 리비전에 붙임
- `scripts/prompt_compose.py` — 팩 + 옵션으로 프롬프트 조립
- `20-knowledge/capture-protocol.md` — 캡처 규약
