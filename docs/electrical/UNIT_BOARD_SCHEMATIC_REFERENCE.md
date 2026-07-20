# ユニット基板 回路図作成リファレンス(KiCad転記用)

作成日: 2026-07-20。対象: 差動ステアユニット基板 Rev.A(STM32G474RET6 LQFP64)。

この文書は、人間がKiCad GUIで回路図を作成するための転記用集約資料である。内容は以下の正本から集約したものであり、**矛盾がある場合は正本側が優先する**(`回路仕様.md`という単独ファイルは存在しないため、下記4本を仕様として扱った)。

- `CARRIER_BOARD_REQUIREMENTS.md`(ピン割当・外部IF・部品リスト)
- `STM32G474_MINIMUM_CIRCUIT_PART_SELECTION.md`(MCU最小構成)
- `POWER_5V_COMMON_BLOCK_PART_SELECTION.md`(電源)
- `CAN_COMMON_BLOCK_PART_SELECTION.md`(CAN)

凡例: ピン番号欄の`-`は「正本に番号の記載がなく、KiCadシンボル/データシートで転記時に照合すること」を意味する。**推測**と明記した箇所以外は正本記載事項。

---

## 1. 機能ブロック分割(階層シート案)

| シート名 | 内容 | インスタンス数 |
|---|---|---|
| `power_input_5v` | GH2入力、LM66100逆接/逆流保護、予備降圧フットプリント | 1 |
| `power_3v3` | TLV1117LV33 LDO、入出力コンデンサ | 1 |
| `mcu_min_g474` | G474RET6、デカップリング、HSE、NRST、BOOT0、VDDA/VREF+、5V監視ADC | 1 |
| `can_interface` | TCAN1051V+ESD+終端SW+GHコネクタ | 2(中央CAN / C620 CAN) |
| `amt22_spi` | AMT22中継GH6、SPI直列抵抗フットプリント | 1 |
| `debug_id_led` | デバッグGH6、ID DIPスイッチ、状態LED4個、テストポイント | 1 |

- `can_interface`はシートを1枚描いて2回インスタンス化する(階層ピン: `CAN_TX`、`CAN_RX`、`CAN_H`、`CAN_L`、電源)。中央CAN側はコネクタ2個(パススルー)、C620側はコネクタ構成が未確定(→6章)のため、コネクタだけシート外(ルート)に置く構成でもよい。
- ルートシートは配線を持たず、階層シートと基板外形コメントだけを置く。

## 2. 配置案

### ルートシートの並び(左→右=電源・信号の流れ)

```text
[power_input_5v] → [power_3v3] → [mcu_min_g474] → [can_interface x2]
                                       ↓
                          [amt22_spi] [debug_id_led]
```

### 各シート内の配置方針

- **power_input_5v**: 左端にJ1(GH2)、右へLM66100、右端で`PWR_5V`をシート出力。予備降圧(OKI-78SR互換、通常未実装)は下段に置きDNP明記。
- **power_3v3**: 左から`PWR_5V`入力→入力C→TLV1117→出力C→右端`3V3`出力。
- **mcu_min_g474**: 中央にU1(MCU)。左に電源系(デカップリング列・VDDA/VREF+フィルタ)、左下にHSE、右下にNRST/BOOT0、上に5V監視ADC。デカップリングコンデンサは「VDDピン番号を備考に書いて」1列に並べてよい(物理配置はPCBで行うため、回路図は個数と対応の明示を優先)。
- **can_interface**: 左からMCU側(TXD/RXD)→トランシーバ→ESD→終端→右端コネクタ。信号方向: TXD=MCU→トランシーバ、RXD=トランシーバ→MCU。
- **amt22_spi / debug_id_led**: 左にMCU側ネットラベル、右にコネクタ。

### ネットラベル/電源記号の方針

- 電源レール(`PWR_5V_IN`、`PWR_5V`、`3V3`、`VDDA_A`、`GND`)は電源シンボル+PWR_FLAGで統一し、ワイヤで引き回さない。
- シート間信号は階層ピンで渡す: `COMM_TX/COMM_RX`(FDCAN1)、`C620_CAN_TX/C620_CAN_RX`(FDCAN2)、`SPI3_SCK/MISO/MOSI`、`AMT22_CS_N`、`UNIT_ID0/1/2`、`LED_RUN/COMM/ERR`、`DBG_TX/DBG_RX`、`SWCLK/SWDIO`、`NRST`、`ADC_5V_MON`。
- MCUシート内でも、MCUシンボルから各ピンは短いスタブ+ネットラベルとし、長距離ワイヤを描かない。
- 外部コネクタのバス側シルク名は`COMM_A/COMM_B`(`CAN_H/L`とは書かない。命名規約は`COMMUNICATION_NAMING_AND_IDS.md`)。

### リファレンス指定子(アノテーション提案)

シート別に100番台を分けると転記・レビューが楽(KiCadの階層アノテーションで設定可能)。

| シート | 範囲 | 主要例 |
|---|---|---|
| power_input_5v | 100番台 | J101(GH2)、U101(LM66100)、C101… |
| power_3v3 | 200番台 | U201(TLV1117)、C201… |
| mcu_min_g474 | 300番台 | U301(G474)、X301(水晶)、D301(BAT54S) |
| can_interface(中央) | 400番台 | U401、D401(ESD)、R401(120Ω)、SW401、J401/J402 |
| can_interface(C620) | 500番台 | U501、D501、R501、SW501、J501 |
| amt22_spi | 600番台 | J601(GH6)、R601-604 |
| debug_id_led | 700番台 | J701(GH6)、SW701(DIP)、D701-704(LED) |

## 3. 接続表

電圧欄: 論理=0-3.3V CMOS。バス=CANバス電位(TCAN1051Vはバスフォルト±58V耐性)。

### 3.1 電源入力・保護(power_input_5v)

| Net名 | 部品 | ピン名 | ピン番号 | 接続先部品 | 接続先ピン | 電圧 | 備考 |
|---|---|---|---|---|---|---|---|
| PWR_5V_IN | J101 `SM02B-GHS-TB` | 1 | 1 | U101 LM66100 | VIN | 5V(未保護) | 横挿しGH2。ハーネスAWG26 |
| GND | J101 | 2 | 2 | GNDプレーン | - | 0V | 正本名`GND_CTRL`はハーネス側名。基板内はGND |
| PWR_5V_IN | C101 2.2uF以上 | + | - | GND | - | 5V | LM66100 VIN直近 |
| PWR_5V | U101 LM66100 | VOUT | - | 全5V負荷 | - | 5V(保護後) | ピン番号はKiCad `Power_Management:LM66100DCK`(照合済みシンボル)に従い転記時確認 |
| PWR_5V | U101 | CE_N | - | U101 VOUT | - | 5V | **RPP+RCB構成(TIデータシート8.3節)。標準アプリ図(CE_N=GND)と意図的に異なる** |
| - | U101 | ST | - | 未接続 | - | - | オープンで使用 |
| GND | U101 | GND | - | GNDプレーン | - | 0V | |
| PWR_5V_IN | U102 OKI-78SR-5互換FP | VIN | - | (通常未実装) | - | - | 予備降圧。バイパスジャンパ付き、DNP。ピン配置はOKI-78SR図面照合 |

### 3.2 電源変換(power_3v3)

| Net名 | 部品 | ピン名 | ピン番号 | 接続先部品 | 接続先ピン | 電圧 | 備考 |
|---|---|---|---|---|---|---|---|
| PWR_5V | U201 `TLV1117LV33DCYR` | IN | - | PWR_5V | - | 5V | SOT-223。ピン番号はDS照合(1117系は品種でピン順が異なる例あり) |
| 3V3 | U201 | OUT + タブ | - | 3V3レール | - | 3.3V | **タブ=VOUT。GNDヒートシンク接続は誤り** |
| GND | U201 | GND | - | GNDプレーン | - | 0V | |
| PWR_5V | C201/C202 | 100nF + 10uF | - | GND | - | 5V | 入力側、X7R |
| 3V3 | C203/C204 | 100nF + 10uF | - | GND | - | 3.3V | 出力側、X7R。DC bias後もDS最小容量を満たす品 |

### 3.3 MCU最小構成(mcu_min_g474) — U301 = STM32G474RET6(LQFP64)

電源系(ピン番号は正本記載、DS12288照合済み):

| Net名 | 部品 | ピン名 | ピン番号 | 接続先部品 | 接続先ピン | 電圧 | 備考 |
|---|---|---|---|---|---|---|---|
| 3V3 | U301 | VDD | 16/32/48/64 | 3V3 | - | 3.3V | 各ピンに100nF 1個ずつ(C301-304) |
| GND | U301 | VSS | 15/31/47/63 | GND | - | 0V | |
| 3V3 | U301 | VBAT | 1 | 3V3 | - | 3.3V | RTC不使用。100nF直近(C305) |
| VDDA_A | U301 | VDDA | 29 | FB301 `BLM18AG601SN1D` | 3V3側 | 3.3V | フェライト後の島。100nF+1uF(C306/307) |
| GND | U301 | VSSA | 27 | GND | - | 0V | VDDA系コンデンサの帰路をこの近傍へ |
| VREF+ | U301 | VREF+ | 28 | R301 0Ω | VDDA_A側 | 3.3V | 10nF+1uF(C308/309)。0Ωは将来の外部基準用に明示部品とする |
| 3V3 | C310 4.7uF | - | - | GND | - | 3.3V | 3.3V全体バルク(0805) |

HSE・リセット・BOOT:

| Net名 | 部品 | ピン名 | ピン番号 | 接続先部品 | 接続先ピン | 電圧 | 備考 |
|---|---|---|---|---|---|---|---|
| OSC_IN | U301 | PF0-OSC_IN | - | X301 `ECS-80-8-33Q` | 信号pad | 発振 | 水晶の信号pad/GND pad番号はECS図面照合(→6章) |
| OSC_OUT | U301 | PF1-OSC_OUT | - | R302(R_HSE、0Ω初期) | - | 発振 | R302経由でX301へ。drive level実測用 |
| OSC_IN/OUT | C311/C312 10pF C0G | - | - | GND | - | - | 各信号-GND間 |
| GND | X301 | ケース/GND pad | - | GND | - | 0V | |
| NRST | U301 | PG10-NRST | 7 | C313 100nF | - | 3.3V | 内部pull-upのため外付けpull-up無し。J701-4とTPへも接続 |
| BOOT0 | U301 | PB8-BOOT0 | - | R303 10kΩ | GND側 | 3.3V | pull-down。TP(BOOT0)+隣接TP(3V3)。**PB8をGPIOに使わない** |

5V監視ADC:

| Net名 | 部品 | ピン名 | ピン番号 | 接続先部品 | 接続先ピン | 電圧 | 備考 |
|---|---|---|---|---|---|---|---|
| PWR_5V | R304 33kΩ | - | - | ADC_5V_MON | - | 5V→2V | 分圧上側 |
| ADC_5V_MON | R305 22kΩ | - | - | GND | - | max2.2V | 分圧下側。0.4倍 |
| ADC_5V_MON | U301 | PA0 | - | - | - | ADC | サンプリング時間はソースインピーダンス13.2kΩに合わせる(ファーム) |
| ADC_5V_MON | C314 10nF | - | - | GND | - | - | 約1.2kHz LPF |
| GND | D301 `BAT54SLT1G` | pin 1 | 1 | GND | - | - | 正本記載: 1=GND、2=3V3、3=PA0。**シンボルのダイオード向きをDSと必ず照合** |
| 3V3 | D301 | pin 2 | 2 | 3V3 | - | - | |
| ADC_5V_MON | D301 | pin 3 | 3 | PA0 | - | - | 上下クランプ |

### 3.4 CAN(can_interface、中央CAN=400番台/C620=500番台で同一回路)

| Net名 | 部品 | ピン名 | ピン番号 | 接続先部品 | 接続先ピン | 電圧 | 備考 |
|---|---|---|---|---|---|---|---|
| COMM_TX | U401 `TCAN1051VDRQ1` | TXD | 1 | U301 PA12(FDCAN1_TX) | - | 3.3V論理 | C620側: C620_CAN_TX=PB13(FDCAN2_TX) |
| GND | U401 | GND | 2 | GND | - | 0V | |
| PWR_5V | U401 | VCC | 3 | PWR_5V | - | **5V** | 100nF直近(C401) |
| COMM_RX | U401 | RXD | 4 | U301 PA11(FDCAN1_RX) | - | 3.3V論理 | C620側: C620_CAN_RX=PB12(FDCAN2_RX) |
| 3V3 | U401 | VIO | 5 | 3V3 | - | 3.3V | 100nF直近(C402)。**VIOをNC/5Vにしない** |
| COMM_B | U401 | CANL | 6 | D401/R401/J401-2 | - | バス | 外部名COMM_B |
| COMM_A | U401 | CANH | 7 | D401/R401/J401-1 | - | バス | 外部名COMM_A |
| GND | U401 | S | 8 | GND | - | 0V | **Sピンは必ずGND固定(Normal mode)。フロート禁止** |
| COMM_A | D401 `ESD2CAN24DBZRQ1` | pin 1 | 1 | COMM_A | - | バス | 1/2=ライン(区別なし)、3=GND |
| COMM_B | D401 | pin 2 | 2 | COMM_B | - | バス | |
| GND | D401 | pin 3 | 3 | GND | - | 0V | コネクタ直近配置: connector→TVS→transceiverの順 |
| COMM_A | R401 120Ω | - | - | SW401 Common | - | バス | 終端: COMM_A—120Ω—SW—COMM_B |
| COMM_B | SW401 `JS102011SAQN` | 片側throw | - | COMM_B | - | バス | Commonと片throwのみ使用、逆側throwはNC。シルク`TERM ON/OFF` |
| COMM_A | J401/J402 `SM03B-GHS-TB` | 1 | 1 | バス | - | バス | パススルー2個をIN/OUT区別なく並列直結 |
| COMM_B | J401/J402 | 2 | 2 | バス | - | バス | |
| GND | J401/J402 | 3 | 3 | GND | - | 0V | GND参照線は省略しない |

C620側(500番台)の差分: 外部ネット名は`C620_CAN_H/L`、コネクタ構成は**未確定**(→6章)。

### 3.5 AMT22 SPI(amt22_spi)

| Net名 | 部品 | ピン名 | ピン番号 | 接続先部品 | 接続先ピン | 電圧 | 備考 |
|---|---|---|---|---|---|---|---|
| PWR_5V | J601 `SM06B-GHS-TB` | +5V | 1 | PWR_5V | - | 5V | AMT22と同ピン順=ストレート結線 |
| SPI3_SCK | J601 | SCLK | 2 | R601→U301 PC10 | - | 3.3V論理 | VIH 2.0Vのため3.3V直結成立 |
| SPI3_MOSI | J601 | MOSI | 3 | R602→U301 PC12 | - | 3.3V論理 | |
| GND | J601 | GND | 4 | GND | - | 0V | |
| SPI3_MISO | J601 | MISO | 5 | R603→U301 PC11 | - | 3.3V論理 | AMT22出力High=3.3V。直結可 |
| AMT22_CS_N | J601 | CS | 6 | R604→U301 PD2 | - | 3.3V論理 | ソフト制御GPIO(バイト間ウェイト要) |
| - | R601-604 | 直列R FP | - | - | - | - | 0603フットプリントのみ確定。値は未確定(→6章、初期0Ω実装が候補) |

### 3.6 デバッグ・ID・LED(debug_id_led)

| Net名 | 部品 | ピン名 | ピン番号 | 接続先部品 | 接続先ピン | 電圧 | 備考 |
|---|---|---|---|---|---|---|---|
| GND | J701 `BM06B-GHS-TBT` | GND | 1 | GND | - | 0V | 上挿しGH6。デバッガ電源出力は結線しない |
| SWCLK | J701 | SWCLK | 2 | U301 PA14 | - | 3.3V | SWD専用ピン。他用途不可 |
| SWDIO | J701 | SWDIO | 3 | U301 PA13 | - | 3.3V | |
| NRST | J701 | NRST | 4 | U301 PG10 | 7 | 3.3V | |
| DBG_TX | J701 | DBG_TX | 5 | U301 PA2(LPUART1_TX) | - | 3.3V | **推測**: DBG_TX=MCU送信(基板視点)。ケーブル製作時にWeAct側と照合 |
| DBG_RX | J701 | DBG_RX | 6 | U301 PA3(LPUART1_RX) | - | 3.3V | 同上 |
| UNIT_ID0 | SW701 3bit DIP | bit0 | - | U301 PC6 | - | 3.3V | 内部プルアップ、ON=GND短絡(読み値反転)。型番未確定 |
| UNIT_ID1 | SW701 | bit1 | - | U301 PC7 | - | 3.3V | |
| UNIT_ID2 | SW701 | bit2 | - | U301 PC8 | - | 3.3V | |
| GND | SW701 | 共通側 | - | GND | - | 0V | |
| 3V3 | D701緑+R701 1kΩ | PWR | - | GND | - | 3.3V | 3V3→1kΩ→LED→GND(常時点灯) |
| LED_RUN | U301 PA5→R702 1kΩ→D702緑 | RUN | - | GND | - | 3.3V | 起動時ID回数点滅に使用 |
| LED_COMM | U301 PB10→R703 1kΩ→D703黄 | COMM | - | GND | - | 3.3V | |
| LED_ERR | U301 PB11→R704 1kΩ→D704赤 | ERR | - | GND | - | 3.3V | |
| SWO | U301 PB3 | SWO | - | TP | - | 3.3V | テストポイントのみ(コネクタに出さない) |
| I2C1_SCL/SDA | U301 PA15/PB7 | 予約 | - | 拡張ヘッダ | - | 3.3V | ヘッダ型番未確定(→6章) |

テストポイント(`S1751-46R`、最低実装): `PWR_5V_IN`、`PWR_5V`、`3V3`、`VDDA_A`、GND x2、`NRST`、`BOOT0`(+隣接`3V3`)、`SWO`、`COMM_A`、`COMM_B`、`C620_CAN_H`、`C620_CAN_L`。補助信号は露出銅パッド(1.0-1.5mm)。

## 4. 必要部品一覧(ブロック別)

### IC・半導体

| ブロック | RefDes | 型番 | パッケージ |
|---|---|---|---|
| 電源保護 | U101 | `LM66100DCKR` | SC70-6 |
| 電源変換 | U201 | `TLV1117LV33DCYR` | SOT-223 |
| MCU | U301 | `STM32G474RET6` | LQFP64 |
| ADCクランプ | D301 | `BAT54SLT1G` | SOT-23 |
| CAN x2 | U401/U501 | `TCAN1051VDRQ1` | SOIC-8 |
| CAN保護 x2 | D401/D501 | `ESD2CAN24DBZRQ1` | SOT-23-3 |
| LED | D701-704 | `LTST-C190KGKT`緑x2 / `KSKT`黄 / `KRKT`赤 | 0603 |

### 抵抗(全て0603)

| ブロック | RefDes | 値 | 型番 |
|---|---|---|---|
| VREF+接続 | R301 | 0Ω | `RC0603JR-070RL` |
| R_HSE | R302 | 0Ω(初期) | 汎用0603 |
| BOOT0 | R303 | 10kΩ | `RC0603FR-0710KL` |
| 5V監視 | R304/R305 | 33kΩ/22kΩ | `RC0603FR-0733KL`/`RC0603FR-0722KL` |
| CAN終端 x2 | R401/R501 | 120Ω | `RC0603FR-07120RL` |
| SPI直列 | R601-604 | 未確定(初期0Ω候補) | - |
| LED | R701-704 | 1kΩ | `RC0603FR-071KL` |

### コンデンサ

| ブロック | RefDes | 値 | 型番/仕様 |
|---|---|---|---|
| LM66100入力 | C101 | 2.2uF以上 | X7R |
| LDO入出力 | C201-204 | 100nF+10uF x2組 | X7R |
| VDDデカップリング | C301-304 | 100nF x4 | `GRM188R71A104KA01D` |
| VBAT | C305 | 100nF | 同上 |
| VDDA | C306/307 | 100nF+1uF | `GRM188R71A104KA01D`/`GRM188R71A105KA61D` |
| VREF+ | C308/309 | 10nF+1uF | `GRM1885C1H103JA01D`/`GRM188R71A105KA61D` |
| 3V3バルク | C310 | 4.7uF | `GRM21BR71A475KA73L`(0805) |
| HSE | C311/312 | 10pF C0G | `GRM1885C1H100JA01D` |
| NRST | C313 | 100nF | `GRM188R71H104KA93D`(50V) |
| ADCフィルタ | C314 | 10nF | `GRM188R71H103KA01D` |
| CANデカップリング | C401/402、C501/502 | 100nF x2/ch | X7R |

### インダクタ・水晶・スイッチ・コネクタ・その他

| ブロック | RefDes | 型番 | 備考 |
|---|---|---|---|
| VDDAフェライト | FB301 | `BLM18AG601SN1D` | 0603 |
| HSE水晶 | X301 | `ECS-80-8-33Q-JES-TR` | 3225-4pad |
| CAN終端SW x2 | SW401/SW501 | `JS102011SAQN` | SPDT横スライド |
| ID DIP | SW701 | 未確定(3bit) | →6章 |
| 電源入力 | J101 | `SM02B-GHS-TB` | 横挿しGH2 |
| 中央CAN | J401/J402 | `SM03B-GHS-TB` x2 | 横挿しGH3パススルー |
| C620 CAN | J501? | 未確定 | →6章 |
| AMT22 | J601 | `SM06B-GHS-TB` | 横挿しGH6 |
| デバッグ | J701 | `BM06B-GHS-TBT` | 上挿しGH6 |
| 予備降圧 | U102 | OKI-78SR-5互換FP | 通常未実装+バイパスジャンパ |
| テストポイント | TP群 | `S1751-46R` | 3.3節のリスト |

## 5. 回路上の注意点(ERCで検出できないものを含む)

**ERCが検出できない誤り(重点レビュー項目):**

1. **TLV1117のタブ=VOUT**。GNDベタへ「放熱のため」接続すると3.3VがGNDへ短絡する。ERCはタブをVOUTピンと同一ネットとして見るため気づけない。
2. **LM66100のCE_N=VOUT接続**は意図的(RPP+RCB、DS8.3節)。標準アプリ図(CE_N=GND)を見て「修正」しないこと。
3. **BAT54Sの向き**。シリーズ接続品で、pin1=GND/pin2=3V3/pin3=PA0以外に繋ぐと逆クランプになる。シンボルの内部ダイオード向きをDSの図と照合する。
4. **TCAN1051VのSピン**はGND固定。フロートでもERCは通り得るが、Silent mode に入って通信不能になる。
5. **DIPスイッチの論理反転**(ON=Low)。回路は正しくてもファームで反転を忘れるとIDが化ける。回路図に`ON=Low、読み値反転`をコメントで残す。
6. **水晶3225-4padのpad番号**。汎用`Crystal_GND24`シンボルのpin番号とECS実物のpad配置が一致するとは限らない。フットプリント割当時に図面照合。
7. **PA13/PA14はSWD専用**、**PB8はBOOT0専用**(GPIO使用禁止)。ERCは「使ってしまう」誤りを検出しない。
8. **デバッガ電源非接続**。WeAct側ケーブルの5V/3.3V線を基板へ入れない(ターゲット自己給電)。回路図でJ701に電源ピンが無いことがその保証になっている。

**設計上の注意:**

- デカップリング: 100nFは「MCU周辺に4個」ではなく各VDD/VSSピン対に1個ずつ割当てる。VBATにも100nF。
- プルアップ/ダウン: NRSTは内部pull-upのため外付け禁止(100nFのみ)。BOOT0は10kΩ pull-down。UNIT_ID0-2は内部プルアップ使用(外付け不要)。
- 未使用ピン処理: ハードは未接続、ファームでアナログ入力設定が原則(**推測**: AN5093の推奨に従う想定。転記前に要照合→6章)。
- 電源投入順序: 5V→(LDO)→3.3Vの順で自然に立ち上がる。TCAN1051VのVCC/VIO間シーケンス要件はDS未照合(→6章)。AMT22は起動に最大200ms、起動中シャフト静止が必要(ファーム側で待つ)。
- 逆流: LM66100が逆接+逆流の両方を遮断。予備降圧実装時のバイパスジャンパ運用に注意(両方有効にしない)。
- 電圧レベル: AMT22は5V電源・3.3V論理互換(VIH 2.0V/出力High 3.3V)で全信号直結。TCAN1051VはVIO=3.3Vで論理レベル整合。5V系がADCへ入る唯一の点はPA0分圧。
- 終端: 各バスの物理両端だけTERM ON。C620バスはC620内蔵終端の実測後に既定を決める。
- 電流容量: LM66100=1.5A、GH端子・AWG26ハーネスが5V枝の上限を規定。LDOはSOT-223の熱で実効上限が決まる(300mA連続超なら再選定)。
- コネクタ向き: GHラッチ側は基板内側。**本表のコネクタピン番号はJST図面の番号=KiCadフットプリントの番号(基板面視)**。ハーネス製作時は嵌合面視で番号が左右反転して見えるため、圧着前にJST図面の嵌合面図で照合すること。
- データシート推奨回路との差異: LM66100 CE_N(上記2)、TCAN1051VのSプルダウン抵抗省略(直結GND、Rev.A方針)、NRST外付けpull-up省略(内部PU利用)の3点が「DSの図と違うが意図的」な箇所。

## 6. 未確定事項(推測で描かないこと)

| # | 未確定内容 | 確認が必要な理由 | 確認すべき資料・項目 |
|---|---|---|---|
| 1 | C620 CAN側コネクタの型番・個数・ピン順 | 部品リストに未記載。C620実機のCAN線(コネクタ/線色)との整合が必要 | C620/M3508現物とRoboMaster C620ユーザーガイドのCANコネクタ仕様。GH3統一の可否 |
| 2 | ID DIPスイッチ型番 | 3bit・SMT・リフロー対応の正式選定が未実施 | 候補品DS: 接点定格(低電流での接触信頼性)、洗浄性、リフロープロファイル |
| 3 | SPI直列抵抗R601-604の値(0/22-100Ω) | 配線長と立上り実測で決める方針(UNIT-05) | AMT22 DSのタイミング余裕、実基板の波形 |
| 4 | LM66100 SC70-6のピン番号 | 正本にピン機能のみ記載。転記時の照合先を明示するため | LM66100 DS「Pin Configuration」。KiCad公式シンボルは照合済みだが転記時に再確認 |
| 5 | TLV1117LV SOT-223のピン番号 | 1117系はメーカー・品種でピン順の違いがあり得る | TLV1117LV DS「Pin Configuration」 |
| 6 | 水晶3225-4padのpad番号(信号/GND) | 汎用シンボル・フットプリントとECS実物の対応が未照合 | ECS-80-8-33Qの推奨ランド図 |
| 7 | DBG_TX/DBG_RXの方向定義 | 「基板視点」解釈は推測。ケーブルでクロスするか直結かが決まらない | WeAct MiniDebugger V1.0回路図のUART_RX/TX(J2 pin3/4)の向きと突き合わせ |
| 8 | TCAN1051VのVCC/VIO電源シーケンス要件 | 5V/3.3V立上り順序の制約有無が未照合 | TCAN1051V-Q1 DSのsupply sequencing/undervoltage節 |
| 9 | 未使用ピンの処理方針 | AN5093推奨との照合が未実施(現方針は推測) | AN5093「Unused I/Os」該当節 |
| 10 | 拡張I2Cヘッダ(PA15/PB7)の型番・ピン順 | 「ヘッダに出す」のみ確定 | GHか露出パッドか、IMU拡張計画との整合 |
| 11 | GHコネクタpin1の向き(シルク表示) | 基板配置時決定と確定済み(COM-02)。回路図には影響しないが図面注記が必要 | 配置時にハーネス引出方向から決定 |
| 12 | JS102011SAQNのどちら側throwを使うか | フットプリント上のON方向がシルク表示と整合する必要 | JSシリーズDSの回路図とフットプリントの対応 |

## 7. 参照回路図

正は3章の接続表。図は接続関係・信号方向・電源系統の確認用。

レンダリング済み参照図(2026-07-20生成、schemdraw製SVG。CircuitikZソースは`figures/unit-board-circuitikz.tex`、LaTeX環境が無いため未コンパイル):

| 図 | ファイル | 内容 |
|---|---|---|
| 1 | `figures/unit-board-block1.svg` | 電源チェーン(GH2→LM66100→TLV1117→3V3) |
| 2 | `figures/unit-board-block2.svg` | CANブロック(TCAN1051V+ESD+終端+GH3 x2) |
| 3 | `figures/unit-board-block3.svg` | MCU電源・デカップリング |
| 4 | `figures/unit-board-block4.svg` | HSE+NRST+BOOT0 |
| 5 | `figures/unit-board-block5.svg` | 5V監視ADC |
| 6 | `figures/unit-board-block6.svg` | AMT22・デバッグ・ID・LED |

以下のASCII図はSVGと同内容の簡易版。

### 電源チェーン(power_input_5v + power_3v3)

```text
J101(GH2横挿し)                U101 LM66100                        U201 TLV1117LV33
 1 ●──── PWR_5V_IN ──┬────── VIN    VOUT ──┬──┬── PWR_5V ──┬────── IN    OUT ──┬──┬──┬── 3V3
 2 ●──┐              │        CE_N ────────┘  │            │                   │  │  │
      │            C101                (ST:open)│          C201 C202    (tab=VOUT)│ C203 C204
      │           2.2uF+                       │          100nF 10uF           │ 100nF 10uF
     GND             │         GND             │            │       GND        │  │  │
                    GND         │             5V負荷へ      GND      │         GND GND
                               GND        (TCAN VCC, AMT22)         GND
```

### CANブロック(can_interface、中央/C620共通)

```text
MCU側                U40x TCAN1051VDRQ1                  外部
COMM_TX ──────────→ 1 TXD      CANH 7 ──┬─────┬───┬──● J401-1 COMM_A
COMM_RX ←────────── 4 RXD      CANL 6 ──┼──┐  │   └──● J402-1 (パススルー)
PWR_5V ──C401┐───── 3 VCC         S 8 ──┴─GND │
3V3 ────C402┐───── 5 VIO                      │      ● J401-2 COMM_B ── J402-2
GND ─────────────── 2 GND     D401 ESD2CAN24  │      ● J401-3 GND ────── J402-3
                              1←COMM_A        R401 120Ω
                              2←COMM_B        │
                              3←GND          SW401 ──── COMM_B   (TERM ON/OFF)
配置順: コネクタ → TVS(D401) → トランシーバ。スタブ20mm以下
```

### 5V監視ADC

```text
PWR_5V ── R304 33k ──┬── ADC_5V_MON ── U301 PA0
                     │
                R305 22k    C314 10nF    D301 BAT54S: pin2──3V3
                     │         │                pin3──ADC_5V_MON
                    GND       GND               pin1──GND
```

### HSE

```text
U301 PF0/OSC_IN ──┬── X301 ──┬── R302(0Ω) ── U301 PF1/OSC_OUT
                  │  (case→GND)
                C311 10pF   C312 10pF
                  │          │
                 GND        GND
```

### デバッグ・ID・LED

```text
J701 GH6上挿し: 1=GND 2=SWCLK(PA14) 3=SWDIO(PA13) 4=NRST(PG10) 5=DBG_TX(PA2*) 6=DBG_RX(PA3*)  *方向は未確定#7
SW701 DIP: PC6/PC7/PC8 ──[ON=GND]── GND(内部プルアップ、読み値反転)
LED: 3V3──1k──PWR緑──GND / PA5──1k──RUN緑──GND / PB10──1k──COMM黄──GND / PB11──1k──ERR赤──GND
```

CircuitikZ版(電源チェーン、コンパイル用参考):

```latex
\begin{circuitikz}[american]
\draw (0,0) node[left]{J101-1 PWR\_5V\_IN} to[short,o-] (1.5,0)
  to[short] (3,0) node[twoportshape,t=LM66100,anchor=west](u101){};
\draw (1.5,0) to[C,l=C101 2.2uF] (1.5,-2) node[ground]{};
\draw (u101.east) to[short] (7,0) node[above]{PWR\_5V}
  to[short] (9,0) node[twoportshape,t=TLV1117,anchor=west](u201){};
\draw (7,0) to[C,l=100nF+10uF] (7,-2) node[ground]{};
\draw (u201.east) to[short,-o] (13,0) node[above]{3V3};
\draw (12.5,0) to[C,l=100nF+10uF+4.7uF] (12.5,-2) node[ground]{};
\end{circuitikz}
```

---

## 転記後のチェック手順(AI照合に渡すもの)

1. `.kicad_sch`保存後、本文書3章の接続表とS式を突き合わせ(AI作業)。
2. `kicad-cli sch erc`実行と結果解釈。
3. 5章「ERCが検出できない誤り」8項目の目視レビュー。
4. BOM出力と4章の個数照合(特に100nF x4+VBAT、VDDA/VREF+の2組)。
