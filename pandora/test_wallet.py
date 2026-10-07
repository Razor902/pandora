# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Tests for wallet.py -- the three-layer wallet for the mandala currency.

Every test is a law of Curtis's, checked in code:
  - the hand shows, it never spends
  - the vault receives the Multiplication Law's handshake
  - the reserve moves only with administrator approval
  - the fingerprint is the citizen's proof
  - Nola's Law: the ledger always reconciles, or it shouts
"""

import pytest

from wallet import (
    ThreeLayerWallet,
    WalletError,
    IdentityError,
    LayerError,
    AdminError,
    DiscrepancyError,
    APPROVER,
)

PRINT_AYA = "print-aya"
PRINT_NOAH = "print-noah"


def make_aya():
    return ThreeLayerWallet("aya", fingerprint=PRINT_AYA, clock=lambda: 1_000.0)


def make_noah():
    return ThreeLayerWallet("noah", fingerprint=PRINT_NOAH, clock=lambda: 1_000.0)


def seed_vault(wallet, amount, fp):
    """Bench helper: put mandalas in the vault WITH a ledger entry."""
    wallet._layers[wallet.VAULT] += amount
    wallet._record("seed", wallet.VAULT, +amount, "test seed")


# -- Layer 1: THE HAND ----------------------------------------------------------

def test_earn_puts_one_mandala_in_the_hand():
    aya = make_aya()
    assert aya.earn_mandala(PRINT_AYA) == 1
    assert aya.balances()["hand"] == 1


def test_show_returns_receipt_and_hand_keeps_the_mandala():
    aya = make_aya()
    aya.earn_mandala(PRINT_AYA)
    receipt = aya.show_mandala("bookshop", PRINT_AYA)
    assert receipt["shown"] == 1
    assert receipt["spent"] == 0
    assert receipt["hand_still_holds"] == 1
    assert aya.balances()["hand"] == 1  # shown, not spent


def test_show_twice_keeps_the_mandala_both_times():
    aya = make_aya()
    aya.earn_mandala(PRINT_AYA)
    aya.show_mandala("bookshop", PRINT_AYA)
    aya.show_mandala("toolshop", PRINT_AYA)
    assert aya.balances()["hand"] == 1


def test_spend_from_hand_is_always_refused():
    aya = make_aya()
    aya.earn_mandala(PRINT_AYA)
    with pytest.raises(LayerError):
        aya.spend_from_hand(1)
    assert aya.balances()["hand"] == 1


def test_show_with_empty_hand_is_refused():
    aya = make_aya()
    with pytest.raises(LayerError):
        aya.show_mandala("bookshop", PRINT_AYA)


# -- proof-of-self ---------------------------------------------------------------

def test_wrong_fingerprint_shuts_the_wallet():
    aya = make_aya()
    with pytest.raises(IdentityError):
        aya.earn_mandala("print-stranger")
    aya.earn_mandala(PRINT_AYA)
    with pytest.raises(IdentityError):
        aya.show_mandala("bookshop", "print-stranger")


def test_wrong_fingerprint_blocks_vault_transfer():
    aya, noah = make_aya(), make_noah()
    seed_vault(aya, 5, PRINT_AYA)
    with pytest.raises(IdentityError):
        aya.transfer_vault(noah, 2, "print-stranger")
    assert aya.balances()["vault"] == 5


# -- Layer 2: THE VAULT + the Multiplication Law ----------------------------------

def test_handshake_multiplies_both_vaults():
    aya, noah = make_aya(), make_noah()
    seed_vault(aya, 2, PRINT_AYA)
    seed_vault(noah, 4, PRINT_NOAH)
    result = aya.handshake(noah, my_swarm=5, their_swarm=3,
                           fingerprint=PRINT_AYA)
    # aya's vault (2) x noah's swarm (3) = 6 ; noah's vault (4) x aya's swarm (5) = 20
    assert aya.balances()["vault"] == 6
    assert noah.balances()["vault"] == 20
    assert result["me"]["gained"] == 4
    assert result["them"]["gained"] == 16


def test_handshake_with_empty_vault_multiplies_nothing():
    aya, noah = make_aya(), make_noah()
    seed_vault(noah, 4, PRINT_NOAH)
    aya.handshake(noah, my_swarm=5, their_swarm=3, fingerprint=PRINT_AYA)
    assert aya.balances()["vault"] == 0  # the law multiplies, not creates
    assert noah.balances()["vault"] == 20


def test_handshake_refuses_bad_swarm_counts():
    aya, noah = make_aya(), make_noah()
    with pytest.raises(WalletError):
        aya.handshake(noah, my_swarm=0, their_swarm=3, fingerprint=PRINT_AYA)
    with pytest.raises(WalletError):
        aya.handshake(aya, my_swarm=2, their_swarm=2, fingerprint=PRINT_AYA)


def test_vault_transfer_moves_between_citizens():
    aya, noah = make_aya(), make_noah()
    seed_vault(aya, 6, PRINT_AYA)
    aya.transfer_vault(noah, 2, PRINT_AYA)
    assert aya.balances()["vault"] == 4
    assert noah.balances()["vault"] == 2


def test_vault_transfer_refuses_what_you_lack():
    aya, noah = make_aya(), make_noah()
    seed_vault(aya, 1, PRINT_AYA)
    with pytest.raises(WalletError):
        aya.transfer_vault(noah, 5, PRINT_AYA)
    assert aya.balances()["vault"] == 1


# -- Layer 3: THE RESERVE ----------------------------------------------------------

def test_reserve_refuses_without_admin():
    aya = make_aya()
    seed_vault(aya, 5, PRINT_AYA)
    with pytest.raises(AdminError):
        aya.move_reserve(2, "in", by_admin=False, approved_by=APPROVER,
                         fingerprint=PRINT_AYA)
    assert aya.balances()["reserve"] == 0


def test_reserve_refuses_without_curtis_approval():
    aya = make_aya()
    seed_vault(aya, 5, PRINT_AYA)
    with pytest.raises(AdminError):
        aya.move_reserve(2, "in", by_admin=True, approved_by="someone-else",
                         fingerprint=PRINT_AYA)
    assert aya.balances()["reserve"] == 0


def test_reserve_moves_with_admin_and_curtis_approval():
    aya = make_aya()
    seed_vault(aya, 5, PRINT_AYA)
    balances = aya.move_reserve(2, "in", by_admin=True,
                                approved_by=APPROVER, fingerprint=PRINT_AYA)
    assert balances["vault"] == 3
    assert balances["reserve"] == 2
    balances = aya.move_reserve(1, "out", by_admin=True,
                                approved_by=APPROVER, fingerprint=PRINT_AYA)
    assert balances["vault"] == 4
    assert balances["reserve"] == 1


# -- Nola's Law: the ledger -------------------------------------------------------

def test_every_movement_is_written_down():
    aya, noah = make_aya(), make_noah()
    aya.earn_mandala(PRINT_AYA)
    aya.show_mandala("bookshop", PRINT_AYA)
    seed_vault(aya, 2, PRINT_AYA)
    aya.handshake(noah, my_swarm=2, their_swarm=3, fingerprint=PRINT_AYA)
    aya.transfer_vault(noah, 1, PRINT_AYA)
    kinds = [e["kind"] for e in aya.ledger_entries()]
    assert kinds == ["earn", "show", "seed", "handshake", "vault_out"]
    assert [e["seq"] for e in aya.ledger_entries()] == [1, 2, 3, 4, 5]


def test_reconcile_passes_on_a_healthy_wallet():
    aya, noah = make_aya(), make_noah()
    aya.earn_mandala(PRINT_AYA)
    seed_vault(aya, 6, PRINT_AYA)
    aya.handshake(noah, my_swarm=2, their_swarm=3, fingerprint=PRINT_AYA)
    aya.transfer_vault(noah, 4, PRINT_AYA)
    aya.move_reserve(2, "in", by_admin=True, approved_by=APPROVER,
                     fingerprint=PRINT_AYA)
    assert aya.reconcile() is True
    assert noah.reconcile() is True


def test_reconcile_shouts_on_a_tampered_layer():
    aya = make_aya()
    aya.earn_mandala(PRINT_AYA)
    seed_vault(aya, 5, PRINT_AYA)
    assert aya.reconcile() is True
    aya._layers[aya.VAULT] += 10  # someone fudged the books
    with pytest.raises(DiscrepancyError) as exc:
        aya.reconcile()
    assert "vault" in str(exc.value)


def test_reconcile_catches_a_missing_ledger_entry():
    aya = make_aya()
    aya.earn_mandala(PRINT_AYA)
    seed_vault(aya, 5, PRINT_AYA)
    aya._ledger.pop()  # someone tore a page out
    with pytest.raises(DiscrepancyError):
        aya.reconcile()


def test_ledger_only_grows():
    aya = make_aya()
    aya.earn_mandala(PRINT_AYA)
    n = len(aya.ledger_entries())
    assert not hasattr(aya, "delete_entry")
    assert not hasattr(aya, "clear_ledger")
    assert len(aya.ledger_entries()) == n
