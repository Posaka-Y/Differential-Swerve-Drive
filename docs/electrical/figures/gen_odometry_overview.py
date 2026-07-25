# -*- coding: utf-8 -*-
"""
Odometry board zone/block overview diagram (schemdraw SVG rendering).
Source of truth: docs/electrical/ODOMETRY_BOARD_SCHEMATIC_REFERENCE.md
  Section "1枚上の配置" / "RefDes割当" / "ブロック接続".
Generated: 2026-07-25

Box + arrow + net-name level only (no IC pin layout, no R/C values).
"""
import os
import matplotlib
from matplotlib import font_manager

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
from schemdraw.elements import Rect

FIGDIR = os.path.dirname(os.path.abspath(__file__))

BOX_KW = dict(lw=1.3)


def box(d, xy, w, h, title, body='', title_size=11, body_size=9):
    x, y = xy
    d.add(Rect(corner1=(x, y), corner2=(x + w, y + h), **BOX_KW))
    d.add(elm.Label().at((x + w / 2, y + h - 0.35)).label(
        title, halign='center', valign='top', fontsize=title_size))
    if body:
        d.add(elm.Label().at((x + w / 2, y + h - 0.9)).label(
            body, halign='center', valign='top', fontsize=body_size, color='#333333'))
    return (x, y, w, h)


def arrow(d, p1, p2, label='', loc='top', fontsize=9, color='black'):
    d.add(elm.Arrow().at(p1).to(p2).color(color).label(label, loc=loc, fontsize=fontsize))


def main():
    d = schemdraw.Drawing(show=False)
    d.config(fontsize=10, font=FONT)

    d.add(elm.Label().at((0, 15.6)).label(
        'オドメトリ基板(STM32F405RGT6) ゾーン/ブロック概観図 — '
        'ODOMETRY_BOARD_SCHEMATIC_REFERENCE.md 準拠(簡易版・ピン配置/定数は省略)',
        loc='right', halign='left', fontsize=12))

    # ---------------- Top row: power chain -> CAN (100/200/300/400台) ----------------
    top_y = 12.6
    b_pwr = box(d, (0, top_y), 3.4, 2.2, 'J101 5V入力\n逆接/逆流保護', '100番台\nLM66100')
    b_ldo = box(d, (4.6, top_y), 3.4, 2.2, '3.3V LDO', '200番台\nTLV1117LV33')
    b_can = box(d, (16.4, top_y), 3.6, 2.2, 'センサーCAN', '400番台\nTCAN1051V')

    # ---------------- Mid row: Debug | MCU | IMU (700/300/600台) ----------------
    mid_y = 8.4
    b_dbg = box(d, (0, mid_y), 3.4, 2.6, 'Debug/BOOT/\nID/LED', '700番台\nSWD, UNIT_ID, LED x3')
    b_mcu = box(d, (7.4, mid_y - 0.3), 5.6, 3.2, 'STM32F405RGT6', '300番台\nF405最小回路(HSE/NRST/\nVDDA/VCAP)')
    b_imu = box(d, (16.4, mid_y), 3.6, 2.6, 'ICM-42688-P', '600番台\nSPI3 IMU')

    # ---------------- Bottom row: AMT102 x3 (500台) ----------------
    bot_y = 4.2
    b_w1 = box(d, (0, bot_y), 3.6, 2.4, 'AMT102\nWheel 1', 'J501/D501/U501\nR511-512')
    b_w2 = box(d, (5.4, bot_y), 3.6, 2.4, 'AMT102\nWheel 2', 'J502/D502/U502\nR513-514')
    b_w3 = box(d, (10.8, bot_y), 3.6, 2.4, 'AMT102\nWheel 3', 'J503/D503/U503\nR515-516')

    # ================= Arrows: power flow (top row, left to right) =================
    # Drawn below the box bottoms (y < top_y) so the label never overlaps box body text.
    arrow(d, (3.4, top_y - 0.6), (4.6, top_y - 0.6), 'PWR_5V_IN→PWR_5V')

    # PWR_5V continues right along the top to CAN transceiver VCC, and down into
    # the encoder buffers; drawn as a bus line rather than one arrow per box.
    d.add(elm.Line().at((8.0, top_y + 1.1)).right().to((16.4, top_y + 1.1)))
    d.add(elm.Label().at((12.0, top_y + 1.3)).label('PWR_5V (CAN VCC, AMT102 VCC)', fontsize=9, halign='center'))

    # 3V3 rail drop from LDO box down to MCU / Debug / IMU / CAN VIO
    d.add(elm.Line().at((6.3, top_y)).down().to((6.3, mid_y + 2.9)))
    d.add(elm.Line().at((6.3, mid_y + 2.9)).right().to((7.4, mid_y + 2.9)))
    d.add(elm.Label().at((6.3, mid_y + 3.3)).label('3V3', fontsize=9, halign='center'))

    # ================= Arrows: mid row signal connections =================
    arrow(d, (3.4, mid_y + 1.3), (7.4, mid_y + 1.3), 'SWCLK/SWDIO/NRST\nDBG_TX/RX, UNIT_ID0-2\nLED_RUN/COMM/ERR', fontsize=8)
    arrow(d, (13.0, mid_y + 1.3), (16.4, mid_y + 1.3), 'SPI3_SCK/MISO/MOSI\nIMU_CS_N, IMU_INT1/2', fontsize=8)
    arrow(d, (13.0, top_y + 0.3), (16.4, top_y + 0.3), 'COMM_TX/COMM_RX', fontsize=8)

    # ================= Arrows: bottom row encoders up into MCU =================
    for bx, label in [((1.8, bot_y + 2.4), 'W1_A/W1_B\n(TIM2)'),
                       ((7.2, bot_y + 2.4), 'W2_A/W2_B\n(TIM3)'),
                       ((12.6, bot_y + 2.4), 'W3_A/W3_B\n(TIM4)')]:
        arrow(d, bx, (bx[0], mid_y - 0.3), label, loc='right', fontsize=8)

    # ================= External connectors / net legend =================
    d.add(elm.Label().at((0, 1.6)).label(
        'COMM_A/COMM_B: J401↔J402 完全並列パススルー(センサーCAN)。'
        '電源: PWR_5V_IN→PWR_5V→3V3。GNDは全ブロック共通。',
        halign='left', fontsize=9, color='#444444'))
    d.add(elm.Label().at((0, 1.1)).label(
        '詳細ピン割当・部品定数は STM32F405_ODOMETRY_PIN_ASSIGNMENT.md /'
        ' ODOMETRY_BOARD_SCHEMATIC_REFERENCE.md を参照。',
        halign='left', fontsize=9, color='#444444'))

    d.save(os.path.join(FIGDIR, 'odometry-board-overview.svg'))
    if os.environ.get('GEN_FIGS_PNG'):
        d.save(os.path.join(FIGDIR, 'odometry-board-overview.png'), dpi=130)
    print('saved odometry-board-overview.svg')


if __name__ == '__main__':
    main()
