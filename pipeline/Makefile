# encounter-pipeline Makefile
# Run `make all` for a clean end-to-end rebuild from source.

PY := python3
SCRIPTS := scripts
DATA := data
DOCS := docs

ENCOUNTER_DB := $(DATA)/encounter.db
WORKCOPY := $(DATA)/gg_systems_workcopy.db
SYSTEMS_BASE := $(DATA)/systems_base.db
V3_MD := $(DOCS)/v3_scorecard.md
PREDICTIONS_JSON := $(DATA)/predictions_summary.json

.PHONY: all clean fresh test summary drift sync

all: $(V3_MD) summary

# Default: rebuild everything from scratch
fresh: clean all

clean:
	rm -f $(ENCOUNTER_DB) $(WORKCOPY) $(PREDICTIONS_JSON)
	@echo "Cleaned generated databases and summaries."

# Step 1: empty schema
$(ENCOUNTER_DB):
	cd $(SCRIPTS) && $(PY) init_db.py

# Step 2-3: seed trials + arms
seed-trials: $(ENCOUNTER_DB)
	cd $(SCRIPTS) && $(PY) seed_trials.py
	cd $(SCRIPTS) && $(PY) seed_dellphi312.py

# Step 4-5: extend GG framework work copy
$(WORKCOPY): $(SYSTEMS_BASE)
	cp $(SYSTEMS_BASE) $(WORKCOPY)
	cd $(SCRIPTS) && $(PY) add_missing_agents.py
	cd $(SCRIPTS) && $(PY) add_sclc_domain.py

# Step 6: run formula-driven predictions
predictions: seed-trials $(WORKCOPY)
	cd $(SCRIPTS) && $(PY) make_predictions_all.py

# Step 7: add backtested historical hits
backtested: predictions
	
# Step 8: score predictions vs readouts
scored: backtested
	
# Step 9: generate v3 markdown
$(V3_MD): scored
	cd $(SCRIPTS) && $(PY) export_v3.py

# Step 10: emit predictions_summary.json for the website
summary: $(V3_MD)
	cd $(SCRIPTS) && $(PY) build_predictions_summary.py

# Drift check: compare website reports.json against pipeline summary
drift: summary
	cd $(SCRIPTS) && $(PY) check_drift.py

# Full sync: rebuild everything + check drift against website prose
sync: fresh drift
	@echo "Pipeline rebuilt and drift checked against website reports.json."

# Quick smoke test — just verify init runs
test:
	cd $(SCRIPTS) && $(PY) init_db.py
	@echo "OK: schema initializes cleanly"
