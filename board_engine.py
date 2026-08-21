#!/usr/bin/env python3
"""NQ System — autopilot board engine (lite/mechanical mode).
Fetches NQ/ES/YM 1m via yfinance, computes the system's mechanical layers,
renders board.html. Narrative/bias layer intentionally absent in auto mode."""
import sys, traceback, datetime as dtm
import pandas as pd, numpy as np
TZ='America/New_York'; TICK=0.25
CLASS_P={'5M':'33% n=2,999','15M':'35% n=997','30M':'39% n=480','1H':'32% n=247','4H':'40% n=58'}

def fetch(sym, interval, period):
    import yfinance as yf
    df=yf.download(sym, interval=interval, period=period, progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns=[c[0] for c in df.columns]
    df=df.rename(columns=str.lower)[['open','high','low','close']].dropna()
    idx=df.index
    if idx.tz is None: idx=idx.tz_localize('UTC')
    df.index=idx.tz_convert(TZ); df.index.name='dt'
    return df.reset_index()

def sday(s): return (s - pd.Timedelta(hours=18)).dt.date

def render(ctx):
    rows=''.join(f"<div class='lv'><span class='p'>{p}</span><span class='t'>{t}</span></div>" for p,t in ctx['ladder'])
    cards=''.join(f"<tr><td>{a}</td><td class='mono'>{b}</td><td>{c}</td></tr>" for a,b,c in ctx['cards'])
    return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>NQ auto-board</title><style>
body{{background:#101318;color:#dae0ea;font:14.5px -apple-system,Segoe UI,Roboto,Arial;margin:0;padding:18px}}
h1{{font-size:19px;color:#e8edf5;margin:0 0 2px}} .sub{{color:#8e97a8;font-size:12px;font-family:ui-monospace,monospace}}
.grid{{display:grid;grid-template-columns:1fr 280px;gap:16px;margin-top:14px}}@media(max-width:820px){{.grid{{grid-template-columns:1fr}}}}
.card{{background:#161b23;border:1px solid #2a3140;border-radius:10px;padding:14px 16px;margin-bottom:14px}}
table{{width:100%;border-collapse:collapse;font-size:13px}} td{{padding:6px;border-bottom:1px solid #222836;vertical-align:top}}
.mono{{font-family:ui-monospace,monospace;color:#e8edf5;white-space:nowrap}}
.lv{{display:flex;justify-content:space-between;font-family:ui-monospace,monospace;font-size:11.5px;padding:2px 6px;border-left:3px solid #2a3140;margin:2px 0}}
.lv .p{{color:#e8edf5}} .lv .t{{color:#8e97a8;font-size:10px}}
.warn{{color:#fbbf24;font-size:11.5px}} h2{{font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:#e8edf5;margin:0 0 8px}}
</style></head><body>
<h1>NQ SYSTEM — AUTO BOARD (mechanical)</h1>
<div class='sub'>generated {ctx['ts']} · data: Yahoo continuous futures (unofficial; may lag CME by minutes/ticks) · narrative layer OFF in auto mode · not advice</div>
<div class='grid'><div>
<div class='card'><h2>Session</h2><table>{ctx['session']}</table></div>
<div class='card'><h2>DCV 2.0</h2><table>{ctx['dcv']}</table></div>
<div class='card'><h2>Objects & statuses</h2><table>{cards}</table></div>
</div><div><div class='card'><h2>Ladder</h2>{rows}</div></div></div>
<div class='warn'>{ctx['warn']}</div></body></html>"""

def main():
    warn=''
    nq=fetch('NQ=F','1m','5d'); es=fetch('ES=F','1m','5d'); ym=fetch('YM=F','1m','5d')
    dly=fetch('NQ=F','1d','1y')
    now=nq['dt'].iloc[-1]; spot=float(nq['close'].iloc[-1])
    nq['sd']=sday(nq['dt']); cur=nq['sd'].iloc[-1]
    s=nq[nq['sd']==cur]
    O=float(s['open'].iloc[0]); Hh=float(s['high'].max()); Ll=float(s['low'].min())
    # A20 + bands
    r=((dly['high']-dly['low'])/TICK).tail(20); A=float(r.mean())
    up=(Hh-O)/TICK; dn=(O-Ll)/TICK
    b=lambda x: f"{x:,.2f}"
    dcv=(f"<tr><td>A (20d mean range)</td><td class='mono'>{A:,.0f}t</td></tr>"
         f"<tr><td>excursions</td><td class='mono'>+{up:,.0f}t ({up/A:.2f}A) / \u2212{dn:,.0f}t ({dn/A:.2f}A)</td></tr>"
         f"<tr><td>upper value / coin / alarm</td><td class='mono'>{b(O+.15*A*TICK)}\u2013{b(O+.34*A*TICK)} / \u2013{b(O+.5*A*TICK)} / >{b(O+.5*A*TICK)}</td></tr>"
         f"<tr><td>lower value / coin / alarm</td><td class='mono'>{b(O-.34*A*TICK)}\u2013{b(O-.15*A*TICK)} / {b(O-.5*A*TICK)}\u2013 / <{b(O-.5*A*TICK)}</td></tr>")
    # pools
    def pool(h0,h1):
        g=s[(s['dt'].dt.hour>=h0)&(s['dt'].dt.hour<h1)]
        if not len(g): return None
        hi,lo=float(g['high'].max()),float(g['low'].min())
        after=s[s['dt']>g['dt'].iloc[-1]]
        return hi,lo,(after['high']>=hi).any(),(after['low']<=lo).any()
    ses=f"<tr><td>O / H / L / spot</td><td class='mono'>{b(O)} / {b(Hh)} / {b(Ll)} / {b(spot)}</td></tr>"
    for nm,h0,h1 in [('Asia 19\u201322',19,22),('London 2\u20135',2,5)]:
        p=pool(h0,h1)
        if p: ses+=f"<tr><td>{nm}</td><td class='mono'>H {b(p[0])} {'taken' if p[2] else 'INTACT'} · L {b(p[1])} {'taken' if p[3] else 'INTACT'}</td></tr>"
    ab=(s['close']>O).any(); bl=(s['close']<O).any()
    ses+=f"<tr><td>6PM open</td><td class='mono'>{'efficient' if ab and bl else ('above owed' if not ab else 'below owed')}</td></tr>"
    # ledger (standing) -> macro
    SH=[];SL=[]
    def cls(t): return 'retail' if not t else ('protected' if all(x[1]=='retail' for x in t) else 'ins')
    for _,rw in dly.iterrows():
        th=[x for x in SH if rw['high']>x[0]]; [SH.remove(x) for x in th]; SH.append((float(rw['high']),cls(th)))
        tl=[x for x in SL if rw['low']<x[0]]; [SL.remove(x) for x in tl]; SL.append((float(rw['low']),cls(tl)))
    insH=[x for x in SH if x[1]!='retail' and x[0]>spot]; insL=[x for x in SL if x[1]!='retail' and x[0]<spot]
    ladder=[]
    if insH: hh=min(insH,key=lambda x:x[0]); ladder.append((b(hh[0]),'ins high (macro)'))
    # connectors
    di=nq.set_index('dt'); times=nq['dt'].values; Hn=nq['high'].values; Ln=nq['low'].values
    anchor=pd.Timestamp(str(nq['sd'].iloc[0]))+pd.Timedelta(hours=18); anchor=anchor.tz_localize(TZ)
    def rsm(m): return di.resample(f'{m}min',origin=anchor,label='left').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna().reset_index()
    cards=[]
    for tfm,lab in [(240,'4H'),(60,'1H'),(30,'30M'),(15,'15M'),(5,'5M')]:
        df=rsm(tfm); vz=[]
        for i in range(1,len(df)):
            Ac,Bc=df.iloc[i-1],df.iloc[i]; bt=max(Ac['open'],Ac['close']); bb=min(Ac['open'],Ac['close'])
            mc=df['dt'].iloc[i]+pd.Timedelta(minutes=tfm)
            if mc>now: continue
            zz=[]
            if Ac['high']>bt and Bc['close']>=bt+0.5*(Ac['high']-bt): zz.append(('long',float(bt),float(Ac['high'])))
            if Ac['low']<bb and Bc['close']<=bb-0.5*(bb-Ac['low']): zz.append(('short',float(Ac['low']),float(bb)))
            for dd,lo,hi in zz:
                i0=int(np.searchsorted(times,np.datetime64(mc.tz_convert('UTC').tz_localize(None)))); st='virgin'
                for j in range(i0,len(times)):
                    if Ln[j]<=hi and Hn[j]>=lo: st='spent'; break
                if st=='virgin' and abs((lo+hi)/2-spot)<450: vz.append((dd,lo,hi))
        for dd,lo,hi in sorted(vz,key=lambda z:abs((z[1]+z[2])/2-spot))[:2]:
            e=hi if dd=='long' else lo
            stp=e-37.5 if dd=='long' else e+37.5; tg=e+75 if dd=='long' else e-75
            cards.append((f"{lab} connector {dd} {b(lo)}\u2013{b(hi)}",f"E {b(e)} S {b(stp)} 2R {b(tg)}",CLASS_P[lab]))
            ladder.append((f"{b(lo)}\u2013{b(hi)}",f"{lab} {dd} seam"))
    # MIST triple replay (actives near spot)
    m=nq.merge(es[['dt','high','low']],on='dt',suffixes=('','_e')).merge(ym[['dt','high','low']],on='dt',suffixes=('','_y'))
    if len(m)>500:
        m=m.iloc[:-1].reset_index(drop=True)
        def piv(sr,md):
            v=sr.values;o=np.zeros(len(v),bool)
            if md=='H': o[1:-1]=(v[1:-1]>v[:-2])&(v[1:-1]>v[2:])
            else: o[1:-1]=(v[1:-1]<v[:-2])&(v[1:-1]<v[2:])
            return o
        PH=[piv(m['high'],'H'),piv(m['high_e'],'H'),piv(m['high_y'],'H')]
        PL=[piv(m['low'],'L'),piv(m['low_e'],'L'),piv(m['low_y'],'L')]
        lv=[]
        for i in range(1,len(m)-1):
            if PH[0][i]&PH[1][i]&PH[2][i]: lv.append({'s':'H','tip':float(m['high'][i]),'er':m['high_e'][i],'yr':m['high_y'][i],'i':i,'st':'cand','eb':False,'yb':False})
            if PL[0][i]&PL[1][i]&PL[2][i]: lv.append({'s':'L','tip':float(m['low'][i]),'er':m['low_e'][i],'yr':m['low_y'][i],'i':i,'st':'cand','eb':False,'yb':False})
        for j in range(2,len(m)):
            rr=m.iloc[j]
            for Q in lv:
                if j<=Q['i']+1 or Q['st'] in('still','taken'): continue
                if Q['s']=='H':
                    t=rr['high']>=Q['tip']
                    if Q['st']=='cand':
                        if t: Q['st']='still'; continue
                        Q['eb']|=rr['high_e']>Q['er']; Q['yb']|=rr['high_y']>Q['yr']
                        if Q['eb'] and Q['yb']: Q['st']='active'
                    elif Q['st']=='active' and t: Q['st']='taken'
                else:
                    t=rr['low']<=Q['tip']
                    if Q['st']=='cand':
                        if t: Q['st']='still'; continue
                        Q['eb']|=rr['low_e']<Q['er']; Q['yb']|=rr['low_y']<Q['yr']
                        if Q['eb'] and Q['yb']: Q['st']='active'
                    elif Q['st']=='active' and t: Q['st']='taken'
        eq=(Hh+Ll)/2
        for Q in sorted([x for x in lv if x['st']=='active'],key=lambda z:abs(z['tip']-spot))[:6]:
            hp=(Q['s']=='L' and Q['tip']<eq) or (Q['s']=='H' and Q['tip']>eq)
            cards.append((f"MIST active {'short' if Q['s']=='H' else 'long'} {b(Q['tip'])}",f"\u00b1150t race on touch","52% n=398" if hp else "43\u201349%"))
            ladder.append((b(Q['tip']),f"MIST {'S' if Q['s']=='H' else 'L'}{' · HP' if hp else ''}"))
    else:
        warn+=' MIST off: symbol timestamps failed to align this pull.'
    ladder.append((b(spot),'SPOT')); ladder.append((b((Hh+Ll)/2),'micro EQ'))
    if insL: llw=max(insL,key=lambda x:x[0]); ladder.append((b(llw[0]),'ins low (macro)'))
    ladder=sorted(set(ladder),key=lambda z:-float(z[0].replace(',','').split('\u2013')[0]))
    ctx={'ts':now.strftime('%a %b %d, %I:%M %p ET'),'session':ses,'dcv':dcv,'cards':cards[:14],'ladder':ladder[:22],'warn':warn or 'auto mode: mechanical layers only \u2014 narrative, scorecard, and judgment live in the chat sessions.'}
    open('board.html','w').write(render(ctx))
    print('board.html written', now)

if __name__=='__main__':
    try: main()
    except Exception:
        traceback.print_exc()
        open('board.html','a').write(f"<div style='color:#f87171;font-family:monospace'>engine error {dtm.datetime.now()}: kept last good board</div>")
        sys.exit(0)
