"""글꼴 → SVG path 변환 (harfbuzz로 커닝 적용)."""
import io
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen


class Font:
    def __init__(self, path, axes=None):
        tt = TTFont(path)
        if axes and "fvar" in tt:
            tt = instancer.instantiateVariableFont(tt, axes)
        buf = io.BytesIO()
        tt.save(buf)
        self.data = buf.getvalue()
        self.tt = TTFont(io.BytesIO(self.data))
        self.upem = self.tt["head"].unitsPerEm
        self.glyphset = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.hbfont = hb.Font(hb.Face(hb.Blob(self.data)))
        os2 = self.tt["OS/2"]
        self.cap = getattr(os2, "sCapHeight", 0) or self.upem * 0.7
        self.xh = getattr(os2, "sxHeight", 0) or self.upem * 0.5

    def shape(self, text, features=None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, features or {"kern": True, "liga": False})
        return buf.glyph_infos, buf.glyph_positions

    def path(self, text, size, x=0.0, y=0.0, tracking=0.0, by="em"):
        """size: by="em"이면 글꼴 크기, by="cap"이면 대문자 높이.
        tracking: em 단위 자간. 반환: (path d, 전체 폭)."""
        scale = size / (self.cap if by == "cap" else self.upem)
        infos, poss = self.shape(text)
        pen = SVGPathPen(self.glyphset, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        cx = x
        n = len(infos)
        for i, (info, pos) in enumerate(zip(infos, poss)):
            name = self.order[info.codepoint]
            gx = cx + pos.x_offset * scale
            gy = y - pos.y_offset * scale
            tp = TransformPen(pen, (scale, 0, 0, -scale, gx, gy))
            self.glyphset[name].draw(tp)
            cx += pos.x_advance * scale
            if i < n - 1:
                cx += tracking * self.upem * scale
        return pen.getCommands(), cx - x

    def width(self, text, size, tracking=0.0, by="em"):
        return self.path(text, size, tracking=tracking, by=by)[1]

    def bounds(self, text, size, by="em"):
        """잉크 영역 (xmin, ymin, xmax, ymax), baseline y=0 기준(아래가 +)."""
        from fontTools.pens.boundsPen import BoundsPen
        scale = size / (self.cap if by == "cap" else self.upem)
        infos, poss = self.shape(text)
        bp = BoundsPen(self.glyphset)
        cx = 0
        for info, pos in zip(infos, poss):
            tp = TransformPen(bp, (scale, 0, 0, -scale, cx + pos.x_offset * scale, -pos.y_offset * scale))
            self.glyphset[self.order[info.codepoint]].draw(tp)
            cx += pos.x_advance * scale
        return bp.bounds
