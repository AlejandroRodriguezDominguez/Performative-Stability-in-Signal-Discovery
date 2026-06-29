"""
Experiment 2 — Phase diagram over deployment scale (beta) and discovery margin (rho_D).

We make the discovery margin explicit by adding a hysteresis/deadband of half-width rho
around the inclusion threshold: discovery keeps its previous call unless the estimated edge
crosses tau by more than rho. Larger rho = more robust discovery = wider sub-threshold
(fixed-point) region, matching Theorem 1: bigger rho_D pushes beta* up.

Output: a (beta, rho) grid coloured by regime (fixed vs cycle), plus the theoretical
boundary curve beta*(rho).
"""
import numpy as np
import json

mu, lam, tau, sigma, T = 0.020, 1.0, 0.012, 0.05, 1500
w = lambda beta: beta

def realized_edge(graph, beta):
    return (mu - lam * w(beta)) if graph == 'on' else mu

def discover(prev_call, graph, beta, rho, rng):
    """Margin/hysteresis discovery: flip to 'on' only if ehat > tau+rho, to 'off' only if
       ehat < tau-rho, else hold prev_call."""
    e = realized_edge(graph, beta)
    ehat = (e + rng.normal(0, sigma, size=T)).mean()
    if ehat > tau + rho:
        return 'on'
    if ehat < tau - rho:
        return 'off'
    return prev_call

def orbit_regime(start, beta, rho, rng, steps=10):
    g = start; call = start; seq = [g]
    for _ in range(steps):
        call = discover(call, g, beta, rho, rng)
        g = call
        seq.append(g)
    tail = seq[-4:]
    if all(x == tail[0] for x in tail):
        return 0  # fixed
    if tail[0] == tail[2] and tail[1] == tail[3] and tail[0] != tail[1]:
        return 1  # cycle
    return 2      # other

betas = np.linspace(0.001, 0.020, 40)
rhos  = np.linspace(0.000, 0.012, 25)
n_seed = 60

grid = np.zeros((len(rhos), len(betas)))   # fraction of (start,seed) trials that cycle
for i, rho in enumerate(rhos):
    for j, beta in enumerate(betas):
        c = 0; n = 0
        for s in range(n_seed):
            for start in ('on', 'off'):
                rng = np.random.default_rng(7777 * s + int(beta*1e6) + int(rho*1e7))
                reg = orbit_regime(start, beta, rho, rng)
                c += 1 if reg == 1 else 0
                n += 1
        grid[i, j] = c / n

# Theoretical boundary: cycle requires deployed 'on' edge below tau-rho (to flip off) AND
# un-crowded edge above tau+rho (to flip back on). The binding one for the on->off flip is
# mu - lam*beta < tau - rho  =>  beta > (mu - tau + rho)/lam = beta_c + rho/lam.
beta_star = (mu - tau + rhos) / lam   # boundary scale as a function of rho

np.savez('exp2_phase.npz', betas=betas, rhos=rhos, grid=grid, beta_star=beta_star,
         beta_c=(mu-tau)/lam)
print("grid range:", float(grid.min()), float(grid.max()))
print("boundary at rho=0:", float(beta_star[0]), " at rho=max:", float(beta_star[-1]))
print("saved exp2_phase.npz")
