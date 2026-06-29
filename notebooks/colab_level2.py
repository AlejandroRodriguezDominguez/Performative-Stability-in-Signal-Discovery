# %% CELL 1 -- montar Mi unidad y comprobar archivos
from google.colab import drive
drive.mount('/content/drive')
import os
DATA_DIR = '/content/drive/MyDrive/OSAP'   # <-- carpeta en Mi unidad

assert os.path.isdir(DATA_DIR), f'No existe {DATA_DIR}. Crea la carpeta OSAP en Mi unidad.'
print('Archivos en OSAP:')
for f in sorted(os.listdir(DATA_DIR)):
    p = os.path.join(DATA_DIR, f)
    sz = os.path.getsize(p)/1e6 if os.path.isfile(p) else 0
    print(f'   {f}   ({sz:.1f} MB)')

# obligatorios (Nivel 1 + control placebo + patas separadas)
need = ['SignalDoc.csv', 'PredictorLSretWide.csv', 'PredictorPortsFull.csv', 'PlaceboPortsFull.csv']
miss = [f for f in need if not os.path.isfile(os.path.join(DATA_DIR, f))]
assert not miss, f'Faltan archivos obligatorios: {miss}'

# opcionales: ejes de capacidad (holding period y liquidez). Se usan si estan.
HOLD_ZIPS = {h: f'PredictorAltPorts_HoldPer_{h}.zip' for h in [1,3,6,12]}
LIQ_ZIPS  = {'NYSEonly':'PredictorAltPorts_LiqScreen_NYSEonly.zip',
             'Price_gt_5':'PredictorAltPorts_LiqScreen_Price_gt_5.zip',
             'ME_gt_NYSE20pct':'PredictorAltPorts_LiqScreen_ME_gt_NYSE20pct.zip'}
have_hold = {k:v for k,v in HOLD_ZIPS.items() if os.path.isfile(os.path.join(DATA_DIR,v))}
have_liq  = {k:v for k,v in LIQ_ZIPS.items()  if os.path.isfile(os.path.join(DATA_DIR,v))}
print('\nHolding-period zips disponibles:', list(have_hold.keys()))
print('Liquidity-screen zips disponibles:', list(have_liq.keys()))


# %% CELL 2 -- imports + helpers
import numpy as np, pandas as pd, scipy.stats as st
import zipfile, io
import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams.update({'font.family':'serif','font.size':9,'axes.linewidth':0.6,
                 'axes.spines.top':False,'axes.spines.right':False,
                 'figure.dpi':140,'savefig.dpi':200})
np.random.seed(0)

def parse_ym(x):
    s = str(x)
    if 'm' in s:
        y,m = s.split('m'); return pd.Timestamp(int(y), int(m), 1)
    return pd.to_datetime(s, errors='coerce')

def normalize_long(df):
    """Lleva cualquier tabla de retornos a columnas: date, signal, ret (largo)."""
    cols = {c.lower():c for c in df.columns}
    date_c = cols.get('date', df.columns[0])
    if 'signalname' in cols and 'ret' in cols:       # ya es largo, una pata = LS
        out = df.rename(columns={cols['signalname']:'signal', cols['ret']:'ret', date_c:'date'})
        return out[['date','signal','ret']].copy()
    # formato ancho: date + una columna por senal
    wide = df.rename(columns={date_c:'date'})
    return wide.melt(id_vars='date', var_name='signal', value_name='ret')

def long_short_from_portsfull(df):
    """De PredictorPortsFull (date,signalname,port,ret) saca el spread LS por senal:
       port mas alto menos port mas bajo (las dos puntas de la ordenacion)."""
    cols = {c.lower():c for c in df.columns}
    d = df.rename(columns={cols.get('signalname','signalname'):'signal',
                           cols.get('port','port'):'port',
                           cols.get('ret','ret'):'ret',
                           cols.get('date','date'):'date'})
    d = d[['date','signal','port','ret']].dropna(subset=['ret'])
    # 'port' puede ser numerico (1..N) o etiquetas tipo '01','10','LS'. Si hay 'LS', usalo.
    def spread(group):
        ports = group['port'].astype(str)
        if (ports=='LS').any():
            return group.loc[ports=='LS','ret']
        # si no, top - bottom por orden de 'port'
        g = group.copy(); g['pnum'] = pd.to_numeric(g['port'], errors='coerce')
        g = g.dropna(subset=['pnum'])
        if g.empty: return pd.Series(dtype=float)
        lo, hi = g.pnum.min(), g.pnum.max()
        top = g[g.pnum==hi].set_index('date')['ret']
        bot = g[g.pnum==lo].set_index('date')['ret']
        return (top - bot)
    # construir LS por (signal,date)
    recs=[]
    for sig, grp in d.groupby('signal'):
        ls = spread(grp.assign(signal=sig))
        if len(ls):
            tmp = ls.reset_index(); tmp.columns=['date','ret']; tmp['signal']=sig
            recs.append(tmp)
    out = pd.concat(recs, ignore_index=True) if recs else pd.DataFrame(columns=['date','signal','ret'])
    return out

def read_zip_returns(path):
    """Abre un .zip de AltPorts y concatena todos los CSV de retornos que contenga,
       devolviendo LS por senal. Maneja subcarpetas (Original_Cuts, etc.)."""
    frames=[]
    with zipfile.ZipFile(path) as z:
        csvs = [n for n in z.namelist() if n.lower().endswith('.csv')]
        # preferir la carpeta Original_Cuts (sin VW) si existe, para comparar manzanas con manzanas
        pref = [n for n in csvs if 'original_cuts' in n.lower() and 'vw' not in n.lower()]
        use = pref if pref else csvs
        for n in use:
            with z.open(n) as fh:
                try:
                    df = pd.read_csv(fh)
                except Exception:
                    continue
            if 'port' in [c.lower() for c in df.columns]:
                ls = long_short_from_portsfull(df)
            else:
                ls = normalize_long(df)
            if len(ls): frames.append(ls)
    if not frames: return pd.DataFrame(columns=['date','signal','ret'])
    out = pd.concat(frames, ignore_index=True)
    out = out.groupby(['date','signal'], as_index=False)['ret'].mean()  # dedup si varias cuts
    return out


# %% CELL 3 -- metadatos + funcion de regimenes
doc = pd.read_csv(os.path.join(DATA_DIR, 'SignalDoc.csv'))
doc = doc[doc['Cat.Signal'] == 'Predictor'].copy()
doc['Acronym'] = doc['Acronym'].str.strip()
meta = doc[['Acronym','Year','SampleEndYear']].dropna()
meta = meta.rename(columns={'Acronym':'signal','Year':'PubYear','SampleEndYear':'SampleEnd'})
meta['PubYear']=meta.PubYear.astype(int); meta['SampleEnd']=meta.SampleEnd.astype(int)
print(f'{len(meta)} predictores con anyo de publicacion y fin de muestra')

def build_regimes(long, meta):
    long = long.dropna(subset=['ret']).copy()
    long['date'] = long['date'].map(parse_ym)
    long['signal'] = long['signal'].str.strip()
    long = long.dropna(subset=['date'])
    long['year'] = long.date.dt.year
    df = long.merge(meta, on='signal', how='inner').sort_values(['signal','date'])
    def reg(r):
        if r.year <= r.SampleEnd: return 'in_sample'
        if r.year <= r.PubYear:   return 'post_sample'
        return 'post_pub'
    df['regime'] = df.apply(reg, axis=1)
    scale = 1.0 if df.ret.abs().median() < 0.05 else 0.01
    df['ret_dec'] = df.ret * scale
    return df

def decay_stats(df, label):
    g = df.groupby(['signal','regime'])['ret_dec'].mean().reset_index()
    piv = g.pivot(index='signal', columns='regime', values='ret_dec').dropna(subset=['in_sample','post_pub'])
    ins, post = piv['in_sample'].values, piv['post_pub'].values
    abs_decay = ins.mean() - post.mean()                 # cambio absoluto (robusto)
    # fraccion solo si el edge in-sample medio es claramente positivo
    frac = abs_decay/ins.mean() if ins.mean() > 0.001 else np.nan
    tt = st.ttest_rel(ins, post)
    fr_txt = f'{frac*100:.1f}%' if not np.isnan(frac) else 'n/a'
    print(f'[{label}] n={len(piv)}  in={ins.mean()*100:.3f}%  post={post.mean()*100:.3f}%  '
          f'abs_decay={abs_decay*100:.3f}pp  frac={fr_txt}  t={tt.statistic:.2f} p={tt.pvalue:.1e}')
    return dict(label=label, n=len(piv), edge_in=ins.mean(), edge_post=post.mean(),
                abs_decay=abs_decay, decay_frac=frac, t=tt.statistic, p=tt.pvalue, piv=piv)


# %% CELL 4 -- EXP A: decay headline (usar LSretWide: limpio, todas las senales)
ls_main = normalize_long(pd.read_csv(os.path.join(DATA_DIR,'PredictorLSretWide.csv')))
dfA = build_regimes(ls_main, meta)
A = decay_stats(dfA, 'PRED headline')


# %% CELL 5 -- EXP B: PLACEBO control (no debe haber decay)
pl = pd.read_csv(os.path.join(DATA_DIR,'PlaceboPortsFull.csv'))
ls_pl = long_short_from_portsfull(pl) if 'port' in [c.lower() for c in pl.columns] else normalize_long(pl)
# los placebos no tienen Year/SampleEnd propios; usamos el calendario medio de predictores
# (control: aplicamos las MISMAS ventanas temporales medias). Construimos pseudo-meta.
pub_med = int(meta.PubYear.median()); end_med = int(meta.SampleEnd.median())
meta_pl = pd.DataFrame({'signal': ls_pl['signal'].unique()})
meta_pl['PubYear']=pub_med; meta_pl['SampleEnd']=end_med
dfB = build_regimes(ls_pl, meta_pl)
B = decay_stats(dfB, 'PLACEBO')
print(f'  -> control OK si el decay del placebo es ~0 y NO significativo')


# %% CELL 6 -- EXP C: REVIVAL / ciclo (unico del paper), sobre predictores
def revival_test(df, label):
    post_df = df[df.regime=='post_pub']
    rows=[]
    for s, sub in post_df.groupby('signal'):
        sub=sub.sort_values('date')
        if len(sub)<72: continue
        e=sub['ret_dec'].rolling(36).mean().dropna().values
        if len(e)<24: continue
        med=np.median(e); lo,hi=[],[]
        for t in range(len(e)-12):
            (lo if e[t]<med else hi).append(e[t+12])
        if lo and hi: rows.append((s,np.mean(lo),np.mean(hi)))
    rev=pd.DataFrame(rows,columns=['signal','after_crowded','after_slack'])
    tt=st.ttest_rel(rev['after_crowded'],rev['after_slack'])
    fr=(rev.after_crowded>rev.after_slack).mean()
    print(f'[{label}] revival n={len(rev)}  after_crowded={rev.after_crowded.mean()*100:.3f}%  '
          f'after_slack={rev.after_slack.mean()*100:.3f}%  t={tt.statistic:.2f} p={tt.pvalue:.1e}  frac={fr*100:.0f}%')
    return dict(label=label,n=len(rev),ac=rev.after_crowded.mean(),as_=rev.after_slack.mean(),
                t=tt.statistic,p=tt.pvalue,frac=fr,rev=rev)
C = revival_test(dfA,'PRED')
Cpl = revival_test(dfB,'PLACEBO')   # el placebo tampoco debe revivir


# %% CELL 7 -- EXP D: CAPACIDAD = escala de despliegue (phase diagram real)
# La teoria predice: menos capacidad -> mas decay. Holding corto y screens
# restrictivos = menos capacidad efectiva. Medimos decay_frac por nivel.
cap_rows=[]
# eje holding period (1<3<6<12 meses; holding corto = mas turnover = menos capacidad)
for h, fn in have_hold.items():
    ls = read_zip_returns(os.path.join(DATA_DIR, fn))
    if len(ls)==0:
        print('  (vacio)', fn); continue
    dfh = build_regimes(ls, meta)
    r = decay_stats(dfh, f'HoldPer_{h}')
    cap_rows.append(('hold', h, r['abs_decay'], r['n']))
# eje liquidez (mas restrictivo = menos capacidad). orden aproximado de severidad:
liq_order = {'Price_gt_5':1,'NYSEonly':2,'ME_gt_NYSE20pct':3}
for k, fn in have_liq.items():
    ls = read_zip_returns(os.path.join(DATA_DIR, fn))
    if len(ls)==0:
        print('  (vacio)', fn); continue
    dfl = build_regimes(ls, meta)
    r = decay_stats(dfl, f'Liq_{k}')
    cap_rows.append(('liq', liq_order.get(k,9), r['abs_decay'], r['n']))
cap = pd.DataFrame(cap_rows, columns=['axis','level','abs_decay','n'])
print('\nCapacidad vs decay absoluto (pp/mes):')
print(cap.to_string())
hold = cap[cap.axis=='hold'].sort_values('level')
if len(hold)>=3:
    rho,pr = st.spearmanr(hold.level, hold.abs_decay)
    print(f'Spearman(holding period, abs_decay) = {rho:.2f} (p={pr:.2f})  '
          f'[esperado <0: holding largo=mas capacidad=menos decay]')


# %% CELL 8 -- FIGURAS
# Fig A: decay event-time, predictores vs placebo
for d,lab,col in [(dfA,'predictors','0.1'),(dfB,'placebo','0.55')]:
    d['rel']=d.year-d.PubYear
    prof=(d[d.rel.between(-10,10)].groupby('rel')['ret_dec'].mean()*100)
    plt.plot(prof.index,prof.values,marker='o',ms=2.5,mfc='white',mew=0.6,color=col,label=lab)
plt.axvline(0,color='0.5',ls='--',lw=0.9); plt.axhline(0,color='0.7',lw=0.6)
plt.xlabel('anyos relativos a publicacion'); plt.ylabel('edge L-S medio (%/mes)')
plt.legend(fontsize=7,frameon=False); plt.title('Decay: predictores vs placebo',fontsize=9,loc='left')
plt.tight_layout(); plt.savefig('/content/real_fig_decay.pdf'); plt.show()

# Fig B: revival scatter
rev=C['rev']
lim=[min(rev.after_crowded.min(),rev.after_slack.min())*100,
     max(rev.after_crowded.max(),rev.after_slack.max())*100]
plt.plot(lim,lim,color='0.6',ls='--',lw=0.9)
plt.scatter(rev.after_slack*100,rev.after_crowded*100,s=14,facecolors='white',edgecolors='0.1',linewidths=0.7)
plt.xlabel('edge tras ventana slack (%/mes)'); plt.ylabel('edge tras ventana crowded (%/mes)')
plt.title('Revival: crowded -> edge mayor',fontsize=9,loc='left')
plt.tight_layout(); plt.savefig('/content/real_fig_revival.pdf'); plt.show()

# Fig C: capacidad vs decay (phase diagram real)
if len(cap):
    fig,ax=plt.subplots(figsize=(3.6,2.6))
    for axis,mk,col in [('hold','o','0.1'),('liq','s','0.5')]:
        sub=cap[cap.axis==axis].sort_values('level')
        if len(sub): ax.plot(sub.level,sub.abs_decay*100,marker=mk,color=col,
                             mfc='white',mew=0.6,label=axis)
    ax.set_xlabel('escala de capacidad (nivel)'); ax.set_ylabel('decay post-pub (pp/mes)')
    ax.legend(fontsize=7,frameon=False); ax.set_title('Capacidad vs decay',fontsize=9,loc='left')
    plt.tight_layout(); plt.savefig('/content/real_fig_capacity.pdf'); plt.show()
print('figuras guardadas en /content')


# %% CELL 9 -- RESULTS BLOCK (copiame TODO)
print('='*64); print('PEGAME ESTE BLOQUE ENTERO'); print('='*64)
print(f'N_signals_total          = {len(meta)}')
print(f'PRED_n_decay             = {A["n"]}')
print(f'PRED_edge_in_pctmo       = {A["edge_in"]*100:.4f}')
print(f'PRED_edge_post_pctmo     = {A["edge_post"]*100:.4f}')
print(f'PRED_abs_decay_pp        = {A["abs_decay"]*100:.3f}')
print(f'PRED_decay_t             = {A["t"]:.3f}')
print(f'PRED_decay_p             = {A["p"]:.3e}')
print(f'PLACEBO_n_decay          = {B["n"]}')
print(f'PLACEBO_abs_decay_pp     = {B["abs_decay"]*100:.3f}')
print(f'PLACEBO_decay_t          = {B["t"]:.3f}')
print(f'PLACEBO_decay_p          = {B["p"]:.3e}')
print(f'PRED_revival_n           = {C["n"]}')
print(f'PRED_after_crowded_pctmo = {C["ac"]*100:.4f}')
print(f'PRED_after_slack_pctmo   = {C["as_"]*100:.4f}')
print(f'PRED_revival_t           = {C["t"]:.3f}')
print(f'PRED_revival_p           = {C["p"]:.3e}')
print(f'PRED_frac_reviving_pct   = {C["frac"]*100:.1f}')
print(f'PLACEBO_revival_t        = {Cpl["t"]:.3f}')
print(f'PLACEBO_revival_p        = {Cpl["p"]:.3e}')
print('CAPACITY_table (axis,level,decay_pct,n):')
for _,r in cap.iterrows():
    print(f'   {r.axis},{int(r.level)},{r.abs_decay*100:.3f},{int(r.n)}')
print(f'data_release             = OSAP_Oct2025')
print('='*64)
