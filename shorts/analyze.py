"""collect.py 결과에서 잘된 영상과 안된 영상의 차이를 숫자로 뽑는다.

    python3 shorts/analyze.py 신비한_건축사전_1
"""
import json
import re
import statistics as st
import sys
from pathlib import Path

DATA = Path(__file__).parent / "data"

# 제목 특징: 이름 → 정규식 (긴 제목은 따로 계산)
TITLE_FEATURES = {
    "가정형 '만약 ~라면'": r"만약",
    "부정 반전 '~이 아닙니다'": r"아닙니다|아니라|아니었",
    "'이유·방법·비밀'": r"이유|방법|비밀",
    "익숙한 장소·고유명사": r"서울|한강|부산|해운대|제주|경복궁|강남|인천|대구|아파트|빌라|지하철|청계천|남한산성|강화도|창덕궁|한양|석굴암|엘시티|롯데|성수|목동",
    "숫자 포함": r"\d",
}
LONG_TITLE = 35
LENGTH_BINS = ((0, 60), (61, 90), (91, 120), (121, 150), (151, 180))
# 전기 소재: '전기도 없던', '에어컨 없이'처럼 전기를 빼는 소재는 넣지 않는다
ELECTRIC = r"발전소|발전기|원자력|송전|변전|전력|(?<!근)정전|충전|전기의|전기가 나오|에어컨을 켜"


def median(xs):
    return f"{st.median(xs):,.0f}" if xs else "-"


def like_rate(ms):
    return f"{st.median(m['like_count'] / m['view_count'] for m in ms):.2%}" if ms else "-"


def man(n):
    return f"{n / 10000:,.0f}만" if n >= 10000 else f"{n:,}"


def main(name):
    rows = [r for r in json.loads((DATA / f"{name}.list.json").read_text()) if r[1] > 0]
    meta = [json.loads(l) for l in open(DATA / f"{name}.jsonl")]
    views = sorted(r[1] for r in rows)
    print(f"## {name}: 숏츠 {len(rows)}편\n")
    print(f"- 조회수 중앙값 {median(views)}, 상위 10% 기준 {views[int(len(views) * 0.9)]:,}\n")

    cut_hi, cut_lo = views[int(len(views) * 0.9)], views[int(len(views) * 0.1)]
    # 업로드 시기가 조회수를 크게 가른다(초기엔 낮고 최근엔 덜 쌓였다). 그래서 상위 10%가 나온 기간 안에서도 따로 본다
    dated = [m for m in meta if m["upload_date"]]
    top_dates = [m["upload_date"] for m in dated if m["view_count"] >= cut_hi]
    lo, hi = (min(top_dates), max(top_dates)) if top_dates else (None, None)
    peak = [(m["id"], m["view_count"], m["title"]) for m in dated if lo and lo <= m["upload_date"] <= hi]

    tests = [(label, lambda t, pat=pat: re.search(pat, t)) for label, pat in TITLE_FEATURES.items()]
    tests.append((f"제목 {LONG_TITLE}자 초과", lambda t: len(t) > LONG_TITLE))
    if peak:
        print(f"'기간 내'는 상위 10%가 나온 {lo}~{hi}에 올라온 {len(peak)}편입니다.\n")
    print("| 제목 특징 | 해당 편수 | 해당 중앙값 | 비해당 중앙값 | 기간 내 편수 | 기간 내 해당 | 기간 내 비해당 |")
    print("|---|---|---|---|---|---|---|")
    for label, hit in tests:
        cells = []
        for group in (rows, peak):
            yes = [r[1] for r in group if hit(r[2])]
            no = [r[1] for r in group if not hit(r[2])]
            cells += [str(len(yes)), median(yes), median(no)]
        print(f"| {label} | " + " | ".join(cells) + " |")
    print()

    for label, group in (("상위 10%", [m for m in meta if m["view_count"] >= cut_hi]),
                         ("하위 10%", [m for m in meta if m["view_count"] <= cut_lo])):
        if not group:
            continue
        # 봇 확인에 걸려 받은 영상은 길이·좋아요·날짜가 비어 있다
        full = [m for m in group if m["duration"] and m["like_count"] and m["upload_date"]]
        if not full:
            print(f"- {label} ({len(group)}편): 길이·반응 데이터 없음 (collect.py --cookies로 다시 받기)")
            continue
        print(f"- {label} ({len(group)}편): 길이 중앙값 {median([m['duration'] for m in full])}초, "
              f"좋아요율 {like_rate(full)}, "
              f"업로드 {min(m['upload_date'] for m in full)}~{max(m['upload_date'] for m in full)}")

    # 아래 표는 길이·좋아요가 다 있는 영상만 쓴다. API로 받으면 전부, yt-dlp로 받으면 일부다
    full = [m for m in meta if m["duration"] and m["like_count"] is not None and m["upload_date"]]
    if not full:
        return
    # 길이도 업로드 시기와 얽혀 있다(초기엔 짧고 최근엔 길다)
    peak = [m for m in full if lo <= m["upload_date"] <= hi]
    print(f"\n### 길이 구간\n\n'기간 내'는 상위 10%가 나온 {lo}~{hi}에 올라온 {len(peak)}편입니다.\n")
    print("| 길이 | 편수 | 조회수 중앙값 | 좋아요율 | 기간 내 편수 | 기간 내 조회수 중앙값 | 기간 내 좋아요율 |")
    print("|---|---|---|---|---|---|---|")
    for a, b in LENGTH_BINS:
        g = [m for m in full if a <= m["duration"] <= b]
        p = [m for m in peak if a <= m["duration"] <= b]
        print(f"| {a}–{b}초 | {len(g)} | {median([m['view_count'] for m in g])} | {like_rate(g)} "
              f"| {len(p)} | {median([m['view_count'] for m in p])} | {like_rate(p)} |")

    print(f"\n### 좋아요율 4분위 ({lo}~{hi} 업로드 {len(peak)}편)\n")
    print("| 구간 | 좋아요율 중앙값 | 조회수 중앙값 | 길이 중앙값 |\n|---|---|---|---|")
    ranked, q = sorted(peak, key=lambda m: m["like_count"] / m["view_count"]), len(peak) // 4
    for i in range(4):
        g = ranked[i * q : (i + 1) * q if i < 3 else None]
        print(f"| {i + 1}분위 | {like_rate(g)} | {median([m['view_count'] for m in g])} "
              f"| {median([m['duration'] for m in g])}초 |")
    print(f"\n- 전체 좋아요율 중앙값 {like_rate(full)}")

    print("\n### 상위 15편\n")
    for m in sorted(meta, key=lambda m: -m["view_count"])[:15]:
        lr = f" · 좋아요 {m['like_count'] / m['view_count']:.2%}" if m["like_count"] is not None else ""
        print(f"- {m['view_count']:,} · {m['duration'] or '?'}초{lr} · {m['title']}")

    print("\n### 전기 관련 영상\n")
    print("| 조회수 | 길이 | 좋아요율 | 업로드 | 제목 |\n|---|---|---|---|---|")
    for m in sorted((m for m in full if re.search(ELECTRIC, m["title"])), key=lambda m: -m["view_count"]):
        print(f"| {man(m['view_count'])} | {m['duration']}초 | {m['like_count'] / m['view_count']:.2%} "
              f"| {m['upload_date']} | {m['title'].strip()} |")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "신비한_건축사전_1")
