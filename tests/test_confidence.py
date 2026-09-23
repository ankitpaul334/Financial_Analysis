"""I2 verify — direct edge outscores 2-hop; components inspectable."""
from graph_intel.confidence import score

def test_confidence():
    direct = score(source_tier=1, zscore=2.5, stability=0.8, strength=0.9, depth=0)
    two_hop = score(source_tier=1, zscore=2.5, stability=0.8, strength=0.9, depth=2)
    assert direct["confidence"] > two_hop["confidence"], (direct, two_hop)
    assert set(direct["components"]) == {"source", "z", "stability", "strength"}
    weak = score(source_tier=8, zscore=0.2, stability=0.3, strength=0.2, depth=0)
    assert direct["confidence"] > weak["confidence"]
    print(f"I2 PASS | direct={direct['confidence']} two_hop={two_hop['confidence']} weak={weak['confidence']}")

if __name__ == "__main__":
    test_confidence()
