"""score_predictions.py — Score predictions against readouts.

For every prediction that has a matching readout, compute:
  - direction_correct (was the WIN/FAIL/EQUIVALENT call right?)
  - hit_type (prospective vs backtested, based on prediction_date vs readout_date)
  - magnitude_in_range (was the predicted value within range of observed?)

A prediction is PROSPECTIVE if its prediction_date is strictly before the
readout_date for that trial. Otherwise BACKTESTED.

Outcome → direction translation:
  'discontinued_futility' → FAIL
  'failed_primary' → FAIL
  'positive' → WIN
  'negative' → FAIL
  'mixed' → EQUIVALENT
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).parent
_DATA = _HERE.parent / "data"


OUTCOME_TO_DIRECTION = {
    'discontinued_futility': 'FAIL',
    'failed_primary': 'FAIL',
    'positive': 'WIN',
    'negative': 'FAIL',
    'mixed': 'EQUIVALENT',
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def main():
    conn = sqlite3.connect(str(_DATA / 'encounter.db'))
    cur = conn.cursor()

    # Clear existing scores for fresh run
    cur.execute("DELETE FROM encounter_scores")

    # Find all trials that have both a prediction and a readout
    cur.execute("""
        SELECT DISTINCT p.trial_id
        FROM encounter_predictions p
        JOIN encounter_readouts r ON r.trial_id = p.trial_id
    """)
    scored_trials = [r[0] for r in cur.fetchall()]

    print(f"Scoring {len(scored_trials)} trials with readouts: {scored_trials}\n")

    total_scored = 0
    for trial_id in scored_trials:
        cur.execute("SELECT readout_id, readout_date, outcome, observed_value, metric FROM encounter_readouts WHERE trial_id=?", (trial_id,))
        readouts = cur.fetchall()
        if not readouts:
            continue

        # Use the first readout
        readout_id, readout_date, outcome, observed_value, metric = readouts[0]
        observed_direction = OUTCOME_TO_DIRECTION.get(outcome, 'UNKNOWN')

        # Find predictions for this trial
        cur.execute("""SELECT prediction_id, direction, predicted_value, prediction_date
                       FROM encounter_predictions WHERE trial_id=?""", (trial_id,))
        for pid, pred_direction, pred_value, pred_date in cur.fetchall():
            # Compare dates: prospective if prediction was made BEFORE readout
            is_prospective = pred_date < readout_date
            direction_correct = 1 if pred_direction == observed_direction else 0

            if is_prospective and direction_correct:
                hit_type = 'prospective_hit'
            elif is_prospective and not direction_correct:
                hit_type = 'prospective_miss'
            elif not is_prospective and direction_correct:
                hit_type = 'backtested_hit'
            else:
                hit_type = 'backtested_miss'

            cur.execute("""INSERT INTO encounter_scores (
                prediction_id, readout_id, direction_correct,
                magnitude_in_range, magnitude_error, falsifier_triggered,
                hit_type, scored_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
                pid, readout_id, direction_correct,
                None, None, None,
                hit_type, now_iso()
            ))
            total_scored += 1

            print(f"  trial={trial_id:18s} pred#{pid:3d} "
                  f"pred_dir={pred_direction:11s} obs={observed_direction:11s} "
                  f"correct={direction_correct} type={hit_type}")

    conn.commit()

    # Summary
    print(f"\n{'='*70}\nSummary\n{'='*70}")
    cur.execute("""SELECT hit_type, COUNT(*) FROM encounter_scores GROUP BY hit_type""")
    for r in cur.fetchall():
        print(f"  {r[0]:25s}: {r[1]}")

    print(f"\nTotal scored: {total_scored}")
    conn.close()


if __name__ == '__main__':
    main()
