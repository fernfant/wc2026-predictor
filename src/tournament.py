"""48-team World Cup 2026 tournament: groups -> best thirds -> knockout bracket."""
import csv
import itertools
import random
from collections import defaultdict
from pathlib import Path

from engine import Team, sim_score, sim_knockout

GROUPS = list("ABCDEFGHIJKL")

# Official FIFA R32 template. Each entry: (slot_a, slot_b).
# "1A"=winner A, "2A"=runner-up A, "3:ID"=a best-third slot (filled per sim).
R32 = [
    ("2A", "2B"), ("1E", "3:74"), ("1F", "2C"), ("1C", "2F"),
    ("1I", "3:77"), ("2E", "2I"), ("1A", "3:79"), ("1L", "3:80"),
    ("1D", "3:81"), ("1G", "3:82"), ("2K", "2L"), ("1H", "2J"),
    ("1B", "3:85"), ("1J", "2H"), ("1K", "3:87"), ("2D", "2G"),
]

# Which groups may feed each third-place slot (FIFA allocation table).
THIRD_SLOTS = {
    "74": set("ABCDF"), "77": set("CDFGH"), "79": set("CEFHI"),
    "80": set("EHIJK"), "81": set("BEFIJ"), "82": set("AEHIJ"),
    "85": set("EFGIJ"), "87": set("DEIJL"),
}


def load_teams(path):
    teams = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            t = Team(r["team"], r["group"], r["confed"], r["elo"], r["form"], r["host"],
                     r.get("avg_age", 27.5), r.get("depth", 3.0))
            teams[t.name] = t
    return teams


def _standings(group_teams, P, rng):
    pts = defaultdict(int); gf = defaultdict(int); ga = defaultdict(int)
    for a, b in itertools.combinations(group_teams, 2):
        x, y = sim_score(a, b, P, rng)
        gf[a] += x; ga[a] += y; gf[b] += y; ga[b] += x
        if x > y: pts[a] += 3
        elif y > x: pts[b] += 3
        else: pts[a] += 1; pts[b] += 1
    key = lambda t: (pts[t], gf[t] - ga[t], gf[t], rng.random())
    ranked = sorted(group_teams, key=key, reverse=True)
    rec = {t: (pts[t], gf[t] - ga[t], gf[t]) for t in group_teams}
    return ranked, rec


def _assign_thirds(qualifying_groups):
    """Bipartite match the 8 qualifying third-place groups to the 8 slots."""
    match = {}  # slot_id -> group
    slots = list(THIRD_SLOTS.items())
    def try_assign(g, seen):
        for sid, allowed in slots:
            if g in allowed and sid not in seen:
                seen.add(sid)
                if sid not in match or try_assign(match[sid], seen):
                    match[sid] = g
                    return True
        return False
    for g in qualifying_groups:
        try_assign(g, set())
    return {sid: g for sid, g in match.items()}  # slot_id -> group letter


def simulate_once(teams, P, rng):
    by_group = defaultdict(list)
    for t in teams.values():
        by_group[t.group].append(t)

    winners, runners = {}, {}
    thirds = []  # (rec_tuple, team, group)
    reached = defaultdict(set)  # team.name -> {stages}
    for g in GROUPS:
        ranked, rec = _standings(by_group[g], P, rng)
        winners[g], runners[g] = ranked[0], ranked[1]
        thirds.append((rec[ranked[2]], ranked[2], g))
        for t in ranked[:2]:
            reached[t.name].add("qualify")

    # 8 best third-placed teams, ranked by (pts, GD, GF).
    thirds.sort(key=lambda x: (x[0][0], x[0][1], x[0][2], rng.random()), reverse=True)
    best = thirds[:8]
    third_by_group = {g: t for _, t, g in best}
    for _, t, _ in best:
        reached[t.name].add("qualify")

    slot_group = _assign_thirds([g for _, _, g in best])

    def resolve(slot):
        kind = slot[0]
        if slot.startswith("3:"):
            return third_by_group[slot_group[slot[2:]]]
        return winners[slot[1]] if kind == "1" else runners[slot[1]]

    # Round of 32 (3 group games already played), then 4/5/6/7 matches deep.
    bracket = [sim_knockout(resolve(a), resolve(b), P, rng, 3) for a, b in R32]
    for w in bracket:
        reached[w.name].add("r16")
    for stage, played in (("qf", 4), ("sf", 5), ("final", 6)):
        nxt = []
        for i in range(0, len(bracket), 2):
            w = sim_knockout(bracket[i], bracket[i + 1], P, rng, played)
            reached[w.name].add(stage)
            nxt.append(w)
        bracket = nxt
    champ = sim_knockout(bracket[0], bracket[1], P, rng, 7) if len(bracket) == 2 else bracket[0]
    reached[champ.name].add("champion")
    return winners, runners, reached, champ.name


# Actual round-of-32 field (reconstructed from real group results + FIFA
# third-place allocation), in bracket order M73..M88.
ACTUAL_R32 = [
    ("South Africa", "Canada"), ("Germany", "Paraguay"),
    ("Netherlands", "Morocco"), ("Brazil", "Japan"),
    ("France", "Sweden"), ("Ivory Coast", "Norway"),
    ("Mexico", "Ecuador"), ("England", "DR Congo"),
    ("United States", "Bosnia and Herzegovina"), ("Belgium", "Senegal"),
    ("Portugal", "Croatia"), ("Spain", "Austria"),
    ("Switzerland", "Algeria"), ("Argentina", "Cape Verde"),
    ("Colombia", "Ghana"), ("Australia", "Egypt"),
]


def run_from_r32(teams, P, field=ACTUAL_R32):
    """Monte Carlo the knockout from a fixed R32 field; title odds among the 32."""
    rng = random.Random(P["random_seed"])
    n = P["n_sims"]
    stages = ("r16", "qf", "sf", "final", "champion")
    pairs = [(teams[a], teams[b]) for a, b in field]
    tally = {t.name: defaultdict(int) for p in pairs for t in p}
    for _ in range(n):
        bracket = [sim_knockout(a, b, P, rng, 3) for a, b in pairs]
        for w in bracket:
            tally[w.name]["r16"] += 1
        for stage, played in (("qf", 4), ("sf", 5), ("final", 6)):
            nxt = []
            for i in range(0, len(bracket), 2):
                w = sim_knockout(bracket[i], bracket[i + 1], P, rng, played)
                tally[w.name][stage] += 1
                nxt.append(w)
            bracket = nxt
        tally[sim_knockout(bracket[0], bracket[1], P, rng, 7).name]["champion"] += 1
    return {nm: {s: tally[nm][s] / n for s in stages} for nm in tally}


def run(teams, P):
    rng = random.Random(P["random_seed"])
    n = P["n_sims"]
    stages = ("qualify", "r16", "qf", "sf", "final", "champion")
    tally = {name: defaultdict(int) for name in teams}
    grp_win = defaultdict(int)
    for _ in range(n):
        winners, _, reached, _ = simulate_once(teams, P, rng)
        for g, t in winners.items():
            grp_win[t.name] += 1
        for name, st in reached.items():
            for s in st:
                tally[name][s] += 1
    out = {}
    for name in teams:
        out[name] = {s: tally[name][s] / n for s in stages}
        out[name]["group_win"] = grp_win[name] / n
    return out
