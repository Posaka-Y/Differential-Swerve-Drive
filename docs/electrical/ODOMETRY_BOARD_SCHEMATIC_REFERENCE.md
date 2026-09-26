# オドメトリ基板 フラット回路図作成リファレンス

> **V2改版（2026-09-23着手）**: デバッグ・TP・V1修正の変更要件は[共通V2要件](UNIT_ODOMETRY_V2_REQUIREMENTS.md)を優先する。本文のGH6/SWD・UART一体配列はV1仕様。V2の正式ヘッダ型番とPCB配線は未確定/未完了。

作成日: 2026-07-25。対象: STM32F405RGT6 + AMT102 x3 + ICM-42688-Pオドメトリ基板 Rev.A。

## 方針

- 回路図は**A3横1枚のフラット構成**とし、階層シートを使わない。
- MCUから各機能へ長い配線を引かず、短いスタブと通常のローカルネットラベルで接続する。
- 電源、CAN、コネクタ、LED、デバッグ部品はunit board採用品を優先流用する。
- STデータシート、`STM32F405_ODOMETRY_PIN_ASSIGNMENT.md`、`ODOMETRY_BOARD_REQUIREMENTS.md`を正本とする。
- 旧`hardware/odometry-board/*.kicad_sch`はG474階層シートの履歴であり、新しいフラット回路図から参照しない。

## 1枚上の配置

信号と電源の流れが左から右へ読めるよう、次のゾーンに分ける。

```text
上段: [5V入力/保護] -> [3.3V LDO] -> [F405最小回路] -> [CAN]

中段: [Debug/BOOT/ID/LED]       [STM32F405RGT6]       [IMU]

下段: [AMT102 Wheel 1] [AMT102 Wheel 2] [AMT102 Wheel 3]
```

- A3座標の目安: 電源=x30～90、MCU=x110～190、CAN=x210～285、エンコーダ=x30～190下段、IMU=x210～285中段。
- 各ゾーンをgraphic rectangleとテキスト見出しで囲む。rectangleは配線と重ねない。
- 外部コネクタは各ゾーンの外周側、MCU向き信号は中央側へ向ける。

## RefDes割当

フラット回路図でも機能別に100番台を分ける。

| 範囲 | ブロック | 主な部品 |
|---:|---|---|
| 100 | 5V入力・逆接/逆流保護 | J101、U101 LM66100、C101 |
| 200 | 3.3V LDO | U201 TLV76133、C201～C204 |
| 300 | F405最小回路 | U301、Y301、FB301、C301～C313、R301～R302 |
| 400 | センサーCAN | U401、D401、SW401、R401、C401～C402、J401～J402 |
| 500 | AMT102入力 x3 | J501～J503、D501～D503、U501～U503、C501～C503、C511～C516、R511～R516 |
| 600 | ICM-42688-Pモジュール | J601、C601～C602 |
| 700 | Debug・ID・LED | J701、SW701、D701～D704、R701～R705 |
| 800 | テストポイント | TP801～ |

## ブロック接続

### 5V入力・3.3V

| Net | 接続 |
|---|---|
| `PWR_5V_IN` | J101-1 -> U101 VIN、C101 2.2uF |
| `GND` | J101-2、U101 GND、全電源帰路 |
| `PWR_5V` | U101 VOUT、U101 CE_N、U201 IN、TCAN VCC、AMT102 x3 VCC |
| `3V3` | U201 OUT/tab、F405 VDD/VBAT、TCAN VIO、バッファ、IMU、LED |

- J101=`SM02B-GHS-TB`、1=5V、2=GND。
- U101=`LM66100DCKR`。CE_N=VOUT、ST/NCは未接続。
- U201=`TLV76133DCYR`。tab=VOUT。入力/出力へ各100nF+10uF。

### STM32F405RGT6最小回路

| 機能 | 接続 |
|---|---|
| VDD | pin 19/32/48/64へ3V3、各100nF |
| VSS | pin 18/63をGND |
| VBAT | pin 1を3V3、100nF |
| VDDA/VSSA | FB301経由3V3、100nF+1uF、VSSA=GND |
| VCAP_1/2 | pin 31/47から各2.2uF・ESR<2ΩをGND。他ネットへ接続禁止 |
| HSE | PH0 pin5 / PH1 pin6、8MHz `FC3BAEBDI8.0-T1`、C0G 10pF x2 |
| NRST | pin7、100nF to GND、J701、TP |
| BOOT0 | pin60、10kΩ pull-down、BOOT/3V3隣接TP |

F405電源部品:

- VDD 100nF: `C0603C104K5RACTU`
- VDD bulk: `GRM21BZ71E475KE15K` 4.7uF
- VDDA: `BLM18AG601SN1D` + 100nF + `C1608X7R1E105K080AB` 1uF
- VCAP: `GCM21BR71E225KA73L` x2

### センサーCAN

| Net | 接続 |
|---|---|
| `COMM_TX` | F405 PA12 -> U401 TXD pin1 |
| `COMM_RX` | U401 RXD pin4 -> F405 PA11 |
| `COMM_A` | U401 CANH pin7、D401、終端、J401/J402 pin1 |
| `COMM_B` | U401 CANL pin6、D401、終端、J401/J402 pin2 |
| `GND` | U401 pin2/S pin8、D401 pin3、J401/J402 pin3 |

- U401=`TCAN1051VDRQ1`、VCC=5V、VIO=3.3V、S=GND。
- D401=`ESD2CAN24DBZRQ1`をJ401/J402側へ置く。
- `COMM_A -- R401 120Ω -- SW401 -- COMM_B`。SW401=`JS102011SAQN`。
- J401/J402=`SM03B-GHS-TB`の完全並列パススルー。

### AMT102 x3

各コネクタは`SM04B-GHS-TB`、1=5V、2=GND、3=A、4=B。

| Wheel | Connector | Buffer | MCU |
|---:|---|---|---|
| 1 | J501-3/4 | U501A/B `SN74LVC2G17DBVR` | PA0/PA1 (TIM2 CH1/2) |
| 2 | J502-3/4 | U502A/B | PA6/PA7 (TIM3 CH1/2) |
| 3 | J503-3/4 | U503A/B | PB6/PB7 (TIM4 CH1/2) |

- U501～U503は3.3V給電、各100nF。
- D501～D503は`ESDS452DBZR`。各エンコーダのA/Bをpin 1/2、pin 3をGNDへ接続する。5.5V working、2ch双方向、SOT-23-3。
- 信号順は**J501～J503 -> D501～D503 -> R511～R516 -> U501～U503 -> F405**。TVSはコネクタ直近、GND帰路を短くする。
- R511～R516は0603直列抵抗。初期値100Ω、実波形で0～100Ωを調整可能にする。
- U501～U503の共通pinoutはpin 1=`1A`、2=GND、3=`2A`、4=`2Y`、5=3V3、6=`1Y`。
- 各輪の対応は次表を正本とする。

| Wheel | A経路 | B経路 |
|---:|---|---|
| 1 | J501-3 -> D501-1 -> R511 -> U501-1 -> U501-6 -> PA0 | J501-4 -> D501-2 -> R512 -> U501-3 -> U501-4 -> PA1 |
| 2 | J502-3 -> D502-1 -> R513 -> U502-1 -> U502-6 -> PA6 | J502-4 -> D502-2 -> R514 -> U502-3 -> U502-4 -> PA7 |
| 3 | J503-3 -> D503-1 -> R515 -> U503-1 -> U503-6 -> PB6 | J503-4 -> D503-2 -> R516 -> U503-3 -> U503-4 -> PB7 |

- C511～C516は各バッファ入力からGNDへのRC調整用0603 footprintで、Rev.A初期実装はDNP。帯域計算と実波形確認前に容量値を決めない。
- 保護部品の正本: [TI ESDS452 datasheet](https://www.ti.com/lit/ds/symlink/esds452.pdf)。

### ICM-42688-Pブレークアウト

J601は購入モジュールの8信号を表す。実物の物理pin番号は到着後に確定する。

| モジュール信号 | Net / F405 |
|---|---|
| VCC | 3V3固定 |
| GND | GND |
| AD0/MISO | `SPI3_MISO` / PC11 |
| SDA/MOSI | `SPI3_MOSI` / PC12 |
| SCL/SCLK | `SPI3_SCK` / PC10 |
| CS | `IMU_CS_N` / PD2 |
| INT1 | `IMU_INT1` / PC4 |
| INT2 | `IMU_INT2` / PC5 |

- J601電源直近にC601=100nF、C602=2.2uF。
- 回路図上に`VCC=3.3V ONLY ON THIS BOARD`と注記する。
- モジュールのpin 1方向、pitch、1列/2列、固定穴は実物確認までfootprint未割当とする。

### Debug・ID・LED

- J701=`BM06B-GHS-TBT`: 1=GND、2=SWCLK(PA14)、3=SWDIO(PA13)、4=NRST、5=DBG_TX(PA2 USART2_TX)、6=DBG_RX(PA3 USART2_RX)。
- SW701=`DS04-254-1-03BK-SMT`: PC6/PC7/PC8を各switch経由でGND。内部pull-up、ON=Low。unitId=4はbit2だけON。旧A6S用footprintと列中心間8.9mm、縦pitch 2.54mm、pad寸法が一致する。
- D701 PWR緑、D702 RUN緑(PA5)、D703 COMM黄(PB10)、D704 ERR赤(PB11)。各1kΩ。
- PB3はSWOテストポイント。

## ローカルネットラベル一覧

```text
PWR_5V_IN  PWR_5V  3V3  VDDA_A  GND
COMM_TX  COMM_RX  COMM_A  COMM_B
W1_A  W1_B  W2_A  W2_B  W3_A  W3_B
SPI3_SCK  SPI3_MISO  SPI3_MOSI  IMU_CS_N  IMU_INT1  IMU_INT2
SWCLK  SWDIO  NRST  DBG_TX  DBG_RX
UNIT_ID0  UNIT_ID1  UNIT_ID2
LED_RUN  LED_COMM  LED_ERR
```

## 初回ERC前チェック

1. F405の全VDD/VSS、VDDA/VSSA、VBAT、VCAP_1/2が接続されている。
2. VCAPはコンデンサ以外へ接続されていない。
3. CANはPA12->TXD、RXD->PA11であり逆でない。
4. TCANのVCC=5V、VIO=3.3V、S=GND。
5. TLV1117のtab/pin2が3V3でありGNDでない。
6. AMT102コネクタは1=5V、2=GND、3=A、4=B。
7. IMUは3.3V給電で、CS/INTのLow active・方向を注記している。
8. SWD/UARTコネクタへデバッガ電源を入れていない。
9. 未使用MCU pinへNo Connect、意図的open-drain出力へ必要なERC処理を設定する。

## レンダリング済み参照図

2026-07-25生成、schemdraw製SVG(ゾーン/ブロック概観・箱と矢印とネット名のみ、ICピン配置やR/C定数は省略)。生成スクリプトは`figures/gen_odometry_overview.py`。

| 図 | 内容 |
|---|---|
| `figures/odometry-board-overview.svg` | 本書「1枚上の配置」を図示した全体ブロック図(電源チェーン→CAN、Debug/MCU/IMU、AMT102 x3) |

## CLI検証

回路図を閉じて保存後、プロジェクト名に合わせて実行する。

```powershell
.\tools\kicad\check.ps1 `
  -Project 'hardware/odometry-board/Oddom board/Oddom board' `
  -SkipDrc `
  -FailOnViolations `
  -OutputDirectory output/kicad/odometry-board
```
