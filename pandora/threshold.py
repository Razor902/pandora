# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — NOT A PRODUCTION ACCESS SYSTEM.
# A classroom model of Curtis's entry law for Pandora's Box. Demo citizens,
# demo mandalas, a demo box. The real registry, the real fee, and the real
# box are his to wire in.
# ============================================================================
"""The entry threshold of Pandora's Box -- what it takes to step inside.

Curtis's law (2026-10-07, his words):
    "The mandala is a currency used in Pandora. Each citizen that proves
    their self earns one mandala. That will get them one thing out of any
    shop -- they just have to show it."

And his term, asterisk-marked: "My mandala."

Three gates. All three must open, or the citizen does not step inside:

    1. PROOF-OF-SELF -- the citizen is registered as having proven
       themselves. The registry here is a demo with clearly fictional
       citizens; the real registry is Curtis's to build.
    2. THE MANDALA SHOWN -- the citizen holds at least the entry fee.
       Default: 1 mandala buys one step inside -- his one-mandala-one-thing
       law. The fee is a tunable parameter (ASSUMED); he sets the real one.
       On entry the fee moves to the box treasury, written on the chain.
    3. THE BOX IS SAFE -- the box reads SAFE. Duck-typed on purpose: this
       module reads status_word and never imports the defense stack, so it
       can never weaken the guardrails. ARMED, TRIPPED, DISARMED -- or no
       box at all -- refuse entry, in plain words.

TREASURY HANDOFF: the fee goes to the holder id "pandora-treasury" on the
chain -- the same id used by mandala-economy/pandora_treasury.py (built in
parallel). One treasury, one id, both modules feed it.
"""

import time

ENTRY_FEE = 1  # ASSUMED -- Curtis sets the real price of a step inside.
TREASURY_HOLDER = "pandora-treasury"  # shared id; see module docstring.

SAFE_WORD = "SAFE"


class ThresholdError(Exception):
    """Raised when entry is refused -- carries the plain-words reasons."""
    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("Entry refused: " + "; ".join(self.reasons))


class FakeCitizenBox:
    """Bench stand-in for a box: anything with a status_word works."""
    def __init__(self, word="SAFE"):
        self.status_word = word


class EntryThreshold:
    """The three gates of Pandora's Box."""

    def __init__(self, contract, entry_fee=ENTRY_FEE,
                 treasury_holder=TREASURY_HOLDER, box=None, clock=None):
        self.contract = contract
        self.entry_fee = entry_fee
        self.treasury_holder = treasury_holder
        self.box = box
        self.clock = clock or time.time
        self.proven = set()  # citizen ids registered as proven (demo registry)

    # -- gate 1: proof of self ------------------------------------------------
    def register_proven(self, citizen_id):
        """Mark a citizen as having proven themselves. Demo registry."""
        self.proven.add(citizen_id)

    def is_proven(self, citizen_id):
        return citizen_id in self.proven

    # -- the three gates -------------------------------------------------------
    def check_entry(self, citizen_id):
        """Test all three gates. Returns (allowed: bool, reasons: list).

        Reasons name every gate that closed, in plain words -- so a
        refused citizen knows exactly what to fix.
        """
        reasons = []

        # Gate 1: proof of self.
        if not self.is_proven(citizen_id):
            reasons.append(
                "Gate 1 closed (proof-of-self): '%s' is not registered as "
                "proven. Prove yourself first; the mandala is earned, not "
                "given." % citizen_id)

        # Gate 2: the mandala shown.
        held = self.contract.balances_of(citizen_id)["unlocked"]
        if held < self.entry_fee:
            reasons.append(
                "Gate 2 closed (the mandala): '%s' holds %s mandala, but the "
                "step inside costs %s. One mandala, one step -- that is the "
                "law." % (citizen_id, held, self.entry_fee))

        # Gate 3: the box is safe. Duck-typed -- read the word, never touch
        # the defense stack. No box, no entry: a door with no box behind it
        # stays shut.
        word = getattr(self.box, "status_word", None)
        if word != SAFE_WORD:
            if word is None:
                reasons.append(
                    "Gate 3 closed (the box): no box is attached, so SAFE "
                    "cannot be read. The door stays shut until the box "
                    "itself says SAFE.")
            else:
                reasons.append(
                    "Gate 3 closed (the box): the box reads %s, not SAFE. "
                    "Nobody steps inside while a session is live, after the "
                    "breaker has fired, or in any non-quiet state. Quiet the "
                    "box first." % word)

        return (len(reasons) == 0, reasons)

    def enter(self, citizen_id):
        """Step inside: run the gates, move the fee, hand back a receipt.

        On pass, the entry fee transfers citizen -> treasury on the chain
        and a receipt comes back. On fail, ThresholdError speaks plainly.
        """
        allowed, reasons = self.check_entry(citizen_id)
        if not allowed:
            raise ThresholdError(reasons)
        self.contract.transfer(citizen_id, self.treasury_holder, self.entry_fee)
        return {
            "citizen": citizen_id,
            "fee": self.entry_fee,
            "treasury": self.treasury_holder,
            "entered_at": self.clock(),
            "box_word": getattr(self.box, "status_word", None),
        }


def demo():
    """Walk a citizen through the three gates, on the bench."""
    import sys
    sys.path.insert(0, "/home/hatch/workspace/mandala-chain")
    from mandala import MandalaContract
    from chain import Chain

    chain = Chain()
    contract = MandalaContract(minter="curtis", chain=chain)
    contract.mint("aya", 1, by="curtis")

    gate = EntryThreshold(contract, box=FakeCitizenBox("SAFE"))
    gate.register_proven("aya")

    allowed, reasons = gate.check_entry("aya")
    print("check:", allowed, reasons)
    receipt = gate.enter("aya")
    print("receipt:", receipt)
    print("aya holds:", contract.balances_of("aya"))
    print("treasury holds:", contract.balances_of(TREASURY_HOLDER))
    print("chain valid:", chain.verify_chain()[0])


if __name__ == "__main__":
    demo()
