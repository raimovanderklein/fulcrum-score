-- Encounter prediction pipeline schema
-- Trial-level prospective predictions with full audit trail.
-- NOT the GG systems.db (which is agent/regimen-keyed) or the CDS patient db.
-- This is purpose-built for encounter.bio's trial prediction service.

CREATE TABLE IF NOT EXISTS encounter_trials (
    trial_id TEXT PRIMARY KEY,
    nct_id TEXT NOT NULL,
    trial_name TEXT NOT NULL,
    sponsor TEXT NOT NULL,
    indication TEXT NOT NULL,
    domain_id TEXT,
    stage_id TEXT,
    n_target INTEGER,
    arm_count INTEGER,
    primary_endpoint TEXT,
    estimated_readout TEXT,
    status TEXT,
    metadata_verified_date TEXT,
    metadata_verified_source TEXT,
    site_slug TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS encounter_arms (
    arm_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_id TEXT NOT NULL,
    arm_label TEXT NOT NULL,
    arm_role TEXT NOT NULL,
    drug_combo TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (trial_id) REFERENCES encounter_trials(trial_id)
);

CREATE TABLE IF NOT EXISTS encounter_predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_id TEXT NOT NULL,
    experimental_arm_id INTEGER NOT NULL,
    control_arm_id INTEGER NOT NULL,

    direction TEXT NOT NULL,
    confidence TEXT NOT NULL,

    metric TEXT NOT NULL,
    predicted_value REAL,
    predicted_range_low REAL,
    predicted_range_high REAL,

    population_held_in TEXT,
    bottleneck_position INTEGER,
    bottleneck_description TEXT,
    coverage_analysis TEXT,
    structural_reason TEXT,

    falsifier TEXT NOT NULL,

    method TEXT NOT NULL,
    method_trace TEXT,
    analog_trials TEXT,

    prediction_date TEXT NOT NULL,
    prediction_session TEXT,
    superseded_by INTEGER,

    FOREIGN KEY (trial_id) REFERENCES encounter_trials(trial_id),
    FOREIGN KEY (experimental_arm_id) REFERENCES encounter_arms(arm_id),
    FOREIGN KEY (control_arm_id) REFERENCES encounter_arms(arm_id),
    FOREIGN KEY (superseded_by) REFERENCES encounter_predictions(prediction_id)
);

CREATE TABLE IF NOT EXISTS encounter_readouts (
    readout_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_id TEXT NOT NULL,
    readout_date TEXT NOT NULL,
    readout_source TEXT NOT NULL,

    metric TEXT NOT NULL,
    observed_value REAL,
    observed_ci_low REAL,
    observed_ci_high REAL,

    outcome TEXT NOT NULL,
    notes TEXT,

    FOREIGN KEY (trial_id) REFERENCES encounter_trials(trial_id)
);

CREATE TABLE IF NOT EXISTS encounter_scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    readout_id INTEGER NOT NULL,

    direction_correct INTEGER,
    magnitude_in_range INTEGER,
    magnitude_error REAL,
    falsifier_triggered INTEGER,

    hit_type TEXT,

    scored_date TEXT NOT NULL,

    FOREIGN KEY (prediction_id) REFERENCES encounter_predictions(prediction_id),
    FOREIGN KEY (readout_id) REFERENCES encounter_readouts(readout_id)
);

CREATE TABLE IF NOT EXISTS encounter_analogs (
    analog_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    analog_trial_name TEXT NOT NULL,
    analog_source TEXT NOT NULL,
    similarity_basis TEXT,
    contribution_weight REAL,
    notes TEXT,
    FOREIGN KEY (prediction_id) REFERENCES encounter_predictions(prediction_id)
);

CREATE INDEX IF NOT EXISTS idx_predictions_trial ON encounter_predictions(trial_id);
CREATE INDEX IF NOT EXISTS idx_predictions_current ON encounter_predictions(trial_id, superseded_by);
CREATE INDEX IF NOT EXISTS idx_readouts_trial ON encounter_readouts(trial_id);
CREATE INDEX IF NOT EXISTS idx_scores_prediction ON encounter_scores(prediction_id);
CREATE INDEX IF NOT EXISTS idx_analogs_prediction ON encounter_analogs(prediction_id);
