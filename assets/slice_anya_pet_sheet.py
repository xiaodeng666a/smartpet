from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image


SRC = Path("assets/anya_pet_sheet.png")
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
    # Keep dark outlines and colored subject parts safe.
    if max(r, g, b) < 170:
        return False
    # Preserve bright interior subject regions that touch line art.
    if _has_dark_neighbor(px, x, y, w, h):
        return False
    # Checkerboard cells are low-saturation near-white tones.
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

    # Sample corners and edge midpoints as likely checkerboard references.
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


def _remove_floor_shadow(frame: Image.Image) -> Image.Image:
    img = frame.copy().convert("RGBA")
    px = img.load()
    w, h = img.size
    start_y = int(h * 0.76)

    def is_shadow_candidate(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        if a == 0:
            return False
        brightness = max(r, g, b)
        spread = max(r, g, b) - min(r, g, b)
        # Only target very light, low-saturation pixels low in the frame.
        return brightness >= 180 and spread <= 12

    seen: set[tuple[int, int]] = set()
    for y in range(start_y, h):
        for x in range(w):
            if (x, y) in seen or not is_shadow_candidate(x, y):
                continue

            q: deque[tuple[int, int]] = deque([(x, y)])
            seen.add((x, y))
            component: list[tuple[int, int]] = []
            min_x = max_x = x
            min_y = max_y = y
            touches_dark = False

            while q:
                cx, cy = q.popleft()
                component.append((cx, cy))
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                if _has_dark_neighbor(px, cx, cy, w, h):
                    touches_dark = True

                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and is_shadow_candidate(nx, ny):
                        seen.add((nx, ny))
                        q.append((nx, ny))

            comp_w = max_x - min_x + 1
            comp_h = max_y - min_y + 1

            # Remove only detached, flat shadow blobs near the bottom.
            # Be a bit more permissive than before so the pale ground streak disappears,
            # but still avoid anything hugging the line art.
            if not touches_dark and comp_h <= 14 and comp_w >= 12 and min_y >= int(h * 0.78):
                for cx, cy in component:
                    r, g, b, _ = px[cx, cy]
                    px[cx, cy] = (r, g, b, 0)

    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sheet = Image.open(SRC).convert("RGBA")
    frame_w = sheet.width // COLS
    frame_h = sheet.height // ROWS

    raw_frames: list[Image.Image] = []
    bboxes: list[tuple[int, int, int, int]] = []

    for row in range(ROWS):
        for col in range(COLS):
            left = col * frame_w
            top = row * frame_h
            frame = sheet.crop((left, top, left + frame_w, top + frame_h))
            frame = _remove_checkerboard(frame)
            frame = _remove_floor_shadow(frame)
            bbox = frame.getbbox() or (0, 0, frame.width, frame.height)
            raw_frames.append(frame)
            bboxes.append(bbox)

    union_left = max(0, min(b[0] for b in bboxes) - PADDING)
    union_top = max(0, min(b[1] for b in bboxes) - PADDING)
    union_right = min(frame_w, max(b[2] for b in bboxes) + PADDING)
    union_bottom = min(frame_h, max(b[3] for b in bboxes) + PADDING)

    out_w = union_right - union_left
    out_h = union_bottom - union_top

    for old in OUT_DIR.glob("frame_*.png"):
        old.unlink()

    for index, frame in enumerate(raw_frames):
        cropped = frame.crop((union_left, union_top, union_right, union_bottom))
        cropped.save(OUT_DIR / f"frame_{index:03d}.png")

    print(f"sliced={len(raw_frames)} size={out_w}x{out_h} dir={OUT_DIR}")


if __name__ == "__main__":
    main()
