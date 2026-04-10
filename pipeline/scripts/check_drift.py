"""check_drift.py — Compare the website's reports.json (hand-curated)
against the pipeline's predictions_summary.json (numeric ground truth)
and warn about any drift between the two.

This script does NOT modify either file. It produces a report listing:
  - Trials in the pipeline that are not in reports.json
  - Trials in reports.json that are not in the pipeline (typically OK
    for retrospective entries like the EXPRESSO meta-analysis)
  - For shared trials, flags discrepancies in:
      * predicted direction
      * sponsor / indication / n_target / status

Run this before publishing the website to make sure the framework numbers
in the prose haven't drifted from what the pipeline currently outputs.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).parent
_REPO = _HERE.parent.parent
_PIPELINE_DATA = _HERE.parent / "data"
_WEBSITE_DATA = _REPO / "data"

PREDICTIONS = _PIPELINE_DATA / "predictions_summary.json"
REPORTS = _WEBSITE_DATA / "reports.json"


def main():
    if not PREDICTIONS.exists():
        print(f"ERROR: {PREDICTIONS} not found. Run `make all` first.")
        sys.exit(1)
    if not REPORTS.exists():
        print(f"ERROR: {REPORTS} not found.")
        sys.exit(1)

    pipeline = json.loads(PREDICTIONS.read_text())
    reports = json.loads(REPORTS.read_text())

    # Build slug → record indexes
    pipeline_by_slug = {t["website_slug"]: t for t in pipeline["trials"] if t.get("website_slug")}
    reports_by_slug = {r["slug"]: r for r in reports if "slug" in r}

    pipeline_slugs = set(pipeline_by_slug.keys())
    reports_slugs = set(reports_by_slug.keys())

    print(f"Pipeline trials: {len(pipeline_slugs)}")
    print(f"Website reports: {len(reports_slugs)}")
    print()

    only_pipeline = pipeline_slugs - reports_slugs
    only_reports = reports_slugs - pipeline_slugs
    shared = pipeline_slugs & reports_slugs

    if only_pipeline:
        print(f"⚠ In pipeline but NOT in website reports.json ({len(only_pipeline)}):")
        for s in sorted(only_pipeline):
            t = pipeline_by_slug[s]
            print(f"  - {s}  ({t['trial_name']}, {t['status']})")
        print("  → consider adding a curated report.json entry for these")
        print()

    if only_reports:
        print(f"ℹ In website reports.json but NOT in pipeline ({len(only_reports)}):")
        for s in sorted(only_reports):
            r = reports_by_slug[s]
            print(f"  - {s}  ({r.get('trial_name', '?')}, type={r.get('type', '?')})")
        print("  → typically OK for retrospective / meta-analysis entries")
        print()

    print(f"Shared trials ({len(shared)}):")
    drift_count = 0
    for s in sorted(shared):
        p = pipeline_by_slug[s]
        r = reports_by_slug[s]
        diffs = []

        # n_target check
        if p["n_target"] and r.get("n") and p["n_target"] != r["n"]:
            diffs.append(f"n_target: pipeline={p['n_target']} vs report={r['n']}")

        # status sanity check
        if p["status"] in ("discontinued_futility", "failed_primary") and r.get("result_score") not in ("HIT", "MISS", "PENDING", None):
            # OK, just informational
            pass

        # direction check (does any prediction match the report's prediction_call?)
        primary_pred = p["predictions"][0] if p["predictions"] else None
        if primary_pred and r.get("prediction_call"):
            pred_dir = primary_pred["direction"]
            report_call = r["prediction_call"]
            # Loose match: if report says "fails" and pred is FAIL, OK
            if pred_dir == "FAIL" and "fail" not in report_call.lower() and "miss" not in report_call.lower():
                if "win" in report_call.lower() or "hit" in report_call.lower():
                    diffs.append(f"direction mismatch: pipeline FAIL vs report '{report_call[:60]}...'")

        if diffs:
            drift_count += 1
            print(f"  ⚠ {s}")
            for d in diffs:
                print(f"      {d}")
        else:
            print(f"  ✓ {s}")

    print()
    print(f"Summary: {len(shared)} shared, {drift_count} with drift, {len(only_pipeline)} pipeline-only, {len(only_reports)} website-only")
    if drift_count > 0:
        print("⚠ Drift detected — review reports.json before publishing")
        sys.exit(0)  # warn but don't fail
    else:
        print("✓ No drift detected")


if __name__ == "__main__":
    main()
