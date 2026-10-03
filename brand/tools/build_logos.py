#!/usr/bin/env python3
"""노빠꾸컴퍼니 BI 로고 SVG 생성기.

    pip install fonttools uharfbuzz brotli
    python3 brand/tools/build_logos.py

글꼴은 처음 실행할 때 brand/tools/.cache/ 에 내려받습니다.
글자는 모두 path(아웃라인)로 바꿔서 저장하므로 SVG를 열 때 글꼴이 필요 없습니다.
"""
import math
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from textpath import Font  # noqa: E402

OUT = os.path.join(HERE, "..", "logo")
CACHE = os.path.join(HERE, ".cache")

FONT_URLS = {
    "Archivo-VF.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/archivo/Archivo%5Bwdth,wght%5D.ttf",
    "JetBrainsMono-VF.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
    "Pretendard-Black.otf": "https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/public/static/Pretendard-Black.otf",
}

# ── 컬러 (BRAND.md 4장) ─────────────────────────────────────────
BLUE = "#1857A5"      # Nobbakku Blue (메인)
RED = "#E83E30"       # Nobbakku Red (포인트)
INK = "#111B2E"       # 글자
SUB = "#5A6577"       # 보조 글자
WHITE = "#FFFFFF"

# ── 심볼 설계값 (100 × 100 그리드) ─────────────────────────────
LEAN = 10            # 앞으로 기울기(°)
TILE_R = 20          # 타일 모서리
S = 18               # 기본 획 굵기 s
STEM_X = 20          # 세로 획 왼쪽
ARM_Y = 60           # 가로 획 중심선
HEAD_X = 56          # 화살촉 뒷변
TIP_X = 86           # 화살촉 끝
HEAD_H = 54          # 화살촉 높이 = 3s
BLOCKS = [(13, 20), (25, 34)]   # 데이터 블록 (위 → 아래로 점점 커짐)
STEM_TOP = 39        # 꽉 찬 세로 획이 시작되는 곳


def _skew(x, y, cy=50.0):
    return x - (y - cy) * math.tan(math.radians(LEAN)), y


def _num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _poly(pts):
    pts = [_skew(x, y) for x, y in pts]
    return "M" + "L".join(f"{_num(x)} {_num(y)}" for x, y in pts) + "Z"


def mark_parts():
    """ㄴ 애로우를 [맨 위 데이터 블록, 나머지]로 나눠 돌려준다. 맨 위 블록은 레드 포인트 자리."""
    p = mark_path()
    cut = p.index("Z") + 1
    return p[:cut], p[cut:]


def mark_path():
    """ㄴ 애로우: 데이터 블록 → 꺾이는 파이프 → 화살촉. 10° 앞으로 기울어 있다."""
    a, b = ARM_Y - S / 2, ARM_Y + S / 2
    parts = [_poly([(STEM_X, y0), (STEM_X + S, y0), (STEM_X + S, y1), (STEM_X, y1)]) for y0, y1 in BLOCKS]
    parts.append(_poly([
        (STEM_X, STEM_TOP), (STEM_X + S, STEM_TOP), (STEM_X + S, a), (HEAD_X, a),
        (HEAD_X, ARM_Y - HEAD_H / 2), (TIP_X, ARM_Y), (HEAD_X, ARM_Y + HEAD_H / 2),
        (HEAD_X, b), (STEM_X, b),
    ]))
    return "".join(parts)


def tile_path(r=TILE_R, w=100):
    return (f"M{r} 0H{w - r}A{r} {r} 0 0 1 {w} {r}V{w - r}A{r} {r} 0 0 1 {w - r} {w}"
            f"H{r}A{r} {r} 0 0 1 0 {w - r}V{r}A{r} {r} 0 0 1 {r} 0Z")


def symbol(tile, mark, knockout=False, accent=RED):
    """knockout=True면 화살표를 뚫어서 한 가지 색으로만 그린다 (단색 인쇄용).
    accent: 맨 위 데이터 블록 색 (데이터가 들어오는 시작점)."""
    if knockout:
        return f'<path fill="{tile}" fill-rule="evenodd" d="{tile_path()}{mark_path()}"/>'
    first, rest = mark_parts()
    return (f'<path fill="{tile}" d="{tile_path()}"/><path fill="{mark}" d="{rest}"/>'
            f'<path fill="{accent}" d="{first}"/>')


def svg(w, h, body, label="노빠꾸컴퍼니"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" role="img" '
            f'aria-label="{label}"><title>{label}</title>{body}</svg>\n')


def font_file(name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print("download", name)
        urllib.request.urlretrieve(FONT_URLS[name], path)
    return path


def main():
    display = Font(font_file("Archivo-VF.ttf"), {"wght": 800, "wdth": 115})
    mono = Font(font_file("JetBrainsMono-VF.ttf"), {"wght": 700})
    kr = Font(font_file("Pretendard-Black.otf"))

    # 영문 워드마크: NOBBAKKU (Archivo ExtraBold Expanded) + COMPANY (JetBrains Mono)
    # 정렬: 글자 묶음의 위아래 = 화살표의 위아래 (첫 데이터 블록 13 ~ 화살촉 끝 87)
    GAP = 30                       # 심볼과 글자 사이
    X0 = 100 + GAP
    top, bottom = BLOCKS[0][0], ARM_Y + HEAD_H / 2
    NAME_CAP, CO_CAP = 48, 12
    name_d, name_w = display.path("NOBBAKKU", NAME_CAP, x=X0, y=top + NAME_CAP, tracking=-0.005, by="cap")
    co_d, co_w = mono.path("COMPANY", CO_CAP, x=X0 + 2, y=bottom, tracking=0.45, by="cap")
    W_H = math.ceil(X0 + name_w + 2)

    # 국문 워드마크: 노빠꾸 + 컴퍼니 (Pretendard Black), 잉크 높이를 심볼 가운데에 맞춘다
    ksize = 66
    kb = kr.bounds("노빠꾸컴퍼니", ksize)
    ky = 50 - (kb[1] + kb[3]) / 2
    k1_d, k1_w = kr.path("노빠꾸", ksize, x=X0, y=ky, tracking=-0.02, by="em")
    k2_d, k2_w = kr.path("컴퍼니", ksize, x=X0 + k1_w + 2, y=ky, tracking=-0.02, by="em")
    W_K = math.ceil(X0 + k1_w + 2 + k2_w + 2)

    # 세로형: 심볼 위, 글자 아래 가운데
    sn_d, sn_w = display.path("NOBBAKKU", 30, x=0, y=0, tracking=-0.005, by="cap")
    st_w = math.ceil(max(sn_w, 100) + 4)
    cx = st_w / 2
    sn_d, _ = display.path("NOBBAKKU", 30, x=cx - sn_w / 2, y=164, tracking=-0.005, by="cap")
    sc_d, sc_w = mono.path("COMPANY", 9, x=0, y=0, tracking=0.42, by="cap")
    sc_d, _ = mono.path("COMPANY", 9, x=cx - sc_w / 2, y=186, tracking=0.42, by="cap")
    ST_H = 190

    def horiz(tile, mark, text, sub, knockout=False):
        return svg(W_H, 100, symbol(tile, mark, knockout)
                   + f'<path fill="{text}" d="{name_d}"/><path fill="{sub}" d="{co_d}"/>',
                   "NOBBAKKU COMPANY 노빠꾸컴퍼니")

    def stacked(tile, mark, text, sub):
        sym = f'<g transform="translate({cx - 50:.2f} 0)">{symbol(tile, mark)}</g>'
        return svg(st_w, ST_H, sym + f'<path fill="{text}" d="{sn_d}"/><path fill="{sub}" d="{sc_d}"/>',
                   "NOBBAKKU COMPANY 노빠꾸컴퍼니")

    def korean(tile, mark, t1, t2):
        return svg(W_K, 100, symbol(tile, mark) + f'<path fill="{t1}" d="{k1_d}"/><path fill="{t2}" d="{k2_d}"/>')

    # 링크 공유 미리보기 (1200 × 630): 가로형 로고 + 슬로건 + 큰 ㄴ 애로우
    logo = horiz(BLUE, WHITE, BLUE, RED)
    logo_body = logo[logo.index("</title>") + 8:logo.rindex("</svg>")]
    h1_d, h1_w = kr.path("개발에", 116, x=80, y=356, tracking=-0.04)
    h2a_d, h2a_w = kr.path("실패는 ", 116, x=80, y=492, tracking=-0.04)
    h2b_d, _ = kr.path("없다.", 116, x=80 + h2a_w, y=492, tracking=-0.04)
    og_label_d, _ = mono.path("FROM DATA TO IT SOLUTIONS", 15, x=82, y=566, tracking=0.12, by="cap")
    og = svg(1200, 630,
             f'<rect width="1200" height="630" fill="{WHITE}"/>'
             f'<g transform="translate(80 64) scale(.6)">{logo_body}</g>'
             f'<path fill="{INK}" d="{h1_d}{h2a_d}"/><path fill="{BLUE}" d="{h2b_d}"/>'
             f'<path fill="{SUB}" d="{og_label_d}"/>'
             f'<g transform="translate(700 118) scale(5.1)"><path fill="{BLUE}" d="{mark_parts()[1]}"/>'
             f'<path fill="{RED}" d="{mark_parts()[0]}"/></g>',
             "노빠꾸컴퍼니 — 개발에 실패는 없다.")
    with open(os.path.join(OUT, "..", "og-image.svg"), "w", encoding="utf-8") as f:
        f.write(og)

    files = {
        # 심볼
        # 심볼: 블루 타일 + 흰 화살표 + 레드 블록. 밝은 바탕 · 어두운 바탕 모두에 쓴다
        "symbol.svg": svg(100, 100, symbol(BLUE, WHITE)),
        "symbol-square.svg": svg(100, 100, f'<path fill="{BLUE}" d="M0 0H100V100H0Z"/>'
                                 f'<path fill="{WHITE}" d="{mark_parts()[1]}"/><path fill="{RED}" d="{mark_parts()[0]}"/>'),
        "symbol-inverse.svg": svg(100, 100, symbol(WHITE, BLUE)),
        "symbol-mono-dark.svg": svg(100, 100, symbol(INK, None, knockout=True)),
        "symbol-mono-light.svg": svg(100, 100, symbol(WHITE, None, knockout=True)),
        # 가로형
        "logo-horizontal-on-light.svg": horiz(BLUE, WHITE, BLUE, RED),
        "logo-horizontal-on-dark.svg": horiz(BLUE, WHITE, WHITE, RED),
        "logo-horizontal-mono-dark.svg": horiz(INK, None, INK, INK, knockout=True),
        "logo-horizontal-mono-light.svg": horiz(WHITE, None, WHITE, WHITE, knockout=True),
        # 세로형
        "logo-stacked-on-light.svg": stacked(BLUE, WHITE, BLUE, RED),
        "logo-stacked-on-dark.svg": stacked(BLUE, WHITE, WHITE, RED),
        # 국문
        "logo-kr-on-light.svg": korean(BLUE, WHITE, BLUE, BLUE),
        "logo-kr-on-dark.svg": korean(BLUE, WHITE, WHITE, WHITE),
    }
    os.makedirs(OUT, exist_ok=True)
    for name, content in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"{name:34s} {len(content):6d} bytes")


if __name__ == "__main__":
    main()
