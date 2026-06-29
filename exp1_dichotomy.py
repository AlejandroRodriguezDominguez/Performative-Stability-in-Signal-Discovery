"""
Placebo falsification check (OSAP).

Placebo signals are constructed to have no genuine predictive content, so they
should show no systematic decline. Because placebos have no publication date,
each placebo's own sample is split at its midpoint as a pseudo-event and the two
halves are compared, mirroring the predictor test in decay_windows.py.

Reproduces the placebo row of Table 3: mean change ~0.05pp, median ~0.02pp,
t ~ 1.9 (at most marginal), against ~0.32pp for published predictors.

Data (Open Source Asset Pricing, Chen & Zimmermann 2020):
  - PlaceboPortsFull.csv   long-format placebo portfolios, includes an 'LS' port

Default location ../../data/. Override with --placebo. See data/README.md.

Usage:
    python placebo_decay.py
    python placebo_decay.py --placebo path/to/PlaceboPortsFull.csv --out ../../figures
"""
import argparse
import csv
import math
import os
import statistics


def load_placebo_ls(path):
    """Return {signal: [(year, ret)]} for the long-short ('LS') portfolio."""
    ls = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("port") != "LS":
                continue
            s = r["signalname"]
            d = r.get("date", "")
            if not d or len(d) < 4:
                continue
            try:
                ret = float(r["ret"])
            except (KeyError, ValueError, TypeError):
                continue
            ls.setdefault(s, []).append((int(d[:4]), ret))
    return ls


def midpoint_decline(series):
    """First-half minus second-half mean, split at the sample midpoint year."""
    yrs = [y for y, _ in series]
    if len(series) < 60:
        return None
    lo, hi = min(yrs), max(yrs)
    mid = (lo + hi) // 2
    first = [r for (y, r) in series if y <= mid]
    second = [r for (y, r) in series if y > mid]
    if len(first) < 12 or len(second) < 12:
        return None
    return statistics.mean(first) - statistics.mean(second)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.normpath(os.path.join(here, "..", "..", "data"))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--placebo", default=os.path.join(data_dir, "PlaceboPortsFull.csv"))
    ap.add_argument("--out", default=os.path.normpath(os.path.join(here, "..", "..", "figures")))
    args = ap.parse_args()

    if not os.path.exists(args.placebo):
        raise SystemExit(
            f"missing data file: {args.placebo}\n"
            "Download the Open Source Asset Pricing release and place "
            "PlaceboPortsFull.csv in data/ (see data/README.md)."
        )

    ls = load_placebo_ls(args.placebo)
    declines = [d for d in (midpoint_decline(s) for s in ls.values()) if d is not None]

    n = len(declines)
    mean_dec = statistics.mean(declines)
    med_dec = statistics.median(declines)
    sd = statistics.stdev(declines)
    t = mean_dec / (sd / math.sqrt(n))

    print("=== Placebo falsification check (OSAP) ===\n")
    print(f"placebo signals with LS portfolio: {len(ls)}")
    print(f"usable (>=60 months, both halves): n={n}")
    print(f"  mean pseudo-decline   = {mean_dec:.3f} pp")
    print(f"  median pseudo-decline = {med_dec:.3f} pp")
    print(f"  t-stat                = {t:.2f}")
    print("\nExpected: near-zero decline, at most marginal t (vs ~0.32pp for predictors).")

    os.makedirs(args.out, exist_ok=True)
    csv_path = os.path.join(args.out, "placebo_decay_results.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "mean_decline_pp", "median_decline_pp", "t_stat"])
        w.writerow([n, f"{mean_dec:.4f}", f"{med_dec:.4f}", f"{t:.2f}"])
    print(f"\nwrote {csv_path}")


if __name__ == "__main__":
    main()
