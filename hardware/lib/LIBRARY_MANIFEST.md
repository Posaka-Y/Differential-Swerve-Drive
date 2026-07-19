# KiCad部品ライブラリ構成

## 方針

このフォルダは「正式型番のpinoutを誤りやすい部品」と「KiCad標準にない特殊footprint」だけを保持する。抵抗、コンデンサ、LED、STM32、汎用SOT/SOICなどをコピーせず、KiCad標準ライブラリを利用する。

各基板ディレクトリの`sym-lib-table`/`fp-lib-table`からこのライブラリを相対参照する。日本語を含む絶対パスは保存しない。

## 現在収録済み

シンボルは2026-07-19にSamacSys(Component Search Engine)からダウンロードした正式型番モデルを取り込んだもの。ダウンロード時の誤りを修正済み(照合記録参照)。元zipは`LIB_<型番>.zip`。

| 部品 | Project symbol | Footprint | 状態 |
|---|---|---|---|
| `TCAN1051VDRQ1` | `DifferentialSwerve:TCAN1051VDRQ1` | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | SamacSys由来。pin 5をNC→VIOへ修正、pin typeをデータシート通りに設定 |
| `ESD2CAN24DBZRQ1` | `DifferentialSwerve:ESD2CAN24DBZRQ1` | `Package_TO_SOT_SMD:SOT-23` | SamacSys由来。pin 1/2=IO、3=GND一致 |
| `LM66100DCKR` | `DifferentialSwerve:LM66100DCKR` | `Package_TO_SOT_SMD:SOT-363_SC-70-6` | SamacSys由来。pin typeをデータシート通りに設定 |
| `JS102011SAQN` | `DifferentialSwerve:JS102011SAQN` | `DifferentialSwerve:JS102011SAQN` | SamacSys由来。pin 1の誤no_connectをpassiveへ修正。**footprintはメーカー図面との照合が未実施** |
| `S1751-46R` | 標準`Connector:TestPoint` | `DifferentialSwerve:Harwin_S1751-46R` | Harwin推奨pad 3.45x1.85mmで作成 |

footprintはSOIC-8/SOT-23/SC-70-6とも照合済みのKiCad標準を割り当てた(SamacSysのIPC名footprintは使わない)。JS102011SAQNのみSamacSys footprintを取り込み(2.5mmピッチSMD 3pad+位置決めNPTH 0.9mm x2)、発注前に図面照合する。

## KiCad標準を使う部品

| 正式型番 | Symbol | Footprint |
|---|---|---|
| `STM32G474RET6` | `MCU_ST_STM32G4:STM32G474RETx` | `Package_QFP:LQFP-64_10x10mm_P0.5mm` |
| `TLV1117LV33DCYR` | `Regulator_Linear:TLV1117-33`を公式pinoutと照合 | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` |
| `BAT54SLT1G` | `Device:D_Schottky_x2_Serial_AKC` | `Package_TO_SOT_SMD:SOT-23` |
| 3225-4pad HSE | `Device:Crystal_GND24` | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |
| `SM02B-GHS-TB` | `Connector_Generic:Conn_01x02` | `Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal` |
| `SM03B-GHS-TB` | `Connector_Generic:Conn_01x03` | `Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal` |
| `BM06B-GHS-TBT` | `Connector_Generic:Conn_01x06` | `Connector_JST:JST_GH_BM06B-GHS-TBT_1x06-1MP_P1.25mm_Vertical` |

## まだ作らないもの

- JST GH: KiCad公式footprintが存在するためコピーしない。使用時にJST最新版の推奨land patternと照合する。
- `TLV1117LV33DCYR`: 標準シンボルを使うが、tab=VOUT/pin2であることを回路図レビューで再確認する。

## 導入方法

KiCadのPreferences → Manage Symbol Libraries / Footprint Librariesから、プロジェクト単位で次を登録する。

```text
Symbol:    hardware/lib/DifferentialSwerve.kicad_sym
Footprint: hardware/lib/DifferentialSwerve.pretty
```

基板プロジェクトからは`${KIPRJMOD}/../lib/...`のような相対パスを使う。Windows/WSL固有の絶対パスをコミットしない。

`hardware/lib/sym-lib-table`と`hardware/lib/fp-lib-table`はテンプレートであり、この場所ではKiCadに読まれない。各基板プロジェクトの`.kicad_pro`と同じディレクトリ(`hardware/unit-board/`等)へコピーして使う。URIは`${KIPRJMOD}/../lib/...`で書いてあり、基板ディレクトリが`hardware/lib`の兄弟である前提。それ以外の階層に置く場合は相対パスを合わせて直す。

## 照合記録(2026-07-19)

公式データシートを`hardware/reference/datasheets/`へ保存し、シンボルと1:1照合済み。

| 部品 | 資料 | 結果 |
|---|---|---|
| `TCAN1051VDRQ1` | `ti-tcan1051.pdf`(SLLSET0D、D package V系列) | 1=TXD/2=GND/3=VCC/4=RXD/5=VIO/6=CANL/7=CANH/8=S 一致 |
| `ESD2CAN24DBZRQ1` | `ti-esd2can24-q1.pdf`(SLVSFW5D、DBZ) | 1,2=IO/3=GND 一致 |
| `LM66100DCKR` | `ti-lm66100.pdf`(SLVSEZ8A、DCK) | 1=VIN/2=GND/3=CE̅/4=NC/5=ST/6=VOUT 一致。STはopen-drain=open_collector型 |
| `S1751-46R` | `harwin-s1751r-drg-02202.pdf`(DRG-02202 iss.10) | 推奨pad 3.45x1.85mm、本体3.25x1.63mm 一致 |

### SamacSysダウンロード品の取り込み記録(2026-07-19)

Component Search Engineから`LIB_TCAN1051VDRQ1.zip`、`LIB_ESD2CAN24DBZRQ1.zip`、`LIB_LM66100DCKR.zip`、`LIB_JS102011SAQN.zip`を取得し、各zipの`KiCad/<型番>.kicad_sym`を1ライブラリへ統合した。ダウンロード品に以下の誤り・不足があり修正した。

| 部品 | SamacSys原品の問題 | 適用した修正 |
|---|---|---|
| `TCAN1051VDRQ1` | **pin 5が`NC`(no_connect)**。V系列の実物はpin 5=VIO(I/O電源、3.3V接続必須) | pin 5を`VIO`/power_inへ修正 |
| 全シンボル共通 | 全pinがelectrical type `passive`でERCが機能しない | TXD/S/CE̅=input、RXD=output、GND/VCC/VIN/VIO=power_in、VOUT=power_out、ST=open_collector、CANH/L=bidirectionalへ設定(ESD保護とスイッチはpassiveのまま) |
| `JS102011SAQN` | pin 1(切替接点)がtype `no_connect`で、接続するとERCエラーになる | passiveへ修正 |
| 全シンボル共通 | Footprint欄がライブラリ名なしの裸のIPC名(例`SOIC127P600X175-8N`)で解決不能 | 照合済みKiCad標準footprint(JS102011のみ`DifferentialSwerve:JS102011SAQN`)へ変更 |
| 全シンボル共通 | Reference prefixが`IC`/`S`等 | KiCad慣例の`U`/`D`/`SW`へ変更 |

pin番号・名称は上表「照合記録」のデータシート照合結果と一致することを確認済み。ファイルはKiCad 6世代フォーマット(version 20211014)のため、KiCad 10 GUIで開いて保存し直すと現行フォーマットへ正規化される。GUIでのロード確認・symbol checkerは未実施。

## 発注前確認

1. Symbol pin番号をメーカー最新版datasheetと一対一照合する。
2. Footprint pad番号、寸法、courtyard、pin 1表示をメーカー推奨land patternと照合する。
3. KiCad 3D表示ではなく、1:1 PDF印刷または寸法測定で確認する。
4. ERC/DRC合格だけでpinout/land patternの正しさを保証したとみなさない。
