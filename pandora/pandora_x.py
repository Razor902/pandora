# © 2026 Curtis Ray Dyess · Crimson Rose LLC
#!/usr/bin/env python3
"""
pandora_x.py -- "X marks the spot": the PythonX bridge for Pandora's Box.

Curtis's lore, his words: the X in PythonX is derived from a cross.
X marks the spot -- so this module makes treasure maps. A message goes
in, wrapped in 2 to 4 encoding layers; the same PythonX engine that
unwraps payloads digs it back up. Bury the treasure, mark the spot,
dig it up.

Two doors:
    hide(message)          -> (payload, answer_key)   bury it
    reveal(payload, box)   -> result dict             dig it up

The layers are textbook wraps, nothing exotic: base64, hex, letter
rotation, the atbash mirror alphabet, XOR with a key. The answer key
is kept separate, like a real map -- whoever holds the map AND the
key finds the treasure.

Safety -- his rules, enforced here, never weakened:
  * reveal() with a box attached REFUSES unless the box reads SAFE.
    No digging while a scare session is live (ARMED), after the breaker
    has fired (TRIPPED), or in any other non-quiet state. This module
    only READS the status word -- it never touches the guardrails,
    the thresholds, the biometric breaker, or the kill switch.
  * reveal() without a box is bench use: pure PythonX decipher.
  * The triage gate still applies: noise is refused, in plain words.
  * Encode/decode of Curtis's own content only. No new capability
    against anyone else's systems.

EDUCATIONAL MODEL ONLY.
"""

import base64
import binascii
import os
import random
import sys

# Find the PythonX engine next to this package: ~/workspace/pythonx.
# (Same path-hack style as pandora_defense.py -- the box and the
# engine live side by side in the workspace, not in site-packages.)
_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "pythonx"))

import pythonx13 as _px  # noqa: E402 -- the decipher engine, triage gate wired in

__version__ = "1.0.0"


class PandoraXError(Exception):
    """The bridge refusing, in plain language."""


# ---------------------------------------------------------------------------
# The wraps: one layer on (hide), PythonX peels them off (reveal).
# Each wrap takes bytes and returns bytes. atbash and xor are their own
# undoing -- mirror a mirror and the words come back.
# ---------------------------------------------------------------------------

def _wrap_b64(data):
    return base64.b64encode(data)


def _wrap_hex(data):
    return binascii.hexlify(data)


def _wrap_rot(data, n):
    return _px._rot(data, n)


def _wrap_atbash(data):
    return _px._atbash(data)


def _wrap_xor(data, key):
    return _px._xor(data, key)


# The envelope rule: the OUTERMOST layer must always be readable text
# (base64 or hex). Two reasons, both honest:
#   1. A treasure map you can't copy by hand isn't a map -- it's static.
#   2. The triage gate correctly calls raw random-looking bytes noise
#      and refuses them. Text on the outside keeps the gate honest.
_TEXT_ENVELOPES = ("base64", "hex")


def _random_layers(rng):
    """Pick 2-4 layers, innermost first, text envelope outermost."""
    pool = ["base64", "hex", "rot", "atbash", "xor"]
    count = rng.randint(2, 4)
    inner = [rng.choice(pool) for _ in range(count - 1)]
    outer = rng.choice(list(_TEXT_ENVELOPES))
    return inner + [outer]


def _apply_layer(data, spec, rng):
    """Apply one layer. spec is a name, or {"layer": name, ...params}."""
    if isinstance(spec, dict):
        name = spec["layer"]
        params = {k: v for k, v in spec.items() if k != "layer"}
    else:
        name, params = spec, {}
    if name == "base64":
        return _wrap_b64(data), {"layer": "base64"}
    if name == "hex":
        return _wrap_hex(data), {"layer": "hex"}
    if name == "rot":
        n = params.get("n", rng.randint(1, 25))
        return _wrap_rot(data, n), {"layer": "rot", "n": n}
    if name == "atbash":
        return _wrap_atbash(data), {"layer": "atbash"}
    if name == "xor":
        key = params.get("key", rng.randint(1, 255))
        return _wrap_xor(data, key), {"layer": "xor", "key": key}
    raise PandoraXError("Unknown layer %r -- pick from: base64, hex, rot, "
                        "atbash, xor." % (name,))


def _build_map(data, plan, rng):
    """Wrap data in the plan's layers. Returns (payload, answer_key)."""
    answer_key = []
    for spec in plan:
        data, used = _apply_layer(data, spec, rng)
        answer_key.append(used)
    return data, answer_key


def _digs_clean(payload, message):
    """The mapmaker's promise: run the real dig, check the words come back."""
    out, path, _, _ = _px.decipher_beam(payload)
    if path == ["triage: skipped as noise"]:
        return False
    try:
        return out.decode("utf-8") == message
    except UnicodeDecodeError:
        return False


def _check_envelope(plan):
    """The envelope rule, enforced even on explicit plans: the outermost
    layer must be readable text, or the triage gate will (correctly)
    call the payload noise."""
    last = plan[-1]
    last_name = last["layer"] if isinstance(last, dict) else last
    if last_name not in _TEXT_ENVELOPES:
        raise PandoraXError(
            "The outermost layer must be base64 or hex -- a map has to be "
            "readable text, and the triage gate refuses raw noise.")


def hide(message, layers=None, seed=None, _max_tries=12):
    """Bury the treasure.

    message: the words to hide (str).
    layers:  optional explicit layers, innermost first --
             ["xor", "base64"] or [{"layer": "rot", "n": 13}, "base64"].
             Omitted: 2-4 random layers, text envelope outermost.
    seed:    optional random seed, so a map can be remade exactly.

    Returns (payload_bytes, answer_key). The answer key lists every
    layer in the order applied (innermost first) with its parameters --
    keep it separate from the payload, like a real map.

    The mapmaker's promise: hide() test-digs every map with the real
    engine before selling it. Random plans are re-rolled until the dig
    comes back clean (up to _max_tries); an explicit plan that doesn't
    dig clean is refused honestly instead of sold broken.
    """
    if not isinstance(message, str) or not message:
        raise PandoraXError("hide() needs a non-empty message to bury.")
    rng = random.Random(seed)
    data0 = message.encode("utf-8")
    if layers is not None:
        plan = list(layers)
        if not (2 <= len(plan) <= 6):
            raise PandoraXError("2 to 6 layers -- fewer is no map, more is a maze.")
        _check_envelope(plan)
        payload, answer_key = _build_map(data0, plan, rng)
        if not _digs_clean(payload, message):
            raise PandoraXError(
                "That exact layer stack doesn't dig clean through the "
                "engine -- the beam loses the trail. Try a different "
                "stack; the map won't be sold broken.")
        return payload, answer_key
    for _ in range(_max_tries):
        plan = _random_layers(rng)
        payload, answer_key = _build_map(data0, plan, rng)
        if _digs_clean(payload, message):
            return payload, answer_key
    raise PandoraXError(
        "Couldn't bury a diggable map in %d tries -- the engine keeps "
        "losing the trail. Try again; the map won't be sold broken."
        % _max_tries)


def _gate_for_box(box):
    """The one safety rule of this bridge: the box must read SAFE.

    Duck-typed on purpose -- this module never imports the defense
    stack, so it can never disturb it. It only reads the status word.
    """
    if box is None:
        return  # bench use: no box, no gate
    word = getattr(box, "status_word", None)
    if word != "SAFE":
        raise PandoraXError(
            "The box reads %s -- not SAFE. The bridge refuses to dig "
            "while a session is live, after the breaker has fired, or "
            "in any non-quiet state. Quiet the box first." % (word,))


def reveal(payload, box=None):
    """Dig up the treasure.

    payload: the buried bytes from hide().
    box:     optional Pandora's Box (anything with a status_word).
             When given, the box MUST read SAFE or this refuses --
             no digging during a live session or after a trip.

    Returns a dict:
        refused     -- True when the gate or triage said no
        reason      -- plain-language why (when refused)
        message     -- the dug-up words (str), or None
        path        -- the layer path PythonX walked, outermost first
        states_tried, seconds -- what the dig cost
    """
    _gate_for_box(box)
    if not isinstance(payload, (bytes, bytearray)) or not payload:
        return {"refused": True,
                "reason": "Nothing to dig -- the payload is empty.",
                "message": None, "path": [],
                "states_tried": 0, "seconds": 0.0}
    out, path, tried, secs = _px.decipher_beam(bytes(payload))
    if path == ["triage: skipped as noise"]:
        return {"refused": True,
                "reason": "The triage gate called it noise and refused "
                          "to spend the search on it. A real map wears "
                          "a readable envelope -- base64 or hex outside.",
                "message": None, "path": path,
                "states_tried": tried, "seconds": secs}
    try:
        message = out.decode("utf-8")
    except UnicodeDecodeError:
        message = None
    return {"refused": False, "reason": None, "message": message,
            "path": path, "states_tried": tried, "seconds": secs}


def describe_key(answer_key):
    """One plain-language line per layer, innermost first."""
    lines = []
    for i, used in enumerate(answer_key, 1):
        name = used["layer"]
        if name == "rot":
            lines.append("%d. letter rotation, %d steps" % (i, used["n"]))
        elif name == "xor":
            lines.append("%d. XOR mask, key %d" % (i, used["key"]))
        elif name == "atbash":
            lines.append("%d. atbash mirror alphabet" % i)
        elif name == "base64":
            lines.append("%d. base64 envelope" % i)
        elif name == "hex":
            lines.append("%d. hex envelope" % i)
    return lines


if __name__ == "__main__":
    payload, key = hide("x marks the spot", seed=7)
    print("buried : %r" % (payload[:64],))
    for line in describe_key(key):
        print("key    : " + line)
    result = reveal(payload)
    print("dug up : %r" % (result["message"],))
    print("path   : %s" % (" -> ".join(result["path"]) or "(already plain)",))
