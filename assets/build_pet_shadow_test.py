from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

from slice_anya_pet_sheet import COLS, PADDING, ROWS, _remove_checkerboard


SRC = Path("assets/anya_pet_sheet.png")
OUT_DIR = Path("assets/anya_pet_frames_test_detached")
TEST_DIR = Path("assets/test_outputs")
CLEAN_SHEET_PATH = TEST_DIR / "anya_pet_sheet_test_detached.png"
COMPARE_PATH = TEST_DIR / "pet_shadow_compare.png"
MANUAL_SHADOW_MASKS = {
    3: (136, 309, 60, 22),
    4: (198, 292, 54, 14),
    7: (150, 293, 58, 14),
    11: (144, 272, 60, 14),
}
EXTRA_REMOVE_MASKS = {
    3: [(123, 292, 30, 12)],
    7: [(112, 293, 34, 10), (182, 283, 28, 10)],
}
RESTORE_MASKS = {
    3: [(113, 301, 18, 9)],
}


def _find_components(frame: Image.Image) -> list[dict[str, object]]:
    px = frame.load()
    w, h = frame.size
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, object]] = []

    for y in range(h):
        for x in range(w):
            if (x, y) in seen or px[x, y][3] == 0:
                continue

            q: deque[tuple[int, int]] = deque([(x, y)])
            seen.add((x, y))
            points: list[tuple[int, int]] = []
            min_x = max_x = x
            min_y = max_y = y
            brightness_total = 0
            spread_total = 0

            while q:
                cx, cy = q.popleft()
                points.append((cx, cy))
                r, g, b, _ = px[cx, cy]
                brightness = max(r, g, b)
                spread = brightness - min(r, g, b)
                brightness_total += brightness
                spread_total += spread
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)

                for nx, ny in (
                    (cx - 1, cy),
                    (cx + 1, cy),
                    (cx, cy - 1),
                    (cx, cy + 1),
                    (cx - 1, cy - 1),
                    (cx + 1, cy - 1),
                    (cx - 1, cy + 1),
                    (cx + 1, cy + 1),
                ):
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and px[nx, ny][3] > 0:
                        seen.add((nx, ny))
                        q.append((nx, ny))

            components.append(
                {
                    "points": points,
                    "size": len(points),
                    "bbox": (min_x, min_y, max_x, max_y),
                    "avg_brightness": brightness_total / len(points),
                    "avg_spread": spread_total / len(points),
                }
            )

    components.sort(key=lambda comp: int(comp["size"]), reverse=True)
    return components


def _remove_detached_bottom_shadow(frame: Image.Image) -> tuple[Image.Image, int]:
    img = frame.copy().convert("RGBA")
    px = img.load()
    _, h = img.size
    removed = 0

    components = _find_components(img)
    if len(components) <= 1:
        return img, removed

    for comp in components[1:]:
        min_x, min_y, max_x, max_y = comp["bbox"]
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        is_bottom_shadow = (
            min_y >= int(h * 0.72)
            and height <= 18
            and width <= 180
            and int(comp["size"]) <= 1600
            and float(comp["avg_brightness"]) >= 215
            and float(comp["avg_spread"]) <= 4
        )
        if not is_bottom_shadow:
            continue

        for x, y in comp["points"]:
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 0)
            removed += 1

    # A few frames still leave behind tiny detached white dashes at the bottom edge.
    # These are safe to drop because they are isolated, very small, and far below the body.
    components = _find_components(img)
    for comp in components[1:]:
        min_x, min_y, max_x, max_y = comp["bbox"]
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        is_tiny_bottom_dash = (
            min_y >= int(h * 0.96)
            and height <= 3
            and width <= 10
            and int(comp["size"]) <= 20
        )
        if not is_tiny_bottom_dash:
            continue

        for x, y in comp["points"]:
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 0)
            removed += 1

    return img, removed


def _apply_manual_shadow_mask(frame: Image.Image, frame_index: int) -> tuple[Image.Image, int]:
    img = frame.copy().convert("RGBA")
    px = img.load()
    w, h = img.size
    removed = 0

    masks = []
    if frame_index in MANUAL_SHADOW_MASKS:
        masks.append(MANUAL_SHADOW_MASKS[frame_index])
    masks.extend(EXTRA_REMOVE_MASKS.get(frame_index, []))

    for cx, cy, rx, ry in masks:
        for y in range(max(0, cy - ry - 2), min(h, cy + ry + 3)):
            for x in range(max(0, cx - rx - 2), min(w, cx + rx + 3)):
                norm = ((x - cx) / max(1, rx)) ** 2 + ((y - cy) / max(1, ry)) ** 2
                if norm > 1.2:
                    continue

                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                brightness = max(r, g, b)
                spread = brightness - min(r, g, b)
                if brightness < 125 or spread > 48:
                    continue

                if y < cy - max(2, ry // 2):
                    continue

                has_dark_neighbor = False
                for ny in range(max(0, y - 2), min(h, y + 3)):
                    for nx in range(max(0, x - 2), min(w, x + 3)):
                        nr, ng, nb, na = px[nx, ny]
                        if na and max(nr, ng, nb) < 90:
                            has_dark_neighbor = True
                            break
                    if has_dark_neighbor:
                        break

                if has_dark_neighbor:
                    continue

                px[x, y] = (r, g, b, 0)
                removed += 1

    return img, removed


def _restore_protected_pixels(
    original_frame: Image.Image, frame: Image.Image, frame_index: int
) -> tuple[Image.Image, int]:
    if frame_index not in RESTORE_MASKS:
        return frame, 0

    original = original_frame.convert("RGBA")
    img = frame.copy().convert("RGBA")
    opx = original.load()
    px = img.load()
    w, h = img.size
    restored = 0

    for cx, cy, rx, ry in RESTORE_MASKS[frame_index]:
        for y in range(max(0, cy - ry - 2), min(h, cy + ry + 3)):
            for x in range(max(0, cx - rx - 2), min(w, cx + rx + 3)):
                norm = ((x - cx) / max(1, rx)) ** 2 + ((y - cy) / max(1, ry)) ** 2
                if norm > 1.05:
                    continue

                or_, og, ob, oa = opx[x, y]
                if oa == 0:
                    continue
                if px[x, y][3] != 0:
                    continue

                near_dark_line = False
                for ny in range(max(0, y - 2), min(h, y + 3)):
                    for nx in range(max(0, x - 2), min(w, x + 3)):
                        nr, ng, nb, na = opx[nx, ny]
                        if na and max(nr, ng, nb) < 115:
                            near_dark_line = True
                            break
                    if near_dark_line:
                        break

                if not near_dark_line and y > cy + max(1, ry // 3):
                    continue

                px[x, y] = (or_, og, ob, oa)
                restored += 1

    return img, restored


def _remove_remaining_bottom_components(frame: Image.Image, frame_index: int) -> tuple[Image.Image, int]:
    if frame_index not in MANUAL_SHADOW_MASKS:
        return frame, 0

    img = frame.copy().convert("RGBA")
    px = img.load()
    _, h = img.size
    removed = 0
    components = _find_components(img)

    for comp in components[1:]:
        min_x, min_y, max_x, max_y = comp["bbox"]
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        is_bottom_leftover = (
            min_y >= int(h * 0.8)
            and height <= 18
            and width <= 60
            and int(comp["size"]) <= 320
        )
        if not is_bottom_leftover:
            continue

        for x, y in comp["points"]:
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 0)
            removed += 1

    if frame_index == 11:
        components = _find_components(img)
        for comp in components[1:]:
            if int(comp["size"]) > 400:
                continue
            for x, y in comp["points"]:
                r, g, b, _ = px[x, y]
                px[x, y] = (r, g, b, 0)
                removed += 1

    return img, removed


def _save_compare(originals: list[Image.Image], cleaned: list[Image.Image], indices: list[int]) -> None:
    tiles_original = [originals[index] for index in indices]
    tiles_cleaned = [cleaned[index] for index in indices]
    tile_w = max(tile.width for tile in tiles_original + tiles_cleaned)
    tile_h = max(tile.height for tile in tiles_original + tiles_cleaned)
    margin = 20
    gap = 12
    header_h = 28
    canvas_w = margin * 2 + len(indices) * tile_w + (len(indices) - 1) * gap
    canvas_h = margin * 2 + header_h * 2 + tile_h * 2 + gap
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, margin), "Original", fill=(40, 40, 40, 255))
    draw.text((margin, margin + header_h + tile_h + gap), "Test", fill=(40, 40, 40, 255))

    for col, index in enumerate(indices):
        x = margin + col * (tile_w + gap)
        draw.text((x, margin + 12), f"frame_{index:03d}", fill=(90, 90, 90, 255))
        original = tiles_original[col]
        cleaned_frame = tiles_cleaned[col]
        canvas.alpha_composite(original, (x, margin + header_h))
        canvas.alpha_composite(cleaned_frame, (x, margin + header_h * 2 + tile_h + gap))

    COMPARE_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(COMPARE_PATH)


def main() -> None:
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sheet = Image.open(SRC).convert("RGBA")
    frame_w = sheet.width // COLS
    frame_h = sheet.height // ROWS
    clean_sheet = Image.new("RGBA", sheet.size, (0, 0, 0, 0))

    original_frames: list[Image.Image] = []
    cleaned_frames: list[Image.Image] = []
    bboxes: list[tuple[int, int, int, int]] = []
    removed_pixels_total = 0

    for row in range(ROWS):
        for col in range(COLS):
            left = col * frame_w
            top = row * frame_h
            frame = sheet.crop((left, top, left + frame_w, top + frame_h))
            frame = _remove_checkerboard(frame)
            original_frames.append(frame.copy())
            frame_index = row * COLS + col
            cleaned_frame, removed_pixels = _remove_detached_bottom_shadow(frame)
            cleaned_frame, manual_removed = _apply_manual_shadow_mask(cleaned_frame, frame_index)
            cleaned_frame, leftover_removed = _remove_remaining_bottom_components(
                cleaned_frame, frame_index
            )
            cleaned_frame, restored_pixels = _restore_protected_pixels(
                frame, cleaned_frame, frame_index
            )
            removed_pixels_total += (
                removed_pixels + manual_removed + leftover_removed - restored_pixels
            )
            cleaned_frames.append(cleaned_frame)
            clean_sheet.paste(cleaned_frame, (left, top))
            bboxes.append(cleaned_frame.getbbox() or (0, 0, cleaned_frame.width, cleaned_frame.height))

    clean_sheet.save(CLEAN_SHEET_PATH)

    union_left = max(0, min(b[0] for b in bboxes) - PADDING)
    union_top = max(0, min(b[1] for b in bboxes) - PADDING)
    union_right = min(frame_w, max(b[2] for b in bboxes) + PADDING)
    union_bottom = min(frame_h, max(b[3] for b in bboxes) + PADDING)

    for old in OUT_DIR.glob("frame_*.png"):
        old.unlink()

    for index, frame in enumerate(cleaned_frames):
        cropped = frame.crop((union_left, union_top, union_right, union_bottom))
        cropped.save(OUT_DIR / f"frame_{index:03d}.png")

    _save_compare(original_frames, cleaned_frames, [3, 4, 5, 6, 7, 8, 9, 10, 11])

    print(
        f"test_frames={OUT_DIR} cleaned_sheet={CLEAN_SHEET_PATH} "
        f"compare={COMPARE_PATH} removed_pixels={removed_pixels_total}"
    )


if __name__ == "__main__":
    main()
