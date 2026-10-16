"""지도교수 연구의 주제 분포, 문헌 영역(주제 코드)과의 겹침, 그리고 본인이 적은 후보의 적합성을 계산한다.
표준 라이브러리만 사용. 보통 build.py가 부른다(python scripts/build.py advisor). 혼자 실행해도 된다.

입력
    data/advisor/advisor_publications.tsv   지도교수 논문 목록 (학교 프로필 + Google Scholar)
    config/advisor_themes.tsv               논문 제목 -> 주제 규칙
    data/screening/review_codes.tsv         AutCon 리뷰의 범위·주제 코드
    data/raw/scopus_*.csv                   있는 것 전부 (리뷰 제목·키워드, 중앙대 소속 논문)
    config/candidates.tsv                   본인이 적은 후보 (비어 있으면 후보 계산은 건너뛴다)

출력
    output/advisor_profile.csv              지도교수 주제별 논문 수와 시기
    output/advisor_overlap.csv              주제 코드(A–K, Z)별로 지도교수 주제가 걸리는 리뷰 수
    output/advisor_fit.csv                  후보별 적합 지표 (후보가 있을 때만)
    output/advisor_stats.txt                통계 (화면 출력과 같음)

겹침: 리뷰 제목 + 저자 키워드에 지도교수 주제 정규식이 걸리면 그 주제와 겹친다고 센다(초록은 일반어가 많아 쓰지 않는다).
후보 적합 지수 = 2 x (최근 3년 연결 주제 논문 수) + (그 이전 연결 주제 논문 수)
               + 3 x (지도교수 논문 제목에 후보 내용어가 직접 걸린 수) + (중앙대 소속 논문 중 후보 내용어가 걸린 수)
보수적 지수 = 3 x (제목 직접 일치) + (중앙대 논문 일치). '연결 주제'라는 판단 없이 순위가 유지되는지 본다.
"""
import collections
import glob
import re
import sys

from common import CONFIG, OUT, RAW, ROOT, SCREEN, Tee, load, load_topics, read_tsv, tak, write_csv

PUBS = ROOT / "data" / "advisor" / "advisor_publications.tsv"
RECENT_FROM = 2024


def build():
    pubs = read_tsv(PUBS)
    themes = [(r["주제"], re.compile(r["정규식"])) for r in read_tsv(CONFIG / "advisor_themes.tsv")]
    TOPIC = load_topics()

    # ---------------------------------------------------------------- 지도교수 주제 분포
    tag = {p["제목"]: [name for name, rx in themes if rx.search(p["제목"].lower())] for p in pubs}
    print(f"[지도교수 논문] {sum(p['유형'] == '논문' for p in pubs)}편 + 프로필 문장 {sum(p['유형'] == '프로필' for p in pubs)}"
          f" | 연도 {min(p['연도'] for p in pubs)}–{max(p['연도'] for p in pubs)}")
    prof = []
    print(" 주제별 (전체 / 2024년 이후 / 최근 논문):")
    for name, _ in themes:
        allp = [p for p in pubs if name in tag[p["제목"]]]
        rec = [p for p in allp if int(p["연도"]) >= RECENT_FROM]
        latest = max((p["연도"] for p in allp), default="-")
        prof.append([name, len(allp), len(rec), latest, " / ".join(f"{p['연도']} {p['제목'][:60]}" for p in allp)])
        print(f"   {name:16s} {len(allp):2d} / {len(rec):2d} / {latest}")
    untagged = [p["제목"][:70] for p in pubs if not tag[p["제목"]]]
    if untagged:
        print(" 주제 없음:", untagged)
    write_csv(OUT / "advisor_profile.csv", ["주제", "논문 수", "2024년 이후", "가장 최근", "논문"], prof)
    print(" 2024년 이후 논문:")
    for p in sorted(pubs, key=lambda p: p["연도"], reverse=True):
        if int(p["연도"]) >= RECENT_FROM and p["유형"] == "논문":
            print(f"   {p['연도']} {p['제목'][:90]} | {', '.join(tag[p['제목']])}")

    # ---------------------------------------------------------------- 원본 (리뷰, 중앙대)
    rows_by_eid, cau = {}, []
    for fn in sorted(glob.glob(str(RAW / "scopus_*.csv"))):
        _, rows = load(fn)
        for r in rows:
            if r["EID"] not in rows_by_eid:
                rows_by_eid[r["EID"]] = r
                if "chung-ang" in r["Affiliations"].lower():
                    cau.append(r)

    # ---------------------------------------------------------------- 문헌 영역과의 겹침
    codes = {r["EID"]: r for r in read_tsv(SCREEN / "review_codes.tsv")}
    reviews = [(codes[e], rows_by_eid[e]) for e in codes if e in rows_by_eid]
    print(f"\n[지도교수 주제와 AutCon 리뷰 영역의 겹침] 리뷰 {len(reviews)}편 (제목 + 저자 키워드 기준)")
    names = [n for n, _ in themes]
    print("   " + "주제 코드".ljust(26) + " 편수 | " + " | ".join(n[:6] for n in names))
    ov_rows = []
    for k in TOPIC:
        for sc in ("핵심+주변", "밖"):
            grp = [r for c, r in reviews if c["주제코드"] == k and ((c["범위"] != "밖") == (sc == "핵심+주변"))]
            if not grp:
                continue
            cnt = [sum(bool(rx.search((r["Title"] + " " + r["Author Keywords"]).lower())) for r in grp) for _, rx in themes]
            ov_rows.append([TOPIC[k], sc, len(grp)] + cnt)
            print(f"   {(TOPIC[k] + ' ' + sc)[:26]:26s} {len(grp):4d} | " + " | ".join(f"{c:6d}" for c in cnt))
    write_csv(OUT / "advisor_overlap.csv", ["주제 코드", "범위", "리뷰 수"] + names, ov_rows)

    print(f"\n[중앙대 소속 논문] data/raw 전체에서 {len(cau)}편")
    for r in sorted(cau, key=lambda r: r["Year"]):
        c = codes.get(r["EID"])
        where = f"{c['범위']} {c['주제코드']}" if c else "AutCon 리뷰 밖"
        print(f"   {r['Year']} {r['Authors'].split(';')[0]:12s} [{where}] {r['Title'][:80]}")

    # ---------------------------------------------------------------- 본인 후보 (있을 때만)
    cands = read_tsv(CONFIG / "candidates.tsv")
    if not cands:
        print("\n[후보 적합] config/candidates.tsv가 비어 있어 건너뜀. 후보를 적으면 지수를 계산한다.")
        return
    for c in cands:
        bad = {x for x in c["연결 주제"].split(";") if x and x != "-"} - set(names)
        assert not bad, f"candidates.tsv {c['코드']}: advisor_themes.tsv에 없는 주제 {bad}"
    rows, idx, cons = [], {}, {}
    for c in cands:
        linked = [x for x in c["연결 주제"].split(";") if x and x != "-"]
        rx = re.compile(c["정규식"])
        lp = [p for p in pubs if set(tag[p["제목"]]) & set(linked)]
        rec = sum(int(p["연도"]) >= RECENT_FROM for p in lp)
        direct = [p for p in pubs if rx.search(p["제목"].lower())]
        net = [r for r in cau if rx.search(tak(r))]
        idx[c["코드"]] = 2 * rec + (len(lp) - rec) + 3 * len(direct) + len(net)
        cons[c["코드"]] = 3 * len(direct) + len(net)
        rows.append([c["코드"], c["이름"], ";".join(linked) or "-", idx[c["코드"]], cons[c["코드"]], len(lp), rec,
                     len(direct), " / ".join(f"{p['연도']} {p['제목'][:60]}" for p in direct), len(net),
                     " / ".join(f"{r['Year']} {r['Authors'].split(';')[0]} {r['Title'][:60]}" for r in net),
                     c["연결 근거"]])
    print("\n[후보 적합] (지수 | 보수적 지수 | 연결 주제 논문 전체/최근 | 제목 직접 일치 | 중앙대 논문 일치)")
    for row in sorted(rows, key=lambda x: -x[3]):
        print(f" {row[0]} {row[1][:30]:30s} {row[3]:3d} | {row[4]:3d} | {row[5]}/{row[6]} | {row[7]} | {row[9]}")
    write_csv(OUT / "advisor_fit.csv",
              ["코드", "후보", "연결 주제", "적합 지수", "보수적 지수(판단 제외)", "연결 주제 논문", "그중 2024년 이후",
               "제목 직접 일치 수", "제목 직접 일치 논문", "중앙대 논문 일치 수", "중앙대 논문", "연결 근거"], rows)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "advisor_stats.txt", "w", encoding="utf-8", newline="\n") as log:
        console, sys.stdout = sys.stdout, Tee(sys.stdout, log)
        try:
            print("=" * 20, "3. 지도교수", "=" * 20)
            build()
        finally:
            sys.stdout = console


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run()
