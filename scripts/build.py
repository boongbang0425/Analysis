"""Scopus 내보내기 4개를 병합하고 1차 분류표, VOSviewer 입력 파일, thesaurus, 통계를 만든다.
표준 라이브러리만 사용 (pandas 불필요).

입력
    data/raw/scopus_sitevision_autcon_20261008.csv  현장 x 인식 (주 집합)
    data/raw/scopus_main_autcon_20261008.csv        현장 x 인식 x 주제 (1차 본검색, 주 집합의 부분집합)
    data/raw/scopus_wearable_autcon_20261008.csv    웨어러블 비교군
    data/raw/scopus_depth_autcon_20261008.csv       뎁스·스테레오
    data/screening/screening_codes.tsv              논문별 1차 분류 (Claude, 초록만 읽음) + 본인 검수
    config/topics.tsv                               주제 코드 -> 이름
    config/thesaurus_rules.tsv                      키워드 통일 규칙

출력 (모두 다시 만들어지므로 직접 고치지 않는다)
    output/vosviewer/scopus_sitevision_screened_autcon_20261008.csv  VOSviewer 주 입력
    output/vosviewer/scopus_all_autcon_20261008.csv                  합집합
    output/vosviewer/thesaurus_keywords.txt                          VOSviewer thesaurus
    output/screening_1st_pass.csv                                     읽기용 분류표
    output/stats.txt                                                  통계 (화면 출력과 같음)

사용법 (저장소 최상위에서)
    python scripts/build.py
"""
import csv
import collections
import re
import sys
from pathlib import Path

csv.field_size_limit(10**9)
DATE = "20261008"

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SCREENING = ROOT / "data" / "screening" / "screening_codes.tsv"
CONFIG = ROOT / "config"
OUT = ROOT / "output"
VOS = OUT / "vosviewer"


def read_tsv(fn):
    """'#' 주석 줄과 빈 줄을 건너뛰고 탭 구분 표를 읽는다."""
    with open(fn, encoding="utf-8", newline="") as f:
        lines = [ln for ln in f if ln.strip() and not ln.startswith("#")]
    return list(csv.DictReader(lines, delimiter="	"))


def load_topics():
    return {r["코드"]: f"{r['코드']} {r['이름']}" for r in read_tsv(CONFIG / "topics.tsv")}


def load_thesaurus_rules():
    rules = {}
    for r in read_tsv(CONFIG / "thesaurus_rules.tsv"):
        lab, tgt = r["label"].strip().lower(), r["replace by"].strip().lower()
        assert lab not in rules or rules[lab] == tgt, f"thesaurus_rules.tsv: '{lab}' 규칙이 둘 이상"
        rules[lab] = tgt
    return rules


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


def kwset(r, th):
    return {th.get(k.strip().lower(), k.strip().lower()) for k in r["Author Keywords"].split(";") if k.strip()}


def kwcount(rows, th=None):
    c = collections.Counter()
    for r in rows:
        c.update(kwset(r, th or {}))
    return c


def refs(r):
    return {x.strip().lower() for x in re.split(r"(?<=\(\d{4}\));\s*", r["References"]) if x.strip()}


def sensing_class(s):
    t = s.replace("단안 깊이 추정", "").replace("깊이 추정", "").replace("깊이는", "")
    if any(k in t for k in ("뎁스", "RGB-D", "스테레오", "Kinect", "깊이 맵", "3D 카메라")):
        return "뎁스·스테레오"
    if any(k in t for k in ("LiDAR", "레이저", "점군", "구조광")):
        return "LiDAR·점군"
    if any(k in t for k in ("RGB", "영상", "이미지", "카메라", "CCTV", "사진", "웹캠", "열화상")):
        return "RGB 영상"
    return "기타"


def main():
    VOS.mkdir(parents=True, exist_ok=True)
    TOPIC = load_topics()
    fields, S = load(RAW / f"scopus_sitevision_autcon_{DATE}.csv")
    _, M = load(RAW / f"scopus_main_autcon_{DATE}.csv")
    _, W = load(RAW / f"scopus_wearable_autcon_{DATE}.csv")
    _, D = load(RAW / f"scopus_depth_autcon_{DATE}.csv")
    se, me, we, de = ({r["EID"] for r in x} for x in (S, M, W, D))
    assert me <= se

    allr = {}
    for rows in (S, W, D):
        for r in rows:
            allr.setdefault(r["EID"], r)
    union = list(allr.values())

    with open(SCREENING, encoding="utf-8", newline="") as f:
        codes = {r["EID"]: r for r in csv.DictReader(f, delimiter="\t")}
    assert set(codes) == set(allr), (len(codes), len(allr))
    bad = {c["주제코드"] for c in codes.values()} - set(TOPIC)
    assert not bad, f"config/topics.tsv에 없는 주제코드: {bad}"

    # ---------------------------------------------------------------- thesaurus
    present = collections.Counter()
    for r in union:
        for col in ("Author Keywords", "Index Keywords"):
            present.update({k.strip().lower() for k in r[col].split(";") if k.strip()})
    th = {lab: tgt for lab, tgt in load_thesaurus_rules().items() if lab in present}
    assert not (set(th) & set(th.values())), set(th) & set(th.values())
    with open(VOS / "thesaurus_keywords.txt", "w", encoding="utf-8", newline="") as f:
        f.write("label\treplace by\n")
        for a in sorted(th):
            f.write(f"{a}\t{th[a]}\n")

    # ---------------------------------------------------------------- VOSviewer 입력
    write_scopus(VOS / f"scopus_all_autcon_{DATE}.csv", fields, union)
    screened = [r for r in S if codes[r["EID"]]["적합도"] != "제외"]
    write_scopus(VOS / f"scopus_sitevision_screened_autcon_{DATE}.csv", fields, screened)

    # ---------------------------------------------------------------- 분류표
    def sets(e):
        tags = []
        if e in se:
            tags.append("현장×인식")
        if e in me:
            tags.append("주제 한정")
        if e in we:
            tags.append("웨어러블")
        if e in de:
            tags.append("뎁스")
        return " + ".join(tags)

    cols = ["검색 집합", "연도", "저자", "제목", "피인용", "단계", "센싱", "주제", "세부 주제", "인식 뒤 반응",
            "검증(초록 기준)", "언어·생성모델 중심", "관심 적합도", "보유 장비로 재현(추정)", "메모", "본인 검수", "DOI", "EID"]
    order = {"상": 0, "중": 1, "하": 2, "제외": 3, "비교군": 4}
    table = []
    for r in union:
        c = codes[r["EID"]]
        memo = [c["메모"]] if c["메모"] else []
        if "Ham, Y" in r["Author full names"]:
            memo.append("Youngjib Ham(이지희 교수 공저자) 참여")
        if "chung-ang" in r["Affiliations"].lower():
            memo.append("중앙대 소속 저자 포함")
        table.append([sets(r["EID"]), r["Year"], r["Authors"], r["Title"], r["Cited by"], c["단계"], c["센싱"],
                      TOPIC[c["주제코드"]], c["주제"], c["반응"], c["검증"], c["언어생성모델"], c["적합도"],
                      c["재현추정"], ". ".join(memo), c.get("본인검수") or "", r["DOI"], r["EID"]])
    table.sort(key=lambda t: (order[t[12]], -int(t[1]), t[3]))
    with open(OUT / "screening_1st_pass.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(table)

    # ---------------------------------------------------------------- 통계
    C = lambda rows, key: collections.Counter(key(codes[r["EID"]]) for r in rows)
    print(f"현장×인식 {len(S)} | 주제 한정 {len(M)} | 웨어러블 {len(W)} | 뎁스 {len(D)} | 합집합 {len(union)}")
    print(f"중복: 현장×인식∩뎁스 {len(se & de)}, 현장×인식∩웨어러블 {len(se & we)}, 뎁스∩웨어러블 {len(de & we)}")
    print(f"선별 후 현장×인식 {len(screened)}편 (제외 {len(S) - len(screened)})")

    print("\n[현장×인식 256편]")
    print(" 연도:", sorted(collections.Counter(r["Year"] for r in S).items()))
    tc = C(S, lambda c: c["주제코드"])
    for k in TOPIC:
        if tc[k]:
            per = collections.Counter()
            for r in S:
                if codes[r["EID"]]["주제코드"] == k:
                    y = int(r["Year"])
                    per["2015-19" if y <= 2019 else "2020-22" if y <= 2022 else "2023-26"] += 1
            print(f"  {TOPIC[k]:28s} {tc[k]:3d}  (2015-19 {per['2015-19']}, 2020-22 {per['2020-22']}, 2023-26 {per['2023-26']})")
    print(" 적합도:", dict(C(S, lambda c: c["적합도"])))
    print(" 언어·생성모델 중심:", C(S, lambda c: c["언어생성모델"])["Y"],
          "| 연도별:", sorted(collections.Counter(r["Year"] for r in S if codes[r["EID"]]["언어생성모델"] == "Y").items()))
    print(" 인식 뒤 반응 있음:", sum(codes[r["EID"]]["반응"] != "없음" for r in S))
    print(" 센싱:", dict(C(S, lambda c: sensing_class(c["센싱"]))))
    print(" 단계:", dict(C(S, lambda c: c["단계"])))

    print("\n[뎁스 46편]")
    print(" 단계:", dict(C(D, lambda c: c["단계"])))
    dc = [r for r in D if codes[r["EID"]]["적합도"] != "제외"]
    print(" 제외가 아닌 것:", len(dc), "| 주제:", dict(collections.Counter(TOPIC[codes[r["EID"]]["주제코드"]] for r in dc)))
    print(" 연도:", sorted(collections.Counter(r["Year"] for r in D).items()))

    print("\n[뎁스·스테레오 센서를 실제로 쓴 논문 (합집합, 제외 아닌 것)]")
    for r in sorted(union, key=lambda r: r["Year"]):
        c = codes[r["EID"]]
        if sensing_class(c["센싱"]) == "뎁스·스테레오" and c["적합도"] != "제외":
            print(f"  {r['Year']} {r['Authors'].split(';')[0]:18s} {TOPIC[c['주제코드']][:1]} {c['적합도']} | {c['센싱']} | {c['주제']}")

    print("\n[적합도 상]", sum(codes[e]["적합도"] == "상" for e in codes))
    print(" 재현:", dict(collections.Counter(codes[e]["재현추정"].split("(")[0] for e in codes if codes[e]["적합도"] == "상")))
    print(" 주제:", dict(collections.Counter(codes[e]["주제코드"] for e in codes if codes[e]["적합도"] == "상")))

    print("\n[저자]")
    au = collections.Counter()
    for r in S:
        for a in r["Author full names"].split(";"):
            a = re.sub(r"\s*\(\d+\)", "", a).strip()
            if a:
                au[a] += 1
    print(" 현장×인식 상위:", au.most_common(12))
    for name, key in (("Ham", lambda r: "Ham, Y" in r["Author full names"]),
                      ("이지희", lambda r: "jeehee" in r["Author full names"].lower()),
                      ("중앙대", lambda r: "chung-ang" in r["Affiliations"].lower())):
        hits = [(r["Year"], r["Authors"].split(";")[0], r["Title"][:70], sets(r["EID"])) for r in union if key(r)]
        print(f" {name}: {len(hits)}")
        for h in hits:
            print("    ", h)

    print("\n[VOSviewer 기준값]")
    for name, rows in (("현장×인식 256", S), ("선별 후", screened), ("합집합 339", union)):
        t = kwcount(rows, th)
        rc = collections.Counter()
        for r in rows:
            rc.update(refs(r))
        print(f" {name}: 저자 키워드 {len(kwcount(rows))} -> {len(t)}, 2회+ {sum(v >= 2 for v in t.values())}, "
              f"3회+ {sum(v >= 3 for v in t.values())}, 5회+ {sum(v >= 5 for v in t.values())} | "
              f"참고문헌 5편+ {sum(v >= 5 for v in rc.values())}, 10편+ {sum(v >= 10 for v in rc.values())}, 20편+ {sum(v >= 20 for v in rc.values())}")
    print(" thesaurus 쌍:", len(th))
    print(" 상위 키워드(현장×인식):", kwcount(S, th).most_common(25))

    known = {"107262", "107264", "107271", "107196", "107222", "107171", "107188", "107230", "107154", "107288"}
    print("\n[요약본 10편 포함 여부]", [(r["Art. No."], sets(r["EID"])) for r in union if r["Art. No."] in known])
    print(" 191권 이상:", sum(1 for r in union if r["Volume"].isdigit() and int(r["Volume"]) >= 191))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "stats.txt", "w", encoding="utf-8", newline="\n") as log:
        console, sys.stdout = sys.stdout, Tee(sys.stdout, log)
        try:
            main()
        finally:
            sys.stdout = console
