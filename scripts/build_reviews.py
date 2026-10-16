"""리뷰 논문 내보내기 7개로 연구 주제 선정용 분류표, VOSviewer 입력 파일, thesaurus, 방법 카탈로그, 통계를 만든다.
표준 라이브러리만 사용. 보통 build.py가 부른다(python scripts/build.py reviews). 혼자 실행해도 된다.

입력
    data/raw/scopus_review_autcon_20261016.csv              R0 AutCon 리뷰 전체
    data/raw/scopus_reviewtitle_autcon_20261016.csv         R1 AutCon Article 중 제목에 review
    data/raw/scopus_biblioreview_autcon_20261016.csv        R2 AutCon 계량서지 리뷰
    data/raw/scopus_sysreview_autcon_20261016.csv           R3 AutCon 체계적·비판적 리뷰
    data/raw/scopus_review_construction_20261016.csv        S1 건설 분야 리뷰 (여러 저널)
    data/raw/scopus_bibliometric_construction_20261016.csv  S2 건설 분야 계량서지
    data/raw/scopus_reviewframework_alldomain_20261016.csv  S3 분야 무관 리뷰 -> 프레임워크·연구 의제
    data/screening/review_codes.tsv                         AutCon 리뷰 합집합의 1차 분류 + 본인 검수
    config/topics.tsv, thesaurus_rules.tsv, thesaurus_rules_reviews.tsv, thesaurus_ignore_reviews.tsv
    config/review_terms.tsv                                 관심어·도구 용어
    config/method_catalog.tsv                               연구 주제를 찾는 방법 목록

출력 (모두 다시 만들어지므로 직접 고치지 않는다)
    output/vosviewer/scopus_review_autcon_{screened,sitevision,core}_20261016.csv  VOSviewer 입력
    output/vosviewer/thesaurus_reviews_topic.txt / thesaurus_reviews_method.txt     thesaurus
    output/review_screening.csv              읽기용 분류표
    output/reviews/gap_sentences.csv         핵심·주변 리뷰 초록의 공백 문장
    output/reviews/watch_terms.csv           관심어의 시기별 비율
    output/reviews/method_terms.csv          도구·자료원·분석·절차의 시기별 사용
    output/reviews/method_catalog.csv        방법별 사용 편수·추세·대표 논문·특징 인용 문헌
    output/reviews/emerging_keywords.csv     최근 비중이 크게 늘어난 키워드
    output/reviews/whitespace_pairs.csv      관심어 쌍의 기대 대비 동시 출현
    output/reviews/top_references.csv        코퍼스별 많이 인용된 참고문헌
    output/review_stats.txt                  통계 (화면 출력과 같음)
"""
import collections
import itertools
import math
import re
import sys

from common import (CONFIG, OUT, RAW, SCREEN, VOS, Tee, kwcount, load, load_topics, read_tsv, refs, tak, write_csv,
                    write_scopus)

DATE = "20261016"
CODES = SCREEN / "review_codes.tsv"
REV = OUT / "reviews"
SETS = {  # 코드: (파일 이름 부분, 설명)
    "R0": ("review_autcon", "AutCon 리뷰 전체"),
    "R1": ("reviewtitle_autcon", "AutCon Article 중 제목에 review"),
    "R2": ("biblioreview_autcon", "AutCon 계량서지 리뷰"),
    "R3": ("sysreview_autcon", "AutCon 체계적·비판적 리뷰"),
    "S1": ("review_construction", "건설 분야 리뷰(여러 저널)"),
    "S2": ("bibliometric_construction", "건설 분야 계량서지"),
    "S3": ("reviewframework_alldomain", "분야 무관 리뷰->프레임워크·의제"),
}
AUTCON = ("R0", "R3", "R2", "R1")
PERIODS = (("~2019", 0, 2019), ("2020-22", 2020, 2022), ("2023-27", 2023, 2027))
GAP_CUE = re.compile(r"\b(gaps?|lack(s|ing)?|limited|limitations?|challenges?|future|remains?|insufficient|scarce|"
                     r"under-?explored|unexplored|few studies|little attention|not yet|missing|need(s|ed)? (to|for))\b")
BROKEN_REF = re.compile(r"\(\d{4}\)")


def period(y):
    y = int(y)
    return next(name for name, a, b in PERIODS if a <= y <= b)


def review_kind(r):
    """초록·키워드에 적힌 방법으로 리뷰 유형을 나눈다 (자동)."""
    t = tak(r)
    if re.search(r"bibliometri|scientometri|science mapping|vosviewer|citespace|co-citation", t):
        return "계량서지"
    if re.search(r"systematic|prisma|scoping review|meta-analy", t):
        return "체계적"
    return "서술·기타"


def clean_refs(r):
    return {x for x in refs(r) if not BROKEN_REF.fullmatch(x)}


def load_thesaurus(present):
    """기본 + 리뷰 규칙을 합치고 사슬(a->b->c)을 c로 정리한다. 데이터에 나오는 label만 남긴다."""
    rules = {}
    for fn in ("thesaurus_rules.tsv", "thesaurus_rules_reviews.tsv"):
        for r in read_tsv(CONFIG / fn):
            lab, tgt = " ".join(r["label"].split()).lower(), " ".join(r["replace by"].split()).lower()
            assert lab not in rules or rules[lab] == tgt, f"{fn}: '{lab}' 규칙이 둘 이상"
            rules[lab] = tgt
    for lab in list(rules):
        seen, t = {lab}, rules[lab]
        while t in rules and rules[t] != t:
            assert t not in seen, f"thesaurus 순환: {lab}"
            seen.add(t)
            t = rules[t]
        rules[lab] = t
    return {k: v for k, v in rules.items() if k != v and k in present}


def write_thesaurus(fn, th):
    with open(fn, "w", encoding="utf-8", newline="") as f:
        f.write("label\treplace by\n")
        for a in sorted(th):
            f.write(f"{a}\t{th[a]}\n")


def short_ref(ref):
    """참고문헌 문자열을 '제1저자 (연도) 제목' 꼴로 줄인다."""
    au = ref.split(";")[0].split(",")[0].strip()
    year = re.findall(r"\((\d{4})\)", ref)
    parts = ref.split(", ")
    title = next((p for p in parts[1:] if len(p) > 25 and not re.search(r"\d+\s*\(|pp\.", p)), "")
    return f"{au} ({year[-1] if year else '?'}) {title[:90]}"


def method_catalog(corpora, everything, cites):
    """config/method_catalog.tsv의 방법마다 코퍼스별 편수, 추세, 대표 논문, 특징 인용 문헌을 구한다."""
    methods = [(r["코드"], r["계열"], r["방법"], re.compile(r["정규식"])) for r in read_tsv(CONFIG / "method_catalog.tsv")]
    texts = {e: tak(r) for e, r in everything.items()}
    ref_sets = {e: clean_refs(r) for e, r in everything.items()}
    ref_all = collections.Counter()
    for s in ref_sets.values():
        ref_all.update(s)
    n_all = len(everything)
    construction = set().union(*(set(corpora[k]) for k in ("AutCon 리뷰", "S1 건설 리뷰", "S2 건설 계량서지")))
    rows, summary = [], []
    for code, fam, name, rx in methods:
        hit = {e for e, t in texts.items() if rx.search(t)}
        cells = []
        for cname, eset in corpora.items():
            h = hit & set(eset)
            rec = sum(1 for e in h if int(everything[e]["Year"]) >= 2023)
            early = len(h) - rec
            n_rec = sum(1 for e in eset if int(everything[e]["Year"]) >= 2023)
            cells += [len(h), f"{len(h) / len(eset):.1%}",
                      f"{early / max(len(eset) - n_rec, 1):.1%} -> {rec / max(n_rec, 1):.1%}"]
        ex_c = sorted(hit & construction, key=lambda e: -cites[e])[:2]
        ex_o = sorted(hit - construction, key=lambda e: -cites[e])[:1]
        ex = lambda es: " / ".join(f"{everything[e]['Authors'].split(';')[0]} {everything[e]['Year']} "
                                   f"{everything[e]['Title'][:70]} ({cites[e]}회)" for e in es)
        rc = collections.Counter()
        for e in hit:
            rc.update(ref_sets[e])
        m = max(len(hit), 1)
        scored = [(c * math.log((c / m) / (ref_all[x] / n_all)), x, c) for x, c in rc.items()
                  if c >= 3 and (c / m) / (ref_all[x] / n_all) > 1.5]
        canon = " / ".join(f"{short_ref(x)} [{c}편]" for _, x, c in sorted(scored, reverse=True)[:3])
        rows.append([code, fam, name, len(hit)] + cells + [ex(ex_c), ex(ex_o), canon])
        summary.append((code, fam, name, len(hit), cells))
    head = ["코드", "계열", "방법", "전체 편수"]
    for cname in corpora:
        head += [f"{cname} 편수", f"{cname} 비율", f"{cname} ~2022 -> 2023~"]
    head += ["건설 분야 대표 논문(피인용 순)", "다른 분야 대표 논문", "이 방법을 쓴 논문이 특히 많이 인용한 문헌"]
    write_csv(REV / "method_catalog.csv", head, rows)
    return summary


def emerging_keywords(name, rows, th, recent_from=2024, min_recent=6):
    """최근(recent_from~) 키워드 비중을 그 이전과 비교한다. 이전에 없던 키워드는 '신규'."""
    early = [r for r in rows if int(r["Year"]) < recent_from]
    late = [r for r in rows if int(r["Year"]) >= recent_from]
    ce, cl = kwcount(early, th), kwcount(late, th)
    ce.pop("", None)
    cl.pop("", None)
    out = []
    for k, n in cl.items():
        if n < min_recent:
            continue
        se, sl = ce[k] / max(len(early), 1), n / len(late)
        growth = sl / se if se else float("inf")
        out.append([name, k, ce[k], n, f"{se:.2%}", f"{sl:.2%}", "신규" if not se else f"{growth:.1f}배"])
    out.sort(key=lambda x: (-(float("inf") if x[6] == "신규" else float(x[6][:-1])), -x[3]))
    return out, len(early), len(late)


def whitespace_pairs(rows, terms):
    """관심어 쌍마다 실제 동시 출현과 독립일 때의 기대값을 비교한다. 비율이 낮으면 함께 연구되지 않은 조합."""
    texts = [tak(r) for r in rows]
    n = len(texts)
    hit = {name: {i for i, t in enumerate(texts) if rx.search(t)} for _, name, rx in terms}
    out = []
    for a, b in itertools.combinations(hit, 2):
        both = len(hit[a] & hit[b])
        exp = len(hit[a]) * len(hit[b]) / n
        out.append([a, b, len(hit[a]), len(hit[b]), both, f"{exp:.1f}", f"{both / exp:.2f}" if exp else "-"])
    out.sort(key=lambda x: (float(x[6]) if x[6] != "-" else 99, -float(x[5])))
    return out, n


def build():
    VOS.mkdir(parents=True, exist_ok=True)
    REV.mkdir(parents=True, exist_ok=True)
    TOPIC = load_topics()
    data, fields = {}, None
    for code, (part, _) in SETS.items():
        fn = RAW / f"scopus_{part}_{DATE}.csv"
        if not fn.exists():
            sys.exit(f"리뷰 원본이 없다: {fn.name}. docs/review_search_log.md '파일' 표를 보고 data/raw/에 넣는다.")
        f, rows = load(fn)
        fields = fields or f
        assert f == fields, f"{code}: 열 구성이 다르다"
        data[code] = rows
    eids = {k: {r["EID"] for r in v} for k, v in data.items()}

    union = {}
    for code in AUTCON:
        for r in data[code]:
            union.setdefault(r["EID"], r)
    codes = {r["EID"]: r for r in read_tsv(CODES)}
    assert set(codes) == set(union), (len(codes), len(union))
    bad = {c["주제코드"] for c in codes.values()} - set(TOPIC)
    assert not bad, f"config/topics.tsv에 없는 주제코드: {bad}"
    assert {c["범위"] for c in codes.values()} <= {"핵심", "주변", "밖"}

    # ---------------------------------------------------------------- thesaurus
    present = collections.Counter()
    for rows in data.values():
        for r in rows:
            for col in ("Author Keywords", "Index Keywords"):
                present.update({" ".join(k.split()).lower() for k in r[col].split(";") if k.strip()})
    th = load_thesaurus(present)
    write_thesaurus(VOS / "thesaurus_reviews_method.txt", th)
    ignore = {" ".join(r["label"].split()).lower() for r in read_tsv(CONFIG / "thesaurus_ignore_reviews.tsv")}
    th_topic = {lab: ("" if tgt in ignore else tgt) for lab, tgt in th.items()}
    th_topic.update({w: "" for w in ignore if w in present})
    assert not (set(th) & set(th.values())), set(th) & set(th.values())
    write_thesaurus(VOS / "thesaurus_reviews_topic.txt", th_topic)

    # ---------------------------------------------------------------- VOSviewer 입력
    ordered = sorted(union.values(), key=lambda r: (r["Year"], r["Title"]))
    screened = [r for r in ordered if not codes[r["EID"]]["메모"].startswith("리뷰 아님")]
    site = [r for r in screened if codes[r["EID"]]["범위"] in ("핵심", "주변")]
    core = [r for r in screened if codes[r["EID"]]["범위"] == "핵심"]
    write_scopus(VOS / f"scopus_review_autcon_screened_{DATE}.csv", fields, screened)
    write_scopus(VOS / f"scopus_review_autcon_sitevision_{DATE}.csv", fields, site)
    write_scopus(VOS / f"scopus_review_autcon_core_{DATE}.csv", fields, core)

    # ---------------------------------------------------------------- 분류표
    order = {"핵심": 0, "주변": 1, "밖": 2}
    table = []
    for r in union.values():
        c = codes[r["EID"]]
        table.append([c["범위"], TOPIC[c["주제코드"]], c["단계"], r["Year"], r["Authors"].split(";")[0], r["Title"],
                      r["Cited by"], review_kind(r), c["공백(초록 기준)"], c["관련 후보"], c["메모"], c["본인검수"],
                      " + ".join(k for k in AUTCON if r["EID"] in eids[k]), r["Document Type"], r["DOI"], r["EID"]])
    table.sort(key=lambda t: (order[t[0]], t[1], -int(t[3]), t[5]))
    write_csv(OUT / "review_screening.csv",
              ["범위", "주제", "단계", "연도", "제1저자", "제목", "피인용", "리뷰 유형(자동)", "공백(초록 기준)", "관련 후보",
               "메모", "본인 검수", "검색 집합", "문서 유형", "DOI", "EID"], table)

    # ---------------------------------------------------------------- 공백 문장
    gap_rows = []
    for r in site:
        c = codes[r["EID"]]
        ab = re.sub(r"©.*$", "", r["Abstract"]).strip()
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", ab):
            if GAP_CUE.search(s.lower()):
                gap_rows.append([c["범위"], TOPIC[c["주제코드"]], r["Year"], r["Title"], s.strip(), r["EID"]])
    write_csv(REV / "gap_sentences.csv", ["범위", "주제", "연도", "제목", "공백 문장(자동 추출)", "EID"], gap_rows)

    # ---------------------------------------------------------------- 용어 집계
    terms = [(r["구분"], r["이름"], re.compile(r["정규식"])) for r in read_tsv(CONFIG / "review_terms.tsv")]
    corpora = {"AutCon 리뷰": screened, "AutCon 핵심+주변": site, "S1 건설 리뷰": data["S1"],
               "S2 건설 계량서지": data["S2"], "S3 분야 무관": data["S3"]}

    def share_rows(kinds, names):
        out = []
        for cname in names:
            rows = corpora[cname]
            texts = [(period(r["Year"]), tak(r)) for r in rows]
            n_p = collections.Counter(p for p, _ in texts)
            for kind, name, rx in terms:
                if kind not in kinds:
                    continue
                hit = collections.Counter(p for p, t in texts if rx.search(t))
                tot = sum(hit.values())
                out.append([cname, kind, name, len(rows), tot, f"{tot / len(rows):.1%}"] +
                           [f"{hit[p]}/{n_p[p]} ({hit[p] / n_p[p]:.0%})" if n_p[p] else "-" for p, _, _ in PERIODS])
        return out

    head = ["코퍼스", "구분", "이름", "편수", "언급 편수", "비율"] + [p for p, _, _ in PERIODS]
    watch = share_rows({"관심어"}, ("AutCon 리뷰", "AutCon 핵심+주변", "S1 건설 리뷰"))
    method = share_rows({"도구", "자료원", "분석", "절차"}, ("S2 건설 계량서지", "S3 분야 무관", "AutCon 리뷰"))
    write_csv(REV / "watch_terms.csv", head, watch)
    write_csv(REV / "method_terms.csv", head, method)

    # ---------------------------------------------------------------- 방법 카탈로그
    everything = {}
    for rows in data.values():
        for r in rows:
            everything.setdefault(r["EID"], r)
    cites = {e: int(r["Cited by"] or 0) for e, r in everything.items()}
    mc_corpora = {"AutCon 리뷰": [r["EID"] for r in screened], "S1 건설 리뷰": [r["EID"] for r in data["S1"]],
                  "S2 건설 계량서지": [r["EID"] for r in data["S2"]], "S3 분야 무관": [r["EID"] for r in data["S3"]]}
    catalog = method_catalog(mc_corpora, everything, cites)

    # ---------------------------------------------------------------- 신흥 키워드, 동시 출현 공백
    em_rows, em_info = [], {}
    s1_autcon = list({r["EID"]: r for r in data["S1"] + screened}.values())
    for name, rows in (("AutCon 리뷰", screened), ("건설 리뷰(S1+AutCon)", s1_autcon)):
        out, ne, nl = emerging_keywords(name, rows, th_topic)
        em_rows += out
        em_info[name] = (ne, nl, out)
    write_csv(REV / "emerging_keywords.csv",
              ["코퍼스", "키워드", "~2023 편수", "2024~ 편수", "~2023 비중", "2024~ 비중", "증가"], em_rows)
    watch_terms = [t for t in terms if t[0] == "관심어"]
    ws, ws_n = whitespace_pairs(s1_autcon, watch_terms)
    write_csv(REV / "whitespace_pairs.csv",
              ["관심어 A", "관심어 B", "A 편수", "B 편수", "함께 나온 편수", "독립일 때 기대", "실제/기대"], ws)

    # ---------------------------------------------------------------- 참고문헌
    ref_rows = []
    for cname, rows in (("AutCon 핵심", core), ("AutCon 핵심+주변", site), ("S2 건설 계량서지", data["S2"]),
                        ("S3 분야 무관", data["S3"])):
        rc = collections.Counter()
        for r in rows:
            rc.update(clean_refs(r))
        for i, (ref, n) in enumerate(rc.most_common(40), 1):
            ref_rows.append([cname, i, n, ref[:300]])
    write_csv(REV / "top_references.csv", ["코퍼스", "순위", "인용 편수", "참고문헌(소문자, 원문 앞 300자)"], ref_rows)

    # ---------------------------------------------------------------- 통계
    print("[파일]")
    for code, (part, desc) in SETS.items():
        rows = data[code]
        print(f" {code} {desc:28s} {len(rows):5d}편 | 문서 유형 {dict(collections.Counter(r['Document Type'] for r in rows))}")
    print(" 중복:", {f"{a}∩{b}": len(eids[a] & eids[b]) for i, a in enumerate(SETS) for b in list(SETS)[i + 1:]
                   if eids[a] & eids[b]})
    print(f" AutCon 합집합 {len(union)} -> 리뷰 아닌 것 제외 {len(screened)} | 핵심+주변 {len(site)} | 핵심 {len(core)}")

    print("\n[AutCon 리뷰]")
    print(" 시기:", dict(collections.Counter(period(r["Year"]) for r in screened)))
    print(" 리뷰 유형(자동):", dict(collections.Counter(review_kind(r) for r in screened)))
    print(" 리뷰 유형 x 시기:", {p: dict(collections.Counter(review_kind(r) for r in screened if period(r["Year"]) == p))
                             for p, _, _ in PERIODS})
    print(" 범위:", dict(collections.Counter(codes[r["EID"]]["범위"] for r in screened)))
    for sc in ("핵심", "주변"):
        rows = [r for r in screened if codes[r["EID"]]["범위"] == sc]
        print(f" {sc} 주제별 (~2019 / 2020-22 / 2023-27):")
        tc = collections.Counter(codes[r["EID"]]["주제코드"] for r in rows)
        for k in TOPIC:
            if tc[k]:
                per = collections.Counter(period(r["Year"]) for r in rows if codes[r["EID"]]["주제코드"] == k)
                print(f"   {TOPIC[k]:24s} {tc[k]:3d}  ({' / '.join(str(per[p]) for p, _, _ in PERIODS)})")
        print(f" {sc} 단계:", dict(collections.Counter(codes[r["EID"]]["단계"] for r in rows)))
    cand = collections.Counter()
    for r in site:
        cand.update(x for x in codes[r["EID"]]["관련 후보"].split(";") if x)
    print(" 관련 후보 열(본인 입력)별 리뷰 수:", dict(sorted(cand.items())) or "아직 없음")
    print(" 본인 검수 완료:", sum(bool(c["본인검수"].strip()) for c in codes.values()))
    print(" 공백 문장 자동 추출:", len(gap_rows), "문장 /", len({g[-1] for g in gap_rows}), "편")
    print(" 핵심 피인용 상위:")
    for r in sorted(core, key=lambda r: -int(r["Cited by"] or 0))[:10]:
        print(f"   {r['Cited by']:>5s} {r['Year']} {r['Authors'].split(';')[0]:14s} {r['Title'][:80]}")

    print("\n[관심어 비율] (코퍼스 | 이름 | 전체 | " + " | ".join(p for p, _, _ in PERIODS) + ")")
    for w in watch:
        print(f" {w[0]:14s} {w[2]:18s} {w[5]:>6s} | " + " | ".join(w[6:]))
    print("\n[도구·자료원·분석·절차]")
    for w in method:
        print(f" {w[0]:14s} {w[1]:4s} {w[2]:24s} {w[4]:4d}편 {w[5]:>6s} | " + " | ".join(w[6:]))

    print("\n[방법 카탈로그] (전체 편수 | AutCon 리뷰 / S1 / S2 / S3 비율 | S3 ~2022 -> 2023~)")
    for code, fam, name, n, cells in catalog:
        print(f" {code} {fam:8s} {name:22s} {n:5d} | {cells[1]:>6s} {cells[4]:>6s} {cells[7]:>6s} {cells[10]:>6s} | {cells[11]}")

    print("\n[신흥 키워드] (2024년 이후 비중 / 이전 비중, 2024년 이후 6편 이상)")
    for name, (ne, nl, out) in em_info.items():
        print(f" {name} (이전 {ne}편, 이후 {nl}편):", ", ".join(f"{x[1]}({x[6]}, {x[3]}편)" for x in out[:20]))
    print(f"\n[관심어 쌍의 동시 출현 공백] (건설 리뷰 {ws_n}편, 실제/기대가 낮을수록 함께 연구되지 않음, 기대 2편 이상만)")
    for x in [x for x in ws if float(x[5]) >= 2][:15]:
        print(f" {x[0]} × {x[1]}: 실제 {x[4]} / 기대 {x[5]} = {x[6]}")

    print("\n[VOSviewer 기준값] (저자 키워드, 주제용 thesaurus 적용 / 참고문헌은 문자열이 같은 것만 센 하한값)")
    for name, rows, t in (("AutCon 리뷰", screened, th_topic), ("AutCon 핵심+주변", site, th_topic),
                          ("AutCon 핵심", core, th_topic), ("S1 건설 리뷰", data["S1"], th_topic),
                          ("S2 건설 계량서지", data["S2"], th), ("S3 분야 무관", data["S3"], th)):
        kc = kwcount(rows, t)
        kc.pop("", None)
        rc = collections.Counter()
        for r in rows:
            rc.update(clean_refs(r))
        thr = " ".join(f"{m}회+ {sum(v >= m for v in kc.values())}" for m in (2, 3, 5, 10, 20))
        rthr = " ".join(f"{m}편+ {sum(v >= m for v in rc.values())}" for m in (3, 5, 10, 20, 50))
        print(f" {name}: 키워드 {thr} | 참고문헌 {rthr}")
    print(" thesaurus 쌍: 방법용", len(th), "| 주제용", len(th_topic), f"(그중 제거 {sum(1 for v in th_topic.values() if not v)})")
    print(" 상위 키워드(AutCon 핵심+주변):", [k for k, _ in kwcount(site, th_topic).most_common(31) if k][:30])


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "review_stats.txt", "w", encoding="utf-8", newline="\n") as log:
        console, sys.stdout = sys.stdout, Tee(sys.stdout, log)
        try:
            print("=" * 20, "2. 리뷰", "=" * 20)
            build()
        finally:
            sys.stdout = console


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run()
