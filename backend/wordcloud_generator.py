import html
import math
import re


PALETTE = [
    "#0f172a",
    "#1d4ed8",
    "#0f766e",
    "#7c3aed",
    "#c2410c",
    "#0891b2",
]
MAX_WORDS = 36


def _font_size(value, min_value, max_value):
    if max_value <= min_value:
        return 34
    ratio = (value - min_value) / (max_value - min_value)
    eased = ratio ** 0.72
    return round(15 + eased * 40)


def _estimate_box(word, font_size, rotate):
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", word))
    latin_chars = max(0, len(word) - cjk_chars)
    width = (cjk_chars * font_size * 1.02) + (latin_chars * font_size * 0.64) + 10
    height = font_size * 1.14
    if rotate == 90:
        width, height = height, max(font_size * 1.45, width * 0.92)
    return max(width, font_size * 1.6), max(height, font_size * 1.1)


def _box_in_ellipse(box, center_x, center_y, radius_x, radius_y):
    left, top, right, bottom = box
    corners = ((left, top), (left, bottom), (right, top), (right, bottom))
    for x, y in corners:
        dx = (x - center_x) / radius_x
        dy = (y - center_y) / radius_y
        if dx * dx + dy * dy > 1:
            return False
    return True


def _overlaps(candidate, placed, padding):
    left, top, right, bottom = candidate
    for item in placed:
        il, it, ir, ib = item["box"]
        if not (right + padding < il or left - padding > ir or bottom + padding < it or top - padding > ib):
            return True
    return False


def _place_words(items, width, height):
    center_x = width / 2
    center_y = height / 2
    radius_x = width * 0.41
    radius_y = height * 0.33
    placed = []

    for index, item in enumerate(items):
        rotations = [0] if index < 8 or item["font_size"] >= 34 else [0, 0, 90]
        scales = [1.0, 0.94, 0.88]
        placed_item = None

        for scale in scales:
            font_size = max(13, round(item["font_size"] * scale))
            for rotate in rotations:
                box_w, box_h = _estimate_box(item["name"], font_size, rotate)
                padding = 8 if font_size >= 34 else 6 if font_size >= 24 else 4

                for step in range(1400):
                    angle = (step * 0.31) + (index * 0.53)
                    distance = 6 + step * 0.42
                    x = center_x + math.cos(angle) * distance
                    y = center_y + math.sin(angle) * distance * 0.78
                    candidate = (x - box_w / 2, y - box_h / 2, x + box_w / 2, y + box_h / 2)

                    if not _box_in_ellipse(candidate, center_x, center_y, radius_x, radius_y):
                        continue
                    if _overlaps(candidate, placed, padding):
                        continue

                    placed_item = {
                        "name": item["name"],
                        "x": round(x, 1),
                        "y": round(y, 1),
                        "font_size": font_size,
                        "color": item["color"],
                        "rotate": rotate,
                        "box": candidate,
                        "weight": item["weight"],
                    }
                    break

                if placed_item:
                    break
            if placed_item:
                break

        if placed_item:
            placed.append(placed_item)

    return placed


def build_wordcloud_svg(words, width=960, height=540):
    cleaned = [item for item in words if item.get("name") and item.get("value", 0) > 0][:MAX_WORDS]
    if not cleaned:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            '<rect width="100%" height="100%" fill="#f8fbff" rx="28"/>'
            '<text x="50%" y="50%" text-anchor="middle" fill="#64748b" font-size="24" font-family="Microsoft YaHei, PingFang SC, sans-serif">暂无词云数据</text>'
            "</svg>"
        )

    min_value = min(item["value"] for item in cleaned)
    max_value = max(item["value"] for item in cleaned)
    prepared = []
    total = len(cleaned)
    for index, item in enumerate(cleaned):
        prepared.append(
            {
                "name": item["name"],
                "value": item["value"],
                "font_size": _font_size(item["value"], min_value, max_value),
                "color": PALETTE[index % len(PALETTE)],
                "weight": 800 if index < 4 else 700 if index < 12 else 600,
            }
        )

    prepared.sort(key=lambda row: (-row["value"], row["name"]))
    placed = _place_words(prepared, width, height)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        '<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '<stop offset="0%" stop-color="#f8fbff"/>',
        '<stop offset="100%" stop-color="#ecf5ff"/>',
        "</linearGradient>",
        '<radialGradient id="ellipseGlow" cx="50%" cy="50%" r="58%">',
        '<stop offset="0%" stop-color="#ffffff" stop-opacity="0.96"/>',
        '<stop offset="100%" stop-color="#dbeafe" stop-opacity="0.78"/>',
        "</radialGradient>",
        "</defs>",
        '<rect width="100%" height="100%" rx="30" fill="url(#bg)"/>',
        f'<ellipse cx="{width / 2}" cy="{height / 2}" rx="{width * 0.43}" ry="{height * 0.35}" fill="url(#ellipseGlow)" stroke="#bfdbfe" stroke-opacity="0.55" stroke-width="1.2"/>',
    ]

    for item in placed:
        escaped = html.escape(item["name"])
        transform = (
            f'transform="translate({item["x"]} {item["y"]}) rotate({item["rotate"]})"'
            if item["rotate"]
            else ""
        )
        svg_parts.append(
            f'<text x="{item["x"] if not item["rotate"] else 0}" y="{item["y"] if not item["rotate"] else 0}" '
            f'{transform} text-anchor="middle" dominant-baseline="middle" '
            f'font-family="Microsoft YaHei, PingFang SC, sans-serif" font-size="{item["font_size"]}" '
            f'font-weight="{item["weight"]}" fill="{item["color"]}">{escaped}</text>'
        )

    if len(placed) < total:
        svg_parts.append(
            f'<text x="{width - 26}" y="{height - 20}" text-anchor="end" fill="#94a3b8" font-size="12" '
            'font-family="Microsoft YaHei, PingFang SC, sans-serif">仅展示高频技能</text>'
        )

    svg_parts.append("</svg>")
    return "".join(svg_parts)
