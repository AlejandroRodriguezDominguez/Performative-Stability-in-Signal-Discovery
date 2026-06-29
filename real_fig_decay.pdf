# Data

No data is redistributed in this repository. Download the public datasets below
and place the files directly in this `data/` folder.

## Open Source Asset Pricing (Chen & Zimmermann 2020)

Used by `src/empirical/decay_windows.py` and `src/empirical/placebo_decay.py`,
and by `notebooks/osap_decay.ipynb`.

Download the latest data release from:
- https://www.openassetpricing.com/  (Data Releases)
- or the project's repository linked there.

Place the following files in `data/`:

| File | Used for |
|------|----------|
| `PredictorLSretWide.csv` | wide monthly long-short returns, one column per signal |
| `SignalDoc.csv`          | signal documentation (publication year, sample end year) |
| `PlaceboPortsFull.csv`   | placebo portfolios (includes an `LS` long-short column) |

`SignalDoc.csv` must contain the columns `Acronym`, `Cat.Signal`, `Year`
(publication year), and `SampleEndYear`.

## Daily U.S. equity returns (comomentum)

Used by `notebooks/comomentum.ipynb`. The notebook downloads daily prices from
Stooq (free, no account) for public reproducibility. For an institutional,
survivorship-bias-free replication use `notebooks/comomentum_wrds.ipynb`, which
reads CRSP via a WRDS account (not included).

## Note

The empirical results are consistency evidence, not identification of the
discovery loop (see Section 6 of the paper). The Stooq universe may differ from
a fully point-in-time CRSP universe with delisting returns and historical
share-code filters.
