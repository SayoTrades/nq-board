#!/usr/bin/env python3
"""NQ System auto-board v2 — renders index.html in the session-board style. Mechanical layers only."""
import sys, traceback, datetime as dtm
import pandas as pd, numpy as np
TZ='America/New_York'; TICK=0.25
CP={'5M':'33% · n=2,999','15M':'35% · n=997','30M':'39% · n=480','1H':'32% · n=247','4H':'40% · n=58'}

def fetch(sym,interval,period):
    import yfinance as yf
    df=yf.download(sym,interval=interval,period=period,progress=False,auto_adjust=False)
    if isinstance(df.columns,pd.MultiIndex): df.columns=[c[0] for c in df.columns]
    df=df.rename(columns=str.lower)[['open','high','low','close']].dropna()
    idx=df.index
    if idx.tz is None: idx=idx.tz_localize('UTC')
    df.index=idx.tz_convert(TZ); df.index.name='dt'
    return df.reset_index()

CSS=""":root{--bg:#101318;--panel:#161b23;--line:#2a3140;--tx:#dae0ea;--mut:#8e97a8;--grn:#4ade80;--grnD:#123423;--red:#f87171;--redD:#3a1717;--amb:#fbbf24;--cyn:#38bdf8;--blu:#6ea8fe;--wht:#e8edf5}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--tx);font:15px/1.6 -apple-system,"Segoe UI",Roboto,Arial,sans-serif;padding:26px 18px 50px}
.wrap{max-width:1080px;margin:0 auto}
.eyebrow{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--mut)}
h1{font-size:24px;font-weight:650;margin:4px 0 4px;color:var(--wht)}
h2{font-size:12.5px;letter-spacing:.16em;text-transform:uppercase;font-weight:600;margin:0 0 12px;color:var(--wht)}
.head{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:22px}
.stat .k{font-size:11px;color:var(--mut);letter-spacing:.14em;text-transform:uppercase}
.stat .v{font-family:ui-monospace,Consolas,monospace;font-size:16px;color:var(--wht)}
.stats{display:flex;gap:22px;flex-wrap:wrap}
.pill{display:inline-block;padding:6px 14px;border-radius:999px;font-family:ui-monospace,Consolas,monospace;font-size:12.5px;font-weight:700;background:#2b2410;color:var(--amb);border:1px solid #6b5714}
.grid{display:grid;grid-template-columns:1fr 300px;gap:20px}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:18px}
.card.g{border-left:3px solid var(--grn)}.card.r{border-left:3px solid var(--red)}.card.a{border-left:3px solid var(--amb)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
td,th{padding:7px 8px;border-bottom:1px solid #222836;text-align:left;vertical-align:top}
th{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}
.mono{font-family:ui-monospace,Consolas,monospace;color:var(--wht);white-space:nowrap}
.gg{color:var(--grn)}.rr{color:var(--red)}.aa{color:var(--amb)}
.tag{font-family:ui-monospace,Consolas,monospace;font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:999px;white-space:nowrap}
.tag.s{background:var(--redD);color:var(--red)}.tag.l{background:var(--grnD);color:var(--grn)}.tag.u{background:#242a35;color:var(--mut);border:1px solid var(--line)}
.ladder{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 12px;position:sticky;top:14px;font-family:ui-monospace,Consolas,monospace;font-size:12px}
.lv{display:flex;justify-content:space-between;gap:8px;padding:3px 6px;border-left:3px solid transparent;margin:2px 0;white-space:nowrap}
.lv .p{color:var(--wht)}.lv .t{color:var(--mut);font-size:10.5px;overflow:hidden;text-overflow:ellipsis}
.lv.ins .p{color:var(--red)}.lv.ins{border-left-color:var(--red)}
.lv.conn .p{color:var(--blu)}.lv.conn{border-left-color:var(--blu)}
.lv.tme .p{color:var(--amb)}.lv.tme{border-left-color:var(--amb)}
.lv.eq .p{color:var(--wht)}.lv.eq{border-left-color:var(--wht)}
.lv.spot{background:#0d2233;border-left-color:var(--cyn)}.lv.spot .p{font-weight:800}
.note{font-size:12.5px;color:var(--mut);line-height:1.5}"""

def main():
    nq=fetch('NQ=F','1m','5d'); es=fetch('ES=F','1m','5d'); ym=fetch('YM=F','1m','5d'); dly=fetch('NQ=F','1d','1y')
    now=nq['dt'].iloc[-1]; spot=float(nq['close'].iloc[-1])
    nq['sd']=(nq['dt']-pd.Timedelta(hours=18)).dt.date
    s=nq[nq['sd']==nq['sd'].iloc[-1]]
    O=float(s['open'].iloc[0]); Hh=float(s['high'].max()); Ll=float(s['low'].min()); mEQ=(Hh+Ll)/2
    r=((dly['high']-dly['low'])/TICK).tail(20); A=float(r.mean())
    up=(Hh-O)/TICK; dn=(O-Ll)/TICK
    b=lambda x:f"{x:,.2f}"
    def bucket(x):
        if x<0.15: return 'sub-value'
        if x<0.34: return 'VALUE (73%)'
        if x<0.50: return 'coin-flip (53%)'
        return 'PAST ALARM (85%)'
    # ledger
    SH=[];SL=[]
    def cls(t): return 'retail' if not t else ('protected' if all(x[1]=='retail' for x in t) else 'ins')
    for _,rw in dly.iterrows():
        th=[x for x in SH if rw['high']>x[0]]; [SH.remove(x) for x in th]; SH.append((float(rw['high']),cls(th)))
        tl=[x for x in SL if rw['low']<x[0]]; [SL.remove(x) for x in tl]; SL.append((float(rw['low']),cls(tl)))
    insH=[x for x in SH if x[1]!='retail' and x[0]>spot]; insL=[x for x in SL if x[1]!='retail' and x[0]<spot]
    macro=''
    if insH and insL:
        hh=min(insH,key=lambda x:x[0]); llw=max(insL,key=lambda x:x[0]); meq=(hh[0]+llw[0])/2
        macro=f"<tr><td>macro range</td><td class='mono'>{b(llw[0])} \u2194 {b(hh[0])} · EQ {b(meq)} · spot {'premium' if spot>meq else 'discount'}</td></tr>"
    # pools
    pr=''
    for nm,h0,h1 in [('Asia 19\u201322',19,22),('London 2\u20135',2,5)]:
        g=s[(s['dt'].dt.hour>=h0)&(s['dt'].dt.hour<h1)]
        if len(g):
            hi,lo=float(g['high'].max()),float(g['low'].min()); aft=s[s['dt']>g['dt'].iloc[-1]]
            pr+=f"<tr><td>{nm}</td><td class='mono'>H {b(hi)} {'taken' if (aft['high']>=hi).any() else '<span class=gg>INTACT</span>'} · L {b(lo)} {'taken' if (aft['low']<=lo).any() else '<span class=gg>INTACT</span>'}</td></tr>"
    ab=(s['close']>O).any(); bl=(s['close']<O).any()
    # connectors
    di=nq.set_index('dt'); times=nq['dt'].values; Hn=nq['high'].values; Ln=nq['low'].values
    anchor=(pd.Timestamp(str(nq['sd'].iloc[0]))+pd.Timedelta(hours=18)).tz_localize(TZ)
    def rsm(m): return di.resample(f'{m}min',origin=anchor,label='left').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna().reset_index()
    cards=[]; lad=[]
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
            e=hi if dd=='long' else lo; stp=e-37.5 if dd=='long' else e+37.5; tg=e+75 if dd=='long' else e-75
            tc='l' if dd=='long' else 's'
            cards.append(f"<tr><td>{lab} connector <b>{dd}</b> {b(lo)}\u2013{b(hi)}</td><td class='mono'>{b(e)} / {b(stp)} / {b(tg)}</td><td><span class='tag {tc}'>{CP[lab]}</span></td></tr>")
            lad.append((max(lo,hi),f"{b(lo)}\u2013{b(hi)}",f"{lab} {dd} seam",'conn'))
    # MIST
    mistN=0
    m=nq.merge(es[['dt','high','low']],on='dt',suffixes=('','_e')).merge(ym[['dt','high','low']],on='dt',suffixes=('','_y'))
    actH=actL=0
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
        acts=[x for x in lv if x['st']=='active']
        actH=sum(1 for x in acts if x['s']=='H'); actL=sum(1 for x in acts if x['s']=='L')
        for Q in sorted(acts,key=lambda z:abs(z['tip']-spot))[:6]:
            hp=(Q['s']=='L' and Q['tip']<mEQ) or (Q['s']=='H' and Q['tip']>mEQ)
            tc='s' if Q['s']=='H' else 'l'
            cards.append(f"<tr><td>MIST active <b>{'short' if Q['s']=='H' else 'long'}</b> {b(Q['tip'])}{' · HP' if hp else ''}</td><td class='mono'>\u00b1150t race on touch</td><td><span class='tag {tc}'>{'52% · n=398' if hp else '43\u201349%'}</span></td></tr>")
            lad.append((Q['tip'],b(Q['tip']),f"MIST {'S' if Q['s']=='H' else 'L'}{' HP' if hp else ''}",'tme'))
        mistN=len(acts)
    # votes (mechanical, per indicator logic)
    v_m = 1 if actH>actL else (-1 if actL>actH else 0)
    v_d = 1 if (up>=300 and up>dn) else (-1 if (dn>=300 and dn>up) else 0)
    v_e = 1 if spot<mEQ else -1
    tally=v_m+v_d+v_e
    pill=f"VOTES {'\u2191' if tally>0 else ('\u2193' if tally<0 else '\u2014')} · MIST {actH}H/{actL}L · DCV {'+' if v_d>0 else ('-' if v_d<0 else '0')} · EQ {'disc' if v_e>0 else 'prem'}"
    # bands + ladder assembly
    for px,t,c in [(O+.5*A*TICK,'upper alarm','tme'),(O+.34*A*TICK,'upper value top','tme'),(O+.15*A*TICK,'upper value floor','tme'),
                   (O-.15*A*TICK,'lower value top','tme'),(O-.34*A*TICK,'lower value floor','tme'),(O-.5*A*TICK,'lower alarm','tme')]:
        lad.append((px,b(px),t,c))
    lad.append((spot,b(spot),'SPOT','spot')); lad.append((mEQ,b(mEQ),'micro EQ','eq')); lad.append((O,b(O),'session open','eq'))
    if insH: lad.append((hh[0],b(hh[0]),f"ins high",'ins'))
    if insL: lad.append((llw[0],b(llw[0]),f"ins low",'ins'))
    lad=sorted({(round(p,2),lbl,t,c) for p,lbl,t,c in lad},key=lambda z:-z[0])
    lrows=''.join(f"<div class='lv {c}'><span class='p'>{lbl}</span><span class='t'>{t}</span></div>" for _,lbl,t,c in lad[:26])
    dcv=(f"<tr><th>zone</th><th>range</th><th>base rate</th></tr>"
         f"<tr><td>Upper alarm</td><td class='mono'>above {b(O+.5*A*TICK)}</td><td>past-alarm \u2192 85% close with move</td></tr>"
         f"<tr><td>Upper coin-flip</td><td class='mono'>{b(O+.34*A*TICK)} \u2013 {b(O+.5*A*TICK)}</td><td>53%</td></tr>"
         f"<tr><td class='rr'><b>UPPER VALUE</b></td><td class='mono'>{b(O+.15*A*TICK)} \u2013 {b(O+.34*A*TICK)}</td><td>stops here \u2192 73% close red-side</td></tr>"
         f"<tr><td class='gg'><b>LOWER VALUE</b></td><td class='mono'>{b(O-.34*A*TICK)} \u2013 {b(O-.15*A*TICK)}</td><td>stops here \u2192 73% close green-side</td></tr>"
         f"<tr><td>Lower coin-flip</td><td class='mono'>{b(O-.5*A*TICK)} \u2013 {b(O-.34*A*TICK)}</td><td>53%</td></tr>"
         f"<tr><td>Lower alarm</td><td class='mono'>below {b(O-.5*A*TICK)}</td><td>past-alarm \u2192 85% close with move</td></tr>")
    ses=(f"<tr><td>O / H / L / spot</td><td class='mono'>{b(O)} / {b(Hh)} / {b(Ll)} / {b(spot)}</td></tr>"
         f"<tr><td>excursions</td><td class='mono'>+{up:,.0f}t ({up/A:.2f}A · {bucket(up/A)}) / \u2212{dn:,.0f}t ({dn/A:.2f}A · {bucket(dn/A)})</td></tr>"
         f"<tr><td>6PM open</td><td class='mono'>{'efficient' if ab and bl else ('above owed' if not ab else 'below owed')}</td></tr>"
         +pr+macro+f"<tr><td>A (20-day)</td><td class='mono'>{A:,.0f} ticks</td></tr>")
    html=f"""<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<meta http-equiv='refresh' content='120'><title>NQ Board — auto</title><style>{CSS}</style></head><body><div class='wrap'>
<div class='head'><div>
<div class='eyebrow'>NQ · auto board · mechanical layers · generated {now.strftime('%a %b %d · %I:%M %p ET')}</div>
<h1>Live System Board</h1>
<div class='note'>data: Yahoo continuous futures (may lag CME by minutes/ticks; TradingView = execution truth) · narrative, grading &amp; scorecard live in the Claude sessions · not advice</div>
</div><div class='stats'>
<div class='stat'><span class='k'>Spot</span><div class='v'>{b(spot)}</div></div>
<div class='stat'><span class='k'>DCV</span><div class='v'>+{up/A:.2f}A / \u2212{dn/A:.2f}A</div></div>
<div class='stat'><span class='k'>Micro EQ</span><div class='v'>{b(mEQ)}</div></div>
<div class='stat'><span class='k'>Bias engine</span><div><span class='pill'>{pill}</span></div></div>
</div></div>
<div class='grid'><div>
<div class='card a'><h2 class='aa'>Session &amp; profile</h2><table>{ses}</table></div>
<div class='card'><h2>DCV 2.0 bands (off {b(O)})</h2><table>{dcv}</table></div>
<div class='card'><h2>Objects &amp; statuses — virgin connectors (50% rule, 1M-verified) + active MIST</h2><table><tr><th>object</th><th>entry / stop / 2R</th><th>tag</th></tr>{''.join(cards[:14])}</table>
<p class='note'>auto-refreshes every 2 min in your browser · engine reruns every ~15 min · {mistN} MIST actives on the jury</p></div>
</div><div><div class='ladder'><h2>Ladder</h2>{lrows}</div></div></div>
</div></body></html>"""
    open('index.html','w').write(html)
    print('index.html written',now)

if __name__=='__main__':
    try: main()
    except Exception:
        traceback.print_exc(); sys.exit(0)
