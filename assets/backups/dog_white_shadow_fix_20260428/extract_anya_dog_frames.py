from collections import Counter, deque
from pathlib import Path

from PIL import Image


SRC = Path("assets/anya_dog.gif")
OUT_DIR = Path("assets/anya_dog_frames")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def bucket(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple((c // 8) * 8 for c in rgb)


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def collect_background_colors(image: Image.Image) -> list[tuple[int, int, int]]:
    w, h = image.size
    px = image.load()
    samples: list[tuple[int, int, int]] = []

    edge_points = []
    step_x = max(1, w // 20)
    step_y = max(1, h // 20)
    for x in range(0, w, step_x):
        edge_points.extend([(x, 0), (x, h - 1)])
        if h > 8:
            edge_points.extend([(x, 4), (x, min(h - 1, 8))])
    for y in range(0, h, step_y):
        edge_points.extend([(0, y), (w - 1, y)])
        if w > 8:
            edge_points.extend([(4, y), (min(w - 1, 8), y)])

    for x, y in edge_points:
        rgba = px[x, y]
        if rgba[3] > 0:
            samples.append(rgba[:3])

    counts = Counter(bucket(rgb) for rgb in samples)
    # 棋盘底通常只有 2-4 个主色；保守一点避免误伤白色细节
    return [rgb for rgb, _ in counts.most_common(4)]


def strip_edge_connected_background(image: Image.Image) -> Image.Image:
    frame = image.copy().convert("RGBA")
    w, h = frame.size
    px = frame.load()
    bg_colors = collect_background_colors(frame)
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    for x in range(w):
        queue.append((x, 0))
        queue.append((x, h - 1))
    for y in range(h):
        queue.append((0, y))
        queue.append((w - 1, y))

    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or (x, y) in visited:
            continue
        visited.add((x, y))

        rgba = px[x, y]
        if rgba[3] == 0:
            queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
            continue

        rgb = rgba[:3]
        # 阈值收紧，只清掉和边缘棋盘底非常接近的连通区域
        if any(color_distance(rgb, bg) <= 30 for bg in bg_colors):
            px[x, y] = (255, 255, 255, 0)
            queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return frame


im = Image.open(SRC)
stripped_frames: list[Image.Image] = []
bboxes: list[tuple[int, int, int, int]] = []

for i in range(getattr(im, "n_frames", 1)):
    im.seek(i)
    clean = strip_edge_connected_background(im)
    bbox = clean.getbbox()
    if bbox is None:
        bbox = (0, 0, clean.width, clean.height)
    stripped_frames.append(clean)
    bboxes.append(bbox)

left = min(b[0] for b in bboxes)
top = min(b[1] for b in bboxes)
right = max(b[2] for b in bboxes)
bottom = max(b[3] for b in bboxes)
frame_w = right - left
frame_h = bottom - top

for old in OUT_DIR.glob("frame_*.png"):
    old.unlink()

for idx, frame in enumerate(stripped_frames):
    cropped = frame.crop((left, top, right, bottom))
    cropped.save(OUT_DIR / f"frame_{idx:03d}.png")

print(f"extracted={len(stripped_frames)} size={frame_w}x{frame_h} dir={OUT_DIR}")
