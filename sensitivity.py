#!/usr/bin/env python3
"""Sensitivity analysis: sweep a principle and watch the title odds move.

Usage:
  python sensitivity.py home_advantage_elo 0 40 80 120 160
  python sensitivity.py goal_elo_beta 0.25 0.35 0.45 0.55 0.65
  python sensitivity.py form_weight 0 1 2 3
  python sensitivity.py --teams Mexico,Spain,Argentina home_advantage_elo 0 80 160

Each column is one value of the knob; each row a team's title %. The tornado at
the end ranks which teams are most sensitive to the knob across the swept range.
"""
import argparse
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from tournament import load_teams, run            # noqa: E402
from principles import PRINCIPLES as BASE          # noqa: E402

DATA = Path(__file__).parent / "data" / "teams.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("knob", help="principle key to sweep, e.g. home_advantage_elo")
    ap.add_argument("values", nargs="+", help="values to try")
    ap.add_argument("--teams", help="comma-separated subset; default = top movers")
    ap.add_argument("--sims", type=int, help="override n_sims (lower = faster sweep)")
    args = ap.parse_args()

    if args.knob not in BASE:
        sys.exit(f"unknown knob '{args.knob}'. options: {', '.join(BASE)}")
    cast = type(BASE[args.knob])
    vals = [cast(v) for v in args.values]
    teams = load_teams(DATA)

    cols = {}
    for v in vals:
        P = copy.deepcopy(BASE)
        P[args.knob] = v
        if args.sims:
            P["n_sims"] = args.sims
        cols[v] = {n: r["champion"] for n, r in run(teams, P).items()}

    if args.teams:
        watch = [t.strip() for t in args.teams.split(",")]
    else:
        last = cols[vals[-1]]
        watch = sorted(teams, key=lambda n: last[n], reverse=True)[:12]

    head = "  ".join(f"{v:>8}" for v in vals)
    print(f"\nTitle odds vs {args.knob}\n")
    print(f"{'team':>22}  {head}")
    swing = {}
    for n in watch:
        series = [cols[v][n] for v in vals]
        swing[n] = max(series) - min(series)
        cells = "  ".join(f"{100*s:7.1f}%" for s in series)
        print(f"{n:>22}  {cells}")

    print(f"\nMost sensitive to {args.knob} (swing across range):")
    for n in sorted(swing, key=swing.get, reverse=True)[:8]:
        print(f"  {n:>22}  +/- {100*swing[n]:.1f} pts")


if __name__ == "__main__":
    main()
