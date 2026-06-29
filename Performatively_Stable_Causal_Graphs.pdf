# %% CELL 1 -- montar Drive y localizar el ZIP de Stooq
# ANTES DE CORRER:
#  1. Ve a https://stooq.com/db/h/  -> fila U.S., columna ASCII, Daily -> descarga d_us_txt.zip
#     (pide un CAPTCHA; es una descarga manual de una vez, ~300 MB)
#  2. Sube d_us_txt.zip a una carpeta en Mi unidad, p.ej. Mi unidad/STOOQ/
from google.colab import drive
drive.mount('/content/drive')
import os
STOOQ_DIR = '/content/drive/MyDrive/STOOQ'     # <-- carpeta donde subiste el zip
ZIP_NAME  = 'd_us_txt.zip'
zip_path = os.path.join(STOOQ_DIR, ZIP_NAME)
assert os.path.isfile(zip_path), f'No encuentro {zip_path}. Sube d_us_txt.zip a {STOOQ_DIR}'
print('ZIP encontrado:', zip_path, f'({os.path.getsize(zip_path)/1e6:.0f} MB)')


# %% CELL 2 -- imports + parametros
import numpy as np, pandas as pd, scipy.stats as st
import zipfile, io
import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams.update({'font.family':'serif','font.size':9,'axes.linewidth':0.6,
                 'axes.spines.top':False,'axes.spines.right':False,
                 'figure.dpi':140,'savefig.dpi':200})
np.random.seed(0)

PRICE_MIN   = 5.0      # excluir precio < $5 (Lou-Polk)
N_DECILES   = 10
FORM_MONTHS = 12       # ventana de formacion
SKIP        = 1        # saltar el mes mas reciente
TOP_LIQUID  = 1500     # universo: las N mas liquidas cada mes (senal sin tardar horas)
START_YEAR  = 1990     # Stooq US tiene buena cobertura desde ~1990


# %% CELL 3 -- leer todos los .txt de acciones US del zip -> panel diario
# estructura: data/daily/us/<nasdaq|nyse|nysemkt> stocks/<n>/<ticker>.us.txt
frames = []
with zipfile.ZipFile(zip_path) as z:
    names = [n for n in z.namelist()
             if n.endswith('.txt') and '/us/' in n.lower() and 'stocks' in n.lower()]
    print('ficheros de acciones US:', len(names))
    for i, n in enumerate(names):
        try:
            raw = z.read(n)
            if len(raw) < 50:   # vacio
                continue
            d = pd.read_csv(io.BytesIO(raw))
            d.columns = [c.strip('<>').lower() for c in d.columns]
            if 'close' not in d.columns or 'date' not in d.columns:
                continue
            d = d[['ticker','date','close','vol']].copy()
            frames.append(d)
        except Exception:
            continue
        if i % 1000 == 0:
            print(f'  {i}/{len(names)}', end='\r')
px = pd.concat(frames, ignore_index=True)
px['date'] = pd.to_datetime(px['date'].astype(str), format='%Y%m%d', errors='coerce')
px['ticker'] = px['ticker'].str.replace('.US','',regex=False).str.upper()
px = px.dropna(subset=['date','close'])
px = px[px['date'].dt.year >= START_YEAR]
px['dollar_vol'] = px['close']*px['vol'].fillna(0)
print('\npanel diario:', px.shape, '| tickers:', px.ticker.nunique(),
      '| span:', px.date.dt.year.min(), '-', px.date.dt.year.max())


# %% CELL 4 -- retornos mensuales y semanales
px = px.sort_values(['ticker','date'])
# mensual: ultimo close del mes
px['ym'] = px['date'].dt.to_period('M')
monthly = (px.groupby(['ticker','ym'])
             .agg(close=('close','last'), dvol=('dollar_vol','mean')).reset_index())
monthly['ret'] = monthly.groupby('ticker')['close'].pct_change()
monthly = monthly.dropna(subset=['ret'])
# semanal: ultimo close de la semana -> retorno
px['yw'] = px['date'].dt.to_period('W')
weekly = (px.groupby(['ticker','yw']).agg(close=('close','last')).reset_index())
weekly['ret'] = weekly.groupby('ticker')['close'].pct_change()
weekly = weekly.dropna(subset=['ret'])
print('mensual:', monthly.shape, '| semanal:', weekly.shape)


# %% CELL 5 -- momentum decile cada mes sobre universo liquido
m = monthly.copy()
m['logret'] = np.log1p(m['ret'].clip(-0.95, 5))
m['mom'] = (m.groupby('ticker')['logret']
              .rolling(FORM_MONTHS, min_periods=FORM_MONTHS).sum()
              .shift(SKIP).reset_index(level=0, drop=True))
# filtro liquidez: top N por dollar-vol y precio>=5, cada mes (sin groupby.apply)
m = m[(m.close >= PRICE_MIN) & m.mom.notna()].copy()
m['dvol_rank'] = m.groupby('ym')['dvol'].rank(method='first', ascending=False)
m = m[m['dvol_rank'] <= TOP_LIQUID].copy()
m['decile'] = (m.groupby('ym')['mom']
                 .transform(lambda x: pd.qcut(x, N_DECILES, labels=False, duplicates='drop')+1))
print('panel con decil (universo liquido):', m.shape)


# %% CELL 6 -- COMOMENTUM: corr media de pares semanal en winner y loser
def pair_corr(tickers, wk_win, max_names=120):
    sub = wk_win[wk_win.ticker.isin(tickers)]
    piv = sub.pivot_table(index='yw', columns='ticker', values='ret')
    piv = piv.dropna(axis=1, thresh=int(0.6*len(piv)))
    if piv.shape[1] < 10: return np.nan
    if piv.shape[1] > max_names:
        piv = piv.sample(max_names, axis=1, random_state=0)
    C = piv.corr().values
    iu = np.triu_indices(C.shape[0], 1)
    v = C[iu]; v = v[~np.isnan(v)]
    return v.mean() if len(v) else np.nan

months = sorted(m['ym'].unique())
recs = []
for t in months:
    snap = m[m.ym == t]
    W = snap[snap.decile == N_DECILES].ticker.values
    L = snap[snap.decile == 1].ticker.values
    if len(W) < 10 or len(L) < 10: continue
    wlo = (t.to_timestamp() - pd.DateOffset(months=FORM_MONTHS)).to_period('W')
    whi = t.to_timestamp().to_period('W')
    win = weekly[(weekly.yw >= wlo) & (weekly.yw <= whi)]
    cW = pair_corr(W, win); cL = pair_corr(L, win)
    if not (np.isnan(cW) and np.isnan(cL)):
        recs.append((t, np.nanmean([cW, cL])))
com = pd.DataFrame(recs, columns=['ym','comom']).dropna()
print('serie comomentum:', com.shape, '| media=%.3f' % com.comom.mean())


# %% CELL 7 -- TEST DE FASE: alto comomentum -> reversion (CICLO)
wml = (m[m.decile==N_DECILES].groupby('ym')['ret'].mean()
       - m[m.decile==1].groupby('ym')['ret'].mean()).rename('wml').reset_index()
wml = wml.sort_values('ym').reset_index(drop=True)
wml['fwd12'] = wml['wml'].rolling(12).mean().shift(-12)
wml['fwd24'] = wml['wml'].rolling(24).mean().shift(-24)
mm = com.merge(wml, on='ym', how='inner').dropna(subset=['comom'])
mm['q'] = pd.qcut(mm['comom'], 5, labels=False) + 1
tab = mm.groupby('q')[['wml','fwd12','fwd24']].mean()*100
print('Retorno momentum por quintil de comomentum (%/mes):')
print(tab.to_string())
hi = mm[mm.q==5]; lo = mm[mm.q==1]
for h in ['fwd12','fwd24']:
    a, b = hi[h].dropna(), lo[h].dropna()
    tt = st.ttest_ind(a, b, equal_var=False)
    print(f'{h}: alto={a.mean()*100:+.3f}%  bajo={b.mean()*100:+.3f}%  '
          f'diff={(a.mean()-b.mean())*100:+.3f}%  t={tt.statistic:+.2f} p={tt.pvalue:.1e}')
print('\nTEORIA: alto comomentum -> fwd menor (reversion=ciclo); bajo -> estable.')


# %% CELL 8 -- FIGURAS
fig,ax=plt.subplots(figsize=(3.6,2.6))
ax.plot(com.ym.dt.to_timestamp(), com.comom, color='0.2', lw=0.8)
ax.set_xlabel('fecha'); ax.set_ylabel('comomentum (corr media)')
ax.set_title('Comomentum (Stooq US)', fontsize=9, loc='left')
fig.tight_layout(); fig.savefig('/content/real_fig_comomentum.pdf'); plt.show()

fig,ax=plt.subplots(figsize=(3.4,2.6))
ax.bar(tab.index, tab['fwd12'], color='0.4', width=0.6); ax.axhline(0,color='0.6',lw=0.6)
ax.set_xlabel('quintil comomentum (1=bajo,5=alto)')
ax.set_ylabel('momentum fwd 12m (%/mes)')
ax.set_title('Estable abajo, reversion arriba', fontsize=9, loc='left')
fig.tight_layout(); fig.savefig('/content/real_fig_phase.pdf'); plt.show()
print('figuras en /content')


# %% CELL 9 -- RESULTS BLOCK
print('='*64); print('PEGAME ESTE BLOQUE ENTERO'); print('='*64)
print(f'source                = Stooq_US_daily')
print(f'span                  = {px.date.dt.year.min()}-{px.date.dt.year.max()}')
print(f'n_tickers             = {px.ticker.nunique()}')
print(f'top_liquid_universe   = {TOP_LIQUID}')
print(f'comom_n_months        = {len(com)}')
print(f'comom_mean            = {com.comom.mean():.4f}')
print(f'comom_min             = {com.comom.min():.4f}')
print(f'comom_max             = {com.comom.max():.4f}')
for q in range(1,6):
    if q in tab.index:
        r=tab.loc[q]; print(f'q{q}_wml={r["wml"]:+.4f}  fwd12={r["fwd12"]:+.4f}  fwd24={r["fwd24"]:+.4f}')
for h in ['fwd12','fwd24']:
    a,b=hi[h].dropna(),lo[h].dropna(); tt=st.ttest_ind(a,b,equal_var=False)
    print(f'{h}_hi_minus_lo_pctmo = {(a.mean()-b.mean())*100:.4f}')
    print(f'{h}_t = {tt.statistic:.3f}   {h}_p = {tt.pvalue:.3e}')
print('='*64)
