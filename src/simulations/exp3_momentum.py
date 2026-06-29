"""
Experiment 3 — A momentum crowding simulation: the alpha-decay cycle in a panel.

We simulate a cross-section of N assets with a genuine momentum signal whose paper edge is
mu0. A discoverer each period estimates the momentum decile-spread edge from a rolling
window and decides whether to deploy ('on') a momentum book at aggregate scale beta. When
deployed, crowding impact reduces the realised spread by lam * w(beta); when not deployed,
the spread reverts to its un-crowded value. We track the deployed graph over many rounds and
the realised (live) edge, and compare to the theoretical performatively-stable crowd and
surviving edge from the closed-form skeleton:
    w_PS = mu0 / (kappa + lam),   live edge = mu0 * kappa / (kappa + lam).
We also show the period-2 discovery cycle above the crowding threshold.
"""
import numpy as np
import json

rng = np.random.default_rng(11)

N      = 200      # assets
Trond  = 120      # discovery rounds
win    = 240       # rolling window (months) for edge estimation
mu0    = 0.018    # un-crowded monthly momentum decile-spread edge
lam    = 0.9      # crowding impact per unit aggregate capital
kappa  = 1.0      # marginal deployment cost / risk aversion
tau    = 0.010    # discovery inclusion threshold on the spread
xsig   = 0.05     # idiosyncratic monthly vol of the spread estimate

# closed-form benchmarks
w_PS      = mu0 / (kappa + lam)
edge_live = mu0 * kappa / (kappa + lam)

def deployed_spread(graph, beta):
    """Realised momentum decile spread given the deployed graph and scale."""
    if graph == 'on':
        # crowd at scale w=beta; surviving edge
        return mu0 - lam * beta
    return mu0

def estimate_spread(graph, beta, rng):
    """Rolling-window noisy estimate of the spread (discovery input)."""
    s = deployed_spread(graph, beta)
    draws = s + rng.normal(0, xsig, size=win)
    return draws.mean()

rho = 0.004   # discovery margin (deadband half-width), as in Theorem 1

def run(beta, start='off', rng=None):
    g = start; call = start
    graphs, live_edges, est = [], [], []
    for t in range(Trond):
        e_hat = estimate_spread(g, beta, rng)
        if e_hat > tau + rho:
            call = 'on'
        elif e_hat < tau - rho:
            call = 'off'
        # else hold previous call (margin region)
        g = call
        graphs.append(g)
        live_edges.append(deployed_spread(g, beta))
        est.append(e_hat)
    return graphs, np.array(live_edges), np.array(est)

# (A) below the crowding threshold: stable deployment, edge survives
beta_lo = 0.003
g_lo, le_lo, _ = run(beta_lo, 'off', np.random.default_rng(1))

# (B) above the crowding threshold: alpha-decay cycle
beta_hi = 0.016
g_hi, le_hi, _ = run(beta_hi, 'off', np.random.default_rng(2))

# (C) sweep beta: long-run fraction of rounds deployed, and average live edge
betas = np.linspace(0.001, 0.020, 40)
frac_on, avg_live, theo_live = [], [], []
for beta in betas:
    fr, al = [], []
    for s in range(80):
        g, le, _ = run(beta, 'off', np.random.default_rng(500 + s + int(beta*1e6)))
        fr.append(np.mean([x == 'on' for x in g[-40:]]))
        al.append(le[-40:].mean())
    frac_on.append(np.mean(fr)); avg_live.append(np.mean(al))
    # theoretical surviving edge if deployed at this scale (one-sided)
    theo_live.append(mu0 - lam * beta if (mu0 - lam*beta) > tau else None)

beta_c = (mu0 - tau + rho) / lam

summary = dict(
    N=N, mu0=mu0, lam=lam, kappa=kappa, tau=tau,
    w_PS=float(w_PS), edge_live_closed_form=float(edge_live),
    beta_c_crowding=float(beta_c),
    beta_lo=beta_lo, frac_on_lo=float(np.mean([x=='on' for x in g_lo[-40:]])),
    beta_hi=beta_hi, frac_on_hi=float(np.mean([x=='on' for x in g_hi[-40:]])),
    cycle_detected_hi=bool(0.3 < np.mean([x=='on' for x in g_hi[-40:]]) < 0.7),
)
print(json.dumps(summary, indent=2))

np.savez('exp3_momentum.npz',
         g_lo=np.array([1 if x=='on' else 0 for x in g_lo]),
         le_lo=le_lo,
         g_hi=np.array([1 if x=='on' else 0 for x in g_hi]),
         le_hi=le_hi,
         betas=betas, frac_on=np.array(frac_on), avg_live=np.array(avg_live),
         beta_c=beta_c, edge_live=edge_live, w_PS=w_PS, mu0=mu0, tau=tau, lam=lam,
         beta_lo=beta_lo, beta_hi=beta_hi)
with open('exp3_summary.json','w') as f: json.dump(summary, f, indent=2)
print("saved exp3_momentum.npz, exp3_summary.json")
