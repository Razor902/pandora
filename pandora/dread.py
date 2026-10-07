# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Pandora level-2 effects — DREAD. Tension events. Nothing pops.

Same buffer contract as atmosphere: each effect takes (buf, h, w, tension,
tick) and returns the buffer, never crashes on odd cell shapes, and never
startles. presence() is the strictest one — edge cells only, fading in over
~150 ticks, never the center, never sudden.
"""

from .atmosphere import _hash, _split, _join, _rows, _copy_buffer


def presence(buf, h, w, tension, tick):
    """Something wrong at the screen EDGES. It fades in over about 150
    ticks — never sudden — and never appears in the center of the screen."""
    if tension <= 0 or h < 4 or w < 6:
        return buf
    fade = min(1.0, tick / 150.0) * tension
    if fade < 0.2:
        return buf
    # edge cells only: top/bottom two rows, or within 3 columns of the sides
    spots = [(0, 2), (0, w - 3), (h - 1, 2), (h - 1, w - 3),
             (1, 1), (1, w - 2), (h - 2, 1), (h - 2, w - 2)]
    n = 1 + int(tension * (len(spots) - 1))
    glyphs = ["·", "•", "◉"]
    glyph = glyphs[min(len(glyphs) - 1, int(fade * len(glyphs)))]
    out = _copy_buffer(buf)
    for ri, ci in spots[:n]:
        if ri >= len(out):
            continue
        row = out[ri]
        if ci >= len(row):
            continue
        parts = _split(row[ci])
        if not parts:
            continue
        ch, slot, bold = parts
        row[ci] = _join(row[ci], glyph, slot, False)
    return out


def pursuit_cues(buf, h, w, tension, tick):
    """The world reacts to being hunted: a quiet marker circling the bottom
    edge. It only ever writes onto empty cells — never over the game's own
    visuals."""
    if tension < 0.25 or h < 2 or w < 4:
        return buf
    out = _copy_buffer(buf)
    row = out[h - 1]
    pos = (tick // 25) % w
    marks = [pos, (pos + w // 2) % w] if tension > 0.6 else [pos]
    for ci in marks:
        if ci >= len(row):
            continue
        parts = _split(row[ci])
        if not parts:
            continue
        ch, slot, bold = parts
        if ch != " ":
            continue
        row[ci] = _join(row[ci], "•", slot, False)
    return out


def heartbeat_phase(tension, tick):
    """Pacing phase 0.0-1.0 synced to tension. The game layer can map this
    to haptics; the visual layer uses it for a soft swell."""
    t = max(0.0, min(1.0, float(tension)))
    period = max(20, int(70 - 50 * t))  # faster heart at higher tension
    phase = (tick % period) / period
    if phase < 0.15:
        return phase / 0.15
    return max(0.0, 1.0 - (phase - 0.15) / 0.85)


def heartbeat(buf, h, w, tension, tick):
    """Pacing layer synced to tension. A soft visual swell — felt, never
    popping. At most it quiets bold on a few cells during the beat."""
    if tension <= 0:
        return buf
    strength = heartbeat_phase(tension, tick)
    if strength <= 0:
        return buf
    out = _copy_buffer(buf)
    epoch = tick // 2
    for ri, row in enumerate(_rows(out)):
        for ci in range(len(row)):
            parts = _split(row[ci])
            if not parts:
                continue
            ch, slot, bold = parts
            if ch == " " or not bold:
                continue
            if _hash(ri, ci, 900 + epoch) < 0.10 * strength * tension:
                row[ci] = _join(row[ci], ch, slot, False)
    return out
