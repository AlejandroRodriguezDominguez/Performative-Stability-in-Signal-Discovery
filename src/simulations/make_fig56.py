"""Generate Figure 5 (bifurcation of the live edge) and Figure 6 (transient length and
realised period) from exp5 and exp6 outputs."""
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

# ---------- Figure 5: bifurcation diagram ----------
d5 = np.load('exp5_bifurcation.npz')
fig, ax = plt.subplots(figsize=(3.6, 2.6))
ax.scatter(d5['xs'], d5['ys'], s=4, color=BLK, alpha=0.7, edgecolors='none')
ax.axvline(float(d5['beta_c']), color=GRAY, ls='--', lw=0.9)
ax.text(float(d5['beta_c'])*1.02, ax.get_ylim()[0] + 0.85*(ax.get_ylim()[1]-ax.get_ylim()[0]),
        r'$\beta_c$', color=GRAY, fontsize=9)
ax.axhline(float(d5['tau']), color='0.6', ls=':', lw=0.9)
ax.text(d5['betas'][1], float(d5['tau'])*1.05, r'detection threshold $\tau$',
        color='0.5', fontsize=6.5)
ax.set_xlabel(r'deployment scale $\beta$')
ax.set_ylabel('live-edge values in orbit tail')
ax.set_title('Bifurcation of the live edge', fontsize=9, loc='left')
fig.tight_layout(); fig.savefig('fig5_bifurcation.pdf'); plt.close(fig)

# ---------- Figure 6: transient length + realised period ----------
d6 = np.load('exp6_transient.npz')
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6))

ax = axes[0]
ax.plot(d6['betas'], d6['mean_transient'], color=BLK, marker='o', ms=2.5,
        mfc='white', mew=0.6)
ax.axvline(float(d6['beta_c']), color=GRAY, ls='--', lw=0.9)
ax.text(float(d6['beta_c'])*1.01, ax.get_ylim()[1]*0.9, r'$\beta_c$', color=GRAY, fontsize=9)
ax.set_xlabel(r'deployment scale $\beta$')
ax.set_ylabel('mean transient length')
ax.set_title('(a) Convergence speed', fontsize=9, loc='left')

ax = axes[1]
ax.plot(d6['betas'], d6['frac_p1'], color=BLK, marker='o', ms=2.5, mfc='white',
        mew=0.6, label='period 1 (fixed)')
ax.plot(d6['betas'], d6['frac_p2'], color=GRAY, marker='s', ms=2.5, mfc='white',
        mew=0.6, label='period 2 (cycle)')
ax.axvline(float(d6['beta_c']), color=GRAY, ls='--', lw=0.9)
ax.set_xlabel(r'deployment scale $\beta$')
ax.set_ylabel('fraction of orbits')
ax.set_ylim(-0.03, 1.03)
ax.set_title('(b) Realised period', fontsize=9, loc='left')
ax.legend(fontsize=6.5, frameon=False, loc='center right')

fig.tight_layout(); fig.savefig('fig6_transient.pdf'); plt.close(fig)
print("saved fig5_bifurcation.pdf, fig6_transient.pdf")
