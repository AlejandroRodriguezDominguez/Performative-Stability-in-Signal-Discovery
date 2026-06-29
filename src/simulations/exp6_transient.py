"""
Experiment 6 — Transient length and the one-step claim.

Theorem 1 says that below beta_c the map is constant on the reachable set, so the orbit
reaches the unique stable graph in ONE step from any start. We verify this by measuring the
transient length: the number of steps until the orbit first enters its eventual cycle/fixed
point. Below beta_c the transient should be <= 1 from both starts; above beta_c the orbit is
the 2-cycle with period 2 (transient 0 or 1 then alternation). We also confirm the bound
from Proposition 1 (transient and period <= |G| = 2) is not just respected but tight in the
predicted way, and that finite-sample noise does not create long transients except in a thin
band around beta_c where occasional misclassification lengthens them.
"""
import numpy as np, json
mu, lam, tau, rho, sigma, T = 0.020, 1.0, 0.012, 0.002, 0.03, 1500
w = lambda b: b
def edge(g,b): return mu - lam*w(b) if g=='on' else mu
def step(prev,g,b,rng):
    e=edge(g,b); ehat=(e+rng.normal(0,sigma,size=T)).mean()
    if ehat>tau+rho: return 'on'
    if ehat<tau-rho: return 'off'
    return prev

def transient_and_period(start, beta, rng, horizon=40):
    g=start; call=start; seq=[g]
    for _ in range(horizon):
        call=step(call,g,beta,rng); g=call; seq.append(g)
    tail=seq[-12:]
    # period 1: all tail equal
    if all(x==tail[-1] for x in tail):
        period=1
    # period 2: strict alternation in the tail
    elif tail[-1]!=tail[-2] and all(tail[k]==tail[-1] for k in range(len(tail)-1,-1,-2)) \
                            and all(tail[k]==tail[-2] for k in range(len(tail)-2,-1,-2)):
        period=2
    else:
        period=0  # unresolved (thin noise band near beta_c)
    n=len(seq)
    if period==1:
        val=seq[-1]; tr=n-1
        for i in range(n):
            if all(seq[j]==val for j in range(i,n)): tr=i; break
    elif period==2:
        last=seq[-1]; prev=seq[-2]; tr=n-1
        for i in range(n-1):
            # from i to end, parity-consistent alternation ending in `last`
            ok=all(seq[j]==(last if (n-1-j)%2==0 else prev) for j in range(i,n))
            if ok: tr=i; break
    else:
        tr=horizon
    return tr, period

betas=np.linspace(0.002,0.018,33)
beta_c=(mu-tau+rho)/lam
rows=[]
for beta in betas:
    trs=[]; pds=[]
    for s in range(150):
        for st in ('on','off'):
            rng=np.random.default_rng(31*s+int(beta*1e6)+(1 if st=='on' else 0))
            tr,pd=transient_and_period(st,beta,rng)
            trs.append(tr); pds.append(pd)
    rows.append(dict(beta=float(beta),
                     mean_transient=float(np.mean(trs)),
                     max_transient=int(np.max(trs)),
                     frac_period1=float(np.mean([p==1 for p in pds])),
                     frac_period2=float(np.mean([p==2 for p in pds]))))

# headline checks
below=[r for r in rows if r['beta']<beta_c-0.001]
above=[r for r in rows if r['beta']>beta_c+0.001]
summary=dict(
    beta_c=float(beta_c),
    max_transient_below_bc=int(max(r['max_transient'] for r in below)),
    mean_transient_below_bc=float(np.mean([r['mean_transient'] for r in below])),
    frac_period1_below=float(np.mean([r['frac_period1'] for r in below])),
    frac_period2_above=float(np.mean([r['frac_period2'] for r in above])),
)
print(json.dumps(summary, indent=2))
np.savez('exp6_transient.npz',
         betas=np.array([r['beta'] for r in rows]),
         mean_transient=np.array([r['mean_transient'] for r in rows]),
         frac_p1=np.array([r['frac_period1'] for r in rows]),
         frac_p2=np.array([r['frac_period2'] for r in rows]),
         beta_c=beta_c)
with open('exp6_summary.json','w') as f: json.dump(summary,f,indent=2)
print("saved exp6_transient.npz, exp6_summary.json")
