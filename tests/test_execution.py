"""I8 verify — deny unsigned/expired/duplicate/unauthorized; research cannot touch broker."""
from datetime import datetime, timedelta, timezone
from graph_intel.execution.broker import Auth, PaperBroker

SECRET = "test-secret"

def _auth(**kw):
    base = dict(signal_id="sig_1", asset="X", action="BUY", qty=10.0, max_loss=1000.0,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
                risk_approved=True)
    base.update(kw)
    return Auth(**base)

def test_execution():
    b = PaperBroker()
    b.set_limit("X", 100.0)
    a = _auth(); a.sign(SECRET)
    assert b.execute(a, SECRET, True, True, "k1")["executed"] is True
    assert b.execute(a, SECRET, True, True, "k1")["reason"] == "duplicate"
    bad = _auth(); bad.signature = "forged"
    assert b.execute(bad, SECRET, True, True, "k2")["reason"] == "bad_signature"
    exp = _auth(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)); exp.sign(SECRET)
    assert b.execute(exp, SECRET, True, True, "k3")["reason"] == "expired"
    assert b.execute(a, SECRET, False, True, "k4")["reason"] == "not_approved"
    big = _auth(qty=1000.0); big.sign(SECRET)
    assert b.execute(big, SECRET, True, True, "k5")["reason"] == "position_limit"
    b.kill_switch = True
    assert b.execute(a, SECRET, True, True, "k6")["reason"] == "kill_switch"
    kinds = [r["kind"] for r in b.audit()]
    assert "fill" in kinds and "deny" in kinds
    import graph_intel.execution.broker as mod
    assert "graph_intel.agents" not in open(mod.__file__).read(), "no research imports"
    print("I8 PASS | fill_once denies=5 audit_ok=True isolated=True")

if __name__ == "__main__":
    test_execution()
