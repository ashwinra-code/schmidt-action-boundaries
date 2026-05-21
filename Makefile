PYTHON ?= python3
RUN_FULL_REPRO := $(shell if [ -f code/run_full_repro.sh ]; then printf "code/run_full_repro.sh"; else printf "run_full_repro.sh"; fi)
RUN_ALL := $(shell if [ -f code/run_all.sh ]; then printf "code/run_all.sh"; else printf "run_all.sh"; fi)
SRC_DIR := $(shell if [ -d code/src ]; then printf "code/src"; else printf "src"; fi)

.PHONY: preflight reproduce strict allow-frozen-null assert clean smoke artifact

preflight:
	bash $(RUN_FULL_REPRO) --preflight

reproduce:
	bash $(RUN_FULL_REPRO) --strict

strict:
	bash $(RUN_FULL_REPRO) --strict

allow-frozen-null:
	bash $(RUN_FULL_REPRO) --allow-frozen-null

assert:
	$(PYTHON) $(SRC_DIR)/09_assert_final_reproduction.py --mode strict

clean:
	rm -rf results/full_repro audit/full_repro data/splits/full_repro

smoke:
	$(PYTHON) $(SRC_DIR)/10_clean_environment_probe.py

artifact:
	bash $(RUN_ALL)
