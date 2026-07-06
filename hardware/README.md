# hardware

KiCadによる基板設計。共通ブロック方針は `docs/electrical/CARRIER_BOARD_BUILD_PLAN.md` 冒頭を参照。

## 構成

```text
hardware/
  lib/             共通シンボル・フットプリントライブラリ
  blocks/          共通階層シート(can_interface, power_input_5v, status_led, mcu_min_g474)
  unit-board/      差動ステアユニット基板(STM32G474RET6)
  central-board/   中央制御ボード(Teensy 4.1)
  odometry-board/  オドメトリ基板(STM32G474RET6 + I2C磁気エンコーダ x3)
  reference/       流用元プロジェクト(下表)
```

## 流用元(reference/)

| 参照 | 形式 | 流用するブロック | ライセンス |
|---|---|---|---|
| `candleLightFD/` ([linux-automation/candleLightFD](https://github.com/linux-automation/candleLightFD)) | **KiCadソース**(階層シート: MCU / PSU / transceiver) | CANトランシーバ周り(TJA1051T/3 + 100nF + 120Ω)→ TCAN332に置換して `blocks/can_interface` の下敷きにする。階層シートの切り方・リリースフォルダ構成(製造データの出し方)も運用の手本になる | CERN-OHL v1.2(流用時はライセンス表記を維持) |
| `mks-canable-v2.0-schematic.pdf` ([makerbase-mks/CANable-MKS](https://github.com/makerbase-mks/CANable-MKS)) | PDF回路図 | STM32G431のMCU最小構成(電源、BOOT0、水晶、SWD)。G474RET6版を起こすときの照合用 | 回路図公開(リポジトリ記載に従う) |
| `nucleo-g474re-mb1367-c05-schematic.pdf`(ST MB1367)**※未取得** | PDF回路図 | **G474RET6そのものの最小構成の正解例**(VDD/VDDA処理、NRST、BOOT0、HSE周り)。ピンごとのデカップリング数の確認はこれを正とする | ST評価ボード回路図(参照用) |
| `ARK_CANNODE/` ([ARK-Electronics/ARK_CANNODE](https://github.com/ARK-Electronics/ARK_CANNODE)) | PDF回路図 + BOM(`Hardware/Rev 1/`) | 逆接保護(LM66100)、CANコネクタ2個並列のデイジーチェーン渡り、外部信号のESDダイオード、TJA1051+FET切替終端(参考のみ)。詳細は`CARRIER_BOARD_REQUIREMENTS.md`「回路図作成メモ」 | リポジトリのLICENSE参照 |
| `datasheets/` | データシートPDF | AMT22 rev1.10(コネクタピン順1=+5V/2=SCLK/3=MOSI/4=GND/5=MISO/6=CS)、PESD1CAN rev04(1/2=ライン、3=GND) | メーカー資料(参照用) |

※ MB1367回路図はst.comが自動取得を弾くため手動ダウンロードが必要:
<https://www.st.com/resource/en/schematic_pack/mb1367-g474re-c05_schematic.pdf>(または c04)。取得したらこのフォルダに上記ファイル名で保存する。

## 設計ルール

- 回路図のネット名は `docs/communication/COMMUNICATION_NAMING_AND_IDS.md` の命名に従う(`COMM_A/B`、`C620_CAN_*`、`PWR_*`、`_N`)。
- ピン割当は `docs/electrical/CARRIER_BOARD_REQUIREMENTS.md`(ユニット)/ `ODOMETRY_BOARD_REQUIREMENTS.md`(オドメトリ)の表が正本。
- シンボル・フットプリントは`lib/`に置き、KiCad標準ライブラリ依存を減らす(後続プロジェクトへの持ち出しやすさ優先)。
- 発注前チェックは `docs/checklists/REVIEW_CHECKLIST.md`。
