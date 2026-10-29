"""Generate the ten original, quiet vertical MP4 clips for DopaGakiCheck.
No external footage, fonts or external imagery required at runtime.
Requires: pip install Pillow; ffmpeg on PATH.
"""

import math
import os
import random
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, SECONDS = 432, 768, 8, 18
N = FPS * SECONDS
OUT = Path(__file__).resolve().parents[1] / "app" / "src" / "main" / "res" / "raw"
OUT.mkdir(parents=True, exist_ok=True)
FONTPATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
if not os.path.exists(FONTPATH):
    FONTPATH = "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf"


def font(size):
    try:
        return ImageFont.truetype(FONTPATH, size)
    except:
        return ImageFont.load_default()


C = {
    "ink": "#23333B",
    "cream": "#F7F3E9",
    "gold": "#D6A554",
    "peach": "#D9A695",
    "blue": "#668DAD",
    "slate": "#687C88",
    "green": "#64846C",
    "brown": "#996F57",
    "red": "#B65C55",
    "yellow": "#D6BD72",
    "paper": "#EDE7DA",
}


def rnd(x):
    return int(round(x))


def blend(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def rect(d, xy, fill, r=0, outline=None, width=1):
    if r:
        d.rounded_rectangle(
            tuple(map(rnd, xy)), radius=r, fill=fill, outline=outline, width=width
        )
    else:
        d.rectangle(tuple(map(rnd, xy)), fill=fill, outline=outline, width=width)


def line(d, points, fill, width=3, joint="curve"):
    d.line([(rnd(x), rnd(y)) for x, y in points], fill=fill, width=width, joint=joint)


def ell(d, xy, fill, outline=None, width=1):
    d.ellipse(tuple(map(rnd, xy)), fill=fill, outline=outline, width=width)


def poly(d, pts, fill):
    d.polygon([tuple(map(rnd, p)) for p in pts], fill=fill)


def grain(img, seed=0):
    # Sparse dust, not enough to distract from visual recall.
    rng = random.Random(seed)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    o = ImageDraw.Draw(ov)
    for _ in range(160):
        x = rng.randrange(W)
        y = rng.randrange(H)
        o.point(
            (x, y), fill=(255, 255, 255, 15) if rng.random() > 0.5 else (10, 10, 20, 10)
        )
    img.alpha_composite(ov)


def canvas(bg_top, bg_bottom):
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    a = tuple(bytes.fromhex(bg_top.strip("#")))
    b = tuple(bytes.fromhex(bg_bottom.strip("#")))
    for y in range(H):
        d.line((0, y, W, y), fill=blend(a, b, y / (H - 1)) + (255,))
    return im


def backdrop(d, base="#DFD8CC", wall_y=590):
    rect(d, (0, wall_y, W, H), base)
    line(d, [(0, wall_y), (W, wall_y)], "#BEB3A7", 3)


def common_shadow(d, y, x1=70, x2=365):
    ell(d, (x1, y - 13, x2, y + 25), "#B9ADA0")


def scene_clock(t):
    im = canvas("#D8D4CC", "#B8B0A3")
    d = ImageDraw.Draw(im)
    rect(d, (0, 0, W, H), "#CEC6B9")
    # subtle wall joins and shelf
    line(d, [(24, 0), (24, 768)], "#C4BCB0", 2)
    line(d, [(0, 610), (W, 610)], "#AD9E8D", 3)
    ell(d, (67, 186, 366, 486), "#B5A89B")
    ell(d, (74, 174, 362, 462), "#EDE8DF", outline="#766D66", width=9)
    ell(d, (91, 191, 345, 445), "#F4F0E8", outline="#D9D1C5", width=2)
    cx, cy, r = 218, 318, 109
    for h in range(12):
        a = math.radians(h * 30 - 90)
        ax = cx + math.cos(a) * r
        ay = cy + math.sin(a) * r
        bx = cx + math.cos(a) * (r - 10)
        by = cy + math.sin(a) * (r - 10)
        line(d, [(ax, ay), (bx, by)], "#766D66", 3)

    # at 10:10
    def hand(deg, length, color, width):
        a = math.radians(deg - 90)
        line(
            d,
            [(cx, cy), (cx + math.cos(a) * length, cy + math.sin(a) * length)],
            color,
            width,
        )

    hand(305, 69, "#343C41", 9)
    hand(60, 97, "#343C41", 6)
    hand((t / 18 * 360), 101, "#AF6955", 2)
    ell(d, (211, 311, 225, 325), "#AD6D5D")
    rect(d, (48, 594, 381, 650), "#AE9D8B", 7)
    return im


def scene_mug(t):
    im = canvas("#E5DED3", "#D4CEC1")
    d = ImageDraw.Draw(im)
    rect(d, (0, 500, W, H), "#C8A486")
    line(d, [(0, 500), (W, 500)], "#B08D73", 4)
    for yy in (558, 680):
        line(d, [(0, yy), (W, yy)], "#C29A7E", 2)
    ell(d, (83, 506, 364, 554), "#AA927B")
    # cup handle
    ell(d, (275, 303, 376, 455), "#668DAD")
    ell(d, (299, 330, 355, 427), "#D8D3C9")
    rect(d, (120, 278, 309, 511), "#6C92B0", 24)
    ell(d, (120, 259, 308, 302), "#93AFC5")
    ell(d, (133, 265, 296, 294), "#6A4B34")
    ell(d, (143, 269, 286, 288), "#A37352")
    # tiny steam circles drift upwards
    for k in range(3):
        u = (t / 4 + k / 3) % 1
        x = 173 + k * 35 + 7 * math.sin(2 * t + k)
        y = 230 - 90 * u
        ell(d, (x, y, x + 8, y + 14), "#EAE4DB")
    return im


def scene_plant(t):
    im = canvas("#E4DDCE", "#D8D1C2")
    d = ImageDraw.Draw(im)
    rect(d, (0, 585, W, H), "#BCA995")
    # window and light
    rect(d, (51, 95, 382, 350), "#F0ECE2", 8)
    rect(d, (65, 109, 370, 335), "#AFC3C5", 5)
    rect(d, (208, 109, 220, 335), "#E2DBCB")
    rect(d, (65, 215, 370, 224), "#E2DBCB")
    poly(d, [(47, 585), (206, 585), (380, 768), (140, 768)], "#D6C4A7")
    common_shadow(d, 598, 90, 343)
    # plant body and exactly five distinct leaves
    cx = 216
    line(d, [(cx, 474), (cx, 280)], "#527258", 8)
    leaves = [
        (216, 338, 143, 289, -1),
        (216, 370, 293, 304, 1),
        (216, 303, 159, 226, -1),
        (216, 303, 292, 238, 1),
        (216, 271, 222, 198, 0),
    ]
    drift = math.sin(t * 0.65) * 4
    for i, (sx, sy, ex, ey, direction) in enumerate(leaves):
        ex += drift * (i % 2 * 2 - 1)
        line(d, [(sx, sy), (ex, ey)], "#51755D", 5)
        if direction == 0:
            ell(d, (ex - 24, ey - 50, ex + 24, ey + 14), "#779C6D")
        else:
            ell(d, (ex - 29, ey - 23, ex + 29, ey + 23), "#799B6A")
    # pot
    poly(d, [(146, 450), (293, 450), (277, 597), (163, 597)], "#B87459")
    rect(d, (139, 442, 301, 468), "#C98461", 5)
    line(d, [(170, 479), (168, 562)], "#D29C78", 4)
    return im


def scene_books(t):
    im = canvas("#D4CEC3", "#C1B5A5")
    d = ImageDraw.Draw(im)
    for yy in (270, 540):
        rect(d, (18, yy, 417, yy + 28), "#8C6D56", 5)
        rect(d, (18, yy + 25, 417, yy + 34), "#6D5447")
    # first shelf trinket
    ell(d, (30, 173, 110, 265), "#C6A978")
    rect(d, (142, 200, 260, 265), "#A8A195", 4)
    ell(d, (320, 206, 386, 265), "#779184")
    # right-hand shelf, last book red
    books = [
        (36, 390, 78, 540, "#7C91A1"),
        (85, 371, 128, 540, "#D2B57B"),
        (136, 398, 175, 540, "#88A184"),
        (184, 379, 234, 540, "#B7A295"),
        (243, 393, 284, 540, "#8F9DA9"),
        (295, 365, 351, 540, "#C06B61"),
    ]
    for i, (x1, y1, x2, y2, c) in enumerate(books):
        sway = math.sin(t * 0.3 + i) * 0.3
        rect(d, (x1 + sway, y1, x2 + sway, y2), c, 3)
        rect(d, (x1 + 6, y1 + 14, x2 - 6, y1 + 20), "#DCD3BD", 2)
        line(d, [(x1 + 10, y2 - 18), (x2 - 10, y2 - 18)], "#DDD1C1", 2)
    return im


def scene_bus(t):
    im = canvas("#C9D8D4", "#BFC4B9")
    d = ImageDraw.Draw(im)
    rect(d, (0, 515, W, 768), "#A2AAA5")
    rect(d, (0, 631, W, 768), "#6F8083")
    for x in range(-40, 550, 125):
        rect(d, (x, 690, x + 62, 697), "#E8DECE", 3)
    # little buildings
    for x, y, w, h, c in [
        (-30, 245, 131, 278, "#A4AAA0"),
        (75, 308, 123, 209, "#B9B8A9"),
        (290, 270, 150, 256, "#A6B2AE"),
    ]:
        rect(d, (x, y, x + w, 516), c, 4)
        for xx in range(x + 20, x + w - 9, 28):
            for yy in range(y + 35, 480, 65):
                rect(d, (xx, yy, xx + 13, yy + 25), "#DFDCD0", 2)
    # bus stop sign 2 and bench
    line(d, [(73, 200), (73, 605)], "#596C70", 8)
    ell(d, (42, 154, 104, 215), "#F1EBDB", outline="#5B7479", width=6)
    d.text((73, 172), "B", font=font(23), fill="#41616B", anchor="ma")
    rect(d, (16, 537, 142, 555), "#A58D78", 6)
    line(d, [(37, 548), (37, 613)], "#695D54", 5)
    line(d, [(121, 548), (121, 613)], "#695D54", 5)
    # moving bus, route number 7
    x = 275 - 52 * (t / 18)
    rect(d, (x, 394, x + 250, 607), "#C8B478", 20)
    rect(d, (x + 10, 426, x + 237, 525), "#6B8A94", 10)
    for q in range(4):
        rect(d, (x + 36 + q * 49, 432, x + 68 + q * 49, 505), "#A5BDC0", 3)
    rect(d, (x + 7, 530, x + 239, 575), "#D5C492", 6)
    rect(d, (x + 20, 400, x + 85, 437), "#273B43", 6)
    d.text((x + 52, 404), "7", font=font(31), fill="#F9F1DB", anchor="ma")
    for wc in (x + 54, x + 203):
        ell(d, (wc - 23, 582, wc + 23, 631), "#3A434A", outline="#AAB0AA", width=6)
    return im


def scene_laundry(t):
    im = canvas("#ADC5C6", "#E5DED0")
    d = ImageDraw.Draw(im)
    # sky garden
    rect(d, (0, 590, W, 768), "#B8AE9B")
    rect(d, (0, 536, W, 590), "#8EA99A")
    for x in (48, 127, 220, 325, 402):
        ell(d, (x - 48, 501, x + 54, 566), "#6D947E")
    # clothesline
    line(d, [(10, 254), (427, 265)], "#F0E8DC", 4)
    for i, (xx, color) in enumerate(
        [(90, "#F1E7D4"), (213, "#D6BA6F"), (337, "#7495B0")]
    ):
        sway = math.sin(t * 0.8 + i) * 3
        # shirts, 3 total
        pts = [
            (xx - 38 + sway, 290),
            (xx - 58 + sway, 323),
            (xx - 37 + sway, 340),
            (xx - 26 + sway, 330),
            (xx - 24 + sway, 420),
            (xx + 29 + sway, 420),
            (xx + 27 + sway, 329),
            (xx + 39 + sway, 342),
            (xx + 59 + sway, 324),
            (xx + 36 + sway, 291),
            (xx + 21 + sway, 299),
            (xx - 17 + sway, 299),
        ]
        poly(d, pts, color)
        line(d, [(xx - 16 + sway, 293), (xx + 17 + sway, 293)], "#8B8E85", 2)
        rect(d, (xx - 5, 265, xx + 7, 287), "#9D8163", 3)
    # two clips each shirt
    for x in (58, 120, 180, 243, 303, 369):
        rect(d, (x, 250, x + 8, 274), "#8D7A65", 3)
    return im


def scene_pencils(t):
    im = canvas("#E8E2D7", "#CFC7B9")
    d = ImageDraw.Draw(im)
    rect(d, (0, 531, W, H), "#BBAA98")
    line(d, [(0, 531), (W, 531)], "#AB9987", 4)
    # notepad
    poly(d, [(24, 547), (144, 550), (160, 728), (9, 708)], "#E6E2D9")
    for y in (583, 621, 659, 693):
        line(d, [(35, y), (131, y + 5)], "#B8C9CD", 2)
    common_shadow(d, 542, 160, 354)
    # three pencils in upright holder
    pencils = [
        (188, 315, -8, "#C05E4D"),
        (240, 280, 2, "#D5BB70"),
        (278, 332, 10, "#749E97"),
    ]
    for xx, tip, angle, color in pencils:
        line(d, [(xx, 505), (xx + angle, tip)], color, 17)
        line(d, [(xx + angle, tip), (xx + angle + 2, tip - 17)], "#D1B18E", 13)
        ell(d, (xx + angle - 3, tip - 26, xx + angle + 6, tip - 15), "#423D3A")
    poly(d, [(148, 455), (326, 455), (300, 600), (171, 600)], "#84959A")
    rect(d, (142, 453, 334, 479), "#A0ADB0", 9)
    line(d, [(172, 486), (183, 565)], "#B2C0C0", 5)
    return im


def scene_umbrella(t):
    im = canvas("#A9B8BE", "#84959F")
    d = ImageDraw.Draw(im)
    rect(d, (0, 464, W, 768), "#9A9EA2")
    rect(d, (0, 553, W, 768), "#5A6E7C")
    # urban windows
    rect(d, (0, 180, 173, 467), "#87959B")
    rect(d, (183, 236, 432, 460), "#7D9299")
    for x in (30, 93, 213, 288, 361):
        for y in (251, 335):
            rect(d, (x, y, x + 30, y + 43), "#BCC9CA", 4)
    for q in range(35):
        yy = 107 + q * 17
        xx = (q * 73 + int(t * 27)) % W
        line(d, [(xx, yy), (xx - 8, yy + 23)], "#D0DEE0", 2)
    # walking person with a red umbrella
    xx = 196 + 20 * math.sin(t * 0.15)
    ell(d, (xx - 18, 475, xx + 15, 516), "#D3B6A4")
    line(d, [(xx, 515), (xx, 595)], "#344A56", 22)
    line(d, [(xx, 586), (xx - 20, 635)], "#344A56", 9)
    line(d, [(xx, 586), (xx + 22, 636)], "#344A56", 9)
    line(d, [(xx, 530), (xx + 26, 557)], "#344A56", 9)
    line(d, [(xx, 530), (xx - 26, 562)], "#344A56", 9)
    line(d, [(xx, 426), (xx, 535)], "#7B5C4E", 4)
    poly(
        d,
        [
            (xx - 93, 432),
            (xx - 83, 404),
            (xx - 60, 384),
            (xx - 28, 370),
            (xx, 364),
            (xx + 29, 369),
            (xx + 63, 387),
            (xx + 89, 414),
            (xx + 94, 432),
        ],
        "#BA5D56",
    )
    line(d, [(xx - 93, 432), (xx + 94, 432)], "#8B4F4A", 3)
    return im


def scene_toast(t):
    im = canvas("#D7D1C5", "#BEB6AA")
    d = ImageDraw.Draw(im)
    rect(d, (0, 470, W, H), "#B5A08D")
    line(d, [(0, 470), (W, 470)], "#A5917E", 3)
    ell(d, (48, 425, 406, 718), "#A78E7C")
    ell(d, (54, 415, 398, 705), "#E9E4D9")
    ell(d, (78, 440, 373, 681), "#F6F2EA")

    # 2 bread slices, slightly overlapped but both exposed
    def bread(x, y, rot=0):
        poly(
            d,
            [
                (x + 3, y + 13),
                (x + 6, y + 104),
                (x + 115, y + 104),
                (x + 119, y + 15),
                (x + 95, y - 12),
                (x + 29, y - 12),
            ],
            "#B47B4B",
        )
        poly(
            d,
            [
                (x + 14, y + 14),
                (x + 16, y + 90),
                (x + 105, y + 90),
                (x + 108, y + 16),
                (x + 89, y + 0),
                (x + 35, y + 0),
            ],
            "#EAC691",
        )
        for b in range(7):
            xdot = x + 29 + (b * 17) % 72
            ydot = y + 29 + (b * 23) % 49
            ell(d, (xdot, ydot, xdot + 5, ydot + 5), "#D5A777")

    bread(113, 467)
    bread(192, 529)
    # butter dish in the top-right (clearly NOT a third toast)
    ell(d, (304, 453, 380, 500), "#CFD0C8")
    rect(d, (324, 459, 360, 482), "#E4D084", 5)
    return im


def scene_calendar(t):
    im = canvas("#D4D2CB", "#B9BBB2")
    d = ImageDraw.Draw(im)
    rect(d, (0, 555, W, H), "#B2A596")
    # hanging calendar and red circle around 14
    rect(d, (65, 172, 373, 581), "#A2A19A", 10)
    rect(d, (74, 164, 363, 565), "#F2EFE6", 8)
    rect(d, (74, 164, 363, 234), "#748F91", 8)
    d.text((219, 187), "OCTOBER", font=font(25), fill="#F8F4EB", anchor="ma")
    for i in range(7):
        xx = 91 + i * 37
        d.text((xx + 14, 246), "SMTWTFS"[i], font=font(12), fill="#87908D")
    for i in range(31):
        val = i + 1
        col = i % 7
        row = i // 7
        xx = 104 + col * 36
        yy = 297 + row * 46
        d.text((xx, yy), str(val), font=font(19), fill="#59636A", anchor="mm")
    # 14 = third? Calendar has sequential numbers 1..31; i=13, col6 row1
    x14 = 104 + ((14 - 1) % 7) * 36
    y14 = 297 + ((14 - 1) // 7) * 46
    ell(d, (x14 - 17, y14 - 21, x14 + 17, y14 + 19), None, outline="#B95D54", width=4)
    rect(d, (23, 610, 410, 637), "#A69A8C", 6)
    return im


SCENES = [
    scene_clock,
    scene_mug,
    scene_plant,
    scene_books,
    scene_bus,
    scene_laundry,
    scene_pencils,
    scene_umbrella,
    scene_toast,
    scene_calendar,
]


def main():
    for clip_idx, scene in enumerate(SCENES, 1):
        dest = OUT / f"clip{clip_idx:02d}.mp4"
        cmd = [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            f"{W}x{H}",
            "-pix_fmt",
            "rgb24",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "26",
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "baseline",
            "-level",
            "3.0",
            "-r",
            str(FPS),
            "-movflags",
            "+faststart",
            str(dest),
        ]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for frame in range(N):
                t = frame / FPS
                im = scene(t)
                if frame == 0:
                    grain(im, clip_idx)
                ff.stdin.write(im.convert("RGB").tobytes())
        except BrokenPipeError as exc:
            raise RuntimeError(f"ffmpeg failed: {dest}") from exc
        finally:
            ff.stdin.close()
        rc = ff.wait()
        if rc:
            raise RuntimeError(f"ffmpeg exited with {rc}")
        print(
            f"{clip_idx:02d}/10 {dest.name}: {dest.stat().st_size//1024} KiB",
            flush=True,
        )


if __name__ == "__main__":
    main()
