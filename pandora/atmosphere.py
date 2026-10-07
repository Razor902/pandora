# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Pandora level-1 effects — ATMOSPHERE. Unease only. Nothing startles.

Every effect takes (buf, h, w, tension, tick) and returns the buffer.
The buffer is a list of rows; each row is a list of cells; a normal cell
looks like (char, color_slot, bold). Cells are handled defensively: anything
that is not a (char, slot, bold)-shaped sequence passes through untouched,
and no effect ever raises on odd cell shapes.

Hard rule for this level: no effect may brighten, flash, or startle.
flicker_dim only ever dims — per-cell brightness can only go down.
"""

import math


# ---------------------------------------------------------------------------
# small helpers (shared with dread.py)
# ---------------------------------------------------------------------------

def _hash(row, col, seed):
    """Deterministic pseudo-random in [0, 1) for a cell and a seed."""
    x = (row * 73856093) ^ (col * 19349663) ^ (seed * 83492791)
    x &= 0xFFFFFFFF
    return (x % 10000) / 10000.0


def _split(cell):
    """Split a cell into (char, slot, bold). None for odd shapes."""
    if isinstance(cell, (tuple, list)) and len(cell) >= 1:
        ch = cell[0]
        if isinstance(ch, str) and len(ch) == 1:
            slot = cell[1] if len(cell) > 1 else ""
            bold = cell[2] if len(cell) > 2 else False
            return ch, slot, bool(bold)
    return None


def _join(cell, ch, slot, bold):
    """Rebuild a cell of the same type and shape, with new values."""
    parts = list(cell)
    parts[0] = ch
    if len(parts) > 1:
        parts[1] = slot
    if len(parts) > 2:
        parts[2] = bold
    return tuple(parts) if isinstance(cell, tuple) else parts


def _rows(buf):
    for row in buf:
        if isinstance(row, (list, tuple)):
            yield row


def _copy_buffer(buf):
    """Fresh list-of-lists copy. Cells are shared, never mutated in place."""
    out = []
    for row in buf:
        if isinstance(row, (list, tuple)):
            out.append(list(row))
        else:
            out.append(row)
    return out


# ---------------------------------------------------------------------------
# level-1 effects
# ---------------------------------------------------------------------------

_DRAIN_MAP = [
    ("white", "ash"),
    ("yellow", "ember"),
    ("green", "moss"),
    ("cyan", "slate"),
    ("blue", "abyss"),
    ("purple", "blood"),
    ("violet", "blood"),
    ("magenta", "blood"),
    ("volt", "ash"),
    ("gold", "rust"),
]


def _drain_slot(slot):
    """Map a bright color slot toward blood-red and black. Unknown slots are
    left alone — never invent a slot name the game doesn't know."""
    name = str(slot).lower()
    for bright, drained in _DRAIN_MAP:
        if bright in name:
            return name.replace(bright, drained)
    return None


def palette_drain(buf, h, w, tension, tick):
    """Colors desaturate toward blood-red and black as tension rises."""
    if tension <= 0:
        return buf
    out = _copy_buffer(buf)
    for ri, row in enumerate(_rows(out)):
        for ci in range(len(row)):
            parts = _split(row[ci])
            if not parts:
                continue
            ch, slot, bold = parts
            drained = _drain_slot(slot)
            if drained is not None and _hash(ri, ci, 11) < tension:
                row[ci] = _join(row[ci], ch, drained, bold and tension < 0.5)
    return out


def flicker_dim(buf, h, w, tension, tick):
    """Brief, slow, controlled dimming. Only ever dims — it blanks a sparse,
    slowly shifting subset of characters and clears bold. It never brightens
    a cell and never flashes the screen. That is a hard guarantee."""
    if tension <= 0:
        return buf
    phase = 0.5 + 0.5 * math.sin(tick * 0.12)  # slow breathing, ~52 ticks/cycle
    density = tension * phase * 0.30            # at most 30% of cells, at peak
    if density <= 0:
        return buf
    epoch = tick // 6                          # change slowly; no shimmer
    out = _copy_buffer(buf)
    for ri, row in enumerate(_rows(out)):
        for ci in range(len(row)):
            parts = _split(row[ci])
            if not parts:
                continue
            ch, slot, bold = parts
            if ch == " ":
                continue
            if _hash(ri, ci, 1000 + epoch) < density:
                row[ci] = _join(row[ci], " ", slot, False)
    return out


def vignette_creep(buf, h, w, tension, tick):
    """Darkness closes in from the edges as danger rises."""
    if tension <= 0 or h < 3 or w < 3:
        return buf
    depth = 1 + int(tension * 3)  # how far the dark reaches inward
    out = _copy_buffer(buf)
    for ri, row in enumerate(_rows(out)):
        for ci in range(len(row)):
            edge = min(ri, h - 1 - ri, ci, len(row) - 1 - ci)
            if edge >= depth:
                continue
            closeness = 1.0 - (edge / depth)  # 1.0 at the rim
            parts = _split(row[ci])
            if not parts:
                continue
            ch, slot, bold = parts
            if ch == " ":
                continue
            if _hash(ri, ci, 77) < closeness * tension:
                row[ci] = _join(row[ci], " ", slot, False)
    return out


_ROT_GLYPHS = list("░▒▓#%&?*+=~¿¡")


def text_rot(buf, h, w, tension, tick):
    """Dialogue and banners glitch and corrupt, slowly. Spaces and layout
    are never touched — only letters and digits rot."""
    if tension <= 0:
        return buf
    epoch = tick // 12
    density = tension * 0.12
    out = _copy_buffer(buf)
    for ri, row in enumerate(_rows(out)):
        for ci in range(len(row)):
            parts = _split(row[ci])
            if not parts:
                continue
            ch, slot, bold = parts
            if not ch.isalnum():
                continue
            r = _hash(ri, ci, 500 + epoch)
            if r < density:
                glyph = _ROT_GLYPHS[int(r / density * len(_ROT_GLYPHS))
                                   % len(_ROT_GLYPHS)]
                row[ci] = _join(row[ci], glyph, slot, False)
    return out


def drone_pattern(tension, tick):
    """Haptic pulse pattern as pure data. The game layer may map this to
    termux-vibrate or similar. Pandora never executes it."""
    t = max(0.0, min(1.0, float(tension)))
    return {
        "type": "drone",
        "intensity": round(t, 2),
        "interval_ms": int(1400 - 900 * t),
        "pulse_ms": int(80 + 120 * t),
    }


def drone(buf, h, w, tension, tick):
    """Level-1 drone. The visual buffer passes through untouched; the pulse
    pattern is available via drone_pattern()."""
    return buf
