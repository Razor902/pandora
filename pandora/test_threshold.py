# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — tests for the entry threshold (threshold.py).
# ============================================================================
"""Every gate, every refusal, and the fee's honest accounting."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/hatch/workspace/mandala-chain")

from threshold import EntryThreshold, ThresholdError, FakeCitizenBox, TREASURY_HOLDER
from mandala import MandalaContract
from chain import Chain as MandalaChain

MINTER = "curtis"


def fresh(fee=1, box_word="SAFE", with_chain=True):
    chain = MandalaChain() if with_chain else None
    contract = MandalaContract(minter=MINTER, chain=chain)
    gate = EntryThreshold(contract, entry_fee=fee, box=FakeCitizenBox(box_word))
    return gate, contract, chain


def check(name, cond):
    print("[%s] %s" % ("ok " if cond else "FAIL", name))
    if not cond:
        raise AssertionError(name)


passed = []


def t(name, fn):
    fn()
    passed.append(name)


# -- happy path ---------------------------------------------------------------
def happy_path():
    gate, contract, chain = fresh()
    contract.mint("aya", 1, by=MINTER)
    gate.register_proven("aya")
    allowed, reasons = gate.check_entry("aya")
    check("happy path: all three gates open", allowed and reasons == [])
    receipt = gate.enter("aya")
    check("happy path: receipt names citizen", receipt["citizen"] == "aya")
    check("happy path: receipt names fee", receipt["fee"] == 1)
    check("happy path: receipt names treasury", receipt["treasury"] == TREASURY_HOLDER)
    check("happy path: citizen paid 1", contract.balances_of("aya")["unlocked"] == 0)
    check("happy path: treasury gained 1",
          contract.balances_of(TREASURY_HOLDER)["unlocked"] == 1)
    check("happy path: chain still valid", chain.verify_chain()[0])

t("happy path", happy_path)


# -- gate 1: proof of self -----------------------------------------------------
def unknown_citizen():
    gate, contract, _ = fresh()
    contract.mint("stranger", 5, by=MINTER)  # rich, but unproven
    allowed, reasons = gate.check_entry("stranger")
    check("gate 1: unknown citizen refused", not allowed)
    check("gate 1: reason names proof-of-self",
          any("proof-of-self" in r for r in reasons))
    try:
        gate.enter("stranger")
        check("gate 1: enter raises", False)
    except ThresholdError as e:
        check("gate 1: error carries reasons", len(e.reasons) >= 1)

t("gate 1 refusal", unknown_citizen)


# -- gate 2: the mandala --------------------------------------------------------
def no_mandala():
    gate, contract, _ = fresh()
    gate.register_proven("broke")  # proven, but empty-handed
    allowed, reasons = gate.check_entry("broke")
    check("gate 2: empty-handed refused", not allowed)
    check("gate 2: reason names the mandala",
          any("mandala" in r for r in reasons))

t("gate 2 refusal", no_mandala)


def double_entry_one_mandala():
    gate, contract, _ = fresh()
    contract.mint("aya", 1, by=MINTER)
    gate.register_proven("aya")
    gate.enter("aya")  # spends the one mandala
    allowed, reasons = gate.check_entry("aya")
    check("gate 2: second step with no mandala refused", not allowed)
    check("gate 2: treasury kept the fee",
          contract.balances_of(TREASURY_HOLDER)["unlocked"] == 1)

t("double entry refused", double_entry_one_mandala)


def fee_conservation():
    gate, contract, _ = fresh(fee=3)
    contract.mint("aya", 5, by=MINTER)
    gate.register_proven("aya")
    before = contract.totals()["supply"]
    gate.enter("aya")
    check("fee: citizen down exactly the fee",
          contract.balances_of("aya")["unlocked"] == 2)
    check("fee: treasury up exactly the fee",
          contract.balances_of(TREASURY_HOLDER)["unlocked"] == 3)
    check("fee: supply conserved (nothing created or lost)",
          contract.totals()["supply"] == before)

t("fee conservation", fee_conservation)


# -- gate 3: the box is safe -----------------------------------------------------
def unsafe_words():
    for word in ("ARMED", "TRIPPED", "DISARMED"):
        gate, contract, _ = fresh(box_word=word)
        contract.mint("aya", 1, by=MINTER)
        gate.register_proven("aya")
        allowed, reasons = gate.check_entry("aya")
        check("gate 3: box reading %s refuses entry" % word, not allowed)
        check("gate 3: reason names the word",
              any(word in r for r in reasons))
        try:
            gate.enter("aya")
            check("gate 3: enter raises on %s" % word, False)
        except ThresholdError:
            pass
        check("gate 3: no fee moved on %s" % word,
              contract.balances_of("aya")["unlocked"] == 1)

t("unsafe box refused", unsafe_words)


def no_box():
    gate, contract, _ = fresh()
    gate.box = None  # no box attached at all
    contract.mint("aya", 1, by=MINTER)
    gate.register_proven("aya")
    allowed, reasons = gate.check_entry("aya")
    check("gate 3: no box means no entry", not allowed)
    check("gate 3: reason says so plainly",
          any("No box" in r or "no box" in r for r in reasons))

t("no box refused", no_box)


# -- all gates closed at once -----------------------------------------------------
def everything_closed():
    gate, contract, _ = fresh(box_word="TRIPPED")
    allowed, reasons = gate.check_entry("nobody")
    check("all closed: refused", not allowed)
    check("all closed: all three gates named", len(reasons) == 3)

t("all gates closed", everything_closed)


print("\n%d passed, 0 failed" % len(passed))
