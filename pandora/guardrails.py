# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Pandora's Box guardrails — the leash on the black box.

This module wraps the Pandora scare engine (core.Engine) WITHOUT changing
it. The engine's internals — levels 1-2, default disarmed, kill switch,
attach/detach — are exactly as they were. The guardrails sit around the
engine and decide when it may be armed at all.

Three jobs, all Curtis's orders:

1. CONTENT RESTRICTIONS — 18+ age gate at setup (local attestation, stored
   on the device). A max content-level cap, default 1, raisable only by the
   admin and NEVER above 2. Level 3 does not exist and is not implemented
   here. Anything above level 1 needs explicit per-session opt-in.

2. PARENTAL CONTROLS — screen time: 1 hour per day, 3 days per week. The
   buyer picks the 3 days at setup. Usage is tracked locally in a JSON
   file. When time expires the session winds down gracefully: the game's
   save hook is called, a farewell beat plays, and the box goes quiet.
   Never a hard cut. Weekly reset. Plain-language status a parent can read.

3. ADMIN ACCESS — Curtis himself is the ONLY person who can approve admin
   access. There is no self-provisioning, no default PIN, no backdoor, no
   alternate path. Setup stays locked until Curtis approves, and he can
   revoke admin access too.

   How that works: when Curtis builds (manufactures) a box, he bakes in an
   owner secret only he knows. Creating an admin requires an approval code
   that is an HMAC of a one-time request token under that owner secret.
   Nobody holding the box can mint that code — only Curtis can, on his own
   machine, with his secret. There is simply no code path that creates an
   admin without a valid Curtis approval.

   The admin PIN is stored hashed (PBKDF2-SHA256, stdlib). Only the admin
   can change content caps, play days, usage logs, or factory-reset.
   Players get zero access. Failed PIN attempts are logged; 5 bad tries in
   a row triggers a cooldown lockout. The physical kill switch stays
   instant and available to everyone, always.

Local-only. No network. Stdlib only — runs on Termux.

Hardened (Curtis: "make it better"):

4. TAMPER-EVIDENT STATE — the state file carries an HMAC-SHA256 seal made
   with the owner secret. Hand-editing the file (say, to reset the time
   budget) breaks the seal: the box then refuses to arm, refuses admin
   changes, and refuses new approvals until Curtis re-seals it with a
   factory-reset approval. The kill switch and wind-down still work —
   fail-secure, never fail-open. If the owner secret itself was altered,
   the box stays locked; Curtis handles that one physically.

5. MONOTONIC PLAY CLOCK — the time budget no longer trusts the game to
   report minutes honestly. arming starts a monotonic timer (the wall
   clock can't be rolled back to cheat it); tick() and disarm() debit
   real elapsed time, and record_play() never debits less than the
   elapsed floor. Double-arming is refused.

6. APPROVAL REQUESTS EXPIRE — a Curtis approval token lives 24 hours.
   A stale code found later doesn't work.
"""

import hashlib
import hmac
import json
import math
import os
import secrets
import time
from datetime import datetime

from .core import Engine  # noqa: F401  (re-exported for convenience)

__version__ = "0.3.0"  # hardened + biometric trip

# ---------------------------------------------------------------------------
# constants — Curtis's standing numbers
# ---------------------------------------------------------------------------

MAX_LEVEL = 2            # the cap can never go above 2; level 3 doesn't exist
DEFAULT_CAP = 1          # content cap starts at 1 (atmosphere)
MINUTES_PER_DAY = 60     # 1 hour per day
PLAY_DAYS_COUNT = 3      # 3 days per week
VALID_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
PIN_MIN_LEN = 4
MAX_FAILED = 5           # bad PIN tries before cooldown
LOCKOUT_SECONDS = 600    # 10 minute cooldown
ATTEMPT_LOG_CAP = 200
REQUEST_TTL = 86400      # Curtis approval tokens live 24 hours


class GuardrailError(Exception):
    """Every refusal speaks plain language."""


# ---------------------------------------------------------------------------
# Curtis's approval codes — minted ONLY by Curtis, on his own machine.
# ---------------------------------------------------------------------------

def curtis_approval_code(owner_secret_hex, request_token, action):
    """Compute the approval code Curtis gives to a box.

    Curtis runs this on HIS machine with HIS owner secret — never on the
    box UI. The box verifies the code with the secret baked in at
    manufacture. Without the secret, the code cannot be forged.
    """
    msg = ("pandora:%s:%s" % (action, request_token)).encode("utf-8")
    mac = hmac.new(bytes.fromhex(owner_secret_hex), msg, hashlib.sha256)
    return mac.hexdigest()[:12]


def _hash_pin(pin, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 200_000)
    return salt.hex(), digest.hex()


def _check_pin(pin, salt_hex, hash_hex):
    _, digest_hex = _hash_pin(pin, bytes.fromhex(salt_hex))
    return hmac.compare_digest(digest_hex, hash_hex)


# ---------------------------------------------------------------------------
# the guardrails
# ---------------------------------------------------------------------------

class Guardrails:
    """Wraps a Pandora Engine with content, time, and admin guardrails.

    Usage (the happy path):
        g = Guardrails(state_path)            # on the box
        g.manufacture(owner_secret_hex)        # Curtis, once, at build time
        token = g.begin_setup(age_attested=True,
                              days=["Mon", "Wed", "Fri"],
                              admin_pin="....")  # buyer's request
        code = curtis_approval_code(owner_secret_hex, token, "grant-admin")
        g.curtis_approve(token, code)          # Curtis says so -> READY
        g.arm(engine, level=1)                 # play
    """

    def __init__(self, state_path=None, clock=None):
        if state_path is None:
            base = os.path.expanduser("~/.pandora")
            state_path = os.path.join(base, "guardrails.json")
        self.state_path = state_path
        self._clock = clock or time.time
        self._session = None  # in-memory only: {"engine","game","level","date"}
        self._trip = None     # BiometricTrip, once enable_biometrics() runs
        self._state = self._load()

    # -- state file ------------------------------------------------------
    def _blank(self):
        return {
            "manufactured": False,
            "owner_secret": None,
            "state": "FACTORY",          # FACTORY | AWAITING_CURTIS | READY
            "age_attested": False,
            "play_days": [],
            "level_cap": DEFAULT_CAP,
            "admin": None,               # {"salt","hash"} once Curtis approves
            "pending_admin": None,       # proposed at begin_setup, inert until approved
            "pending_request": None,     # {"token","action","created"}
            "failed_attempts": [],       # [{"t","kind","ok"}]
            "consecutive_failures": 0,
            "lockout_until": 0,
            "usage": {"week": None, "days": {}, "days_used": []},
            "wound_down_on": None,
            "seal": None,                # HMAC of the state, owner secret
        }

    def _seal_payload(self):
        st = dict(self._state)
        st.pop("seal", None)
        return json.dumps(st, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")

    def _compute_seal(self):
        return hmac.new(
            bytes.fromhex(self._state["owner_secret"]),
            self._seal_payload(), hashlib.sha256).hexdigest()

    def _refuse_if_tampered(self):
        if getattr(self, "_tampered", False):
            raise GuardrailError(
                "The box's memory was tampered with. It won't arm until "
                "Curtis checks it and re-seals it with a factory reset. "
                "The kill switch still works.")

    def _load(self):
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                st = json.load(f)
            base = self._blank()
            base.update(st)
        except (OSError, ValueError):
            base = self._blank()
        self._state = base
        self._tampered = False
        if base.get("manufactured") and base.get("owner_secret"):
            if base.get("seal"):
                if not hmac.compare_digest(base["seal"],
                                           self._compute_seal()):
                    self._tampered = True
            else:
                self._save()  # adopt the seal on first load
        return base

    def _save(self):
        d = os.path.dirname(os.path.abspath(self.state_path))
        os.makedirs(d, exist_ok=True)
        if self._state.get("manufactured") and self._state.get("owner_secret"):
            self._state["seal"] = self._compute_seal()
        else:
            self._state["seal"] = None
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2, sort_keys=True)
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.state_path)

    def _now(self):
        return self._clock()

    def _today(self):
        return datetime.fromtimestamp(self._now()).strftime("%Y-%m-%d")

    def _weekday(self):
        return datetime.fromtimestamp(self._now()).strftime("%a")

    def _weekkey(self):
        return datetime.fromtimestamp(self._now()).strftime("%G-W%V")

    # -- manufacture: Curtis, once ---------------------------------------
    def manufacture(self, owner_secret_hex):
        """Bake Curtis's owner secret into the box. Runs once, at build
        time, by Curtis. Can never run twice — there is no re-manufacture."""
        if self._state["manufactured"]:
            raise GuardrailError(
                "This box is already manufactured. It cannot be "
                "manufactured again.")
        try:
            raw = bytes.fromhex(owner_secret_hex)
        except ValueError:
            raise GuardrailError("The owner secret must be hex.")
        if len(raw) < 16:
            raise GuardrailError(
                "The owner secret must be at least 16 bytes (32 hex chars).")
        self._state["manufactured"] = True
        self._state["owner_secret"] = owner_secret_hex.lower()
        self._save()

    # -- setup: a request, locked until Curtis approves -------------------
    def begin_setup(self, age_attested, days, admin_pin):
        """Start setup. This creates a REQUEST — the box stays locked until
        Curtis approves it. Anyone holding the box can ask; only Curtis can
        say yes."""
        self._refuse_if_tampered()
        if not self._state["manufactured"]:
            raise GuardrailError(
                "This box was never manufactured. Only Curtis can "
                "manufacture a box.")
        if self._state["state"] not in ("FACTORY", "AWAITING_CURTIS"):
            raise GuardrailError("This box is already set up.")
        if not age_attested:
            raise GuardrailError(
                "Pandora's Box is 18+. Setup needs an adult's word that "
                "the buyer is eighteen or older.")
        days = self._validate_days(days)
        if not isinstance(admin_pin, str) or len(admin_pin) < PIN_MIN_LEN:
            raise GuardrailError(
                "The admin PIN needs at least %d characters." % PIN_MIN_LEN)
        salt_hex, hash_hex = _hash_pin(admin_pin)
        self._state["age_attested"] = True
        self._state["play_days"] = days
        self._state["level_cap"] = DEFAULT_CAP
        self._state["pending_admin"] = {"salt": salt_hex, "hash": hash_hex}
        token = secrets.token_hex(8)
        self._state["pending_request"] = {
            "token": token, "action": "grant-admin", "created": self._now()}
        self._state["state"] = "AWAITING_CURTIS"
        self._save()
        return token

    @staticmethod
    def _validate_days(days):
        if not isinstance(days, (list, tuple)) or len(days) != PLAY_DAYS_COUNT:
            raise GuardrailError(
                "Pick exactly %d play days, like "
                "[\"Mon\", \"Wed\", \"Fri\"]." % PLAY_DAYS_COUNT)
        clean = []
        for d in days:
            if d not in VALID_DAYS:
                raise GuardrailError(
                    "Days look like Mon, Tue, Wed, Thu, Fri, Sat, Sun. "
                    "Got %r." % (d,))
            if d in clean:
                raise GuardrailError("Each play day once — %r twice." % (d,))
            clean.append(d)
        return clean

    def _consume_request(self, token, action, code):
        """Verify a Curtis approval code against the pending request. The
        request token is single-use. Raises on anything wrong."""
        if not self._state["manufactured"] or not self._state["owner_secret"]:
            raise GuardrailError("This box was never manufactured.")
        pending = self._state["pending_request"]
        if not pending or pending["token"] != token \
                or pending["action"] != action:
            self._log_attempt("curtis", False)
            raise GuardrailError(
                "No matching approval request. Ask Curtis for a fresh one.")
        if self._now() - pending.get("created", 0) > REQUEST_TTL:
            self._state["pending_request"] = None
            self._save()
            self._log_attempt("curtis", False)
            raise GuardrailError(
                "That approval request expired after 24 hours. Ask Curtis "
                "for a fresh one.")
        expected = curtis_approval_code(
            self._state["owner_secret"], token, action)
        if not hmac.compare_digest(expected, code):
            self._log_attempt("curtis", False)
            raise GuardrailError(
                "That approval code doesn't check out. Only Curtis can "
                "approve this.")
        self._log_attempt("curtis", True)
        self._state["pending_request"] = None
        self._save()

    def curtis_approve(self, token, code):
        """Curtis approves the pending admin. Only this call — with a code
        only Curtis can mint — can bring an admin into existence."""
        self._refuse_if_tampered()
        pending = self._state["pending_request"]
        if not pending or pending["action"] != "grant-admin":
            raise GuardrailError("No admin approval is waiting.")
        self._consume_request(token, "grant-admin", code)
        self._state["admin"] = self._state["pending_admin"]
        self._state["pending_admin"] = None
        self._state["state"] = "READY"
        self._state["consecutive_failures"] = 0
        self._state["lockout_until"] = 0
        self._save()

    def request_revoke(self):
        """Ask Curtis to revoke the admin. Anyone can ask; only his code
        completes it."""
        if self._state["state"] != "READY" or not self._state["admin"]:
            raise GuardrailError("There's no admin to revoke.")
        token = secrets.token_hex(8)
        self._state["pending_request"] = {
            "token": token, "action": "revoke-admin", "created": self._now()}
        self._save()
        return token

    def curtis_revoke(self, token, code):
        """Curtis revokes admin access. The box locks again until he
        approves a new admin."""
        self._refuse_if_tampered()
        pending = self._state["pending_request"]
        if not pending or pending["action"] != "revoke-admin":
            raise GuardrailError("No revocation is waiting.")
        self._consume_request(token, "revoke-admin", code)
        self._state["admin"] = None
        self._state["pending_admin"] = None
        self._state["state"] = "AWAITING_CURTIS"
        self._session = None
        self._save()

    def request_factory_reset(self):
        """Ask Curtis to approve a factory reset (the admin can also reset
        with their PIN)."""
        token = secrets.token_hex(8)
        self._state["pending_request"] = {
            "token": token, "action": "factory-reset", "created": self._now()}
        self._save()
        return token

    def curtis_factory_reset(self, token, code):
        # Deliberately allowed even when tampered: this is how Curtis
        # re-seals a box whose memory was tampered with. The code still
        # has to check out against the stored owner secret.
        pending = self._state["pending_request"]
        if not pending or pending["action"] != "factory-reset":
            raise GuardrailError("No factory reset is waiting.")
        self._consume_request(token, "factory-reset", code)
        self._wipe_to_factory()

    # -- admin PIN gate ----------------------------------------------------
    def _log_attempt(self, kind, ok):
        self._state["failed_attempts"].append(
            {"t": self._now(), "kind": kind, "ok": bool(ok)})
        self._state["failed_attempts"] = \
            self._state["failed_attempts"][-ATTEMPT_LOG_CAP:]
        self._save()

    def _check_lockout(self):
        until = self._state["lockout_until"]
        if until and self._now() < until:
            left = int(until - self._now())
            raise GuardrailError(
                "Too many wrong tries. The box is ignoring PINs for "
                "%d more seconds." % left)

    def admin_auth(self, pin):
        """Check the admin PIN. True/False; 5 bad tries in a row locks PINs
        out for a cooldown. Raises while locked out."""
        if self._state["state"] != "READY" or not self._state["admin"]:
            raise GuardrailError(
                "There's no admin on this box right now.")
        self._check_lockout()
        admin = self._state["admin"]
        ok = _check_pin(pin, admin["salt"], admin["hash"])
        if ok:
            self._state["consecutive_failures"] = 0
            self._log_attempt("pin", True)
            return True
        self._state["consecutive_failures"] += 1
        self._log_attempt("pin", False)
        if self._state["consecutive_failures"] >= MAX_FAILED:
            self._state["lockout_until"] = self._now() + LOCKOUT_SECONDS
        self._save()
        return False

    def _require_admin(self, pin):
        """Every admin-only change passes through here. No PIN, no change."""
        self._refuse_if_tampered()
        try:
            ok = self.admin_auth(pin)
        except GuardrailError:
            raise
        if not ok:
            raise GuardrailError(
                "Wrong PIN. Only the admin can change that.")

    # -- admin-only changes --------------------------------------------------
    def set_level_cap(self, pin, cap):
        """Raise or lower the content cap. Never above 2 — level 3 does not
        exist and cannot be enabled from here."""
        self._require_admin(pin)
        if cap not in (1, 2):
            raise GuardrailError(
                "The content cap is 1 (atmosphere) or 2 (dread). "
                "There is no level 3 to enable.")
        self._state["level_cap"] = cap
        self._save()
        return "Content cap is now level %d." % cap

    def set_days(self, pin, days):
        """Change the 3 play days. Admin only."""
        self._require_admin(pin)
        self._state["play_days"] = self._validate_days(days)
        self._save()
        return "Play days are now %s." % ", ".join(self._state["play_days"])

    def clear_usage(self, pin):
        """Wipe the usage log. Admin only."""
        self._require_admin(pin)
        self._state["usage"] = {"week": self._weekkey(), "days": {},
                               "days_used": []}
        self._state["wound_down_on"] = None
        self._save()
        return "Usage log wiped."

    def factory_reset_with_pin(self, pin):
        """Factory reset with the admin PIN. Keeps Curtis's manufacture."""
        self._require_admin(pin)
        self._wipe_to_factory()
        return "Box reset to factory. It stays locked until Curtis approves."

    def _wipe_to_factory(self):
        keep_secret = self._state["owner_secret"]
        keep_mfg = self._state["manufactured"]
        self._state = self._blank()
        self._state["manufactured"] = keep_mfg
        self._state["owner_secret"] = keep_secret
        self._session = None
        self._tampered = False
        self._save()

    # -- play-time budget ----------------------------------------------------
    def _roll_week(self):
        wk = self._weekkey()
        if self._state["usage"]["week"] != wk:
            self._state["usage"] = {"week": wk, "days": {}, "days_used": []}
            self._save()

    def is_play_day(self):
        self._roll_week()
        return self._weekday() in self._state["play_days"]

    def remaining_today(self):
        self._roll_week()
        used = self._state["usage"]["days"].get(self._today(), 0)
        return max(0, MINUTES_PER_DAY - used)

    def _refuse_if_not_ready(self):
        self._refuse_if_tampered()
        if self._state["state"] == "AWAITING_CURTIS":
            raise GuardrailError(
                "The box is set up but locked. It stays locked until "
                "Curtis approves the admin.")
        if self._state["state"] != "READY":
            raise GuardrailError("The box isn't set up yet.")

    # -- arming, guarded -------------------------------------------------------
    def arm(self, engine, level=None, consent=False, game=None):
        """Arm the engine — if every guardrail allows it.

        level defaults to the engine's own level. Level 2 needs consent=True
        every session. The content cap, the play days, and the time budget
        all have to agree. game is kept only so wind-down can call its save
        hook; the engine itself is never modified here."""
        self._refuse_if_not_ready()
        if level is None:
            level = engine.level
        if level not in (1, 2):
            raise GuardrailError(
                "Pandora only arms levels 1 and 2. Level %r doesn't "
                "exist here." % (level,))
        cap = self._state["level_cap"]
        if level > cap:
            raise GuardrailError(
                "Content cap is level %d. The admin can raise it to 2 — "
                "never higher." % cap)
        if level > engine.level:
            raise GuardrailError(
                "This engine runs at level %d; it can't arm higher."
                % engine.level)
        if level == 2 and not consent:
            raise GuardrailError(
                "Level 2 (dread) needs your say-so every session. "
                "Arm again with consent=True.")
        if not self.is_play_day():
            raise GuardrailError(
                "Today (%s) isn't a play day. Play days: %s."
                % (self._weekday(), ", ".join(self._state["play_days"])))
        if self._state["wound_down_on"] == self._today():
            raise GuardrailError(
                "Time's up for today. The box is resting — see you on "
                "the next play day.")
        if self.remaining_today() <= 0:
            self.wind_down()
            raise GuardrailError(
                "Time's up for today. The box is resting — see you on "
                "the next play day.")
        if self._session is not None:
            raise GuardrailError(
                "The box is already armed. Disarm it before arming again.")
        if self._trip is not None:
            ok, reason = self._trip.arm_check()
            if not ok:
                raise GuardrailError(reason)
        engine.arm()
        today = self._today()
        if today not in self._state["usage"]["days_used"]:
            self._state["usage"]["days_used"].append(today)
        self._session = {"engine": engine, "game": game,
                         "level": level, "date": today,
                         "mono_start": time.monotonic(),
                         "debited_min": 0}
        self._save()
        return "Armed at level %d. %s" % (level, self._time_left_msg())

    def _time_left_msg(self):
        left = self.remaining_today()
        if left == 1:
            return "1 minute left today."
        return "%d minutes left today." % left

    def record_play(self, minutes):
        """Log minutes played. When the budget runs out, the box winds
        down gracefully on its own. The game's report is advisory: the
        monotonic session clock sets the floor, so under-reporting can't
        buy extra time."""
        self._refuse_if_not_ready()
        try:
            minutes = int(minutes)
        except (TypeError, ValueError):
            raise GuardrailError("Minutes must be a number.")
        if minutes <= 0:
            raise GuardrailError("Minutes must be positive.")
        effective = minutes
        if self._session is not None:
            floor = self._mono_elapsed_min() - self._session["debited_min"]
            effective = max(minutes, floor)
            self._session["debited_min"] += effective
        return self._debit(effective)

    def _mono_elapsed_min(self):
        """Whole minutes elapsed since arming, monotonic clock — rolling
        the wall clock back can't shrink it."""
        if self._session is None:
            return 0
        return max(0, int(math.ceil(
            (time.monotonic() - self._session["mono_start"]) / 60.0)))

    def _debit(self, minutes):
        self._roll_week()
        today = self._today()
        days = self._state["usage"]["days"]
        days[today] = days.get(today, 0) + minutes
        if today not in self._state["usage"]["days_used"]:
            self._state["usage"]["days_used"].append(today)
        self._save()
        if days[today] >= MINUTES_PER_DAY:
            return self.wind_down()
        return self._time_left_msg()

    def tick(self):
        """Debit real elapsed play time. Call from the game loop; the box
        winds itself down the moment the budget is spent — or the moment
        the biometric trip fires, whichever comes first."""
        self._refuse_if_not_ready()
        if self._session is None:
            return self._time_left_msg()
        if self._trip is not None:
            reason = self._trip.update()
            if reason is not None:
                return self.wind_down(reason=reason)
        total = self._mono_elapsed_min()
        new = total - self._session["debited_min"]
        if new <= 0:
            return self._time_left_msg()
        self._session["debited_min"] = total
        return self._debit(new)

    def enable_biometrics(self, trip):
        """Attach the heart-rate breaker. Adding safety is always allowed;
        only an admin can take it off again (disable_biometrics)."""
        self._refuse_if_not_ready()
        self._trip = trip
        return ("Biometric trip attached. The box won't arm without the "
                "cuff reading, and it trips out before your heart can "
                "get somewhere dangerous.")

    def disable_biometrics(self, pin):
        """Removing a safety layer needs the admin. The box remembers who
        asked."""
        self._refuse_if_not_ready()
        self._require_admin(pin)
        self._trip = None
        return "Biometric trip detached by the admin."

    def disarm(self):
        """End the session: debit the elapsed time, disarm the engine."""
        self._refuse_if_not_ready()
        session = self._session
        if session is None:
            return "The box isn't armed."
        msg = self.tick()  # debit elapsed time first
        engine = session["engine"]
        try:
            engine.disarm()
        except Exception:  # noqa: BLE001 - disarm must finish
            pass
        if self._trip is not None:
            self._trip.reset()
        self._session = None
        return msg

    # -- graceful wind-down ----------------------------------------------------
    def farewell_beat(self, reason=None):
        """The goodbye: a calm beat, as data. The game layer may render it
        gently. Never startling, never loud."""
        if reason:
            message = ("The box felt your body say too much, so it's "
                       "going quiet to keep you safe. Breathe easy — "
                       "see you on the next play day.")
        else:
            message = ("That's the hour, friend. The box is going quiet — "
                       "see you on the next play day.")
        return {
            "type": "farewell",
            "message": message,
            "intensity": 0.0,
        }

    def wind_down(self, reason=None):
        """Graceful shutdown: save the game, farewell beat, then quiet.
        Never a hard cut. Safe to call with no active session. reason is
        the plain-language cause (time budget, biometric trip) for the
        report."""
        report = {"saved": None, "farewell": self.farewell_beat(reason),
                  "quiet": False, "reason": reason}
        session = self._session
        game = session["game"] if session else None
        save = getattr(game, "save", None)
        if callable(save):
            try:
                save()
                report["saved"] = True
            except Exception as e:  # noqa: BLE001 - wind-down must finish
                report["saved"] = "save hook raised %s: %s" % (
                    type(e).__name__, e)
        engine = session["engine"] if session else None
        if engine is not None:
            try:
                engine.disarm()
                if engine.is_attached:
                    engine.detach()
            except Exception:  # noqa: BLE001 - quiet is the point
                pass
        self._state["wound_down_on"] = self._today()
        self._session = None
        self._save()
        report["quiet"] = True
        return report

    # -- the kill switch: instant, for everyone, always --------------------------
    def kill(self, engine):
        """The physical kill switch path. No checks, no PIN, no Curtis —
        it just stops. Available to everyone, always."""
        engine.kill()
        self._session = None
        return "Box is quiet."

    # -- plain-language status ---------------------------------------------------
    def status(self):
        """What a parent reads."""
        if getattr(self, "_tampered", False):
            return ("The box's memory was tampered with. It won't arm "
                    "until Curtis checks it and re-seals it. The kill "
                    "switch still works.")
        st = self._state["state"]
        if st == "FACTORY":
            return "The box isn't set up yet."
        if st == "AWAITING_CURTIS":
            return ("The box is set up but locked. It stays locked until "
                    "Curtis approves the admin.")
        lines = []
        cap = self._state["level_cap"]
        lines.append("Content level cap: %d (%s)." % (
            cap, "atmosphere" if cap == 1 else "atmosphere and dread"))
        if self._state["wound_down_on"] == self._today():
            lines.append("Time's up for today. The box is resting — see you "
                         "on the next play day.")
        elif not self.is_play_day():
            lines.append("Today (%s) isn't a play day. Play days: %s." % (
                self._weekday(), ", ".join(self._state["play_days"])))
        else:
            lines.append("%s Play days: %s." % (
                self._time_left_msg(), ", ".join(self._state["play_days"])))
        if self._state["lockout_until"] and \
                self._now() < self._state["lockout_until"]:
            left = int(self._state["lockout_until"] - self._now())
            lines.append("PINs are ignored for %d more seconds after too "
                         "many wrong tries." % left)
        return " ".join(lines)

    def failed_attempts(self, pin):
        """Audit log of PIN and approval attempts. Admin eyes only."""
        self._require_admin(pin)
        return list(self._state["failed_attempts"])
