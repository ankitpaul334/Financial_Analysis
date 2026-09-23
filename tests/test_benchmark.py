"""I6 verify — strong signal passes, borderline goes WATCH, rejected goes NO_ACTION."""
from graph_intel.benchmark import evaluate

def test_benchmark():
    strong = evaluate(overseas_move=4.0, residual=-2.2, zscore=-2.5, hit_rate=0.65,
                      stability=0.7, net_edge_bps=175, novelty=0.9, exposure=0.8, is_new=True)
    assert strong.passes and strong.decision == "ACTION_CANDIDATE", strong
    border = evaluate(overseas_move=1.0, residual=0.5, zscore=1.0, hit_rate=0.4,
                      stability=0.4, net_edge_bps=5, novelty=0.5, exposure=0.5, is_new=True)
    assert not border.passes and border.decision == "WATCH", border
    dead = evaluate(overseas_move=4.0, residual=-2.2, zscore=-2.5, hit_rate=0.65,
                    stability=0.7, net_edge_bps=175, novelty=0.9, exposure=0.8,
                    is_new=True, fx_explains=True)
    assert not dead.passes and dead.decision == "NO_ACTION" and dead.rejects == ["fx_explains"]
    print(f"I6 PASS | strong={strong.score} border={border.score} dead_rejects={dead.rejects}")

if __name__ == "__main__":
    test_benchmark()
