"""
Experiment 5 — Empirical bifurcation diagram.

This is the dynamical-systems-standard visualization of the result. For each deployment
scale beta we run the discover-deploy loop to its long-run regime and plot the set of
LIVE EDGE values the orbit visits in its tail. Below beta_c the tail is a single value
(period-1 fixed point); above beta_c the tail visits two values (period-2 cycle), namely
the crowded edge (deployed) and the un-crowded edge (withdrawn). This makes the period-1
-> period-2 bifurcation directly visible in an observable quantity (the live edge), not
just in the abstract graph label.
"""
import numpy as np, json
mu, lam, tau, rho, sigma, T = 0.020, 1.0, 0.012, 0.0, 0.03, 4000
w = lambda b: b

def edge(graph, beta):
    return mu - lam*w(beta) if graph=='on' else mu

def step(prev, g, beta, rng):
    e = edge(g, beta)
    ehat = (e + rng.normal(0, sigma, size=T)).mean()
    if ehat > tau + rho: return 'on'
    if ehat < tau - rho: return 'off'
    return prev

betas = np.linspace(0.001, 0.020, 80)
beta_c = (mu - tau + rho)/lam
tail_vals = []   # list of arrays of distinct tail live-edges per beta
for beta in betas:
    rng = np.random.default_rng(424242 + int(beta*1e6))
    g = 'off'; call='off'
    seq=[]
    for t in range(60):
        call = step(call, g, beta, rng); g=call
        seq.append(edge(g, beta))   # the realised live edge that round
    tail = np.array(seq[-20:])
    # collapse to distinct levels (round to remove noise-free duplicates)
    levels = np.unique(np.round(tail, 6))
    tail_vals.append(levels)

# pack for plotting: x repeated per level
xs=[]; ys=[]
for b, lv in zip(betas, tail_vals):
    for v in lv:
        xs.append(b); ys.append(v)
xs=np.array(xs); ys=np.array(ys)

# count of distinct tail levels per beta = period proxy
periods = np.array([len(lv) for lv in tail_vals])
emp_bif = float(betas[np.argmax(periods>=2)]) if np.any(periods>=2) else None

np.savez('exp5_bifurcation.npz', xs=xs, ys=ys, betas=betas, periods=periods,
         beta_c=beta_c, mu=mu, tau=tau)
print(json.dumps(dict(beta_c=float(beta_c), empirical_bifurcation=emp_bif,
                      max_period_levels=int(periods.max())), indent=2))
print("saved exp5_bifurcation.npz")
