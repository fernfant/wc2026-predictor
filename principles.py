"""
PRINCIPLES — the tunable assumptions of the predictor.

Every number here is a lever. Change one, re-run `predict.py`, and watch how the
odds move. `sensitivity.py` sweeps these automatically. Nothing else in the model
is hard-coded: if a belief about football lives anywhere, it lives here.

The model is a hybrid:
  - ELO gives each team a strength number (data/teams.csv).
  - A POISSON goals model turns the strength GAP between two teams into expected
    goals for each side, then draws a random scoreline. That yields win/draw/loss
    AND plausible scorelines (needed for group tiebreakers).
"""

PRINCIPLES = {
    # --- Core Elo -> probability ---
    # Elo divisor. Larger = rating gaps matter LESS (more parity, more upsets).
    # Smaller = the favourite's edge is amplified. 400 is the classic value.
    "elo_scale": 400.0,

    # --- Poisson goals model ---
    # Baseline goals each team scores in a perfectly even match. Sets the overall
    # scoring environment (~2.6 goals/game total at 1.30).
    "avg_goals_per_team": 1.30,

    # How strongly an Elo gap bends expected goals. Higher = strong teams win
    # bigger and more reliably (fewer upsets). Lower = flatter, more chaos.
    # This is the single biggest "predictability vs randomness" knob.
    "goal_elo_beta": 0.45,

    # --- KNOB 1: HOME ADVANTAGE ---
    # Elo points added to the three HOSTS (USA, Canada, Mexico) for every match
    # they play, reflecting crowd, travel, familiarity. ~70-100 is typical for
    # a host nation. Set to 0 to remove home advantage entirely.
    "home_advantage_elo": 80.0,

    # Smaller boost for non-host CONCACAF teams (Haiti, Panama, Curacao):
    # close to home, familiar conditions, friendly crowds. Set 0 to disable.
    "concacaf_region_elo": 15.0,

    # --- KNOB 2: RECENT FORM ---
    # Multiplier applied to each team's `form` column in data/teams.csv (form is
    # expressed in Elo points: +30 = hot streak, -30 = slumping).
    #   0.0 = ignore form, pure long-run rating.
    #   1.0 = take the form column at face value.
    #   2.0 = double down on momentum.
    # Defaults: form column is 0 for everyone, so this is inert until you fill it
    # in. That's deliberate — set the numbers you believe, then sweep this weight.
    "form_weight": 1.0,

    # --- KNOB 3: FATIGUE (age + squad depth) ---
    # Teams tire as the tournament drags on. The penalty grows each round, is
    # amplified by an OLD squad and softened by a DEEP one (more rotation). It's
    # applied as an Elo penalty per team, so it CANCELS between similar squads and
    # only swings a match when an old/thin team meets a young/deep one late on.
    #   penalty = fatigue_per_match_elo × matches_played × age_mult × depth_mult
    # Drives off each squad's average age + depth rating in data/teams.csv, so the
    # individual players (their ages) and bench strength feed straight in.
    # Set fatigue_per_match_elo = 0 to switch fatigue off entirely.
    "fatigue_per_match_elo": 7.0,    # Elo lost per cumulative match, at baseline age/depth
    "fatigue_age_baseline": 27.5,    # tournament-average age; older squads pay more
    "fatigue_age_sensitivity": 0.10, # +10% fatigue per year above the baseline age
    "fatigue_depth_baseline": 3.0,   # average depth rating (1=very thin … 5=two strong XIs)
    "fatigue_depth_relief": 0.15,    # −15% fatigue per depth point above baseline

    # --- Knockout penalty shootouts ---
    # If a knockout match is level after a simulated 90 mins, the winner is decided
    # here. 0.0 = pure coin flip. 1.0 = the better team wins as often as their Elo
    # win-expectancy says. ~0.30 reflects that shootouts are mostly a lottery.
    "penalty_skill": 0.30,

    # --- Simulation ---
    "n_sims": 20000,     # Monte Carlo runs. 20k is stable; drop to 2k for speed.
    "random_seed": 42,   # Fix for reproducible runs; set None for fresh randomness.
}
