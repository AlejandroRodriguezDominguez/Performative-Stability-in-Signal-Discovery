"""Generate Figure 4 (robustness) from exp4 outputs: (a) headline cycle-fraction
curve with a 95% Wilson band, (b) empirical switch scale vs predicted crossing scale
across the whole battery."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams.update({
    'font.family': 'serif', 'font.size': 9, 'axes.linewidth': 0.6,
    'axes.spines.top': False, 'axes.spines.right': False,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'figure.dpi': 200, 'savefig.dpi': 200, 'lines.linewidth': 1.1,
})
GRAY = '0.35'; BLK = '0.1'

d = np.load('exp4_robust.npz')
with open('exp4_summary.json') as f:
    S = json.load(f)

fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6))

# (a) headline curve with Wilson band
ax = axes[0]
ax.fill_between(d['betas'], d['lo'], d['hi'], color='0.8', lw=0, label='95% Wilson band')
ax.plot(d['betas'], d['fr'], color=BLK, marker='o', ms=2.5, mfc='white', mew=0.6,
        label='cycle fraction')
ax.axvline(float(d['beta_c']), color=GRAY, ls='--', lw=0.9)
ax.axhline(0.5, color='0.6', ls=':', lw=0.8)
ax.text(float(d['beta_c'])*1.02, 0.08, r'$\beta_c$', color=GRAY, fontsize=9)
ax.set_xlabel(r'deployment scale $\beta$')
ax.set_ylabel('fraction in 2-cycle')
ax.set_ylim(-0.03, 1.03)
ax.set_title('(a) Cycle fraction with confidence band', fontsize=9, loc='left')
ax.legend(fontsize=6.5, frameon=False, loc='center right')

# (b) empirical switch vs predicted crossing across battery
ax = axes[1]
pred, emp, small = [], [], []
for key in ['R1_sample_size', 'R2_noise', 'R3_threshold', 'R4_nonlinear_impact', 'R5_asymmetric']:
    for row in S[key]:
        bc = row.get('beta_c')
        sw = row.get('switch')
        if bc is None or sw is None:
            continue
        pred.append(bc); emp.append(sw)
        small.append(row.get('T', 99999) in (250, 500))
pred = np.array(pred); emp = np.array(emp); small = np.array(small)
lim = [0, max(pred.max(), emp.max()) * 1.1]
ax.plot(lim, lim, color='0.6', ls='--', lw=0.9, label='identity')
ax.scatter(pred[~small], emp[~small], s=14, facecolors='white', edgecolors=BLK,
           linewidths=0.7, label='battery cases')
ax.scatter(pred[small], emp[small], s=16, marker='s', facecolors='0.4',
           edgecolors=BLK, linewidths=0.5, label='small-sample')
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel(r'predicted crossing scale $\beta_c$')
ax.set_ylabel('empirical switch scale')
ax.set_title('(b) Recovery across the battery', fontsize=9, loc='left')
ax.legend(fontsize=6.5, frameon=False, loc='upper left')

fig.tight_layout(); fig.savefig('fig4_robust.pdf'); plt.close(fig)
print("saved fig4_robust.pdf")
