"""벤치마크 채널의 숏츠를 모아 조회수 순으로 정리한다.

YouTube API 키 없이 공개 페이지에서 yt-dlp로 읽는다. 결과는 data/<handle>.jsonl.
유튜브가 봇 확인을 걸면 길이·좋아요가 비는데, 브라우저 쿠키를 넘기면 다 받는다.

    python3 shorts/collect.py @신비한_건축사전_1 --top 60 --bottom 40 --match "전기|전력|발전"
    python3 shorts/collect.py @채널 --cookies cookies.txt
"""
import argparse
import json
import re
from pathlib import Path

import yt_dlp

DATA = Path(__file__).parent / "data"


KOREAN = {
    "http_headers": {"Accept-Language": "ko-KR,ko;q=0.9"},
    "extractor_args": {"youtube": {"lang": ["ko"]}},
}


def list_shorts(handle):
    """채널의 숏츠 탭 전체를 (id, 조회수, 한국어 제목) 목록으로 가져온다.

    한국어로 요청하면 조회수가 빠지고, 기본 언어로 요청하면 제목이 영어로 번역된다.
    그래서 두 번 읽어 합친다.
    """
    url = f"https://www.youtube.com/{handle}/shorts"
    base = {"extract_flat": True, "quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(base) as ydl:
        views = {e["id"]: e.get("view_count") or 0 for e in ydl.extract_info(url, download=False)["entries"]}
    with yt_dlp.YoutubeDL({**base, **KOREAN}) as ydl:
        titles = {e["id"]: e.get("title") or "" for e in ydl.extract_info(url, download=False)["entries"]}
    return [(vid, n, titles.get(vid, "")) for vid, n in views.items()]


def video_meta(video_id, cookies=None):
    """영상 하나의 한국어 제목·길이·반응·설명란. 설명란은 대본 요약 역할을 한다."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignore_no_formats_error": True,
        **KOREAN,
    }
    if cookies:
        opts["cookiefile"] = cookies
    with yt_dlp.YoutubeDL(opts) as ydl:
        d = ydl.extract_info(f"https://www.youtube.com/shorts/{video_id}", download=False)
    keys = ("id", "title", "duration", "view_count", "like_count", "comment_count", "upload_date", "description")
    return {k: d.get(k) for k in keys}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handle", help="채널 핸들, 예: @신비한_건축사전_1")
    ap.add_argument("--top", type=int, default=60, help="조회수 상위 몇 편의 상세를 받을지")
    ap.add_argument("--bottom", type=int, default=40, help="조회수 하위 몇 편의 상세를 받을지")
    ap.add_argument("--match", default="", help="제목이 이 정규식에 맞는 영상도 상세를 받는다")
    ap.add_argument("--cookies", help="Netscape 형식 쿠키 파일 (봇 확인 우회)")
    args = ap.parse_args()

    rows = sorted(list_shorts(args.handle), key=lambda r: -r[1])
    views = {r[0]: r[1] for r in rows}
    pick = [r[0] for r in rows[: args.top]] + [r[0] for r in rows[-args.bottom :]]
    if args.match:
        pick += [r[0] for r in rows if re.search(args.match, r[2])]
    pick = list(dict.fromkeys(pick))

    DATA.mkdir(exist_ok=True)
    name = args.handle.lstrip("@")
    (DATA / f"{name}.list.json").write_text(json.dumps(rows, ensure_ascii=False))
    with open(DATA / f"{name}.jsonl", "w") as f:
        for i, vid in enumerate(pick, 1):
            try:
                meta = video_meta(vid, args.cookies)
                # 한국어로 받으면 조회수가 빠지므로 목록의 값으로 채운다
                meta["view_count"] = meta["view_count"] or views[vid]
                f.write(json.dumps(meta, ensure_ascii=False) + "\n")
            except yt_dlp.utils.DownloadError as e:
                print(f"skip {vid}: {e}")
            print(f"\r{i}/{len(pick)}", end="", flush=True)
    print(f"\n{len(rows)}편 목록, {len(pick)}편 상세 → {DATA}/{name}.jsonl")


if __name__ == "__main__":
    main()
