# encounter-bio top-level Makefile
# The website lives at the repo root. The prediction pipeline lives in pipeline/.
# This Makefile delegates to the pipeline's Makefile and runs Flask locally.

PY := python3
PIPELINE := pipeline

.PHONY: help all dev clean fresh sync test pipeline-all pipeline-fresh pipeline-sync

help:
	@echo "encounter-bio targets:"
	@echo "  make pipeline-all     — rebuild predictions from formula.predict_orr"
	@echo "  make pipeline-fresh   — clean + rebuild pipeline from scratch"
	@echo "  make pipeline-sync    — rebuild + check drift vs reports.json"
	@echo "  make sync             — alias for pipeline-sync"
	@echo "  make dev              — run Flask locally on port 8000"
	@echo "  make test             — pipeline smoke test"
	@echo "  make clean            — remove pipeline-generated files"

# Rebuild the pipeline (formula.predict_orr against all trials)
pipeline-all:
	cd $(PIPELINE) && $(MAKE) all

pipeline-fresh:
	cd $(PIPELINE) && $(MAKE) fresh

pipeline-sync:
	cd $(PIPELINE) && $(MAKE) sync

sync: pipeline-sync

# Local Flask dev server
dev:
	$(PY) app.py

clean:
	cd $(PIPELINE) && $(MAKE) clean

test:
	cd $(PIPELINE) && $(MAKE) test
