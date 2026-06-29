"""
Experiment 4 — Robustness battery required by the referees.

We re-test the threshold/cycle dichotomy under:
 (R1) varying sample size T of the discovery estimator,
 (R2) varying return noise sigma,
 (R3) alternative inclusion thresholds tau,
 (R4) a nonlinear (concave) impact function,
 (R5) asymmetric entry/exit thresholds (deadband already covers symmetric case),
and we report Wilson confidence intervals on every Monte-Carlo fraction so the
"fraction in cycle" curves carry uncertainty bands.

Ground truth edge mu, impact lam, capital map w(beta). Discovery estimates the edge from T
noisy obs and uses a deadband of half-width rho around tau. We locate the empirical switch
scale (first beta with cycle-fraction > 0.5) and compare to the theoretical
beta_c(rho) = (mu - tau + rho)/lam   [linear impact]
or, for nonlinear impact g(.), the solution of g(w(beta_c)) = mu - tau + rho.
"""
import numpy as np, json
from math import sqrt

def wilson(p, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    denom = 1 + z*z/n
    centre = (p + z*z/(2*n))/denom
    half = z*sqrt(p*(1-p)/n + z*z/(4*n*n))/denom
    return (max(0.0, centre-half), min(1.0, centre+half))

def make_discover(mu, lam, tau, sigma, T, rho, impact='linear', a=1.0):
    """Return a discovery step using deadband rho; impact in {'linear','concave'}."""
    def g(wcap):
        if impact == 'linear':
            return lam*wcap
        # concave (square-root) impact, normalised so g is comparable near operating range
        return lam*np.sqrt(max(wcap,0.0)/a)*sqrt(a)
    def realized_edge(graph, beta):
        return mu - g(beta) if graph == 'on' else mu
    def step(prev_call, graph, beta, rng):
        e = realized_edge(graph, beta)
        ehat = (e + rng.normal(0, sigma, size=T)).mean()
        if ehat > tau + rho: return 'on'
        if ehat < tau - rho: return 'off'
        return prev_call
    return step, g

def cycle_fraction(step, beta, n_seed, key):
    c = n = 0
    for s in range(n_seed):
        for start in ('on','off'):
            rng = np.random.default_rng(key + 13*s + (1 if start=='on' else 0))
            g = start; call = start; seq=[g]
            for _ in range(10):
                call = step(call, g, beta, rng); g = call; seq.append(g)
            tail = seq[-4:]
            is_cycle = (tail[0]==tail[2] and tail[1]==tail[3] and tail[0]!=tail[1])
            c += 1 if is_cycle else 0; n += 1
    return c/n, n

def switch_scale(step, betas, n_seed, key):
    fr = []
    for j,beta in enumerate(betas):
        f,_ = cycle_fraction(step, beta, n_seed, key+1000*j)
        fr.append(f)
    fr = np.array(fr)
    idx = np.argmax(fr > 0.5) if np.any(fr>0.5) else None
    return (float(betas[idx]) if idx is not None else None), fr

base = dict(mu=0.020, lam=1.0, tau=0.012, sigma=0.05, T=1500, rho=0.0)
betas = np.linspace(0.001, 0.020, 39)
n_seed = 300
results = {}

# R1: sample size
r1 = []
for T in [250, 500, 1500, 5000]:
    step,_ = make_discover(base['mu'],base['lam'],base['tau'],base['sigma'],T,base['rho'])
    sw,_ = switch_scale(step, betas, n_seed, key=int(T))
    bc = (base['mu']-base['tau']+base['rho'])/base['lam']
    r1.append(dict(T=T, switch=sw, beta_c=bc, match=(sw==round(bc,6) or abs((sw or 1)-bc)<=0.0006)))
results['R1_sample_size'] = r1

# R2: noise
r2 = []
for sigma in [0.02, 0.05, 0.10, 0.20]:
    step,_ = make_discover(base['mu'],base['lam'],base['tau'],sigma,base['T'],base['rho'])
    sw,_ = switch_scale(step, betas, n_seed, key=int(sigma*1e4))
    bc = (base['mu']-base['tau']+base['rho'])/base['lam']
    r2.append(dict(sigma=sigma, switch=sw, beta_c=bc, abs_err=(None if sw is None else abs(sw-bc))))
results['R2_noise'] = r2

# R3: thresholds
r3 = []
for tau in [0.008, 0.012, 0.016]:
    step,_ = make_discover(base['mu'],base['lam'],tau,base['sigma'],base['T'],base['rho'])
    sw,_ = switch_scale(step, betas, n_seed, key=int(tau*1e5))
    bc = (base['mu']-tau+base['rho'])/base['lam']
    r3.append(dict(tau=tau, switch=sw, beta_c=bc, abs_err=(None if sw is None else abs(sw-bc))))
results['R3_threshold'] = r3

# R4: nonlinear (concave) impact; theoretical beta_c solves lam*sqrt(beta_c)=mu-tau
r4 = []
for lam in [0.5, 1.0]:
    bc = ((base['mu']-base['tau'])/lam)**2
    # grid centred to resolve the (small) crossing scale
    betas_nl = np.linspace(0.2*bc, 5*bc, 48)
    step,g = make_discover(base['mu'],lam,base['tau'],base['sigma'],base['T'],base['rho'],impact='concave')
    sw, fr = switch_scale(step, betas_nl, n_seed, key=int(lam*1e3)+7)
    grid_step = float(betas_nl[1]-betas_nl[0])
    r4.append(dict(lam=lam, switch=sw, beta_c=float(bc),
                   abs_err=(None if sw is None else abs(sw-bc)),
                   within_one_grid=(None if sw is None else abs(sw-bc)<=1.5*grid_step)))
results['R4_nonlinear_impact'] = r4

# R5: asymmetric entry/exit (entry at tau+rho_in, exit at tau-rho_out)
def make_asym(mu,lam,tau,sigma,T,rho_in,rho_out):
    def step(prev,graph,beta,rng):
        e = mu - lam*beta if graph=='on' else mu
        ehat=(e+rng.normal(0,sigma,size=T)).mean()
        if ehat>tau+rho_in: return 'on'
        if ehat<tau-rho_out: return 'off'
        return prev
    return step
r5=[]
for rin,rout in [(0.002,0.002),(0.004,0.001),(0.001,0.004)]:
    step = make_asym(base['mu'],base['lam'],base['tau'],base['sigma'],base['T'],rin,rout)
    sw,_ = switch_scale(step, betas, n_seed, key=int(rin*1e5)+int(rout*1e3))
    # on->off flip needs crowded edge below tau-rout => beta_c=(mu-tau+rout)/lam
    bc=(base['mu']-base['tau']+rout)/base['lam']
    r5.append(dict(rho_in=rin,rho_out=rout,switch=sw,beta_c=bc,
                   abs_err=(None if sw is None else abs(sw-bc))))
results['R5_asymmetric'] = r5

# headline curve with CIs at base config for the figure
step,_ = make_discover(**base)
fr=[]; lo=[]; hi=[]
for j,beta in enumerate(betas):
    f,n = cycle_fraction(step, beta, n_seed, key=99+1000*j)
    l,h = wilson(f,n); fr.append(f); lo.append(l); hi.append(h)
np.savez('exp4_robust.npz', betas=betas, fr=np.array(fr), lo=np.array(lo), hi=np.array(hi),
         beta_c=(base['mu']-base['tau']+base['rho'])/base['lam'])

print(json.dumps(results, indent=2, default=float))
with open('exp4_summary.json','w') as f: json.dump(results,f,indent=2,default=float)
print("\nsaved exp4_robust.npz, exp4_summary.json")
