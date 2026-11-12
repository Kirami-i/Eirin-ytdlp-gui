"""Рисует assets/icon.ico для приложения (нужен Pillow)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 256
RADIUS = 58
TOP = (124, 92, 255)
BOTTOM = (74, 45, 209)
WHITE = (255, 255, 255, 245)
WHITE_DIM = (255, 255, 255, 165)


def make_icon() -> Image.Image:
    gradient = Image.new("RGBA", (SIZE, SIZE))
    draw = ImageDraw.Draw(gradient)
    for y in range(SIZE):
        t = y / (SIZE - 1)
        color = tuple(int(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
        draw.line([(0, y), (SIZE, y)], fill=(*color, 255))

    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=RADIUS, fill=255)

    icon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    icon.paste(gradient, (0, 0), mask)

    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle([112, 52, 144, 132], radius=10, fill=WHITE)
    draw.polygon([(78, 122), (178, 122), (128, 190)], fill=WHITE)
    draw.rounded_rectangle([74, 206, 182, 222], radius=8, fill=WHITE_DIM)
    return icon


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    icon = make_icon()
    icon.save(assets / "icon.png", "PNG")
    icon.save(
        assets / "icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"saved {assets / 'icon.ico'}")


if __name__ == "__main__":
    main()
