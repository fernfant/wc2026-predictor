# World Cup 2026 Predictor

A hybrid **Elo + Poisson** Monte Carlo simulator for the 48-team 2026 World Cup.
Gives win/draw/loss odds for every match and each team's odds of winning the cup —
and lets you tweak a small set of **principles** to see how sensitive the forecast is.

## Quick start

```bash
cd wc2026-predictor
python3 predict.py                 # title race — everyone's odds to win it all
python3 predict.py --matches       # W/D/L odds for every group-stage match
python3 predict.py --group H       # one group: match odds + advancement
python3 predict.py --full          # stage-by-stage table (qualify→R16→QF→SF→final→champ)

python3 sensitivity.py home_advantage_elo 0 40 80 120 160
python3 sensitivity.py goal_elo_beta 0.25 0.35 0.45 0.55
python3 sensitivity.py --teams Mexico,United States home_advantage_elo 0 80 160

python3 calibrate.py --write              # fit knobs to actual group results
python3 predict.py --actual --calibrated  # retrofit forecast from the real R32
```

Pure Python stdlib — no dependencies. ~2.5s for 20,000 sims.

## How the model works

1. **Strength** — each team has an Elo rating (`data/teams.csv`, real values from
   eloratings.net / Wikipedia, 2026-06-24).
2. **Effective rating** — Elo adjusted by two knobs: *home advantage* (hosts) and
   *recent form*. See `principles.py`.
3. **Goals** — the effective-Elo gap feeds a log-linear Poisson model:
   `λ = avg_goals · exp(±β · Δrating/scale)`. Sampling two Poissons gives a
   scoreline → win/draw/loss **and** the goals needed for group tiebreakers.
4. **Tournament** — 12 groups (round-robin, FIFA tiebreakers: pts→GD→GF), top 2 +
   8 best thirds advance; the official FIFA R32 bracket template (incl. the
   third-place allocation) runs through to the final. Knockout ties go to a
   skill-weighted shootout. Repeated `n_sims` times → probabilities.

## The principles (your sensitivity knobs)

All live in [`principles.py`](principles.py), each documented inline:

| Knob | What it controls |
|---|---|
| `home_advantage_elo` | Elo boost for hosts USA/Canada/Mexico |
| `concacaf_region_elo` | smaller boost for other CONCACAF teams |
| `form_weight` | multiplier on each team's `form` column |
| `goal_elo_beta` | how hard rating gaps bend goals → predictability vs upsets |
| `elo_scale` | Elo divisor — parity vs amplified favourites |
| `avg_goals_per_team` | overall scoring environment |
| `penalty_skill` | how much shootouts favour the better team (0 = coin flip) |
| `n_sims`, `random_seed` | run count / reproducibility |

**Editing inputs:** change any team's `elo` in `data/teams.csv`, or fill the
`form` column (Elo points: `+30` hot, `-30` cold) and set `form_weight` > 0 to
make it bite. Form is `0` for everyone by default, so that knob is inert until
you supply opinions.

## Fine-tuning on actual results

Once the group stage is played, `calibrate.py` retrofits the model to it. Holding
the pre-tournament Elo fixed, it grid-searches `avg_goals_per_team`,
`goal_elo_beta` and `home_advantage_elo` to minimise squared error between each
team's **expected** (goals-for, goals-against, points) over its three real
fixtures and the **observed** values in [`data/group_results.csv`](data/group_results.csv).

Fitting to the real 2026 group stage (215 goals, 2.99/match — blowout-heavy)
pushes `goal_elo_beta` 0.45 → 0.80 and `home_advantage_elo` 80 → 120 (fit error
−22.5%). `--write` saves these to `principles_calibrated.py`; `predict.py --actual`
then forecasts the knockout from the 32 teams that actually qualified
(`ACTUAL_R32` in `tournament.py`). The sharper model concentrates title odds at
the top — e.g. Argentina 16% → 25% on the same field.

## Caveats

- **Form defaults to 0** — the form knob does nothing until you populate the column.
- **Best-third allocation** uses a valid constrained matching of the 8 qualifying
  third-place groups to the 8 FIFA slots; it respects the official allowed-group
  table but may not reproduce FIFA's exact tie-break ordering in rare cases.
- **R16→final adjacencies** in `tournament.py` use a balanced bracket; the R32
  pairings are the official template. Exact later-round cross-pairings affect
  individual *paths*, not much the overall title odds. Edit `R32` / the pairing
  loop in `tournament.py` to match the official bracket precisely.
- The tournament is already underway (sim predicts from the **pre-tournament**
  state). To re-forecast from a live state, edit `data/teams.csv` to only the
  surviving teams, or hard-set group results.

## Files

```
principles.py        the tunable assumptions — start here
data/teams.csv       48 teams: group, confederation, Elo, form, host flag
src/engine.py        Elo → expected goals → scoreline; match probabilities
src/tournament.py    groups, best-thirds, knockout bracket, Monte Carlo loop
predict.py           CLI: match odds + title race
sensitivity.py       sweep a principle, tabulate how the odds respond
```
