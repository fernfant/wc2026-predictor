"""Match engine: effective ratings -> expected goals -> simulated scorelines."""
import math
import random


class Team:
    def __init__(self, name, group, confed, elo, form, host):
        self.name = name
        self.group = group
        self.confed = confed
        self.elo = float(elo)
        self.form = float(form)
        self.host = bool(int(host))


def effective_elo(t, P):
    """Base Elo adjusted by home advantage and recent form."""
    e = t.elo
    if t.host:
        e += P["home_advantage_elo"]
    elif t.confed == "CONCACAF":
        e += P["concacaf_region_elo"]
    e += P["form_weight"] * t.form
    return e


def expected_goals(a, b, P):
    """Log-linear Poisson means from the effective-Elo gap."""
    diff = (effective_elo(a, P) - effective_elo(b, P)) / P["elo_scale"]
    mu = P["avg_goals_per_team"]
    la = mu * math.exp(P["goal_elo_beta"] * diff)
    lb = mu * math.exp(-P["goal_elo_beta"] * diff)
    return la, lb


def _poisson(lam, rng):
    # Knuth sampler; goals are small so this is fast.
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def sim_score(a, b, P, rng):
    la, lb = expected_goals(a, b, P)
    return _poisson(la, rng), _poisson(lb, rng)


def win_expectancy(a, b, P):
    """Elo win-expectancy of a over b (used for shootouts)."""
    diff = effective_elo(a, P) - effective_elo(b, P)
    return 1.0 / (1.0 + 10 ** (-diff / P["elo_scale"]))


def sim_knockout(a, b, P, rng):
    """Return the winning team; level scores go to a skill-weighted shootout."""
    ga, gb = sim_score(a, b, P, rng)
    if ga > gb:
        return a
    if gb > ga:
        return b
    we = win_expectancy(a, b, P)
    p = 0.5 + (we - 0.5) * P["penalty_skill"]
    return a if rng.random() < p else b


def match_probs(a, b, P, gmax=12):
    """Analytic W/D/L + expected goals for a fixture (no sampling)."""
    la, lb = expected_goals(a, b, P)
    def pmf(lam, k):
        return math.exp(-lam) * lam ** k / math.factorial(k)
    pa = pb = pd = 0.0
    for i in range(gmax):
        for j in range(gmax):
            p = pmf(la, i) * pmf(lb, j)
            if i > j:
                pa += p
            elif j > i:
                pb += p
            else:
                pd += p
    return {"win": pa, "draw": pd, "loss": pb, "xg_a": la, "xg_b": lb}
