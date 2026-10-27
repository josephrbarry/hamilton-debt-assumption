"""
Draw the schedule-letter tiles (A-H) that sit beside the RB monogram in each
page's header band: a gold Georgia Bold letter, centred on its ink, on a
transparent square the same size as the monogram.

    python src/make_schedule_tiles.py      (writes powerbi/assets/schedule_A.png ...)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "powerbi" / "assets"
GOLD = "#C9B77A"                       # same antique gold as the monogram
FONT = Path("C:/Windows/Fonts/georgiab.ttf")
SIZE = 336                             # 4x the 84 px display size, for crisp scaling
LETTERS = "ABCDEFGH"


def tile(letter: str) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(FONT), int(SIZE * 0.70))
    x0, y0, x1, y1 = d.textbbox((0, 0), letter, font=font)
    d.text(((SIZE - (x1 - x0)) / 2 - x0, (SIZE - (y1 - y0)) / 2 - y0), letter, font=font, fill=GOLD)
    return img


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for letter in LETTERS:
        tile(letter).save(ASSETS / f"schedule_{letter}.png")
    print(f"Wrote {len(LETTERS)} tiles to {ASSETS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
