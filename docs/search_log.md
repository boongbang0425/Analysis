# 계량서지 검색 기록 (2026-10-08, 2차 갱신)

대상: Automation in Construction에 실린 시공 현장 인식 문헌. 목적은 주제 선정용 지도 작성.
분류 주체: Claude 1차 분류(초록만 읽음). 본인 검수 전.

## 먼저 알아둘 한계

- 분류와 적합도는 초록만 읽고 한 사람(Claude)이 매겼다. "보유 장비로 재현" 열은 초록에서 추정한 값이다.
- 검색식이 놓치는 논문이 있다. 앞서 읽은 10편(`claude/시공자동화_논문10편_요약.md`) 중 주제상 걸릴 만한 4편(01, 02, 05, 09번)에서 09번만 잡혔다. 192권 일부가 색인돼 있어서 색인 지연만으로는 설명되지 않는다. 원인이 검색어인지 색인 누락인지는 확인하지 못했다.
- 저널을 AutCon 하나로 한정했다. 공저 지도는 이 저널에 낸 논문만 반영한다.
- 리뷰 논문은 문서 유형에서 뺐다. 그래도 Article로 분류된 리뷰 2편이 섞여 있어 "제외"로 표시했다.

## 1차 기록에서 바뀐 점

- 1차는 주제어까지 건 42편을 주 집합으로 썼다. 2차는 주제어를 뺀 현장 × 인식 256편이 주 집합이다. 42편은 그 부분집합이다.
- 1차에 "최신 호 누락은 색인 시점 때문일 가능성이 크다"고 적었다. 191–192권 논문 8편이 잡혔으므로 이 추정은 근거가 약하다.
- 적합도 "상" 기준을 아래처럼 명시했다. 이 기준에 따라 Kim D. 외(2019, UAV 근접 감시)를 상에서 중으로 내렸다.
- 1차에 "뎁스 카메라 0건"이라 적은 것은 42편 + 비교군 48편 안에서의 결과다. 뎁스 전용 검색에서는 46편이 나왔다.

## 검색 조건

DB는 Scopus(중앙대 기관 접속), 검색일은 2026-10-08이다. 네 검색 모두 아래 공통 조건을 붙였다.

```
AND PUBYEAR AFT 2014 AND DOCTYPE(ar) AND LANGUAGE(english) AND EXACTSRCTITLE("Automation in Construction")
```

| 집합 | 편수 | 검색식 (공통 조건 앞부분) |
|---|---|---|
| 현장 × 인식 | 256 | [현장] AND [인식] |
| 주제 한정 (1차 본검색) | 42 | [현장] AND [인식] AND [주제] |
| 웨어러블 비교군 | 48 | [현장] AND [웨어러블] AND [주제] |
| 뎁스 | 46 | [뎁스] |

```
[현장]   TITLE-ABS-KEY("construction site" OR "construction worker" OR "construction work" OR jobsite OR "job site" OR worksite OR "construction equipment" OR "construction machinery" OR excavator OR "tower crane" OR "construction safety")
[인식]   TITLE-ABS-KEY("computer vision" OR "vision based" OR "image based" OR "object detection" OR "pose estimation" OR "depth camera" OR "RGB D" OR "stereo vision" OR "point cloud" OR lidar OR cctv OR "surveillance camera" OR "surveillance video")
[주제]   TITLE-ABS-KEY(proximity OR "struck by" OR collision OR intrusion OR "blind spot" OR "hazard zone" OR "danger zone" OR "hazard recognition" OR "hazard identification" OR "unsafe behavior" OR "unsafe behaviour" OR "unsafe act" OR "augmented reality" OR "mixed reality" OR "safety training" OR posture OR ergonomic OR ergonomics OR fatigue OR "heat stress")
[웨어러블] TITLE-ABS-KEY(wearable OR physiological OR "heart rate" OR electrodermal OR eeg OR imu OR "inertial measurement" OR "smart helmet" OR smartwatch OR wristband)
[뎁스]   TITLE-ABS-KEY("depth camera" OR "RGB D" OR kinect OR "stereo camera" OR "stereo vision" OR realsense)
```

합집합은 339편이다. 현장 × 인식과 뎁스의 중복은 8편, 현장 × 인식과 웨어러블의 중복은 3편, 뎁스와 웨어러블의 중복은 0편이다.

내보낸 파일 이름은 내용과 반대였다(`Depth.csv`가 현장 × 인식 256편, `NonTheme.csv`가 뎁스 46편). 저장소에는 내용 기준 이름으로 넣었다.

검색식 변경 이력: 첫 두 판은 Scopus 오류로 실행되지 않았다. `PUBYEAR > 2014`를 `AFT`로, 하이픈이 든 단어를 띄어쓰기로 바꾸자 통과했다. 원인은 이 둘 중 하나이며 분리해서 확인하지 않았다.

## 현장 × 인식 256편의 주제 분포

| 주제 | 편수 | 2015–19 | 2020–22 | 2023–26 |
|---|---|---|---|---|
| A 위험 인식·규정 판단 (PPE, 불안전 행동 포함) | 58 | 7 | 15 | 36 |
| K 기반 기술 (데이터셋, 탐지 모델, 측위) | 43 | 5 | 12 | 26 |
| G 진도·형상 기록 (Scan-vs-BIM, 공정률) | 40 | 12 | 11 | 17 |
| F 장비 활동·자세 | 31 | 10 | 10 | 11 |
| E 작업자 활동·추적 | 19 | 2 | 3 | 14 |
| H 품질·치수 검사 | 16 | 1 | 6 | 9 |
| I 로봇·자동화 시공 | 16 | 3 | 2 | 11 |
| B 근접·충돌 | 11 | 4 | 2 | 5 |
| C 작업자 상태 | 11 | 3 | 2 | 6 |
| J 자재 인식·계측 | 3 | 0 | 1 | 2 |
| D 교육·AR·VR | 2 | 1 | 1 | 0 |
| Z 주제 밖 | 6 | 1 | 2 | 3 |
| 합계 | 256 | 49 | 67 | 140 |

- 센싱: RGB 영상 176편, LiDAR·점군 54편, 뎁스·스테레오 센서 9편, 비전이 아닌 것 17편.
- 인식 결과가 경고·제어·모델 갱신·계획으로 이어지는 논문: 51편. 주제별로 A 15, G 11, I 11, H 6, B 5, D 2, C 1.
- 언어·생성모델 중심: 19편 (2022년 1, 2024년 5, 2025년 6, 2026년 7).
- AR·MR을 다룬 논문: 합집합 339편 중 4편, 현장 × 인식 안에서는 1편.
- 단계: 시공 237편, 공장 제작 포함 8편, 범용 6편, 유지관리 3편, 광산 2편.

## 뎁스 46편

- 단계: 시공 21편, 유지관리 15편, 범용(실내) 6편, 기타 4편(해체, 공장 제작, 폐기물 처리, 단계 불명).
- "제외" 14편(전부 유지관리 단계의 점검 연구)을 뺀 32편의 주제: H 품질·치수 검사 8, I 로봇·자동화 시공 6, G 5, K 5, F 3, 기타 5.
- 연도: 2017–2024년에 연 1–8편, 2025년 7편, 2026년 10편.
- 철근 검사 논문은 합집합에 8편이고, 그중 4편이 스테레오·뎁스 카메라를 쓴다 (Kardovskyi 2021, Woo 2025, Song 2026, Zhao 2026).
- 한계를 적은 논문: Soltani 외(2017)는 저가 뎁스 센서의 측정 거리가 수 m라서 장비 인식에 쓰지 않았다고 적었다. Lam 외(2022, 구조광 센서)는 소비자용 뎁스 카메라가 mm급 작업에는 정확도가 부족하다고 적었다. Nahangi 외(2019)는 Kinect의 배관 반지름 오차를 평균 10–18%로 보고했다.

## 저자

- 이지희 교수: 0편.
- Youngjib Ham(이지희 교수 공저자): 현장 × 인식에 7편, 웨어러블 비교군에 1편. 7편은 모두 영상 기반이다. 그중 Oh 외(2025)는 작업 지시서 문서 파싱과 영상 인식을 결합한다.
- 중앙대 소속 저자: 현장 × 인식에 8편. 7편은 건축 계열 학과, 1편은 기계공학 소속이다.
- 현장 × 인식 다작 저자: Jinwoo Kim, Seokho Chi, Hyoungkwan Kim 각 11편, Jack C.P. Cheng, Hongjo Kim 각 9편.

## 적합도 기준

관심사 정의(인식 → 공간 구조의 반응 → 값 추출)와 보유 장비를 기준으로 삼았다.

- 상: 시공 또는 공장 제작 단계이고, 언어·생성모델 중심이 아니며, 다음 중 하나에 해당한다.
  (a) 인식 결과가 경고, 기계 제어, BIM·디지털 트윈 갱신, 계획 산출로 이어진다.
  (b) 뎁스·스테레오 센서를 수 m 이내에서 쓴다.
  (c) 공간이나 가설 구조물(난간, 비계, 개구부)의 상태를 형상에서 판정한다.
- 중: 시공 단계의 인식 연구이지만 위 조건에 해당하지 않는다.
- 하: 모델·데이터셋 개선이 중심이거나, 비전이 아니거나, 언어·생성모델 중심이다.
- 제외: 시공 단계가 아니거나 인식 연구가 아니다.

합집합 339편에서 상 37, 중 123, 하 113, 제외 22, 웨어러블 비교군 44편이다. 상 37편 중 보유 장비로 재현 가능하다고 추정한 것은 18편, 부분 가능 5편, 추가 장비 필요 14편이다.

## 파일

| 경로 | 내용 |
|---|---|
| `data/raw/scopus_sitevision_autcon_20261008.csv` | 현장 × 인식 원본 (256편) |
| `data/raw/scopus_main_autcon_20261008.csv` | 주제 한정 원본 (42편). 복원본, 아래 참고 |
| `data/raw/scopus_wearable_autcon_20261008.csv` | 웨어러블 비교군 원본 (48편). 복원본, 아래 참고 |
| `data/raw/scopus_depth_autcon_20261008.csv` | 뎁스 원본 (46편) |
| `data/screening/screening_codes.tsv` | 논문별 1차 분류 원자료 (339행). 분류와 본인 검수는 이 파일을 고친다 |
| `config/topics.tsv` | 주제 코드(A–K, Z)와 이름 |
| `config/thesaurus_rules.tsv` | 키워드 통일 규칙. thesaurus를 고칠 때는 이 파일을 고친다 |
| `output/screening_1st_pass.csv` | 읽기용 분류표 (339행). "본인 검수" 열은 `screening_codes.tsv`의 `본인검수` 열에서 온다 |
| `output/vosviewer/scopus_sitevision_screened_autcon_20261008.csv` | VOSviewer 주 입력. 현장 × 인식에서 "제외" 8편을 뺀 248편 |
| `output/vosviewer/scopus_all_autcon_20261008.csv` | 합집합 339편 |
| `output/vosviewer/thesaurus_keywords.txt` | VOSviewer용 키워드 통일 파일 (98쌍) |
| `output/stats.txt` | `build.py`가 출력하는 통계 |
| `scripts/build.py` | `output/`을 다시 만드는 스크립트. 표준 라이브러리만 사용 |

현장 × 인식, 뎁스 원본은 내보낸 파일과 바이트가 같다. 주제 한정·웨어러블 원본 두 개는 정리 과정에서 파일이 없어, 합집합 파일과 분류표의 "검색 집합" 열로 복원했다(2026-10-08). 행 내용은 Scopus 내보내기와 같지만 행 순서는 원래 내보내기와 다를 수 있다. 복원본으로 다시 만든 `output/` 파일 네 개는 원래 처리 파일과 바이트가 같다. 원래 내보낸 파일을 찾으면 같은 이름으로 덮어쓴다.

처리 파일 두 개는 Scopus 내보내기와 같은 형식으로 썼다. 원본 CSV에는 초록과 참고문헌이 들어 있으므로 공개 저장소에는 올리지 않는다. `.gitignore`가 `data/raw/`와 `output/`을 제외한다.

## VOSviewer 설정값 (이 데이터 기준)

| 지도 | 입력 | 설정 |
|---|---|---|
| 키워드 동시 출현 | 선별 후 248편 | Author keywords, thesaurus 적용, 최소 출현 3회 → 77개 (5회면 31개) |
| 키워드 동시 출현 | 합집합 339편 | 같은 설정, 최소 출현 3회 → 103개 |
| 참고문헌 동시 인용 | 선별 후 248편 | 최소 인용 10회 → 58개 이상 (20회면 9개 이상) |
| 공저 | 선별 후 248편 | 저자 단위, 최소 3편 |

참고문헌 개수는 문자열이 완전히 같은 것만 센 하한값이다. VOSviewer가 표기 차이를 묶으면 더 늘어난다. 병합 파일이 VOSviewer에서 열리는지는 확인하지 못했다.
