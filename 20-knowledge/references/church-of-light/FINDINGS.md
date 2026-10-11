# 안도 다다오 「빛의 교회」(茨木春日丘教会 礼拝堂, 1989) — SketchUp 모델링용 치수·형태 리서치

조사일: 2026-10-11 · 도면 파일: `drawings/` · 참고 사진/모형: `reference/` · 이미지 출처 목록: `drawings/SOURCES.md`

## 0. 읽는 법

- **확신도**: 높음 = 공식/복수 출처 일치 · 중간 = 단일 출처이거나 도면 실측(오차 ±5cm 내외) · 낮음 = 추정/저해상도 판독/출처 간 충돌
- **[실측]** = 내가 도면 이미지의 축척 막대로 직접 잰 값. 주 도면은 kenchikuzukan(건축도감) CAD 재작도본 4장(7017×4958px, 축척 막대 0‑1‑3m, 1m = 약 236px).
  - 평면도는 공표 치수(내부 5.90 × 17.70)와 오차 1cm 이내로 맞음 → 수평 치수 기준으로 사용
  - **종단면도는 가로 방향이 약 86%로 압축돼 있음**(내부 길이가 15.3m로 나옴) → 단면도에서는 **높이 값만** 사용
- **[추정]** = 계산·교차검증으로 얻은 값. 원 자료에 그 숫자가 직접 있지는 않음.
- 방위 표기: 이 건물은 **긴 축이 거의 남북**이고, 십자가 벽(제단)이 **남남동**을 봄. 영문 자료 상당수의 "east wall"은 틀린 것으로 판단함(7절 참고).

### 모델링 좌표계 제안 (이하 표의 X/Y/Z)
- 원점: 십자가 벽 **내면** × 동측 벽 **내면** × 뒤쪽(입구 쪽) 바닥 마감면
- X: 제단 → 입구 방향(북북서), 0 ~ 17.70 · Y: 동측 내면 → 서측 내면, 0 ~ 5.90 · Z: 뒤쪽 바닥 = 0 (외부 GL은 약 −0.15)

---

## 1. 본당 콘크리트 박스

| 항목 | 값 | 출처 URL | 확신도 |
|---|---|---|---|
| 기본 구성 | 지름 5,900mm 구 3개가 들어가는 직육면체 + 이를 비스듬히 관통하는 벽 1장 | https://artsandculture.google.com/story/2QVRGQpQrOQ8sQ?hl=ja (안도 사무소 감수) | 높음 |
| 내부 치수 (폭×길이×높이) | 5.9 × 17.7 × 5.9 m ("5.9m 큐브 3개") | https://en.wikipedia.org/wiki/Church_of_the_Light · https://architectuul.com/architecture/church-of-the-light | 높음 |
| 〃 (다른 표기) | 6 × 6 × 18 m | https://es.wikiarquitectura.com/edificio/iglesia-de-la-luz · https://www.slideshare.net/slideshow/church-of-light-case-study/59121745 | 높음(반올림 값) |
| 〃 (다른 표기) | 18 × 6 × 6 m | https://hash-casa.com/2018/01/15/ibarakikasugaokachurch/ | 높음(반올림 값) |
| 〃 (다른 표기) | 폭 5.9 × 깊이 17.7, 천장고 5.9~7.0 m | https://www.mirainoshitenclassic.com/2017/02/hikarichurch-arc9.html | 높음 |
| 내부 폭 [실측] | **5.90 m** | kenchikuzukan 평면도 (drawings/plan_kenchikuzukan_cad_7017px.jpg) | 높음 |
| 내부 길이 [실측] | **17.71 m** | 〃 | 높음 |
| 천장고 | **5,900 ~ 7,000 mm** (바닥이 계단식으로 내려가므로 뒤쪽 5.9, 제단 7.0) | https://www.mooponto.com/architecture/church-of-the-light-tadao-ando-architect-associates/ | 높음 |
| 천장고 [실측] | 뒤쪽 바닥 5.90 m · 제단 바닥 7.00 m (단면도 높이 측정 + 계단 11단 × 0.10) | kenchikuzukan 종단면도 | 높음 |
| 측벽(동·서) 두께 | **380 mm** (15 in) | https://en.wikipedia.org/wiki/Church_of_the_Light | 높음 |
| 측벽 두께 [실측] | 0.38 m (동·서 모두) | kenchikuzukan 평면도 | 높음 |
| 측벽 두께 (다른 값) | "38cm 정도" / 십자가 벽 "두께 40cm" (방문 건축가의 육안 추정) | https://m.blog.naver.com/ywpark5293/221441667023 | 낮음 |
| 단부벽(십자가 벽·북측 벽) 두께 [실측] | 약 0.25 m (CAD 재작도본 기준) | kenchikuzukan 평면도 | 중간 |
| 단부벽 두께 [추정] | 0.25~0.30 m. 건축면적 113.04 = 6.28 × 18.00(벽심)이 정확히 맞으려면 단부벽 0.30 | 계산 (아래 "바닥면적" 행) | 낮음 |
| 외부 폭 [실측] | **6.66 m** (5.90 + 0.38×2) | kenchikuzukan 평면도·남측 입면도 | 높음 |
| 외부 길이 [실측] | **18.21 m** (단부벽 0.25 기준) / 단부벽 0.30이면 18.30 m [추정] | kenchikuzukan 평면도 | 중간 |
| 벽심 길이 | **18,000** ("9,000 + 9,000"으로 읽힘) | 안도 사무소 실시설계 배치도 (Naver 블로그 재게재, 저해상도) drawings/plan_site_ando_working_drawing_dims_lowres.jpg | 낮음(판독 불확실) |
| 외부 높이 [실측] | 지붕 상단 = 북측 GL + **6.94 m** (Z = +6.79) | kenchikuzukan 종단면도 | 중간 |
| 최고 높이 | **7,240 mm** (기준 레벨 미기재. 제단 바닥 기준 약 7.9, GL 기준 6.94라 기준면 불명) | https://www.mooponto.com/architecture/church-of-the-light-tadao-ando-architect-associates/ | 중간 |
| 높이 (다른 표기) | "높이 약 6~7m" | https://www.instagram.com/p/DdpVa2NE_zk/ | 낮음 |
| 지붕층 두께 [실측] | 천장면(Z 5.90) → 지붕 상단(Z 6.79) 약 0.89 m (슬래브+파라펫/중공부 포함, 단면도에 내부 사각형 표시) | kenchikuzukan 종단면도 | 중간 |
| 건축면적 / 연면적 | **113.04 m²** / 113.04 m² | https://www.mooponto.com/architecture/church-of-the-light-tadao-ando-architect-associates/ · https://www.architecturelab.net/church-of-the-light-tadao-ando-architect-associates/ | 높음 |
| 〃 (다른 값) | 113 m² | https://www.archiweb.cz/en/b/church-of-light · Wikipedia | 높음 |
| 〃 (다른 값) | 113.3 m² | https://www.slideshare.net/slideshow/church-of-light-case-study/59121745 | 낮음 |
| 바닥면적 검산 [추정] | 6.28 (벽심 폭 = 5.90+0.38) × 18.00 (벽심 길이) = **113.04** 로 정확히 일치 | 계산 | 중간 |
| 구조 | RC 벽식구조 (ja.wikipedia) vs. "Rahmen(라멘) 구조, 1F" (mooponto). **출처 간 충돌** | https://ja.wikipedia.org/wiki/茨木春日丘教会 · mooponto | 낮음 |
| 시공 / 설계·공사 기간 | 竜巳建設(Tatsumi) / 설계 1987.5~1988.4, 공사 1988.5~1989.4 | mooponto · ja.wikipedia | 높음 |

## 2. 정면(제단) 벽의 십자 슬릿

| 항목 | 값 | 출처 URL | 확신도 |
|---|---|---|---|
| 형태 | 세로 슬릿은 바닥~천장, 가로 슬릿은 벽~벽 전체. 콘크리트 줄눈과 정확히 맞춤 | https://en.wikipedia.org/wiki/Church_of_the_Light | 높음 |
| 구조 | 슬릿이 벽 끝까지 가므로 벽이 4조각으로 나뉘고, 위쪽 절반(약 10t)은 천장에 매달린 구조. 시공사가 팔 길이 축소를 제안했으나 안도가 거부 | https://hash-casa.com/2018/01/15/ibarakikasugaokachurch/ · http://www.hetgallery.com/church-of-the-light.html | 높음 |
| 슬릿 폭 [실측] | 세로·가로 모두 **약 0.20 m** | kenchikuzukan 남측 입면도 | 중간 |
| 슬릿 폭 (다른 값) | "20cm 정도로 보인다" (육안 추정) | https://m.blog.naver.com/ywpark5293/221441667023 | 낮음 |
| 슬릿 폭 (다른 값) | "모든 틈이 15cm" / "15cm 폭 유리" | https://www.topys.cn/article/453 · https://zhuanlan.zhihu.com/p/20111546 | 낮음 |
| 슬릿 폭 사진 검증 [추정] | 위키미디어 내부 사진(내부 폭 5.9m 기준 환산): 세로 약 0.21 m, 가로 약 0.19 m (빛 번짐 포함) | reference/photo_interior_commons_2006.jpg | 낮음 |
| 세로 슬릿 위치 | 벽 **정중앙** (Y = 2.85~3.05, 중심 2.95). 슬릿 중심선 = 패널 세로 줄눈 | kenchikuzukan 남측 입면도 [실측] | 높음 |
| 세로 슬릿 길이 (내부) | 제단 바닥(Z −1.10) ~ 천장(Z 5.90) = **약 7.0 m** | 천장고 행 + kenchikuzukan 남측 입면(점선이 GL 아래 제단 레벨까지 내려감) | 중간 |
| 가로 슬릿 길이 | 내부 폭 전체 **5.90 m** (외부에서는 측벽 두께 0.38만큼 덜 보임) | kenchikuzukan 남측 입면도 [실측] | 중간 |
| 가로 슬릿 높이 [실측] | 슬릿 중심 = 외부 GL + 3.10 m = **제단 바닥 + 약 4.05 m** = 천장 − 약 2.95 m (Z ≈ +2.95, 밴드 Z 2.85~3.05) | kenchikuzukan 남측 입면 + 종단면 | 중간 |
| 가로 슬릿 높이 사진 검증 [추정] | 제단 바닥 + 약 4.1 m, 천장 − 약 2.9 m | reference/photo_interior_commons_2006.jpg | 낮음 |
| 유리 | 원래 유리 없이 계획했으나 교회 측 반대로 투명 유리 삽입. 프레임 없이 슬릿 중앙에 매립, 교차부는 유리 맞댐 접합 | ja.wikipedia · https://m.blog.naver.com/ywpark5293/221441667023 | 높음 |
| 외부 소형 십자가 | 안도 사무소 동측 입면도에 외벽 북쪽 상부에 작은 십자가 표기 | drawings/elevation_west_east_ando_office.jpg | 낮음 |

## 3. 15도 사선 벽 · 출입구

| 항목 | 값 | 출처 URL | 확신도 |
|---|---|---|---|
| 각도 | 박스 긴 축에 대해 **15°** | Wikipedia · https://architectuul.com/architecture/church-of-the-light · archiweb | 높음 |
| 각도 [실측] | 15.0° (도면 직선 피팅) | kenchikuzukan 평면도 | 높음 |
| 성격 | 박스·천장 어디에도 닿지 않는 독립 벽. 천장과의 틈으로 빛이 들어옴 | https://www.arckit.com/blogs/news/tadao-ando-s-church-of-the-light · mooponto | 높음 |
| 평면 형태 | "7"자: 제단 끝 바깥에서 시작해 남측 벽과 평행한 리턴 벽 + 15° 장벽 | https://www.50for50.world/projects/church-of-the-light · https://m.blog.naver.com/ywpark5293/221441667023 | 높음 |
| 두께 [실측] | 약 0.28 m | kenchikuzukan 평면도 | 중간 |
| 높이 [실측] | 외부 GL + **약 5.87 m** (Z ≈ +5.72). 천장보다 약 0.17 m 낮아 빛 틈이 생김 | kenchikuzukan 남·북측 입면도 | 중간 |
| 높이 (다른 값) | "사벽 높이 약 5m" / 벽과 천장 사이 틈 약 15cm | https://m.blog.naver.com/ywpark5293/221441667023 | 낮음 |
| 높이 (정성) | 본체보다 낮은 벽 | https://www.metalocus.es/en/news/shaping-light-church-light-tadao-ando | 높음 |
| 장벽(긴 조각) 길이 [실측] | 약 **17.6 m** (리턴 벽 모서리 → 실내 끝단) | kenchikuzukan 평면도 | 중간 |
| 장벽 시작점 [실측] | 리턴 벽 모서리: X ≈ −2.03 (남측 외면에서 1.78 남쪽), Y ≈ 9.15 (서측 외면에서 2.87 서쪽) | 〃 | 중간 |
| 서측 벽 관통 위치 [실측] | 15° 벽이 서측 벽면을 지나는 구간 **X ≈ 7.6 ~ 10.1** (벽 두께 포함) | 〃 | 중간 |
| 장벽 실내 끝단 [실측] | X ≈ 14.98, Y ≈ 4.30 (서측 내면에서 1.6 m) | 〃 | 중간 |
| 예배당 진입 개구(사벽 틈) [실측] | 장벽 끝과 짧은 조각 사이 **약 1.6 m**(벽 방향), 문 없이 위아래 전체가 트임 | kenchikuzukan 평면도 · Naver 블로그("5m 높이 개구부, 문짝 없음") | 중간 |
| 짧은 조각 [실측] | X 16.52 → 18.97, 길이 약 2.5 m. **북측 벽을 관통해 외부로 약 1.0 m 돌출** (벽과 양쪽 약 15cm 틈, 유리 매립) | kenchikuzukan 평면도 · Naver 블로그 | 중간 |
| 리턴 벽 [실측] | 남측 외면에서 1.50 m 떨어져 평행(두께 0.28). 높은 부분 Y 5.19 ~ 9.15(약 4.0 m), 높이 GL + 5.87. 동쪽 나머지는 낮은 벽/옹벽 | kenchikuzukan 평면·남측 입면 | 중간 |
| 리턴 벽과 십자가 벽 사이 | 아래로 내려가는 계단이 있는 좁은 골목(roji)과 드라이 에어리어(남측 입면 점선, GL 약 −1.1까지) | https://www.moma.org/documents/moma_catalogue_348_300085246.pdf · kenchikuzukan 평면(계단 5단, 단너비 약 0.39) | 중간 |
| 서측 벽 유리 개구 [실측] | X ≈ **3.49 ~ 14.41** (약 10.9 m). 유리 구간 3.53–5.61 / 5.65–8.09 / (15°벽) / 9.45–11.82 / 11.97–14.33. 높이는 거의 천장까지(안도 서측 입면 비율 기준 GL + 약 5.9) | kenchikuzukan 평면도 · drawings/elevation_west_east_ando_office.jpg | 중간 |
| 건물 출입구 [추정] | 서측 유리벽 북쪽 끝 구간(X ≈ 12~14.4)의 유리 미닫이문 → 삼각형 전실(방풍실) → 사벽 틈으로 예배당 진입 | Naver 블로그 · hetgallery 평면 ② 표기 위치(X ≈ 13) | 낮음 |
| 접근 동선 | 동측 도로에서 언덕을 올라 북측 벽을 따라 돌아 서측으로. 도로에서 바로 들어가지 않고 벽을 따라 돌아 들어감 | https://m.blog.naver.com/ywpark5293/221441667023 · https://artsandculture.google.com/story/2QVRGQpQrOQ8sQ?hl=ja | 높음 |

## 4. 내부 (바닥 단차 · 벤치 · 천장)

| 항목 | 값 | 출처 URL | 확신도 |
|---|---|---|---|
| 바닥 형식 | 제단 쪽으로 **계단식으로 내려감**(강의실·음악홀처럼, 제단이 가장 낮음) | https://artsandculture.google.com/story/2QVRGQpQrOQ8sQ?hl=ja · ja.wikipedia | 높음 |
| 단 수 · 단 높이 [실측] | **11단 × 약 100 mm = 총 1.10 m** | kenchikuzukan 종단면도(하부 윤곽 계단 11개, 각 23.5px ≈ 0.10 m) | 중간 |
| 검증 | 천장고 5.9 → 7.0 m의 차이 1.1 m와 일치 | mooponto | 높음 |
| 단 너비 [실측] | **900 mm × 10단** (단 선 X = 3.45, 4.35, … 12.45) | kenchikuzukan 평면도 | 중간 |
| 단 너비 (도면 판독) | 실시설계 배치도에 "900"이 반복되고 양 끝에 "3,450", "5,250"으로 읽힘 | drawings/plan_site_ando_working_drawing_dims_lowres.jpg | 낮음(저해상도) |
| 제단 영역(최저 바닥) [실측] | X 0 ~ 3.45 (깊이 3.45 m), Z = −1.10 | kenchikuzukan 평면·단면 | 중간 |
| 뒤쪽 평탄 영역(입구 레벨) [실측] | X 12.45 ~ 17.70 (깊이 5.25 m), Z = 0 (외부 GL + 약 0.15) | 〃 | 중간 |
| 계단 레벨 (모델링용) [추정] | X 3.45~4.35: −1.00 / 4.35~5.25: −0.90 / … / 11.55~12.45: −0.10 / 이후 0.00 | 위 실측값 조합 | 중간 |
| 벤치 배치 (안도 배치도) | **중앙 통로 + 좌우 2열**. 동측 12줄, 서측 11줄(사선 벽 때문에 뒤쪽이 짧아짐) | drawings/plan_site_ando_pencil_scalebar_northarrow.jpg (Naver 블로그) | 중간 |
| 벤치 배치 (다른 도면) | hetgallery: 계단 10줄 + 뒤쪽 평지 2줄 = 12줄 · kenchikuzukan: 단마다 1줄(10줄), 중앙선으로 2분할 | http://www.hetgallery.com/church-of-the-light.html · kenchikuzukan 평면 | 중간 |
| 중앙 통로 | 사진에서 중앙 통로 확인 (2006년 촬영 내부, 안도 모형) | reference/photo_interior_commons_2006.jpg · reference/photo_model_commons.jpg | 높음 |
| 벤치 치수 [실측/추정] | 좌판 깊이 약 0.37 m, 한쪽 길이 약 2.2~2.3 m, 줄 간격 0.9 m(단 너비와 같음) | kenchikuzukan 평면 · 안도 배치도 | 낮음 |
| 재료 | 바닥·벤치 모두 공사용 비계 발판(足場板, 삼나무) 재사용, 검은 오일스테인 | ja.wikipedia · http://www.hetgallery.com/church-of-the-light.html | 높음 |
| 천장 | 평천장(노출콘크리트), 천장고 5.9~7.0 | mooponto | 높음 |
| 기타 실내 | 2005년 뒤쪽(북측) 벽 거의 전체에 Bosch 파이프오르간 설치. 동측 벽 벽부등 몇 개 | ja.wikipedia · Naver 블로그 | 높음 |

## 5. 노출콘크리트 · 지붕

| 항목 | 값 | 출처 URL | 확신도 |
|---|---|---|---|
| 패널 크기 [실측] | **1,800 × 900 (가로로 눕혀 사용)**. 외벽 줄 높이 0.85~0.90 실측 | kenchikuzukan 남측 입면도 | 중간 |
| 패널 크기 (다른 출처) | 다다미 비율 약 1.8 × 0.9 m, 패널당 구멍 6개 (안도 일반론) | https://www.studiomatrx.org/guides/tadao-ando-facade-design | 중간 |
| 패널 크기 (다른 출처) | 안도가 자주 쓰는 900×1800 가로 사용 + 세퍼 간격 @450·@600 (일본 설계자 블로그, 일반론) | https://one-archi.com/exposed-concrete/ | 중간 |
| 패널 크기 (다른 값) | "1500×750 정도 모듈, 콘구멍 6개" (육안 추정) | https://m.blog.naver.com/ywpark5293/221441667023 | 낮음 |
| 폼타이 구멍 [실측] | 패널당 **3 × 2 = 6개**, 가로 간격 **600**, 세로 간격 **450**, 세로 줄눈에서 300 떨어짐 | kenchikuzukan 남측 입면도 (구멍 166개 자동 검출) | 중간 |
| 폼타이 사진 검증 [추정] | 내부 십자가 벽에서도 구멍 간격 약 0.6 × 0.45 m, 슬릿 양옆 패널 폭 약 1.8 m | reference/photo_interior_commons_2006.jpg | 낮음 |
| 패널 줄눈 정렬 | 세로 슬릿 중심선이 패널 줄눈, 가로 슬릿이 수평 줄눈 줄에 맞춤 | Wikipedia · mooponto | 높음 |
| 수평 줄눈 | 중간 높이(가로 슬릿 높이)에 두께 약 3cm 큰 수평 줄눈이 박스를 한 바퀴 돎. 안도 입면도에서도 굵은 선으로 표시 | Naver 블로그 · drawings/elevation_*_ando_office.jpg | 중간 |
| 외벽 줄 높이 [실측, 남측 GL 기준] | 0.30 / 1.20 / 2.10 / (3.00~3.20 슬릿) / 3.50 / 4.34 / 5.19 / 6.05 / 6.94(지붕 상단) | kenchikuzukan 남측 입면도 | 중간 |
| 지붕 | **평지붕**. 파라펫 있음. 위성사진상 상부는 자갈/흙 덮임 | 단면도 · reference/site_satellite_google_z21_crop.jpg | 중간 |
| 지붕 관련 일화 | 자금 부족으로 지붕 없이 지을 뻔했으나 시공사가 지붕을 기부 | Wikipedia · Google Arts & Culture | 높음 |

## 6. 1999년 일요학교(교회 홀) 별동

| 항목 | 값 | 출처 URL | 확신도 |
|---|---|---|---|
| 준공·시공 | 1999년 2월, 錢高組(Zenitaka). 설계 1997.5~1998.4, 공사 1998.5~1999.2 | mooponto · ja.wikipedia | 높음 |
| 건축면적 / 연면적 | **116.80 m² / 148.80 m²** (2층, 라멘조) | https://www.mooponto.com/architecture/church-of-the-light-tadao-ando-architect-associates/ | 높음 |
| 〃 (다른 값) | 117 m² / 149 m² | https://www.archiweb.cz/en/b/nedelni-skola | 높음 |
| 최고 천장고 | 6,050 mm (홀 부분 2층 높이 + 메자닌에 주방·발코니) | mooponto · archiweb | 높음 |
| 위치 | 옛 목조 예배당 자리. 본당 **서쪽**, 본당 남쪽 절반 옆 | ja.wikipedia · reference/site_satellite_google_z21_crop.jpg | 높음 |
| 관계 | "예배당과 같은 크기의 콘크리트 박스를 쌍이 되게 배치하고 그 사이에 포치 등 공용공간" (안도 사무소 설명) | https://artsandculture.google.com/story/2QVRGQpQrOQ8sQ?hl=ja | 높음 |
| 실제 크기 [추정] | 위성사진: 지붕 약 15.5 × 6.5 m (본당 같은 사진에서 18.4 × 6.5) / hetgallery 평면 비율: 약 14.4 × 6.3 m → **"같은 크기"라는 설명보다 짧아 보임** | 위성(Google z21) · http://www.hetgallery.com/church-of-the-light.html | 낮음 |
| 배치 각도 [추정] | 일요학교 긴 축 방위 약 93°/273° → 본당 축과 **약 60~64°** (hetgallery 평면 61°, 위성 62~64°) | 위성 · hetgallery 평면 | 중간 |
| 자체 사선 벽 | 일요학교도 독립벽이 관통(남쪽 면을 따라 15°). 두 동 사이 삼각 마당에 원형 콘크리트 벤치, 두 입구를 잇는 캐노피 | mooponto · https://www.topys.cn/article/453 | 높음 |
| 내부 | 밝은 피나무(シナ) 합판·원목, 평바닥 좌석, 1층에 1988년 안도 사무소가 만든 빛의 교회 모형 전시 | ja.wikipedia · mooponto | 높음 |
| 2010년 | 목사관도 안도 설계로 개축 (위성 기준 대지 북서쪽, 반원형 평면 건물) | ja.wikipedia · hetgallery | 높음 |

## 7. 대지 방위 · 주변

| 항목 | 값 | 출처 URL | 확신도 |
|---|---|---|---|
| 주소 · 좌표 | 大阪府茨木市北春日丘4-3-50 · 34.818528 N, 135.537028 E | https://ja.wikipedia.org/wiki/茨木春日丘教会 | 높음 |
| 대지면적 | 838.60 m² (838.6 / 838.8 / 839로도 표기) | mooponto · archiweb · slideshare | 높음 |
| 도로 접면 폭 | 동측 5.42 m, 남측 6.11 m | mooponto | 중간 |
| **본당 긴 축 방위** [추정] | **약 154~157° / 334~337°** (거의 남북, 시계방향 약 25° 회전) | OSM 건물 way 597276853(변 방위 153.8°) · Google 위성 z21 실측(약 157°) | 높음 |
| **십자가(제단) 벽 방향** | **남남동(약 155°)을 향함**. 입구 쪽은 북북서 | 위 방위 + 안도 사무소 입면도에서 십자가 면이 "South Elevation" · Naver 블로그("남측 제대", "동측 도로에 면함") · 안도 배치도 방위표 | 높음 |
| 〃 (충돌 출처) | "cross on the east façade/wall" | https://architectuul.com/architecture/church-of-the-light · https://www.architecturelab.net/church-of-the-light-tadao-ando-architect-associates/ · slideshare | 낮음 (실제 배치와 불일치) |
| 사선 벽 쪽 | 15° 벽·출입구·일요학교는 **서쪽**, 동쪽 긴 벽은 도로에 면함 | 위성 · Naver 블로그 | 높음 |
| 대지 내 위치 | 두 도로(동측 남북 도로, 남측 동서 도로) 교차로 쪽 **대지 남동 모서리** | 위성 · https://en.wikipedia.org/wiki/Church_of_the_Light ("on the corner of two streets") | 높음 |
| 지형 [실측] | 동측 도로가 교회 GL보다 약 2.0 m 낮음(경사면, 언덕길로 진입) | kenchikuzukan 남·북측 입면도 · Naver 블로그 | 중간 |
| 주변 | 오사카 북쪽 25km 교외의 조용한 단독주택가. 남쪽 도로 건너 저층 아파트, 동쪽은 주차장. 기존 수목 보존 | Wikipedia · https://smile-log.net/light-church/ · 위성 | 높음 |
| 대지 구성 | 예배당 + 일요학교 + 목사관 3동 | http://www.hetgallery.com/church-of-the-light.html | 높음 |
| 참고: 견학 | 2024년부터 건물 견학 전면 중지 (현장 실측 불가) | http://ibaraki-kasugaoka-church.jp/e-top.html | 높음 |

---

## 8. SketchUp용 종합 치수 세트 (권장값, 모두 위 표 근거의 [추정] 종합)

```
박스 내부        : X 0~17.70, Y 0~5.90, 천장 Z 5.90
측벽(동·서)      : 0.38 → 외부 Y −0.38 ~ 6.28
단부벽(남·북)    : 0.25 (0.30도 가능) → 외부 X −0.25 ~ 17.95
지붕             : 평지붕, 천장 Z 5.90 → 지붕 상단 Z 6.79, 외부 GL Z −0.15
바닥             : 제단 X 0~3.45 Z −1.10 / 단 10개(0.90 깊이, 0.10 높이) X 3.45~12.45 / 뒤쪽 X 12.45~17.70 Z 0
십자 슬릿(폭 0.20): 세로 Y 2.85~3.05, Z −1.10~5.90 / 가로 Z 2.85~3.05, Y 0~5.90 (남측 벽 관통)
15° 벽           : 두께 0.28, 상단 Z ≈ 5.72(천장과 약 0.18 틈)
                   장벽 (−2.03, 9.15) → (14.98, 4.30) / 틈 약 1.6 / 단벽 X 16.52~18.97 (북측 벽 관통, 1.0 돌출)
리턴 벽          : X −2.03~−1.75, Y 5.19~9.15, 높이 GL+5.87
서측 유리        : X 3.49~14.41, 높이 거의 천장까지, 출입문은 북쪽 끝 구간
패널             : 1,800 × 900 가로, 구멍 3×2 @600×450, 세로 줄눈은 십자 중심선에서 1,800 간격
벤치             : 단마다 1줄(+뒤쪽 1~2줄), 중앙 통로 양쪽, 좌판 깊이 약 0.37
방위             : +X(입구 쪽) = 방위각 약 335° (북북서). 십자가는 약 155° 방향을 봄
```

## 9. 미확인 / 한계

- **미확인**: 슬릿 폭·벽 두께 등의 안도 사무소 공식 수치(문화청 국립근현대건축자료관에 원도면 1:50 평면·입면·단면이 소장돼 있으나 온라인 이미지 비공개 — https://db.nama.bunka.go.jp/index.php/church-of-the-light-1-50).
- **미확인**: 벤치 정확한 개수·길이(도면마다 10/12/12+11로 다르고, 2005년 오르간 설치 이후 배치가 바뀌었을 수 있음).
- **미확인**: 15° 벽 정확한 두께·높이의 공식값(도면 실측만 있음), 출입문 정확한 폭.
- **미확인**: 일요학교 박스의 공식 외곽 치수(면적만 공식, 크기는 위성·도면 비례 추정).
- **미확인**: 지붕 슬래브 실제 두께와 방수층 구성(단면도에 0.89 m 지붕층만 보임).
- kenchikuzukan 도면은 제3자 CAD 재작도본(원본 아님). 평면은 공표 치수와 맞지만 **종단면은 가로 방향 왜곡**이 있어 높이만 사용함.
- ArchDaily "drawings" 이미지는 원도면이 아니라 학생 렌더링(C. Zeballos 2007)임.
- 일부 도면은 Naver 블로그(박영우 AIA)가 원출처 표기 없이 재게재한 것으로, 안도 사무소 도면으로 보이지만 원출처는 확인하지 못함.
- 참고문헌(미열람, 원도면 수록 가능성 높음): GA Architect / 『Tadao Ando: Details 1』(A.D.A. EDITA, 1991) pp.156‑163, El Croquis 『Tadao Ando 1983‑2000』 pp.106‑114, 『Tadao Ando 0 Process and Idea』(TOTO, 2019) pp.158‑165, Philip Drew 『Church on the Water, Church of the Light』(Phaidon).
