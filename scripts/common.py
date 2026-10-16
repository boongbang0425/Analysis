"""build.py, build_reviews.py, build_advisor.py가 함께 쓰는 경로와 함수. 표준 라이브러리만 사용."""
import collections
import csv
import re
from pathlib import Path

csv.field_size_limit(10**9)

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SCREEN = ROOT / "data" / "screening"
CONFIG = ROOT / "config"
OUT = ROOT / "output"
VOS = OUT / "vosviewer"


def read_tsv(fn):
    """'#' 주석 줄과 빈 줄을 건너뛰고 탭 구분 표를 읽는다."""
    with open(fn, encoding="utf-8", newline="") as f:
        lines = [ln for ln in f if ln.strip() and not ln.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


def load_topics():
    return {r["코드"]: f"{r['코드']} {r['이름']}" for r in read_tsv(CONFIG / "topics.tsv")}


class Tee:
    """화면과 파일에 함께 쓴다."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)

    def flush(self):
        for st in self.streams:
            st.flush()


def load(fn):
    with open(fn, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return rd.fieldnames, list(rd)


def write_scopus(fn, fields, rows):
    """Scopus CSV 내보내기와 같은 형식(BOM, 모든 칸 따옴표, LF)으로 쓴다."""
    with open(fn, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_csv(fn, header, rows):
    """읽기용 CSV (BOM, Excel에서 한글이 깨지지 않게)."""
    with open(fn, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def kwset(r, th):
    return {th.get(k.strip().lower(), k.strip().lower()) for k in r["Author Keywords"].split(";") if k.strip()}


def kwcount(rows, th=None):
    c = collections.Counter()
    for r in rows:
        c.update(kwset(r, th or {}))
    return c


def refs(r):
    return {x.strip().lower() for x in re.split(r"(?<=\(\d{4}\));\s*", r["References"]) if x.strip()}


def tak(r):
    """제목·초록·키워드를 소문자로 이어 붙인다 (용어 검색용)."""
    return " ".join(r[c] for c in ("Title", "Abstract", "Author Keywords", "Index Keywords")).lower()
