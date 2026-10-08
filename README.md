# AutCon 시공 현장 인식 문헌 계량서지 분석

Automation in Construction에 실린 시공 현장 인식 논문(2015–2026, Scopus)을 VOSviewer로 지도화하기 위한 데이터와 처리 스크립트.
검색식, 분류 기준, 한계, 결과 요약은 [docs/search_log.md](docs/search_log.md)에 위치.

## 폴더 구조

```
.
├── config/                     설정 (직접 수정)
│   ├── topics.tsv              주제 코드 A–K, Z
│   └── thesaurus_rules.tsv     키워드 통일 규칙
├── data/
│   ├── raw/                    Scopus 내보내기 원본 (수정 금지, git 제외)
│   └── screening/
│       └── screening_codes.tsv 논문별 1차 분류 + 본인 검수 (직접 수정)
├── docs/
│   └── search_log.md           검색 기록·분류 기준·VOSviewer 설정값
├── output/                     build.py가 만드는 파일 (수정 금지, git 제외)
│   ├── vosviewer/              ← VOSviewer에 넣을 파일
│   ├── screening_1st_pass.csv  읽기용 분류표
│   └── stats.txt               통계
└── scripts/
    └── build.py
```

## 실행

Python 3.8 이상, 표준 라이브러리

```
python scripts/build.py
```

`data/raw/`에 아래 Scopus에서 추출한 csv 저장
`main`과 `wearable`은 복원본. 
자세한 내용은 [docs/search_log.md](docs/search_log.md#파일)에 위치

## 자주 하는 수정

| 하려는 일 | 고칠 파일 | 다음 |
|---|---|---|
| 논문 분류·적합도 수정 | `data/screening/screening_codes.tsv` | `build.py` 실행 |
| 본인 검수 기록 | `screening_codes.tsv`의 `본인검수` 열 | `build.py` 실행 → 분류표 "검수" 열에 반영 |
| 키워드 통일 규칙 추가 | `config/thesaurus_rules.tsv` (탭 구분) | `build.py` 실행 |
| 주제 코드 이름 변경·추가 | `config/topics.tsv` | `build.py` 실행 |
| Scopus 재검색 | `data/raw/`에 새 파일, `build.py`의 `DATE` 수정 | `screening_codes.tsv`에 새 논문 행 추가 후 실행 |

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

## 데이터 공개

Scopus 원본과 `output/`에는 초록과 참고문헌이 들어 있어 `.gitignore`로 제외했다. 저장소에는 설정, 분류 원자료, 스크립트, 문서만 올라간다.
