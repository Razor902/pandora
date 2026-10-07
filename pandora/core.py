# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Pandora platform core — the pluggable scare engine (DLC tier).

Wraps a game's update()/render() methods in memory only. Never touches game
files on disk. The default state after attach() is DISARMED: the engine does
nothing until arm() is called. That is the hard safety rule.

Levels: 1 = atmosphere, 2 = dread. Level 3 (startle) ships later, behind
Curtis's consent gate, and is not built here.
"""

from contextlib import contextmanager

from . import atmosphere, dread


class Engine:
    """The scare engine. Clip onto a game, arm it, unclip clean."""

    LEVELS = (1, 2)

    def __init__(self, level=1):
        if level not in self.LEVELS:
            raise ValueError(
                "Pandora Engine level must be 1 (atmosphere) or 2 (dread); "
                "got %r" % (level,)
            )
        self._level = level
        self._tension = 0.0
        self._armed = False
        self._attached = False
        self._game = None
        self._orig_update = None
        self._orig_render = None
        self._tick = 0
        # Latest haptic pattern as pure data. The game layer may map it to
        # termux-vibrate or similar. Pandora never executes it.
        self.last_drone = None

    # -- level: set at construction, never escalated ---------------------
    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        if value not in self.LEVELS:
            raise ValueError(
                "Pandora Engine level must be 1 or 2; got %r" % (value,)
            )
        if value > self._level:
            raise ValueError(
                "Pandora Engine level can never be escalated "
                "(%d -> %d denied)" % (self._level, value)
            )
        self._level = value  # de-escalation is always safe

    # -- tension: 0.0 - 1.0, clamped ------------------------------------
    @property
    def tension(self):
        return self._tension

    @tension.setter
    def tension(self, value):
        try:
            v = float(value)
        except (TypeError, ValueError):
            raise TypeError(
                "Pandora Engine tension must be a number; got %r" % (value,)
            )
        self._tension = max(0.0, min(1.0, v))

    @property
    def is_attached(self):
        return self._attached

    @property
    def is_armed(self):
        return self._armed

    # -- plug / unplug ----------------------------------------------------
    def attach(self, game):
        """Wrap the game's update(dt) and render(buf) in memory.

        The game plays exactly as before until arm() is called.
        """
        if self._attached:
            raise RuntimeError(
                "Pandora Engine is already attached — detach() first"
            )
        update = getattr(game, "update", None)
        render = getattr(game, "render", None)
        if not callable(update) or not callable(render):
            raise TypeError(
                "Pandora Engine needs a game with callable update(dt) and "
                "render(buf); got %r" % (type(game).__name__,)
            )
        self._orig_update = update
        self._orig_render = render
        self._game = game

        engine = self

        def _pandora_update(*args, **kwargs):
            engine._orig_update(*args, **kwargs)
            if engine._armed:
                engine._tick += 1

        def _pandora_render(*args, **kwargs):
            result = engine._orig_render(*args, **kwargs)
            buf = None
            if args and isinstance(args[0], list):
                buf = args[0]
            elif isinstance(kwargs.get("buf"), list):
                buf = kwargs["buf"]
            if buf is None or not engine._armed:
                return result if result is not None else buf
            return engine._apply(buf)

        _pandora_update.__name__ = "pandora_update"
        _pandora_render.__name__ = "pandora_render"
        game.update = _pandora_update
        game.render = _pandora_render
        self._attached = True
        return self

    def detach(self):
        """Unwrap the game. The exact original method objects are restored
        (verified by identity). The game is byte-for-byte as it was."""
        if not self._attached:
            raise RuntimeError(
                "Pandora Engine is not attached — nothing to detach"
            )
        game = self._game
        game.update = self._orig_update
        game.render = self._orig_render
        assert game.update is self._orig_update, \
            "pandora: update() was not restored cleanly"
        assert game.render is self._orig_render, \
            "pandora: render() was not restored cleanly"
        self._game = None
        self._orig_update = None
        self._orig_render = None
        self._attached = False
        self._armed = False
        self.last_drone = None
        return self

    # -- arm / disarm / kill ----------------------------------------------
    def arm(self):
        """Enable effects. The one explicit decision that turns scary on."""
        self._armed = True
        return self

    def disarm(self):
        """Disable effects instantly. Wrapped methods behave exactly like
        the originals again — effects contribute nothing."""
        self._armed = False
        return self

    def kill(self):
        """Permanent off switch: disarm AND detach in one call."""
        self._armed = False
        if self._attached:
            self.detach()
        return self

    # -- effect chain -------------------------------------------------------
    def _chain(self):
        chain = [
            atmosphere.palette_drain,
            atmosphere.flicker_dim,
            atmosphere.vignette_creep,
            atmosphere.text_rot,
        ]
        if self._level >= 2:
            chain += [
                dread.presence,
                dread.pursuit_cues,
                dread.heartbeat,
            ]
        return chain

    def _apply(self, buf):
        h = len(buf)
        w = 0
        for row in buf:
            try:
                w = max(w, len(row))
            except TypeError:
                pass
        out = buf
        for fx in self._chain():
            out = fx(out, h, w, self._tension, self._tick)
        self.last_drone = atmosphere.drone_pattern(self._tension, self._tick)
        return out


@contextmanager
def armed(game, level=1):
    """Arm the engine for a block only. Always disarms and detaches on exit,
    even if the block raises.

        with armed(game, level=2):
            ...  # dread inside this block only
    """
    engine = Engine(level)
    engine.attach(game)
    engine.arm()
    try:
        yield engine
    finally:
        engine.kill()
