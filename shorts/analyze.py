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


def median(xs):
    return f"{st.median(xs):,.0f}" if xs else "-"


def main(name):
    rows = [r for r in json.loads((DATA / f"{name}.list.json").read_text()) if r[1] > 0]
    meta = [json.loads(l) for l in open(DATA / f"{name}.jsonl")]
    views = sorted(r[1] for r in rows)
    print(f"## {name}: 숏츠 {len(rows)}편\n")
    print(f"- 조회수 중앙값 {median(views)}, 상위 10% 기준 {views[int(len(views) * 0.9)]:,}\n")

    print("| 제목 특징 | 해당 편수 | 해당 중앙값 | 비해당 중앙값 |\n|---|---|---|---|")
    feats = dict(TITLE_FEATURES)
    for label, pat in feats.items():
        yes = [r[1] for r in rows if re.search(pat, r[2])]
        no = [r[1] for r in rows if not re.search(pat, r[2])]
        print(f"| {label} | {len(yes)} | {median(yes)} | {median(no)} |")
    yes = [r[1] for r in rows if len(r[2]) > LONG_TITLE]
    no = [r[1] for r in rows if len(r[2]) <= LONG_TITLE]
    print(f"| 제목 {LONG_TITLE}자 초과 | {len(yes)} | {median(yes)} | {median(no)} |\n")

    cut_hi, cut_lo = views[int(len(views) * 0.9)], views[int(len(views) * 0.1)]
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
              f"좋아요율 {st.median(m['like_count'] / m['view_count'] for m in full):.2%}, "
              f"업로드 {min(m['upload_date'] for m in full)}~{max(m['upload_date'] for m in full)}")

    print("\n### 상위 15편\n")
    for m in sorted(meta, key=lambda m: -m["view_count"])[:15]:
        print(f"- {m['view_count']:,} · {m['duration'] or '?'}초 · {m['title']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "신비한_건축사전_1")
