"""Placeholder paper assets for the draft (until the Gemini images arrive).
Each one is drawn on white, then goes through E.cutout() so it gets the same cream torn border."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import basira_engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi.ttf"))
RAW = os.path.join(E.ROOT, "raw"); os.makedirs(RAW, exist_ok=True)
OR = (226, 110, 52); NV = (22, 30, 48); WHITE = (255, 255, 255)


def font(size):
    f = ImageFont.truetype(E.FONT, size)
    f.set_variation_by_name("Bold")
    return f


def man(path, angry=False):
    im = Image.new("RGB", (640, 1520), WHITE); d = ImageDraw.Draw(im)
    o = dict(fill=OR, outline=NV, width=6)
    # legs + shoes
    d.polygon([(232, 820), (318, 820), (312, 1400), (246, 1400)], **o)
    d.polygon([(312, 820), (400, 820), (394, 1400), (326, 1400)], **o)
    d.polygon([(240, 1392), (318, 1392), (330, 1450), (226, 1450)], fill=NV)
    d.polygon([(322, 1392), (398, 1392), (440, 1450), (316, 1450)], fill=NV)
    # jacket (three-piece suit), shoulders dropped
    d.polygon([(214, 420), (408, 420), (432, 870), (196, 870)], **o)
    d.line([(318, 430), (300, 610), (318, 860)], fill=NV, width=5)       # front edge
    d.line([(318, 430), (352, 560)], fill=NV, width=5)                   # lapel
    d.line([(214, 640), (420, 640)], fill=NV, width=4)                   # pocket line
    for y in (680, 740): d.ellipse((322, y, 334, y + 12), fill=NV)       # buttons
    # arm, hand in pocket
    d.polygon([(370, 440), (420, 450), (426, 690), (380, 700)], **o)
    # tie + neck
    d.polygon([(284, 372), (326, 372), (330, 430), (280, 430)], **o)
    d.polygon([(310, 432), (326, 432), (332, 560), (316, 580), (302, 560)], fill=NV)
    # head (side profile facing right)
    d.ellipse((216, 178, 392, 384), **o)
    d.polygon([(388, 270), (424, 312), (386, 322)], **o)                 # nose
    d.ellipse((350, 248, 364, 262), fill=NV)                             # eye
    if angry:
        d.line([(336, 238), (372, 250)], fill=NV, width=7)              # brow down
        d.line([(356, 344), (384, 338)], fill=NV, width=5)              # flat mouth
    else:
        d.arc((346, 320, 384, 350), 20, 150, fill=NV, width=5)
    d.ellipse((250, 268, 284, 310), outline=NV, width=5)                 # ear
    # fedora
    d.ellipse((168, 178, 448, 222), **o)
    d.rounded_rectangle((214, 92, 394, 200), 28, **o)
    d.rectangle((214, 162, 394, 190), fill=NV)
    d.line([(304, 96), (304, 130)], fill=NV, width=5)                    # pinch
    im.save(path)


def cop(path):
    im = Image.new("RGB", (640, 1520), WHITE); d = ImageDraw.Draw(im)
    o = dict(fill=OR, outline=NV, width=6)
    d.polygon([(240, 1000), (320, 1000), (316, 1400), (248, 1400)], **o)
    d.polygon([(318, 1000), (400, 1000), (396, 1400), (326, 1400)], **o)
    d.polygon([(236, 1392), (318, 1392), (330, 1450), (222, 1450)], fill=NV)
    d.polygon([(322, 1392), (398, 1392), (444, 1450), (316, 1450)], fill=NV)
    d.polygon([(206, 420), (414, 420), (446, 1050), (184, 1050)], **o)  # long coat
    d.line([(328, 430), (336, 1040)], fill=NV, width=5)
    for y in range(500, 1000, 90): d.ellipse((344, y, 360, y + 16), fill=NV)
    d.line([(200, 760), (428, 760)], fill=NV, width=10)                  # belt
    d.polygon([(360, 440), (412, 440), (520, 640), (480, 680)], **o)    # arm reaching forward
    d.ellipse((488, 630, 548, 690), **o)                                 # hand
    d.polygon([(372, 540), (396, 560), (380, 600), (356, 580)], fill=NV) # badge
    d.ellipse((222, 196, 392, 392), **o)
    d.polygon([(388, 282), (422, 322), (386, 330)], **o)
    d.ellipse((350, 262, 364, 276), fill=NV)
    d.line([(352, 352), (382, 346)], fill=NV, width=5)
    d.ellipse((252, 276, 284, 316), outline=NV, width=5)
    # round police cap with visor
    d.chord((212, 120, 400, 300), 180, 360, **o)
    d.rectangle((212, 196, 400, 222), fill=NV)
    d.polygon([(380, 206), (452, 214), (450, 228), (380, 226)], fill=NV)
    d.ellipse((296, 150, 316, 170), fill=NV)
    im.save(path)


def barrel(path):
    im = Image.new("RGB", (520, 700), WHITE); d = ImageDraw.Draw(im)
    wood = (150, 92, 50)
    d.rounded_rectangle((70, 60, 450, 640), 120, fill=wood, outline=NV, width=7)
    for x in (150, 260, 370): d.line([(x, 80), (x, 620)], fill=(110, 66, 36), width=5)
    for y in (150, 350, 550): d.rectangle((66, y, 454, y + 30), fill=(60, 64, 74), outline=NV, width=4)
    d.ellipse((150, 20, 370, 100), fill=(90, 54, 30), outline=NV, width=7)   # open top
    im.save(path)


def chain_lock(path):
    im = Image.new("RGB", (900, 900), WHITE); d = ImageDraw.Draw(im)
    iron, dark = (98, 104, 116), (60, 64, 74)
    for sgn in (1, -1):
        for i in range(13):
            u = i / 12; x = 90 + u * 720; y = 450 + sgn * (u - 0.5) * 720
            ang = math.atan2(sgn * 720, 720)
            w, h = (70, 38) if i % 2 else (38, 30)
            link = Image.new("RGBA", (220, 220), (0, 0, 0, 0)); ld = ImageDraw.Draw(link)
            ld.ellipse((110 - w, 110 - h, 110 + w, 110 + h), fill=(34, 40, 56, 255), outline=NV + (255,), width=26)
            ld.ellipse((110 - w + 6, 110 - h + 6, 110 + w - 6, 110 + h - 6), outline=iron + (255,), width=12)
            link = link.rotate(-math.degrees(ang), resample=Image.BICUBIC)
            im.paste(link, (int(x - 110), int(y - 110)), link)
    # padlock in the middle
    d.pieslice((388, 318, 512, 462), 180, 360, fill=(34, 40, 56))
    d.arc((370, 300, 530, 480), 180, 360, fill=NV, width=34)
    d.arc((370, 300, 530, 480), 180, 360, fill=iron, width=18)
    d.line([(378, 390), (378, 440)], fill=NV, width=34); d.line([(522, 390), (522, 440)], fill=NV, width=34)
    d.rounded_rectangle((330, 420, 570, 640), 26, fill=(176, 140, 70), outline=NV, width=8)
    d.ellipse((432, 488, 468, 524), fill=NV); d.polygon([(440, 510), (460, 510), (466, 580), (434, 580)], fill=NV)
    im.save(path)


def calendar(path, year="1920"):
    im = Image.new("RGB", (660, 760), WHITE); d = ImageDraw.Draw(im)
    d.rectangle((40, 60, 620, 720), fill=E.CREAM, outline=NV, width=6)
    d.rectangle((40, 60, 620, 210), fill=E.BRICK, outline=NV, width=6)
    for x in (170, 490):
        d.rounded_rectangle((x - 16, 20, x + 16, 110), 14, fill=(60, 64, 74), outline=NV, width=4)
    f = font(230)
    tw = d.textlength(year, font=f)
    d.text(((660 - tw) / 2, 290), year, font=f, fill=NV)
    for y in (650, 680): d.line([(110, y), (550, y)], fill=(200, 188, 168), width=4)
    im.save(path)


def street(path, lit):
    """1920s street at night, flat cut-paper look (placeholder for the Gemini background)."""
    w, h = 1240, 2200
    im = Image.new("RGB", (w, h), (20, 28, 46)); d = ImageDraw.Draw(im)
    r = np.random.default_rng(5)
    for i in range(70):                                                 # stars / haze
        x, y = r.uniform(0, w), r.uniform(0, 700); d.ellipse((x, y, x + 4, y + 4), fill=(70, 80, 104))
    d.ellipse((860, 180, 1010, 330), fill=(226, 214, 180))               # moon
    brick, brick2 = (112, 52, 40), (92, 42, 34)
    # left & right buildings, saloon in the middle
    d.polygon([(0, 380), (330, 470), (330, 1580), (0, 1580)], fill=brick2)
    d.polygon([(910, 470), (w, 340), (w, 1580), (910, 1580)], fill=brick2)
    d.rectangle((300, 620, 940, 1580), fill=brick)
    for y in range(640, 1580, 44):                                       # brick courses
        d.line([(300, y), (940, y)], fill=(96, 44, 34), width=3)
    win = (236, 184, 96) if lit else (34, 40, 58)
    for x in (360, 780):
        for y in (700, 900):
            d.rectangle((x, y, x + 100, y + 140), fill=win, outline=(40, 22, 20), width=8)
            d.line([(x + 50, y), (x + 50, y + 140)], fill=(40, 22, 20), width=6)
    for x in (40, 160, 1010, 1120):
        for y in (600, 820, 1040, 1260):
            d.rectangle((x, y, x + 70, y + 110), fill=(30, 36, 54), outline=(30, 16, 14), width=6)
    d.rectangle((420, 1040, 820, 1120), fill=(40, 30, 28), outline=(24, 16, 14), width=6)   # empty sign board
    # doorway (the door itself is drawn per frame)
    d.rectangle((500, 1170, 740, 1580), fill=(236, 184, 96) if lit else (14, 18, 30))
    d.rectangle((486, 1156, 754, 1580), outline=(40, 22, 20), width=16)
    # street lamp
    d.rectangle((1046, 1000, 1062, 1640), fill=(26, 30, 40))
    d.polygon([(1010, 960), (1098, 960), (1080, 1020), (1028, 1020)], fill=(26, 30, 40))
    d.ellipse((1030, 1018, 1078, 1050), fill=(250, 214, 140))
    # sidewalk + wet cobblestones
    d.rectangle((0, 1580, w, 1660), fill=(70, 72, 82))
    d.rectangle((0, 1660, w, h), fill=(38, 44, 60))
    for row in range(14):
        y = 1680 + row * 38; off = (row % 2) * 40
        for x in range(-40 + off, w, 80):
            d.rounded_rectangle((x, y, x + 70, y + 30), 10, fill=(48, 56, 74))
    im.save(path)


if __name__ == "__main__":
    man(os.path.join(RAW, "man.png"))
    man(os.path.join(RAW, "man_angry.png"), angry=True)
    cop(os.path.join(RAW, "cop.png"))
    barrel(os.path.join(RAW, "barrel.png"))
    chain_lock(os.path.join(RAW, "chain.png"))
    calendar(os.path.join(RAW, "calendar.png"))
    for k in ("man", "man_angry", "cop", "barrel", "calendar"):
        E.cutout(k, os.path.join(RAW, k + ".png"))
    E.cutout("chain", os.path.join(RAW, "chain.png"), border=8, min_hole=10 ** 9)
    street(os.path.join(E.ROOT, "bg", "street_lit.png"), True)
    street(os.path.join(E.ROOT, "bg", "street_dark.png"), False)
    # contact sheet on navy
    names = ["man", "man_angry", "cop", "barrel", "chain", "calendar"]
    sheet = Image.new("RGBA", (1800, 700), E.NAVY + (255,))
    for i, n in enumerate(names):
        E.paste(sheet, E.scaled(n, 600), 150 + i * 300, 350)
    sheet.convert("RGB").save(os.path.join(E.ROOT, "assets_sheet.png"))
    print("ok")
