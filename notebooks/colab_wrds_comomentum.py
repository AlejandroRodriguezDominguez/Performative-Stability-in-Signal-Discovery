# %% CELL 1 -- conexion WRDS
# Requiere cuenta WRDS. La primera vez te pide usuario/clave y crea ~/.pgpass.
!pip -q install wrds
import wrds
db = wrds.Connection()   # introduce credenciales WRDS cuando lo pida
print('conectado a WRDS')


# %% CELL 2 -- imports + parametros
import numpy as np, pandas as pd, scipy.stats as st
import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams.update({'font.family':'serif','font.size':9,'axes.linewidth':0.6,
                 'axes.spines.top':False,'axes.spines.right':False,
                 'figure.dpi':140,'savefig.dpi':200})

START='1970-01-01'; END='2023-12-31'
PRICE_MIN=5.0          # excluir precio < $5 (Lou-Polk)
N_DECILES=10
FORM_MONTHS=12         # ventana de formacion para momentum y para comomentum
SKIP=1                 # saltar mes mas reciente
np.random.seed(0)


# %% CELL 3 -- descargar CRSP mensual (retornos, precio, market cap, exchange)
# msf: retornos mensuales; msenames: exchange code. Filtramos common shares (10,11) y NYSE/AMEX/Nasdaq.
crsp_m = db.raw_sql(f"""
    select a.permno, a.date, a.ret, a.prc, a.shrout,
           b.shrcd, b.exchcd
    from crsp.msf a
    left join crsp.msenames b
      on a.permno=b.permno
     and b.namedt<=a.date and a.date<=b.nameendt
    where a.date between '{START}' and '{END}'
      and b.shrcd in (10,11)
      and b.exchcd in (1,2,3)
""", date_cols=['date'])
crsp_m['date']=pd.to_datetime(crsp_m['date'])
crsp_m['me']=crsp_m['prc'].abs()*crsp_m['shrout']
crsp_m=crsp_m.dropna(subset=['ret'])
print('CRSP mensual:', crsp_m.shape, '| permnos:', crsp_m.permno.nunique())


# %% CELL 4 -- CRSP semanal (para correlaciones), por chunks anuales para no agotar RAM
# dsf 1970-2023 es gigante; lo bajamos anyo a anyo y agregamos a semanal sobre la marcha.
wk_parts=[]
for yr in range(int(START[:4]), int(END[:4])+1):
    d = db.raw_sql(f"""
        select permno, date, ret
        from crsp.dsf
        where date between '{yr}-01-01' and '{yr}-12-31'
    """, date_cols=['date'])
    if d.empty: continue
    d=d.dropna(subset=['ret'])
    d['week']=pd.to_datetime(d['date']).dt.to_period('W')
    part=(d.groupby(['permno','week'])['ret']
          .apply(lambda x:(1+x).prod()-1).reset_index())
    wk_parts.append(part)
    print(f'  {yr}: {len(part)} obs semana-accion', end='\r')
wk=pd.concat(wk_parts, ignore_index=True)
print('\nCRSP semanal total:', wk.shape)


# %% CELL 5 -- formar deciles de momentum cada mes
df=crsp_m.sort_values(['permno','date']).copy()
df['logret']=np.log1p(df['ret'])
# retorno acumulado meses [-12,-2] (skip mes -1)
df['mom']=(df.groupby('permno')['logret']
           .rolling(FORM_MONTHS, min_periods=FORM_MONTHS).sum()
           .shift(SKIP).reset_index(level=0,drop=True))
df=df.dropna(subset=['mom'])
df=df[df['prc'].abs()>=PRICE_MIN]
# decil cada mes (1=loser,10=winner)
df['decile']=(df.groupby('date')['mom']
              .transform(lambda x: pd.qcut(x, N_DECILES, labels=False, duplicates='drop')+1))
print('con decil de momentum:', df.shape)


# %% CELL 6 -- COMOMENTUM: corr media de pares semanal en winner y loser deciles
# Para cada fin de mes t, tomar permnos del decil 10 (W) y 1 (L); correlacionar sus
# retornos semanales en los 12 meses previos; comomentum_t = media(corr_W, corr_L).
def pairwise_mean_corr(permnos, wk_window, max_names=150):
    sub=wk_window[wk_window.permno.isin(permnos)]
    piv=sub.pivot(index='week', columns='permno', values='ret')
    piv=piv.dropna(axis=1, thresh=int(0.6*len(piv)))   # quitar acciones con muchos huecos
    if piv.shape[1]<10: return np.nan
    if piv.shape[1]>max_names:                          # submuestrear por velocidad
        piv=piv.sample(max_names, axis=1, random_state=0)
    C=piv.corr().values
    iu=np.triu_indices(C.shape[0],1)
    v=C[iu]; v=v[~np.isnan(v)]
    return v.mean() if len(v) else np.nan

month_ends=sorted(df['date'].unique())
recs=[]
for t in month_ends:
    snap=df[df['date']==t]
    W=snap[snap.decile==N_DECILES].permno.values
    L=snap[snap.decile==1].permno.values
    wlo=pd.Period(pd.Timestamp(t)-pd.DateOffset(months=FORM_MONTHS),'W')
    whi=pd.Period(pd.Timestamp(t),'W')
    win=wk[(wk.week>=wlo)&(wk.week<=whi)]
    cW=pairwise_mean_corr(W,win); cL=pairwise_mean_corr(L,win)
    if not (np.isnan(cW) and np.isnan(cL)):
        recs.append((pd.Timestamp(t), np.nanmean([cW,cL])))
com=pd.DataFrame(recs, columns=['date','comom']).dropna()
print('serie de comomentum:', com.shape, '| media=%.3f' % com.comom.mean())


# %% CELL 7 -- TEST PRINCIPAL: alto comomentum -> reversion del momentum (CICLO)
# retorno futuro del momentum (WML) a 1, 12, 24 meses tras la formacion
wml=(df[df.decile==N_DECILES].groupby('date')['ret'].mean()
     - df[df.decile==1].groupby('date')['ret'].mean()).rename('wml').reset_index()
wml=wml.sort_values('date').reset_index(drop=True)
wml['fwd1']=wml['wml'].shift(-1)
wml['fwd12']=wml['wml'].rolling(12).mean().shift(-12)
wml['fwd24']=wml['wml'].rolling(24).mean().shift(-24)
m=com.merge(wml, on='date', how='inner').dropna(subset=['comom'])
# quintiles de comomentum
m['q']=pd.qcut(m['comom'],5,labels=False)+1
tab=m.groupby('q')[['wml','fwd1','fwd12','fwd24']].mean()*100
print('Retorno momentum por quintil de comomentum (%/mes):')
print(tab.to_string())
hi=m[m.q==5]; lo=m[m.q==1]
for h in ['fwd12','fwd24']:
    tt=st.ttest_ind(hi[h].dropna(), lo[h].dropna(), equal_var=False)
    diff=(hi[h].mean()-lo[h].mean())*100
    print(f'{h}: alto-comom={hi[h].mean()*100:+.3f}%  bajo-comom={lo[h].mean()*100:+.3f}%  '
          f'diff={diff:+.3f}%  t={tt.statistic:+.2f} p={tt.pvalue:.1e}')
print('\nTEORIA: alto comomentum -> fwd negativo/menor (reversion=ciclo);')
print('        bajo comomentum -> fwd positivo (estable). Es tu diagrama de fases.')


# %% CELL 8 -- FIGURAS
fig,ax=plt.subplots(figsize=(3.6,2.6))
ax.plot(com.date, com.comom, color='0.2', lw=0.8)
ax.set_xlabel('fecha'); ax.set_ylabel('comomentum (corr media)')
ax.set_title('Comomentum (actividad de arbitraje)',fontsize=9,loc='left')
fig.tight_layout(); fig.savefig('/content/real_fig_comomentum.pdf'); plt.show()

fig,ax=plt.subplots(figsize=(3.4,2.6))
ax.bar(tab.index, tab['fwd12'], color='0.4', width=0.6)
ax.axhline(0,color='0.6',lw=0.6)
ax.set_xlabel('quintil de comomentum (1=bajo,5=alto)')
ax.set_ylabel('retorno momentum fwd 12m (%/mes)')
ax.set_title('Estable abajo, reversion arriba',fontsize=9,loc='left')
fig.tight_layout(); fig.savefig('/content/real_fig_phase.pdf'); plt.show()
print('figuras guardadas en /content')


# %% CELL 9 -- RESULTS BLOCK
print('='*64); print('PEGAME ESTE BLOQUE ENTERO'); print('='*64)
print(f'comom_n_months        = {len(com)}')
print(f'comom_mean            = {com.comom.mean():.4f}')
print(f'comom_min             = {com.comom.min():.4f}')
print(f'comom_max             = {com.comom.max():.4f}')
for q in range(1,6):
    r=tab.loc[q]
    print(f'q{q}_wml={r["wml"]:+.4f}  fwd12={r["fwd12"]:+.4f}  fwd24={r["fwd24"]:+.4f}')
for h in ['fwd12','fwd24']:
    tt=st.ttest_ind(hi[h].dropna(), lo[h].dropna(), equal_var=False)
    print(f'{h}_hi_minus_lo_pctmo = {(hi[h].mean()-lo[h].mean())*100:.4f}')
    print(f'{h}_t = {tt.statistic:.3f}   {h}_p = {tt.pvalue:.3e}')
print(f'sample = CRSP {START[:4]}-{END[:4]}')
print('='*64)
