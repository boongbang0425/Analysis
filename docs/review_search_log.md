# 리뷰 논문 계량서지 기록 (2026-10-16)

대상: 리뷰 논문 7개 집합. 목적은 연구 주제 선정. 현장 인식 원저 분석([search_log.md](search_log.md))과 짝을 이룬다.
분류 주체: Claude 1차 분류(제목 전체 + 핵심·일부 주변 리뷰의 초록). 본인 검수 전.
리뷰로 주제를 잡는 과정은 [topic_selection.md](topic_selection.md)에, 방법 48개의 설명은 [methods_manual.md](methods_manual.md)에 있다.

## 먼저 알아둘 한계

- **검색식은 받지 않았다.** 아래 검색식 열은 내보낸 파일의 내용(문서 유형, 저널, 공통 용어, 집합 간 중복)으로 추정한 것이다. 실제 검색식을 아래 표에 덮어써야 한다.
- 분류는 한 사람(Claude)이 매겼다. 범위 "밖" 399편은 제목만 보고 판단했다.
- AutCon 리뷰 중 8편은 Scopus 문서 유형이 Review지만 내용은 원저다. `review_codes.tsv` 메모에 "원저"로 표시했고, 범위 판단에는 그대로 넣었다.
- R1의 28편 중 11편은 리뷰가 아니다(제목의 review가 설계 검토·계약 검토). VOSviewer 입력에서 뺐다.
- 관심어·도구 집계(`output/reviews/*_terms.csv`)는 제목·초록·키워드를 정규식으로 센 값이다. 본문에서만 도구 이름을 밝힌 논문은 빠지므로 실제 사용률보다 낮다.
- 참고문헌 개수는 문자열이 완전히 같은 것만 센 하한값이다(`build.py`와 같은 방식).
- 원래 분석의 Scopus 원본 4개(`scopus_*_20261008.csv`)는 이 PC의 `data/raw/`에 없다. `build.py`는 원본을 다시 넣기 전까지 실행되지 않는다. `build_reviews.py`는 영향받지 않는다.

## 파일

`reviewpapers/`에 받은 파일을 내용 기준 이름으로 바꿔 `data/raw/`에 옮겼다. 바이트는 그대로다.

| 원래 이름 | 저장 이름 (`data/raw/`) | 편수 | 문서 유형 | 내용 | 추정 검색식 (확인 필요) |
|---|---|---|---|---|---|
| R0.csv | `scopus_review_autcon_20261016.csv` | 540 | Review 540 | AutCon 리뷰 전체 (2002–2027) | `SRCTITLE("Automation in Construction") AND DOCTYPE(re)` |
| R1.csv | `scopus_reviewtitle_autcon_20261016.csv` | 28 | Article 28 | AutCon Article 중 제목에 review가 든 것 | `... AND DOCTYPE(ar) AND TITLE(review)` |
| R2.csv | `scopus_biblioreview_autcon_20261016.csv` | 90 | Review 89, Article 1 | AutCon 계량서지·과학계량 리뷰 | `... AND TITLE-ABS-KEY(bibliometric OR scientometric OR ...)` |
| R3.csv | `scopus_sysreview_autcon_20261016.csv` | 211 | Review 193, Article 17, Short survey 1 | AutCon 체계적·비판적 리뷰 | `... AND TITLE-ABS-KEY("systematic review" OR "literature review" OR ...)` |
| S1.csv | `scopus_review_construction_20261016.csv` | 2,366 | Review 1,687, Article 679 | 건설 분야 리뷰, 여러 저널 (Buildings 204, Sustainability 104, AutCon 99 ...) | 건설어 AND (리뷰 OR 연구 공백·동향) |
| S2.csv | `scopus_bibliometric_construction_20261016.csv` | 545 | Review 338, Article 207 | 건설 분야 계량서지 연구 (초록·키워드의 92%에 계량서지 용어) | 건설어 AND (VOSviewer OR CiteSpace OR bibliometric ...) |
| S3.csv | `scopus_reviewframework_alldomain_20261016.csv` | 3,243 | Review 1,408, Article 1,835 | 분야 무관, 리뷰로 프레임워크·연구 의제를 만드는 논문 (제목의 84%가 리뷰어 + 프레임워크어) | `TITLE((review OR literature) AND (framework OR agenda ...))` |

중복: R0∩R3 193, R0∩R2 89, R2∩R3 49, R1∩R3 5, S1∩S2 288, S1∩R0 93, S1∩S3 27. R0과 R1은 겹치지 않는다(문서 유형이 다름).
AutCon 합집합(R0∪R1∪R2∪R3)은 582편, 리뷰가 아닌 11편을 빼면 571편이다.

| 경로 | 내용 |
|---|---|
| `data/screening/review_codes.tsv` | AutCon 리뷰 582편의 1차 분류 원자료. 범위, 주제코드, 단계, 공백, 관련 후보(본인 입력용, 비어 있음), 본인 검수 |
| `config/thesaurus_rules_reviews.tsv` | 리뷰용 키워드 통일 규칙 (기본 규칙 위에 덧붙임) |
| `config/thesaurus_ignore_reviews.tsv` | 주제 지도에서 지울 단어 (리뷰 방법, 분야 이름, 일반어) |
| `config/review_terms.tsv` | 관심어와 도구·자료원·분석·절차 용어의 정규식 |
| `config/method_catalog.tsv` | 연구 주제를 찾는 방법 48개의 정규식 |
| `scripts/build_reviews.py` | 아래 출력을 다시 만드는 스크립트. `python scripts/build.py reviews`로도 돈다. 공통 함수는 `scripts/common.py` |
| `output/review_screening.csv` | 읽기용 분류표 (582행) |
| `output/reviews/gap_sentences.csv` | 핵심·주변 리뷰 초록에서 공백 표현이 든 문장 (347문장, 155편) |
| `output/reviews/watch_terms.csv` | 관심어의 시기별 언급 비율 |
| `output/reviews/method_terms.csv` | 도구·자료원·분석·절차의 시기별 사용 |
| `output/reviews/top_references.csv` | 코퍼스별 많이 인용된 참고문헌 상위 40 |
| `output/reviews/method_catalog.csv` | 방법별 사용 편수·추세·대표 논문·특징 인용 문헌 |
| `output/reviews/emerging_keywords.csv` | 2024년 이후 비중이 늘어난 키워드 |
| `output/reviews/whitespace_pairs.csv` | 관심어 쌍의 실제 / 기대 동시 출현 |
| `output/vosviewer/scopus_review_autcon_*_20261016.csv` | VOSviewer 입력 (screened 571, sitevision 183, core 62) |
| `output/vosviewer/thesaurus_reviews_topic.txt` | 주제 지도용 thesaurus (617쌍, 그중 100개는 지움) |
| `output/vosviewer/thesaurus_reviews_method.txt` | 방법 지도용 thesaurus (562쌍, 통일만) |
| `output/review_stats.txt` | `build_reviews.py`가 출력하는 통계 |

## 범위 기준

기존 적합도 기준(시공 단계 + 인식)을 리뷰에 맞게 바꿨다.

- 핵심: 시공·공장 제작 단계의 현장 인식·센싱을 직접 다룬다. 기존 건물의 Scan-to-BIM 리뷰도 시공 중 형상 기록과 같은 기술 문제라서 넣었다.
- 주변: 시공 단계지만 인식이 중심이 아니다(로봇, AR·VR, 웨어러블, 디지털 트윈, 장비 자동화, AI 일반). 또는 유지관리 단계의 영상·점군 인식이다(기법을 가져다 쓸 수 있음).
- 밖: 그 외. 설계, 재료, 3D 프린팅, 블록체인, 에너지, 텍스트·LLM 중심 등.

핵심 62편은 초록을 읽고 "공백(초록 기준)"을 적었다. "관련 후보" 열은 본인이 정한 후보 코드를 적는 칸이라 비워 두었다. 주변은 사용자 관심사와 맞닿은 10편만 초록을 읽었다.

## 결과

### AutCon 리뷰 571편

| 주제 | 핵심 | 주변 | 원저(현장 × 인식 256편, search_log 기준) |
|---|---|---|---|
| A 위험 인식·규정 판단 | 6 | 7 | 58 |
| B 근접·충돌 | 5 | 3 | 11 |
| C 작업자 상태 | 1 | 9 | 11 |
| D 교육·AR·VR | 0 | 8 | 2 |
| E 작업자 활동·추적 | 3 | 4 | 19 |
| F 장비 활동·자세 | 4 | 6 | 31 |
| G 진도·형상 기록 | 15 | 12 | 40 |
| H 품질·치수 검사 | 6 | 38 (유지관리 다수) | 16 |
| I 로봇·자동화 시공 | 3 | 20 | 16 |
| K 기반 기술 | 19 | 14 | 43 |

- 시기: 2019년까지 111편, 2020–22년 160편, 2023–27년 300편. 리뷰도 원저처럼 최근에 몰린다.
- 리뷰 유형(초록 기준 자동): 서술·기타 302, 체계적 179, 계량서지 90. 체계적 리뷰가 2019년까지 19편에서 2023–27년 121편으로 늘었다.
- 근접·충돌(B)은 원저 11편에 핵심 리뷰 5편이다. 원저에 비해 리뷰가 많다. 문제 정의는 정리됐지만 AutCon 안의 원저는 적다는 뜻이다. Ding 외(2026, Automated proximity monitoring and warning)는 3D 객체·자세 탐지, 실시간 3D 복원, 멀티모달 융합을 다음 과제로 꼽았다.
- 진도·형상(G)은 원저 40편, 리뷰 27편으로 양쪽 다 두껍다.
- 관심어 비율(AutCon 리뷰 571편): 뎁스·스테레오 0.5%, 근접·충돌 1.8%, 가설 구조물·개구부 2.5%, AR·MR 3.5%, 디지털 트윈 11.2%(2019년까지 0% → 2023–27년 17%), 데이터셋·벤치마크 8.6%, 언어·생성모델 3.2%(2023년 이후에만).
- 핵심 피인용 상위: Tang 외 2010 as-built BIM(1,068회), Baduge 외 2022 AI·스마트 비전(981회), Rao 외 2022 실시간 현장 모니터링(390회), Paneru 외 2021 건설 CV(324회), Fang 외 2020 CV 안전(283회). 전체 목록은 `output/review_stats.txt`.

### 방법·도구 (S2 545편, S3 3,243편)

| 항목 | S2 건설 계량서지 (2023–27년) | S3 분야 무관 (2023–27년) |
|---|---|---|
| VOSviewer | 57.8% (60%) | 2.9% (4%) |
| CiteSpace | 22.9% (21%, 2020–22년 30%에서 감소) | 0.6% |
| Bibliometrix·Biblioshiny | 14.1% (17%, 2020–22년 5%에서 증가) | 1.4% |
| Scopus / Web of Science | 39.4% / 37.8% | 15.3% / 12.5% |
| 키워드 동시 출현 / 동시 인용 | 27.5% / 16.3% | 2.6% / 1.2% |
| 주제 지도(전략 도표) | 8.3% (10%) | 0.6% |
| PRISMA | 13.9% (16%) | 17.1% (25%) |
| 연구 의제 제시 | 1.8% | 14.8% |
| TCCM / ADO / SPAR-4-SLR | 0 / 0 / 1편 | 58 / 39 / 28편 |
| LLM 보조 리뷰 | 0.7% | 1.9% (2023–27년 3%) |

가장 많이 인용된 방법 문헌:
- S2: van Eck & Waltman 2010(VOSviewer), Aria & Cuccurullo 2017(Bibliometrix), Page 외 2021(PRISMA 2020), Donthu 외 2021(How to conduct a bibliometric analysis), Chen 2006(CiteSpace II), Mongeon & Paul-Hus 2016(WoS·Scopus 수록 범위 비교).
- S3: Tranfield 외 2003(체계적 리뷰 방법론) 161편, PRISMA 2020 109편, Snyder 2019(방법으로서의 문헌 리뷰) 88편, Denyer & Tranfield 2009, Donthu 외 2021, Paul & Criado 2020, Kitchenham & Charters 2007, Zupic & Čater 2015.

연구 공백 찾기 자체를 다룬 문헌의 인용(참고문헌 문자열 검색): Webster & Watson 2002는 S3 105편, S1 22편, AutCon 리뷰 3편. Sandberg & Alvesson 2011(gap-spotting)은 S3 3편, S1 9편, AutCon 리뷰 3편. Müller-Bloch & Kranz 2015(공백 유형)는 S3 10편, S1 3편, AutCon 리뷰 2편. 건설 분야 리뷰는 공백을 찾는 방법을 따로 밝히지 않고, 대부분 "덜 연구된 영역" 하나만 짚는다.

## VOSviewer 설정값 (이 데이터 기준)

`Create map → Create a map based on bibliographic data → Read data from bibliographic database files → Scopus`. 아래 개수는 `build_reviews.py`가 같은 방식으로 센 값이다. VOSviewer는 Author keywords를 다르게 자를 수 있어 몇 개 차이가 날 수 있다.

| # | 지도 | 입력 | 분석 | 설정 | 예상 항목 수 | 무엇을 보는가 |
|---|---|---|---|---|---|---|
| 1 | AutCon 리뷰 지형 | `output/vosviewer/scopus_review_autcon_screened_20261016.csv` | Co-occurrence, Author keywords | thesaurus `thesaurus_reviews_topic.txt`, 최소 5회 | 67 (3회면 150) | 분야 전체의 주제 덩어리. Overlay를 "Avg. pub. year"로 바꿔 최근 주제 확인 |
| 2 | 현장 인식 리뷰 지형 | `..._sitevision_20261016.csv` (183편) | Co-occurrence, Author keywords | 같은 thesaurus, 최소 3회 | 41 (2회면 102) | 관심 영역 안의 주제와 연결. 연결이 약한 쌍은 공백일 수 있다(검증은 별도) |
| 3 | 현장 인식 리뷰의 지적 기반 | `..._sitevision_20261016.csv` | Co-citation, Cited references | 최소 5회 | 89 이상 | 반드시 읽어야 할 원저 (Fang 2018 안전모, Bosché 2015 Scan-vs-BIM 등) |
| 4 | 리뷰끼리의 묶음 | `..._sitevision_20261016.csv` | Bibliographic coupling, Documents | 최소 피인용 0 | 183 이하 | 같은 문헌을 공유하는 리뷰 무리. 무리마다 대표 리뷰 1편씩 정독 |
| 5 | 건설 리뷰 전체 지형 | `data/raw/scopus_review_construction_20261016.csv` | Co-occurrence, Author keywords | `thesaurus_reviews_topic.txt`, 최소 10회 | 114 | AutCon 밖까지 넓힌 맥락 |
| 6 | 계량서지 방법 지도 | `data/raw/scopus_bibliometric_construction_20261016.csv` | Co-occurrence, Author keywords | `thesaurus_reviews_method.txt`, 최소 5회 | 84 | 건설 분야가 어떤 도구·분석을 쓰는가 |
| 7 | 방법론 필독서 | `data/raw/scopus_reviewframework_alldomain_20261016.csv` | Co-citation, Cited references | 최소 20회 | 55 이상 | 리뷰·연구 의제 방법론의 고전 |

S1–S3는 가공하지 않으므로 `data/raw/` 파일을 그대로 넣는다. thesaurus 파일에서 `replace by`가 빈 줄은 그 단어를 지도에서 지운다([UIC 가이드](https://researchguides.uic.edu/bibliometrics/vosviewer) 설명 기준, 공식 매뉴얼 문장은 확인하지 못했다). 지도에 review, construction 같은 단어가 남아 있으면 thesaurus가 적용되지 않은 것이다.
