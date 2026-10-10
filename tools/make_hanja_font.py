"""PDF 사주 표용 한자 글꼴 생성기.

Noto Serif CJK KR (SemiBold, SIL OFL)에서 천간 10자 + 지지 12자 + 오행 5자 + 陰陽만
뽑아 작은 TrueType 파일(fonts/NotoSerifKR-Hanja-SemiBold.ttf)로 만든다.
reportlab TTFont는 TrueType(glyf) 윤곽선만 지원하므로 CFF → TrueType 변환을 포함한다.

사용: python3 tools/make_hanja_font.py [원본.ttc] [출력.ttf]
"""
import sys
from fontTools.ttLib import TTCollection, TTFont, newTable
from fontTools import subset
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

SRC = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc"
OUT = sys.argv[2] if len(sys.argv) > 2 else "fonts/NotoSerifKR-Hanja-SemiBold.ttf"
CHARS = "甲乙丙丁戊己庚辛壬癸" "子丑寅卯辰巳午未申酉戌亥" "木火土金水" "陰陽" " "

coll = TTCollection(SRC)
font = next(f for f in coll.fonts if f["name"].getDebugName(1).startswith("Noto Serif CJK KR"))

opts = subset.Options()
opts.layout_features = []
opts.name_IDs = [0, 1, 2, 3, 4, 5, 6]
opts.notdef_outline = True
opts.hinting = False
ss = subset.Subsetter(opts)
ss.populate(text=CHARS)
ss.subset(font)

# CFF -> TrueType 윤곽선
gs = font.getGlyphSet()
order = font.getGlyphOrder()
glyf = newTable("glyf"); glyf.glyphOrder = order; glyf.glyphs = {}
for name in order:
    pen = TTGlyphPen(gs)
    gs[name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
    glyf.glyphs[name] = pen.glyph()
font["glyf"] = glyf
font["loca"] = newTable("loca")
maxp = font["maxp"]; maxp.tableVersion = 0x00010000
for a in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
          "maxStackElements", "maxSizeOfInstructions", "maxComponentElements"):
    setattr(maxp, a, 0)
maxp.maxZones = 1
for a in ("maxPoints", "maxContours", "maxCompositePoints", "maxCompositeContours", "maxComponentDepth"):
    setattr(maxp, a, 0)
del font["CFF "]
if "VORG" in font: del font["VORG"]
font.sfntVersion = "\x00\x01\x00\x00"
font["head"].glyphDataFormat = 0
font["post"].formatType = 2.0
font["post"].extraNames = []; font["post"].mapping = {}
font.save(OUT)

chk = TTFont(OUT)
cmap = chk.getBestCmap()
missing = [c for c in CHARS if ord(c) not in cmap]
print("saved", OUT, "glyphs", len(chk.getGlyphOrder()), "missing", missing)
