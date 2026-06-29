# Performative Stability in Signal Discovery

<!-- Zenodo concept DOI (always resolves to the latest version) -->
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21038235.svg)](https://doi.org/10.5281/zenodo.21038235)

Replication code for **"Performative Stability in Signal Discovery: Deployment,
Crowding, and the Decay–Revival Cycle"** by Alejandro Rodríguez Domínguez and
Miquel Noguer i Alonso.

A trading signal discovered from market data and then deployed as a rule changes
the distribution from which the next signal is estimated. The paper models this
discovery–deployment feedback as a graph-valued self-map on a finite set,
derives when it is stable and when it cycles, and examines two ingredients of
the mechanism in public data. Deployment is treated as an intervention on the
market law; the discovery operator is **not** claimed to recover a true causal
graph, and the results hold for any graph-valued discovery rule.

This repository reproduces every figure and every reported number.

## Repository layout

```
performative-discovery/
├── paper/                 compiled PDF and LaTeX source
├── src/
│   ├── simulations/       synthetic Monte Carlo experiments (Figures 3–7)
│   └── empirical/         OSAP decay + placebo (Table 3)
├── notebooks/             end-to-end empirical notebooks (decay, comomentum)
├── figures/               pre-built figures and generated result CSVs
├── data/                  place public datasets here (not redistributed)
├── requirements.txt       Python dependencies
├── Makefile               one-command reproduction targets
├── CITATION.cff           how to cite this work
└── LICENSE                MIT
```

## Quick start

```bash
git clone https://github.com/<user>/performative-discovery.git
cd performative-discovery
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Simulations (no external data needed)
make simulations

# 2. Empirical (after placing OSAP data in data/, see data/README.md)
make empirical
```

## What reproduces what

| Output | Command | Data |
|--------|---------|------|
| Figures 3a, 3b (threshold, phase) | `python src/simulations/exp1_dichotomy.py`, `exp2_phase.py` | synthetic |
| Figure 4 (robustness, Wilson bands) | `python src/simulations/exp4_robust.py` | synthetic |
| Figure 5 (bifurcation) | `python src/simulations/exp5_bifurcation.py` | synthetic |
| Figure 6 (transient, period) | `python src/simulations/exp6_transient.py` | synthetic |
| Figure 7 (momentum panel) | `python src/simulations/exp3_momentum.py` | synthetic |
| Table 3, predictor rows | `python src/empirical/decay_windows.py` | OSAP |
| Table 3, placebo row | `python src/empirical/placebo_decay.py` | OSAP |
| Figure 8 (decay event-time) | `notebooks/osap_decay.ipynb` | OSAP |
| Figure 9 (comomentum) | `notebooks/comomentum.ipynb` | daily equity (Stooq) |

## Headline results

**Decay (OSAP, Table 3).** Across published predictors the mean monthly
long-short edge falls from 0.62% in sample to 0.30% post-publication, a decline
of 0.32pp (52%), paired *t* = 7.8 (*n* = 210). The decline is materially
unchanged under fixed 5-year (0.30pp, *t* = 6.5) and 10-year (0.30pp, *t* = 7.6)
post-publication windows; medians track the means. Placebo signals show a
near-zero change of 0.05pp (median 0.02pp, *t* = 1.9, *n* = 114).

**Cycle (comomentum, daily U.S. equities 1990–2025).** Forward 12-month momentum
return is flat in the lowest comomentum quintile (+0.02%/mo) and reverts
monotonically to −2.06%/mo in the highest; high-minus-low = −2.08%/mo (*t* =
−4.4, 12m) and −1.82%/mo (*t* = −4.7, 24m), reproducing Lou & Polk (2022).

## Scope of the evidence

The empirical results are **consistency evidence**, not identification of the
graph-level loop. The decay test uses publication as a proxy for the onset of
deployment; the cycle test uses comomentum as a price-based proxy for deployment
pressure. Neither observes the loop, estimates its thresholds, or identifies
deployment as an intervention. See Section 6 of the paper.

## Data

No proprietary data is bundled. The empirical scripts read public datasets you
download yourself; see [`data/README.md`](data/README.md) for sources and
filenames. The Stooq-based comomentum notebook is for public reproducibility; a
CRSP/WRDS replication (`notebooks/comomentum_wrds.ipynb`) is the institutional
benchmark.

## Citation

See [`CITATION.cff`](CITATION.cff). This repository is archived on Zenodo with
DOI [10.5281/zenodo.21038235](https://doi.org/10.5281/zenodo.21038235) (concept
DOI; resolves to the latest version). Please also cite the data sources: Chen &
Zimmermann (2020) for the anomaly data and Lou & Polk (2022) for the comomentum
construction.

## License

Code released under the MIT License (see [`LICENSE`](LICENSE)). The paper text
and figures are © the authors.
