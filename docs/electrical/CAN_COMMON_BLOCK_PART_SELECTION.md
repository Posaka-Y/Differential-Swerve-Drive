# CAN共通ブロック 部品選定

## 適用範囲

中央Teensy基板、差動ステアユニット基板、オドメトリ基板のClassic CAN 1Mbps回路へ共通適用する。価格・在庫は2026-07-19時点の少量購入スナップショットであり、発注時に再確認する。

## 確定構成

| 機能 | 採用品 | パッケージ/実装 | 代替・備考 |
|---|---|---|---|
| CANトランシーバ | TI `TCAN1051VDRQ1` | SOIC-8、リフロー | NXP `TJA1051T/3`を同一基本ピン配列の代替候補とする |
| CAN ESD/TVS | TI `ESD2CAN24DBZRQ1` | SOT-23-3、リフロー | 2線一括、双方向、VRWM ±24V、CAN専用品 |
| 終端抵抗 | Yageo `RC0603FR-07120RL` | 0603、120Ω、1%、0.1W | 同等の0603 120Ω 1%をAVLへ追加可 |
| 終端スイッチ | Littelfuse/C&K `JS102011SAQN` | SPDT、右向きGullwing SMT、IRリフロー対応 | Commonと片側throwだけ使用、反対側はNC |
| CAN基板ヘッダ | JST `SM03B-GHS-TB` | GH 3極、横挿しSMT | 正式図面上のめっき/梱包suffixを発注時照合 |
| CANハウジング | JST `GHR-03V-S` | GH 3極 | 全基板共通 |
| 圧着コンタクト | JST `SSHL-002T-P0.2` | AWG 30～26 | CAN/GNDとも原則AWG 26 |

外部ピン順は全基板で`1=COMM_A(CAN_H)、2=COMM_B(CAN_L)、3=GND`。中間ノードはGH 3pinを2個載せ、IN/OUTを電気的に区別しないパススルーとする。

## 選定比較

### CANトランシーバ

| 候補 | 電源/MCU I/O | バス耐性 | 実装・流通 | 採用判断 |
|---|---|---|---|---|
| `TCAN1051VDRQ1` | VCC=5V、VIO=3.3V | AEC-Q100、バスフォルト±58V、IEC ESD最大±15kV、Classic CAN対応 | SOIC-8、TI Active。DigiKey/Mouser/LCSCの複数正規流通。2026-07-19時点でDigiKey約2,969個、LCSC約129個、少量約US$0.82～2.50 | **採用**。24V誤配線・ノイズ余裕と修理性を優先 |
| `TJA1051T/3` | VCC=5V、VIO=3.3V | 車載CAN向け、高いバスフォルト耐性 | SOIC-8。candleLightFD、ARK CANnode等の公開設計で採用。基本ピン配列が採用品と一致 | **代替候補**。基板互換性を回路図レビューで維持 |
| `TCAN332DR` | 3.3V単一 | 動作コモンモード±12V、バス端子絶対最大±14V | SOIC-8、流通良好、約US$1.3～2.3 | 不採用。部品数は少ないが24V系での誤配線余裕が小さい |
| `SN65HVD230DR` | 3.3V単一 | 旧来品 | SOIC-8、採用例多数 | 不採用。RSピン処理を含め、TCAN1051Vより保護余裕が小さい |

`TCAN1051VDRQ1`のピンは`1=TXD、2=GND、3=VCC(5V)、4=RXD、5=VIO(3.3V)、6=CANL、7=CANH、8=S`。VCC-GNDとVIO-GNDへ各100nF X7R 0603をピン直近に置く。Rev.AではSをGNDへ固定してNormal modeとし、TXD dominant timeoutを利用する。

### CAN保護

旧候補`PESD1CAN-U`はNexperia公式でNot for Design In、`PESD2CAN`もNRNDのため新規採用しない。

`ESD2CAN24DBZRQ1`はTI Active、AEC-Q101、2ch双方向、SOT-23、±24V working voltage、IEC 61000-4-2接触±30kV、代表3pF。TCAN1051Vの±58Vバスフォルト耐性と組み合わせる。2026-07-19時点でMouser約91,000個、LCSC約3,600個、参考少量価格約US$0.2～0.7。

TVSはGHコネクタ直近に置き、`connector -> TVS -> transceiver`の順にする。TVS-GNDは短く太く、直近のGND planeへvia接続する。未保護配線を保護済み配線と並走させない。

### 終端

終端は`COMM_A -- 120Ω -- switch -- COMM_B`とする。スイッチは`JS102011SAQN`のCommonと片側throwのみ使用し、`TERM ON/OFF`をシルク表示する。メーカー仕様は0.3A@6VDC、5,000 cycles、-40～85℃、260℃ IR reflow対応。DigiKey/Mouserで数万個規模の在庫があり、少量約US$0.7～0.9。

120Ωには`RC0603FR-07120RL`を採用する。1Mbps CANの終端損失に対して0.1Wで余裕があり、DigiKey/Mouser/LCSCで広く流通する。バス物理両端だけスイッチをONにする。

## 回路・PCB制約

- GH IN/OUT間のCOMM_A/Bを本線として直線的に通し、トランシーバへのPCBスタブを目標20mm以下にする。
- GHヘッダは基板端の横挿し。常設ハーネスを基板面に沿って引き出す。
- TVSを外部コネクタ直近、トランシーバをその内側に置く。
- トランシーバのVCC/VIOデカップリングは各電源ピンから最短ループにする。
- 終端抵抗とスライドスイッチは本線近傍に置き、長い枝を作らない。
- COMM_A/Bは差動対として同一層・同一環境で配線し、連続GND plane上を通す。
- CAN活動LEDはCOMM_A/Bへ直接接続せず、MCU GPIOで駆動する。

## 公式資料・流通確認

- [TI TCAN1051V-Q1](https://www.ti.com/product/TCAN1051V-Q1)
- [TI ESD2CAN24-Q1 datasheet](https://www.ti.com/lit/ds/symlink/esd2can24-q1.pdf)
- [C&K JS series datasheet](https://www.littelfuse.com/assetdocs/littelfuse-c-k-slide-js-series-datasheet)
- [JST GH series](https://www.jst-mfg.com/product/index.php?series=105)
- [Nexperia PESD1CAN-U status](https://www.nexperia.com/product/PESD1CAN-U)
- [Yageo RC0603FR-07120RL at DigiKey](https://www.digikey.com/en/products/detail/yageo/RC0603FR-07120RL/726920)

## 実機確認

- 電源OFFでバス両端TERM ON時にCOMM_A-B間が約60Ω、片側だけONで約120Ωになること。
- 各中間ノードTERM OFFで抵抗値を変えないこと。
- 1Mbps連続通信でTX/RXエラーカウンタが増えないこと。
- ESD試験前に通常動作波形とリセッシブ/ドミナント電圧を保存すること。
- C620バスはC620内部終端の実測後に基板側TERMの既定状態を決めること。
