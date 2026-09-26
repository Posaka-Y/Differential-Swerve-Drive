# 中央基板 Rev.1 電源ブロック（24V→5V Buck）

**不採用(2026-09-14)。** 中央基板内蔵Buck方針は撤回し、外部24V→5Vモジュール(`SD-25B-5`)+`TPS259470`eFuseへ戻した。詳細は`ARCHITECTURE_DECISIONS.md`「中央基板 Rev.1 Buck」、`CENTRAL_BOARD_REQUIREMENTS.md`を参照。以下は参考として残す旧内容。

作成: 2026-09-12  
状態: **Buck IC・基本定数を確定。** USB ORing、24V入力保護部品、PCBレイアウトは後続作業で確定する。

この文書は `CENTRAL_BOARD_REV1_CONSTITUTION.md` の「24V入力・基板上Buck」実装詳細である。旧Rev.Aの外部5V入力/TPS259470回路は流用しない。

## 固定した仕様

| 項目 | 決定値 |
|---|---|
| 入力 | 6S LiPo由来 `+24V_SAFE`、通常22.2〜25.2V |
| 入力耐圧設計 | Buck IC 60V、入力MLCC 100V。通常電圧だけでなく配線サージの余裕を持たせる |
| 出力 | `+5V_MAIN`, 5.0V |
| 定格 | 5A連続（通常想定3〜4A） |
| スイッチング | 400kHz、Auto mode（RTは未実装/open） |
| Buck IC | **TI `LM76005RNPR`**、3.5〜60V入力・5A同期整流Buck、WQFN-30（6mm×4mm） |

`LM70660`（65V/6A）も比較したが、29pin QFN、外部シャント/補償の追加が必要である。Rev.1は、内部補償済みでTIに5V/5A・400kHzの完成設計例があるLM76005を採用する。QFN露出パッドは避けられないが、60V耐圧・5A同期整流・小さな外付け回路という利点が明確なため、設計憲法のQFN例外として採用する。

## 回路（Buck部分）

```text
+24V_SAFE ────────────────┬──── PVIN  U1 LM76005
                           │
                       CIN ceramic
                           │
GND ───────────────────────┴──── PGND/AGND

U1 SW ── L1 6.8uH ─────────────── +5V_MAIN ── load
                 │                    │
                BOOT                COUT bank
                 │                    │
              CBOOT 0.47uF          GND
                 │
                SW

+5V_MAIN ── RFBT 100k ──┐
                         ├── FB (U1)
GND ─────── RFBB 24.9k ─┘

RFBTと並列にCFF（初期220pF、C0G）
BIAS → +5V_MAIN （直近に1uF）
VCC  → 1uF → GND
SYNC  → GND（外部同期を使わない）
SS/TRK → NC（内部soft-start約6.3ms）
PGOOD → `PWR_5V_GOOD_N`（3.3Vへ10k pull-up。Teensy入力候補）
```

## 初期BOM・定数

| ref | 初期値 / 条件 | 備考 |
|---|---|---|
| U1 | `LM76005RNPR` | TI、WQFN-30 exposed pad。製造時は推奨land patternと露出パッド下のthermal-via arrayを厳守 |
| L1 | 6.8µH | **Isat 8A以上（できれば10A以上）**、低DCR。5A時にも飽和させない |
| CIN | 100V X7R MLCCを最低2×4.7µF、U1 PVIN/PGND直近 | リード/ハーネスが長い場合は、入力コネクタ近傍に別途47〜100µF/50V以上のダンピング用電解/ポリマーを追加 |
| CBOOT | 0.47µF、6.3V以上、X7R/X5R | BOOT-SW間、U1直近 |
| CVCC | 1µF、10V以上、X7R/X5R | VCC-GND間、U1直近 |
| CBIAS | 1µF、10V以上、X7R/X5R | BIAS-GND間。BIASは`+5V_MAIN`へ接続 |
| COUT | **5V印加時の実効容量合計180µF以上**、X7R中心 | 例: 16V定格100µF級MLCCを複数並列。定格容量ではなくメーカーDC-biasカーブで判定する。合計は800µF未満に保つ |
| RFBT / RFBB | 100kΩ / 24.9kΩ、1% | 5.0V設定（VFB=1V基準） |
| CFF | 220pF C0G、DNPではなく初期実装 | 上側FB抵抗と並列。COUT実効180µFを前提にデータシート式で得る約210pFをE24へ丸めた値。最終COUT実効値と負荷step測定で68〜330pF範囲を再調整可 |
| EN | `+24V_SAFE`直結を初期実装 | LiPo低電圧遮断をBuckに持たせるかは電池保護全体と合わせて後で決める。未決のUVLO閾値を今ここで勝手に固定しない |

## 固定するレイアウト規律

1. `CIN → U1(PVIN/PGND) → U1(SW) → L1 → COUT` の高di/dtループを最短・最小面積にする。
2. SW copperは必要最小限。FB/RFBT/RFBBをSW node、L1、入力コンデンサから離す。
3. U1露出パッドとPGNDは広いGND面と複数thermal viaへ接続する。`+5V_MAIN`は出力コンデンサ後からプレーン/ポリゴンで配電する。
4. 24V負荷用の大きな電流ループとBuckのPGND共有を短絡的に引き回さない。入力保護後の分岐点を明確にし、Buck入力コンデンサの帰路を最短にする。

## 未確定（次に決めるもの）

- XT30、入力ヒューズ、Pch MOS逆接保護、TVSの**正式型番と定数**
- `+24V_SAFE`を24V負荷へどこまで供給するかに基づく入力ヒューズ定格
- USB 5Vとの優先ORing（24V由来5V優先、双方逆流なし）
- LiPo低電圧保護をBuck ENで行うか、BMS/上位安全系で行うか
- `PWR_5V_GOOD_N`をTeensyへ入れるピンと、fault LED/ログへの利用

## 設計根拠

TIのLM76005データシートは、5V/5A・400kHzでL=6.8µH、COUT=180µF、RFBT=100kΩ、RFBB=25kΩを選定表として掲載している。5V設計例も5A/400kHzである。入力コンデンサ、bootstrap、VCC/BIAS、feedback、レイアウトは同データシートおよびEVMの規律を基準にする。

公式資料: [LM76005 datasheet](https://www.ti.com/lit/ds/symlink/lm76005.pdf)、[LM76005QEVM User's Guide](https://www.ti.com/lit/ug/snvu694a/snvu694a.pdf)。
