#!/usr/bin/env python3
"""Predict World Cup 2026: match odds + Monte Carlo title race.

Usage:
  python predict.py              # title race (everyone's odds to win it all)
  python predict.py --matches    # win/draw/loss odds for every group-stage match
  python predict.py --group H     # one group's match odds + advancement
  python predict.py --full        # full stage-by-stage table for all 48 teams
"""
import argparse
import itertools
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from engine import match_probs                       # noqa: E402
from tournament import load_teams, run, GROUPS        # noqa: E402
from principles import PRINCIPLES as P                # noqa: E402

DATA = Path(__file__).parent / "data" / "teams.csv"


def pct(x):
    return f"{100 * x:5.1f}%"


def show_matches(teams, only=None):
    by_group = defaultdict(list)
    for t in teams.values():
        by_group[t.group].append(t)
    for g in GROUPS:
        if only and g != only:
            continue
        print(f"\n=== Group {g} ===")
        for a, b in itertools.combinations(by_group[g], 2):
            m = match_probs(a, b, P)
            print(f"  {a.name:>22} vs {b.name:<22}  "
                  f"W {pct(m['win'])}  D {pct(m['draw'])}  L {pct(m['loss'])}  "
                  f"(xG {m['xg_a']:.2f}-{m['xg_b']:.2f})")


def show_group_odds(res, teams, only=None):
    by_group = defaultdict(list)
    for t in teams.values():
        by_group[t.group].append(t)
    for g in GROUPS:
        if only and g != only:
            continue
        print(f"\n=== Group {g}: advancement ===")
        rows = sorted(by_group[g], key=lambda t: res[t.name]["qualify"], reverse=True)
        print(f"  {'team':>22}   win grp   reach R32")
        for t in rows:
            print(f"  {t.name:>22}   {pct(res[t.name]['group_win'])}    {pct(res[t.name]['qualify'])}")


def show_title(res, teams, full=False):
    rows = sorted(teams.values(), key=lambda t: res[t.name]["champion"], reverse=True)
    if full:
        print(f"\n{'team':>22}  qualify   R16    QF     SF    final   CHAMP")
        for t in rows:
            r = res[t.name]
            print(f"{t.name:>22}  {pct(r['qualify'])} {pct(r['r16'])} {pct(r['qf'])} "
                  f"{pct(r['sf'])} {pct(r['final'])} {pct(r['champion'])}")
    else:
        print(f"\n=== Title odds (top 20, {P['n_sims']:,} sims) ===")
        print(f"{'#':>3}  {'team':>22}   reach final   WIN CUP")
        for i, t in enumerate(rows[:20], 1):
            r = res[t.name]
            print(f"{i:>3}  {t.name:>22}     {pct(r['final'])}      {pct(r['champion'])}")
    fav = rows[0]
    print(f"\nMost likely champion: {fav.name} ({pct(res[fav.name]['champion'])})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", action="store_true", help="group-stage match odds")
    ap.add_argument("--group", help="restrict to one group letter")
    ap.add_argument("--full", action="store_true", help="full stage table, all 48")
    args = ap.parse_args()
    teams = load_teams(DATA)

    if args.matches or args.group:
        show_matches(teams, only=args.group)
        res = run(teams, P)
        show_group_odds(res, teams, only=args.group)
        if args.group:
            return
        show_title(res, teams)
        return

    res = run(teams, P)
    show_title(res, teams, full=args.full)


if __name__ == "__main__":
    main()
