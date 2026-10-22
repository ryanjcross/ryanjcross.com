"""Trace the existing sketch into animation masks; the original image stays unchanged."""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[1]
image = Image.open(root / 'public/images/flatirons-landscape-v2.png').convert('RGBA')
image.thumbnail((887, 444))
rgba = np.asarray(image)
ink = (rgba[:, :, :3].mean(axis=2) < 190) & (rgba[:, :, 3] > 128)
# The red artist stamp is already excluded by the page's existing clip.
ink[:110, 830:] = False

def neighbors(a):
    p = np.pad(a, 1)
    return [p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:], p[2:, 2:],
            p[2:, 1:-1], p[2:, :-2], p[1:-1, :-2], p[:-2, :-2]]

# Distance from the ink boundary provides enough mask width for thicker pen strokes.
distance = np.zeros(ink.shape, dtype=np.uint8)
remaining = ink.copy()
while remaining.any():
    distance[remaining] += 1
    remaining &= np.logical_and.reduce(neighbors(remaining))

# Zhang-Suen thinning retains the topology and centerline of the supplied artwork.
skeleton = ink.copy()
changed = True
while changed:
    changed = False
    for step in (0, 1):
        n = neighbors(skeleton)
        count = sum(v.astype(np.uint8) for v in n)
        transitions = sum((~n[i] & n[(i + 1) % 8]).astype(np.uint8) for i in range(8))
        removable = skeleton & (count >= 2) & (count <= 6) & (transitions == 1)
        if step == 0:
            removable &= ~(n[0] & n[2] & n[4]) & ~(n[2] & n[4] & n[6])
        else:
            removable &= ~(n[0] & n[2] & n[6]) & ~(n[0] & n[4] & n[6])
        if removable.any():
            skeleton[removable] = False
            changed = True

pixels = set(zip(*np.where(skeleton)))
adjacency = {}
for y, x in pixels:
    adjacent = []
    for dy, dx in [(-1, 0), (0, 1), (1, 0), (0, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)]:
        q = (y + dy, x + dx)
        if q not in pixels:
            continue
        # Avoid diagonal shortcuts where an orthogonal connection already exists.
        if dy and dx and ((y + dy, x) in pixels or (y, x + dx) in pixels):
            continue
        adjacent.append(q)
    adjacency[(y, x)] = adjacent

visited = set()
paths = []
starts = sorted(pixels, key=lambda p: (len(adjacency[p]) == 2, p[1], p[0]))
for start in starts:
    for second in adjacency[start]:
        edge = tuple(sorted((start, second)))
        if edge in visited:
            continue
        chain = [start, second]
        visited.add(edge)
        while len(adjacency[chain[-1]]) == 2:
            choices = [q for q in adjacency[chain[-1]] if tuple(sorted((chain[-1], q))) not in visited]
            if not choices:
                break
            q = choices[0]
            visited.add(tuple(sorted((chain[-1], q))))
            chain.append(q)
        if len(chain) < 3:
            continue
        if chain[-1][1] < chain[0][1]:
            chain.reverse()
        # Keep corners but remove redundant collinear points.
        simplified = [chain[0]]
        for i in range(1, len(chain) - 1):
            a, b, c = chain[i - 1:i + 2]
            if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
                simplified.append(b)
        simplified.append(chain[-1])
        xs = [p[1] for p in chain]
        left = min(xs) / 887
        right = max(xs) / 887
        ease_time = lambda p: math.acos(1 - 2 * min(1, max(0, p))) / math.pi
        delay = 4.5 * ease_time(left)
        duration = min(5 - delay, max(.16, 4.5 * (ease_time(right) - ease_time(left)) + .3))
        paths.append({
            'd': 'M' + ' '.join(f'{int(x)*2},{int(y)*2}' for y, x in simplified),
            'width': int(max(distance[y, x] for y, x in chain)) * 4 + 8,
            'delay': round(delay, 3), 'duration': round(duration, 3),
        })

(root / 'src/data/flatirons-traces.json').write_text(json.dumps(paths, separators=(',', ':')), encoding='utf-8')
print(f'Created {len(paths)} pen-stroke animation masks.')
