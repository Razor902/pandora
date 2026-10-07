# © 2026 Curtis Ray Dyess · Crimson Rose LLC
#!/usr/bin/env python3
"""Tests for pandora_x -- the PythonX bridge. All must pass, every time.

Run:  cd ~/workspace/arcade && python3 -m pandora.test_pandora_x
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pandora.pandora_x import hide, reveal, describe_key, PandoraXError

_PASS = 0
_FAIL = 0


def check(name, cond, detail=""):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("[ok ] %s" % name)
    else:
        _FAIL += 1
        print("[FAIL] %s %s" % (name, detail))


class _FakeBox(object):
    """Stands in for PandoraDefense -- the bridge only reads status_word."""
    def __init__(self, word):
        self.status_word = word


# 1. Round trips: bury it, dig it up, words come back ---------------------
for seed in (1, 7, 42, 99, 1234):
    payload, key = hide("the engineer marks the spot", seed=seed)
    result = reveal(payload)
    check("round trip seed=%d" % seed,
          not result["refused"] and result["message"] == "the engineer marks the spot",
          "got %r path=%r" % (result["message"], result["path"]))
    check("envelope is text seed=%d" % seed,
          key[-1]["layer"] in ("base64", "hex"))

# 2. Explicit layers -------------------------------------------------------
payload, key = hide("cross the beams", layers=["xor", "base64"])
result = reveal(payload)
check("explicit [xor, base64] round trip",
      not result["refused"] and result["message"] == "cross the beams",
      "got %r" % (result["message"],))

payload, key = hide("mirror mirror", layers=[{"layer": "rot", "n": 13}, "atbash", "hex"])
result = reveal(payload)
check("explicit [rot13, atbash, hex] round trip",
      not result["refused"] and result["message"] == "mirror mirror",
      "got %r path=%r" % (result["message"], result["path"]))

# 3. The key is honest: same message + different keys -> different maps -----
# (Explicit stacks that don't dig clean are refused honestly, so collect
# two sellable ones first.)
sellable = []
for k in (11, 42, 73, 101, 173, 200, 233):
    try:
        sellable.append((k,) + hide("same map",
                                    layers=[{"layer": "xor", "key": k}, "hex"]))
        if len(sellable) == 2:
            break
    except PandoraXError:
        continue
check("two sellable xor maps found", len(sellable) == 2)
_FIRST_SELLABLE = sellable[0] if sellable else None
if len(sellable) == 2:
    (k1, p1, key1), (k2, p2, key2) = sellable
    check("different keys -> different payloads", p1 != p2)
    check("answer key carries the real params",
          key1[0] == {"layer": "xor", "key": k1}
          and key2[0] == {"layer": "xor", "key": k2},
          "%r %r" % (key1, key2))

# 4. The envelope rule: raw noise outside is refused at hide() -------------
try:
    hide("nope", layers=["base64", "xor"])
    check("non-text outermost refused", False, "hide() allowed it")
except PandoraXError:
    check("non-text outermost refused", True)

# 5. Triage still guards reveal(): noise is refused, in plain words --------
r = reveal(b"")
check("empty payload refused", r["refused"] and r["message"] is None, str(r["reason"]))
r = reveal(b"\x00" * 64)
check("filler payload refused by triage",
      r["refused"] and "triage" in r["reason"], str(r["reason"]))

# 6. The box gate: SAFE digs, anything else refuses ------------------------
payload, _ = hide("quiet words", seed=3)
r = reveal(payload, box=_FakeBox("SAFE"))
check("SAFE box allows reveal", not r["refused"] and r["message"] == "quiet words")
r = reveal(payload, box=None)
check("no box (bench) allows reveal", not r["refused"])
for word in ("ARMED", "TRIPPED", "DISARMED"):
    try:
        reveal(payload, box=_FakeBox(word))
        check("%s box refuses reveal" % word, False, "no refusal raised")
    except PandoraXError as e:
        check("%s box refuses reveal" % word, "not SAFE" in str(e), str(e))

# 7. No key needed: the beam finds the XOR key on its own -------------------
# Take the first sellable explicit xor map from test 3 and dig it --
# the beam was never told the key.
check("an explicit xor map was sellable", _FIRST_SELLABLE is not None)
if _FIRST_SELLABLE is not None:
    k, payload, key = _FIRST_SELLABLE
    r = reveal(payload)
    check("xor key %d found without being told" % k,
          not r["refused"] and r["message"] == "same map",
          "got %r path=%r" % (r["message"], r["path"]))
    check("answer key records the true key", key[0] == {"layer": "xor", "key": k},
          str(key))

# 8. describe_key speaks plainly --------------------------------------------
lines = describe_key([{"layer": "xor", "key": 42}, {"layer": "base64"}])
check("describe_key plain words",
      lines == ["1. XOR mask, key 42", "2. base64 envelope"], str(lines))

# 9. hide() needs real words -------------------------------------------------
try:
    hide("")
    check("empty message refused", False)
except PandoraXError:
    check("empty message refused", True)

print("\n%d passed, %d failed" % (_PASS, _FAIL))
sys.exit(1 if _FAIL else 0)
