# The Three-Layer Wallet

© 2026 Curtis Ray Dyess · Crimson Rose LLC

Curtis's order (2026-10-07): *"Create a three layer wallet. for the currency."*

This is an **educational standalone model** — a classroom wallet for the mandala
currency. Demo fingerprints, demo mandalas, no value, no network. The real
identity binding, the real custody, and the real administrator process are
Curtis's to wire in.

---

## The three layers, in plain words

**Layer 1 — THE HAND (pocket).**
Carries the citizen's earned mandala. When a citizen proves themselves, one
mandala lands in the hand. At any shop, the citizen *shows* it and takes one
thing — and the hand keeps it. There is **no spend path out of the hand**, by
design. `spend_from_hand()` exists only to refuse, loudly. The law lives in
the code: shown, not spent.

**Layer 2 — THE VAULT (savings).**
This is where the Multiplication Law lives. When two wallets handshake, each
vault multiplies by the *other* side's swarm count: your vault times their
swarm, their vault times yours. Vault mandalas move citizen to citizen inside
Pandora. An empty vault stays empty — the law multiplies what is there; it
does not create from nothing.

**Layer 3 — THE RESERVE (cold).**
The deep reserve that backs the currency. Nothing moves here without
administrator approval: `by_admin=True` **and** `approved_by="Curtis Ray Dyess"`,
the same pattern the paradigm module uses for the things only he can approve.
The parents hold the access; he holds the final word.

## The laws, as code

| Curtis's law | How the wallet enforces it |
|---|---|
| **Mandala law** — prove yourself → earn one → show it at any shop | `earn_mandala()` issues into the hand; `show_mandala()` returns a display receipt and the balance never moves |
| **Multiplication Law** — handshakes multiply both parties | `handshake()` multiplies each vault by the other side's swarm count |
| **Nola's Law** — no lies, no deception | Every movement is written to an append-only ledger; `reconcile()` replays the ledger from the first entry and raises `DiscrepancyError` on ANY disagreement — never silently |
| **Proof-of-self** — the fingerprint is what the citizen carries | The wallet binds to the citizen's fingerprint at creation; every sensitive operation must present the matching print, or the wallet stays shut |
| **Paradigm admin law** — administrator access for the deep things | The reserve moves only with `by_admin=True` and Curtis's approval |

## Assumptions (GATHERED — Curtis has not ruled on these)

- One earn = one mandala. He sets the real issuance.
- Swarm counts are positive whole numbers. He defines what a "swarm count" is.
- The fingerprint here is a demo token string. Production fingerprint capture,
  encryption, consent, revocation, and storage are **not built**.
- The ledger is in-memory. A real chain-backed ledger is his to wire in.

## Open tension — his ruling needed

`threshold.py` treats one mandala as an entry fee moved to the treasury when a
citizen steps inside. Curtis's mandala law says the mandala is **shown, not
consumed**. This wallet enforces the shown-not-spent law on the hand and takes
no side on the fee question. Nothing here is canonical until he says it stands.

## Files

- `wallet.py` — the `ThreeLayerWallet` class (stdlib only)
- `test_wallet.py` — 20 tests: layer separation, hand display-never-spends,
  handshake multiplication, reserve admin approval, fingerprint binding,
  ledger reconciliation, Nola's-law discrepancy detection
- `WALLET.md` — this document
