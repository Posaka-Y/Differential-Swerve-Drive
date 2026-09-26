# 差動ステア高応答化・実装引継ぎ計画

作成: 2026-09-12。状態: コードと既存試験記録に基づく計画。実装・実機試験は未実施。

## 目的と読み方

組付け後の機構について、操作から動き始めるまでの遅れ、操舵の到達時間、行き過ぎ後の再収束を改善する。
最高rpmだけを上げる計画ではない。まず浮上単輪で比較できる土台を整え、3輪浮上、接地へ進む。
数値ゲインや回生許容値はこの文書で新規確定しない。

後続実装者はチケットを一つずつ実装する。依存チケットが未完なら先へ進まない。
各チケットの成果物は「変更ファイル、変更理由、検証結果、未検証項目、次のチケット」を報告する。
機体書込み・通電・モータ試験はこの計画作成の範囲外。自動テスト合格と実機採用を区別する。

## 現状の根拠

| 観察 | 根拠 | 意味 |
|---|---|---|
| 角度P＋steer/drive mode PI、速度LPF、速度帯ゲイン補間、加減速FF、摩擦補償、相補observer、共通電流scale、back-calculationは実装済み | `firmware/src/control/unit_controller.c` の `unit_controller_update` | 新規実装としてやり直さず、接続と設定を調べる |
| 現在のソースは `BENCH_CONTROL_UART_ENABLED=1`。UART受信は角度・wheel速度・enableだけを更新 | `firmware/src/main.c` の `receive_bench_uart` と受信経路の条件分岐 | この経路ではCAN由来の操舵速度/加速度FFは供給されず、初期状態からは0となる |
| ESP送信周期20ms、ログ周期50ms。操舵はstickから角度へ変換し、現在角との差を±90°へ制限 | `esp32_gateway/include/gateway_config.h`、`src/main.cpp` | 7月の連続軌道ベンチと同じ制御入力ではない。50Hzだけを遅さの原因とは断定できない |
| boot設定はsteer上限60 axis rpm、steer ramp 600 axis rpm/s、current 4000raw | `firmware/src/main.c` の `control_config` | 7月末のRAM上の300rpm候補を現在の実機設定とみなせない |
| 7月末の3機構空走で90°初回到達平均約0.22〜0.23s、最大行き過ぎ約15〜16° | `firmware/PROGRESS.md` 冒頭のunit 1/2/3比較 | 初回到達は速いが、正確に落ち着くまでの時間は別の改善軸。3台の制御基板同時試験ではない |
| 現行wheel加速度FFは受信・保持されるが、drive電流FFへ接続されていない | `main.c` の `can_wheel_accel_ff_rpm_milli_per_s`、`unit_controller.c` | drive側の未実装候補。計測を見て必要な場合に追加する |
| 80〜235°帯の摩擦boostがコード内固定 | `unit_controller.c` の `ANGLE_FRICTION_BUMP_*` | 旧機構・校正角との対応を前提とした補償。組付け後に効く位置が正しいか未確認 |
| 1msポーリング制御、dtは最大10msへ丸める。debug UARTはTX待ちでブロック | `main.c` の主ループ、`firmware/src/platform/uart.c` | 公称1kHzと実周期は別。ログ起因ジッタは候補であり未計測 |
| Teensy側はハード非依存core。CAN/USB/安全I/Oは未統合 | `central_firmware/README.md` | 中央基板完成だけでは既存高速ベンチ相当の動作にはならない |
| Pythonはjerk=0の旧profile経路を持つがC++のtrajectoryはjerk>0を必須とする | `tools/linux/unit_web_ui.py`、`central_firmware/src/control/steer_trajectory.cpp` | 7月のjerk=0採用候補をC++へそのまま渡すと同じ動作にならない |

実機へ現在接続していないため、動いているバイナリ・RAM設定・機構版は未確認。
古いREADME/進捗には廃止済み構成や当時の「現在値」が残る。アーキテクチャは
`docs/ARCHITECTURE_DECISIONS.md` の日付付き決定、動作の実装は対象ソース、実機値はreadbackを使う。

## 改善の優先順位

1. 同じ入力・同じ設定で比較できるようにする。通信待ち、profile制限、追従遅れを分離する。
2. 実周期を確認し、ログ負荷の影響を除く。
3. 高速ベンチで使えていた軌道とFFを、実際に使う指令経路へ接続する。
4. 組付け後の摩擦補償を再評価し、小角度・切返し・再収束を詰める。
5. drive FFは駆動加速遅れが残る場合、DOBは接地負荷残差が確認された場合に進める。

## 比較指標

- 入力遅延: stick入力観測→送信→MCU受理→制御へ適用。異なる時計の値は同期なしで直接引かない。
- 操舵: 動き出し時間、最終目標の±2°への初回進入、行き過ぎ最大、±2°内で200ms保持するまでの時間。
- 既存の `MOTION_SETTLED` は別列で維持し、上記オフライン指標と混同しない。
- 駆動: ramp開始からの10–90%到達、整形後指令に対する追従誤差、停止時間、操舵への干渉。
- 制約: rpm包絡scale、ramp作動、最終電流scaleの率・継続時間、実peak速度、feedback age、周期最大値。
- 20Hzログでは50ms未満の改善を断定しない。隣接sample補間は推定であり、欠落区間を補間して成功扱いにしない。

初回到達だけで候補を採用しない。探索前に主指標を一つ選び、他の悪化許容値を固定する。
暫定の候補選抜目安は、同条件の基準に対して主指標の中央値を10%以上改善し、p95と最大行き過ぎを悪化させないこと。
これは提案する比較ルールであり機体の受入仕様ではない。少数試行では中央値・全試行・最大値を示し、p95を強い根拠にしない。
既存の空走20°行き過ぎ許容を接地へ持ち込まない。

## 実装チケット

### R01: 現在設定と試験条件のスナップショット

- 依存: なし。
- 対象: `tools/linux/unit_auto_tuner.py`、`unit_bench.py`、ESPログ取得/解析スクリプト、必要な設定応答。
- 作業: 機構ID、controller ID、入力経路、build ID、boot値とreadback値、全gain knot、FF、ramp、電流上限、原点、浮上/接地、電源条件を試験metadataへ保存する。
- 未取得値はunknownとする。現UARTに設定readbackがなければ、まずmanifestと取得可否だけ実装し、応答追加は別変更にする。
- 完了条件: 同一結果を再試験するのに必要な値と不足値が一つのmetadataから分かる。7月の値を勝手に実機へ適用しない。
- 検証: 欠落値、複数unit、RAM/boot不一致をfixtureで保存・再読込する。

### R02: 応答と制約の共通解析

- 依存: R01。
- 対象: `tools/linux/unit_auto_tuner.py`、`esp32_gateway/scripts/analyze_radio_telemetry.py`、必要なら共通解析module。
- 作業: 操作者の最終要求、整形後reference、制御内部command、実測を別列にする。上記の初回/保持/行き過ぎ/停止/制約率を共通定義で出す。
- 完了条件: 同じsynthetic traceならCAN/ESPの入力形式によらず同じ指標。不足列は評価不能と表示する。
- 検証: 正負step、359→1°、帯飛び越し、目標到達後の再逸脱、途中目標変更、sample欠落。任意のstickログからstep区間を無理に捏造しない。

### R03: 制御周期・鮮度の計測

- 依存: R01。
- 対象: `firmware/src/main.c`、`include/platform/clock.h`、`src/platform/clock.c`、出力診断。
- 作業: 実周期、実行時間、1ms deadline超過数、dt clamp回数、C620各motorの鮮度と時刻差、送信失敗/queue圧迫を固定容量の統計またはringへ記録する。制御中の文字列化を増やさない。
- 完了条件: idle/制御中/ログON/OFFを比較でき、元の実dtとclamp後dtを区別できる。計測offでは制御出力を変えない。
- 検証: timestamp wrapとcounter上限。実機で未計測なら「ジッタ改善済み」としない。

### R04: ログ送信を非ブロッキング化

- 依存: R03。ログによる待ち時間を計測してから効果判定する。
- 対象: `firmware/src/platform/uart.c`、`include/platform/uart.h`、`main.c`。必要なら `bench_uart.c` も監査。
- 作業: 固定長TX ringと送信budgetを導入し、満杯時は診断を捨ててdrop数を残す。ログ待ちで制御周期を伸ばさない。DMA/IRQへの大規模変更は必要性を測って別チケット化する。
- 完了条件: 接続先なし・高ログ負荷・ring満杯でも待ち続けない。故障状態はログ送信成功に依存せず保持する。
- 検証: ring wrap、満杯、連続enqueue。実機ではR03で前後比較。割込みを使う場合はvector対応を確認する。

### R05: 軌道生成のPython/C++互換性

- 依存: R02。
- 対象: `central_firmware/src/control/steer_trajectory.cpp`、対応header/test、`tools/linux/unit_web_ui.py`。
- 作業: jerk=0を既存Pythonの加減速制限profileとして明示サポートする。jerk>0も同一入力列でPythonとC++の位置・速度・加速度を比較するgolden fixtureを作る。
- 同時にwheelの加速/制動分離profileを中央coreへ用意する。反転中は速度の減少と増加で制限を選ぶ。
- 完了条件: 0/小角/90/170°、wrapを越える連続角、途中反転、可変dtで契約が一致する。既存jerk>0経路を保持する。
- 注意: 軌道値と微分の整合、終端snap時の扱いもテストする。gain tuningはこの変更に混ぜない。

### R06: 指令入口の契約と単輪試験アダプタ

- 依存: R01、R05。
- 対象: `central_firmware`、`firmware/src/main.c`、`firmware/src/platform/bench_uart.c`、`esp32_gateway/src/main.cpp`、通信仕様。
- 作業順: (a) command source、sequence、reference角/速度/加速度、wheel速度/加速度、validityの内部契約を文書化、(b) 一つのsourceだけを選ぶadapterを実装、(c) 単輪ベンチで同じreference列を再生する。
- 基本方針: 本番の軌道生成と3輪配分はTeensy。短期UARTベンチでFFを試す場合は明示的なベンチadapterとして扱い、ESPに独立した本番plannerを増やさない。
- UART wire formatを拡張する場合は別versionとして旧14byteとの誤認を防ぎ、送受信双方とparser fixtureを同じ変更で更新する。
- 完了条件: UART/Classic CANで同じ内部referenceを作れる。stale FF、source変更、enable切替で前経路のFFが残らない。freshnessはarrivalと適用を区別する。
- 検証: sequence wrap、重複、CRC不良、分割受信、欠落、旧frame、source切替。既存異常停止後の再arm latchを維持。

### R07: reference・FF・局所guardの整合

- 依存: R02、R06。
- 対象: `firmware/src/control/unit_controller.c`、対応header/test、`main.c`。
- 作業: 外部reference、rpm包絡適用後、局所ramp後の各値と制限理由を出す。通常軌道は上位で整形し、局所guardは残す。
- 制限時に入力加速度FFだけが元の大きさで残る問題を評価する。初期契約は、制約非作動時は明示FFを使用、作動時は整形後referenceに対応する有界加速度を使用し、その出所を診断する。
- 完了条件: FFと追従するreferenceの時間断面・単位が一致する。guard解除で不連続なFFが残らない。
- 検証: wheel/steer同時飽和、反転、FF timeout、dt変動。ramp後のmode和が `motor_max_rpm` 内かも検証し、逸脱が再現した場合は最終射影を別変更で追加する。

### R08: 組付け後の摩擦補償を設定化

- 依存: R02、R07。
- 対象: `unit_controller.c`、対応config/header、設定応答、試験metadata。
- 作業: 固定80〜235°boostのenable、開始/終了角、幅、倍率を設定へ移す。補償電流を独立診断列にする。現行と同じ設定で出力互換を先に確認する。
- 完了条件: OFF/旧値/個体別候補をA/Bできる。校正角を変更した際に古い角度mapを無条件に再利用しない。
- 検証: band端の連続性、0/360°をまたぐband、wheel速度とobserver速度によるfade。機械的抵抗を確認せず新mapを決めない。

### R09: 小角度・反転・再収束の調整

- 依存: R02、R04、R07、R08、および組付け後の基準ログ。
- 対象: 既存auto tuner、`unit_steer_mode_id.py`、試験preset。初期は制御式を追加しない。
- 作業: 5/15/30/90/170°の正逆、複数絶対角、wheel=0/正/負の比較。小角度では動き出し、90°では初回と再収束、途中反転ではreferenceと実速度の符号を分けて見る。
- 調整順: profile→加減速FF→外周moving/hold P→内周gainの一群ずつ。Kaw単独探索の優位は過去に再現していないため、無条件で再開しない。
- 完了条件: 基準/候補の交互試行で改善が再現し、全設定と復元値が保存される。速度cap300rpmと実peak300rpmを区別する。
- 再収束が残る場合だけ、終端減衰または制動判定の改善を別チケットにする。observerによる終端補償には過去の悪化例があり、常時追加しない。

### R10: drive加速度FF（条件付き）

- 依存: R07、R09。電流余裕があり、整形後wheel指令に対する加速遅れが残る場合。
- 対象: `unit_controller.c`、対応header、`main.c`、設定/診断、host test。
- 作業: wheel加速度をdrive mode単位へ換算し、係数0を既定としてdrive PI後・共通電流scale前に追加する。正負加速/制動を区別する。
- 完了条件: 係数0で旧出力互換。timeout/停止/resetでFFを消す。FF込みの要求と適用電流を記録する。
- 検証: 単位換算、正逆、飽和、steer同時動作。C620 raw電流指令をbattery電流と同一視しない。

### R11: 通常減速停止と異常disableの区別

- 依存: R06、R07。操作の停止感を改善する場合。
- 対象: ESP入力状態、中央状態機械、単輪adapterとテスト。
- 作業: 正常通信中の通常zero要求と、通信断/異常/非常停止を別eventにする。通常停止のみprofileで減速し、実速度と期限で完了判定する。
- 完了条件: 通常停止中でも異常eventが即座に優先される。通信断時に古い指令を延長しない。既存のR1解放即disable挙動を無断で置換せず、入力意味の変更をチケット冒頭に明記する。
- 検証: 減速中切断、再接続、連打、停止完了しない場合、異常後の再arm要求。

### R12: 本番3輪への接続

- 依存: R05〜R09、中央ハード/ドライバ仕様確定。
- 一度に実装せず、R12a=既存32byte TRAJECTORY_FDとCOMMITのcodec、R12b=pending/sequence/timeout、R12c=G474局所補間、R12d=Teensy配信、R12e=3輪回帰に分ける。
- 対象: `docs/communication/COMMUNICATION_NAMING_AND_IDS.md`、`central_firmware`、G474のFDCAN層とcommand adapter。
- 正本にあるCOMMITでの適用方式を使い、独自の絶対時計同期方式を追加しない。pending欠落時の継続時間上限と3輪停止への集約を実装前に明文化する。
- 完了条件: 同一sequenceのreferenceが3輪に適用され、欠落/重複/古い区間を識別できる。48byte状態frameのsequence echoを解析に使う。
- 検証: codecのgolden bytes→時刻/sequence wrapと欠落のhost test→出力無効で通信→3輪浮上→低速接地の順。
- 3輪では最遅輪の遅れと輪間適用差も測る。単輪で得た最速設定をそのまま本番採用しない。

## 後回しにするもの

DOB/LESO、observer角への外周P置換、MPC、traction controlは今回の初手にしない。
接地でFFとPIでは吸収できない負荷残差が出たときに、既存 `LOAD_ADAPTIVE_CONTROL_ROADMAP.md` へ接続する。
observerはすでに摩擦fadeとgain scheduleへ使われているが、角度Pと安全判定への採用は別審査になる。

## 実機条件と電源側の依存

浮上試験でも、過去に300 axis rpmからの急制動で電源保護停止が発生した。
既存方針の「260rpm超・24V未計測時の制動は500 axis rpm/s以下」を維持する。
この値は操舵軸速度試験の暫定条件であり、wheel rampや3輪の安全を一括保証する数値ではない。
制動側の上限引上げはbus電圧・電流を測れる分電構成とセットで評価する。バスバー設計自体は本計画に含めない。

## 後続モデルへの依頼テンプレート

> `docs/control/RESPONSE_IMPROVEMENT_PLAN_2026-09-12.md` の Rxx だけを実装する。
> 先にAGENTSと依存チケットの成果を確認する。現行コードを読み、実装済み機能を再実装しない。
> 対象ファイルと完了条件を満たす最小変更を行う。新しい判断が必要な箇所は推測でゲインや電気上限を決めず、未決事項として報告する。
> unit制御変更は `firmware/scripts/test-host.sh` と `firmware/scripts/build.ps1`、中央core変更は `central_firmware/scripts/test-host.sh` を実行する。
> スクリプト変更は該当self-checkと境界fixtureを確認する。使えない環境では未実行と理由を報告し、成功と書かない。
> 実機へ書込み・駆動はしない。boot値・原点を勝手に変えない。既存のユーザー変更を保持する。
> 最後に変更内容、検証結果、実機で残る確認、次のチケットを進捗へ記録する。

最初の着手はR01。R01/R02/R03が揃うと、遅延・指令生成・摩擦・電流制約のどこから改善すべきかを実測で選べる。
