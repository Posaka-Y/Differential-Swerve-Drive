# 駆動V2 独立電気監査 — 2026-09-26

> 監査後ユーザー確認: J6逆順はケーブル都合による意図した配列。R13=33k/R14=22kも次回調達・実装値として確定。下記の2点の未確認判定は解消し、V2資料へ反映。回路/ZIPは元から一致しており変更不要。C620外部終端等は引き続き未確認。

対象: `hardware/unit-board-v2/` の保存済み回路図（2026-09-25 22:55）とPCB（監査開始時2026-09-26 16:05）。元データを編集せず、KiCad XML netlistを `tmp/pdfs/unit_v2_latest_2026-09-26.xml` へ独立出力して照合した。DRC・全pad/copper接続照合・製造出力は別担当。以下は回路図ネットの確認であり、実機動作の保証ではない。

## 合格項目

| ブロック | 実際のRef/pin/netと照合結果 |
|---|---|
| MCU電源 | U4 STM32G474RET6: VBAT1、VDD16/32/48/64=`/VTREF_3V3`、VSS15/31/47/63とVSSA27=GND。ネット名VTREFでもLDO U2 OUTと同じデジタル3.3Vレールで、アナログVREF+とは分離されている。 |
| アナログ電源 | U4 VDDA29=`VDDA_A`、FB1 BLM18AG601SN1D経由3.3V、C13 100nF＋C11 1uF。VREF+28=`VREF_PLUS`、R2 0ΩでVDDAへ、C12 10nF＋C14 1uF。 |
| MCUデカップリング | C5/C6/C7/C8/C9各100nFがデジタル3.3V/GND、C10 4.7uFが同レール。各VDD/VBATの個別容量数を満たす。物理的な近接と帰路はPCB担当の確認対象。 |
| Reset/Boot | U4 PG10/NRST7→C15 100nF/GNDとJ8-10。PB8/BOOT0 pin61→R4 10k/GND。HSEはPF0 pin5、PF1 pin6、Y1 FC3BAEBDI8.0-T1の発振端子1/3、ケース2/4=GND、R3 0ΩとC3/C4 10pFを使用。 |
| 保護5V/3.3V | U1 LM66100: pin1=入力5V、2=GND、3 CEと6 VOUT=保護5V。U2 TLV76133DCYR:1 GND、2 OUT=3.3V、3 IN=保護5V。SOT-223 tabもpad2。 |
| 中央CAN | U3 TCAN1051VDRQ1:1 TXD→U4 PA12 pin46、4 RXD→PA11 pin45、2/8=GND、3 VCC=保護5V、5 VIO=3.3V、7 CANH=`COMM_A`、6 CANL=`COMM_B`。C1/C2各100nF、D1 ESD2CAN24 pins1/2=バス、3=GND。J2/J3とも1=A、2=B、3=GND。R1 120Ω＋SW1を持つ。 |
| C620 CAN | U5:1 TXD→U4 PB13 pin35、4 RXD→PB12 pin34、2/8=GND、3 VCC=保護5V、5 VIO=3.3V、7=H、6=L。C17/C18各100nF、D2 TVS pins1/2=H/L、3=GND。J4/J5とも1=H、2=L、3=GND。 |
| SWD/UART | 現在のSWDは **J8** Samtec FTSH-105-01-L-DV-K-P。1=デジタル3.3V、2=SWDIO→U4-49、3/5/9=GND、4=SWCLK→U4-50、6=SWO→U4-56、7/8=NC、10=NRST→U4-7。J9:1 GND、2 TX→U4 PA2-14、3 RX→PA3-17。SWDのPCB側DNPは電気ネット不良でなく組立属性の不一致として別途修正する。 |
| 5Vクランプ接続 | D7 BAT54S-HF:1 GND、2 3.3V、3 ADC→U4 PA0-12。C16 10nF→GND。上下レールへのseries Schottky clamp接続を保持。 |
| 主要footprint銅箔 | PCB内U1 SOT-363、D2/D7 SOT-23、SW3 DIP、J6 GH6についてpad番号・局所座標・寸法をKiCad10標準と比較し一致。library mismatch警告をpad形状不良と混同しない。 |

MCUのピン位置は[ST STM32G474RE datasheet](https://www.st.com/resource/en/datasheet/stm32g474re.pdf)、CANのV suffix/VIO/SとSOIC pin配列は[TI TCAN1051 datasheet](https://www.ti.com/lit/ds/symlink/tcan1051-q1.pdf)、LM66100 CE→VOUTのreverse-current接続は[TI LM66100 datasheet](https://www.ti.com/lit/ds/symlink/lm66100.pdf)、LDO配列は[TI TLV761 datasheet](https://www.ti.com/lit/gpn/tlv761)と照合した。Comchip BAT54S-HFのメーカー一次資料URLは現サイトへリダイレクトするため、正式採用品のseries pin配列と標準pad一致までの確認とし、購入現物の型番/markingは実装前確認事項。

## 確定した資料・組立条件の不一致

1. **5V監視定数:** 回路図はR13 `RC0603FR-0733KL 33k`（5V側）、R14 `RC0603FR-0722KL 22k`（GND側）。現要件/9月21日部品選定の22k/10kと異なる。実回路の分圧率は0.4、5Vで2.000V、5.5Vで2.200V、換算倍率2.5。22k/10kなら率0.3125、5Vで1.5625V、倍率3.2。どちらも通常5V監視として動作し得るが、BOM・実装値・ファーム換算を同じ側へ統一する。元データを推測で変更していない。部品選定書下部にも旧33k/22kの計算文が残り、内部矛盾がある。
2. **AMT22基板側配列:** J6実ネットは **1=CS、2=MISO、3=GND、4=MOSI、5=SCLK、6=5V**。R18/R17/R16/R15各0Ωを介しU4 PD2-55/PC11-53/PC12-54/PC10-52へ接続。現CARRIER要件のGH表、および[Same Sky AMT22 sensor datasheet](https://www.sameskydevices.com/product/resource/amt22.pdf)のセンサ配列1=5V、2=SCLK、3=MOSI、4=GND、5=MISO、6=CSとは逆順。基板とセンサ間の変換ハーネスを逆番号で正しく結線するなら成立するが、「ストレート結線」の旧資料のままでは誤配線する。ユーザーの意図と変換ハーネス対応表を確認してからReleaseとする。GH嵌合面/基板面の見かけの左右反転と実pad番号を混同しない。

## 未確認・Release前に区別する項目

- **C620物理終端:** 今回のnetlistにはC620バス終端R/SWの新追加なし。基板不備とは断定しない。`C620①─駆動基板─C620②` の物理両端へ外部120Ωがあるなら中央の駆動基板へ追加終端は不要。C620内蔵/外部終端と実ハーネスを未測定。電源OFFで両端のみ終端、H-L間約60Ω、片側約120Ωを確認する。
- **SWDケーブル嵌合:** Samtec -K notchとactual cable/adapterのpin1視点、pin7 blocked-holeの有無、STDC14→MIPI10変換を機構照合する。10pinの電気配列だけで付属ケーブルとの互換を断定しない。
- **部品/起動評価:** LM66100 ST pin5は未使用NC（TIは未使用時GNDを推奨）、HSE負荷容量/drive level、LDO温度/容量実効値、購入現物のMPN/方向は実機段階で確認。未使用open-drain STはこの監査で確定した機能不良とは判定しない。
- GPIO/SPI/CAN電気配列は一致するが、実測・CSS/HSI fallback・SPI待ち時間・ファーム5V換算・GND帰路をこのread-only netlist監査だけで合格にしない。

**判定:** MCU電源/Reset/CAN/SPI信号のネット接続に新しい確定断線は検出していない。5V監視の採用定数とAMT22変換ハーネスを統一し、外部終端条件を確定するまで、製造ZIPは検討用/NOT_RELEASEDとして扱う。

## 2026-09-26 C620終端のユーザー確認

2個のGHポートから各ESCへ接続し、各ESCの120Ω終端をONにする構成で確定。ESC①―駆動基板―ESC②の両端終端なので、C620用の基板内終端なしは設計意図に一致し不具合ではない。J6逆順・33k/22k分圧・外部終端の3確認事項はすべて解消。回路/PCB/ZIPは変更不要。電気的ERC/DRCエラー・未接続は0。残るライブラリ/シルク/実装属性・ケーブル機構確認を、この構成確認だけで合格に変更しない。
