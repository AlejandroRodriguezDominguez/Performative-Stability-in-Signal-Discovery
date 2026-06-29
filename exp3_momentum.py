"""
Post-publication decay of published anomalies (OSAP).

Reproduces the decay numbers in Table 3 of the paper:
in-sample vs post-publication long-short edge, across full / 5-year / 10-year
post-publication windows, with mean, median and a paired t-statistic.

Data (Open Source Asset Pricing, Chen & Zimmermann 2020):
  - PredictorLSretWide.csv   wide monthly long-short returns, one column per signal
  - SignalDoc.csv            signal documentation (publication year, sample end year)

By default the script looks for these in ../../data/ (repo-relative). You can
override with --lsret and --signaldoc. See data/README.md for download links.

Usage:
    python decay_windows.py
    python decay_windows.py --lsret path/to/PredictorLSretWide.csv \
                            --signaldoc path/to/SignalDoc.csv \
                            --out ../../figures
"""
import argparse
import csv
import math
import os
import statistics


def load_signaldoc(path):
    """Return {acronym: {'pub': year, 'sampleend': year}} for predictors."""
    meta = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("Cat.Signal", "").strip() != "Predictor":
                continue
            ac = r["Acronym"].strip()
            try:
                pub = int(float(r["Year"]))
                send = int(float(r["SampleEndYear"]))
            except (KeyError, ValueError, TypeError):
                continue
            meta[ac] = {"pub": pub, "sampleend": send}
    return meta


def load_lsret_wide(path):
    """Return (columns, data) where data is list of (year, [ret per column])."""
    with open(path, newline="") as fh:
        rd = csv.reader(fh)
        header = next(rd)
        cols = header[1:]
        data = []
        for row in rd:
            date = row[0]
            if not date or len(date) < 4:
                continue
            yr = int(date[:4])
            vals = []
            for x in row[1:]:
                try:
                    vals.append(float(x))
                except ValueError:
                    vals.append(None)
            data.append((yr, vals))
    return cols, data


def edge_window(colidx, data, ac, lo, hi):
    """Mean monthly LS return for acronym ac over years [lo, hi] inclusive."""
    if ac not in colidx:
        return None
    i = colidx[ac]
    xs = [v[i] for (yr, v) in data if lo <= yr <= hi and v[i] is not None]
    if len(xs) < 12:
        return None
    return statistics.mean(xs)


def run_window(meta, colidx, data, label, post_len=None, end_year=2025):
    declines, ins_list, post_list = [], [], []
    for ac, m in meta.items():
        pub, se = m["pub"], m["sampleend"]
        ins = edge_window(colidx, data, ac, 1900, se)
        if post_len is None:
            post = edge_window(colidx, data, ac, pub + 1, end_year)
        else:
            post = edge_window(colidx, data, ac, pub + 1, pub + post_len)
        if ins is None or post is None or ins <= 0:
            continue
        declines.append(ins - post)
        ins_list.append(ins)
        post_list.append(post)
    if not declines:
        return None
    n = len(declines)
    mean_dec = statistics.mean(declines)
    sd = statistics.stdev(declines)
    t = mean_dec / (sd / math.sqrt(n))
    return {
        "label": label,
        "n": n,
        "in_sample": statistics.mean(ins_list),
        "post_pub": statistics.mean(post_list),
        "mean_decline": mean_dec,
        "median_decline": statistics.median(declines),
        "pct": 100 * mean_dec / statistics.mean(ins_list),
        "t": t,
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.normpath(os.path.join(here, "..", "..", "data"))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lsret", default=os.path.join(data_dir, "PredictorLSretWide.csv"))
    ap.add_argument("--signaldoc", default=os.path.join(data_dir, "SignalDoc.csv"))
    ap.add_argument("--out", default=os.path.normpath(os.path.join(here, "..", "..", "figures")))
    args = ap.parse_args()

    for p in (args.lsret, args.signaldoc):
        if not os.path.exists(p):
            raise SystemExit(
                f"missing data file: {p}\n"
                "Download the Open Source Asset Pricing release and place the "
                "files in data/ (see data/README.md)."
            )

    meta = load_signaldoc(args.signaldoc)
    cols, data = load_lsret_wide(args.lsret)
    colidx = {c: i for i, c in enumerate(cols)}

    rows = []
    rows.append(run_window(meta, colidx, data, "Predictors, full post", None))
    rows.append(run_window(meta, colidx, data, "Predictors, 5-year post", 5))
    rows.append(run_window(meta, colidx, data, "Predictors, 10-year post", 10))

    print("=== Post-publication decay (OSAP) ===\n")
    for r in rows:
        if r is None:
            continue
        print(f"{r['label']}: n={r['n']}")
        print(f"   in-sample mean   = {r['in_sample']:.3f} %/mo")
        print(f"   post-pub  mean   = {r['post_pub']:.3f} %/mo")
        print(f"   mean decline     = {r['mean_decline']:.3f} pp ({r['pct']:.0f}% of IS)")
        print(f"   median decline   = {r['median_decline']:.3f} pp")
        print(f"   paired t         = {r['t']:.1f}\n")

    os.makedirs(args.out, exist_ok=True)
    csv_path = os.path.join(args.out, "decay_windows_results.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["window", "n", "in_sample_pct_mo", "post_pub_pct_mo",
                    "mean_decline_pp", "pct_of_in_sample", "median_decline_pp", "paired_t"])
        for r in rows:
            if r is None:
                continue
            w.writerow([r["label"], r["n"], f"{r['in_sample']:.4f}",
                        f"{r['post_pub']:.4f}", f"{r['mean_decline']:.4f}",
                        f"{r['pct']:.1f}", f"{r['median_decline']:.4f}", f"{r['t']:.2f}"])
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
