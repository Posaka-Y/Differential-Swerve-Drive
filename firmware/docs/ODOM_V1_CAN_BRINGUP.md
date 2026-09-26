# V1 ODOM CAN単体試験

対象: STM32F405RGT6 + TCAN1051VDRQ1。V2設計と独立した実装確認。
`can_f405.hex`はAMT102/IMU処理を含まない。通常制御ファームではない。

## 接続

V1製造PCB `hardware/odometry-board/Oddom board/Oddom board.kicad_pcb`を照合:

- J2 pin1=CAN H、pin2=CAN L、pin3=GND。USB-CAN H/L/GNDへ接続。
- U4 pin1=TXD→PA12、pin4=RXD→PA11、pin3=5V、pin5=3.3V、pin8=S→GND。
- SWDはJ8。J7はIMU用でありデバッグ用ではない。
- バス両端だけ120Ω。無給電でH-L間約60Ωを確認する。
- F405側はClassic CAN 1Mbps、標準11bit ID。CAN FDは使わない。

USB-CAN実測: VID=1D50/PID=606F、serial=`003800394633500E20303035`、
USB名=`canable2 gs_usb`。ユーザー申告型番はSH-C31A。
BOOT OFFで接続する。WindowsではCAN Interface 0にWinUSBが必要。
ST-LinkやUSB Composite Deviceのドライバを変更しない。

## 診断ファーム

`scripts/build.ps1`で`build/debug/can_f405.hex`を生成。
既存`flash.ps1`はG474本体専用なので本ターゲットには使わない。
F405 Device ID=0x413とプローブSNを確認し、必要ならsector0を退避した上で
CubeProgrammerに明示的に本HEXを渡してwrite/verify/resetする。

起動時にHSI16MHzのsilent loopbackでID/DLC/8byte一致を確認。
次にHSE8MHzへ切替え、APB1=8MHz、BRP=1、BS1=5、BS2=2、SJW=1、
sample point=75%で通常通信。水晶起動失敗時は停止し、HSIへ代替しない。
NARTで送信1回のみ、ABOMでbus-off自動復帰。RUNは1Hz、COMMは受信時、
ERRは初期化例外またはCAN warning/passive/bus-off時に点灯。

以下は独立ベンチ専用ID。製品プロトコルへの追加ではない。

| ID | 方向 | 内容 |
|---|---|---|
| 0x6E4 | PC→F405 | DLC 0〜8のテストデータ |
| 0x6E5 | F405→PC | 上記受信データをそのまま返す |
| 0x6E6 | F405→PC | 1Hz、uint32 uptime ms + uint32 RX数、little endian |

`scripts/read-can-f405.ps1`でSWD Hot Plug読取。SRAM先頭のmagicはF405CA01。
phase=3/fault=0/loopbackOK=1/hseReady=1が初期化成功。
fault: 1=CAN init待ち、2=init解除待ち、3=loopback受信待ち、
4=loopback内容不一致、5=HSE待ち、6=clock切替待ち。
各値はlive読取であり同時snapshotではない。

## PC試験

Python環境を`build/can-host`に作成済み。
依存: python-can 4.6.1、gs-usb 0.3.1、libusb-package 1.0.30.0。

```powershell
.\firmware\build\can-host\Scripts\python.exe firmware/scripts/test-can-f405.py --count 10
.\firmware\scripts\read-can-f405.ps1
```

USB自身の送信echoは成功に数えず、0x6E5のsequenceを含む全8byte一致を評価。
10/10応答、heartbeat受信、error frameなし、F405のtxOK/rx増加と
エラーカウンタを確認する。内部loopback成功だけで外部CAN合格とはしない。

## 2026-09-23現在

- 1608byte版をF405へwrite/verify/reset済み。内部loopback/HSE/通常モード移行成功。
- 初版はGPIO AF設定前のloopback初期化解除で停止。AF9/RX pull-upを
  初回init前に設定し修正、実機で成功を確認した。
- 外部txOK=0/rx=0。USB-CAN Interface 0がCode28でWinUSB導入待ち。
  TEC上昇/LEC=5を観測。対向機が使える状態になってから配線・終端も含め再評価。
- 元AMT102のsector0退避: `build/debug/f405-sector0-before-can-20260923.bin`。

### WinUSB導入後

- CAN Interface 0のCode28解消、USB control/bulk操作可能。
- 10回送信要求: 一致返信0、heartbeat受信0。F405側もtxOK=0/rxCount=0。
  外部CANは未成立。LEC=5 (bit dominant error)、TEC増加を観測。
- USB報告CAN clock=170MHz。PC計算値はBRP10/TSEG1=12/TSEG2=4、
  正確に1Mbps、sample point=76.47%。USB側one-shot非対応のため通常再送となる。
- USB側loopbackを一時起動し、固有payloadの送信echoが返ることを確認後stop。
  USB経路の確認でありF405からの返信ではない。外部CAN成功には数えない。
- V1基板終端はR1=120RとSW1。次は両端終端とJ2 H/L/GNDの現物照合。

### 受信経路の切分け

- ユーザー実測: H/L各2.45V、H-L67Ω、U4 pin3/5/8の電圧は正常との回答。
- 1752byte診断版へ更新。起動時、CAN reset後・HSE8MHz状態でPA12を
  一時GPIO出力へ切替え、短いHigh→Low→Highを出しPA11を読む。
  RX弱pulldownの読取後はpull-up/AF9へ戻す。独立ベンチ専用。
- SRAM word24..27の実測=BF0C/EF0C/FF0C/F70C。
  PA12は1→0→1、PA11は1→1→1、RX弱pulldownで0。
- 推定: PA11がU4 RXDの正常なpush-pull出力で駆動されていない可能性が高い。
  MCU内部pullによる変化はCAN受信成功ではない。
- 次: 無給電でU4実リード4(RXD)↔U1実リード44(PA11)の導通、
  U4実リード1(TXD)↔U1実リード45(PA12)の導通。
  導通良好なら給電時U4実リード4の電圧と実装方向/型番を確認する。
  この試験だけでははんだ/断線/IC損傷を区別できない。

参照: [ST CMSIS F405 register definitions](https://github.com/STMicroelectronics/cmsis-device-f4/blob/master/Include/stm32f405xx.h)、
[CANable接続ガイド](https://canable.io/getting-started.html)。

### 外部CAN最小試験合格（2026-09-23）

給電復帰後、10回の8byte echo全一致、heartbeat10件、PC error frame0。
F405のtxOKは0→20、rxCountは0→10、txFailは9→9（試験中増加なし）、
LEC=0/REC=0、FIFO overrun/echo drop=0。試験前ACK待ちで蓄積したTECは72→52。
USB自身のechoは判定から除外。双方向Classic CAN 1Mbpsの最小確認は合格。
具体的な現物修正内容は未聴取、長時間・高負荷・再起動再現性は未評価。
現在はCAN診断版を保持し、USB-CANは試験終了でstop。
起動時pathRxAtLow=1という単発値は残るが通常通信は実測成功しており、
この起動snapshotだけで現時点のRX断線を判定しない。
