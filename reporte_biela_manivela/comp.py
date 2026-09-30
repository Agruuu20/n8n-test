import numpy as np, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from biela_manivela_2da_inversion import *
U='/root/.claude/uploads/945eb71c-abac-5e5b-80dc-b2f2ef8868d6/'
V=leer_csv(U+'2b6cc197-Velocidad_lineal1.csv'); A=leer_csv(U+'a91a5623-Aceleraci_n_lineal1.csv')
L1,L3=100.0,132.88; w1=100*2*np.pi/60
R=simular(L1,L3,w1,np.radians(138.0),5,0.04)
t=R['t']; n=len(t)
# consistencia: B via guia (L2,th2) vs B via manivela
th2=R['th2'];L2=R['L2'];L2d=R['L2d'];w2=R['w2'];L2dd=R['L2dd'];a2=R['a2']
vx=L2d*np.cos(th2)-L2*w2*np.sin(th2); vy=L2d*np.sin(th2)+L2*w2*np.cos(th2)
ar=L2dd-L2*w2**2; at=L2*a2+2*L2d*w2
ax=ar*np.cos(th2)-at*np.sin(th2); ay=ar*np.sin(th2)+at*np.cos(th2)
print('consist', abs(vx-R['vBx']).max(),abs(vy-R['vBy']).max(),abs(ax-R['aBx']).max(),abs(ay-R['aBy']).max())
def stats(a,b):
    e=a-b; return dict(maxabs=float(abs(e).max()),rmse=float(np.sqrt((e**2).mean())),pct=float(abs(e).max()/abs(b).max()*100))
S={'vx':stats(R['vBx'],V[:,1]),'vy':stats(R['vBy']/1000,V[:,2]),'ax':stats(R['aBx'],A[:,1]),'ay':stats(R['aBy']/1000,A[:,2])}
print(json.dumps(S,indent=1))
for k,(a,b) in {'vx':(R['vBx'],V[:,1]),'ax':(R['aBx'],A[:,1])}.items():
    print(k, 'first-row analytic', a[:3], b[:3])
plt.rcParams.update({'font.size':9})
def cmp(fn,title,a1,b1,a2,b2,u1,u2):
    fig,ax=plt.subplots(2,1,figsize=(7.5,5.6),sharex=True)
    ax[0].plot(t,b1,'-',color='#1f5fbf',lw=2.2,label='SolidWorks (Vx)');ax[0].plot(t,a1,'--',color='#e8590c',lw=1.4,label='Analítico (Vx)')
    ax[0].set_ylabel(u1);ax[0].legend(loc='upper right',fontsize=8);ax[0].grid(alpha=.3)
    ax[1].plot(t,b2,'-',color='#1f5fbf',lw=2.2,label='SolidWorks (Vy)');ax[1].plot(t,a2,'--',color='#e8590c',lw=1.4,label='Analítico (Vy)')
    ax[1].set_ylabel(u2);ax[1].set_xlabel('t (s)');ax[1].legend(loc='upper right',fontsize=8);ax[1].grid(alpha=.3)
    fig.suptitle(title);fig.tight_layout();fig.savefig(fn,dpi=160);plt.close(fig)
cmp('cmp_vel.png','Velocidad del punto B: SolidWorks vs analítico',R['vBx'],V[:,1],R['vBy']/1000,V[:,2],'mm/s','(reportado por SW)')
cmp('cmp_acc.png','Aceleración del punto B: SolidWorks vs analítico',R['aBx'],A[:,1],R['aBy']/1000,A[:,2],'mm/s²','(reportado por SW)')
# 5 instantes tabla
idx=[0,4,8,12,16]
for i in idx: print(f"{t[i]:.2f} th1={np.degrees(R['th1'][i])%360:.1f} L2={L2[i]:.2f} th2={np.degrees(th2[i])%360:.2f} L2d={L2d[i]:.1f} w2={w2[i]:.3f} L2dd={L2dd[i]:.0f} a2={a2[i]:.1f} | vx {R['vBx'][i]:.1f} {V[i,1]:.1f} ax {R['aBx'][i]:.0f} {A[i,1]:.0f} vy {R['vBy'][i]/1000:.4f} {V[i,2]:.4f}")
json.dump(dict(S=S,t=t.tolist()),open('stats.json','w'))
Rf=simular(L1,L3,w1,np.radians(138.0),5,0.005); graficar(Rf,'resultado')
rows=[]
for i in [0,3,6,9,12]:
    rows.append(dict(t=float(t[i]),th1=float(np.degrees(R['th1'][i])%360),L2=float(L2[i]),th2=float(np.degrees(th2[i])%360),L2d=float(L2d[i]),w2=float(w2[i]),L2dd=float(L2dd[i]),a2=float(a2[i]),
      vx_a=float(R['vBx'][i]),vx_s=float(V[i,1]),ax_a=float(R['aBx'][i]),ax_s=float(A[i,1]),vy_a=float(R['vBy'][i]/1000),vy_s=float(V[i,2]),ay_a=float(R['aBy'][i]/1000),ay_s=float(A[i,2])))
json.dump(dict(S=S,rows=rows),open('data.json','w'),indent=1)
# geometria captura
import math
print('L1',math.hypot(42.44,90.55),'L3',897.13-764.25,'L2',math.hypot(897.13-(764.25-42.44),90.55),'dist3d',math.hypot(math.hypot(42.44,90.55),60))
th=math.atan2(90.55,-42.44);print('th1',math.degrees(th)); Lc=math.hypot(100*math.sin(th),100*math.cos(th)-132.88);print('L2 model',Lc, 'th2', math.degrees(math.atan2(100*math.sin(th),100*math.cos(th)-132.88)))
