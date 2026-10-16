# AutCon 시공 현장 인식 문헌 계량서지 분석

Automation in Construction에 실린 시공 현장 인식 논문(2015–2026, Scopus)을 VOSviewer로 지도화하기 위한 데이터와 처리 스크립트.
검색식, 분류 기준, 한계, 결과 요약은 [docs/search_log.md](docs/search_log.md)에 위치.

리뷰 논문 분석(2026-10-16 추가)의 목적은 문헌을 분석해 연구 주제를 잡는 방법을 익히는 것이다.
- [docs/methods_manual.md](docs/methods_manual.md): 연구 주제를 찾는 방법 48개(문헌 종합, 계량서지, 텍스트 마이닝, 질적 분석, 의제 도출 틀, 전문가·실무, 기술 예측, 설계·공학, 공백 이론), 도구, 방법을 엮는 순서
- [docs/topic_selection.md](docs/topic_selection.md): 리뷰로 주제를 잡는 7단계를 이 데이터로 실습한 기록과 후보·점수표 양식
- [docs/review_search_log.md](docs/review_search_log.md): 리뷰 파일, 분류 기준, 결과, VOSviewer 설정값

## 폴더 구조

```
.
├── config/                          설정 (직접 수정)
│   ├── topics.tsv                   주제 코드 A–K, Z
│   ├── thesaurus_rules.tsv          키워드 통일 규칙
│   ├── thesaurus_rules_reviews.tsv  리뷰용 통일 규칙 (위 규칙에 덧붙임)
│   ├── thesaurus_ignore_reviews.tsv 리뷰 주제 지도에서 지울 단어
│   ├── review_terms.tsv             관심어·도구 용어 (리뷰 집계용)
│   ├── method_catalog.tsv           연구 주제를 찾는 방법 48개
│   ├── advisor_themes.tsv           지도교수 논문 -> 주제 규칙
│   └── candidates.tsv               본인이 정한 후보 (양식, 비어 있음)
├── data/
│   ├── raw/                         Scopus 내보내기 원본 (수정 금지, git 제외)
│   ├── screening/
│   │   ├── screening_codes.tsv      원저 1차 분류 + 본인 검수 (직접 수정)
│   │   └── review_codes.tsv         리뷰 1차 분류 + 본인 검수 (직접 수정)
│   └── advisor/
│       ├── ProfessorPapers.txt      지도교수 학교 프로필 (받은 그대로)
│       └── advisor_publications.tsv 지도교수 논문 목록 (프로필 + Google Scholar)
├── docs/
│   ├── search_log.md                원저 검색 기록·분류 기준·VOSviewer 설정값
│   ├── review_search_log.md         리뷰 파일·분류 기준·결과·VOSviewer 설정값
│   ├── methods_manual.md            주제를 찾는 방법·도구 매뉴얼
│   └── topic_selection.md           리뷰로 주제를 잡는 과정 (실습 기록, 양식)
├── output/                          스크립트가 만드는 파일 (수정 금지, git 제외)
│   ├── vosviewer/                   ← VOSviewer에 넣을 파일
│   ├── screening_1st_pass.csv       원저 읽기용 분류표
│   ├── review_screening.csv         리뷰 읽기용 분류표
│   ├── reviews/                     공백 문장, 관심어·방법 집계, 방법 카탈로그, 신흥 키워드, 동시 출현 공백
│   ├── advisor_*.csv                지도교수 주제 분포, 문헌 영역 겹침, 후보 적합
│   └── stats.txt, review_stats.txt, advisor_stats.txt
└── scripts/
    ├── build.py                     진입점. 원저 -> 리뷰 -> 지도교수 순서로 모두 실행
    ├── build_reviews.py             리뷰 단계
    ├── build_advisor.py             지도교수 단계
    └── common.py                    공통 경로·함수
```

## 실행

Python 3.8 이상, 표준 라이브러리

```
python scripts/build.py                 세 단계 모두
python scripts/build.py articles        원저만 (reviews, advisor도 같은 방식)
```

원저 원본(`data/raw/*_20261008.csv` 4개)은 git에 없으므로 새로 받은 저장소에는 없다. 그래도 `build.py`는 멈추지 않는다.
- 원본이 없으면 `screening_codes.tsv`만으로 낼 수 있는 통계와 분류표(서지 열은 빈칸)를 만든다.
- 원본에 기대는 처리는 건너뛰고, 다시 받는 방법을 화면에 보여 준다.
- 원본을 [docs/search_log.md](docs/search_log.md#검색-조건)의 검색식으로 다시 내보내 `data/raw/`에 넣으면 전부 다시 만든다.
- `main`과 `wearable`은 원래 복원본이었다. 자세한 내용은 [docs/search_log.md](docs/search_log.md#파일)에 있다.

## 자주 하는 수정

| 하려는 일 | 고칠 파일 | 다음 |
|---|---|---|
| 논문 분류·적합도 수정 | `data/screening/screening_codes.tsv` | `build.py` 실행 |
| 리뷰 범위·공백 수정, 후보 코드 기록 | `data/screening/review_codes.tsv` | `build.py reviews` 실행 |
| 관심어 바꾸기 (추세·동시 출현 공백) | `config/review_terms.tsv` | `build.py reviews` 실행 |
| 방법 추가 (카탈로그) | `config/method_catalog.tsv` | `build.py reviews` 실행 |
| 후보의 지도교수 적합 계산 | `config/candidates.tsv` | `build.py advisor` 실행 |
| 지도교수 새 논문 추가 | `data/advisor/advisor_publications.tsv` | `build.py advisor` 실행 |
| 본인 검수 기록 | `screening_codes.tsv`의 `본인검수` 열 | `build.py` 실행 → 분류표 "검수" 열에 반영 |
| 키워드 통일 규칙 추가 | `config/thesaurus_rules.tsv` (탭 구분) | `build.py` 실행 |
| 주제 코드 이름 변경·추가 | `config/topics.tsv` | `build.py` 실행 |
| Scopus 재검색 | `data/raw/`에 새 파일, 해당 스크립트의 `DATE` 수정 | `screening_codes.tsv`에 새 논문 행 추가 후 실행 |

`output/screening_1st_pass.csv`에 직접 적은 내용은 다시 만들 때 지워진다. 검수는 반드시 `screening_codes.tsv`에 적음.
TSV는 Excel보다 IDE로 고치는 편이 안전하다(Excel은 저장할 때 인코딩과 따옴표를 바꿀 수 있다).

## VOSviewer에 넣기

`Create map → Create a map based on bibliographic data → Read data from bibliographic database files → Scopus`

## [예시]
| 지도 | 입력 파일 (`output/vosviewer/`) | 설정 |
|---|---|---|
| 키워드 동시 출현 | `scopus_sitevision_screened_autcon_20261008.csv` (248편) | Author keywords, thesaurus `thesaurus_keywords.txt`, 최소 3회 → 77개 |
| 키워드 동시 출현 (합집합) | `scopus_all_autcon_20261008.csv` (339편) | 같은 설정 → 103개 |
| 참고문헌 동시 인용 | `scopus_sitevision_screened_autcon_20261008.csv` | 최소 인용 10회 |
| 공저 | `scopus_sitevision_screened_autcon_20261008.csv` | 저자 단위, 최소 3편 |
| 리뷰 지형 (AutCon) | `scopus_review_autcon_screened_20261016.csv` (571편) | Author keywords, thesaurus `thesaurus_reviews_topic.txt`, 최소 5회 → 67개, Overlay는 연도 |
| 현장 인식 리뷰 지형 | `scopus_review_autcon_sitevision_20261016.csv` (183편) | 같은 thesaurus, 최소 3회 → 41개 |
| 현장 인식 리뷰의 지적 기반 | `scopus_review_autcon_sitevision_20261016.csv` | 참고문헌 동시 인용, 최소 5회 |
| 계량서지 방법 지도 | `data/raw/scopus_bibliometric_construction_20261016.csv` | Author keywords, `thesaurus_reviews_method.txt`, 최소 5회 → 84개 |

리뷰 지도 7개의 전체 설정과 각 지도로 무엇을 보는지는 [docs/review_search_log.md](docs/review_search_log.md#vosviewer-설정값-이-데이터-기준)에 있다.

## 데이터 공개

Scopus 원본과 `output/`에는 초록과 참고문헌이 들어 있어 `.gitignore`로 제외했다. 저장소에는 설정, 분류 원자료, 스크립트, 문서만 올라간다.
