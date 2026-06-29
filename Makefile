# Reproduction targets for "Performative Stability in Signal Discovery"
PY ?= python
SIM = src/simulations
EMP = src/empirical

.PHONY: all simulations empirical figures clean help

help:
	@echo "make simulations  - run all synthetic Monte Carlo experiments"
	@echo "make empirical    - run OSAP decay + placebo (needs data/, see data/README.md)"
	@echo "make figures       - rebuild simulation figures from saved runs"
	@echo "make all           - simulations + figures"
	@echo "make clean         - remove generated artifacts"

simulations:
	$(PY) $(SIM)/exp1_dichotomy.py
	$(PY) $(SIM)/exp2_phase.py
	$(PY) $(SIM)/exp3_momentum.py
	$(PY) $(SIM)/exp4_robust.py
	$(PY) $(SIM)/exp5_bifurcation.py
	$(PY) $(SIM)/exp6_transient.py

figures:
	$(PY) $(SIM)/make_figs.py
	$(PY) $(SIM)/make_fig4.py
	$(PY) $(SIM)/make_fig56.py

empirical:
	$(PY) $(EMP)/decay_windows.py
	$(PY) $(EMP)/placebo_decay.py

all: simulations figures

clean:
	rm -f $(SIM)/*.npz $(SIM)/*summary*.json figures/*_results.csv
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
