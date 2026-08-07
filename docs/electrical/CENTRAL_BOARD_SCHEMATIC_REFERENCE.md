# Teensy 4.1中央基板 Rev.A 回路図リファレンス

作成: 2026-08-04
状態: 人間レビュー用KiCad回路図の接続正本。`hardware/central-board/central-board.sch`をrootとする責務別6 child sheetsと同時に照合する。

## Rev.Aの範囲

搭載するもの:

- Teensy 4.1ソケット、micro USBサービス空間
- CAN1/CAN2/CAN3トランシーバ、ESD、切替式120ohm終端、各バスIN/OUTコネクタ
- 5V主入力保護、4ノード＋Teensy＋拡張のスター分配
- E-stop直列ループ、個別補助接点監視、コンタクタコイルドライバ
- コンタクタ後24Vセンス、INA238による外付けシャント監視
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
- U1はTI `TPS259470LRPWR`。真の逆流阻止、突入、過電流、過熱を扱い、USB接続中に`+5V_SYS`からDC-DC側へ逆流させない。負電圧を含む入力逆接は別の60V級series保護で扱う。
- `RILM=750ohm`を初期値とし、過電流閾値はtyp 4.45A。想定1〜2A負荷に十分な余裕を持たせつつ、5A DC-DCと配線を保護する。
- UVLO/OVLOはDC-DC出力公差、TPS259470 comparator公差、抵抗公差を含むworst-case計算後に決める。Teensy VIN推奨上限5.5Vに近いOVLO nominal 5.45Vは確定値として使わない。
- `dVdt`は全枝の実装容量を積算し、起動時の出力立上り20〜50msを目標に決める。初版は22nFを実装し、10nF/47nFへ交換可能にする。
- U1直近に1uF入力、1uF出力、J1近傍に100uF/10V、スター点に470uF/10V low-ESRを置く。
- `FLT`は10kohmで3.3Vへpull-upし`PWR_5V_FAULT_N`へ接続する。
- 2mm角QFNのため、データシート推奨land patternと熱viaを使用し、表裏GND copperへ放熱する。

### A2. 枝

| 枝 | 保護 | コネクタ/接続 | LED |
|---|---|---|---|
| Unit 1 | `1206L050/15YR` | `SM02B-GHS-TB`, 1=5V, 2=GND | 緑+1.5kohm |
| Unit 2 | `1206L050/15YR` | 同上 | 同上 |
| Unit 3 | `1206L050/15YR` | 同上 | 同上 |
| Odometry | `1206L050/15YR` | 同上 | 同上 |
| Teensy | `1206L075/16YR` | VINへ基板内接続 | 緑+1.5kohm |
| Expansion 5V | `1206L050/15YR` | GH拡張電源 | 緑+1.5kohm |

PPTC後を個別ネット`+5V_UNIT1`等とし、各枝へtest pointを置く。PPTCの高温deratingと突入は実機で確認する。

## B. Teensyソケット

- 回路図では1x24 connectorを2個使い、socket pad番号1〜48を`TEENSY41_CENTRAL_PIN_ASSIGNMENT.md`どおりに割り当てる。
- ソケットはPJRC推奨のSullins `PPPC241LFBN-RC`または`PPTC241LFBN-RC` x2を第一候補とする。Teensy側header候補はAmphenol `68000-224HLF`。
- 列間17.78mm。Teensy外形60.96mm x 17.78mmとmicro USB plugの抜差し領域をF.CrtYd相当のkeepoutにする。
- Teensy直下は裏面実装部品との干渉を避けるため、部品、test point、露出pad/copperを全面禁止する。microSD、Program button、micro USBの交換・操作空間も塞がない。
- 組立工程にVUSB-VINパッド切断と導通検査を入れる。

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

- U5: `LTV-847S` 4ch optocoupler。ch1=直列ループ、ch2/3=個別補助接点、ch4=予備24V入力。
- 各入力は2.2kohm x2直列を初期値とし、逆電圧保護diodeをLED逆並列に置く。24V時約5mAとして、LTV-847Sのminimum CTR test条件に合わせる。入力電圧範囲と抵抗損失をworst-case確認する。
- transistor側は10kohmで3.3V pull-up。Low=接点成立なので`*_OK_N`と命名する。
- フォトカプラは診断用であり、安全遮断の主経路ではない。

### D4. モータバス電圧

- コンタクタ後`MOTOR_24V`を100kohm+100kohm / 20kohm (各0.1%)で1/11へ分圧する。
- ADC直前に1kohm、10nF、3.3V対応low-leakage clampを置く。25.2V時は約2.29V。
- 40V印加を1分行ってTeensy ADC pinが絶対最大を越えないことを試験する。ファーム換算係数は実測校正値を保存する。

## E. バッテリー電圧・電流監視

- U6: `INA238AIDGSR`、3.3V給電、I2C0、A0/A1=GNDでaddress 0x40。
- 主電流を中央PCBへ通さない。外付け100A/75mV、0.75mohm、Kelvin端子付きシャントをバッテリー高側へ置き、2本のsense線だけをGH2へ入れる。
- 83A時shunt drop=62.25mV、損失=約5.17W。100A時75mVでINA238の163.84mV range内。
- battery側の各sense線起点にfusible resistorまたはsmall fuseを置く。board側10ohmだけではbattery short時のharnessを保護できない。sense connector -> 10ohm各線 -> INA238 IN+/IN-、差動10nFを初期値とし、配線は対で引いてshunt上でKelvin接続する。
- VBUSはshunt負荷側を1kohm経由で接続する。ALERTは10kohm pull-upで`BAT_MON_ALERT_N`へ接続する。
- 外付けシャントの正式型番は機体分電盤の機械取付寸法を確認後に確定する。0.75mohm/5W以上、100A連続、Kelvin端子を最低条件とする。

## F. 操作・拡張

- `REARM_SW_N`: 基板上タクトスイッチ、10kohm pull-up、100nF。GUIだけではコンタクタを再励磁できない。
- status LED: 赤/緑を各1個、GPIOから1kohmを介して駆動。電源LEDと状態LEDをシルクで区別する。
- I2C0/I2C1: GH4、1=3.3V、2=GND、3=SDA、4=SCL。2.2kohm pull-upはsolder jumperで切離し可能。
- UART x2: GH3、1=GND、2=TX、3=RX。
- SPI: GH7、1=3.3V、2=GND、3=SCK、4=MOSI、5=MISO、6=CS0_N、7=CS1_N。
- GPIO/ADC: GH10、1=3.3V、2=GND、3〜10=IO x8。各IOに100ohm直列抵抗。
- 3.3V外部負荷は全拡張合計100mAをRev.A上限とし、Teensy推奨外部250mAに余裕を残す。

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
6. 100A/75mV shuntを既知電流で校正し、INA238とクランプメータの差を記録する。

## 参照データシート

- PJRC Teensy 4.1 product page / pinout card
- TI `TPS25947` Rev.C (2026-05)
- TI `INA238` Rev.B (2025-05)
- Infineon `IRLML0100`
- Lite-On `LTV-8X7` series Rev.S
- PJRC 24x1 header/socket guidance、Sullins `PPPC241LFBN-RC` / `PPTC241LFBN-RC`
- Molex Micro-Fit 3.0 `43650` / `43645`
- AMASS `XT30PW-M` V1.2
