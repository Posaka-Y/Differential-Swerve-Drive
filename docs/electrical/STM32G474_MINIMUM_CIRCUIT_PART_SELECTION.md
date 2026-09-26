# STM32G474最小構成 部品選定

## 適用範囲

差動ステアユニット基板x3で使用する`STM32G474RET6`のHSE、電源デカップリング、VDDA/VREF+フィルタを対象とする。
オドメトリ基板は2026-07-25に`STM32F405RGT6`へ変更したため本書のMCU最小回路は適用せず、採用品の流用範囲だけ
`STM32F405_ODOMETRY_PIN_ASSIGNMENT.md`に従う。NRST、BOOT0、SWD/UARTコネクタは各基板要件の既決定を使う。

正本はSTの[STM32G474REデータシート DS12288 Rev.6](https://www.st.com/resource/en/datasheet/stm32g474re.pdf)、[AN5093 STM32G4 hardware development](https://www.st.com/resource/en/application_note/an5093-getting-started-with-stm32g4-series--hardware-development-boards-stmicroelectronics.pdf)、[AN2867 oscillator design guide](https://www.st.com/resource/en/application_note/an2867-guidelines-for-oscillator-design-on-stm8afals-and-stm32-mcusmpus-stmicroelectronics.pdf)とする。

## 正式採用品

| 用途 | 採用品 | 仕様/パッケージ | 備考 |
|---|---|---|---|
| 8MHz HSE | `FC3BAEBDI8.0-T1` | 8MHz、CL=8pF、ESR max 500Ω、±20ppm、−40～125℃、AEC-Q200、3225-4pad | 2026-09-06 DigiKey在庫品へ変更 |
| HSE負荷容量 | `GRM1885C1H100JA01D` x2 | 10pF、C0G、±5%、50V、0603 | 初期実装値。8.2pF/12pF同一0603を調整候補にする |
| VDDAフェライト | `BLM18AG601SN1D` | 600Ω@100MHz、500mA、DCR max 0.38Ω、0603、−55～125℃ | Murata Active、広く流通 |
| 100nFデカップリング | `GRM188R71A104KA01D` | 100nF、X7R、10V、±10%、0603 | 各VDD/VSS対、VDDAに使用 |
| 1uFデカップリング | `C1608X7R1E105K080AB` | 1uF、X7R、25V、±10%、0603 | VDDAおよびVREF+に使用。2026-09-06在庫確認 |
| VREF+高周波容量 | `C1608C0G1H103J080AA` | 10nF、C0G、50V、±5%、0603 | VREF+ピン直近。2026-09-06在庫確認 |
| VDDバルク | `GRM21BR71A475KA73L` | 4.7uF、X7R、10V、±10%、0805 | ST推奨の4.7uF。基板の3.3V入口付近に1個 |
| VREF+接続 | `RC0603JR-070RL` | 0Ω、0603 | `VDDA_A`とVREF+を接続。将来外部基準を使う場合に外せる |
| NRST容量 | `GRM188R71H104KA93D` | 100nF、X7R、50V、0603 | NRST-GND間。外付けpull-upは置かない |
| BOOT0 pull-down | `RC0603FR-0710KL` | 10kΩ、±1%、0603 | PB8/BOOT0の既定Low |
| 5V監視分圧 | `RC0603FR-0722KL` / `RC0603FR-0710KL` | 22kΩ(5V側)/10kΩ(GND側)、±1%、0603 | `PWR_5V`を0.3125倍してPA0へ入力。2026-09-21に33kΩ/22kΩ(0.4倍)から変更(33kΩ現物なし) |
| ADCフィルタ | `GRM188R71H103KA01D` | 10nF、X7R、50V、0603 | PA0-GND、分圧抵抗と約1.2kHz LPF |
| ADCクランプ | Comchip `BAT54S-HF` | dual series Schottky、30V、200mA、SOT-23 | onsemi/Diotec品欠品のため2026-09-07変更。PA0をGND/3V3へクランプ |
| 電源LED | `LTST-C190KGKT` | 緑、0603 | 3V3存在表示、1kΩ直列 |
| 通信LED | `LTST-C190KSKT` | 黄、0603 | PB10 GPIO表示、1kΩ直列 |
| エラーLED | `LTST-C190KRKT` | 赤、0603 | PB11 GPIO表示、1kΩ直列 |
| LED抵抗 | `RC0603FR-071KL` | 1kΩ、±1%、0603 | 約1～1.3mA。高輝度LEDを低電流駆動 |
| 主要テストポイント | `S1751-46R` | Harwin SMT loop、3.25x1.63x2.0mm | 5V/3V3/GND/NRST/BOOT0/SWO等。リフロー対応 |

水晶メーカー資料: [ECS製品ページ](https://ecsxtal.com/products/crystals/surface-mount-crystals/ecs-80-8-33q-jes-tr/)。フェライト仕様: [Murata BLM18AG601SN1データシート](https://www.murata.com/en-us/api/pdfdownloadapi?cate=cgsubChipFerriBead&partno=BLM18AG601SN1%23)。

### 2026-07-25 DigiKey調達AVL

Rev.Aを4枚組み立てる購入BOMでは、電気仕様を変えずにDigiKeyで型番認識できる次の代替品を使用する。HSEとVREF+の容量はC0Gを維持し、ADCフィルタだけをX7Rとする。

| 用途/基板リファレンス | 調達品 | DigiKey品番 | 仕様 |
|---|---|---|---|
| HSE負荷 `C3,C4` | `CL10C100JB8NNNC` | `1276-1027-1-ND` | 10pF、C0G、±5%、50V、0603 |
| 100nF `C1,C2,C5-C9,C13,C15,C17,C18,C201,C203` | `C0603C104K5RACTU` | `399-C0603C104K5RACTUCT-ND` | 100nF、X7R、±10%、50V、0603 |
| VDDA/VREF+ `C11,C14` | `C1608X7R1E105K080AB` | `445-5956-1-ND` | 1uF、X7R、±10%、25V、0603。旧Taiyo Yuden品在庫0 |
| VREF+ `C12` | `C1608C0G1H103J080AA` | `445-7404-1-ND` | 10nF、C0G、±5%、50V、0603 |
| 3V3バルク `C10` | `GRM21BZ71E475KE15K` | `490-GRM21BZ71E475KE15KCT-ND` | 4.7uF、X7R、±10%、25V、0805 |
| ADCフィルタ `C16` | `GRM188R72A103KA01D` | `490-GRM188R72A103KA01DCT-ND` | 10nF、X7R、±10%、100V、0603 |

AVL品を別型番へ再置換する場合も、容量、誘電体、許容差、定格電圧、外形を同等以上とし、HSE負荷容量は実機評価なしに値を変えない。

## 回路

### HSE

```text
PF0/OSC_IN  ---+--- X1 ---+--- PF1/OSC_OUT
               |          |
             C_HSE1     C_HSE2
              10pF       10pF
               |          |
              GND        GND
```

- X1の金属ケース/GND padはGNDへ接続する。
- OSC_OUT側に直列抵抗用0603フットプリント`R_HSE`を設け、Rev.Aは0Ω実装または直結とする。水晶drive levelの実測で必要な場合だけ値を変更する。
- 8MHz設定はファームの`HSE_VALUE`、PLL入力、CSS設定と一致させる。

### 負荷容量

AN5093の式は次の通り。

```text
CL = C1*C2/(C1+C2) + Cstray
```

`C1=C2=10pF`、基板・ピン寄生を3pFと仮定すると、`CL=5pF+3pF=8pF`で水晶公称値と一致する。ただしAN5093は寄生容量を概ね2～7pFとしているため、10pFは計算上の初期値であって無条件の確定値ではない。PCB完成後に周波数偏差または専用測定手順で評価し、必要なら同一0603の8.2pF/12pFへ変更する。

### 発振余裕

DS12288のG474 HSEは4～48MHz、最大critical crystal transconductanceは1.5mA/V。AN2867に従い、採用水晶について次式を用いる。

```text
gmcrit = 4 * ESR * (2*pi*F)^2 * (C0+CL)^2
```

水晶シリーズのC0最大7pF、ESR最大500Ω、F=8MHz、CL=8pFのworst-caseでは`gmcrit ≈ 1.14mA/V`となり、1.5mA/V未満を満たす。余裕は大きくないため、C0/ESRの異なる代替水晶を型番だけで置換しない。量産前に複数温度・複数基板で起動確認し、drive levelはAN2867の測定法で確認する。

## 電源接続

| MCUピン | 接続 |
|---|---|
| VDD pin 16/32/48/64 | 3V3。各ピン対に100nFを1個ずつ、直近配置 |
| VSS pin 15/31/47/63 | 連続GND planeへ最短接続 |
| VBAT pin 1 | RTCバックアップ不要のRev.Aでは3V3へ接続し、100nFを直近配置 |
| VDDA pin 29 | 3V3 → `BLM18AG601SN1D` → `VDDA_A`。VDDA側に100nF+1uF |
| VSSA pin 27 | GNDへ接続。VDDAコンデンサの帰路をこの近傍へ落とす |
| VREF+ pin 28 | 0Ωで`VDDA_A`へ接続し、ピン直近に10nF+1uF |

3V3全体にはST推奨の4.7uFを1個置く。既存の10uFを追加してもよいが、4.7uFの代わりに遠いLDO出力コンデンサだけへ依存しない。

## Reset・BOOT0

### NRST

- PG10/NRSTから100nFをGNDへ接続し、MCU直近に置く。
- G474はNRSTに25～55kΩ相当の内部weak pull-upを持つため、外付け10kΩ pull-upは実装しない。
- NRSTはデバッグGH6 pin 4と`S1751-46R`テストポイントへ引き出す。
- 常設Resetボタンは載せない。組付け後はWeAct MiniDebuggerからhardware resetでき、部品点数と誤操作源を減らせる。必要性が出た場合は中央サービスパネルから扱う。

### BOOT0

- PB8/BOOT0を10kΩでGNDへpull-downし、通常起動を既定にする。
- BOOT0と3V3の`S1751-46R`を隣接配置する。ピンセットまたは短絡治具でBOOT0をHighに保持しながらNRSTを操作してROM bootloaderへ入る。
- 2.54mmジャンパは常設しない。BOOT0テストポイント周辺へ`BOOT`、`3V3`、通常状態`LOW`をシルク表示する。
- PB8はアプリケーションGPIOとして使用しない。

## 5V監視ADC

```text
PWR_5V --- 22k ---+--- PA0/ADC
                  |
                 10k
                  |
                 GND

PA0 --- 10nF --- GND
PA0 --- BAT54S clamp --- GND/3V3
```

- 分圧比は`22/(33+22)=0.4`。5.0Vで2.000V、5.5Vで2.200Vとなる。
- 理想換算は`PWR_5V = ADC_voltage * 2.5`。抵抗許容差、VDDA/VREF+、ADC gain/offsetを含め、基板ごとに実測係数をFlashへ保存できるようにする。
- Thevenin抵抗は13.2kΩ。10nFとのカットオフは約1.21kHz。高速波形観測用ではなく、電源低下・異常の診断用とする。
- ADCサンプリング時間は短い既定値を使わず、G474 ADCのsource impedance条件を満たす長さに設定する。複数回平均も行う。
- Comchip `BAT54S-HF`はpin 3をPA0、pin 1をGND、pin 2を3V3として上下クランプにする。KiCadシンボルのダイオード向きと公式pinoutを必ず照合する。
- この回路は保護後の基板内`PWR_5V`監視用であり、24V外部入力へ直接使用しない。

## 状態LED

| 表示 | 接続 | 意味 |
|---|---|---|
| PWR 緑 | 3V3 → 1kΩ → LED → GND | MCU用3.3Vの存在。ソフト正常を意味しない |
| COMM 黄 | PB10 → 1kΩ → LED → GND | 中央CAN通信。点滅方法はファームで定義 |
| ERR 赤 | PB11 → 1kΩ → LED → GND | ラッチ故障/診断異常 |

PA5はNUCLEO LD2互換の動作LEDとして残し、`LTST-C190KGKT`+1kΩを実装する。したがって基板上LEDはPWR、RUN(PA5)、COMM(PB10)、ERR(PB11)の4個とする。GPIO LEDは約1～1.3mAで、GPIO駆動余裕と夜間視認性を両立する。シルクは色ではなく`PWR/RUN/COMM/ERR`を表示する。

## テストポイント

- クリップやフックを掛けたい主要ネットは、テープ&リール供給・260℃リフロー対応の`S1751-46R`を使う。
- 最低実装: `PWR_5V_IN`、`PWR_5V`、`3V3`、`VDDA_A`、GND x2、NRST、BOOT0、SWO、COMM_A、COMM_B、C620_CAN_H、C620_CAN_L。
- 高密度デジタル信号とADC入力は、実装部品を増やさず直径1.0～1.5mmの露出銅テストパッドでもよい。プローブ用途をBOM/シルクで区別する。
- GNDテストポイントを測定対象の近くに置き、長いワニ口GNDだけに依存しない。

## 配置・配線制約

1. 水晶とC_HSE1/C_HSE2をPF0/PF1と同じ面、MCU直近に置く。信号をビアへ通さない。
2. PF0/PF1から水晶までを短く、互いに近い長さにし、CAN、SPI、PWM、クロック、LED配線を近づけない。
3. 水晶領域をGNDガードで囲み、ガードは最寄りMCU GNDへ接続する。発振信号直下には他信号を通さない。GND planeの切断方法はAN2867に合わせ、帰路を長くしない。
4. 100nFは対応するVDD/VSSピン対へ最短ループで置く。「MCU周辺に4個」ではなく各電源ピンに割り当てる。
5. VDDAフェライトは3V3 planeとの境界に置き、フェライト後の`VDDA_A`島へデジタル負荷を接続しない。
6. VDDA/VREF+コンデンサのGND側をCANやLEDの大電流帰路と共有する細い配線にしない。
7. フェライト両側を大容量コンデンサで挟んだ共振が問題になる場合に備え、VDDAノイズとADC値を実機観測する。部品追加を推測だけで行わない。
8. LEDは基板端または上から見える列に並べるが、水晶・VDDA・ADC入力から離す。
9. 5V分圧と10nFをPA0近くへ置き、CAN/LEDの帰還電流がADCのGND帰路へ流れ込まないようにする。

## KiCad/ERC上の注意

- 3225-4pad水晶の信号pad/GND pad番号をECS推奨ランドと照合する。汎用`Crystal_GND24`シンボルを使う場合もpin番号を盲信しない。
- `VDDA_A`とVREF+の0Ωを明示し、ERC上でVREF+を未給電にしない。
- 各VDD、VDDA、VREF+、VBATに電源フラグを適切に置き、実際の給電経路と一致させる。
- 100nF x4、VBAT 100nF、VDDA 100nF+1uF、VREF+ 10nF+1uF、全体4.7uFをBOM/ERCレビューで個数照合する。

## 実機確認

- 常温だけでなく、想定最低/最高基板温度で電源投入を繰り返し、HSE ready失敗がない。
- CSSでHSE異常時に安全停止し、HSIフォールバック後にモータ出力が勝手に再開しない。
- MCOまたはタイマ出力で周波数偏差を測定し、負荷容量の妥当性を確認する。OSC_IN/OUTへ通常の低容量でないオシロプローブを直接当てない。
- CAN 1Mbps連続通信、C620駆動、LEDスイッチング中にADC値とVDDA/VREF+ノイズを確認する。
- LDO最大負荷時にもVDDAがデータシート範囲内にあり、VDDとの電位差条件を満たす。
