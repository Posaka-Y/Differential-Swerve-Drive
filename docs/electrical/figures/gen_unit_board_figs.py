# -*- coding: utf-8 -*-
"""
Unit board reference schematics (schemdraw SVG rendering).
Source of truth: docs/electrical/UNIT_BOARD_SCHEMATIC_REFERENCE.md Section 3.
Generated: 2026-07-20
"""
import os
import matplotlib
from matplotlib import font_manager

# Japanese-capable font (text is converted to paths in SVG: svg.fonttype default 'path')
FONT = 'sans-serif'
for fam in ['Yu Gothic', 'Meiryo', 'MS Gothic']:
    try:
        font_manager.findfont(fam, fallback_to_default=False)
        matplotlib.rcParams['font.family'] = [fam, 'sans-serif']
        FONT = fam
        print('using font', fam)
        break
    except Exception:
        continue

import schemdraw
import schemdraw.elements as elm

FIGDIR = os.path.dirname(os.path.abspath(__file__))

NOTE_KW = dict(fontsize=9, color='#444444')


def note(d, xy, text, halign='left'):
    d.add(elm.Label().at(xy).label(text, loc='right' if halign == 'left' else 'left',
                                   halign=halign, valign='top', **NOTE_KW))


def netlabel(d, xy, text, loc='top'):
    d.add(elm.Dot(open=True).at(xy).label(text, loc=loc, fontsize=10))


def save(d, name):
    d.save(os.path.join(FIGDIR, name + '.svg'))
    if os.environ.get('GEN_FIGS_PNG'):
        d.save(os.path.join(FIGDIR, name + '.png'), dpi=130)
    print('saved', name)


# =====================================================================
# Block 1: power chain
# =====================================================================
def block1():
    d = schemdraw.Drawing(show=False)
    d.config(fontsize=10, font=FONT)
    d.add(elm.Label().at((0, 2.2)).label(
        'Block 1: 電源チェーン  (J101 → LM66100 → PWR_5V → TLV1117LV33 → 3V3)',
        loc='right', halign='left', fontsize=12))

    j101 = d.add(elm.Ic(pins=[
        elm.IcPin(name='1', side='right', slot='2/2', anchorname='p1'),
        elm.IcPin(name='2', side='right', slot='1/2', anchorname='p2')],
        size=(1.2, 2.2)).at((0, 0)).anchor('p1').label('J101\nSM02B-GHS-TB\n(GH2 横挿し)', loc='top', fontsize=9))

    # pin2 -> GND
    d.add(elm.Line().at(j101.p2).right().length(0.8))
    d.add(elm.Ground())
    note(d, (0.4, -3.0), 'ハーネス側 GND_CTRL = 基板内 GND')

    # pin1 -> PWR_5V_IN
    d.add(elm.Line().at(j101.p1).right().length(2.2).label('PWR_5V_IN', loc='top'))
    din = d.add(elm.Dot())
    d.add(elm.Capacitor().at(din.center).down().length(1.8).label('C101\n2.2uF以上', loc='bottom', fontsize=9))
    d.add(elm.Ground())
    d.add(elm.Line().at(din.center).right().length(1.0))

    u101 = d.add(elm.Ic(pins=[
        elm.IcPin(name='VIN', side='left', slot='3/3'),
        elm.IcPin(name='ST', side='left', slot='1/3'),
        elm.IcPin(name='VOUT', side='right', slot='3/3'),
        elm.IcPin(name='CE_N', side='right', slot='2/3', anchorname='CEN'),
        elm.IcPin(name='GND', side='bottom', anchorname='gnd')],
        size=(2.6, 2.6)).anchor('VIN').label('U101\nLM66100DCKR', loc='top', fontsize=9))

    # ST open
    d.add(elm.Line().at(u101.ST).left().length(0.5).label('open', loc='left', fontsize=8))
    # GND
    d.add(elm.Line().at(u101.gnd).down().length(0.5))
    d.add(elm.Ground())
    # VOUT -> PWR_5V rail
    d.add(elm.Line().at(u101.VOUT).right().length(1.6))
    dv = d.add(elm.Dot())
    # CE_N tied to VOUT
    d.add(elm.Wire('-|').at(u101.CEN).to(dv.center))
    note(d, (7.2, -1.3), 'CE_N=VOUT 接続は意図的\n(RPP+RCB、TI DS 8.3節)\n標準アプリ図(CE_N=GND)と異なる')

    d.add(elm.Line().at(dv.center).right().length(1.2).label('PWR_5V', loc='top'))
    dc1 = d.add(elm.Dot())
    d.add(elm.Capacitor().at(dc1.center).down().length(1.8).label('C201\n100nF', loc='bottom', fontsize=9))
    d.add(elm.Ground())
    d.add(elm.Line().at(dc1.center).right().length(1.2))
    dc2 = d.add(elm.Dot())
    d.add(elm.Capacitor().at(dc2.center).down().length(1.8).label('C202\n10uF', loc='bottom', fontsize=9))
    d.add(elm.Ground())
    d.add(elm.Line().at(dc2.center).right().length(1.0))

    u201 = d.add(elm.Ic(pins=[
        elm.IcPin(name='IN', side='left', slot='2/2'),
        elm.IcPin(name='OUT+tab', side='right', slot='2/2', anchorname='OUT'),
        elm.IcPin(name='GND', side='bottom', anchorname='gnd')],
        size=(2.8, 2.2)).anchor('IN').label('U201\nTLV1117LV33DCYR', loc='top', fontsize=9))
    d.add(elm.Line().at(u201.gnd).down().length(0.5))
    d.add(elm.Ground())
    note(d, (14.4, -2.6), 'タブ=VOUT!\nGNDベタへ放熱接続すると3.3V短絡')

    d.add(elm.Line().at(u201.OUT).right().length(1.2))
    dc3 = d.add(elm.Dot())
    d.add(elm.Capacitor().at(dc3.center).down().length(1.8).label('C203\n100nF', loc='bottom', fontsize=9))
    d.add(elm.Ground())
    d.add(elm.Line().at(dc3.center).right().length(1.2))
    dc4 = d.add(elm.Dot())
    d.add(elm.Capacitor().at(dc4.center).down().length(1.8).label('C204\n10uF', loc='bottom', fontsize=9))
    d.add(elm.Ground())
    d.add(elm.Line().at(dc4.center).right().length(1.0))
    netlabel(d, d.here, '3V3', loc='right')

    note(d, (0.0, -4.6),
         '予備降圧 U102 (OKI-78SR-5互換FP, 通常未実装DNP+バイパスジャンパ) は本図では省略。\n'
         'LM66100 / TLV1117LV33 のピン番号は正本に記載なし → データシート照合のうえ転記(未確定 6章#4,#5)。')
    save(d, 'unit-board-block1')


# =====================================================================
# Block 2: CAN interface
# =====================================================================
def block2():
    d = schemdraw.Drawing(show=False)
    d.config(fontsize=10, font=FONT)
    d.add(elm.Label().at((-4, 3.2)).label(
        'Block 2: CANブロック (中央CAN=400番台。C620側=500番台は同一回路)',
        loc='right', halign='left', fontsize=12))

    u401 = d.add(elm.Ic(pins=[
        elm.IcPin(name='TXD', pin='1', side='left', slot='9/9'),
        elm.IcPin(name='RXD', pin='4', side='left', slot='7/9'),
        elm.IcPin(name='VCC', pin='3', side='left', slot='5/9'),
        elm.IcPin(name='VIO', pin='5', side='left', slot='3/9'),
        elm.IcPin(name='GND', pin='2', side='left', slot='1/9', anchorname='gnd'),
        elm.IcPin(name='CANH', pin='7', side='right', slot='9/9'),
        elm.IcPin(name='CANL', pin='6', side='right', slot='7/9'),
        elm.IcPin(name='S', pin='8', side='right', slot='1/9', anchorname='S')],
        size=(3.0, 5.4)).at((0, 0)).anchor('TXD').label('U401\nTCAN1051VDRQ1\n(SOIC-8)', loc='top', fontsize=9))

    # MCU side
    d.add(elm.Line(arrow='->').at((-3.5, 0)).to(u401.TXD).label('COMM_TX', loc='top', fontsize=9))
    netlabel(d, (-3.5, 0), 'U301 PA12\n(FDCAN1_TX)', loc='left')
    ry = u401.RXD.y
    d.add(elm.Line(arrow='->').at(u401.RXD).to((-3.5, ry)).label('COMM_RX', loc='top', fontsize=9))
    netlabel(d, (-3.5, ry), 'U301 PA11\n(FDCAN1_RX)', loc='left')

    # VCC (5V) + C401
    vy = u401.VCC.y
    d.add(elm.Line().at(u401.VCC).to((-2.6, vy)))
    dvcc = d.add(elm.Dot().at((-1.6, vy)))
    netlabel(d, (-2.6, vy), 'PWR_5V', loc='left')
    d.add(elm.Capacitor().at(dvcc.center).down().length(1.4).label('C401\n100nF', loc='bottom', fontsize=8))
    d.add(elm.Ground())
    # VIO (3V3) + C402
    wy = u401.VIO.y
    d.add(elm.Line().at(u401.VIO).to((-3.6, wy)))
    dvio = d.add(elm.Dot().at((-2.8, wy)))
    netlabel(d, (-3.6, wy), '3V3', loc='left')
    d.add(elm.Capacitor().at(dvio.center).down().length(1.4).label('C402\n100nF', loc='bottom', fontsize=8))
    d.add(elm.Ground())
    note(d, (-4.9, wy - 2.6), 'VIO=3V3固定\n(NC/5V禁止)')
    # GND
    d.add(elm.Line().at(u401.gnd).left().length(0.7))
    d.add(elm.Ground())
    # S pin -> GND
    d.add(elm.Line().at(u401.S).right().length(0.7))
    d.add(elm.Ground())
    note(d, (3.4, u401.S.y - 1.6), 'S=GND固定 (Normal mode、フロート禁止)')

    # bus lines (label on first short segment to avoid collisions)
    hy = u401.CANH.y     # y of COMM_A
    ly = u401.CANL.y     # y of COMM_B
    hx0 = u401.CANH.x
    lx0 = u401.CANL.x
    d.add(elm.Line().at(u401.CANH).right().length(2.0).label('COMM_A', loc='top', fontsize=10))
    d.add(elm.Line().right().length(10.0))
    hx_end = hx0 + 12.0
    d.add(elm.Line().at(u401.CANL).right().length(2.0).label('COMM_B', loc='top', fontsize=10))
    d.add(elm.Line().right().length(9.0))
    lx_end = lx0 + 11.0

    ax_term = hx0 + 3.0    # termination x
    ax_esd = hx0 + 7.0     # ESD x (electrically parallel; physically nearest connector)
    ax_br = hx0 + 9.6      # J402 branch x

    # termination: COMM_A --120R-- SW common, one throw -> COMM_B
    # (vertical drop from COMM_A crosses COMM_B without a junction dot)
    dta = d.add(elm.Dot().at((ax_term, hy)))
    d.add(elm.Line().at(dta.center).down().length(2.0))
    d.add(elm.Resistor().down().length(2.2).label('R401\n120Ω', loc='bottom', fontsize=9))
    sw = d.add(elm.SwitchSpdt().at(d.here).theta(-90).anchor('a'))
    d.add(elm.Label().at((ax_term - 0.6, hy - 4.9)).label(
        'SW401\nJS102011SAQN\nシルク TERM ON/OFF', loc='left', halign='right', fontsize=8))
    dtb = d.add(elm.Dot().at((ax_term + 1.4, ly)))
    d.add(elm.Wire('|-').at(sw.c).to(dtb.center))
    d.add(elm.Label().at(sw.b).label('NC', loc='bottom', fontsize=8, ofst=(-0.3, -0.2)))
    note(d, (ax_term - 3.0, ly - 6.4), '終端: COMM_A—120Ω—SW—COMM_B\nCommonと片throwのみ使用。バス物理両端のみTERM ON')

    # ESD D401 (pins 1,2 top / 3 bottom)
    esd = d.add(elm.Ic(pins=[
        elm.IcPin(name='2', side='top', slot='1/2', anchorname='t2'),
        elm.IcPin(name='1', side='top', slot='2/2', anchorname='t1')],
        size=(1.8, 1.0)).at((ax_esd, ly - 2.4)).anchor('center').theta(0))
    d.add(elm.Dot().at((esd.t1.x, hy)))
    d.add(elm.Line().at(esd.t1).to((esd.t1.x, hy)))
    d.add(elm.Dot().at((esd.t2.x, ly)))
    d.add(elm.Line().at(esd.t2).to((esd.t2.x, ly)))
    # pin 3 (bottom) to GND
    ebot = (ax_esd, ly - 2.9)
    d.add(elm.Line().at(ebot).down().length(0.6).label('3', loc='right', fontsize=8))
    d.add(elm.Ground())
    d.add(elm.Label().at((ax_esd, ly - 4.3)).label('D401 ESD2CAN24DBZRQ1', loc='bottom', fontsize=8))
    note(d, (ax_esd - 2.2, ly - 5.4), '配置順: コネクタ → TVS(D401) → トランシーバ\n(D401はコネクタ直近、スタブ20mm以下)')

    # J401 (end of bus) / J402 (branch, parallel pass-through)
    j401 = d.add(elm.Ic(pins=[
        elm.IcPin(name='1', side='left', slot='3/3', anchorname='p1'),
        elm.IcPin(name='2', side='left', slot='2/3', anchorname='p2'),
        elm.IcPin(name='3', side='left', slot='1/3', anchorname='p3')],
        size=(1.4, 2.4)).at((hx_end + 1.6, hy)).anchor('p1').theta(0)
        .label('J401\nSM03B-GHS-TB', loc='top', fontsize=9))
    d.add(elm.Line().at((hx_end, hy)).to(j401.p1))
    d.add(elm.Wire('|-').at((lx_end, ly)).to(j401.p2))
    d.add(elm.Line().at(j401.p3).left().length(0.4))
    d.add(elm.Ground())

    j402 = d.add(elm.Ic(pins=[
        elm.IcPin(name='1', side='left', slot='3/3', anchorname='p1'),
        elm.IcPin(name='2', side='left', slot='2/3', anchorname='p2'),
        elm.IcPin(name='3', side='left', slot='1/3', anchorname='p3')],
        size=(1.4, 2.4)).at((hx_end + 1.6, hy - 5.2)).anchor('p1').theta(0)
        .label('J402\nSM03B-GHS-TB', loc='top', fontsize=9))
    da = d.add(elm.Dot().at((ax_br, hy)))
    d.add(elm.Wire('|-').at(da.center).to(j402.p1))
    db = d.add(elm.Dot().at((ax_br + 0.6, ly)))
    d.add(elm.Wire('|-').at(db.center).to(j402.p2))
    d.add(elm.Line().at(j402.p3).left().length(0.4))
    d.add(elm.Ground())
    note(d, (hx_end + 0.2, hy - 8.4), 'J401/J402はIN/OUT区別なく並列直結(パススルー)。\nGND(3番)は省略しない')

    note(d, (-4.9, ly - 7.6),
         'C620側 (U501/D501/R501/SW501): 同一回路。C620_CAN_TX=PB13(FDCAN2_TX)、C620_CAN_RX=PB12(FDCAN2_RX)、\n'
         '外部ネット名 C620_CAN_H/L。コネクタ型番・個数・ピン順は未確定(正本6章#1)のため描いていない。')
    save(d, 'unit-board-block2')


# =====================================================================
# Block 3: MCU power / decoupling
# =====================================================================
def block3():
    d = schemdraw.Drawing(show=False)
    d.config(fontsize=10, font=FONT)
    d.add(elm.Label().at((-6, 2.0)).label(
        'Block 3: MCU電源・デカップリング (U301 STM32G474RET6, LQFP64)',
        loc='right', halign='left', fontsize=12))

    u301 = d.add(elm.Ic(pins=[
        elm.IcPin(name='VBAT', pin='1', side='left', slot='6/6'),
        elm.IcPin(name='VDD', pin='16', side='left', slot='5/6', anchorname='VDD16'),
        elm.IcPin(name='VDD', pin='32', side='left', slot='4/6', anchorname='VDD32'),
        elm.IcPin(name='VDD', pin='48', side='left', slot='3/6', anchorname='VDD48'),
        elm.IcPin(name='VDD', pin='64', side='left', slot='2/6', anchorname='VDD64'),
        elm.IcPin(name='VSS', pin='15/31/47/63', side='left', slot='1/6', anchorname='VSS'),
        elm.IcPin(name='VDDA', pin='29', side='right', slot='6/6'),
        elm.IcPin(name='VREF+', pin='28', side='right', slot='4/6', anchorname='VREFP'),
        elm.IcPin(name='VSSA', pin='27', side='right', slot='2/6', anchorname='VSSA')],
        size=(4.2, 11.0)).at((0, 0)).anchor('VBAT').label('U301\nSTM32G474RET6', loc='top', fontsize=10))

    railx = -5.2
    capx = -2.2
    # 3V3 rail
    ytop = u301.VBAT.y + 1.0
    ybot = u301.VDD64.y
    netlabel(d, (railx, ytop), '3V3', loc='top')
    d.add(elm.Line().at((railx, ytop)).to((railx, ybot)))
    # bulk C310
    dbulk = d.add(elm.Dot().at((railx, ytop - 0.5)))
    d.add(elm.Capacitor().at(dbulk.center).left().length(1.6).label('C310 4.7uF\n(バルク)', loc='bottom', fontsize=9))
    d.add(elm.Ground())

    for pname, cap in [('VBAT', 'C305\n100nF'), ('VDD16', 'C301\n100nF'),
                       ('VDD32', 'C302\n100nF'), ('VDD48', 'C303\n100nF'),
                       ('VDD64', 'C304\n100nF')]:
        p = getattr(u301, pname)
        if pname != 'VDD64':
            d.add(elm.Dot().at((railx, p.y)))
        d.add(elm.Line().at((railx, p.y)).to(p))
        dc = d.add(elm.Dot().at((capx, p.y)))
        d.add(elm.Capacitor().at(dc.center).down().length(1.3).label(cap, loc='bottom', fontsize=8))
        d.add(elm.Ground())
    note(d, (railx - 1.0, ybot - 1.2), '100nFは各VDDピン対に1個ずつ\n(VBATにも100nF)')
    # VSS
    d.add(elm.Line().at(u301.VSS).left().length(0.8))
    d.add(elm.Ground())

    # VDDA island
    ay = u301.VDDA.y
    d.add(elm.Line().at(u301.VDDA).right().length(3.4).label('VDDA_A', loc='top', fontsize=10))
    dfb = d.add(elm.Dot())
    fb = d.add(elm.Inductor().at(dfb.center).right().length(2.2).label('FB301\nBLM18AG601SN1D', loc='top', fontsize=8))
    d.add(elm.Line().at(fb.end).right().length(0.8))
    netlabel(d, d.here, '3V3', loc='right')
    dca = d.add(elm.Dot().at((u301.VDDA.x + 1.2, ay)))
    d.add(elm.Capacitor().at(dca.center).down().length(1.4).label('C306\n100nF', loc='bottom', fontsize=8))
    d.add(elm.Ground())
    dcb = d.add(elm.Dot().at((u301.VDDA.x + 2.4, ay)))
    d.add(elm.Capacitor().at(dcb.center).down().length(1.4).label('C307\n1uF', loc='bottom', fontsize=8))
    d.add(elm.Ground())

    # VREF+ from VDDA_A through R301
    ry = u301.VREFP.y
    d.add(elm.Line().at(u301.VREFP).right().length(3.4).label('VREF+', loc='top', fontsize=10))
    drr = d.add(elm.Dot())
    d.add(elm.Resistor().at(drr.center).up().toy(ay).label('R301 0Ω', loc='bottom', fontsize=8))
    d.add(elm.Dot())
    dr1 = d.add(elm.Dot().at((u301.VREFP.x + 1.2, ry)))
    d.add(elm.Capacitor().at(dr1.center).down().length(1.4).label('C308\n10nF', loc='bottom', fontsize=8))
    d.add(elm.Ground())
    dr2 = d.add(elm.Dot().at((u301.VREFP.x + 2.4, ry)))
    d.add(elm.Capacitor().at(dr2.center).down().length(1.4).label('C309\n1uF', loc='bottom', fontsize=8))
    d.add(elm.Ground())
    note(d, (u301.VREFP.x + 4.2, ry + 0.3), '0Ωは将来の外部基準用に\n明示部品とする')

    # VSSA
    d.add(elm.Line().at(u301.VSSA).right().length(0.8))
    d.add(elm.Ground())
    note(d, (u301.VSSA.x + 1.6, u301.VSSA.y + 0.2), 'VDDA/VREF+系コンデンサの帰路は\nVSSA(27)近傍へ')

    save(d, 'unit-board-block3')


# =====================================================================
# Block 4: HSE + NRST + BOOT0
# =====================================================================
def block4():
    d = schemdraw.Drawing(show=False)
    d.config(fontsize=10, font=FONT)
    d.add(elm.Label().at((0, 2.4)).label(
        'Block 4: HSE水晶・NRST・BOOT0', loc='right', halign='left', fontsize=12))

    # --- HSE ---
    netlabel(d, (0, 0), 'U301\nPF0-OSC_IN', loc='left')
    d.add(elm.Line().at((0, 0)).right().length(1.2))
    dx1 = d.add(elm.Dot())
    d.add(elm.Capacitor().at(dx1.center).down().length(1.6).label('C311\n10pF C0G', loc='bottom', fontsize=8))
    d.add(elm.Ground())
    xt = d.add(elm.Crystal().at(dx1.center).right().length(2.2).label('X301\nECS-80-8-33Q', loc='top', fontsize=9))
    dx2 = d.add(elm.Dot().at(xt.end))
    d.add(elm.Capacitor().at(dx2.center).down().length(1.6).label('C312\n10pF C0G', loc='bottom', fontsize=8))
    d.add(elm.Ground())
    d.add(elm.Resistor().at(dx2.center).right().length(2.4).label('R302 (R_HSE)\n0Ω初期', loc='top', fontsize=9))
    d.add(elm.Line().right().length(0.8))
    netlabel(d, d.here, 'U301\nPF1-OSC_OUT', loc='right')
    note(d, (0.2, -2.6),
         '水晶ケース/GNDパッド→GND。3225-4padのpad番号は\n汎用シンボルと一致するとは限らない → ECS図面照合(未確定 6章#6)')

    # --- NRST ---
    y2 = -5.2
    netlabel(d, (0, y2), 'U301 PG10-NRST (pin 7)', loc='left')
    d.add(elm.Line().at((0, y2)).right().length(1.6))
    dn = d.add(elm.Dot())
    d.add(elm.Capacitor().at(dn.center).down().length(1.6).label('C313\n100nF', loc='bottom', fontsize=8))
    d.add(elm.Ground())
    d.add(elm.Line().at(dn.center).right().length(1.8))
    netlabel(d, d.here, 'NRST → J701-4, TP', loc='right')
    note(d, (0.2, y2 - 2.6), '外付けプルアップ無し(内部pull-up使用、意図的)')

    # --- BOOT0 ---
    x3 = 9.0
    netlabel(d, (x3, y2), 'U301 PB8-BOOT0', loc='left')
    d.add(elm.Line().at((x3, y2)).right().length(1.6))
    db = d.add(elm.Dot())
    d.add(elm.Resistor().at(db.center).down().length(2.0).label('R303\n10kΩ', loc='bottom', fontsize=8))
    d.add(elm.Ground())
    d.add(elm.Line().at(db.center).right().length(1.8))
    netlabel(d, d.here, 'TP(BOOT0)+隣接TP(3V3)', loc='right')
    note(d, (x3 + 0.2, y2 - 3.0), 'pull-down。PB8はGPIOに使わない')

    save(d, 'unit-board-block4')


# =====================================================================
# Block 5: 5V monitor ADC
# =====================================================================
def block5():
    d = schemdraw.Drawing(show=False)
    d.config(fontsize=10, font=FONT)
    d.add(elm.Label().at((0, 3.6)).label(
        'Block 5: 5V監視ADC (PA0)', loc='right', halign='left', fontsize=12))

    netlabel(d, (0, 0), 'PWR_5V', loc='left')
    d.add(elm.Resistor().at((0, 0)).right().length(2.4).label('R304 33kΩ', loc='top', fontsize=9))
    dm = d.add(elm.Dot())
    d.add(elm.Resistor().at(dm.center).down().length(2.2).label('R305\n22kΩ', loc='bottom', fontsize=9))
    d.add(elm.Ground())
    d.add(elm.Line().at(dm.center).right().length(1.6).label('ADC_5V_MON', loc='top', fontsize=10))
    dc = d.add(elm.Dot())
    d.add(elm.Capacitor().at(dc.center).down().length(2.2).label('C314\n10nF', loc='bottom', fontsize=9))
    d.add(elm.Ground())
    note(d, (dc.center.x - 0.6, -3.2), '約1.2kHz LPF')
    d.add(elm.Line().at(dc.center).right().length(1.8))
    dd = d.add(elm.Dot())
    d.add(elm.Line().at(dd.center).right().length(1.8))
    netlabel(d, d.here, 'U301 PA0 (ADC)\nmax 2.2V (0.4倍)', loc='right')

    # BAT54S: pin1=GND, pin2=3V3, pin3=PA0
    x = dd.center.x
    d1 = d.add(elm.Schottky().at((x, 0)).up().length(1.8).label('', loc='top'))
    d.add(elm.Line().up().length(0.4))
    netlabel(d, d.here, '3V3', loc='top')
    d2 = d.add(elm.Schottky().at((x, -2.2)).up().length(1.8))
    # Keep the lower diode visibly separate from the junction label area, then
    # explicitly wire its cathode to the ADC node.  Without this short wire the
    # generated SVG leaves a 0.4-unit open circuit in the GND clamp path.
    d.add(elm.Line().at(d2.end).to(dd.center))
    d.add(elm.Ground().at((x, -2.2)))
    d.add(elm.Label().at((x + 0.25, 1.4)).label('2', loc='right', fontsize=8))
    d.add(elm.Label().at((x + 0.25, 0.1)).label('3', loc='right', fontsize=8))
    d.add(elm.Label().at((x + 0.25, -1.9)).label('1', loc='right', fontsize=8))
    note(d, (x + 1.6, -1.0),
         'D301 BAT54SLT1G (直列2素子)\npin1=GND / pin2=3V3 / pin3=PA0\n上下クランプ。内部ダイオード向きを\nデータシート図と必ず照合')
    note(d, (0, -4.4), '5V系がADCへ入る唯一の点。サンプリング時間は\nソースインピーダンス13.2kΩに合わせる(ファーム)')
    save(d, 'unit-board-block5')


# =====================================================================
# Block 6: AMT22 SPI + debug + ID DIP + LEDs
# =====================================================================
def block6():
    d = schemdraw.Drawing(show=False)
    d.config(fontsize=10, font=FONT)
    d.add(elm.Label().at((0, 2.2)).label(
        'Block 6: AMT22 SPI中継・デバッグ・ユニットID・状態LED', loc='right', halign='left', fontsize=12))

    # ---- J601 AMT22 ----
    j601 = d.add(elm.Ic(pins=[
        elm.IcPin(name='+5V', pin='1', side='right', slot='6/6', anchorname='p1'),
        elm.IcPin(name='SCLK', pin='2', side='right', slot='5/6', anchorname='p2'),
        elm.IcPin(name='MOSI', pin='3', side='right', slot='4/6', anchorname='p3'),
        elm.IcPin(name='GND', pin='4', side='right', slot='3/6', anchorname='p4'),
        elm.IcPin(name='MISO', pin='5', side='right', slot='2/6', anchorname='p5'),
        elm.IcPin(name='CS', pin='6', side='right', slot='1/6', anchorname='p6')],
        size=(2.2, 5.6)).at((0, 0)).anchor('p1')
        .label('J601\nSM06B-GHS-TB\n(AMT22中継/横挿し)', loc='top', fontsize=9))

    d.add(elm.Line().at(j601.p1).right().length(4.6))
    netlabel(d, d.here, 'PWR_5V', loc='right')
    d.add(elm.Resistor().at(j601.p2).right().length(2.6).label('R601', loc='top', fontsize=8))
    d.add(elm.Line().right().length(2.0))
    netlabel(d, d.here, 'SPI3_SCK (U301 PC10)', loc='right')
    d.add(elm.Resistor().at(j601.p3).right().length(2.6).label('R602', loc='top', fontsize=8))
    d.add(elm.Line().right().length(2.0))
    netlabel(d, d.here, 'SPI3_MOSI (U301 PC12)', loc='right')
    d.add(elm.Line().at(j601.p4).right().length(0.4))
    d.add(elm.Ground())
    d.add(elm.Resistor().at(j601.p5).right().length(2.6).label('R603', loc='top', fontsize=8))
    d.add(elm.Line().right().length(2.0))
    netlabel(d, d.here, 'SPI3_MISO (U301 PC11)', loc='right')
    d.add(elm.Resistor().at(j601.p6).right().length(2.6).label('R604', loc='top', fontsize=8))
    d.add(elm.Line().right().length(2.0))
    netlabel(d, d.here, 'AMT22_CS_N (U301 PD2, ソフトCS)', loc='right')
    note(d, (0, -6.6),
         'AMT22と同ピン順=ストレート結線。R601-604は0603フットプリントのみ確定、\n'
         '値は未確定(初期0Ω実装が候補、正本6章#3)。5V電源・3.3V論理で直結成立')

    # ---- J701 debug ----
    xj = 13.5
    j701 = d.add(elm.Ic(pins=[
        elm.IcPin(name='GND', pin='1', side='right', slot='6/6', anchorname='p1'),
        elm.IcPin(name='SWCLK', pin='2', side='right', slot='5/6', anchorname='p2'),
        elm.IcPin(name='SWDIO', pin='3', side='right', slot='4/6', anchorname='p3'),
        elm.IcPin(name='NRST', pin='4', side='right', slot='3/6', anchorname='p4'),
        elm.IcPin(name='DBG_TX', pin='5', side='right', slot='2/6', anchorname='p5'),
        elm.IcPin(name='DBG_RX', pin='6', side='right', slot='1/6', anchorname='p6')],
        size=(2.4, 5.6)).at((xj, 0)).anchor('p1')
        .label('J701\nBM06B-GHS-TBT\n(デバッグ/上挿し)', loc='top', fontsize=9))
    d.add(elm.Line().at(j701.p1).right().length(0.8))
    d.add(elm.Ground())
    for pin, name in [('p2', 'SWCLK (U301 PA14)'), ('p3', 'SWDIO (U301 PA13)'),
                      ('p4', 'NRST (U301 PG10 pin7)'),
                      ('p5', 'DBG_TX (U301 PA2, LPUART1_TX)'),
                      ('p6', 'DBG_RX (U301 PA3, LPUART1_RX)')]:
        d.add(elm.Line().at(getattr(j701, pin)).right().length(1.6))
        netlabel(d, d.here, name, loc='right')
    note(d, (xj, -6.6),
         'DBG_TX/RX方向は「基板視点TX/RX」の推測=未確定(正本6章#7)。\n'
         'WeActデバッガ側と照合のこと。J701に電源ピン無し=デバッガ給電を\n'
         '基板へ入れない(意図的)。PA13/PA14はSWD専用')

    # ---- SW701 ID DIP ----
    ys = -10.0
    sw = d.add(elm.Ic(pins=[
        elm.IcPin(name='bit0', side='right', slot='3/3', anchorname='b0'),
        elm.IcPin(name='bit1', side='right', slot='2/3', anchorname='b1'),
        elm.IcPin(name='bit2', side='right', slot='1/3', anchorname='b2'),
        elm.IcPin(name='com', side='left', slot='2/3', anchorname='com')],
        size=(2.0, 3.0)).at((0, ys)).anchor('b0')
        .label('SW701 3bit DIP\n(型番未確定 6章#2)', loc='top', fontsize=9))
    d.add(elm.Line().at(sw.com).left().length(0.8))
    d.add(elm.Ground())
    for pin, name in [('b0', 'UNIT_ID0 (U301 PC6)'), ('b1', 'UNIT_ID1 (U301 PC7)'),
                      ('b2', 'UNIT_ID2 (U301 PC8)')]:
        d.add(elm.Line().at(getattr(sw, pin)).right().length(1.6))
        netlabel(d, d.here, name, loc='right')
    note(d, (0, ys - 3.2), '内部プルアップ、ON=GND短絡\n→ ON=Low、ファームで読み値反転')

    # ---- LEDs ----
    xl = 10.5
    rows = [('3V3 (常時点灯)', 'R701\n1kΩ', 'D701 PWR 緑'),
            ('LED_RUN (U301 PA5)', 'R702\n1kΩ', 'D702 RUN 緑'),
            ('LED_COMM (U301 PB10)', 'R703\n1kΩ', 'D703 COMM 黄'),
            ('LED_ERR (U301 PB11)', 'R704\n1kΩ', 'D704 ERR 赤')]
    for i, (src, rr, dd) in enumerate(rows):
        y = ys + 1.2 - i * 1.9
        netlabel(d, (xl, y), src, loc='left')
        d.add(elm.Resistor().at((xl, y)).right().length(2.2).label(rr, loc='top', fontsize=8))
        d.add(elm.LED().right().length(2.0).label(dd, loc='top', fontsize=8))
        d.add(elm.Line().right().length(0.6))
        d.add(elm.Ground())
    note(d, (xl, ys - 7.0), 'LED_RUNは起動時ID回数点滅に使用')

    save(d, 'unit-board-block6')


if __name__ == '__main__':
    block1()
    block2()
    block3()
    block4()
    block5()
    block6()
    print('done')
