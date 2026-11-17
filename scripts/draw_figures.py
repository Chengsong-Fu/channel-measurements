"""Reproduce the simple scene maps and antenna figures from archived numeric sources."""
from __future__ import annotations
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np
from scipy.interpolate import PchipInterpolator

ROOT=Path(__file__).resolve().parents[1]
GEOMETRY=json.loads((ROOT/'report/geometry.json').read_text(encoding='utf-8'))
FONT=Path('C:/Windows/Fonts/msyh.ttc')
if FONT.exists():font_manager.fontManager.addfont(str(FONT))
available={f.name for f in font_manager.fontManager.ttflist}
families=[name for name in ['Microsoft YaHei','Noto Sans CJK SC','Source Han Sans SC','DejaVu Sans'] if name in available]
plt.rcParams.update({'font.family':families,
    'font.size':12,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,
    'axes.labelcolor':'#345064','xtick.color':'#526b7b','ytick.color':'#526b7b',
    'axes.edgecolor':'#a9bac5','text.color':'#254456','svg.fonttype':'path','pdf.fonttype':42})
INK='#254456';TX='#087f73';RX='#3679bf';NLOS='#bf7b20';LIGHT='#eef4f7'

def save(fig,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path.with_suffix('.png'),dpi=170,facecolor='white')
    fig.savefig(path.with_suffix('.svg'),facecolor='white')
    plt.close(fig)

def frame(title,subtitle):
    fig=plt.figure(figsize=(9.2,7.3),facecolor='white')
    fig.text(.075,.944,title,fontsize=22,fontweight='bold',va='top')
    fig.text(.075,.886,subtitle,fontsize=12,color='#637d8c')
    ax=fig.add_axes([.135,.23,.80,.59])
    ax.tick_params(labelsize=10,length=3)
    ax.grid(color='#e3ebf0',lw=.65,zorder=0)
    ax.set_axisbelow(True)
    return fig,ax

def footer(fig,lines,handles=None):
    if handles is None:
        handles=[Line2D([],[],marker='o',color='none',markerfacecolor=TX,markeredgecolor='white',markersize=9,label='Tx 测量点'),
                 Line2D([],[],marker='s',color='none',markerfacecolor=RX,markeredgecolor='white',markersize=9,label='Rx 固定接收机')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.53,.105),ncol=len(handles),frameon=False,fontsize=11)
    for i,line in enumerate(lines):fig.text(.075,.095-i*.031,line,fontsize=10,color='#647d8a',va='top')

def receiver(ax,xy,offset=(10,0),coords=False):
    ax.scatter([xy[0]],[xy[1]],s=110,marker='s',c=RX,edgecolors='white',linewidths=1.6,zorder=6)
    label='Rx'+(f' ({xy[0]:g}, {xy[1]:g})' if coords else '')
    ax.annotate(label,xy,xytext=offset,textcoords='offset points',ha='left',va='center',fontsize=11,color=RX,fontweight='bold')

def scene1():
    s=GEOMETRY['scenarios']['sc1']
    fig,ax=frame('SC1  开放大厅','当前 16 个测量点，4 × 4 网格；定向与准全向批次使用相同点位')
    ax.add_patch(Rectangle((0,0),28,28.8,fc='#f7fafb',ec='#9db2bf',lw=1.5,zorder=0))
    ax.set(xlim=(-.8,29),ylim=(30,-.8),xlabel='x / m（向东）',ylabel='y / m（向南）')
    ax.set_aspect('equal',adjustable='box')
    ax.set_xticks([0,3.85,10.2,16.69,22.83,28]);ax.set_yticks([0,9.2,15.2,21.2,27.2,28.8])
    for p in s['points']:
        x,y=p['tx'][:2]
        ax.scatter([x],[y],s=66,c=TX,edgecolors='white',linewidths=1.1,zorder=5)
        ax.annotate(p['point_label'],(x,y),xytext=(0,10),textcoords='offset points',ha='center',va='bottom',fontsize=10)
    receiver(ax,s['rx'][:2],coords=True)
    footer(fig,['房间尺寸 28 × 28.8 m；Tx / Rx 高度均为 1.5 m。',
                'P01–P16 对应原始位置 2–17；原始位置 1 为系统校准，不画为空间测量点。'])
    save(fig,ROOT/'report/sc1-layout')

def scene2():
    s=GEOMETRY['scenarios']['sc2']
    fig,ax=frame('SC2  狭窄走廊','当前 11 个测量点；Tx / Rx 均位于 x = 0.85 m')
    ax.add_patch(Rectangle((0,0),2,70,fc=LIGHT,ec='#9db2bf',lw=1.4,zorder=0))
    ax.plot([.85,.85],[3.2,59.9],color='#c4d4de',lw=1.1,ls='--',zorder=1)
    ax.set(xlim=(-.9,10),ylim=(72,-2),xlabel='x / m（横向放大示意）',ylabel='y / m（向南）')
    ax.set_xticks([0,.85,2]);ax.set_yticks([0,10,20,30,40,50,60,70])
    for p in s['points']:
        x,y=p['tx'][:2]
        ax.scatter([x],[y],s=62,c=TX,edgecolors='white',linewidths=1.2,zorder=5)
        ax.plot([x+.12,2.6],[y,y],color='#bacdd5',lw=.7)
        ax.text(2.85,y,f"{p['point_label']}    y = {y:g} m",fontsize=11,va='center')
    ax.scatter([.85],[3.2],s=100,marker='s',c=RX,edgecolors='white',linewidths=1.5,zorder=6)
    ax.text(2.85,3.2,'Rx (0.85, 3.20)',va='center',fontsize=11,color=RX,fontweight='bold')
    ax.text(1,-1.1,'宽 2 m',ha='center',va='bottom',fontsize=10,color='#637d8c')
    footer(fig,['走廊长约 70 m、宽 2 m；横向放大以便查看，坐标数值采用实际测量定义。',
                'P01–P11 对应原始位置 2–12；Tx / Rx 高度均为 1.5 m。'])
    save(fig,ROOT/'report/sc2-layout')

def scene3():
    s=GEOMETRY['scenarios']['sc3']
    fig,ax=frame('SC3  L 型走廊','16 个测量点：7 个 LOS，9 个 NLOS；保留报告的 x / y 方向定义')
    # In this scene the original x axis points south and y points east.
    ax.plot([19,1,1],[14.8,14.8,32.8],color='#e6eef3',lw=25,solid_capstyle='butt',solid_joinstyle='miter',zorder=0)
    ax.plot([19,1,1],[14.8,14.8,32.8],color='#c2d0d9',lw=1,ls='--',zorder=1)
    ax.set(xlim=(-1,21),ylim=(34.8,12),xlabel='y / m（向东）',ylabel='x / m（向南）')
    ax.set_aspect('equal',adjustable='box')
    ax.set_xticks([0,5,10,15,20]);ax.set_yticks([14.8,18.8,22.8,26.8,30.8,34.8])
    for p in s['points']:
        x,y=p['tx'][:2];color=TX if p['condition']=='LOS' else NLOS
        ax.scatter([y],[x],s=57,c=color,edgecolors='white',linewidths=1.1,zorder=5)
        offset=(0,12) if p['condition']=='LOS' else (12,0)
        ax.annotate(p['point_label'],(y,x),xytext=offset,textcoords='offset points',ha='center' if p['condition']=='LOS' else 'left',
                    va='center',fontsize=9.5,color=color)
    ax.scatter([19],[14.8],s=90,marker='s',c=RX,edgecolors='white',linewidths=1.3,zorder=6)
    ax.annotate('Rx',(19,14.8),xytext=(0,12),textcoords='offset points',ha='center',fontsize=11,color=RX,fontweight='bold')
    ax.text(8,23,'P01–P07：LOS\nP08–P16：NLOS',fontsize=13,linespacing=1.8,color=INK)
    ax.text(8,29,'Rx 原始坐标\n(x, y) = (14.8, 19) m',fontsize=11,linespacing=1.7,color='#637d8c')
    handles=[Line2D([],[],marker='o',color='none',markerfacecolor=TX,markersize=7,label='LOS 测量点'),
             Line2D([],[],marker='o',color='none',markerfacecolor=NLOS,markersize=7,label='NLOS 测量点'),
             Line2D([],[],marker='s',color='none',markerfacecolor=RX,markersize=7,label='固定 Rx')]
    footer(fig,['点位按原始坐标绘制；灰带仅表示通道，宽度为示意。Tx / Rx 高度均为 1.5 m。',
                'NLOS 沿走廊距离 20–36 m 单独记录，不与三维直线距离混用。'],handles)
    save(fig,ROOT/'report/sc3-layout')

def scene4():
    s=GEOMETRY['scenarios']['sc4']
    fig,ax=frame('SC4  室内实验室','9 个实际测量点，3 × 3 网格；二维坐标与两个批次的距离表一致')
    ax.set(xlim=(0,10.2),ylim=(14,0),xlabel='x / m',ylabel='y / m')
    ax.set_aspect('equal',adjustable='box')
    ax.set_xticks([0,2.02,5.22,8.5]);ax.set_yticks([0,1.24,5.45,9.2,12.6])
    for p in s['points']:
        x,y=p['tx'][:2]
        ax.scatter([x],[y],s=74,c=TX,edgecolors='white',linewidths=1.2,zorder=5)
        ax.annotate(p['point_label'],(x,y),xytext=(0,-13),textcoords='offset points',ha='center',va='top',fontsize=11)
    receiver(ax,s['rx'][:2],coords=True)
    footer(fig,['Tx x = 2.02、5.22、8.50 m；Tx y = 5.45、9.20、12.60 m。',
                'P01–P09 按行编号，对应原始位置 2–10；天线高度未核实，仅显示二维坐标。',
                '只画收发点位，不补造家具、遮挡物或房间边界。'])
    save(fig,ROOT/'report/sc4-layout')

def read_numeric(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        return [{k:float(v) for k,v in row.items()} for row in csv.DictReader(stream)]

def pattern(antenna,title,note):
    records=read_numeric(ROOT/f'antenna/data/{antenna}-pattern.csv')
    angle=np.array([r['angle_deg'] for r in records])
    assert np.all(np.diff(angle)>0) and angle.min()==-100 and angle.max()==100
    dense=np.linspace(-100,100,801)
    fig,ax=frame(title,'E 面与 H 面的方向图截面；曲线来自既有图片数字化数据')
    for key,label,color,style in [('e_plane_gain_dbi','E 面',RX,'-'),('h_plane_gain_dbi','H 面',TX,'--')]:
        gain=np.array([r[key] for r in records])
        ax.plot(dense,PchipInterpolator(angle,gain)(dense),color=color,lw=2,label=label,ls=style)
        ax.plot(angle,gain,'o',color=color,ms=3,alpha=.65)
    ax.set(xlim=(-100,100),xlabel='截面角度 / °',ylabel='增益 / dBi')
    ax.legend(loc='lower center',ncol=2,frameon=False)
    fig.text(.075,.105,note,fontsize=10,color='#647d8a')
    fig.text(.075,.065,'只展示源数据覆盖的 −100° 至 100°，不补画未提供的角度或三维方向图。',fontsize=10,color='#647d8a')
    save(fig,ROOT/f'antenna/{antenna}-pattern')

def gains(full=False):
    native=ROOT/'antenna/data'
    d=read_numeric(native/'directional-gain-native.csv')
    q=read_numeric(native/'quasi-omni-gain-processing-grid.csv')
    title='天线峰值增益随频率变化' if not full else '天线增益曲线的原始频率覆盖范围'
    fig,ax=frame(title,'后处理采用的增益曲线；增益单位 dBi，频率单位 GHz')
    for rows,label,color in [(d,'定向天线',RX),(q,'准全向天线',TX)]:
        ax.plot([r['frequency_ghz'] for r in rows],[r['gain_dbi'] for r in rows],color=color,lw=2,label=label)
    ax.plot([r['frequency_ghz'] for r in d],[r['gain_dbi'] for r in d],'o',color=RX,ms=4)
    if full:
        ax.axvspan(6,7.5,color='#dcecf6',alpha=.5,label='本次测量 6–7.5 GHz')
        ax.set_xlim(3,8.2)
    else:
        ax.axvspan(6.425,7.125,color='#dcecf6',alpha=.5,label='目标频带 6.425–7.125 GHz')
        ax.set_xlim(6,7.5)
    ax.set(xlabel='频率 / GHz',ylabel='增益 / dBi')
    ax.legend(loc='center left',frameon=True,facecolor='white',edgecolor='#dce6ed')
    fig.text(.075,.105,'定向：配置中的厂家曲线结点。准全向：既有 G_ant_golden 处理曲线。',fontsize=10,color='#647d8a')
    fig.text(.075,.065,'准全向频率轴沿用原处理映射；3,001 点结果为线性插值，不作为新的逐频实测值。',fontsize=10,color='#647d8a')
    save(fig,ROOT/('antenna/gain-full-range' if full else 'antenna/gain-measurement-band'))

def main():
    scene1();scene2();scene3();scene4()
    pattern('directional','定向天线方向图','源图频率 6.89 GHz；旧资料转用于 6.775 GHz 比较，保留该转用说明。')
    pattern('quasi-omni','准全向天线方向图','既有资料标称比较频率 6.775 GHz；数值为图片数字化近似。')
    gains();gains(full=True)
    print('Rendered 4 scene maps and 4 antenna figures as PNG + SVG.')

if __name__=='__main__':main()
