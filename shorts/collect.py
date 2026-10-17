"""벤치마크 채널의 숏츠를 모아 조회수 순으로 정리한다.

YOUTUBE_API_KEY가 있으면 YouTube Data API로 채널 업로드 전체의 길이·조회수·좋아요·설명란을 받는다.
키가 없거나, 틀렸거나, 하루 한도를 넘으면 공개 페이지를 yt-dlp로 읽는 방식으로 자동 전환한다.
yt-dlp 방식은 유튜브가 봇 확인을 걸면 길이·좋아요가 비는데, 브라우저 쿠키를 넘기면 다 받는다.
어느 쪽이든 길이가 180초를 넘는 영상은 숏츠가 아니므로 뺀다. 결과는 data/<handle>.jsonl.

    python3 shorts/collect.py @신비한_건축사전_1 --top 60 --bottom 40 --match "전기|전력|발전"
    python3 shorts/collect.py @채널 --cookies cookies.txt
    python3 shorts/collect.py @채널 --no-api
"""
import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DATA = Path(__file__).parent / "data"
API = "https://www.googleapis.com/youtube/v3"
SHORTS_MAX = 180  # 유튜브 숏츠 최대 길이(초)


class ApiUnavailable(Exception):
    """키가 틀렸거나, 막혔거나, 하루 한도를 넘었거나, 접속이 안 될 때. yt-dlp로 넘어간다."""


# --- YouTube Data API -------------------------------------------------------

def api_get(endpoint, key, **params):
    url = f"{API}/{endpoint}?" + urllib.parse.urlencode({**params, "key": key})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body)["error"]
            reasons = {x.get("reason") for x in err.get("errors", []) + err.get("details", [])}
        except (ValueError, KeyError, TypeError, AttributeError):
            reasons = set()
        if reasons & {"quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded"}:
            raise ApiUnavailable(f"한도 초과({', '.join(sorted(filter(None, reasons)))})") from None
        if reasons & {"API_KEY_INVALID", "keyInvalid", "accessNotConfigured", "SERVICE_DISABLED",
                      "API_KEY_SERVICE_BLOCKED", "API_KEY_HTTP_REFERRER_BLOCKED", "API_KEY_IP_ADDRESS_BLOCKED"}:
            raise ApiUnavailable(f"키를 쓸 수 없음({', '.join(sorted(filter(None, reasons)))})") from None
        raise RuntimeError(f"YouTube API {e.code} {endpoint}: {body[:300]}") from None
    except urllib.error.URLError as e:
        raise ApiUnavailable(f"접속 실패({e.reason})") from None


def iso_seconds(s):
    """ISO 8601 길이(PT1M36S)를 초로."""
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m:
        return None
    d, h, mi, se = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + se


def api_collect(handle, key):
    """채널 업로드 전체를 API로 받아 180초 이하만 남긴다. 단위 비용은 영상 50편당 약 2."""
    ch = api_get("channels", key, part="contentDetails", forHandle=handle)
    if not ch.get("items"):
        raise RuntimeError(f"채널을 찾지 못했습니다: {handle}")
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    ids, token = [], None
    while True:
        page = api_get("playlistItems", key, part="contentDetails", playlistId=uploads,
                       maxResults=50, **({"pageToken": token} if token else {}))
        ids += [it["contentDetails"]["videoId"] for it in page["items"]]
        token = page.get("nextPageToken")
        if not token:
            break

    metas = []
    for i in range(0, len(ids), 50):
        page = api_get("videos", key, part="snippet,contentDetails,statistics", id=",".join(ids[i : i + 50]))
        for v in page["items"]:
            sn, st = v["snippet"], v.get("statistics", {})
            num = lambda k: int(st[k]) if k in st else None  # 좋아요·댓글을 숨긴 영상은 키가 없다
            metas.append({
                "id": v["id"],
                "title": sn["title"],
                "duration": iso_seconds(v["contentDetails"]["duration"]),
                "view_count": num("viewCount") or 0,
                "like_count": num("likeCount"),
                "comment_count": num("commentCount"),
                "upload_date": sn["publishedAt"][:10].replace("-", ""),
                "description": sn.get("description", ""),
            })
        print(f"\r{min(i + 50, len(ids))}/{len(ids)}", end="", flush=True)
    print()
    shorts = [m for m in metas if m["duration"] is not None and 0 < m["duration"] <= SHORTS_MAX]
    print(f"업로드 {len(metas)}편 중 {SHORTS_MAX}초 이하 {len(shorts)}편")
    return shorts


# --- yt-dlp (API 키가 없을 때) ----------------------------------------------

KOREAN = {
    "http_headers": {"Accept-Language": "ko-KR,ko;q=0.9"},
    "extractor_args": {"youtube": {"lang": ["ko"]}},
}


def list_shorts(handle):
    """채널의 숏츠 탭 전체를 (id, 조회수, 한국어 제목) 목록으로 가져온다.

    한국어로 요청하면 조회수가 빠지고, 기본 언어로 요청하면 제목이 영어로 번역된다.
    그래서 두 번 읽어 합친다.
    """
    import yt_dlp

    url = f"https://www.youtube.com/{handle}/shorts"
    base = {"extract_flat": True, "quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(base) as ydl:
        views = {e["id"]: e.get("view_count") or 0 for e in ydl.extract_info(url, download=False)["entries"]}
    with yt_dlp.YoutubeDL({**base, **KOREAN}) as ydl:
        titles = {e["id"]: e.get("title") or "" for e in ydl.extract_info(url, download=False)["entries"]}
    return [(vid, n, titles.get(vid, "")) for vid, n in views.items()]


def video_meta(video_id, cookies=None):
    """영상 하나의 한국어 제목·길이·반응·설명란. 설명란은 대본 요약 역할을 한다."""
    import yt_dlp

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


def ytdlp_collect(handle, args):
    """숏츠 탭 목록을 받고, 상위·하위·키워드 영상만 상세를 받는다."""
    import yt_dlp

    rows = sorted(list_shorts(handle), key=lambda r: -r[1])
    views = {r[0]: r[1] for r in rows}
    pick = [r[0] for r in rows[: args.top]] + [r[0] for r in rows[-args.bottom :]]
    if args.match:
        pick += [r[0] for r in rows if re.search(args.match, r[2])]
    pick = list(dict.fromkeys(pick))

    metas, long_ids = [], set()
    for i, vid in enumerate(pick, 1):
        try:
            meta = video_meta(vid, args.cookies)
        except yt_dlp.utils.DownloadError as e:
            print(f"skip {vid}: {e}")
            continue
        # 한국어로 받으면 조회수가 빠지므로 목록의 값으로 채운다
        meta["view_count"] = meta["view_count"] or views[vid]
        # 봇 확인에 걸리면 길이가 비어 걸러낼 수 없다. 그런 영상은 숏츠 탭에 있었으니 남긴다
        if meta["duration"] and meta["duration"] > SHORTS_MAX:
            long_ids.add(vid)
        else:
            metas.append(meta)
        print(f"\r{i}/{len(pick)}", end="", flush=True)
    print()
    rows = [r for r in rows if r[0] not in long_ids]
    return rows, metas


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handle", help="채널 핸들, 예: @신비한_건축사전_1")
    ap.add_argument("--top", type=int, default=60, help="yt-dlp 방식에서 조회수 상위 몇 편의 상세를 받을지")
    ap.add_argument("--bottom", type=int, default=40, help="yt-dlp 방식에서 조회수 하위 몇 편의 상세를 받을지")
    ap.add_argument("--match", default="", help="yt-dlp 방식에서 제목이 이 정규식에 맞는 영상도 상세를 받는다")
    ap.add_argument("--cookies", help="yt-dlp 방식의 Netscape 형식 쿠키 파일 (봇 확인 우회)")
    ap.add_argument("--no-api", action="store_true", help="API 키가 있어도 yt-dlp 방식으로 받는다")
    args = ap.parse_args()
    handle = args.handle if args.handle.startswith("@") else "@" + args.handle

    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    metas = None
    if args.no_api:
        print("--no-api: yt-dlp 방식으로 받습니다")
    elif not key:
        print("YOUTUBE_API_KEY가 없어 yt-dlp 방식으로 받습니다")
    else:
        try:
            metas = api_collect(handle, key)
            source = "api"
        except ApiUnavailable as e:
            print(f"\nYouTube API {e}, yt-dlp 방식으로 전환합니다")

    if metas is not None:
        # API는 모든 숏츠의 상세를 받으므로 목록도 상세에서 만든다
        rows = [(m["id"], m["view_count"], m["title"]) for m in metas]
    else:
        rows, metas = ytdlp_collect(handle, args)
        source = "yt-dlp"
    rows.sort(key=lambda r: -r[1])

    DATA.mkdir(exist_ok=True)
    name = handle.lstrip("@")
    (DATA / f"{name}.list.json").write_text(json.dumps(rows, ensure_ascii=False))
    with open(DATA / f"{name}.jsonl", "w") as f:
        for m in metas:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    print(f"[{source}] {len(rows)}편 목록, {len(metas)}편 상세 → {DATA}/{name}.jsonl")


if __name__ == "__main__":
    main()
