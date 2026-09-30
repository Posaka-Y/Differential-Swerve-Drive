# Teensy 4.1中央基板 Rev.A 回路図リファレンス

> 2026-09-23: 本文は旧Rev.Aの参考。次回製造のCAN端子とコイルdriver搭載境界は最新一括発注計画に従う。中央回路図は改訂PDFを人が転記する。 詳細: [次回PCB一括発注計画](PCB_BATCH_V2_CENTRAL_PLAN.md)。

作成: 2026-08-04
状態: 人間レビュー用KiCad回路図の接続正本。`hardware/central-board/central-board.sch`をrootとする責務別6 child sheetsと同時に照合する。

> **Rev.1注記(2026-09-14)**: Rev.1(コンタクタドライバ・24Vセンス・INA238を持たない構成)のKiCad転記用接続表は`CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md`を使う。本書のD2(コンタクタドライバ)、D4(モータバス電圧)、E(INA238部分)はRev.1で不採用。

## Rev.Aの範囲

搭載するもの:

- Teensy 4.1ソケット、micro USBサービス空間
- CAN1/CAN2/CAN3トランシーバ、ESD、切替式120ohm終端、各バスIN/OUTコネクタ
- 5V主入力保護、4ノード＋Teensy＋拡張のスター分配
- E-stop直列ループ、個別補助接点監視、コンタクタコイルドライバ
- コンタクタ後24Vセンス、購入済みMatek I2C-INA-BMによる外部電流・電圧監視
- 物理再アームボタン、基板状態LED、I2C/UART/SPI/GPIO拡張

載せないもの:

- C620主電流、外付け100Aシャント、メインコンタクタ本体
- 24V表示灯・電磁弁・LEDテープの電力ドライバ
- 24V→5V DC-DC、24V→12V DC-DC
- Ethernet magjack、USB Host、追加3.3V LDO

## A. 5V主入力・スター分配

### A1. 主入力

```text
J1 XT30PW-M
  1 = +5V_IN
  2 = GND_CTRL

+5V_IN -> TPS259470LRPWR -> +5V_SYS
```

- J1正式型番はAMASS `XT30PW-M`、横向きTHT、連続15A定格。5A入力に使用する。
- U1はTI `TPS259470LRPWR`。真の逆流阻止、突入、過電流、過熱を扱い、USB接続中に`+5V_SYS`からDC-DC側へ逆流させない。入力逆極性保護はTPS259470の内蔵back-to-back FETで扱う（連続5Aに使えない`LM66100`や別series diodeは中央主入力へ追加しない）。ただし絶対最大はIN=28V、負電圧=-15Vなので、24V側の大きなサージを5V出力へ通さないことはDC-DC側の責務とする。
- `RILM=750ohm`を初期値とし、過電流閾値はtyp 4.45A。想定1〜2A負荷に十分な余裕を持たせつつ、5A DC-DCと配線を保護する。
- SD-25B-5を5.00Vへ調整・封印した前提で、UVLO/OVLO dividerは1% `R102=732k` (IN→EN/UVLO)、`R103=51.1k` (EN/UVLO→OVLO)、`R104=221k` (OVLO→GND) とする。typ設定値はUVLO rising約4.43V、OVLO rising約5.46V。これは異常時の切離しであり、SD-25B-5の出力trimを5.5Vまで上げてよい意味ではない。組立時に無負荷/定格負荷で5.00V±0.10Vを記録する。
- `dVdt`は全枝の実装容量を積算し、起動時の出力立上り20〜50msを目標に決める。初版は`C_dVdt=10nF`（5Vでtyp約25ms）とし、22nF/47nFへ交換可能にする。
- U1直近に1uF入力、1uF出力、J1近傍に100uF/10V、スター点に470uF/10V low-ESRを置く。`FLT`は10kohmで3.3Vへpull-upし`PWR_5V_FAULT_N`へ接続する。
- `FLT`は10kohmで3.3Vへpull-upし`PWR_5V_FAULT_N`へ接続する。
- 2mm角QFNのため、データシート推奨land patternと熱viaを使用し、表裏GND copperへ放熱する。

### A2. 枝

| 枝 | 保護 | コネクタ/接続 | LED |
|---|---|---|---|
| Unit 1 | `1206L050/15YR` | `SM02B-GHS-TB`, 1=5V, 2=GND | 緑+1.5kohm |
| Unit 2 | `1206L050/15YR` | 同上 | 同上 |
| Unit 3 | `1206L050/15YR` | 同上 | 同上 |
| Odometry | `1206L050/15YR` | 同上 | 同上 |
| Teensy | `1206L075/16WR` | VINへ基板内接続 | 緑+1.5kohm |
| Expansion 5V | `1206L050/15YR` | GH拡張電源 | 緑+1.5kohm |

PPTC後を個別ネット`+5V_UNIT1`等とし、各枝へtest pointを置く。PPTCの高温deratingと突入は実機で確認する。

## B. Teensyソケット

- 回路図では1x24 connectorを2個使い、socket pad番号1〜48を`TEENSY41_CENTRAL_PIN_ASSIGNMENT.md`どおりに割り当てる。
- ソケットはPJRC推奨のSullins `PPPC241LFBN-RC`または`PPTC241LFBN-RC` x2を第一候補とする。Teensy側header候補はAmphenol `68000-224HLF`。
- 列中心間15.24mm。Teensy外形60.96mm x 17.78mmとmicro USB plugの抜差し領域をF.CrtYd相当のkeepoutにする。
- Teensy直下は裏面実装部品との干渉を避けるため、部品、test point、露出pad/copperを全面禁止する。microSD、Program button、micro USBの交換・操作空間も塞がない。
- 組立工程にVUSB-VINパッド切断と導通検査を入れる。

### B1. USB給電diode-OR(2026-09-12追加)

```text
+5V_SYS -> D1(Schottky) -\
                           +-> VIN(pad48)
Teensy VUSBパッド -> D2(Schottky) -/
```

- VUSB-VINパッドは従来通りカット。カット後のVUSBパッドからD2を介してVINへ接続する。
- D1/D2はNexperia `PMEG2010EA,115`（20V/1A low-VF、SOD-323）を初期指定とする。逆流はTPS259470側で別途保護済みのためD1はOR用途のみ。
- ~~外部5V枝をUSBから給電させない~~ → 2026-09-26撤回。USBからも第2 eFuse経由で`+5V_SYS`へ給電する(B2)。

### B2. USB→+5V_SYS 給電(2026-09-26追加)

```text
Teensy VUSB -> U102 TPS259470ARPWR (ILIM≈1A, auto-retry) -> +5V_SYS
+5V_RAW -> 100k/37.4k -> U102 OVLO   (外部5V≥4.41VでU102 OFF = 外部5V優先)
```

- USBだけでCAN x3とノード1基分(ユニット or オドメトリ)の5Vを動かすため。定数・接続表は`CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md` 3.1節が正本。
- D2(VUSB→VIN)は残す。外部5Vの抜き差し時とU102の電流制限時にTeensyのUSB接続を切らさないため。

## C. CAN x3

各バスは`CAN_COMMON_BLOCK_PART_SELECTION.md`の同一回路を使う。

| bus | Teensy | 初期実装 | 通信 |
|---|---|---|---|
| CAN1 Sensor | pin 22/23 | 実装 | Classic CAN 1Mbps |
| CAN2 Expansion | pin 0/1 | 実装 | Classic CAN 1Mbps初期値 |
| CAN3 Drive | pin 31/30 | 実装 | CAN FD nominal 1Mbps/data 2Mbps+BRS |

- U2/U3/U4: `TCAN1051VDRQ1`、VCC=5V、VIO=3.3V、各電源pinへ100nF。
- connector -> `ESD2CAN24DBZRQ1` -> bus trunk -> transceiverの順に置く。
- 各バスに横挿しGH3を2個並列配置し、1=`COMM_A`、2=`COMM_B`、3=`GND_CTRL`。バス名は`SENSOR_COMM_*`、`EXP_COMM_*`、`DRIVE_COMM_*`のprefixで回路図内を区別する。
- `RC0603FR-07120RL`と`JS102011SAQN`を直列にした終端を各バスへ1組置く。スイッチ近傍へ`TERM ON/OFF`を表示する。
- CAN3差動pairは100ohm differentialを目標、同一層・連続GND reference・スタブ10mm以下とする。CAN1/2も同じ配置規律を使う。

## D. 24V安全回路

### D1. コネクタとハードループ

```text
+24V_CTRL_IN
  -> F1 250mA fuse
  -> ESTOP_LOOP_OUT
  -> E-stop 1 NC
  -> E-stop 2 NC
  -> ESTOP_LOOP_RETURN
  -> contactor coil +
  -> contactor coil -
  -> Q1 drain/source
  -> GND_CTRL
```

- `24V_CTRL_IN`と`CONTACTOR_COIL`は誤挿入を避けるため別キー/明確な色表示を持つロック付き2pin connectorとする。
- `ESTOP_CTRL`はMolex Micro-Fit 3.0 single-row header `43650-0600`、相手housing `43645-0600`。dual-row housing `43025-0600`とは嵌合しない。既定の6pin割当は`CENTRAL_BOARD_REQUIREMENTS.md`に従う。
- 安全ループ用F1とLED/補助接点用F2を分離する。F2短絡でF1が開かないことを配線試験する。

### D2. コンタクタドライバ

- Q1: `IRLML0100TRPBF`, 100V N-channel SOT-23。80mAコイルではVGS=3.3V時にRds(on)が悪化しても発熱余裕が十分あることを試作で確認する。
- Gate: Teensy -> 100ohm -> Gate、Gate-Source 47kohm pulldown。Teensy未起動時はOFF。
- coil clampはdiode+TVSを第一候補とし、TVS電圧はE228の解放時間とQ1 VDS実測から確定する。`1N4007`単独の低電圧clampは解放を遅くするため初期案にしない。
- coil connector近傍にD1、Q1、24V/GND test pointをまとめる。コイル電流は大電流GND面を横断させず24V I/O領域で閉じる。

### D3. E-stop監視

- U5: `LTV-847S` 4ch optocoupler。ch1=直列ループ、ch2/3=個別補助接点、ch4=予備24V入力。実pinはch1=`A1/K2, C16/E15`、ch2=`A3/K4, C14/E13`、ch3=`A5/K6, C12/E11`、ch4=`A7/K8, C10/E9`で固定する(**2026-09-14訂正**: 旧記載「ch1=E9/C10 … ch4=E15/C16」はLite-On BNS-OD-C131/A4の内部接続図と不一致。DIPのミラー対でLED 1/2はTr 16/15と組む。`reference-2026-09-12/`の安全シートは旧対応のままなので流用しない)。
- `LTV-847S`は標準SOIC-16ではない。購入リール実物とLite-On outlineを照合して、wide 2.54mm-pitch SMD用の専用footprintを`hardware/lib/`へ起こすまでPCBフットプリントは空欄とする。
- 各使用入力は2.2kohm x2直列（R10A/R10B等）と`1N4148W`のLED逆並列保護を置く。24V時は約5mA、抵抗合計4.4kohmの損失は約0.12Wなので各0603へ約60mWずつ配分される。24V制御電源の上限を30Vとしても各抵抗は約75mWに留める。
- transistor側は各chのcollectorを10kohmで3.3Vへpull-up、emitterをGND_CTRLへ接続する。Low=接点成立なので`*_OK_N`と命名する。
- フォトカプラは診断用であり、安全遮断の主経路ではない。

### D4. モータバス電圧

- コンタクタ後`MOTOR_24V`を100kohm+100kohm / 20kohm (各0.1%)で1/11へ分圧する。
- ADC直前に1kohm、10nF、3.3V対応low-leakage clampを置く。25.2V時は約2.29V。
- 40V印加を1分行ってTeensy ADC pinが絶対最大を越えないことを試験する。ファーム換算係数は実測校正値を保存する。

## E. バッテリー電圧・電流監視

- 購入済みのMatek `I2C-INA-BM`を中央PCB外へ置く。内蔵INA228/INA238系と200uΩ typシャントで、主電源の正側をモジュールのBAT+側からESC+/負荷側へ直列に通す。中央PCBに主電流もKelvin sense harnessも入れない。
- 中央PCBのJ20はJST-GH 4pinで、**pin 1=GND、pin 2=I2C0_SDA、pin 3=I2C0_SCL、pin 4=+5V_SYS**。Matekは5V pinへ4〜9Vを要するため、Teensyの3.3V枝には接続しない。
- I2C addressは既定のdecimal 69（0x45）。必要時だけモジュールのaddress jumperで68（0x44）または65（0x41）へ変更する。`BAT_MON_ALERT_N`はこのモジュール接続では使用しない。
- 公称は0〜85V、連続150A／burst 204.8A、電流精度±2%。内蔵シャント損失は200uΩ typなので、83Aで約1.38W、150Aで約4.5W。電源線・端子・熱設計が連続電流を満たすことを実機確認する。
- I2C信号のプルアップ電圧はモジュール実装状態で確認する。Teensy GPIOへ5Vを印加しないこと（3.3V logicであること）を通電前の必須確認とする。

## F. 操作・拡張

- `REARM_SW_N`: 基板上タクトスイッチ、10kohm pull-up、100nF。GUIだけではコンタクタを再励磁できない。
- status LED: 赤/緑を各1個、GPIOから1kohmを介して駆動。電源LEDと状態LEDをシルクで区別する。
- I2C0/I2C1拡張: GH4、1=3.3V、2=GND、3=SDA、4=SCL。2.2kohm pull-upはsolder jumperで切離し可能。Matek用J20は別系統で、1=GND、2=SDA、3=SCL、4=5Vとする。
- UART x2: GH3、1=GND、2=TX、3=RX。
- SPI: GH7、1=3.3V、2=GND、3=SCK、4=MOSI、5=MISO、6=CS0_N、7=CS1_N。
- GPIO/ADC: GH10、1=3.3V、2=GND、3〜10=IO x8。各IOに100ohm直列抵抗。
- 3.3V外部負荷は全拡張合計100mAをRev.A上限とし、Teensy推奨外部250mAに余裕を残す。

### F1. 拡張ヘッダTVS/アクティビティLED(2026-09-12追加)

```text
GHコネクタ -> SRV05-4(pin5=+3V3_TEENSY, pin2=GND_CTRL) -> Teensy pin
既存信号net(TXD/RXD/SCK等) -> digital transistor -> LED
```

- `SRV05-4`(SOT-23-6、4ch)をI2C(1個・4本)、UART(1個・4本)、SPI(2個・5本使用)、GPIO/ADC(2個・8本)へ計6個配置する。新規Teensy pinは消費しない。
- アクティビティLEDは既存信号netを直接タップし、GPIOを追加消費しない。ただしUART/CANのidle HIGHを単純なNPNへ入れると常時点灯になるため、Rev.AはLED用footprintとtap padのみDNPで残し、RC one-shotまたは専用bufferを別途実測してから実装する。予備pin 33/37/38/39はそのまま温存する。

## G. PCB制約

- 4層、1.6mm、外層1ozを初期条件。L2を連続GND、L3を5V/3.3Vと低速信号に使う。
- 暫定外形100mm x 80mm、四隅M3穴、穴中心を各辺から4mm。機体CAD確定時に外形だけ更新する。
- 左辺: 5V入力と電源枝。上辺: CAN。右辺: 24V安全I/O。下辺: 拡張I/O。中央: Teensy。
- 24V領域、CAN connector領域、アナログsense領域を分離する。L2 GNDは分割しない。
- 5V主幹は4A連続を暫定設計電流とし、表裏copper pour＋via stitchingで配る。eFuse熱padはTI推奨例を優先する。
- USB端から基板外へ15mm以上のplug/cable keepoutを確保する。
- 基板名、Rev、5V/24V、全connector pin、CAN bus名、TERM状態、E-stop pinを機能シルクで表示する。RefDesは製造図で確認できれば基板上非表示でもよい。

## H. ERC/DRC以外の必須試験

1. Teensyを外した状態で5V逆接、出力側5V印加、枝短絡を試験する。
2. USB接続＋外部5V給電でPC側へ逆流しないことを測る。
3. ダミー24V/80mAコイルでE-stop抜去、各NC開放、Teensy reset、MOSFET OFFを試験する。
4. コンタクタ実物でGate、Drain、coil voltageを測り、Q1 VDSと解放時間を確認する。
5. CAN各busを終端60ohm合成、1Mbps、CAN3 FD 2Mbps+BRSで連続試験する。
6. I2C-INA-BMを既知電流でクランプメータと比較し、I2C pull-up電圧・電流値・温度上昇を記録する。

## 参照データシート

- PJRC Teensy 4.1 product page / pinout card
- TI `TPS25947` Rev.C (2026-05)
- Matek `I2C-INA-BM` product page / wiring guide（購入済み外部モジュール）
- Infineon `IRLML0100`
- Lite-On `LTV-8X7` series Rev.S
- PJRC 24x1 header/socket guidance、Sullins `PPPC241LFBN-RC` / `PPTC241LFBN-RC`
- Molex Micro-Fit 3.0 `43650` / `43645`
- AMASS `XT30PW-M` V1.2
