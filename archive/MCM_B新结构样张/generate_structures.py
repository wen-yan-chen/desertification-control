"""Second figure collection: original composite layouts, synthetic data, offline rendering."""
from pathlib import Path
import json, math, time, csv, zipfile
import numpy as np
from scipy.stats import gaussian_kde, norm, rankdata
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib import colors
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch, Wedge, PathPatch
from matplotlib.path import Path as PlotPath
from matplotlib.lines import Line2D
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image, ImageDraw, ImageFont
import fitz

ROOT=Path(__file__).resolve().parent
for folder in ["PNG","SVG","research"]:
    (ROOT/folder).mkdir(exist_ok=True)
SEED=202711071
C=dict(ink="#293B52",blue="#607FA7",teal="#7C9E91",apricot="#D09C7B",
       violet="#9C8CB3",rose="#B98091",olive="#A7AD7D",muted="#74808E",grid="#E5E8EC",pale="#F3F5F8")
COL=[C[k] for k in ["blue","teal","apricot","violet","rose","olive"]]
SEQ=colors.LinearSegmentedColormap.from_list("slate_density",
    ["#F4F6F9","#D2DCE9","#9DB2CB","#6787AE","#3C597B","#22384F"])
plt.rcParams.update({
    "font.family":"DejaVu Sans","font.size":10.5,"axes.labelsize":10.5,
    "axes.titlesize":11,"axes.titleweight":"bold","text.color":C["ink"],
    "axes.labelcolor":C["ink"],"axes.edgecolor":"#C7CFD8",
    "xtick.color":C["muted"],"ytick.color":C["muted"],
    "axes.spines.top":False,"axes.spines.right":False,
    "axes.linewidth":.7,"grid.color":C["grid"],"grid.linewidth":.65,
    "legend.frameon":False,"legend.fontsize":9,"lines.linewidth":2,
    "figure.facecolor":"white","axes.facecolor":"white","savefig.facecolor":"white",
    "svg.fonttype":"none","pdf.fonttype":42,"hatch.linewidth":.4,
})
INDEX=[]; CHECK={}; DATA={}; DURATIONS={}
def rng(code):return np.random.default_rng(SEED+code)
def header(code,category,title,subtitle):
    fig=plt.figure(figsize=(11.4,7.4))
    fig.text(.055,.955,f"{code}  /  {category.upper()}",fontsize=10,color=C["blue"],weight="bold")
    fig.text(.055,.903,title,fontsize=22,fontfamily="DejaVu Serif",weight="bold",va="top")
    fig.text(.055,.838,subtitle,fontsize=10.5,color=C["muted"],va="top")
    return fig
def axes(fig,pos):return fig.add_axes(pos)
def tidy(ax,axis="y"):
    ax.grid(axis=axis);ax.set_axisbelow(True)
def label(ax,text):ax.set_title(text,loc="left",pad=12)
def save(fig,code,stem,cn,question,inputs,method,source,difficulty,pdf,started):
    fig.text(.055,.092,"INPUT  "+inputs,fontsize=8.3,color=C["muted"])
    fig.text(.055,.037,"SYNTHETIC DEMO  /  GENERATED VALUES AND SCHEMATIC COORDINATES",
             fontsize=8,color=C["muted"])
    fig.text(.945,.037,"INSPIRATION  "+source,fontsize=8,color=C["muted"],ha="right")
    filename=f"{code}_{stem}"
    fig.savefig(ROOT/"PNG"/f"{filename}.png",dpi=300)
    fig.savefig(ROOT/"SVG"/f"{filename}.svg")
    pdf.savefig(fig,dpi=300)
    plt.close(fig)
    INDEX.append(dict(id=code,title=cn,question=question,inputs=inputs,method=method,
                      source=source,difficulty=difficulty,png=f"PNG/{filename}.png",svg=f"SVG/{filename}.svg"))
    DURATIONS[code]=round(time.perf_counter()-started,3)
    print("Rendered",code,stem,flush=True)
def arrow(ax,a,b,**kw):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=12,
                               linewidth=1.4,color=C["ink"],shrinkA=2,shrinkB=2,**kw))
def cover(pdf):
    fig=plt.figure(figsize=(11.4,7.4))
    fig.text(.06,.91,"MCM / ICM  •  SECOND COLLECTION",fontsize=11,weight="bold",color=C["blue"])
    fig.text(.06,.80,"Structures that explain decisions",fontfamily="DejaVu Serif",fontsize=30,weight="bold")
    fig.text(.06,.72,"12 composite figure studies  /  synthetic data  /  reproducible Python",fontsize=13,color=C["muted"])
    entries=[
      "N01   Allocation simplex and robustness","N02   Probability fields and search evidence",
      "N03   Joint uncertainty with marginals","N04   Distribution ridges and threshold risk",
      "N05   Constraint failure intersections","N06   Preference-driven rank changes",
      "N07   Adaptive policy pathways","N08   Interaction chords and strongest links",
      "N09   State probabilities and uncertainty","N10   Phase portrait and attraction basins",
      "N11   Coalition attribution and ablation","N12   Rainclouds and extreme-loss behavior"]
    for i,text in enumerate(entries):
        x=.06+(i//6)*.48;y=.60-(i%6)*.059
        fig.text(x,y,text,fontsize=11)
    for i,(k,col) in enumerate(zip(["SLATE","SAGE","APRICOT","IRIS","DUSTY ROSE","OLIVE"],COL)):
        x=.06+i*.15
        fig.patches.append(Rectangle((x,.15),.105,.028,transform=fig.transFigure,facecolor=col,edgecolor="none"))
        fig.text(x,.125,k,fontsize=8,color=C["muted"])
    fig.text(.06,.055,"Sources and adaptation requirements are indexed in the accompanying Chinese guide.",
             fontsize=10,color=C["muted"])
    pdf.savefig(fig);plt.close(fig)

def n01(pdf):
    start=time.perf_counter()
    fig=header("N01","allocation geometry","Allocation geometry under uncertainty",
               "A simplex exposes feasible mixes and the cost of protecting the worst scenario.")
    ax=axes(fig,[.075,.23,.57,.51]);side=axes(fig,[.72,.49,.23,.23]);low=axes(fig,[.72,.22,.23,.16])
    n=60
    shares=np.array([(i/n,j/n,1-(i+j)/n) for i in range(n+1) for j in range(n+1-i)])
    a,b,c=shares.T
    x=b+.5*c;y=np.sqrt(3)/2*c
    nominal=1.25*np.sqrt(a)+.90*np.sqrt(b)+.65*np.sqrt(c)
    scenario=np.stack([nominal,.65*np.sqrt(a)+1.05*np.sqrt(b)+1.05*np.sqrt(c),
                       .95*np.sqrt(a)+.65*np.sqrt(b)+1.12*np.sqrt(c)])
    worst=scenario.min(axis=0)
    feasible=(a>=.1-1e-9)&(b<=.6+1e-9)&(c<=.6+1e-9)
    tri=mtri.Triangulation(x,y);tri.set_mask(~feasible[tri.triangles].all(axis=1))
    ax.add_patch(Polygon([[0,0],[1,0],[.5,np.sqrt(3)/2]],facecolor="#F0F1F4",edgecolor="none"))
    contour=ax.tricontourf(tri,worst,levels=15,cmap=SEQ)
    for q in [.2,.4,.6,.8]:
        ax.plot([q, .5+.5*q],[0,(1-q)*np.sqrt(3)/2],color="white",alpha=.36,lw=.7)
        ax.plot([1-q,.5*(1-q)],[0,(1-q)*np.sqrt(3)/2],color="white",alpha=.36,lw=.7)
        ax.plot([q/2,1-q/2],[q*np.sqrt(3)/2]*2,color="white",alpha=.36,lw=.7)
    ax.plot([0,1,.5,0],[0,0,np.sqrt(3)/2,0],color="#AAB4C2",lw=.8)
    label(ax,"(a) Feasible mixes")
    i0=np.where(feasible,nominal,-np.inf).argmax();ir=np.where(feasible,worst,-np.inf).argmax()
    ax.scatter([x[i0]],[y[i0]],s=100,facecolor="white",edgecolor=C["apricot"],lw=2,zorder=4,marker="o")
    ax.scatter([x[ir]],[y[ir]],s=210,color=C["rose"],edgecolor="white",lw=.9,zorder=5,marker="*")
    arrow(ax,(x[i0],y[i0]),(x[ir],y[ir]))
    ax.annotate("Nominal",(x[i0],y[i0]),xytext=(-40,-20),textcoords="offset points",fontsize=9,color=C["ink"],bbox=dict(fc="white",ec="none",alpha=.85,pad=2))
    ax.annotate("Robust",(x[ir],y[ir]),xytext=(12,16),textcoords="offset points",fontsize=9,color=C["rose"],bbox=dict(fc="white",ec="none",alpha=.85,pad=2))
    for vx,vy,t in [(-.035,-.04,"A  •  100%"),(1.035,-.04,"B  •  100%"),(.5,.92,"C  •  100%")]:
        ax.text(vx,vy,t,ha="center",fontsize=10,weight="bold")
    ax.set(xlim=(-.1,1.1),ylim=(-.08,1),aspect="equal");ax.axis("off")
    cbax=axes(fig,[.17,.18,.40,.018]);cb=fig.colorbar(contour,cax=cbax,orientation="horizontal")
    cb.set_label("Worst-scenario utility",fontsize=9);cb.ax.tick_params(labelsize=8)
    label(side,"(b) Allocation shares")
    left=np.zeros(2)
    for j,co in enumerate(COL[:3]):
        side.barh([1,0],shares[[i0,ir],j],left=left,color=co,height=.43,label=chr(65+j))
        left+=shares[[i0,ir],j]
    side.set(yticks=[1,0],yticklabels=["Nominal","Robust"],xlim=(0,1))
    side.set_xticks([0,.5,1],["0%","50%","100%"]);side.legend(ncol=3,loc="upper right",bbox_to_anchor=(1,1.35))
    label(low,"(c) Scenario performance")
    fig.text(.72,.425,"Open = nominal     Filled = worst case",fontsize=8.5,color=C["muted"])
    for j,(idx,co) in enumerate([(i0,C["apricot"]),(ir,C["rose"])]):
        low.hlines(j,worst[idx],nominal[idx],color=co,lw=3)
        low.scatter([nominal[idx]],[j],facecolor="white",edgecolor=co,s=60)
        low.scatter([worst[idx]],[j],color=co,s=45)
    low.set(yticks=[0,1],yticklabels=["Nominal","Robust"],xlabel="Utility")
    tidy(low,"x")
    CHECK["N01_shares_sum_to_one"]=bool(np.allclose(shares.sum(axis=1),1))
    CHECK["N01_robust_improves_worst"]=bool(worst[ir]>=worst[i0])
    DATA["N01_shares"]=shares;DATA["N01_scenario_utility"]=scenario
    save(fig,"N01","allocation_simplex","三元配比与鲁棒选择","三类投入如何分配，稳健性要付出多少代价？",
         "Three shares summing to 1 + scenario utilities + explicit constraints",
         "单纯形三角网格、显式可行约束、逐点最坏情景比较","T1 + own synthesis","中",pdf,start)

def n02(pdf):
    start=time.perf_counter()
    fig=header("N02","search evidence","Probability fields guide sequential search",
               "Negative evidence changes the distribution; coverage and uncertainty are read together.")
    r=rng(2);v=np.linspace(0,1,85);X,Y=np.meshgrid(v,v)
    prior=.62*np.exp(-((X-.32)**2/.035+(Y-.53)**2/.026))+.38*np.exp(-((X-.73)**2/.045+(Y-.35)**2/.04))
    prior/=prior.sum();p=prior.copy();post=[p.copy()];cover=[0.];likelihoods=[]
    zones=[(.12,.47,.31,.72),(.48,.84,.19,.48)]
    notfound=np.ones_like(p)
    for x0,x1,y0,y1 in zones:
        likelihood=np.where((X>=x0)&(X<=x1)&(Y>=y0)&(Y<=y1),.20,1.)
        likelihoods.append(likelihood);notfound*=likelihood
        p=p*likelihood;p/=p.sum();post.append(p.copy());cover.append(1-np.sum(prior*notfound))
    vmax=max(x.max() for x in post)*1e4
    for i,p in enumerate(post):
        ax=axes(fig,[.075+i*.29,.405,.245,.35])
        im=ax.imshow(p*1e4,origin="lower",extent=(0,1,0,1),cmap=SEQ,vmin=0,vmax=vmax,aspect="equal")
        ax.set(xticks=[0,.5,1],yticks=[0,.5,1]);label(ax,["(a) Prior","(b) After search 1","(c) After search 2"][i])
        for j,(x0,x1,y0,y1) in enumerate(zones[:i]):
            ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec=C["apricot"],ls="--",lw=1.5))
        if i==2:
            path=np.array([[.50,.50],[.74,.50],[.74,.56],[.50,.56],[.50,.62],[.74,.62]])
            ax.plot(*path.T,color=C["rose"],lw=2)
            ax.scatter(*path[0],s=35,color=C["rose"],edgecolor="white",zorder=4)
        # The shared note below the maps defines normalized coordinates.
        if i==0:ax.set_ylabel("Normalized y")
        else:ax.tick_params(labelleft=False)
    cbax=axes(fig,[.925,.435,.012,.27]);cb=fig.colorbar(im,cax=cbax);cb.set_label(r"Probability / cell  $\times 10^{-4}$",fontsize=9)
    fig.text(.10,.355,"Normalized coordinates. Dashed boxes = completed searches; solid path = next candidate.",fontsize=8.5,color=C["muted"])
    a=axes(fig,[.09,.19,.36,.13]);b=axes(fig,[.57,.19,.33,.13])
    entropy=np.array([-np.sum(p*np.log(np.maximum(p,1e-15))) for p in post])
    a.plot(range(3),cover,"o-",color=C["rose"]);a.set(xticks=range(3),xlabel="Completed search stages",ylabel="Detection probability",ylim=(0,1))
    b.plot(range(3),entropy,"o-",color=C["blue"]);b.set(xticks=range(3),xlabel="Completed search stages",ylabel="Entropy (nats)")
    tidy(a);tidy(b)
    CHECK["N02_posteriors_normalized"]=bool(all(np.isclose(x.sum(),1) for x in post))
    CHECK["N02_detection_monotonic"]=bool(np.all(np.diff(cover)>=0))
    DATA["N02_probability_fields"]=np.array(post);DATA["N02_cumulative_detection"]=np.array(cover)
    save(fig,"N02","probability_search","概率场、搜索路径与证据更新","新搜索证据出现后，下一步去哪里？",
         "Spatial prior + sensor likelihood + search footprints",
         "贝叶斯负证据更新、归一化后验、累计发现概率；路线为可执行示意，未优化",
         "P1 + P2","中",pdf,start)

def n03(pdf):
    start=time.perf_counter()
    fig=header("N03","joint uncertainty","Joint uncertainty and the operating window",
               "Marginals summarize each output; the center shows how the two outputs fail together.")
    r=rng(3);x=r.beta(2.8,2.3,7000);y=np.clip(.18+.66*x+.10*np.sin(5*x)+r.normal(0,.085,len(x)),.02,.98)
    good=(x>=.45)&(y<=.65)
    ax=axes(fig,[.10,.21,.60,.46]);top=axes(fig,[.10,.70,.60,.09],);right=axes(fig,[.73,.21,.13,.46])
    im=ax.hexbin(x,y,gridsize=35,mincnt=1,cmap=SEQ,bins="log",extent=(0,1,0,1),linewidths=.2,rasterized=True)
    ax.axhline(.65,color=C["rose"],ls="--",lw=1.5);ax.axvline(.45,color=C["rose"],ls="--",lw=1.5)
    ax.add_patch(Rectangle((.45,0),.55,.65,fc=C["teal"],alpha=.055,ec="none"))
    ax.text(.04,.94,f"{good.mean():.1%} within both limits",transform=ax.transAxes,fontsize=11,weight="bold",va="top")
    ax.set(xlim=(0,1),ylim=(0,1),xlabel="Benefit index",ylabel="System load")
    top.hist(x,bins=35,color=C["blue"],alpha=.55,density=True);top.set(xlim=(0,1));top.axis("off")
    right.hist(y,bins=35,orientation="horizontal",color=C["apricot"],alpha=.6,density=True)
    right.set(ylim=(0,1));right.axis("off")
    cax=axes(fig,[.90,.24,.014,.39]);cb=fig.colorbar(im,cax=cax);cb.set_label("Sample count / hexagon",fontsize=9)
    DATA["N03_joint_samples"]=np.column_stack([x,y])
    CHECK["N03_hexbin_sample_count"]=len(x)
    save(fig,"N03","joint_uncertainty","带边缘分布的联合不确定性图","两个指标的联合达标范围在哪里？",
         "Paired Monte Carlo outputs + two operational thresholds",
         "六边形分箱、边缘密度和联合达标标记","T5 + own synthesis","低",pdf,start)

def n04(pdf):
    start=time.perf_counter()
    fig=header("N04","evolving distributions","Distributions approaching a critical threshold",
               "Ridgelines show shape; the aligned right panel quantifies exceedance risk.")
    r=rng(4)
    samples=np.array([np.clip(r.normal(.30+.055*k,.042+.007*k,1000),0,1) for k in range(8)])
    xx=np.linspace(0,1,240);dens=np.array([gaussian_kde(d)(xx) for d in samples])
    ax=axes(fig,[.10,.20,.59,.55]);risk=axes(fig,[.78,.20,.16,.55]);med=[]
    scale=.58/dens.max()
    for k in range(7,-1,-1):
        base=7-k;yy=base+dens[k]*scale
        ax.fill_between(xx,base,yy,color=SEQ(.30+.065*k),alpha=.86,zorder=10-k)
        ax.fill_between(xx,base,yy,where=xx>=.65,color=C["apricot"],alpha=.9,zorder=10-k)
        ax.plot(xx,yy,color="white",lw=.8,zorder=11-k)
        m=np.median(samples[k]);med.append((m,base))
        ax.scatter(m,base+.04,color=C["ink"],s=16,zorder=20)
    ax.axvline(.65,color=C["rose"],ls="--",lw=1.4,zorder=21)
    ax.text(.665,7.8,"Threshold",color=C["rose"],fontsize=9)
    ax.set(xlim=(0,1),ylim=(-.35,8.1),yticks=np.arange(8),yticklabels=[f"T+{k}" for k in range(7,-1,-1)],
           xlabel="Load index",ylabel="Forecast slice")
    prob=(samples>.65).mean(axis=1)
    risk.hlines(np.arange(8),0,prob[::-1],color="#D6DEE5",lw=3)
    risk.scatter(prob[::-1],np.arange(8),s=42,color=C["rose"],zorder=3)
    for j,v in enumerate(prob[::-1]):risk.text(v+.04,j,f"{v:.0%}",va="center",fontsize=9)
    risk.set(ylim=ax.get_ylim(),xlim=(-.05,1.15),yticks=[],xticks=[0,.5,1],xlabel="P(load > 0.65)")
    label(risk,"Exceedance")
    for sp in ["left","right","top"]:risk.spines[sp].set_visible(False)
    DATA["N04_slice_samples"]=samples
    save(fig,"N04","distribution_ridges","分布山脊与超阈风险图","风险在何时集中，尾部如何变化？",
         "Repeated output samples at each time slice + one threshold",
         "同一密度缩放的山脊图、样本中位数及超阈比例","own synthesis + P3","低",pdf,start)

def n05(pdf):
    start=time.perf_counter()
    fig=header("N05","failure fingerprints","Constraint failures that occur together",
               "Exact intersections partition every stress case once; totals include overlapping failures.")
    r=rng(5);latent=r.normal(size=(900,3))
    failed=np.column_stack([latent[:,0]+.25*latent[:,1]>.35,
                           .45*latent[:,0]+latent[:,1]>.65,
                           -.4*latent[:,0]+latent[:,2]>.80,
                           latent[:,1]+.6*latent[:,2]>.65])
    codes=(failed*(2**np.arange(4))).sum(axis=1)
    counts=np.bincount(codes,minlength=16)
    order=np.r_[0,np.argsort(counts[1:])[::-1]+1]
    matrix=((order[:,None]>>np.arange(4))&1).astype(bool)
    top=axes(fig,[.37,.48,.57,.27]);dot=axes(fig,[.37,.20,.57,.22]);left=axes(fig,[.15,.20,.16,.22])
    top.bar(range(16),counts[order],color=[C["teal"]]+[C["blue"]]*15,width=.7)
    for j,v in enumerate(counts[order]):top.text(j,v+5,str(v),ha="center",fontsize=8)
    top.set(xlim=(-.6,15.6),xticks=[],ylabel="Exact pattern count",ylim=(0,max(counts)*1.20))
    tidy(top)
    for j,row in enumerate(matrix):
        dot.scatter(np.full(4,j),np.arange(4),s=32,color="#E0E5EA")
        active=np.flatnonzero(row)
        if len(active):
            dot.plot([j,j],[active.min(),active.max()],color=C["ink"],lw=1.3)
            dot.scatter(np.full(len(active),j),active,s=38,color=C["ink"])
    dot.set(xlim=top.get_xlim(),ylim=(3.6,-.6),yticks=[],xticks=[0],xticklabels=["Pass"])
    dot.set_xlabel("Connected dots identify the constraints in each exact pattern",labelpad=12)
    for sp in dot.spines.values():sp.set_visible(False)
    totals=failed.sum(axis=0)
    left.barh(np.arange(4),totals,color=COL[:4],height=.5)
    for j,v in enumerate(totals):left.text(v+8,j,str(v),fontsize=9,va="center")
    left.set(yticks=np.arange(4),yticklabels=["Budget","Capacity","Ecology","Peak load"],
             ylim=(3.6,-.6),xlim=(0,totals.max()*1.3),xticks=[])
    label(left,"Failure totals")
    left.spines["bottom"].set_visible(False)
    CHECK["N05_pattern_counts_partition_all_cases"]=bool(counts.sum()==len(failed))
    DATA["N05_failure_flags"]=failed;DATA["N05_exact_counts"]=counts
    save(fig,"N05","constraint_upset","约束失效交集 UpSet 图","预算超支和容量超限是否经常一起发生？",
         "One Boolean failure flag per constraint and per stress case",
         "互斥失效组合计数与重叠集合总数对齐","T2","低",pdf,start)

def n06(pdf):
    start=time.perf_counter()
    fig=header("N06","preference transitions","Policy rankings under changing priorities",
               "Lines connect eleven sampled weight settings; integer ranks are evaluated at the markers.")
    ax=axes(fig,[.10,.22,.80,.51])
    metrics=np.array([[.98,.38,.35],[.81,.68,.48],[.56,.91,.62],[.38,.63,.98],[.73,.74,.74],[.64,.82,.78]])
    w=np.linspace(0,1,11);weights=np.column_stack([w,.65*(1-w),.35*(1-w)])
    scores=metrics@weights.T;ranks=np.array([rankdata(-scores[:,j],method="ordinal") for j in range(11)]).T
    ax.axvspan(.30,.60,color=C["blue"],alpha=.045)
    for i,row in enumerate(ranks):
        ax.plot(w,row,color=COL[i],lw=3,alpha=.92,marker="o",ms=5,markeredgecolor="white",markeredgewidth=.7)
        
        ax.text(1.035,row[-1],f"Policy {chr(65+i)}",va="center",color=COL[i],weight="bold")
    ax.set(xlim=(-.02,1.20),ylim=(6.5,.5),yticks=range(1,7),xticks=w,xlabel="Weight on economic performance",
           ylabel="Rank  /  1 is best")
    ax.text(.45,.72,"Mixed priorities",ha="center",color=C["muted"],fontsize=9)
    tidy(ax)
    CHECK["N06_each_column_has_unique_ranks"]=bool(all(np.array_equal(np.sort(ranks[:,j]),np.arange(1,7)) for j in range(11)))
    DATA["N06_metrics"]=metrics;DATA["N06_weights"]=weights;DATA["N06_ranks"]=ranks
    save(fig,"N06","ranking_braid","偏好变化的排名编织图","偏好改变后，推荐方案会不会换位？",
         "Policy-by-objective scores + sampled preference vectors",
         "加权评分与离散排名；连线仅连接已算权重设置","own synthesis + P3","低",pdf,start)

def n07(pdf):
    start=time.perf_counter()
    fig=header("N07","adaptive pathways","Adaptive actions as stress increases",
               "Availability windows, switching opportunities and one illustrative pathway share the same axis.")
    ax=axes(fig,[.27,.25,.63,.47])
    begins=np.array([0,.18,.42,.64]);ends=np.array([.36,.66,.88,1.])
    names=["Maintain current policy","Add targeted capacity","Expand the intervention","Redesign the system"]
    for i,(a,b,name,co) in enumerate(zip(begins,ends,names,COL[:4])):
        y=3-i
        ax.plot([0,1],[y,y],color="#EEF0F4",lw=7,solid_capstyle="round")
        ax.plot([a,b],[y,y],color=co,lw=7,solid_capstyle="round")
        ax.scatter([a,b],[y,y],s=60,facecolor="white",edgecolor=co,lw=1.5,zorder=4)
        ax.text(1.025,y,f"limit {b:.2f}",fontsize=9,va="center",color=co)
    switches=[.29,.55,.77]
    px=[0,.29,.29,.55,.55,.77,.77,1];py=[3,3,2,2,1,1,0,0]
    ax.plot(px,py,color=C["ink"],lw=1.7,ls="--",zorder=5)
    for i,x in enumerate(switches):
        ax.scatter(x,3-i,s=100,marker="D",facecolor="white",edgecolor=C["ink"],lw=1.3,zorder=6)
        arrow(ax,(x,3-i-.1),(x,2-i+.12))
        ax.text(x+.018,2.5-i,f"switch\n{x:.2f}",fontsize=8.5,color=C["ink"],va="center")
    ax.set(xlim=(-.015,1.13),ylim=(-.45,3.5),yticks=[3,2,1,0],yticklabels=names,
           xlabel="External stress index")
    ax.tick_params(axis="y",length=0,pad=12);ax.spines["left"].set_visible(False)
    ax.set_xticks(np.linspace(0,1,6));tidy(ax,"x")
    fig.text(.16,.17,"Colored segment = viable range     Diamond = decision trigger     Dashed line = illustrative sequence",
             fontsize=9,color=C["muted"])
    CHECK["N07_switches_within_both_availability_windows"]=bool(all(
        max(begins[i],begins[i+1])<=x<=min(ends[i],ends[i+1]) for i,x in enumerate(switches)))
    DATA["N07_availability"]=np.column_stack([begins,ends]);DATA["N07_switches"]=np.array(switches)
    save(fig,"N07","adaptation_pathways","适应路径地铁图","条件恶化时，何时升级、从哪条路径切换？",
         "Action viability intervals + candidate switching thresholds",
         "可行区间与转换触发点同轴；示意路径不宣称优化最优","own synthesis","中",pdf,start)

def n08(pdf):
    start=time.perf_counter()
    fig=header("N08","interaction structure","Exchanges between groups",
               "Ribbon and sector widths encode the same symmetric interaction matrix.")
    ax=axes(fig,[.06,.19,.57,.57]);rank=axes(fig,[.73,.29,.20,.36])
    matrix=np.array([[0,16,7,4,12,3],[16,0,11,7,4,10],[7,11,0,20,8,5],
                     [4,7,20,0,10,8],[12,4,8,10,0,17],[3,10,5,8,17,0]],float)
    strength=matrix.sum(axis=1);gap=.065
    totalangle=2*np.pi-6*gap;unit=totalangle/strength.sum();starts=[];cursor=.35
    segments={}
    def xy(t,r=1):return np.array([r*np.cos(t),r*np.sin(t)])
    for i,s in enumerate(strength):
        a=cursor;b=a+s*unit;starts.append((a,b));cursor=b+gap
        ax.add_patch(Wedge((0,0),1.045,np.degrees(a),np.degrees(b),width=.075,facecolor=COL[i],edgecolor="white",lw=1))
        cur=a
        for j,v in enumerate(matrix[i]):
            if v:
                segments[i,j]=(cur,cur+v*unit);cur+=v*unit
        mid=(a+b)/2
        ax.text(*xy(mid,1.19),f"{chr(65+i)}\n{s:.0f}",ha="center",va="center",fontsize=10,weight="bold",color=COL[i])
    for i in range(6):
        for j in range(i+1,6):
            a0,a1=segments[i,j];b0,b1=segments[j,i]
            arc1=np.array([xy(t,.97) for t in np.linspace(a0,a1,16)])
            arc2=np.array([xy(t,.97) for t in np.linspace(b0,b1,16)])
            p=arc1[-1];q=arc2[0];p2=arc2[-1];q2=arc1[0]
            verts=list(arc1)+[p*.20,q*.20,q]+list(arc2[1:])+[p2*.20,q2*.20,q2]
            codes=[PlotPath.MOVETO]+[PlotPath.LINETO]*15+[PlotPath.CURVE4]*3+[PlotPath.LINETO]*15+[PlotPath.CURVE4]*3
            ax.add_patch(PathPatch(PlotPath(np.array(verts),codes),fc=COL[i],alpha=.36,ec="white",lw=.45))
    ax.set(xlim=(-1.42,1.42),ylim=(-1.38,1.38),aspect="equal");ax.axis("off")
    pairs=sorted([(matrix[i,j],f"{chr(65+i)} - {chr(65+j)}",COL[i]) for i in range(6) for j in range(i+1,6)],reverse=True)[:6]
    rank.barh(np.arange(6),[x[0] for x in pairs],color=[x[2] for x in pairs],height=.5)
    for k,(v,_,_) in enumerate(pairs):rank.text(v+.5,k,f"{v:.0f}",va="center",fontsize=10)
    rank.set(yticks=np.arange(6),yticklabels=[x[1] for x in pairs],xlabel="Interaction units",xlim=(0,25))
    rank.invert_yaxis();label(rank,"Strongest exchanges");tidy(rank,"x")
    fig.text(.73,.75,f"{matrix.sum()/2:.0f} total pair units",fontsize=14,fontfamily="DejaVu Serif",weight="bold")
    fig.text(.73,.16,"Undirected relationships\nNode totals count incident flows",fontsize=9,color=C["muted"],linespacing=1.5)
    CHECK["N08_symmetric_matrix"]=bool(np.allclose(matrix,matrix.T))
    CHECK["N08_sector_widths_conserve_strength"]=bool(np.isclose(sum(b-a for a,b in starts),totalangle))
    DATA["N08_interaction_matrix"]=matrix
    save(fig,"N08","interaction_chords","守恒弦图与主联系排序","哪些群体之间联系最强，强度如何分布？",
         "Small symmetric nonnegative interaction matrix",
         "节点弧长与弦端宽度按矩阵强度分配；表达无向交换","T3","中",pdf,start)

def n09(pdf):
    start=time.perf_counter()
    fig=header("N09","latent states","State changes under noisy observations",
               "One shared timeline links observations, filtered state probabilities and posterior entropy.")
    r=rng(9);N=180;T=np.array([[.93,.06,.01],[.05,.90,.05],[.02,.08,.90]])
    means=np.array([-.6,0,.65]);state=np.zeros(N,dtype=int)
    for i in range(1,N):state[i]=r.choice(3,p=T[state[i-1]])
    obs=means[state]+r.normal(0,.28,N);posterior=[];p=np.ones(3)/3
    for value in obs:
        pred=p@T;prob=pred*norm.pdf(value,loc=means,scale=.28);p=prob/prob.sum();posterior.append(p)
    posterior=np.array(posterior);entropy=-np.sum(posterior*np.log(np.maximum(posterior,1e-15)),axis=1)
    tt=np.arange(N)
    top=axes(fig,[.10,.59,.83,.16]);mid=axes(fig,[.10,.36,.83,.18]);low=axes(fig,[.10,.18,.83,.12])
    top.stackplot(tt,posterior.T,colors=[C["blue"],C["apricot"],C["teal"]],alpha=.8,labels=["State A","State B","State C"])
    top.set(ylim=(0,1),ylabel="State probability",xticks=[]);top.legend(loc="upper center",bbox_to_anchor=(.5,1.28),ncol=3)
    mid.scatter(tt,obs,s=8,color="#B9C2CD",alpha=.7,label="Generated observation")
    mid.plot(tt,posterior@means,color=C["ink"],lw=1.7,label="Filtered expectation")
    mid.set(ylabel="Signal",xticks=[]);mid.legend(loc="upper right",ncol=2);tidy(mid)
    low.fill_between(tt,0,entropy,color=C["violet"],alpha=.25)
    low.plot(tt,entropy,color=C["violet"],lw=1.5)
    low.set(ylabel="Entropy",xlabel="Time step",ylim=(0,1.15),xlim=(0,N-1));tidy(low)
    for a in [top,mid]:a.set_xlim(0,N-1)
    CHECK["N09_state_posteriors_normalized"]=bool(np.allclose(posterior.sum(axis=1),1))
    CHECK["N09_entropy_bounds"]=bool(np.all((entropy>=0)&(entropy<=np.log(3)+1e-12)))
    DATA["N09_observations"]=obs;DATA["N09_posterior"]=posterior;DATA["N09_transition"]=T
    save(fig,"N09","state_probability_ribbon","潜在状态色带与不确定性联动图","系统是在换状态，还是观测本身波动？",
         "Ordered observations + state model + transition and observation probabilities",
         "三状态高斯观测 HMM 前向过滤；概率与熵来自同一后验","P3 + own synthesis","中",pdf,start)

def n10(pdf):
    start=time.perf_counter()
    fig=header("N10","nonlinear dynamics","Initial conditions and long-run equilibria",
               "Attraction basins, nullclines and time trajectories explain the same two-state ODE.")
    a=1.35
    def ode(t,z):
        x,y=z;return [x*(1-x-a*y),.8*y*(1-y-a*x)]
    v=np.linspace(.008,1.04,65);X,Y=np.meshgrid(v,v);xx=X.copy();yy=Y.copy()
    for _ in range(1400):
        dx=xx*(1-xx-a*yy);dy=.8*yy*(1-yy-a*xx)
        xx+=.035*dx;yy+=.035*dy
    basin=(xx>yy).astype(int)
    ax=axes(fig,[.085,.24,.50,.49]);side=axes(fig,[.70,.32,.24,.37])
    ax.contourf(X,Y,basin,levels=[-.5,.5,1.5],colors=[C["apricot"],C["blue"]],alpha=.14)
    vv=np.linspace(0,1.04,22);U,V=np.meshgrid(vv,vv)
    dx=U*(1-U-a*V);dy=.8*V*(1-V-a*U)
    ax.streamplot(vv,vv,dx,dy,color="#A5B2C2",density=.7,linewidth=.65,arrowsize=.8)
    q=np.linspace(0,1,120)
    ax.plot(q,(1-q)/a,ls="--",color=C["blue"],lw=1.3,label="dx/dt = 0")
    ax.plot(q,1-a*q,ls="--",color=C["apricot"],lw=1.3,label="dy/dt = 0")
    starts=[(.76,.20),(.20,.76),(.56,.52)]
    for i,initial in enumerate(starts):
        sol=solve_ivp(ode,(0,22),initial,t_eval=np.linspace(0,22,350),rtol=1e-8,atol=1e-10)
        ax.plot(*sol.y,color=COL[i],lw=2)
        ax.scatter(*initial,s=55,color=COL[i],ec="white",lw=.8,zorder=4)
        side.plot(sol.t,sol.y[0],color=COL[i],lw=2,label=f"Start {i+1}")
        side.plot(sol.t,sol.y[1],color=COL[i],lw=1.3,ls="--")
    eq=1/(1+a)
    ax.scatter([1,0],[0,1],s=75,color=C["ink"],edgecolor="white",zorder=5)
    ax.scatter([eq],[eq],s=80,facecolor="white",edgecolor=C["rose"],lw=1.7,marker="D",zorder=6)
    ax.set(xlim=(-.03,1.07),ylim=(-.03,1.07),xlabel="State x",ylabel="State y")
    ax.legend(loc="upper right",fontsize=8.5)
    side.set(xlabel="Time",ylabel="State value",ylim=(-.03,1.05));tidy(side);label(side,"Trajectories")
    side.legend(loc="upper center",bbox_to_anchor=(.5,1.28),ncol=3,fontsize=8,columnspacing=.8,handlelength=1.4)
    fig.text(.70,.19,"Solid = x    Dashed = y\nFilled point = stable equilibrium\nOpen diamond = saddle",fontsize=9,color=C["muted"],linespacing=1.6)
    CHECK["N10_integrated_states_nonnegative"]=bool(np.all(xx>=0)&np.all(yy>=0))
    DATA["N10_basin"]=basin;DATA["N10_initial_grid_x"]=X;DATA["N10_initial_grid_y"]=Y
    save(fig,"N10","phase_portrait","吸引域、零增长线与动态轨迹相图","相同政策为何可能导向不同长期状态？",
         "Two-state differential equations + initial states + integration horizon",
         "竞争系统显式 ODE、数值吸引域、零增长线与轨迹；接近分界时需增加积分时长",
         "P4 + own synthesis","中",pdf,start)

def n11(pdf):
    start=time.perf_counter()
    fig=header("N11","mechanism attribution","Attribution and lever interactions",
               "Coalition attribution shares interaction terms; leave-one-out effects retain the active context.")
    def value(z):
        return .4+.18*z[0]+.14*z[1]+.12*z[2]-.10*z[3]+.08*z[4]+.16*z[0]*z[2]-.12*z[1]*z[3]+.06*z[2]*z[4]
    p=5
    vals=np.array([value(np.array([(mask>>j)&1 for j in range(p)])) for mask in range(2**p)])
    phi=np.zeros(p)
    for j in range(p):
        for mask in range(2**p):
            if not (mask>>j)&1:
                k=mask.bit_count();weight=math.factorial(k)*math.factorial(p-k-1)/math.factorial(p)
                phi[j]+=weight*(vals[mask|1<<j]-vals[mask])
    drop=np.array([vals[-1]-vals[(2**p-1)^(1<<j)] for j in range(p)])
    ax=axes(fig,[.085,.25,.54,.47]);side=axes(fig,[.73,.27,.22,.42])
    base=vals[0];ax.bar(0,base,width=.62,color="#C3CBD5")
    previous=base
    for j,v in enumerate(phi,1):
        ax.bar(j,abs(v),bottom=min(previous,previous+v),width=.62,color=C["blue"] if v>=0 else C["rose"])
        ax.plot([j-1+.31,j-.31],[previous,previous],color="#A3ADBA",lw=.9,ls=":")
        ax.text(j,max(previous,previous+v)+.025,f"{v:+.2f}",ha="center",fontsize=9)
        previous+=v
    ax.bar(6,vals[-1],width=.62,color=C["teal"])
    ax.text(0,base+.025,f"{base:.2f}",ha="center",fontsize=10)
    ax.text(6,vals[-1]+.025,f"{vals[-1]:.2f}",ha="center",fontsize=10)
    ax.set(xticks=range(7),xticklabels=["Base","Capacity","Protection","Transit","Fee","Outreach","Total"],
           ylabel="Model response",ylim=(0,1.23))
    ax.tick_params(axis="x",rotation=25,labelsize=8.5);tidy(ax);label(ax,"(a) Exact coalition attribution")
    y=np.arange(p)
    side.hlines(y,phi,drop,color="#CAD3DE",lw=2.5)
    side.scatter(phi,y,s=42,color=C["blue"],label="Shapley")
    side.scatter(drop,y,s=42,facecolor="white",edgecolor=C["rose"],lw=1.5,label="Leave one out")
    side.axvline(0,color="#A9B2BF",lw=.8)
    side.set(yticks=y,yticklabels=["Capacity","Protection","Transit","Fee","Outreach"],xlabel="Attributed / removed effect",xlim=(-.23,.4))
    side.invert_yaxis();label(side,"(b) Interaction check");tidy(side,"x")
    side.legend(loc="upper center",bbox_to_anchor=(.5,-.18),ncol=2,fontsize=8)
    CHECK["N11_shapley_efficiency"]=bool(np.isclose(phi.sum(),vals[-1]-vals[0]))
    DATA["N11_coalition_values"]=vals;DATA["N11_shapley"]=phi;DATA["N11_ablation"]=drop
    save(fig,"N11","attribution_waterfall","精确归因瀑布与消融对照","收益来自哪个措施，交互项有多重要？",
         "Model outputs for all 32 coalitions of five binary levers",
         "精确 Shapley 组合归因与逐项消融，解释该数学模型而非实证因果识别",
         "P3 + own synthesis","中",pdf,start)

def n12(pdf):
    start=time.perf_counter()
    fig=header("N12","tail risk","Average performance and extreme-loss risk",
               "Rainclouds retain individual samples; survival curves expose the high-loss tail.")
    r=rng(12);n=1100
    samples=np.array([
        np.maximum(0,r.normal(.31,.048,n)+(r.random(n)<.055)*r.uniform(.35,.62,n)),
        np.maximum(0,r.normal(.355,.045,n)),
        np.maximum(0,r.normal(.285,.045,n)+(r.random(n)<.12)*r.uniform(.23,.40,n))])
    xx=np.linspace(0,1.05,320);density=np.array([gaussian_kde(d)(xx) for d in samples]);scale=.55/density.max()
    top=axes(fig,[.10,.47,.55,.27]);bottom=axes(fig,[.10,.18,.55,.20]);table=axes(fig,[.73,.30,.22,.35])
    q90=np.quantile(samples,.9,axis=1);cvar=np.array([d[d>=q].mean() for d,q in zip(samples,q90)])
    for i,(d,co) in enumerate(zip(samples,COL[:3])):
        y=2-i
        top.fill_between(xx,y,y+density[i]*scale,color=co,alpha=.45)
        top.plot(xx,y+density[i]*scale,color=co,lw=1.4)
        subset=d[::12]
        top.scatter(subset,y-r.uniform(.08,.20,len(subset)),s=9,color=co,alpha=.45)
        top.scatter(d.mean(),y+.03,color=C["ink"],s=28,zorder=3)
        top.scatter(cvar[i],y+.03,color=C["rose"],s=65,marker="*",zorder=4)
        ds=np.sort(d);survival=(n-np.arange(1,n+1))/n
        bottom.step(ds,survival,where="post",color=co,lw=1.8,label=f"Policy {chr(65+i)}")
    top.set(yticks=[2,1,0],yticklabels=["Policy A","Policy B","Policy C"],xlim=(0,1.05),ylim=(-.30,2.7))
    top.tick_params(axis="x",labelbottom=False)
    top.axvline(.65,color=C["rose"],ls="--",lw=1.2)
    bottom.axvline(.65,color=C["rose"],ls="--",lw=1.2)
    bottom.set_yscale("log");bottom.set(xlim=(0,1.05),ylim=(.001,1),xlabel="Loss index",ylabel="P(loss > x)")
    bottom.legend(loc="upper right");tidy(bottom)
    table.axis("off")
    table.text(0,1.08,"Tail statistics",fontsize=12,weight="bold")
    table.text(0,.9,"Policy",fontsize=9);table.text(.4,.9,"Mean",fontsize=9);table.text(.78,.9,"CVaR90",fontsize=9)
    for i in range(3):
        y=.72-i*.22
        table.text(0,y,chr(65+i),color=COL[i],weight="bold",fontsize=12)
        table.text(.4,y,f"{samples[i].mean():.3f}",fontsize=10)
        table.text(.78,y,f"{cvar[i]:.3f}",fontsize=10)
    fig.text(.73,.21,"Dot = mean\nStar = tail mean\nCVaR90 = mean above\nsample 90th percentile",fontsize=9,color=C["muted"],linespacing=1.5)
    CHECK["N12_tail_mean_above_quantile"]=bool(np.all(cvar>=q90))
    DATA["N12_loss_samples"]=samples;DATA["N12_cvar90"]=cvar
    save(fig,"N12","raincloud_tail_risk","雨云图、尾部风险与极端损失","均值相近的方案，哪个更容易遭遇大损失？",
         "Repeated loss samples per policy + a tail probability level",
         "半小提琴、原始样本、经验生存曲线与经验 CVaR90",
         "T4 + own synthesis","低",pdf,start)

def references(pdf):
    fig=plt.figure(figsize=(11.4,7.4))
    fig.text(.06,.91,"Research and implementation references",fontfamily="DejaVu Serif",fontsize=24,weight="bold")
    fig.text(.06,.845,"P = inspected award paper  /  T = visualization source  /  layouts are original adaptations",fontsize=11,color=C["muted"])
    refs=[
      ("Awards","COMAP 2024 official Outstanding Winner list","https://www.contest.comap.com/undergraduate/contests/mcm/contests/2024/results/"),
      ("P1","2024 B 2407038 - probability-grid search, Figs. 8-10","https://reformship.github.io/pages/3competition/4mcm/MCM%20Outstanding/2024/B/2407038.pdf"),
      ("P2","2024 B 2419984 - trajectories and search path, Figs. 6, 10, 12","https://reformship.github.io/pages/3competition/4mcm/MCM%20Outstanding/2024/B/2419984.pdf"),
      ("P3","2024 C 2401298 - state, prediction and entropy, Figs. 4, 12-14","https://github.com/Team-of-2401298-for-MCM2024/Dual-Temporal-Bayesian-Network"),
      ("P4","2024 A 2400996 - disturbance and recovery, Figs. 10, 16","https://reformship.github.io/pages/3competition/4mcm/MCM%20Outstanding/2024/A/2400996.pdf"),
      ("T1","mpltern - ternary geometry and contours","https://mpltern.readthedocs.io/en/latest/gallery/introductory/index.html"),
      ("T2","UpSetPlot - exact intersections","https://upsetplot.readthedocs.io/en/stable/"),
      ("T3","pyCirclize - chord geometry","https://moshi4.github.io/pyCirclize/chord_diagram/"),
      ("T4","Allen et al. - Raincloud plots","https://pmc.ncbi.nlm.nih.gov/articles/PMC6480976/"),
      ("T5","Matplotlib - hexbin and marginal distributions","https://matplotlib.org/stable/gallery/statistics/hexbin_demo.html"),
      ("T6","Crameri - scientific color-map design","https://www.fabiocrameri.ch/colourmaps/"),
    ]
    for i,(key,title,url) in enumerate(refs):
        y=.76-i*.051
        fig.text(.06,y,key,fontsize=10,weight="bold",color=C["blue"])
        fig.text(.15,y,title,fontsize=10,url=url)
    fig.text(.06,.115,"Award status is checked against COMAP. Paper PDFs P1, P2 and P4 are public mirrored copies.",
             fontsize=9.5,color=C["muted"])
    fig.text(.06,.075,"All sample values are generated. The Python renderer runs offline with NumPy, SciPy and Matplotlib.",
             fontsize=9.5,color=C["muted"])
    pdf.savefig(fig);plt.close(fig)

def main():
    started=time.perf_counter()
    with PdfPages(ROOT/"MCM_B_New_Structures.pdf") as pdf:
        cover(pdf)
        for func in [n01,n02,n03,n04,n05,n06,n07,n08,n09,n10,n11,n12]:
            func(pdf)
        references(pdf)
    np.savez_compressed(ROOT/"demo_arrays.npz",**DATA)
    (ROOT/"figure_index.json").write_text(json.dumps(INDEX,ensure_ascii=False,indent=2),encoding="utf8")
    with (ROOT/"figure_index.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=INDEX[0].keys());writer.writeheader();writer.writerows(INDEX)
    fpath=Path("C:/Windows/Fonts/arial.ttf")
    font=ImageFont.truetype(str(fpath),25) if fpath.exists() else ImageFont.load_default()
    for group,ids,title in [
        ("01_geometry",["N01","N02"],"ALLOCATION GEOMETRY  /  SEQUENTIAL SEARCH"),
        ("02_uncertainty",["N03","N04"],"JOINT UNCERTAINTY  /  DISTRIBUTION EVOLUTION"),
        ("03_robustness",["N05","N06"],"FAILURE INTERSECTIONS  /  PREFERENCE TRANSITIONS"),
        ("04_pathways",["N07","N08"],"ADAPTIVE PATHWAYS  /  EXCHANGE STRUCTURE"),
        ("05_dynamics",["N09","N10"],"LATENT STATES  /  NONLINEAR DYNAMICS"),
        ("06_explanation",["N11","N12"],"MECHANISM ATTRIBUTION  /  TAIL RISK")]:
        sheet=Image.new("RGB",(2070,743),"#E9EDF3");draw=ImageDraw.Draw(sheet)
        draw.text((22,15),title,font=font,fill=C["ink"])
        for j,key in enumerate(ids):
            row=next(x for x in INDEX if x["id"]==key)
            im=Image.open(ROOT/row["png"]).convert("RGB").resize((1014,658),Image.Resampling.LANCZOS)
            sheet.paste(im,(14+1026*j,66))
        sheet.save(ROOT/f"Preview_{group}.jpg",quality=95,subsampling=0)
    # Rasterize every final PDF page for inspection.
    qa=ROOT/"research"/"_qa";qa.mkdir(exist_ok=True)
    with fitz.open(ROOT/"MCM_B_New_Structures.pdf") as doc:
        for i,p in enumerate(doc):
            pix=p.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False)
            pix.save(qa/f"page_{i+1:02}.png")
        CHECK["pdf_pages"]=len(doc)
        outside=[]
        for i,p in enumerate(doc):
            for block in p.get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    for span in line["spans"]:
                        rect=fitz.Rect(span["bbox"])
                        if rect.x0<-.5 or rect.y0<-.5 or rect.x1>p.rect.width+.5 or rect.y1>p.rect.height+.5:
                            outside.append([i+1,span["text"]])
        CHECK["pdf_text_outside_page"]=outside
        CHECK["synthetic_markers_on_all_figure_pages"]=all("SYNTHETIC DEMO" in doc[i].get_text() for i in range(1,13))
    CHECK["figure_count"]=len(INDEX)
    CHECK["render_seconds_by_figure"]=DURATIONS
    CHECK["total_seconds"]=round(time.perf_counter()-started,2)
    CHECK["seed"]=SEED
    (ROOT/"validation.json").write_text(json.dumps(CHECK,ensure_ascii=False,indent=2),encoding="utf8")
    assert not outside,outside
    assert all(v for k,v in CHECK.items() if k.startswith("N") and isinstance(v,bool))
    print(json.dumps(CHECK,ensure_ascii=False,indent=2),flush=True)
if __name__=="__main__":main()
