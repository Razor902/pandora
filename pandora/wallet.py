# © 2026 Curtis Ray Dyess · Crimson Rose LLC
# ============================================================================
# EDUCATIONAL MODEL ONLY — NOT A PRODUCTION WALLET.
# A classroom model of Curtis's three-layer wallet for the mandala currency.
# Demo fingerprints, demo mandalas, no value, no network. The real identity
# binding, the real custody, and the real administrator process are his to
# wire in.
# ============================================================================
"""wallet.py -- the three-layer wallet for the mandala currency.

Curtis's order (2026-10-07): "Create a three layer wallet. for the currency."

The three layers:

    Layer 1 -- THE HAND (pocket)
        Carries the citizen's earned mandala. It is SHOWN at shops, never
        spent: "they just have to show it." No method in this module moves
        the hand's mandala anywhere. Display-only, by law.

    Layer 2 -- THE VAULT (savings)
        Receives multiplied mandalas from swarm handshakes
        (the Multiplication Law). Transferable citizen to citizen inside
        Pandora.

    Layer 3 -- THE RESERVE (cold)
        The deep reserve that backs the currency. Nothing moves here without
        administrator approval -- the parents hold it, and Curtis alone
        approves (the paradigm law).

THE LAWS, AS CODE:
    * Proof-of-self: every wallet is bound to the citizen's fingerprint at
      creation. Every sensitive operation must present the matching print.
      A wrong print is refused, plainly.
    * Mandala law: the hand shows, it never spends. There is no spend path
      out of the hand -- by design, not by accident.
    * Multiplication Law: when two wallets handshake, each vault multiplies
      by the other side's swarm count.
    * Nola's Law ("no lies, no deception"): every movement is written to an
      append-only ledger, and reconcile() replays the ledger from the first
      entry. If the layers disagree with the ledger, reconcile() raises
      DiscrepancyError -- loudly, never silently.
    * Admin law: the reserve moves only with by_admin=True and
      approved_by="Curtis Ray Dyess".

OPEN TENSION (Curtis's ruling needed -- NOT resolved here):
    threshold.py treats one mandala as an entry fee moved to the treasury.
    Curtis's mandala law says the mandala is shown, not consumed. This
    wallet enforces the shown-not-spent law on the hand; it takes no side
    on the fee question. See WALLET.md.
"""

import time

APPROVER = "Curtis Ray Dyess"  # the only name that approves reserve moves


class WalletError(Exception):
    """Base for everything the wallet refuses."""


class IdentityError(WalletError):
    """The fingerprint did not match the wallet's bound print."""


class LayerError(WalletError):
    """An operation tried to use a layer the wrong way."""


class AdminError(WalletError):
    """A reserve move lacked administrator approval."""


class DiscrepancyError(WalletError):
    """Nola's Law: the layers disagree with the ledger. No silent gaps."""


class ThreeLayerWallet:
    """One citizen's three-layer wallet, bound to their fingerprint."""

    HAND = "hand"
    VAULT = "vault"
    RESERVE = "reserve"
    LAYERS = (HAND, VAULT, RESERVE)

    def __init__(self, citizen_id, fingerprint, clock=None):
        """Bind a wallet to a citizen's fingerprint (proof-of-self).

        fingerprint here is a demo token string standing in for the real
        print. Production fingerprint capture, encryption, consent,
        revocation, and storage are NOT built.
        """
        if not citizen_id:
            raise WalletError("a wallet needs a citizen")
        if not fingerprint:
            raise WalletError("a wallet needs the citizen's fingerprint")
        self.citizen_id = citizen_id
        self.fingerprint = fingerprint
        self.clock = clock or time.time
        self._layers = {self.HAND: 0, self.VAULT: 0, self.RESERVE: 0}
        self._ledger = []
        self._seq = 0

    # -- the ledger (Nola's Law) ------------------------------------------------
    def _record(self, kind, layer, delta, detail=""):
        """Append one immutable entry. The ledger only ever grows."""
        self._seq += 1
        self._ledger.append({
            "seq": self._seq,
            "at": self.clock(),
            "citizen": self.citizen_id,
            "kind": kind,
            "layer": layer,
            "delta": delta,
            "detail": detail,
        })

    def _check_print(self, fingerprint):
        if fingerprint != self.fingerprint:
            raise IdentityError(
                "fingerprint does not match '%s'. The wallet stays shut."
                % self.citizen_id)

    def ledger_entries(self):
        """Read the whole ledger. Append-only: nothing here removes entries."""
        return list(self._ledger)

    def reconcile(self):
        """Nola's Law, as code: replay the ledger; the layers must agree.

        Returns True on agreement. Raises DiscrepancyError naming the layer
        and both numbers on ANY disagreement -- never silently.
        """
        expected = {layer: 0 for layer in self.LAYERS}
        for entry in self._ledger:
            expected[entry["layer"]] += entry["delta"]
        for layer in self.LAYERS:
            if self._layers[layer] != expected[layer]:
                raise DiscrepancyError(
                    "Nola's Law broken on '%s': the ledger says %s, the "
                    "wallet holds %s. Nothing moves until this is answered."
                    % (layer, expected[layer], self._layers[layer]))
        return True

    # -- Layer 1: THE HAND -------------------------------------------------------
    def earn_mandala(self, fingerprint):
        """Proof-of-self done: one mandala lands in the hand.

        (ASSUMED: one earn = one mandala. Curtis sets the real issuance.)
        """
        self._check_print(fingerprint)
        self._layers[self.HAND] += 1
        self._record("earn", self.HAND, +1, "proof-of-self accepted")
        return self._layers[self.HAND]

    def show_mandala(self, shop, fingerprint):
        """Show the mandala at a shop for one thing. The hand keeps it.

        Returns a display receipt. The balance does NOT change -- shown,
        not spent. That is the law.
        """
        self._check_print(fingerprint)
        if self._layers[self.HAND] < 1:
            raise LayerError(
                "the hand is empty: nothing to show at '%s'." % shop)
        receipt = {
            "citizen": self.citizen_id,
            "shop": shop,
            "shown": 1,
            "hand_still_holds": self._layers[self.HAND],
            "spent": 0,
            "shown_at": self.clock(),
        }
        self._record("show", self.HAND, 0,
                     "shown at '%s', never spent" % shop)
        return receipt

    def spend_from_hand(self, *args, **kwargs):
        """There is no spend path out of the hand. This always refuses."""
        raise LayerError(
            "the hand shows; it never spends. The mandala stays with "
            "the citizen.")

    # -- Layer 2: THE VAULT ------------------------------------------------------
    def handshake(self, other, my_swarm, their_swarm, fingerprint):
        """The Multiplication Law: two wallets shake, both multiply.

        My vault multiplies by THEIR swarm count; their vault multiplies by
        MY swarm count. What is there multiplies; an empty vault stays
        empty -- the law multiplies, it does not create from nothing.
        """
        self._check_print(fingerprint)
        if not isinstance(other, ThreeLayerWallet):
            raise WalletError("a handshake needs another three-layer wallet")
        if other is self:
            raise WalletError("a citizen cannot handshake with themselves")
        for name, count in (("my_swarm", my_swarm), ("their_swarm", their_swarm)):
            if not isinstance(count, int) or count < 1:
                raise WalletError("%s must be a positive whole number" % name)

        my_gain = self._layers[self.VAULT] * their_swarm - self._layers[self.VAULT]
        their_gain = other._layers[other.VAULT] * my_swarm - other._layers[other.VAULT]

        self._layers[self.VAULT] += my_gain
        other._layers[other.VAULT] += their_gain
        self._record("handshake", self.VAULT, my_gain,
                     "multiplied by their swarm of %d" % their_swarm)
        other._record("handshake", other.VAULT, their_gain,
                      "multiplied by their swarm of %d" % my_swarm)
        return {
            "me": {"vault": self._layers[self.VAULT], "gained": my_gain},
            "them": {"vault": other._layers[other.VAULT], "gained": their_gain},
        }

    def transfer_vault(self, to_wallet, amount, fingerprint):
        """Move vault mandalas citizen to citizen, inside Pandora."""
        self._check_print(fingerprint)
        if not isinstance(to_wallet, ThreeLayerWallet):
            raise WalletError("vault transfers go wallet to wallet")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise WalletError("amount must be positive")
        if self._layers[self.VAULT] < amount:
            raise WalletError(
                "'%s' holds %s in the vault, cannot send %s"
                % (self.citizen_id, self._layers[self.VAULT], amount))
        self._layers[self.VAULT] -= amount
        to_wallet._layers[to_wallet.VAULT] += amount
        self._record("vault_out", self.VAULT, -amount,
                     "to '%s'" % to_wallet.citizen_id)
        to_wallet._record("vault_in", to_wallet.VAULT, +amount,
                          "from '%s'" % self.citizen_id)
        return self._layers[self.VAULT]

    # -- Layer 3: THE RESERVE ----------------------------------------------------
    def move_reserve(self, amount, direction, by_admin, approved_by,
                     fingerprint):
        """Move mandalas between the vault and the reserve.

        direction is "in" (vault -> reserve) or "out" (reserve -> vault).
        Requires administrator access AND Curtis's approval -- the paradigm
        law. Anything less is refused.
        """
        self._check_print(fingerprint)
        if not by_admin:
            raise AdminError(
                "the reserve does not move without administrator access.")
        if approved_by != APPROVER:
            raise AdminError(
                "the reserve moves only with %s's approval." % APPROVER)
        if direction not in ("in", "out"):
            raise WalletError("direction must be 'in' or 'out'")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise WalletError("amount must be positive")
        source = self.VAULT if direction == "in" else self.RESERVE
        dest = self.RESERVE if direction == "in" else self.VAULT
        if self._layers[source] < amount:
            raise WalletError(
                "'%s' holds %s, cannot move %s %s the reserve"
                % (self.citizen_id, self._layers[source], amount, direction))
        self._layers[source] -= amount
        self._layers[dest] += amount
        self._record("reserve_%s" % direction, source, -amount,
                     "approved by %s" % approved_by)
        self._record("reserve_%s" % direction, dest, +amount,
                     "approved by %s" % approved_by)
        return self.balances()

    # -- reading the wallet ------------------------------------------------------
    def balances(self):
        return dict(self._layers)

    def total(self):
        return sum(self._layers.values())


def demo():
    """A citizen's whole evening, on the bench."""
    aya = ThreeLayerWallet("aya", fingerprint="print-aya")
    noah = ThreeLayerWallet("noah", fingerprint="print-noah")

    aya.earn_mandala("print-aya")
    print("aya shows at the bookshop:", aya.show_mandala("bookshop", "print-aya"))
    try:
        aya.spend_from_hand()
    except LayerError as e:
        print("spend refused:", e)

    # swarm handshakes multiply the vaults (seeded with ledger entries, so
    # the books still balance -- Nola's Law even in the demo)
    aya._layers[aya.VAULT] = 2
    aya._record("seed", aya.VAULT, +2, "demo seed")
    noah._layers[noah.VAULT] = 4
    noah._record("seed", noah.VAULT, +4, "demo seed")
    print("handshake:", aya.handshake(noah, my_swarm=5, their_swarm=3,
                                      fingerprint="print-aya"))

    # the reserve needs the administrator
    aya.transfer_vault(noah, 3, "print-aya")
    print("reserve in:", aya.move_reserve(1, "in", by_admin=True,
                                          approved_by=APPROVER,
                                          fingerprint="print-aya"))
    print("reconcile:", aya.reconcile(), noah.reconcile())


if __name__ == "__main__":
    demo()
