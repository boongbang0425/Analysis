"""저장소의 모든 출력을 다시 만든다. 표준 라이브러리만 사용 (pandas 불필요).

단계
    1. 원저   현장 인식 원저 Scopus 내보내기 4개 -> 1차 분류표, VOSviewer 입력, thesaurus, 통계 (이 파일)
    2. 리뷰   리뷰 논문 7개 집합 -> 분류표, VOSviewer 입력, 공백 문장, 관심어·방법 집계 (build_reviews.py)
    3. 지도교수  지도교수 논문 -> 주제 분포, 후보별 적합성 (build_advisor.py)

원저 원본은 git에 올리지 않으므로 새로 받은 저장소에는 없다. 없으면 그 파일에 기대는 처리만 건너뛰고,
분류 원자료(screening_codes.tsv)만으로 낼 수 있는 통계와 분류표는 그대로 만든다. 다시 받는 방법은 화면에 나온다.

원저 입력 (data/raw/, 없어도 된다)
    scopus_sitevision_autcon_20261008.csv  현장 x 인식 (주 집합)
    scopus_main_autcon_20261008.csv        현장 x 인식 x 주제 (1차 본검색, 주 집합의 부분집합)
    scopus_wearable_autcon_20261008.csv    웨어러블 비교군
    scopus_depth_autcon_20261008.csv       뎁스·스테레오
    data/screening/screening_codes.tsv     논문별 1차 분류 (Claude, 초록만 읽음) + 본인 검수
    config/topics.tsv, config/thesaurus_rules.tsv

원저 출력 (모두 다시 만들어지므로 직접 고치지 않는다)
    output/vosviewer/scopus_sitevision_screened_autcon_20261008.csv  VOSviewer 주 입력 (현장 x 인식 원본 필요)
    output/vosviewer/scopus_all_autcon_20261008.csv                  합집합 (있는 원본만으로)
    output/vosviewer/thesaurus_keywords.txt                          VOSviewer thesaurus
    output/screening_1st_pass.csv                                     읽기용 분류표 (원본이 없으면 서지 열이 빈다)
    output/stats.txt                                                  통계 (화면 출력과 같음)

사용법 (저장소 최상위에서)
    python scripts/build.py                  세 단계 모두
    python scripts/build.py articles         원저만 (reviews, advisor도 같은 방식)
"""
import collections
import re
import sys

from common import (CONFIG, OUT, RAW, SCREEN, VOS, Tee, kwcount, load, load_topics, read_tsv, refs, write_csv,
                    write_scopus)

DATE = "20261008"
SCREENING = SCREEN / "screening_codes.tsv"
ARTICLE_SETS = {  # 코드: (파일 이름 부분, 이름)
    "S": ("sitevision", "현장×인식"),
    "M": ("main", "주제 한정"),
    "W": ("wearable", "웨어러블"),
    "D": ("depth", "뎁스"),
}
RESTORE = """  다시 받는 법: Scopus(기관 접속)에서 docs/search_log.md '검색 조건'의 검색식을 실행하고
  CSV로 내보낸다(모든 필드, 초록·참고문헌 포함). 위 이름으로 data/raw/에 넣고 다시 실행한다.
  주제 한정·웨어러블 두 개는 복원본이었으므로, 합집합 파일이 있으면 그것으로도 다시 만들 수 있다."""


def load_thesaurus_rules():
    rules = {}
    for r in read_tsv(CONFIG / "thesaurus_rules.tsv"):
        lab, tgt = r["label"].strip().lower(), r["replace by"].strip().lower()
        assert lab not in rules or rules[lab] == tgt, f"thesaurus_rules.tsv: '{lab}' 규칙이 둘 이상"
        rules[lab] = tgt
    return rules


def sensing_class(s):
    t = s.replace("단안 깊이 추정", "").replace("깊이 추정", "").replace("깊이는", "")
    if any(k in t for k in ("뎁스", "RGB-D", "스테레오", "Kinect", "깊이 맵", "3D 카메라")):
        return "뎁스·스테레오"
    if any(k in t for k in ("LiDAR", "레이저", "점군", "구조광")):
        return "LiDAR·점군"
    if any(k in t for k in ("RGB", "영상", "이미지", "카메라", "CCTV", "사진", "웹캠", "열화상")):
        return "RGB 영상"
    return "기타"


def period(y):
    y = int(y)
    return "2015-19" if y <= 2019 else "2020-22" if y <= 2022 else "2023-26"


def build_articles():
    VOS.mkdir(parents=True, exist_ok=True)
    TOPIC = load_topics()
    codes = {r["EID"]: r for r in read_tsv(SCREENING)}
    bad = {c["주제코드"] for c in codes.values()} - set(TOPIC)
    assert not bad, f"config/topics.tsv에 없는 주제코드: {bad}"

    data, fields, missing = {}, None, []
    for k, (part, _) in ARTICLE_SETS.items():
        fn = RAW / f"scopus_{part}_autcon_{DATE}.csv"
        if fn.exists():
            f, data[k] = load(fn)
            fields = fields or f
        else:
            missing.append(fn.name)
    if missing:
        print(f"[원본 없음] {len(missing)}개: {', '.join(missing)}")
        print("  이 파일에 기대는 처리(VOSviewer 입력, 연도·서지 통계)는 건너뛴다.")
        print(RESTORE)
    eids = {k: {r["EID"] for r in v} for k, v in data.items()}
    if "M" in eids and "S" in eids:
        assert eids["M"] <= eids["S"]

    allr = {}
    for k in ("S", "W", "D"):
        for r in data.get(k, []):
            allr.setdefault(r["EID"], r)
    union = list(allr.values())
    assert set(allr) <= set(codes), f"screening_codes.tsv에 없는 EID {len(set(allr) - set(codes))}개"
    if all(k in data for k in ("S", "W", "D")):
        assert set(codes) == set(allr), (len(codes), len(allr))

    # ---------------------------------------------------------------- thesaurus
    rules = load_thesaurus_rules()
    if union:
        present = collections.Counter()
        for r in union:
            for col in ("Author Keywords", "Index Keywords"):
                present.update({k.strip().lower() for k in r[col].split(";") if k.strip()})
        th = {lab: tgt for lab, tgt in rules.items() if lab in present}
    else:
        th = dict(rules)  # 데이터가 없으면 규칙 전체를 쓴다 (VOSviewer는 없는 label을 무시한다)
    assert not (set(th) & set(th.values())), set(th) & set(th.values())
    with open(VOS / "thesaurus_keywords.txt", "w", encoding="utf-8", newline="") as f:
        f.write("label\treplace by\n")
        for a in sorted(th):
            f.write(f"{a}\t{th[a]}\n")

    # ---------------------------------------------------------------- VOSviewer 입력
    S = data.get("S", [])
    screened = [r for r in S if codes[r["EID"]]["적합도"] != "제외"]
    if union:
        write_scopus(VOS / f"scopus_all_autcon_{DATE}.csv", fields, union)
    if S:
        write_scopus(VOS / f"scopus_sitevision_screened_autcon_{DATE}.csv", fields, screened)

    # ---------------------------------------------------------------- 분류표
    def sets(e):
        tags = [name for k, (_, name) in ARTICLE_SETS.items() if e in eids.get(k, ())]
        return " + ".join(tags) if tags else "(원본 없음)"

    cols = ["검색 집합", "연도", "저자", "제목", "피인용", "단계", "센싱", "주제", "세부 주제", "인식 뒤 반응",
            "검증(초록 기준)", "언어·생성모델 중심", "관심 적합도", "보유 장비로 재현(추정)", "메모", "본인 검수", "DOI", "EID"]
    order = {"상": 0, "중": 1, "하": 2, "제외": 3, "비교군": 4}
    table = []
    for e, c in codes.items():
        r = allr.get(e)
        memo = [c["메모"]] if c["메모"] else []
        if r and "Ham, Y" in r["Author full names"]:
            memo.append("Youngjib Ham(이지희 교수 공저자) 참여")
        if r and "chung-ang" in r["Affiliations"].lower():
            memo.append("중앙대 소속 저자 포함")
        bib = [r["Year"], r["Authors"], r["Title"], r["Cited by"]] if r else ["", "", "", ""]
        table.append([sets(e)] + bib + [c["단계"], c["센싱"], TOPIC[c["주제코드"]], c["주제"], c["반응"], c["검증"],
                                        c["언어생성모델"], c["적합도"], c["재현추정"], ". ".join(memo),
                                        c.get("본인검수") or "", r["DOI"] if r else "", e])
    table.sort(key=lambda t: (order[t[12]], -int(t[1] or 0), t[3], t[17]))
    write_csv(OUT / "screening_1st_pass.csv", cols, table)

    # ---------------------------------------------------------------- 통계 (분류 원자료만으로)
    C = collections.Counter
    print(f"\n[분류 원자료 {len(codes)}편] (screening_codes.tsv, 원본 없이도 계산)")
    print(" 적합도:", dict(C(c["적합도"] for c in codes.values())))
    tc = C(c["주제코드"] for c in codes.values())
    print(" 주제:", {TOPIC[k]: tc[k] for k in TOPIC if tc[k]})
    print(" 센싱:", dict(C(sensing_class(c["센싱"]) for c in codes.values())))
    print(" 단계:", dict(C(c["단계"] for c in codes.values())))
    print(" 언어·생성모델 중심:", C(c["언어생성모델"] for c in codes.values())["Y"])
    print(" 인식 뒤 반응 있음:", sum(c["반응"] not in ("없음", "") for c in codes.values() if c["적합도"] != "비교군"))
    top = [c for c in codes.values() if c["적합도"] == "상"]
    print(f" 적합도 상 {len(top)}: 재현", dict(C(c["재현추정"].split("(")[0] for c in top)),
          "| 주제", dict(C(c["주제코드"] for c in top)))
    print(" 본인 검수 완료:", sum(bool((c.get("본인검수") or "").strip()) for c in codes.values()))

    # ---------------------------------------------------------------- 통계 (원본 필요)
    if not data:
        print("\n[원본 기반 통계] 원본이 없어 건너뜀 (연도별 주제, 저자, VOSviewer 기준값)")
        return
    have = " | ".join(f"{name} {len(data[k])}" for k, (_, name) in ARTICLE_SETS.items() if k in data)
    print(f"\n[원본] {have} | 합집합(있는 것만) {len(union)}")
    if S:
        print(f" 선별 후 현장×인식 {len(screened)}편 (제외 {len(S) - len(screened)})")
        print("\n[현장×인식]")
        print(" 연도:", sorted(C(r["Year"] for r in S).items()))
        tcs = C(codes[r["EID"]]["주제코드"] for r in S)
        for k in TOPIC:
            if tcs[k]:
                per = C(period(r["Year"]) for r in S if codes[r["EID"]]["주제코드"] == k)
                print(f"  {TOPIC[k]:28s} {tcs[k]:3d}  (2015-19 {per['2015-19']}, 2020-22 {per['2020-22']}, 2023-26 {per['2023-26']})")
        print(" 언어·생성모델 중심 연도별:",
              sorted(C(r["Year"] for r in S if codes[r["EID"]]["언어생성모델"] == "Y").items()))
        au = C()
        for r in S:
            for a in r["Author full names"].split(";"):
                a = re.sub(r"\s*\(\d+\)", "", a).strip()
                if a:
                    au[a] += 1
        print(" 다작 저자:", au.most_common(12))
    if "D" in data:
        D = data["D"]
        print("\n[뎁스]")
        print(" 단계:", dict(C(codes[r["EID"]]["단계"] for r in D)))
        print(" 연도:", sorted(C(r["Year"] for r in D).items()))
    print("\n[뎁스·스테레오 센서를 실제로 쓴 논문 (있는 원본, 제외 아닌 것)]")
    for r in sorted(union, key=lambda r: r["Year"]):
        c = codes[r["EID"]]
        if sensing_class(c["센싱"]) == "뎁스·스테레오" and c["적합도"] != "제외":
            print(f"  {r['Year']} {r['Authors'].split(';')[0]:18s} {c['주제코드']} {c['적합도']} | {c['센싱']} | {c['주제']}")
    for name, key in (("Ham", lambda r: "Ham, Y" in r["Author full names"]),
                      ("이지희", lambda r: "jeehee" in r["Author full names"].lower()),
                      ("중앙대", lambda r: "chung-ang" in r["Affiliations"].lower())):
        hits = [(r["Year"], r["Authors"].split(";")[0], r["Title"][:70], sets(r["EID"])) for r in union if key(r)]
        print(f" {name}: {len(hits)}")
        for h in hits:
            print("    ", h)

    print("\n[VOSviewer 기준값]")
    for name, rows in (("현장×인식", S), ("선별 후", screened), ("합집합", union)):
        if not rows:
            continue
        t = kwcount(rows, th)
        rc = C()
        for r in rows:
            rc.update(refs(r))
        print(f" {name} {len(rows)}: 저자 키워드 {len(kwcount(rows))} -> {len(t)}, 3회+ {sum(v >= 3 for v in t.values())}, "
              f"5회+ {sum(v >= 5 for v in t.values())} | 참고문헌 10편+ {sum(v >= 10 for v in rc.values())}, "
              f"20편+ {sum(v >= 20 for v in rc.values())}")
    print(" thesaurus 쌍:", len(th))


def run_articles():
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "stats.txt", "w", encoding="utf-8", newline="\n") as log:
        console, sys.stdout = sys.stdout, Tee(sys.stdout, log)
        try:
            print("=" * 20, "1. 원저", "=" * 20)
            build_articles()
        finally:
            sys.stdout = console


def main(argv):
    import build_advisor
    import build_reviews
    steps = {"articles": run_articles, "reviews": build_reviews.run, "advisor": build_advisor.run}
    for name in argv or steps:
        if name not in steps:
            sys.exit(f"알 수 없는 단계: {name} (가능: {', '.join(steps)})")
        steps[name]()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
