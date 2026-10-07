# EDUCATIONAL MODEL ONLY — not a medical device, not a product, not legal advice.
# © 2026 Curtis Ray Dyess · Crimson Rose LLC

"""Tests for the V2 Gift Module (v2_gift)."""

import v2_gift


def test_four_phases_in_order():
    numbers = [p["number"] for p in v2_gift.PHASES]
    assert numbers == [1, 2, 3, 4]


def test_phase_names():
    names = [p["name"] for p in v2_gift.PHASES]
    assert names == [
        "The Guardian Platform",
        "The Healing Room",
        "The Open Door",
        "The Dream",
    ]


def test_every_phase_has_a_gate():
    for phase in v2_gift.PHASES:
        assert phase["gate"], "phase %d has no gate" % phase["number"]


def test_every_phase_names_who_distributes():
    for phase in v2_gift.PHASES:
        assert phase["who_distributes"]


def test_get_phase():
    assert v2_gift.get_phase(2)["name"] == "The Healing Room"
    assert v2_gift.get_phase(99) is None


def test_gate_logic():
    assert v2_gift.gate_passed(1, {1: True}) is True
    assert v2_gift.gate_passed(1, {1: False}) is False
    assert v2_gift.gate_passed(2, {}) is False


def test_unlocks_in_order():
    # Phase 1 always unlocked; nothing else without gates.
    assert v2_gift.unlocked_phases({}) == [1]
    # Phase 2 unlocks when phase 1's gate passes.
    assert v2_gift.unlocked_phases({1: True}) == [1, 2]
    # No skipping: phase 3 needs phase 2's gate too.
    assert v2_gift.unlocked_phases({1: True, 3: True}) == [1, 2]
    assert v2_gift.unlocked_phases({1: True, 2: True}) == [1, 2, 3]
    assert v2_gift.unlocked_phases({1: True, 2: True, 3: True}) == [1, 2, 3, 4]


def test_deal_terms_present():
    deal = v2_gift.DEAL
    assert "license" in deal["shape"].lower()
    assert "royalty" in deal["royalty"].lower()
    assert "non-negotiable" in deal["safety_clause"]
    assert "attorney" in deal["status"].lower()


def test_honesty_line_present():
    assert "lifetime work" in v2_gift.HONESTY_LINE
    assert "never" in v2_gift.HONESTY_LINE


def test_roadmap_runs():
    v2_gift.roadmap()


def test_deal_summary_runs():
    v2_gift.deal_summary()


if __name__ == "__main__":
    import traceback

    count = 0
    failed = 0
    for name, fn in sorted(vars().items()):
        if name.startswith("test_") and callable(fn):
            count += 1
            try:
                fn()
                print("ok - %s" % name)
            except Exception:
                failed += 1
                print("FAIL - %s" % name)
                traceback.print_exc()
    print("%d/%d passed" % (count - failed, count))
