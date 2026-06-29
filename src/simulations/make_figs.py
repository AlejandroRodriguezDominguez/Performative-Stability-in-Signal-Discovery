"""Generate dull, journal-style figures (grayscale-friendly) from the three experiments."""
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

# ---------- Figure 1: dichotomy curve (Experiment 1) ----------
d1 = np.load('exp1_curve.npz')
fig, ax = plt.subplots(figsize=(3.4, 2.5))
ax.plot(d1['betas'], d1['frac_cycle'], color=BLK, marker='o', ms=2.5, mfc='white', mew=0.6)
ax.axvline(float(d1['beta_c']), color=GRAY, ls='--', lw=0.9)
ax.text(float(d1['beta_c'])*1.02, 0.5, r'$\beta_c$', color=GRAY, fontsize=9)
ax.set_xlabel(r'deployment scale $\beta$')
ax.set_ylabel('fraction of trials in 2-cycle')
ax.set_ylim(-0.03, 1.03)
ax.set_title('(a) Regime switch at the edge-crossing scale', fontsize=9, loc='left')
fig.tight_layout(); fig.savefig('fig1_dichotomy.pdf'); plt.close(fig)

# ---------- Figure 2: phase diagram (Experiment 2) ----------
d2 = np.load('exp2_phase.npz')
fig, ax = plt.subplots(figsize=(3.6, 2.6))
im = ax.imshow(d2['grid'], origin='lower', aspect='auto', cmap='Greys',
               extent=[d2['betas'][0], d2['betas'][-1], d2['rhos'][0], d2['rhos'][-1]],
               vmin=0, vmax=1)
ax.plot(d2['beta_star'], d2['rhos'], color=BLK, lw=1.3)
ax.set_xlabel(r'deployment scale $\beta$')
ax.set_ylabel(r'discovery margin $\rho_{\mathsf{D}}$')
ax.set_title(r'(b) Phase diagram: cycle fraction; line $=\beta^\star(\rho_{\mathsf{D}})$',
             fontsize=9, loc='left')
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cb.set_label('fraction in 2-cycle', fontsize=8); cb.ax.tick_params(labelsize=7)
fig.tight_layout(); fig.savefig('fig2_phase.pdf'); plt.close(fig)

# ---------- Figure 3: momentum orbits + alpha decay (Experiment 3) ----------
d3 = np.load('exp3_momentum.npz')
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.5))
# left: deployed-graph orbits, low vs high beta
ax = axes[0]
T = len(d3['g_lo'])
ax.step(range(T), d3['g_lo'] + 1.15, where='mid', color=BLK, lw=1.0,
        label=r'$\beta<\beta_c$ (stable)')
ax.step(range(T), d3['g_hi'], where='mid', color=GRAY, lw=1.0,
        label=r'$\beta>\beta_c$ (cycle)')
ax.set_yticks([0, 1, 1.15, 2.15]); ax.set_yticklabels(['off', 'on', 'off', 'on'], fontsize=7)
ax.set_xlabel('discovery round'); ax.set_ylabel('deployed graph')
ax.set_title('(c) Re-discovery orbits', fontsize=9, loc='left')
ax.legend(fontsize=6.5, frameon=False, loc='center right')
# right: live edge vs beta, with closed-form benchmark
ax = axes[1]
ax.plot(d3['betas'], d3['avg_live'], color=BLK, marker='o', ms=2.5, mfc='white', mew=0.6,
        label='simulated live edge')
ax.axvline(float(d3['beta_c']), color=GRAY, ls='--', lw=0.9)
ax.text(float(d3['beta_c'])*1.01, ax.get_ylim()[1]*0.92, r'$\beta_c$', color=GRAY, fontsize=9)
ax.axhline(float(d3['tau']), color='0.6', ls=':', lw=0.9)
ax.text(d3['betas'][1], float(d3['tau'])*1.04, r'detection threshold $\tau$',
        color='0.5', fontsize=6.5)
ax.set_xlabel(r'deployment scale $\beta$'); ax.set_ylabel('average live edge')
ax.set_title('(d) Alpha decay with deployment', fontsize=9, loc='left')
fig.tight_layout(); fig.savefig('fig3_momentum.pdf'); plt.close(fig)

print("saved fig1_dichotomy.pdf, fig2_phase.pdf, fig3_momentum.pdf")
