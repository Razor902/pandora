# EDUCATIONAL MODEL ONLY — not a medical device, not a product, not legal advice.
# © 2026 Curtis Ray Dyess · Crimson Rose LLC

"""The V2 Gift Module — Pandora's Box Version 2, the medical field.

Curtis's words: "I want Pandora's box Version two to be my gift to the
medical field. They can distribute it, I get some money out of it,
everybody's happy."

This module encodes the lifetime roadmap: four phases, each one a real gift
the medical field can use and distribute, sequenced so every phase earns and
unlocks the next. A phase's gate must be real before the next phase begins.
"""

PHASES = [
    {
        "number": 1,
        "name": "The Guardian Platform",
        "horizon": "now — the lifetime work begins here",
        "what": (
            "The secure medical data platform — digital guardian angel "
            "infrastructure. Curtis's stack: C and Perl/CPAN. Patient data "
            "encrypted, access logged, consent honored — the white-hat floor "
            "built into the foundation."
        ),
        "gift_to_the_field": (
            "Hospitals and device makers get a licensable security layer for "
            "medical data — the part of the dream machine that works today."
        ),
        "who_distributes": "Device makers and hospital systems, under license.",
        "money_flows_back": (
            "Per-installation license fee plus annual support — the wedge "
            "that funds the rest of the road."
        ),
        "gate": "First paying deployment in a real care setting, "
                "security reviewed by an independent third party.",
    },
    {
        "number": 2,
        "name": "The Healing Room",
        "horizon": "near — built on the V1 box",
        "what": (
            "Therapeutic VR: pain, fear, palliative comfort — the fear of "
            "death alleviated. Curtis's words: \"It will alleviate the fear "
            "of death.\" Paradise instead of purgatory, for life-support "
            "patients, starting as comfort care."
        ),
        "gift_to_the_field": (
            "Care teams get a comfort tool — real patients, real calm, "
            "real dignity at the hardest moments."
        ),
        "who_distributes": "Licensed to palliative and pain programs through "
                           "clinical partners.",
        "money_flows_back": (
            "Per-seat clinical license plus outcomes partnership — "
            "comfort that pays for itself in care quality."
        ),
        "gate": "Published comfort outcomes from a real clinical "
                "partnership — evidence, not enthusiasm.",
    },
    {
        "number": 3,
        "name": "The Open Door",
        "horizon": "horizon — architected ready, not promised",
        "what": (
            "The box architected BCI-ready: a neural interface can dock the "
            "day the science arrives. Today that science is investigational "
            "— Neuralink holds an FDA Investigational Device Exemption, not "
            "an approval. Say it plainly: the door is open; the guest has "
            "not yet arrived."
        ),
        "gift_to_the_field": (
            "Researchers get a ready-made, safety-first platform to dock "
            "their interfaces into — the white-hat floor travels with it."
        ),
        "who_distributes": "Research institutions under research license.",
        "money_flows_back": (
            "Research partnerships and platform licensing — the science "
            "pays its own way home."
        ),
        "gate": "An investigational interface docks in a supervised "
                "research setting with ethics-board approval.",
    },
    {
        "number": 4,
        "name": "The Dream",
        "horizon": "north star — never promised on a date",
        "what": (
            "Paradise instead of purgatory. Mind-transfer when it is "
            "genuinely possible — not before. Seeing God. Curtis's dream: "
            "\"And instead of living in purgatory until the day of "
            "judgment — in paradise until God calls you.\""
        ),
        "gift_to_the_field": (
            "The destination the architecture grows toward — the reason "
            "every earlier phase was built the way it was built."
        ),
        "who_distributes": "The field, when the science is real.",
        "money_flows_back": (
            "The dream is the gift. What flows back is legacy — and by "
            "then, the earlier phases have already fed the family."
        ),
        "gate": "Genuine, peer-reviewed science says the time has come. "
                "Not hope. Evidence.",
    },
]

DEAL = {
    "shape": "Non-exclusive medical distribution license",
    "royalty": "Royalty per deployed unit — negotiated per phase, not fixed here",
    "safety_clause": (
        "Curtis's safety stack (guardrails, biometric breaker, white-hat "
        "floor) travels with every license, non-negotiable."
    ),
    "status": (
        "SKETCH ONLY — a real attorney drafts the real paper before "
        "anything is signed."
    ),
}

HONESTY_LINE = (
    "Phases 1 and 2 are the lifetime work. Mind-transfer is never "
    "promised on a timeline — it waits on genuine science, and the "
    "architecture grows toward it honestly."
)


def get_phase(number):
    """Return the phase dict for a phase number, or None."""
    for phase in PHASES:
        if phase["number"] == number:
            return phase
    return None


def gate_passed(number, gates):
    """A phase's gate must be real before the next begins.

    gates: dict of {phase_number: bool} — True means that phase's gate
    has genuinely been met (deployed, reviewed, evidenced).
    """
    return bool(gates.get(number, False))


def unlocked_phases(gates):
    """Phases unlock in order: phase N unlocks only when phase N-1's
    gate has passed. Phase 1 is always unlocked — the work starts now."""
    unlocked = [1]
    for phase in PHASES[1:]:
        if gate_passed(phase["number"] - 1, gates):
            unlocked.append(phase["number"])
        else:
            break
    return unlocked


def roadmap():
    """Print the journey in plain words."""
    print("PANDORA'S BOX, VERSION TWO — THE GIFT TO THE MEDICAL FIELD")
    print()
    print(HONESTY_LINE)
    print()
    for phase in PHASES:
        print("Phase %d — %s" % (phase["number"], phase["name"]))
        print("  Horizon: %s" % phase["horizon"])
        print("  What: %s" % phase["what"])
        print("  The gift: %s" % phase["gift_to_the_field"])
        print("  Who distributes: %s" % phase["who_distributes"])
        print("  Money flows back: %s" % phase["money_flows_back"])
        print("  The gate: %s" % phase["gate"])
        print()


def deal_summary():
    """Print the everybody's-happy model."""
    print("THE DEAL — everybody's happy")
    print()
    print("Shape: %s" % DEAL["shape"])
    print("Royalty: %s" % DEAL["royalty"])
    print("Safety clause: %s" % DEAL["safety_clause"])
    print()
    print(DEAL["status"])


if __name__ == "__main__":
    roadmap()
    deal_summary()
