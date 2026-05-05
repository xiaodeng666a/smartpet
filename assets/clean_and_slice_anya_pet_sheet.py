from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image


SRC = Path("assets/anya_pet_sheet.png")
CLEAN_SRC = Path("assets/anya_pet_sheet_cleaned.png")
OUT_DIR = Path("assets/anya_pet_frames")
ROWS = 3
COLS = 4
PADDING = 6


def _has_dark_neighbor(px, x: int, y: int, w: int, h: int) -> bool:
    for ny in range(max(0, y - 1), min(h, y + 2)):
        for nx in range(max(0, x - 1), min(w, x + 2)):
            r, g, b, a = px[nx, ny]
            if a and max(r, g, b) < 120:
                return True
    return False


def _is_bg_like(
    rgba: tuple[int, int, int, int],
    bg_refs: list[tuple[int, int, int]],
    px,
    x: int,
    y: int,
    w: int,
    h: int,
) -> bool:
    r, g, b, a = rgba
    if a == 0:
        return True
    if max(r, g, b) < 170:
        return False
    if _has_dark_neighbor(px, x, y, w, h):
        return False
    if (max(r, g, b) - min(r, g, b)) > 18:
        return False
    for br, bg, bb in bg_refs:
        if abs(r - br) <= 18 and abs(g - bg) <= 18 and abs(b - bb) <= 18:
            return True
    return False


def _remove_checkerboard(frame: Image.Image) -> Image.Image:
    img = frame.copy().convert("RGBA")
    px = img.load()
    w, h = img.size
    sample_points = [
        (0, 0),
        (w - 1, 0),
        (0, h - 1),
        (w - 1, h - 1),
        (w // 2, 0),
        (w // 2, h - 1),
        (0, h // 2),
        (w - 1, h // 2),
    ]
    bg_refs: list[tuple[int, int, int]] = []
    for sx, sy in sample_points:
        r, g, b, a = px[sx, sy]
        if a:
            bg_refs.append((r, g, b))
    if not bg_refs:
        return img

    q: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    def maybe_push(x: int, y: int) -> None:
        if (x, y) in seen:
            return
        if _is_bg_like(px[x, y], bg_refs, px, x, y, w, h):
            seen.add((x, y))
            q.append((x, y))

    for x in range(w):
        maybe_push(x, 0)
        maybe_push(x, h - 1)
    for y in range(h):
        maybe_push(0, y)
        maybe_push(w - 1, y)

    while q:
        x, y = q.popleft()
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)
        if x > 0:
            maybe_push(x - 1, y)
        if x < w - 1:
            maybe_push(x + 1, y)
        if y > 0:
            maybe_push(x, y - 1)
        if y < h - 1:
            maybe_push(x, y + 1)

    return img


def _component_stats(frame: Image.Image) -> list[dict[str, object]]:
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


def _remove_bottom_shadow_components(frame: Image.Image) -> Image.Image:
    img = frame.copy().convert("RGBA")
    components = _component_stats(img)
    if len(components) <= 1:
        return img

    px = img.load()
    _, h = img.size
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

    return img


def _wipe_bottom_pale_shadow(frame: Image.Image) -> Image.Image:
    img = frame.copy().convert("RGBA")
    px = img.load()
    w, h = img.size
    start_y = int(h * 0.72)

    for y in range(start_y, h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            brightness = max(r, g, b)
            spread = brightness - min(r, g, b)
            if brightness < 172 or spread > 20:
                continue

            near_dark_line = False
            for ny in range(max(0, y - 2), min(h, y + 3)):
                for nx in range(max(0, x - 2), min(w, x + 3)):
                    nr, ng, nb, na = px[nx, ny]
                    if na and max(nr, ng, nb) < 118:
                        near_dark_line = True
                        break
                if near_dark_line:
                    break

            if not near_dark_line:
                px[x, y] = (r, g, b, 0)

    return img


def _wipe_bottom_center_shadow(frame: Image.Image) -> Image.Image:
    img = frame.copy().convert("RGBA")
    px = img.load()
    w, h = img.size
    start_y = int(h * 0.74)
    min_x = int(w * 0.18)
    max_x = int(w * 0.86)

    for y in range(start_y, h):
        for x in range(min_x, max_x):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            brightness = max(r, g, b)
            spread = brightness - min(r, g, b)
            if brightness >= 150 and spread <= 36:
                px[x, y] = (r, g, b, 0)

    return img


def main() -> None:
    sheet = Image.open(SRC).convert("RGBA")
    frame_w = sheet.width // COLS
    frame_h = sheet.height // ROWS

    clean_sheet = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    cleaned_frames: list[Image.Image] = []
    bboxes: list[tuple[int, int, int, int]] = []

    for row in range(ROWS):
        for col in range(COLS):
            left = col * frame_w
            top = row * frame_h
            frame = sheet.crop((left, top, left + frame_w, top + frame_h))
            frame = _remove_checkerboard(frame)
            frame = _remove_bottom_shadow_components(frame)
            frame = _wipe_bottom_pale_shadow(frame)
            frame = _wipe_bottom_center_shadow(frame)
            clean_sheet.paste(frame, (left, top))
            cleaned_frames.append(frame)
            bboxes.append(frame.getbbox() or (0, 0, frame.width, frame.height))

    CLEAN_SRC.parent.mkdir(parents=True, exist_ok=True)
    clean_sheet.save(CLEAN_SRC)

    union_left = max(0, min(b[0] for b in bboxes) - PADDING)
    union_top = max(0, min(b[1] for b in bboxes) - PADDING)
    union_right = min(frame_w, max(b[2] for b in bboxes) + PADDING)
    union_bottom = min(frame_h, max(b[3] for b in bboxes) + PADDING)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("frame_*.png"):
        old.unlink()

    for index, frame in enumerate(cleaned_frames):
        cropped = frame.crop((union_left, union_top, union_right, union_bottom))
        cropped.save(OUT_DIR / f"frame_{index:03d}.png")

    print(
        f"cleaned_sheet={CLEAN_SRC} frames={len(cleaned_frames)} "
        f"crop={union_right - union_left}x{union_bottom - union_top}"
    )


if __name__ == "__main__":
    main()
