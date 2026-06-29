# Notebooks

End-to-end empirical notebooks. Place the required public data in `../data/`
first (see `../data/README.md`).

| Notebook | Produces | Data |
|----------|----------|------|
| `osap_decay.ipynb` | post-publication decay, event-time figure (Fig. 8) | OSAP |
| `comomentum.ipynb` | comomentum vs forward momentum return (Fig. 9) | daily equity (Stooq) |
| `comomentum_wrds.ipynb` | same as above on CRSP | WRDS/CRSP account |

The `colab_*.py` files are flat-script versions of the notebooks, convenient for
running in Google Colab or from the command line.

The decay numbers in Table 3 (window robustness and placebo) are reproduced more
directly by the standalone scripts in `../src/empirical/`.
