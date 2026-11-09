"""Reproducible scientific figure demonstrations. All data are synthetic."""
from pathlib import Path
import csv
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, PathPatch, Rectangle
from matplotlib.path import Path as MplPath
from matplotlib.backends.backend_pdf import PdfPages
from scipy.stats import gaussian_kde
from PIL import Image, ImageDraw, ImageFont
import fitz

ROOT = Path(__file__).resolve().parent
PNG, SVG = ROOT / "PNG", ROOT / "SVG"
for directory in (PNG, SVG):
    directory.mkdir(exist_ok=True)
SEED = 20271107
rng = np.random.default_rng(SEED)
P = dict(ink="#243E46", primary="#357B8B", eco="#83A38A", social="#D4A653",
         accent="#C77562", slate="#8796B0", muted="#75838B", grid="#E2E7E8", pale="#F3F6F5")
SERIES = [P["primary"], P["eco"], P["social"], P["accent"], P["slate"]]
SEQ = colors.LinearSegmentedColormap.from_list("ocean", ["#F1F6F5", "#8AB4B1", "#357B8B", "#234A60"])
DIV = colors.LinearSegmentedColormap.from_list("balance", ["#357B8B", "#FAF8F3", "#C77562"])
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10.5, "axes.titlesize": 11.5,
    "axes.labelsize": 10.5, "text.color": P["ink"], "axes.labelcolor": P["ink"],
    "xtick.color": P["muted"], "ytick.color": P["muted"],
    "axes.edgecolor": "#BFCBCD", "axes.linewidth": .7,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": P["grid"], "grid.linewidth": .65,
    "legend.frameon": False, "legend.fontsize": 9,
    "svg.fonttype": "none", "pdf.fonttype": 42, "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.facecolor": "white",
    "hatch.color": "#AEBBBD", "hatch.linewidth": .45,
    "lines.linewidth": 2, "xtick.labelsize": 9, "ytick.labelsize": 9,
})
INDEX, CHECKS = [], {}

def canvas(title, subtitle, code, nrows=1, ncols=1, **kwargs):
    fig, ax = plt.subplots(nrows, ncols, figsize=(9.5, 6.2), **kwargs)
    fig.subplots_adjust(left=.10, right=.94, top=.78, bottom=.18, wspace=.34, hspace=.5)
    fig.text(.06, .945, title, fontsize=17, weight="bold", va="top")
    fig.text(.06, .885, subtitle, fontsize=10, color=P["muted"], va="top")
    fig.text(.94, .955, code, fontsize=11, color=P["primary"], ha="right", va="bottom", weight="bold")
    return fig, ax

def finish(fig, code, name, chinese, use, pdf):
    fig.text(.06, .045, "SYNTHETIC DEMO  /  Normalized or arbitrary units  /  No field observations",
             fontsize=8, color=P["muted"])
    fig.text(.94, .045, "MCM  •  FIGURE STUDIO", fontsize=8, ha="right", color=P["muted"])
    stem = f"{code}_{name}"
    fig.savefig(PNG / f"{stem}.png", dpi=300)
    fig.savefig(SVG / f"{stem}.svg")
    pdf.savefig(fig, dpi=300)
    INDEX.append(dict(id=code, name=name, title=chinese, purpose=use,
                      png=f"PNG/{stem}.png", svg=f"SVG/{stem}.svg"))
    plt.close(fig)
    print(f"Rendered {code} {name}", flush=True)

def clean(ax, axis="y"):
    ax.grid(axis=axis, zorder=0)
    ax.set_axisbelow(True)

def panel(ax, text):
    ax.set_title(text, loc="left", weight="bold", pad=12)

def box(ax, x, y, w, h, text, color, fontsize=11):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.018",
                               facecolor=colors.to_rgba(color,.09), edgecolor=colors.to_rgba(color,.6), linewidth=1))
    ax.text(x+w/2, y+h/2, text, va="center", ha="center", fontsize=fontsize, color=P["ink"])

def arrow(ax, start, end, color=None, rad=0, lw=1.4, text=None, textpos=None):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12,
                                color=color or P["muted"], linewidth=lw,
                                connectionstyle=f"arc3,rad={rad}", shrinkA=3, shrinkB=3))
    if text:
        ax.text(*textpos, text, fontsize=9.5, ha="center", color=color or P["muted"],
                bbox=dict(facecolor="white", edgecolor="none", pad=1))

def synthetic_model(x):
    return (1.8*x[...,0] + .8*x[...,1]**2 + 1.2*x[...,2]*x[...,3]
            + .15*np.sin(3*np.pi*x[...,4]) + .05*x[...,5])

def cover(pdf):
    fig = plt.figure(figsize=(9.5, 6.2))
    fig.text(.06,.9,"MCM / ICM",color=P["primary"],fontsize=12,weight="bold")
    fig.text(.06,.80,"A visual language for model evidence",fontsize=24,weight="bold")
    fig.text(.06,.72,"24 figure types + 4 palette comparisons",fontsize=14,color=P["muted"])
    fig.text(.06,.65,"All values, profiles, locations and scenarios are synthetic demonstrations.",
             fontsize=10.5,color=P["muted"])
    groups = [
        ("01–04   MODEL & DATA","Workflow • feedback • exploration • comparison"),
        ("05–09   OPTIMIZATION","Pareto • 3D surface • parallel axes • feasible domain • response"),
        ("10–14   ALLOCATION & SENSITIVITY","Sankey • budget mix • correlation • tornado • Morris"),
        ("15–18   UNCERTAINTY & DECISIONS","Distributions • fan chart • regret • policy regimes"),
        ("19–24   SPACE & VALIDATION","Network • transfers • radar • residuals • margins • convergence"),
        ("25–28   COLOR STUDIES","Coastal • Academic • Terracotta • High contrast"),
    ]
    for i,(a,b) in enumerate(groups):
        y=.54-i*.073
        fig.text(.06,y,a,fontsize=10.5,weight="bold")
        fig.text(.06,y-.028,b,fontsize=9.4,color=P["muted"])
    fig.text(.06,.045,"REPRODUCIBLE DEMONSTRATIONS  /  SEED 20271107",fontsize=8,color=P["muted"])
    pdf.savefig(fig, dpi=300)
    plt.close(fig)

with PdfPages(ROOT / "MCM_B_Figure_Atlas.pdf") as pdf:
    cover(pdf)
    fig, ax = canvas("From questions to defensible recommendations",
                     "A modular workflow with explicit checks and decision outputs", "01")
    ax.set(xlim=(0,1), ylim=(0,1)); ax.axis("off")
    for x, title, color in zip([.02,.355,.69], ["01  DATA & SCOPE","02  MODEL & SOLVE","03  TEST & COMMUNICATE"], SERIES[:3]):
        ax.text(x+.14,.94,title,ha="center",fontsize=10,weight="bold",color=color)
    labels = [
        (.02,.68,"Questions\nDeliverables & boundaries",P["primary"]),
        (.02,.37,"Evidence\nUnits, sources & assumptions",P["primary"]),
        (.355,.68,"Mechanisms\nStates, feedback & constraints",P["eco"]),
        (.355,.37,"Candidate policies\nSearch & independent replay",P["eco"]),
        (.69,.68,"Robustness\nParameters, scenarios\n& preferences",P["social"]),
        (.69,.37,"Decision brief\nTrade-offs, limits & triggers",P["social"]),
    ]
    for x,y,t,c in labels: box(ax,x,y,.28,.18,t,c,10.5)
    for a,b in [((.16,.68),(.16,.55)),((.30,.46),(.355,.77)),((.495,.68),(.495,.55)),
                ((.635,.46),(.69,.77)),((.83,.68),(.83,.55))]:
        arrow(ax,a,b)
    arrow(ax,(.72,.36),(.53,.35),color=P["accent"],rad=-.3,text="revise if needed",textpos=(.64,.24))
    box(ax,.02,.035,.95,.115,"OUTPUT CONTRACT   •   locked inputs   →   audited tables   →   figures   →   paper",P["slate"],10)
    finish(fig,"01","workflow","总工作流程图","概览数据、模型、验证与交付的关系",pdf)

    fig, ax = canvas("A policy feedback system",
                     "Signed arrows show local directions of influence in a conceptual loop", "02")
    ax.set(xlim=(0,1),ylim=(0,1));ax.axis("off")
    nodes=[(.08,.70,"Demand",P["primary"]),(.65,.70,"Receipts",P["primary"]),
           (.65,.15,"Investment",P["social"]),(.08,.15,"System quality",P["eco"])]
    for x,y,t,c in nodes: box(ax,x,y,.25,.15,t,c)
    arrow(ax,(.33,.775),(.65,.775),text="+",textpos=(.49,.82))
    arrow(ax,(.775,.70),(.775,.30),text="+",textpos=(.82,.50))
    arrow(ax,(.65,.225),(.33,.225),text="+",textpos=(.49,.17))
    arrow(ax,(.205,.30),(.205,.70),text="+",textpos=(.16,.50))
    box(ax,.405,.45,.20,.14,"Policy lever",P["accent"])
    arrow(ax,(.405,.52),(.32,.71),color=P["accent"],text="−",textpos=(.33,.56))
    arrow(ax,(.605,.52),(.70,.70),color=P["accent"],text="+",textpos=(.66,.56))
    ax.text(.49,.035,"Investment feedback   •   directional policy effects",ha="center",fontsize=10,color=P["muted"])
    finish(fig,"02","feedback_loop","带正负方向的反馈环","解释政策、资金与状态之间的机制",pdf)

    fig, axs = canvas("Read the data before solving the model",
                       "Three complementary views of an illustrative input dataset", "03",1,3)
    fig.subplots_adjust(wspace=.60,left=.09,right=.95)
    t=np.arange(1,13);a=.55+.035*t+.13*np.sin(t/2)
    axs[0].plot(t,a,"o-",color=P["primary"],ms=4)
    axs[0].fill_between(t,0,a,color=P["primary"],alpha=.08)
    axs[0].set(xlabel="Period",ylabel="Demand index",ylim=(0,1.2));panel(axs[0],"(a) Trend");clean(axs[0])
    cats=["Access","Crowding","Services","Ecology"];vals=[.74,.62,.48,.35]
    axs[1].barh(cats,vals,color=[P["primary"],P["social"],P["slate"],P["eco"]],height=.5)
    axs[1].invert_yaxis();axs[1].set(xlabel="Share",xlim=(0,1));panel(axs[1],"(b) Input profile")
    for i,v in enumerate(vals):axs[1].text(v+.025,i,f"{v:.0%}",va="center",fontsize=9)
    clean(axs[1],"x")
    m=np.linspace(0,12,200);season=.2+.8*np.exp(-.5*((m-6.8)/2)**2)
    axs[2].plot(m,season,color=P["eco"]);axs[2].fill_between(m,0,season,color=P["eco"],alpha=.2)
    axs[2].axhline(.8,color=P["accent"],ls="--",lw=1.2)
    axs[2].set(xlabel="Seasonal period",ylabel="Load index",ylim=(0,1.2));panel(axs[2],"(c) Concentration");clean(axs[2])
    finish(fig,"03","data_dashboard","数据探索三联图","同时呈现趋势、问题构成和季节集中度",pdf)

    fig, ax = canvas("A direct comparison of policy outcomes",
                     "Connected dots preserve scale and reveal the direction of each change", "04")
    labels=["Economic performance","Environmental quality","Resident acceptance","Infrastructure quality","Fiscal flexibility"]
    before=np.array([.72,.39,.47,.58,.52]);after=np.array([.78,.73,.71,.76,.64]);y=np.arange(5)
    ax.hlines(y,before,after,color="#CDD7D7",lw=5,zorder=1)
    ax.scatter(before,y,s=70,color="white",edgecolor=P["muted"],linewidth=1.6,label="Baseline",zorder=3)
    ax.scatter(after,y,s=80,color=P["accent"],edgecolor="white",label="Illustrative policy",zorder=4)
    for i,(b,a) in enumerate(zip(before,after)):
        ax.text(a+.025,i,f"+{a-b:.2f}",va="center",fontsize=10,weight="bold",color=P["accent"])
    ax.set(yticks=y,yticklabels=labels,xlim=(.2,1),xlabel="Normalized performance  /  higher is better")
    ax.invert_yaxis();clean(ax,"x");ax.legend(loc="lower right")
    fig.subplots_adjust(left=.29)
    finish(fig,"04","outcome_dumbbell","基准与方案哑铃图","比较多个指标的提升幅度",pdf)

    fig, ax = canvas("A trade-off that can be read at a glance",
                     "The envelope is computed from all generated candidate policies", "05")
    x=rng.uniform(.15,1,650);y=.10+.57*x**1.7+rng.gamma(1.3,.08,len(x))
    score=.4*x+.6*(1-np.minimum(y,1))
    pts=ax.scatter(x,y,c=score,cmap=SEQ,s=21,alpha=.6,edgecolor="none")
    order=np.argsort(-x);best=np.inf;front=[]
    for i in order:
        if y[i]<best:front.append(i);best=y[i]
    front=np.array(front)
    ax.plot(x[front],y[front],color=P["primary"],lw=1.5,label="Non-dominated envelope")
    selected=front[np.argmin(np.abs(x[front]-.72))]
    ax.scatter(x[selected],y[selected],marker="*",s=240,color=P["accent"],edgecolor="white",lw=1,zorder=5)
    ax.annotate("Illustrative choice",xy=(x[selected],y[selected]),xytext=(.28,.68),
                arrowprops=dict(arrowstyle="-",color=P["accent"]),color=P["accent"],weight="bold")
    ax.set(xlabel="Benefit  /  higher is better",ylabel="Pressure  /  lower is better",ylim=(0,1),xlim=(.1,1.03))
    clean(ax);cb=fig.colorbar(pts,ax=ax,pad=.035,fraction=.045);cb.set_label("Illustrative normalized score")
    ax.legend(loc="upper right")
    finish(fig,"05","pareto_2d","二维 Pareto 点云与推荐点","显示目标冲突、非支配边界和折中选择",pdf)

    fig=plt.figure(figsize=(9.5,6.2));ax=fig.add_subplot(projection="3d")
    fig.subplots_adjust(left=.03,right=.82,bottom=.13,top=.83)
    fig.text(.06,.945,"A three-objective Pareto surface",fontsize=17,weight="bold",va="top")
    fig.text(.06,.885,"An explicit analytic surface with three distinct objectives; all are minimized",fontsize=10,color=P["muted"])
    fig.text(.94,.955,"06",ha="right",fontsize=11,color=P["primary"],weight="bold")
    u,v=np.meshgrid(np.linspace(.07,1,42),np.linspace(.07,1,42))
    w=(1-np.sqrt(u))**2+.55*(1-np.sqrt(v))**2
    surf=ax.plot_surface(u,v,w,cmap=SEQ,linewidth=0,antialiased=True,alpha=.96)
    
    ax.set(xlabel="Objective A",ylabel="Objective B",zlabel="Objective C");ax.view_init(elev=26,azim=43)
    for axis in (ax.xaxis,ax.yaxis,ax.zaxis):
        axis.pane.fill=False;axis._axinfo["grid"]["color"]=(.86,.90,.90,1)
    cb=fig.colorbar(surf,ax=ax,shrink=.60,pad=.10,fraction=.035);cb.set_label("Objective C")
    finish(fig,"06","pareto_3d_surface","三维解析 Pareto 曲面","展示三项相互权衡的独立目标",pdf)

    fig,ax=canvas("Read several objectives together","Every axis is normalized to a common preference direction", "07")
    pol=rng.beta(2.6,2.6,(70,5))
    pol[:,1]=np.clip(.92-.7*pol[:,0]+rng.normal(0,.10,70),0,1)
    pol[:,3]=np.clip(.3+.6*pol[:,2]+rng.normal(0,.09,70),0,1)
    utility=pol@np.array([.25,.25,.2,.2,.1]);best=np.argmax(utility);xx=np.arange(5)
    for row in pol:ax.plot(xx,row,color=P["primary"],alpha=.13,lw=1)
    ax.plot(xx,pol[best],color=P["accent"],lw=3,marker="o",ms=6,label="Illustrative choice")
    for k in xx:ax.axvline(k,color=P["grid"],lw=.8,zorder=0)
    ax.set(xticks=xx,xticklabels=["Benefit","Ecology","Acceptance","Infrastructure","Flexibility"],
           ylim=(0,1.04),xlim=(-.12,4.12),ylabel="Normalized preference score  /  higher is better")
    ax.legend(loc="upper right");ax.spines["bottom"].set_visible(False)
    finish(fig,"07","parallel_coordinates","多目标平行坐标图","展示方案在五个指标上的优势和代价",pdf)

    fig,ax=canvas("Show the actual constraint boundary",
                  "Colors encode performance; hatching marks the excluded part of the grid", "08")
    xx=np.linspace(0,1,180);X,Y=np.meshgrid(xx,xx)
    Z=1.1*X+.75*Y-.9*X**2-.55*Y**2+.18*X*Y
    feasible=(X+.65*Y<=1.05)&(X>=.15)&(Y>=.1)
    m=ax.contourf(X,Y,np.ma.masked_where(~feasible,Z),levels=14,cmap=SEQ)
    ax.contourf(X,Y,(~feasible).astype(float),levels=[.5,1.5],colors=["#F6F5F1"],hatches=["//"])
    ax.contour(X,Y,X+.65*Y,levels=[1.05],colors=[P["accent"]],linewidths=1.7)
    ax.axvline(.15,color=P["muted"],ls="--",lw=1);ax.axhline(.1,color=P["muted"],ls="--",lw=1)
    ij=np.unravel_index(np.where(feasible,Z,-np.inf).argmax(),Z.shape)
    ax.scatter(X[ij],Y[ij],marker="*",s=190,color=P["accent"],edgecolor="white",zorder=5)
    ax.text(.72,.82,"Excluded by\nconstraints",ha="center",color=P["muted"],bbox=dict(facecolor="white",edgecolor="none",alpha=.9))
    ax.set(xlabel="Policy intensity A",ylabel="Policy intensity B",xlim=(0,1),ylim=(0,1))
    fig.colorbar(m,ax=ax,pad=.035).set_label("Synthetic performance")
    CHECKS["grid_choice_is_feasible"]=bool(feasible[ij])
    finish(fig,"08","feasible_contours","可行域与等值面","区分目标表现、硬约束边界和网格最优点",pdf)

    fig,axs=canvas("Total response and marginal return","The same analytic response is read in levels and derivatives", "09",1,2)
    xx=np.linspace(0,1,200)
    for scale,k,c,label in zip([.95,.86,.72],[2.6,4.5,7],SERIES[:3],["Channel A","Channel B","Channel C"]):
        yy=scale*(1-np.exp(-k*xx));dy=scale*k*np.exp(-k*xx)
        axs[0].plot(xx,yy,color=c,label=label);axs[1].plot(xx,dy,color=c)
    panel(axs[0],"(a) Accumulated response");panel(axs[1],"(b) Marginal response")
    for a in axs:a.set_xlabel("Normalized investment");clean(a)
    axs[0].set_ylabel("Response");axs[1].set_ylabel("Response per unit investment");axs[0].legend(loc="lower right")
    finish(fig,"09","diminishing_returns","响应曲线与边际收益双联图","解释投入的边际递减与渠道差异",pdf)

    fig,ax=canvas("Follow every unit of the budget","Ribbon widths are proportional to a conserved synthetic allocation", "10")
    ax.set(xlim=(0,1),ylim=(0,1));ax.axis("off")
    flow=np.array([[12,5,3],[8,14,8],[3,7,20]],float);row=flow.sum(axis=1);col=flow.sum(axis=0)
    scale=.74/flow.sum();gap=.045
    def spans(tot):
        cursor=.92;out=[]
        for v in tot:
            hi=cursor;lo=hi-v*scale;out.append([lo,hi]);cursor=lo-gap
        return out
    left=spans(row);right=spans(col);left_cursor=[b for a,b in left];right_cursor=[b for a,b in right]
    for i in range(3):
        for j in range(3):
            width=flow[i,j]*scale
            a1=left_cursor[i];a0=a1-width;left_cursor[i]=a0
            b1=right_cursor[j];b0=b1-width;right_cursor[j]=b0
            verts=[(.28,a0),(.47,a0),(.53,b0),(.72,b0),(.72,b1),(.53,b1),(.47,a1),(.28,a1),(.28,a0)]
            codes=[MplPath.MOVETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,MplPath.LINETO,
                   MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,MplPath.CLOSEPOLY]
            ax.add_patch(PathPatch(MplPath(verts,codes),facecolor=SERIES[j],edgecolor="white",lw=.5,alpha=.50))
    for i,(lo,hi) in enumerate(left):
        ax.add_patch(Rectangle((.25,lo),.03,hi-lo,color=P["primary"]))
        ax.text(.235,(lo+hi)/2,f"Source {chr(65+i)}\n{row[i]:.0f} units",ha="right",va="center",fontsize=11)
    for j,(lo,hi) in enumerate(right):
        ax.add_patch(Rectangle((.72,lo),.03,hi-lo,color=SERIES[j]))
        ax.text(.77,(lo+hi)/2,f"Use {chr(65+j)}\n{col[j]:.0f} units",va="center",fontsize=11)
    CHECKS["sankey_conservation"]=bool(flow.sum()==row.sum()==col.sum())
    finish(fig,"10","budget_sankey","守恒资金桑基图","展示资金从多个来源流向多个用途",pdf)

    fig,ax=canvas("How the allocation changes by strategy","Composition and absolute totals are displayed separately", "11")
    mix=np.array([[.30,.27,.23,.20],[.22,.40,.23,.15],[.24,.28,.33,.15],[.28,.30,.26,.16]])
    yy=np.arange(4);left=np.zeros(4);cols=SERIES[:3]+["#B8C0C4"]
    for j,label in enumerate(["Infrastructure","Environment","Community","Reserve"]):
        ax.barh(yy,mix[:,j],left=left,color=cols[j],edgecolor="white",height=.58,label=label)
        for i in range(4):ax.text(left[i]+mix[i,j]/2,i,f"{mix[i,j]:.0%}",ha="center",va="center",color=P["ink"],fontsize=10)
        left+=mix[:,j]
    for i,total in enumerate([80,90,85,88]):ax.text(1.035,i,f"{total} units",va="center",fontsize=10)
    ax.set(yticks=yy,yticklabels=["Balanced","Ecology first","Community first","Robust blend"],xlim=(0,1.21),xlabel="Share of total budget")
    ax.invert_yaxis();ax.set_xticks([0,.25,.5,.75,1],["0%","25%","50%","75%","100%"])
    ax.legend(loc="upper center",bbox_to_anchor=(.5,-.18),ncol=4)
    fig.subplots_adjust(left=.22,bottom=.25)
    CHECKS["budget_shares_sum_to_one"]=bool(np.allclose(mix.sum(axis=1),1))
    finish(fig,"11","budget_composition","百分比堆叠预算图","比较策略的预算结构并保留绝对规模",pdf)

    fig,ax=canvas("Which model quantities move together?","A signed correlation matrix from a generated multivariate sample", "12")
    a=rng.normal(size=(1400,4))
    sample=np.column_stack([a[:,0],-.75*a[:,0]+.55*a[:,1],.6*a[:,1]+.45*a[:,2],
                            .65*a[:,0]-.25*a[:,2]+.5*a[:,3],-.5*a[:,1]+.7*a[:,3]])
    corr=np.corrcoef(sample,rowvar=False);labels=["Benefit","Pressure","Acceptance","Capacity","Tax lever"]
    im=ax.imshow(corr,vmin=-1,vmax=1,cmap=DIV,aspect="auto")
    ax.set_xticks(np.arange(5),labels);ax.set_yticks(np.arange(5),labels)
    for i in range(5):
        for j in range(5):ax.text(j,i,f"{corr[i,j]:+.2f}",ha="center",va="center",
                    color="white" if abs(corr[i,j])>.65 else P["ink"],fontsize=11)
    ax.set_xticks(np.arange(-.5,5,1),minor=True);ax.set_yticks(np.arange(-.5,5,1),minor=True)
    ax.grid(which="minor",color="white",lw=2);ax.tick_params(which="minor",bottom=False,left=False)
    fig.colorbar(im,ax=ax,pad=.035).set_label("Pearson correlation")
    fig.subplots_adjust(left=.17)
    finish(fig,"12","correlation_heatmap","带数值的相关性热力图","筛查变量间的正负关联",pdf)

    fig,ax=canvas("Local sensitivity around a common baseline","Each factor changes by ±20%; all others stay fixed", "13")
    base=np.full(6,.5);v0=synthetic_model(base);lo=[];hi=[]
    for i in range(6):
        l=base.copy();h=base.copy();l[i]*=.8;h[i]*=1.2
        lo.append(synthetic_model(l)-v0);hi.append(synthetic_model(h)-v0)
    lo=np.array(lo);hi=np.array(hi);order=np.argsort(np.maximum(np.abs(lo),np.abs(hi)))[::-1];yy=np.arange(6)
    ax.barh(yy-.14,lo[order],height=.25,color=P["primary"],label="Factor × 0.8")
    ax.barh(yy+.14,hi[order],height=.25,color=P["accent"],label="Factor × 1.2")
    ax.axvline(0,color=P["muted"],lw=1)
    for i,(a,b) in enumerate(zip(lo[order],hi[order])):
        for v,dy in [(a,-.14),(b,.14)]:
            ax.text(v+(.008 if v>=0 else -.008),i+dy,f"{v:+.3f}",va="center",ha="left" if v>=0 else "right",fontsize=9)
    ax.set(yticks=yy,yticklabels=[f"Factor {i+1}" for i in order],xlabel="Change in synthetic output",xlim=(-.25,.25))
    ax.invert_yaxis();clean(ax,"x");ax.legend(loc="lower right")
    finish(fig,"13","local_tornado","双向局部敏感性龙卷风图","保留增减参数的真实方向和影响大小",pdf)

    effects=[]
    for _ in range(160):
        point=rng.choice([0,.2,.4],6).astype(float);ee=np.zeros(6)
        for j in rng.permutation(6):
            start=synthetic_model(point);point[j]+=.6;ee[j]=(synthetic_model(point)-start)/.6
        effects.append(ee)
    effects=np.array(effects);mu=np.abs(effects).mean(axis=0);sigma=effects.std(axis=0,ddof=1)
    fig,ax=canvas("Separate influence from nonlinear response",
                  "Morris elementary effects computed on a six-factor toy function; 160 trajectories", "14")
    ax.scatter(mu,sigma,s=90,color=SERIES+[P["slate"]],edgecolor="white",lw=1,zorder=3)
    for i in range(6):
        offset = (-42, 14) if i == 2 else (10, -17) if i == 3 else (8, 8)
        ax.annotate(f"Factor {i+1}",(mu[i],sigma[i]),xytext=offset,textcoords="offset points",fontsize=10)
    ax.set(xlabel=r"Mean absolute elementary effect  $\mu^*$",ylabel=r"Standard deviation of effects  $\sigma$",
           xlim=(-.03,2.18),ylim=(-.04,.9))
    ax.text(.05,.80,"Nonlinearity / interaction",color=P["muted"],fontsize=10)
    ax.text(1.24,.07,"Strong main effect",color=P["muted"],fontsize=10);clean(ax,"both")
    CHECKS["morris_linear_factor_has_constant_effect"]=bool(np.allclose(effects[:,0],1.8))
    finish(fig,"14","morris_screening","Morris 全局筛选图","区分影响强度和非线性或交互线索",pdf)

    fig,axs=canvas("Distribution, spread and tail behavior",
                    "Generated samples are summarized by densities, observations and quantile intervals", "15",1,2)
    distributions=[rng.normal(.58,.10,650),rng.normal(.66,.075,650),rng.normal(.69,.045,650)]
    xx=np.linspace(.15,1,240)
    for i,(d,c,label) in enumerate(zip(distributions,SERIES[:3],["Baseline","Policy A","Policy B"])):
        density=gaussian_kde(d)(xx);axs[0].plot(xx,density,color=c,label=label)
        axs[0].fill_between(xx,0,density,color=c,alpha=.10)
        q=np.quantile(d,[.05,.25,.5,.75,.95])
        axs[1].hlines(i,q[0],q[4],color=c,lw=2);axs[1].hlines(i,q[1],q[3],color=c,lw=10)
        axs[1].scatter(q[2],i,color="white",edgecolor=c,s=45,zorder=3);sub=d[::18]
        axs[1].scatter(sub,np.full(len(sub),i)+rng.uniform(-.16,.16,len(sub)),s=7,color=c,alpha=.23)
    fig.subplots_adjust(bottom=.24)
    panel(axs[0],"(a) Estimated density");panel(axs[1],"(b) Median and intervals")
    axs[0].set(xlabel="Output index",ylabel="Density",xlim=(.15,1))
    axs[1].set(yticks=range(3),yticklabels=["Baseline","Policy A","Policy B"],xlabel="Output index",xlim=(.15,1))
    axs[1].invert_yaxis();axs[0].legend();clean(axs[0]);clean(axs[1],"x")
    axs[1].text(.02,-.22,"Thick 50%  /  thin 90%  /  dot median",transform=axs[1].transAxes,fontsize=8.8,color=P["muted"])
    finish(fig,"15","distribution_intervals","密度与分位区间双联图","比较方案的分布、波动与尾部风险",pdf)

    fig,ax=canvas("Uncertainty through time",
                  "Nested bands are pointwise sample quantiles from 1,500 synthetic paths", "16")
    t=np.arange(25);paths=.45+.011*t[None,:]+np.cumsum(rng.normal(0,.019,(1500,25)),axis=1)
    q=np.quantile(paths,[.05,.15,.25,.5,.75,.85,.95],axis=0)
    ax.fill_between(t,q[0],q[6],color=P["primary"],alpha=.10,label="90% pointwise band")
    ax.fill_between(t,q[1],q[5],color=P["primary"],alpha=.16,label="70% pointwise band")
    ax.fill_between(t,q[2],q[4],color=P["primary"],alpha=.25,label="50% pointwise band")
    ax.plot(t,q[3],color=P["primary"],label="Median")
    ax.axhline(.8,color=P["accent"],ls="--",lw=1.5,label="Illustrative threshold")
    ax.set(xlabel="Time step",ylabel="System load",xlim=(0,24),ylim=(.3,1))
    ax.legend(loc="upper left",ncol=2);clean(ax)
    CHECKS["fan_quantiles_are_ordered"]=bool(np.all(np.diff(q,axis=0)>=0))
    finish(fig,"16","uncertainty_fan","动态分位数扇形图","显示未来轨迹和逐时不确定性",pdf)

    fig,ax=canvas("A policy that limits the worst regret",
                  "Regret is the gap to the best policy in each scenario; lower is better", "17")
    scores=np.array([[.90,.59,.65,.66,.72,.68],[.70,.92,.60,.73,.66,.70],
                     [.65,.63,.91,.68,.70,.75],[.78,.78,.78,.80,.77,.79],[.85,.72,.70,.85,.88,.68]])
    regret=scores.max(axis=0)-scores;maxr=regret.max(axis=1);choice=maxr.argmin()
    grid=fig.add_gridspec(1,2,left=.14,right=.93,bottom=.21,top=.82,width_ratios=[4.4,1],wspace=.12)
    ax.remove();ax=fig.add_subplot(grid[0]);side=fig.add_subplot(grid[1],sharey=ax)
    im=ax.imshow(regret,cmap=SEQ,vmin=0,vmax=.35,aspect="auto")
    for i in range(5):
        for j in range(6):ax.text(j,i,f"{regret[i,j]:.2f}",ha="center",va="center",
                    color="white" if regret[i,j]>.20 else P["ink"],fontsize=10)
    ax.set(xticks=range(6),xticklabels=[f"S{i+1}" for i in range(6)],yticks=range(5),
           yticklabels=[f"Policy {chr(65+i)}" for i in range(5)],xlabel="Scenario")
    ax.add_patch(Rectangle((-.5,choice-.5),6,1,fill=False,edgecolor=P["accent"],lw=2.2))
    side.barh(range(5),maxr,color=[P["accent"] if i==choice else "#BDCACC" for i in range(5)],height=.55)
    side.set(xlim=(0,.45),xlabel="Worst regret");side.tick_params(left=False,labelleft=False)
    for i,v in enumerate(maxr):side.text(v+.01,i,f"{v:.2f}",va="center",fontsize=9)
    cax=fig.add_axes([.14,.105,.58,.018])
    cbar=fig.colorbar(im,cax=cax,orientation="horizontal",ticks=[0,.1,.2,.3])
    cbar.ax.tick_params(labelsize=8)
    CHECKS["regret_has_a_zero_in_each_scenario"]=bool(np.allclose(regret.min(axis=0),0))
    finish(fig,"17","minimax_regret","最小最大后悔矩阵","把各情景损失与方案最坏后悔并列",pdf)

    fig,ax=canvas("Where does the preferred strategy change?",
                  "Each region selects the largest of four explicit synthetic policy scores", "18")
    X,Y=np.meshgrid(np.linspace(0,1,160),np.linspace(0,1,160))
    targets=[(.15,.18),(.82,.22),(.25,.80),(.8,.80)]
    scores=np.stack([-((X-a)**2+(Y-b)**2)+bias for (a,b),bias in zip(targets,[0,.035,.025,-.01])])
    winner=scores.argmax(axis=0);excluded=(X+.5*Y>1.26)
    cmap=colors.ListedColormap([P["primary"],P["eco"],P["social"],P["slate"]])
    ax.pcolormesh(X,Y,np.ma.masked_where(excluded,winner),cmap=cmap,vmin=-.5,vmax=3.5,shading="auto",alpha=.72,rasterized=True)
    for region in range(4):
        ax.contour(X,Y,(winner==region).astype(float),levels=[.5],colors="white",linewidths=1.0)
    ax.contourf(X,Y,excluded.astype(float),levels=[.5,1.5],colors=["#F2F1ED"],hatches=["//"])
    for i,(a,b) in enumerate(targets):ax.text(a,b,f"Policy {chr(65+i)}",ha="center",weight="bold",fontsize=12,color=P["ink"])
    ax.text(.88,.93,"Excluded",fontsize=9,ha="center",rotation=-25)
    ax.set(xlabel="External condition A",ylabel="External condition B",xlim=(0,1),ylim=(0,1))
    finish(fig,"18","policy_regimes","最优策略分区图","呈现外部条件变化时的政策切换",pdf)

    fig,axs=canvas("Redistribute flow across a network",
                    "Node positions are schematic; edge widths encode generated flow volumes", "19",1,2)
    positions=np.array([[.12,.5],[.53,.82],[.84,.54],[.65,.13],[.3,.15]])
    edges=[(0,1),(0,2),(0,3),(0,4),(1,2),(3,4)]
    flows0=[34,21,9,6,5,3];flows1=[23,18,17,12,4,7]
    for ax,flow,title in zip(axs,[flows0,flows1],["(a) Concentrated allocation","(b) Distributed allocation"]):
        ax.set(xlim=(0,1),ylim=(0,1));ax.axis("off");panel(ax,title)
        for (a,b),v in zip(edges,flow):
            arrow(ax,positions[a],positions[b],color=P["primary"],lw=.6+v/9);mid=(positions[a]+positions[b])/2
            ax.text(*mid,str(v),fontsize=9,ha="center",color=P["ink"],bbox=dict(facecolor="white",edgecolor="none",alpha=.9,pad=1))
        for i,xy in enumerate(positions):
            ax.scatter(*xy,s=570 if i==0 else 380,c=P["accent"] if i==1 else P["eco"],edgecolor="white",lw=2,zorder=5)
            ax.text(*xy,f"N{i+1}",ha="center",va="center",fontsize=10,weight="bold",zorder=6)
        ax.text(.5,.005,"SCHEMATIC POSITIONS  /  NO GEOGRAPHIC COORDINATES",fontsize=7.4,ha="center",color=P["muted"])
    finish(fig,"19","spatial_network","空间网络前后对照","比较流量集中、分流和瓶颈",pdf)

    fig,ax=canvas("Account for every transfer","Rows preserve origin totals; columns reveal the new allocation", "20")
    transfer=np.array([[24,0,7,4],[0,20,6,4],[0,0,17,0],[0,0,0,18]])
    im=ax.imshow(transfer,cmap=SEQ,vmin=0,vmax=25,aspect="auto")
    for i in range(4):
        for j in range(4):ax.text(j,i,str(transfer[i,j]),ha="center",va="center",fontsize=13,
                    color="white" if transfer[i,j]>16 else P["muted"])
    ax.set(xticks=range(4),yticks=range(4),xticklabels=["N1","N2","N3","N4"],
           yticklabels=[f"N{i+1}   (total {transfer[i].sum()})" for i in range(4)],xlabel="Destination node",ylabel="Origin node")
    for j in range(4):ax.text(j,4.08,f"Σ {transfer[:,j].sum()}",ha="center",fontsize=10)
    ax.set_ylim(4.4,-.5);ax.set_xticks(np.arange(-.5,4,1),minor=True);ax.set_yticks(np.arange(-.5,4,1),minor=True)
    ax.grid(which="minor",color="white",lw=3);ax.tick_params(which="minor",bottom=False,left=False)
    fig.colorbar(im,ax=ax,pad=.035).set_label("Flow units");fig.subplots_adjust(left=.21)
    CHECKS["transfer_total_is_100"]=bool(transfer.sum()==100)
    finish(fig,"20","transfer_matrix","守恒转移热力矩阵","解释各节点流出、流入与总量守恒",pdf)

    fig=plt.figure(figsize=(9.5,6.2));ax=fig.add_axes([.20,.17,.58,.60],projection="polar")
    fig.text(.06,.945,"Two contrasting multidimensional profiles",fontsize=17,weight="bold",va="top")
    fig.text(.06,.885,"All axes use a common 0–1 scale; profiles are compared axis by axis",fontsize=10,color=P["muted"])
    fig.text(.94,.955,"21",ha="right",fontsize=11,color=P["primary"],weight="bold")
    angle=np.linspace(0,2*np.pi,6,endpoint=False);aa=np.r_[angle,angle[0]]
    for row,c,label in [([.8,.5,.62,.78,.56,.7],P["primary"],"Profile A"),([.56,.82,.8,.49,.75,.63],P["social"],"Profile B")]:
        rr=np.r_[row,row[0]];ax.plot(aa,rr,color=c,lw=2,marker="o",ms=4,label=label);ax.fill(aa,rr,color=c,alpha=.12)
    ax.set_theta_offset(np.pi/2);ax.set_theta_direction(-1)
    ax.set_xticks(angle,["Benefit","Ecology","Acceptance","Capacity","Equity","Flexibility"])
    ax.set_ylim(0,1);ax.set_yticks([.25,.5,.75,1]);ax.tick_params(pad=10)
    ax.spines["polar"].set_color(P["grid"]);ax.grid(color=P["grid"]);ax.legend(loc="upper left",bbox_to_anchor=(1.17,.95))
    finish(fig,"21","profile_radar","多维画像雷达图","比较两种情境的指标结构",pdf)

    fig,axs=canvas("Fit, hold out, and inspect the errors","A generated nonlinear relationship with a held-out test set", "22",1,2)
    x=np.linspace(0,1,100);true=.25+.65*x-.18*x*x;yy=true+rng.normal(0,.032,100)
    test=np.arange(100)%4==0;train=~test;coef=np.polyfit(x[train],yy[train],2);pred=np.polyval(coef,x)
    err=yy[test]-pred[test];rmse=np.sqrt(np.mean(err**2));r2=1-np.sum(err**2)/np.sum((yy[test]-yy[test].mean())**2)
    axs[0].scatter(x[train],yy[train],color=P["primary"],s=22,alpha=.55,label="Training sample")
    axs[0].scatter(x[test],yy[test],color=P["accent"],s=34,marker="s",label="Held-out sample")
    axs[0].plot(x,pred,color=P["ink"],lw=1.6,label="Quadratic fit")
    axs[0].text(.04,.94,f"Test RMSE = {rmse:.3f}\nTest R² = {r2:.3f}",transform=axs[0].transAxes,va="top",
                fontsize=10,bbox=dict(facecolor="white",edgecolor=P["grid"],pad=6))
    axs[0].set(xlabel="Input",ylabel="Response");axs[0].legend(loc="lower right",fontsize=8)
    axs[1].scatter(pred[test],err,color=P["accent"],s=35,edgecolor="white",lw=.5)
    axs[1].axhline(0,color=P["muted"],ls="--",lw=1.1)
    axs[1].set(xlabel="Prediction on held-out sample",ylabel="Observed − predicted")
    panel(axs[0],"(a) Calibration and holdout");panel(axs[1],"(b) Held-out residuals")
    for a in axs:clean(a)
    CHECKS["calibration_test_n"]=int(test.sum())
    finish(fig,"22","fit_and_residuals","拟合与留出残差双联图","显示样本外精度及误差结构",pdf)

    fig,ax=canvas("Which constraints are close to binding?",
                  "Signed normalized margins from generated policies; negative values indicate violations", "23")
    margins=[rng.normal(.03,.045,250),rng.normal(.17,.06,250),rng.normal(.08,.055,250),
             rng.normal(.28,.07,250),rng.normal(.11,.04,250)];yy=np.arange(1,6)
    parts=ax.violinplot(margins,positions=yy,orientation="horizontal",showextrema=False,widths=.75)
    for b,c in zip(parts["bodies"],SERIES):b.set_facecolor(c);b.set_alpha(.25);b.set_edgecolor(c)
    for i,(d,c) in enumerate(zip(margins,SERIES),1):
        q=np.quantile(d,[.1,.25,.5,.75,.9]);ax.plot([q[0],q[4]],[i,i],color=c,lw=1.5)
        ax.plot([q[1],q[3]],[i,i],color=c,lw=6);ax.scatter(q[2],i,s=30,color="white",edgecolor=c,zorder=4)
    ax.axvspan(-.16,0,color=P["accent"],alpha=.08);ax.axvline(0,color=P["accent"],ls="--",lw=1.4)
    ax.set(yticks=yy,yticklabels=["Budget","Capacity","Ecology","Acceptance","Peak load"],
           xlabel="Signed normalized constraint margin",xlim=(-.16,.52))
    ax.invert_yaxis();clean(ax,"x");fig.subplots_adjust(left=.20)
    finish(fig,"23","constraint_margins","约束余量小提琴与箱线图","定位绑定约束和违例尾部",pdf)

    fig,axs=canvas("Report search behavior and run-to-run variation",
                    "These generated traces illustrate a reporting format for solver diagnostics", "24",1,2)
    it=np.arange(1,101);final=[]
    for k,c,label in zip(range(3),SERIES[:3],["Search A","Search B","Search C"]):
        stack=[]
        for j in range(8):
            raw=(.85+.15*rng.random())*np.exp(-it/(17+4*k))+(.015+.008*k)+rng.uniform(0,.055,len(it))
            stack.append(np.minimum.accumulate(raw))
        stack=np.array(stack);final.append(stack[:,-1]);q=np.quantile(stack,[.1,.5,.9],axis=0)
        axs[0].fill_between(it,q[0],q[2],color=c,alpha=.15);axs[0].plot(it,q[1],color=c,label=label)
    axs[0].set_yscale("log");axs[0].set(xlabel="Iteration",ylabel="Best-so-far objective gap")
    axs[0].legend();panel(axs[0],"(a) Median and 10–90% band");clean(axs[0])
    b=axs[1].boxplot(final,tick_labels=["A","B","C"],patch_artist=True,widths=.45,medianprops=dict(color=P["ink"],lw=1.4))
    for patch,c in zip(b["boxes"],SERIES):patch.set(facecolor=colors.to_rgba(c,.25),edgecolor=c)
    axs[1].set(xlabel="Search label",ylabel="Final objective gap");panel(axs[1],"(b) Eight runs per search");clean(axs[1])
    finish(fig,"24","solver_diagnostics","求解收敛与多次运行诊断","报告搜索过程及重复运行稳定性",pdf)

    palettes=[
        ("25","coastal","Coastal / 青蓝鼠尾草",["#357B8B","#83A38A","#D4A653","#C77562"]),
        ("26","academic","Academic / 学术蓝紫",["#476B94","#6F9D91","#B89A5C","#9B799D"]),
        ("27","terracotta","Terracotta / 暖陶土",["#797F9C","#969B74","#C7A36B","#B96850"]),
        ("28","contrast","High contrast / 高对比",["#0072B2","#009E73","#E69F00","#D55E00"]),
    ]
    for code,name,title,cs in palettes:
        fig,axs=canvas(title.split(" / ")[0]+" — the same data, a different palette",
                       "Identical geometry, scales and values in all four color studies",code,1,2)
        categories=["Infrastructure","Environment","Community","Reserve"];vals=np.array([.31,.37,.21,.11])
        axs[0].barh(np.arange(4),vals,color=cs,height=.55)
        for i,v in enumerate(vals):axs[0].text(v+.012,i,f"{v:.0%}",va="center",fontsize=10)
        axs[0].set(yticks=range(4),yticklabels=categories,xlim=(0,.5),xlabel="Allocation share")
        axs[0].invert_yaxis();clean(axs[0],"x");panel(axs[0],"(a) Categorical encoding")
        x=np.linspace(0,1,150)
        for j,(c,label) in enumerate(zip(cs,["A","B","C","D"])):
            yy=.18+(1-np.exp(-(2+j)*x))*(.50+.06*j);axs[1].plot(x,yy,color=c,label=label,ls=["-","--","-.",":"][j])
        axs[1].set(xlabel="Policy intensity",ylabel="Response index",ylim=(0,1))
        axs[1].legend(ncol=4,loc="lower right");clean(axs[1]);panel(axs[1],"(b) Line and style encoding")
        fig.subplots_adjust(left=.20,wspace=.35,bottom=.23)
        for j,c in enumerate(cs):
            fig.patches.append(Rectangle((.10+j*.205,.102),.035,.022,transform=fig.transFigure,facecolor=c,edgecolor="none"))
            fig.text(.142+j*.205,.106,c,fontsize=9,color=P["muted"])
        finish(fig,code,f"palette_{name}",title,"同一组数据、尺度与版式下比较配色",pdf)

font_path="C:/Windows/Fonts/arial.ttf"
font=ImageFont.truetype(font_path,22) if Path(font_path).exists() else ImageFont.load_default()
groups=[
    ("01_framework",["01","02","03","04"],"MODEL, MECHANISM & DATA"),
    ("02_tradeoffs",["05","06","07","08"],"MULTI-OBJECTIVE OPTIMIZATION"),
    ("03_budget",["09","10","11","12"],"RESPONSE, ALLOCATION & ASSOCIATION"),
    ("04_uncertainty",["13","14","15","16"],"SENSITIVITY & UNCERTAINTY"),
    ("05_decisions",["17","18","19","20"],"ROBUST DECISIONS & SPATIAL FLOWS"),
    ("06_validation",["21","22","23","24"],"PROFILES & MODEL DIAGNOSTICS"),
    ("07_palettes",["25","26","27","28"],"FOUR PALETTES  /  IDENTICAL DATA"),
]
for stem,ids,title in groups:
    sheet=Image.new("RGB",(2040,1386),"#E9EEEF");draw=ImageDraw.Draw(sheet)
    draw.text((24,18),title,font=font,fill=P["ink"])
    for j,id_ in enumerate(ids):
        row=next(i for i in INDEX if i["id"]==id_)
        im=Image.open(ROOT/row["png"]).convert("RGB").resize((1000,653),Image.Resampling.LANCZOS)
        sheet.paste(im,(14+(j%2)*1012,62+(j//2)*661))
    sheet.save(ROOT/f"Preview_{stem}.jpg",quality=94,subsampling=0)
document=fitz.open(ROOT/"MCM_B_Figure_Atlas.pdf")
for page in [0,1,6,10,14,17,22,28]:
    pix=document[page].get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
    pix.save(ROOT/f"_qa_page_{page+1:02}.png")
CHECKS.update(pdf_pages=len(document), figure_count=len(INDEX), seed=SEED,
              all_png_svg_pairs_present=all((ROOT/i["png"]).exists() and (ROOT/i["svg"]).exists() for i in INDEX))
document.close()
(ROOT/"figure_index.json").write_text(json.dumps(INDEX,ensure_ascii=False,indent=2),encoding="utf8")
with (ROOT/"figure_index.csv").open("w",newline="",encoding="utf-8-sig") as f:
    writer=csv.DictWriter(f,fieldnames=INDEX[0].keys());writer.writeheader();writer.writerows(INDEX)
(ROOT/"validation.json").write_text(json.dumps(CHECKS,ensure_ascii=False,indent=2),encoding="utf8")
print(json.dumps(CHECKS,indent=2),flush=True)
