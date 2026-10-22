"""Trace the existing sketch into animation masks; the original image stays unchanged."""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
original = Image.open(root / 'public/images/flatirons-landscape-v2.png').convert('RGBA')
image = original.copy()
image.thumbnail((887, 444))
rgba = np.asarray(image)
ink = (rgba[:, :, :3].mean(axis=2) < 219) & (rgba[:, :, 3] > 128)
# The red artist stamp is already excluded by the page's existing clip.
ink[:103, 834:] = False

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
chains = []
starts = sorted(pixels, key=lambda p: (len(adjacency[p]) != 1, p[1], p[0]))
for start in starts:
    for second in adjacency[start]:
        edge = tuple(sorted((start, second)))
        if edge in visited:
            continue
        chain = [start, second]
        visited.add(edge)
        length = math.dist(start, second)
        while length < 180:
            choices = [q for q in adjacency[chain[-1]] if tuple(sorted((chain[-1], q))) not in visited]
            if not choices:
                break
            # Continue along a pen line through junctions instead of lighting up
            # every tiny branch at the same horizontal position.
            previous, current = chain[-2:]
            direction = (current[0] - previous[0], current[1] - previous[1])
            def straightness(q):
                dy, dx = q[0] - current[0], q[1] - current[1]
                return (dy * direction[0] + dx * direction[1]) / math.hypot(dy, dx)
            q = max(choices, key=straightness)
            visited.add(tuple(sorted((chain[-1], q))))
            chain.append(q)
            length += math.dist(current, q)
        if chain[-1][1] < chain[0][1]:
            chain.reverse()
        # Keep corners but remove redundant collinear points.
        simplified = [chain[0]]
        for i in range(1, len(chain) - 1):
            a, b, c = chain[i - 1:i + 2]
            if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
                simplified.append(b)
        simplified.append(chain[-1])
        chains.append(([(int(x)*2, int(y)*2) for y, x in simplified],
                       int(max(distance[y, x] for y, x in chain)) * 4 + 4))

# Include isolated dots too; no original pen marks are dropped.
for y, x in pixels:
    if not adjacency[(y, x)]:
        chains.append(([(int(x)*2, int(y)*2), (int(x)*2 + 1, int(y)*2)], int(distance[y, x]) * 4 + 4))

coverage = Image.new('L', original.size)
draw = ImageDraw.Draw(coverage)
def cover(points, width):
    draw.line(points, fill=255, width=width, joint='curve')
    radius = width / 2
    for x, y in points:
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=255)
for points, width in chains:
    cover(points, width)

# Check against the full-resolution artwork, including antialiased edges.
# Any small disconnected marks join the normal stroke sequence, never an end fill.
full = np.asarray(original)
luminance = full[:, :, :3] @ np.array([.2126, .7152, .0722])
target = (luminance < 219) & (full[:, :, 3] > 128)
target[:204, 1667:] = False
missing = set(zip(*np.where(target & (np.asarray(coverage) == 0))))
while missing:
    seed = min(missing)
    missing.remove(seed)
    component = [seed]
    frontier = [seed]
    while frontier:
        y, x = frontier.pop()
        for dy, dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            q = (y+dy, x+dx)
            if q in missing:
                missing.remove(q)
                component.append(q)
                frontier.append(q)
    ys, xs = zip(*component)
    cx, cy = (min(xs)+max(xs))//2, (min(ys)+max(ys))//2
    width = math.ceil(math.hypot(max(xs)-min(xs), max(ys)-min(ys))) + 6
    points = [(cx, cy), (cx+1, cy)]
    chains.append((points, width))
    cover(points, width)

uncovered = int(np.count_nonzero(target & (np.asarray(coverage) == 0)))
assert uncovered == 0, f'{uncovered} original ink pixels remain uncovered'

# Stagger actual pen trajectories, rather than exposing a moving rectangle.
# A sinusoidal clock gives the entire drawing a slow-fast-slow five-second pace.
chains.sort(key=lambda item: (min(p[0] for p in item[0]) // 180, item[0][0][1], item[0][0][0]))
lengths = [sum(math.dist(a,b) for a,b in zip(points,points[1:])) for points,_ in chains]
weights = [max(8, length) for length in lengths]
total = sum(weights)
elapsed = 0
paths = []
ease_time = lambda p: math.acos(1 - 2 * min(1, max(0, p))) / math.pi
for (points, width), weight in zip(chains, weights):
    start = elapsed / total
    elapsed += weight
    finish = elapsed / total
    delay = 4.6 * ease_time(start)
    duration = max(.06, 5 * ease_time(finish) - delay)
    paths.append({
        'd': 'M' + ' '.join(f'{x},{y}' for x,y in points),
        'width': width, 'delay': round(delay,3), 'duration': round(duration,3),
    })

(root / 'src/data/flatirons-traces.json').write_text(json.dumps(paths, separators=(',', ':')), encoding='utf-8')
print(f'Created {len(paths)} continuous pen strokes. Full-resolution uncovered ink pixels: {uncovered}.')
