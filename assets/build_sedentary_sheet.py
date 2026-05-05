from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
SPRITE_SHEET_PATH = ROOT / "anya_sprite_sheet.png"
CUTOUT_PATH = ROOT / "anya_cutout.png"
OUTPUT_PATH = ROOT / "anya_sedentary_sheet.png"

FRAME_W = 310
FRAME_H = 430
FRAME_COUNT = 7
CANVAS_W = FRAME_W * FRAME_COUNT
CANVAS_H = FRAME_H


@dataclass(frozen=True)
class Stage:
    kind: str
    sprite_index: int | None
    scale: float
    rotation: float
    x: int
    y: int
    chair_x: int
    chair_y: int
    chair_scale: float
    chair_front: bool
    motion: bool = False
    rays: int = 0
    sparkles: int = 0


STAGES = [
    Stage("cutout", None, 0.215, 7, 62, 108, 104, 210, 0.98, True),
    Stage("cutout", None, 0.225, 4, 78, 92, 114, 208, 0.95, True, motion=True),
    Stage("sprite", 0, 0.385, 1, 104, 70, 134, 216, 0.88, True, motion=True),
    Stage("sprite", 1, 0.392, 0, 110, 38, 164, 226, 0.80, False),
    Stage("sprite", 2, 0.392, -2, 102, 30, 190, 232, 0.74, False, rays=4, sparkles=1),
    Stage("sprite", 3, 0.398, -1, 92, 22, 208, 236, 0.70, False, rays=6, sparkles=2),
    Stage("sprite", 4, 0.404, 2, 82, 16, 226, 242, 0.67, False, rays=8, sparkles=3),
]


def crop_alpha(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    return image.crop(bbox) if bbox else image


def load_cutout() -> Image.Image:
    return crop_alpha(Image.open(CUTOUT_PATH).convert("RGBA"))


def load_sprite_variants() -> list[Image.Image]:
    sheet = Image.open(SPRITE_SHEET_PATH).convert("RGBA")
    width, height = sheet.size
    variants: list[Image.Image] = []
    for index in range(5):
        left = round(index * width / 5)
        right = round((index + 1) * width / 5)
        variants.append(crop_alpha(sheet.crop((left, 0, right, height))))
    return variants


def transform_subject(subject: Image.Image, stage: Stage) -> Image.Image:
    width = max(1, round(subject.width * stage.scale))
    height = max(1, round(subject.height * stage.scale))
    transformed = subject.resize((width, height), Image.Resampling.LANCZOS)
    if stage.rotation:
        transformed = transformed.rotate(
            stage.rotation,
            expand=True,
            resample=Image.Resampling.BICUBIC,
        )
    return transformed


def draw_shadow(panel: Image.Image, x: int, y: int, w: int, h: int, alpha: int, blur: int) -> None:
    shadow = Image.new("RGBA", panel.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.ellipse((x, y, x + w, y + h), fill=(84, 49, 65, alpha))
    panel.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=blur)))


def draw_chair_back(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float) -> None:
    w = round(122 * scale)
    h = round(118 * scale)
    x0 = cx - w // 2
    y0 = cy - h
    draw.rounded_rectangle(
        (x0 - 8, y0 + 8, x0 + w + 8, y0 + h + 10),
        radius=34,
        fill=(239, 213, 224, 205),
        outline=(120, 88, 108, 255),
        width=3,
    )
    draw.rounded_rectangle(
        (x0, y0, x0 + w, y0 + h),
        radius=28,
        fill=(255, 233, 241, 242),
        outline=(120, 88, 108, 215),
        width=2,
    )
    draw.ellipse((x0 + 22, y0 + 20, x0 + 46, y0 + 44), fill=(255, 247, 250, 130))


def draw_chair_front(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float) -> None:
    seat_w = round(130 * scale)
    seat_h = round(42 * scale)
    stem_h = round(88 * scale)
    x0 = cx - seat_w // 2
    y0 = cy
    draw.rounded_rectangle(
        (x0, y0, x0 + seat_w, y0 + seat_h),
        radius=22,
        fill=(255, 223, 236, 250),
        outline=(120, 88, 108, 255),
        width=3,
    )
    draw.rounded_rectangle(
        (x0 + round(24 * scale), y0 + round(30 * scale), x0 + seat_w - round(24 * scale), y0 + seat_h + round(18 * scale)),
        radius=10,
        fill=(233, 196, 210, 238),
        outline=(120, 88, 108, 180),
        width=2,
    )
    stem_x = cx - 7
    stem_y = y0 + seat_h + round(18 * scale)
    draw.rounded_rectangle(
        (stem_x, stem_y, stem_x + 14, stem_y + stem_h),
        radius=7,
        fill=(148, 154, 170, 255),
        outline=(93, 99, 112, 255),
        width=2,
    )
    hub_y = stem_y + stem_h + 8
    draw.ellipse((cx - 18, hub_y - 10, cx + 18, hub_y + 10), fill=(170, 176, 191, 255))
    for dx, dy in ((-50, -8), (48, -8), (-38, 20), (36, 20), (0, 30)):
        end_x = cx + round(dx * scale)
        end_y = hub_y + round(dy * scale)
        draw.line((cx, hub_y, end_x, end_y), fill=(124, 130, 146, 255), width=5)
        draw.ellipse((end_x - 10, end_y - 5, end_x + 10, end_y + 9), fill=(84, 88, 98, 255))
        draw.ellipse((end_x - 7, end_y - 2, end_x + 7, end_y + 6), fill=(127, 132, 147, 255))


def draw_motion(draw: ImageDraw.ImageDraw, frame_x: int) -> None:
    strokes = [
        (frame_x + 70, 282, frame_x + 62, 246),
        (frame_x + 84, 286, frame_x + 78, 254),
        (frame_x + 240, 282, frame_x + 248, 246),
        (frame_x + 254, 286, frame_x + 260, 254),
    ]
    widths = [5, 3, 5, 3]
    alphas = [220, 170, 220, 170]
    for stroke, width, alpha in zip(strokes, widths, alphas, strict=True):
        draw.line(stroke, fill=(255, 204, 148, alpha), width=width)


def draw_rays(draw: ImageDraw.ImageDraw, center: tuple[int, int], count: int) -> None:
    colors = [(255, 214, 132, 255), (255, 190, 212, 245), (255, 236, 178, 255)]
    for index in range(count):
        angle = math.radians((360 / count) * index - 28)
        inner = 12
        outer = 40 if index % 2 == 0 else 28
        x1 = center[0] + int(inner * math.cos(angle))
        y1 = center[1] + int(inner * math.sin(angle))
        x2 = center[0] + int((inner + outer) * math.cos(angle))
        y2 = center[1] + int((inner + outer) * math.sin(angle))
        draw.line((x1, y1, x2, y2), fill=colors[index % len(colors)], width=4 if index % 2 == 0 else 3)


def draw_sparkle(draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    draw.line((x - size, y, x + size, y), fill=(255, 238, 184, 255), width=3)
    draw.line((x, y - size, x, y + size), fill=(255, 238, 184, 255), width=3)
    draw.line((x - size + 3, y - size + 3, x + size - 3, y + size - 3), fill=(255, 198, 222, 240), width=2)
    draw.line((x - size + 3, y + size - 3, x + size - 3, y - size + 3), fill=(255, 198, 222, 240), width=2)


def build_canvas(cutout: Image.Image, sprites: list[Image.Image]) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    for index, stage in enumerate(STAGES):
        frame_x = index * FRAME_W
        chair_cx = frame_x + stage.chair_x
        chair_cy = stage.chair_y

        draw_shadow(canvas, frame_x + 40, 318, 220, 34, 60, 11)
        draw_chair_back(draw, chair_cx, chair_cy, stage.chair_scale)

        subject_source = cutout if stage.kind == "cutout" else sprites[stage.sprite_index or 0]
        subject = transform_subject(subject_source, stage)
        canvas.alpha_composite(subject, (frame_x + stage.x, stage.y))

        if stage.chair_front:
            draw_chair_front(draw, chair_cx, chair_cy, stage.chair_scale)
        else:
            draw_chair_front(draw, chair_cx + 12, chair_cy + 8, stage.chair_scale * 0.94)

        if stage.motion:
            draw_motion(draw, frame_x)

        if stage.rays:
            draw_rays(draw, (frame_x + 150, 74), stage.rays)

        if stage.sparkles >= 1:
            draw_sparkle(draw, frame_x + 268, 96, 12)
        if stage.sparkles >= 2:
            draw_sparkle(draw, frame_x + 74, 118, 10)
        if stage.sparkles >= 3:
            draw_sparkle(draw, frame_x + 288, 168, 8)

    return canvas


def main() -> None:
    cutout = load_cutout()
    sprites = load_sprite_variants()
    canvas = build_canvas(cutout, sprites)
    canvas.save(OUTPUT_PATH)


if __name__ == "__main__":
    main()
