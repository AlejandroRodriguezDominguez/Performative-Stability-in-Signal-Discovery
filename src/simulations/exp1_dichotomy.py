"""
Experiment 1 — Synthetic validation of the threshold/cycle dichotomy.

Ground truth: a single signal X with un-crowded per-unit edge mu. Discovery declares
the X->R edge present iff the estimated deployed edge exceeds an inclusion threshold tau.
Deploying the 'on' graph crowds the edge: surviving edge = mu - lambda * w(beta), with
w(beta) the aggregate capital. We confirm:
  (i)  below beta_c the re-discovery orbit collapses to a unique fixed point in <=1 step;
  (ii) above beta_c it is the period-2 swap (crowding/decay);
  (iii) the empirical switch scale matches beta_c = w^{-1}((mu - tau)/lambda).
Estimation of the edge is from finite samples (noisy), so this is a genuine statistical
recovery test, not an algebraic identity.
"""
import numpy as np
import json

rng = np.random.default_rng(20260627)

# --- ground-truth primitives ---
mu     = 0.020       # un-crowded per-unit edge
lam    = 1.0         # linear impact coefficient
tau    = 0.012       # discovery inclusion threshold on the edge
sigma  = 0.05        # per-period noise of realized returns (for finite-sample discovery)
T      = 1500        # sample length used by the discovery estimator each round
w      = lambda beta: beta          # aggregate capital map (normalised, strictly increasing)
beta_c = (mu - tau) / lam           # theoretical edge-crossing scale

def realized_edge(graph, beta):
    """True surviving per-unit edge of the signal under the deployed graph."""
    if graph == 'on':
        return mu - lam * w(beta)   # deploying on crowds it
    else:
        return mu                   # deploying off leaves it un-crowded

def discover(graph, beta):
    """Finite-sample discovery: estimate the edge from T noisy obs of the deployed law,
       declare 'on' iff the estimate exceeds tau."""
    e = realized_edge(graph, beta)
    obs = e + rng.normal(0, sigma, size=T)
    ehat = obs.mean()               # simple consistent estimator of the edge
    return 'on' if ehat > tau else 'off'

def orbit(start, beta, steps=8):
    g = start; seq = [g]
    for _ in range(steps):
        g = discover(g, beta)
        seq.append(g)
    return seq

def classify_tail(seq):
    """Return 'fixed:G' or 'cycle2' from the tail of an orbit."""
    tail = seq[-4:]
    if all(x == tail[0] for x in tail):
        return f'fixed:{tail[0]}'
    if tail[0] == tail[2] and tail[1] == tail[3] and tail[0] != tail[1]:
        return 'cycle2'
    return 'other'

# --- sweep beta, many seeds, record regime from both starts ---
betas = np.linspace(0.001, 0.020, 39)
n_seed = 200
results = []
for beta in betas:
    regimes = []
    for s in range(n_seed):
        rng = np.random.default_rng(1000 * s + int(beta * 1e6))
        globals()['rng'] = rng
        r_on  = classify_tail(orbit('on',  beta))
        r_off = classify_tail(orbit('off', beta))
        regimes.append((r_on, r_off))
    frac_cycle = np.mean([1.0 if (a == 'cycle2' or b == 'cycle2') else 0.0
                          for a, b in regimes])
    frac_fixed_on = np.mean([1.0 if a.startswith('fixed:on') and b.startswith('fixed:on')
                             else 0.0 for a, b in regimes])
    results.append(dict(beta=float(beta), frac_cycle=float(frac_cycle),
                        frac_fixed_on=float(frac_fixed_on)))

# empirical switch scale: smallest beta with majority cycle
emp_switch = next((r['beta'] for r in results if r['frac_cycle'] > 0.5), None)

summary = dict(
    mu=mu, lam=lam, tau=tau, sigma=sigma, T=T,
    beta_c_theory=float(beta_c),
    beta_switch_empirical=float(emp_switch) if emp_switch else None,
    rel_error=float(abs(emp_switch - beta_c) / beta_c) if emp_switch else None,
)
print(json.dumps(summary, indent=2))

# save curve for plotting
np.savez('exp1_curve.npz',
         betas=np.array([r['beta'] for r in results]),
         frac_cycle=np.array([r['frac_cycle'] for r in results]),
         frac_fixed_on=np.array([r['frac_fixed_on'] for r in results]),
         beta_c=beta_c, emp_switch=emp_switch)
with open('exp1_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)
print("\nsaved exp1_curve.npz, exp1_summary.json")
