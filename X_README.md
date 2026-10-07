# X marks the spot — the PythonX bridge for Pandora's Box

**`pandora_x.py`** · Status: GATHERED · Educational model only

## The lore

Curtis's words: *the X in PythonX is derived from a cross.* X marks the
spot — so this module makes treasure maps. A message goes in, wrapped in
2 to 4 encoding layers; the same PythonX engine that unwraps payloads
digs it back up. Bury the treasure, mark the spot, dig it up.

## The two doors

```python
from pandora.pandora_x import hide, reveal

payload, answer_key = hide("x marks the spot", seed=7)
# payload: the buried bytes (readable text -- see the envelope rule)
# answer_key: [{"layer": "rot", "n": 8}, ...] innermost first --
#             keep it separate from the payload, like a real map

result = reveal(payload)
# {"refused": False, "message": "x marks the spot",
#  "path": [...], "states_tried": N, "seconds": S}
```

With the box attached, the bridge reads its status word:

```python
result = reveal(payload, box=box)   # box must read SAFE, or this refuses
```

## The mapmaker's promise

`hide()` test-digs every map with the real engine before selling it.
Random plans are re-rolled until the dig comes back clean; an explicit
layer stack that doesn't dig clean is refused honestly -- the map won't
be sold broken. Every map `hide()` sells can be dug up. (The beam search
is heuristic: some layer stacks lose the trail. The bridge doesn't argue
with the engine -- it just won't sell those maps.)

## The envelope rule

The outermost layer is always base64 or hex -- readable text. Two honest
reasons: a map you can't copy by hand isn't a map, and the triage gate
correctly calls raw random-looking bytes noise and refuses them.

## Safety -- his rules, never weakened

- `reveal(box=...)` **refuses unless the box reads SAFE.** No digging
  while a session is live (ARMED), after the breaker has fired
  (TRIPPED), or in any other non-quiet state.
- The bridge only **reads** the status word (duck-typed -- it never even
  imports the defense stack). It cannot touch the guardrails, the
  thresholds, the biometric breaker, or the kill switch.
- The triage gate still applies: noise is refused, in plain words.
- This is encode/decode of Curtis's own content. No new capability
  against anyone else's systems -- the layers are textbook wraps.

## The layers

base64 · hex · rot (1-25) · atbash mirror · xor (key 1-255).
Atbash and XOR are their own undoing -- mirror a mirror and the words
come back. The beam finds XOR keys on its own; the answer key records
them anyway, because a map keeps its key separate.

## Run the tests

```
cd ~/workspace/arcade && python3 -m pandora.test_pandora_x
```

28 tests: round trips across seeds, explicit stacks, the envelope rule,
triage refusals, the SAFE gate (ARMED/TRIPPED/DISARMED all refuse),
key discovery, and honest answer keys.

## Limits, stated plainly

- The engine is heuristic: not every layer stack digs clean (hence the
  mapmaker's promise -- bad stacks are refused, not sold).
- This is a classroom bridge on the bench, not a hardened vault. The
  answer key is the secret -- whoever holds map AND key finds the words.
- The Pandora vision (the dream machine, paradise, Neuralink) is Curtis's
  dream, not a build order. This bridge serves the box as it exists:
  guarded content, guarded sessions, guarded digs.

---
© 2026 Curtis Ray Dyess · Crimson Rose LLC
