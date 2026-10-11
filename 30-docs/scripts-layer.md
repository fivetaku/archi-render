# scripts — 결정론 스크립트 레이어

> 데이터·코퍼스를 변환/검출/스코어링하는 스크립트를 두는 표준 위치. 표준 라이브러리만 쓰고,
> 에이전트가 손으로 매칭·계산하지 말고 여기 스크립트로 결정론화한다(환각 방지).

## 무결성 규약 (fabulous 관례 — 채점기도 게이트 대상)

- 판정·필터·스코어링 스크립트는 **`--selftest`를 동봉**한다. 합성 케이스로 자기 검증이 통과해야
  실제 데이터에 적용한다. "검사하는 코드도 검사 대상"이 원칙이다.
- 예: `python3 scripts/detect.py --selftest` → 알려진 입력에 알려진 출력이 나오는지 확인 후 exit 0/1.
- 외부 소스를 읽는 스크립트는 "fetch 실패"와 "결과 0"을 sentinel로 구별한다(빈 입력을 성공으로 오판 금지).

## 관례

- stdlib 우선 (설치 의존 최소화). 예외: `render.py`·`mask_convert.py`·`attach_render.py`는 Pillow 필요(`python3 -m pip install --user pillow`), HTTPS는 certifi가 있으면 그 인증서를 쓴다(python.org 설치본의 인증서 누락 대비).
- 입력은 읽기 전용, 출력은 별도 경로. 원본 payload를 덮어쓰지 않는다.
