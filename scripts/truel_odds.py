from fractions import Fraction as F
import random

pA, pB, pC = F(1,3), F(2,3), F(1)

def duel(first, second, p1, p2):
    """Probability that `first` wins a duel where first shoots first."""
    w = p1 / (1 - (1-p1)*(1-p2))
    return {first: w, second: 1 - w}

def strategy(a_move):
    # Round 1: A acts, then B, then C (order: weakest first). B and C target the strongest opponent.
    res = {"A": F(0), "B": F(0), "C": F(0)}
    def add(d, w):
        for k, v in d.items(): res[k] += v * w
    if a_move == "air":
        # B shoots C
        add(duel("A", "B", pA, pB), pB)            # C dead, A shoots first vs B
        add(duel("A", "C", pA, pC), 1 - pB)        # B missed, C kills B, A first vs C
    elif a_move == "C":
        # A hits C -> duel B vs A with B shooting first
        add(duel("B", "A", pB, pA), pA)
        # A misses -> same as "air" branch
        add(duel("A", "B", pA, pB), (1-pA) * pB)
        add(duel("A", "C", pA, pC), (1-pA) * (1-pB))
    return res

for m in ["air", "C"]:
    r = strategy(m)
    print(m, {k: f"{v} = {float(v):.1%}" for k, v in r.items()})

# Monte Carlo check of the "air" strategy
def sim():
    alive = {"A": pA, "B": pB, "C": pC}
    order = ["A", "B", "C"]
    first = True
    while len(alive) > 1:
        for s in order:
            if s not in alive or len(alive) == 1: continue
            if s == "A" and len(alive) == 3: continue  # A fires into the air
            target = max((t for t in alive if t != s), key=lambda t: alive[t])
            if random.random() < alive[s]: del alive[target]
    return next(iter(alive))
N = 200_000
cnt = {"A": 0, "B": 0, "C": 0}
for _ in range(N): cnt[sim()] += 1
print("MC air:", {k: f"{v/N:.1%}" for k, v in cnt.items()})
