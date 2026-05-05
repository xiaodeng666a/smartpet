from __future__ import annotations

from pathlib import Path
from collections import deque

from PIL import Image


ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "anya_sedentary_source.png"
OUTPUT_SHEET_PATH = ROOT / "anya_sedentary_sheet.png"
FRAMES_DIR = ROOT / "anya_sedentary_frames"

FRAME_W = 362
FRAME_H = 362
EXPECTED_FRAMES = 8
FRAME_CELL_OVERLAP = 80
FRAME_PADDING_LEFT = 10
FRAME_PADDING_TOP = 10
FRAME_PADDING_RIGHT = 32
FRAME_PADDING_BOTTOM = 12
KEY_COLOR = (0, 255, 0)
KEY_TOLERANCE = 20
EDGE_ALPHA_LIMIT = 220
COMPONENT_CENTER_MARGIN = 0


def remove_green_screen(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            green_is_key = (
                green >= 150
                and green - red >= 35
                and green - blue >= 35
            )
            pure_key_match = (
                abs(red - KEY_COLOR[0]) <= KEY_TOLERANCE
                and abs(green - KEY_COLOR[1]) <= KEY_TOLERANCE
                and abs(blue - KEY_COLOR[2]) <= KEY_TOLERANCE
            )
            if green_is_key or pure_key_match:
                pixels[x, y] = (0, 0, 0, 0)
            elif green > red and green > blue:
                dominant_other = max(red, blue)
                corrected_green = min(green, dominant_other + 10)
                pixels[x, y] = (red, corrected_green, blue, alpha)

    return rgba


def split_frames_by_grid(image: Image.Image, expected_frames: int) -> list[Image.Image]:
    width, height = image.size
    frames: list[Image.Image] = []

    for index in range(expected_frames):
        base_start_x = round(index * width / expected_frames)
        base_end_x = round((index + 1) * width / expected_frames)
        expanded_start_x = max(0, base_start_x - FRAME_CELL_OVERLAP)
        expanded_end_x = min(width, base_end_x + FRAME_CELL_OVERLAP)
        local_base_start_x = base_start_x - expanded_start_x
        local_base_end_x = local_base_start_x + (base_end_x - base_start_x)
        cell = image.crop((expanded_start_x, 0, expanded_end_x, height))
        frames.append(
            keep_components_for_cell(cell, local_base_start_x, local_base_end_x)
        )

    return frames


def keep_components_for_cell(
    image: Image.Image,
    local_base_start_x: int,
    local_base_end_x: int,
) -> Image.Image:
    rgba = image.copy().convert("RGBA")
    alpha = rgba.getchannel("A")
    width, height = rgba.size
    visited = [[False] * width for _ in range(height)]
    pixels = rgba.load()

    for start_y in range(height):
        for start_x in range(width):
            if visited[start_y][start_x] or alpha.getpixel((start_x, start_y)) == 0:
                continue

            queue = deque([(start_x, start_y)])
            component: list[tuple[int, int]] = []
            visited[start_y][start_x] = True
            min_x = max_x = start_x

            while queue:
                x, y = queue.popleft()
                component.append((x, y))
                min_x = min(min_x, x)
                max_x = max(max_x, x)

                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < width and 0 <= ny < height:
                        if visited[ny][nx] or alpha.getpixel((nx, ny)) == 0:
                            continue
                        visited[ny][nx] = True
                        queue.append((nx, ny))

            center_x = (min_x + max_x) / 2
            should_keep = (
                local_base_start_x - COMPONENT_CENTER_MARGIN
                <= center_x
                <= local_base_end_x + COMPONENT_CENTER_MARGIN
            )
            if not should_keep:
                for x, y in component:
                    pixels[x, y] = (0, 0, 0, 0)

    return rgba


def fit_frames_to_canvas(frames: list[Image.Image]) -> list[Image.Image]:
    cropped_frames: list[Image.Image] = []
    max_width = 1
    max_height = 1

    for frame in frames:
        bbox = frame.getbbox()
        if not bbox:
            cropped = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        else:
            left = max(0, bbox[0] - FRAME_PADDING_LEFT)
            top = max(0, bbox[1] - FRAME_PADDING_TOP)
            right = min(frame.width, bbox[2] + FRAME_PADDING_RIGHT)
            bottom = min(frame.height, bbox[3] + FRAME_PADDING_BOTTOM)
            cropped = frame.crop((left, top, right, bottom))
        cropped_frames.append(cropped)
        max_width = max(max_width, cropped.width)
        max_height = max(max_height, cropped.height)

    shared_scale = min(FRAME_W / max_width, FRAME_H / max_height)
    fitted_frames: list[Image.Image] = []

    for cropped in cropped_frames:
        resized = cropped.resize(
            (
                max(1, round(cropped.width * shared_scale)),
                max(1, round(cropped.height * shared_scale)),
            ),
            Image.Resampling.LANCZOS,
        )
        canvas = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        x = (FRAME_W - resized.width) // 2
        y = FRAME_H - resized.height
        canvas.alpha_composite(resized, (x, y))
        fitted_frames.append(clean_green_edges(canvas))

    return fitted_frames


def clean_green_edges(image: Image.Image) -> Image.Image:
    cleaned = image.copy().convert("RGBA")
    pixels = cleaned.load()
    width, height = cleaned.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                pixels[x, y] = (0, 0, 0, 0)
                continue

            if green <= red or green <= blue:
                continue

            if alpha < EDGE_ALPHA_LIMIT:
                dominant_other = max(red, blue)
                corrected_green = min(green, dominant_other + 6)
                pixels[x, y] = (red, corrected_green, blue, alpha)

    return cleaned


def write_frames(frames: list[Image.Image]) -> None:
    FRAMES_DIR.mkdir(exist_ok=True)
    for old_file in FRAMES_DIR.glob("*.png"):
        old_file.unlink()

    for index, frame in enumerate(frames):
        frame.save(FRAMES_DIR / f"frame_{index:03}.png")


def build_sheet(frames: list[Image.Image]) -> Image.Image:
    sheet = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        sheet.alpha_composite(frame, (index * FRAME_W, 0))
    return sheet


def main() -> None:
    source = Image.open(SOURCE_PATH)
    cleaned = remove_green_screen(source)
    raw_frames = split_frames_by_grid(cleaned, EXPECTED_FRAMES)
    frames = fit_frames_to_canvas(raw_frames)
    write_frames(frames)
    build_sheet(frames).save(OUTPUT_SHEET_PATH)


if __name__ == "__main__":
    main()
