# Firmware progress

最終更新: 2026-07-07(SET_CONFIG追加、動摩擦同定、積分フロアで低速stick-slip大幅改善)

## 完了(2026-07-07 低速stick-slip対策: SET_CONFIG+積分フロア)

- CAN `SET_CONFIG`(0x141)でランタイムパラメータ変更を実装・実機確認(reflash不要で調整可能に)。
  併せて動摩擦FF(idx14)・積分フロア(idx15)・動作判定しきい値(idx16)を追加(既定0=無効)。
- Linux評価ツール`tools/linux/unit_bench.py`を新規作成(socketcan直、必ずdisable送信)。
  `st-info --probe`→`flash.sh debug`でこのLinux機からの書き込みも初成功。
- 動摩擦電流を定常iDrive法で同定: **約200 raw(185〜215)、速度依存なし、正逆対称**。
  ブレークアウェイ~850との差がstick-slipキックの定量的原因と確定。
- A/B試験の結論: **積分フロア=200+driveKp=10**で、40rpmはp-p 213→19.6・固着66%→0%、
  25rpmも固着0%で連続回転化。150rpmは無退行(mean 150.0)。FF併用は過速NG。
  詳細は`firmware/docs/CONTROL_LOOP_TUNING.md`の同日セクション。

現在の状態(2026-07-08更新):
- **採用値をすべて`main.c`既定値へ焼き込みflash済み**: driveKp=10、積分フロア=200、
  動作しきい値=5、動作開始時積分クランプ=400(idx17、2026-07-08追加実装)。
- クランプ400で25rpm 3回連続固着ゼロ(p-p 17〜47、ばらつきは機構の角度依存の
  引っかかり由来)。40rpmはp-p 16。ユーザー所感とも一致:「機構上改善はできない
  引っかかりがあり、それがオーバーシュートの原因」— 制御側はfloor+クランプで
  通過トルク確保と過剰キック抑制まで対応済み。

次の作業:
1. 接地・負荷ありでの摩擦再同定とフロア/クランプ値の見直し(負荷下では引っかかりの
   相対影響は縮む見込み)。
2. 恒久対策が必要なら角度インデックス摩擦マップ(CALフェーズ、
   `docs/control/CALIBRATION_AND_ADAPTATION_PLAN.md`)。
3. 中央Teensy/mini PCからの連続軌道(`unit_bench.py profile`)での評価。

## 完了(2026-07-07 mini PC LinuxからのCANable smoke test)

## 完了(2026-07-07 mini PC LinuxからのCANable smoke test)

- `docs/testing/MINIPC_LINUX_HANDOFF.md`に従い、mini PC(Ubuntu 22.04)側の評価環境を構築。
  - `python3-serial`追加導入(can-utils/dialoutは既存Linux環境整備で導入済み)。
  - USBデバイス判別に注意: `/dev/ttyACM0`は**ST-Link V3のVCPパススルー**(ユニットのdebug UARTログが
    ここに出る)、`/dev/ttyACM1`が実際の**CANable2**(slcan)。ハンドオフメモの`ttyACM0`前提は
    このPC構成では逆だったため、`slcand -o -c -s8 /dev/ttyACM1 can0`で接続した。
  - `sudo ip link set can0 up`後、`ip -details link show can0`で`UP`/`ERROR-ACTIVE`確認
    (`bitrate 0`表示はslcanインターフェース仕様上の既知表示で異常ではない)。
- ホイールを浮かせた状態でメモ記載の単発smoke(`SET_TARGET`1回→`enable=1`→3秒→`enable=0`)を実施し、
  `candump`と`/dev/ttyACM0`(VCP)を同時キャプチャして正常動作を確認:
  - `SET_TARGET_RX steer=90000 wheel=500000`受信、`START_CAN`後angleが90000mdeg付近(err±2000)へ収束、
    wheelがランプ増加。
  - 単発送信のため周期`SET_TARGET`が止まり、想定どおり`STOP: target timeout`→`UNIT_CTRL enable=0`で安全停止。
- ログ保存: `firmware/logs/linux-minipc-smoke-vcp-2026-07-07T23-29-46.log`、
  `firmware/logs/linux-minipc-smoke-candump-2026-07-07T23-29-46.log`。

次: mini PC側で周期送信スクリプト(メモのCodex prompt例、20〜50Hzで`SET_TARGET`を送り続けるPython実装)を
作成し、単発smokeではなく実際の連続駆動評価に進む。

## 進行中(2026-07-07 CANable手入力consoleの落ち挙動切り分け)

- CANable手入力consoleで、周期的に「落ちる」ように見える挙動が発生。
- 現ファームには電流増加率しきい値で停止する処理はないため、主候補は`STOP: target timeout`。
  PowerShellのキー入力/表示処理で`SET_TARGET`周期が一瞬200msを超え、停止→再STARTしている可能性が高い。
- 対策コードは実装・ビルド済み:
  - `TARGET_TIMEOUT_MS`を200ms→1000msへ変更。
  - `STOP: target timeout`時に`unit_enabled=false`へラッチし、通信断でSTOP/STARTを繰り返さないように変更。
- ただしflashは`invoke-hardware-session.ps1`が`busy`を返したため未反映。
  おそらく手元のconsole sessionがmutexを保持中。ユーザーがconsoleで`q`を押して終了後、再flashが必要。
- wheel rpmが1300rpm以上に見える件:
  - ファーム内の理論上限は`motor_max_rpm=469 * 32/11 = 約1364 wheel-rpm`なので、1300台自体は異常ではない。
  - ただし運用上1200rpmまでにしたいため、console側に`MaxAbsWheelRpmMilli`を追加し、既定を±1200rpmへ制限。
  - `run-canable-target-console-session.ps1`からも同パラメータを渡せるようにした。
- PowerShell構文チェック:
  - `run-canable-target-console.ps1`: OK
  - `run-canable-target-console-session.ps1`: OK

現在の状態:

- 実機flash上は、まだtimeout 200ms版の可能性が高い。
- ワークツリー上のfirmwareはtimeout 1000ms + timeout停止ラッチ版。
- consoleスクリプトは±1200rpm上限版。

次:

1. 手元consoleで`q`を押して終了し、mutexを解放。
2. `.\firmware\scripts\flash.ps1`でtimeout修正版をflash。
3. consoleを再起動し、VCPログの`STOP:`行で落ち原因を確認。

## 完了(2026-07-07 CANable手入力コンソール追加)

- CANableから手入力で`θs`/`ωw`を変えられる操作スクリプトを追加。
  - `firmware/scripts/run-canable-target-console.ps1`
  - `firmware/scripts/run-canable-target-console-session.ps1`
- 操作は`invoke-hardware-session.ps1`経由のsession版を使う前提。操作中はmutexを保持し、
  終了時はconsole側finallyとSafeIdle側の両方で`UNIT_CTRL disable`を送る。
- キー操作:
  - `e`: enable
  - `d`: disable
  - `q`: quit
  - 上下矢印: wheel rpmをstep増減(既定25rpm)
  - 左右矢印: steer角をstep増減(既定5°)
  - `z`/`x`: steer角を-90°/+90°
  - `0`: wheel=0
  - `h`: status表示
- `SET_TARGET`は既定50ms周期(20Hz)で常時送信。起動直後はdisableを送ってから待機。
- PowerShell構文チェック成功。対話操作はユーザーのコンソール入力が必要なため、ここでは未実行。

次: 実機で以下を使って手入力確認。

```powershell
.\firmware\scripts\run-canable-target-console-session.ps1 -CanPort COM16 -InitialSteerMdeg 179912 -InitialWheelRpmMilli 0
```

## 完了(2026-07-07 CANable経由SET_TARGET実動作確認)

- `firmware/src/main.c`を中央CAN(FDCAN1)の実指令で動くベンチアプリへ変更。
  - `SET_TARGET` ID `0x101`: int32 little-endian `steer_mdeg` + int32 little-endian `wheel_rpm_milli`
  - `UNIT_CTRL` ID `0x121`: `01 01`でenable、`01 00`でdisable
  - 起動時は必ずdisabled。`SET_TARGET`は200ms timeout、B1/温度/センサ/C620 timeout/角度発散は停止。
  - 安全停止時は`unit_enabled=false`へラッチし、角度発散時の再START連打を防止。
- CANable用スクリプトを追加:
  - `firmware/scripts/run-canable-target-smoke.ps1`: SET_TARGETを周期送信し、enable後に短時間動かしてdisable。
  - `firmware/scripts/run-canable-target-session.ps1`: `invoke-hardware-session.ps1`経由でflash→smoke→SafeIdle(disable)。
  - `firmware/scripts/send-canable-unit-disable.ps1`: CANableからUNIT_CTRL disableだけを送る。
- 実機確認:
  - CANable COM16、G474 VCP COM15、NUCLEO-G474RE。
  - `θs=179912mdeg`, `ωw=500000milli-rpm`を20Hzで送信し、`UNIT_CTRL enable=1`後に`START_CAN`。
  - wheel commandはランプで500rpmまで到達し、角度誤差は最終的に0〜0.6°程度。
  - `UNIT_CTRL enable=0`で`STOP: disabled`、SafeIdleのdisable送信も成功。
- 最終状態:
  - 最新CAN制御ファームをflash/verify/reset済み。
  - 実機は起動時disabled、最後に`t12120100`をBody/SafeIdle両方で送信済み。

次: mini PC側または中央Teensy相当の送信器から、`θs`/`ωw`の連続プロファイルを生成して評価する。
まずはPC上のCANable送信ツールを、単発smokeではなく任意軌道/CSV/キーボード入力で使える形にする。

## 完了(2026-07-07 wheel RPM staircase試験ハーネス高速化)

- `firmware/src/main.c`の閉ループベンチ試験を、単一RPMではなく複数RPMを1回のflashで順次実行する
  staircase形式へ変更した。現在のステップは40/45/50/60/75/100/150 wheel-rpm。
- 1ステップが`STEP_TIMEOUT_MS`内に安定しない場合は`STEP_FAIL`を出して次RPMへ進む。
  角度発散、温度上限、センサ/C620 timeout、B1 abortは従来どおり即停止。
- `firmware/scripts/compact-test-log.ps1`をstep別集計に対応させ、1本のログから各RPMの後半mean/min/max/p-pと
  角度誤差を出せるようにした。
- `firmware/scripts/build.ps1`でDebugビルド成功。`compact-test-log.ps1`のPowerShell構文チェック成功。
- まだ実機flash/駆動はしていない。安全ゲートは`CLOSED_LOOP_TEST_ENABLED=0`のまま。

次: 実機セッションではmutex wrapper経由でこのstaircase HEXを1回だけflashし、ログ取得後にsafe-idleをflashする。

## 完了(2026-07-07 wheel 40rpm単点試験)

- C620 raw rpmを`/19`した既定ゲイン(steer Kp/Ki=50/20、drive Kp/Ki=5/20)で
  wheel 40rpmを10秒評価。後半平均33.999rpm、範囲-0.032〜243.561rpm、角度誤差peak
  1.670°、m1/m2非ゼロ率32%/34%で、停止・再始動を伴うスティックスリップのためFAIL。
- 2回目はdrive Kiだけ20→30へ変更したが、実行ツールがtimeoutしログ未生成のため評価不能。
  追加駆動は行わず、Ki=20へ戻した。最終状態は`CLOSED_LOOP_TEST_ENABLED=0`をclean buildし、
  mutex内でflash/verify/reset成功済み。ログ: `docs/tuning_logs/2026-07-07_wheel_40rpm_run1.log`。

最終更新: 2026-07-07(wheel 40rpm単点試験、FAIL)

## 完了(2026-07-06 C620 rpm単位修正・RPM点分割試験)

- C620 `feedback.rpm` はM3508内蔵19:1減速機より前のロータrpmと判明。制御器の
  `motor_max_rpm=469`、運動学、目標値は減速後出力軸rpmなので、`main.c`のmeasurement境界で
  raw feedbackを19で除算した。イテレーション12〜17は目標と測定の単位が19倍ずれており、
  そこから導いた「250rpmでも悪化」「低速域原因説を否定」は無効として扱う。
- 修正後、単一モーター50 output-rpmはKp=5/Ki=20で概ね47〜54rpmへ追従。
  差動wheel試験は暫定構成(steer Kp=50/Ki=20、drive Kp=5/Ki=20、current limit=2000、
  integral limit=1200)で50/60/75/100/150/250rpmを各10秒完走。25rpmは周期的な停止・再始動でNG。
  40rpmは正式な再試験が必要。正逆転および各点3回の再現性確認は未実施。
- RPM点ごとに短命エージェントを起動する`.claude/agents/wheel-rpm-point-tuner.md`、最新の
  `START:`〜`STOP:`だけ保存・集計する`scripts/compact-test-log.ps1`、実機処理を直列化して
  必ず安全待機を実行する`scripts/invoke-hardware-session.ps1`を追加。
- 別セッションが`main.c`を試験有効へ再編集していたため、競合中の実機試験は中止。
  `CLOSED_LOOP_TEST_ENABLED=0`へ戻し、clean build、flash、verify、reset済み。競合側が繰り返し
  `=1`へ戻したため、停止確認まで`main.c`を読み取り専用属性にして安全値を固定している。

次: 他セッションの編集停止を確認後、40rpmを正逆転・3回で判定。その結果を境界として
最低安定rpmを二分探索し、上限側は既知安定点から段階的に探索する。全実機操作はmutex wrapper経由。

## 完了(2026-07-06 単一モーター速度制御の追試、5アーキテクチャとも発振)

- 二モーター差動を切り離し、motor1単体・motor2=0固定で5種類のアーキテクチャを試験
  (詳細は`firmware/docs/CONTROL_LOOP_TUNING.md`「単一モーター速度制御の追試」参照):
  1. 単純rpm PI(KP=5,KI=100) → 激しいスティックスリップ限界サイクル
  2. +測定rpmへの一次LPF → 改善なし(キックは実際の動きでノイズではないと確認)
  3. +初期キック電流(1200raw) → キック自体は成功もPI移行後は同じ振動が継続
  4. 仮想シャフト位置追従(C620のrotor_angleで位置制御) → 改善なし
  5. 目標rpmを50→250へ引き上げ(低速域回避仮説) → **悪化**。低速域原因説は否定
- **結論**: 5種類ともKP=5/KI=100の内側電流PIゲインは共通で、外側アーキテクチャ変更では
  解決しないことを確認。ユーザーが目視した「モーターのガクガクした動き」は指令送信の
  不連続バグではなく、1kHzで正しく更新され続けている指令値自体が数百ms周期で
  大きく振動していることの物理的な現れと確認。
- セッション終了時、`CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で書き込み・verify・reset済み。
- 無負荷ベンチでのこれ以上の深追いは費用対効果が低いと判断し保留。

次: KIを大幅に下げる(100→20〜30程度)実験は未実施のまま保留。実走行(接地・負荷あり)で
摩擦特性を取り直すのが優先度高いかもしれない。

## 完了(2026-07-07 Linux機のビルド・書き込み環境整備)

- 開発機(Ubuntu 22.04、これまでのWindows/PowerShell環境とは別の作業PC)に
  ファーム開発ツールチェーンが未導入だったため、ユーザーと相談の上apt版で整備する方針を確定:
  - ARM GCC: 公式Arm GNU Toolchain 14.2(Windows側)ではなく、apt版
    `gcc-arm-none-eabi`(10.3-2021.07-4)を採用(手動導入の手間を避けるため)。
  - 書き込みツール: 公式`STM32CubeProgrammer`(ST公式サイトでのアカウント登録必須)ではなく、
    apt版`stlink-tools`(st-flash 1.7.0)を採用。
  - `ninja-build`(1.10.1)もaptで導入。
- `sudo apt-get install gcc-arm-none-eabi ninja-build stlink-tools`でインストール
  (初回は`unattended-upgrades`がdpkgロックを保持しており一時失敗、時間を置いて再実行で成功)。
- udevルールはパッケージ既定の`/lib/udev/rules.d/49-stlinkv*.rules`で足りており追加設定不要と確認。
- `firmware/scripts/build.sh debug`でビルド成功を確認(FLASH使用0.92%、RAM 1.19%)。
- `firmware/scripts/build.sh`・`flash.sh`に実行権限(`chmod +x`)が付いていなかったため付与。
- `flash.sh`を`STM32_Programmer_CLI`(Windows側専用、未導入)から`st-flash --reset write
  <bin> 0x08000000`(stlink-tools)呼び出しへ書き換え。`.hex`ではなく`.bin`成果物を使う点に注意。

### 現在の状態

- このLinux機でのビルドは動作確認済み。書き込みは未検証(作業時点でST-Link/ボード未接続、
  `st-info --probe`は0件)。ボード接続後に`./scripts/flash.sh debug`での実機書き込み確認が必要。
- Windows側の`build.ps1`/`flash.ps1`/`toolchain.ps1`(Arm GCC 14.2 + STM32CubeProgrammer前提)は
  無変更。今回の変更は`build.sh`/`flash.sh`(Linux用)のみ。

### 次の作業

1. ST-Link(NUCLEO-G474RE搭載のものでも可)をこのPCへ接続し、`st-info --probe`で認識確認。
2. `./scripts/flash.sh debug`で実機書き込みが成功するか確認する
   (ARM GCCバージョン差異(10.3 vs 14.2)によるバイナリ挙動差にも注意して見る)。

## 完了(2026-07-06 rpm発散ガード撤去・駆動ステップ10秒完走)

- ユーザー指摘: 「current_limitで既にハードクランプされているのだから、rpm誤差ベースの
  発散ガードは無駄」。閉ループのwheelステップテストからガードを撤去し、停止条件を
  角度発散(12°)・センサ/C620タイムアウト・B1・最大試験時間(10秒)のみに縮小。
- 再試験の結果、**誤停止なく10秒間完走**。イテレーション10のブレークアウェイ(~850raw)は
  再現し、m1/m2の実測rpmは試験中ずっと非ゼロで振れ続けた(スティックスリップ的な断続動作、
  滑らかな50rpm定常回転ではない)。
- **新知見**: 保持していたはずの操舵角が、開始から終了まで継続的に±0.5〜1.1°振動し続けた
  (単発ドリフトではなく持続的振動)。角度P制御が常にこの外乱を追いかけて
  `steer_rpm_command`が±2rpmを往復。差動機構の駆動→操舵への機械的カップリングが
  想定より強く持続的であることを示す実測データ(`CENTRAL_COORDINATED_CONTROL.md`の
  非干渉性検証項目1の裏付け)。
- セッション終了時、`CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で書き込み・verify・reset済み。
- 詳細は`firmware/docs/CONTROL_LOOP_TUNING.md`「イテレーション11」参照。

次: (1) 持続的な操舵振動への対策(カップリング補正項の要否、angle_deadband見直し等)。
(2) スティックスリップを抑えて滑らかな定常回転に近づける`drive_mode_ki`/
`wheel_accel_rpm_per_s`のチューニング。

## 完了(2026-07-06 駆動(差動)電流ブレークアウェイの開ループ確認)

- 前段(下記「駆動モードwheel≠0ステップ応答テスト」)のイテレーション9で見た
  `measured_wheel_rpm`の巨大スパイクについて、ユーザーから「実機は全然回っていない」との
  指摘を受け、PIを完全に排除した開ループ試験で切り分け。`main.c`を
  「motor1=+I, motor2=-Iの純粋差動電流を500raw/sでランプし、生のC620 rpm/torque_currentを
  20ms周期でそのままログする」テストへ書き換え。ホイールは接地させず浮かせて実施。
- 結果: **電流852(raw、current_limit=2000のうち)でm2rpm=-32を検出し正常にブレークアウェイ**。
  それまでm1/m2の生rpmはほぼ0(±3程度のノイズのみ)で、イテレーション9のような異常値は
  一度も出なかった。**C620フィードバック自体は健全と確認**。イテレーション9のスパイクは
  フィードバックのバグではなく、ブレークアウェイ瞬間の実際の機械的キック(スティックスリップ
  解放)だった可能性が高いと訂正。
- 結論: ホイールは実際に動く(固着・破損していない)。静止摩擦を破るのに約850raw
  (current_limit=2000の半分弱)必要なだけ。閉ループ試験(イテレーション8/9)が失敗していたのは、
  PIの積分がその電流に安定して到達する前に発散ガードへ引っかかっていたため。
- セッション終了時、`CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で書き込み・verify・reset済み。
- 作業中、Bashツール経由(cmd.exe)で`serial-monitor.ps1`を呼ぶと日本語コメント入りスクリプトで
  文字化け・パースエラーが発生する事象を確認。PowerShellツールから直接呼べば問題なし
  (関連: AGENTS.mdの日本語パス起因cmd.exe文字化け注意)。

次: このブレークアウェイ電流(~850raw、方向依存で変動しうる)を踏まえ、閉ループの発散ガードを
「瞬間的なブレークアウェイキックを誤検出しない設計」に見直し、`drive_mode_ki`/
`wheel_accel_rpm_per_s`を再チューニング。モード非干渉(操舵ドリフト-0.615°)の定量評価も残作業。
詳細は`firmware/docs/CONTROL_LOOP_TUNING.md`「駆動(差動)電流のブレークアウェイ確認」参照。

## 進行中(2026-07-06 駆動モード(wheel≠0)ステップ応答テスト)

- `main.c`を「操舵を起動角に保持しつつwheel目標を0→50rpmへステップ」するテストへ書き換え
  (`unit_controller_set_target`のwheel_rpm引数を初めて非ゼロで使用)。モード非干渉の確認と
  `wheel_accel_rpm_per_s`/`drive_mode_ki`の実機評価が目的。ホイールは接地させず浮かせて実施。
- 発散ガード(rpm誤差20rpm、ユーザー指定)を追加したが、初版はランプ完了直後に判定したため
  ブレークアウェイ電流に届く前に誤ってSTOP(モーターほぼ無回転のまま)。
  1.5秒の猶予期間(`WHEEL_ERROR_CHECK_GRACE_MS`)を追加して再試験。
- 猶予期間ありの再試験で`measured_wheel_rpm`計算値が単発で300〜500rpm相当まで跳ね上がり、
  発散ガードが誤発動して停止。**当初「フィードバックのノイズ/バグ」と誤診断したが、
  上記の開ループ確認で否定。ブレークアウェイの実キックだった可能性が高い。**

次: 上記「駆動(差動)電流ブレークアウェイの開ループ確認」参照。

## 完了(2026-07-06 serial-monitor.ps1 早期終了オプション)

- `scripts/serial-monitor.ps1` に `-EarlyExit` スイッチを追加。閉ループ試験ログを
  行単位で解析し、収束(|err|<500かつsteer=0が`-StableSamples`(既定4)連続)または
  `STOP:` 行を検出したら `-TailSeconds`(既定2秒)後に自動終了する。
  イテレーションあたり~8秒の短縮見込み。
- VCPバッファ再生対策: 接続後 `-StartIgnoreSeconds`(既定5秒)以内のSTART行は
  前回ファームの古いデータとして無視。flashが5秒未満で完了した場合は早期終了せず
  従来通りDurationSecondsまで走る(誤検出側に倒れない設計)。
- `-EarlyExit` 未指定時の挙動は完全に従来通り(実行中セッションへの影響なし)。
- 検証はハードウェア非接触で実施(構文チェック+判定ロジックのオフライン
  ユニットテスト7ケース、全PASS)。**実機での動作確認は次回チューニング
  イテレーションで行うこと。**
- gain-tuning SKILL.md の監視コマンドを `-EarlyExit` 付きに更新。

## 完了(2026-07-06 ゲイン調整再開・Ki確定)

- ユーザーがステア軸の手回し点検(引っかかり・ガタ・異音・AMT連れ回りズレ)を実施、異常なしを確認。
  通電試験を再開。
- イテレーション5: `mode_integral_limit=1200`込みで前回ベスト構成の実機再現に成功
  (~3.25秒、終端誤差0.07〜0.16°、発振なし)。積分クランプ導入の影響なしと確認。
- イテレーション6: `steer_mode_ki` 100→125で改善(~3.0秒、終端誤差0.02°、
  軽微な1サンプルのみのオーバーシュート、発振なし)。
- イテレーション7: `steer_mode_ki` 125→150(安全上限)は125より悪化(~3.25秒、
  誤差0.332°、Ki=100相当まで後退)。150は採用せず、**125を確定値**とした。
- `drive_mode_ki`は100のまま据え置き(wheel=0の操舵専用試験のため未検証。駆動実走時に個別調整)。
- セッション終了時、`CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で書き込み・verify・reset済み。
- gain-tuningスキルのシリアル監視時間をユーザー要望で45秒→15秒に短縮
  (収束が~3秒程度のため十分)。パラメータ表・ベスト実績も更新。
- 詳細は `firmware/docs/CONTROL_LOOP_TUNING.md` 実験ログ(イテレーション5〜7)参照。

次: Ki(操舵)は125で確定。次はangle_kp/steer_accelの詰め、または駆動モード
(wheel≠0)実走テストへ。drive_mode_kiは駆動実走時に別途検証が必要。

## 完了(2026-07-06 制御ループ改善: RoboMaster系実装との比較)

- RoboMaster系オープン実装(DJI公式C板例/standard_robot系)のM3508カスケード制御と
  現行モード座標PIを比較。構造は同等と確認し、欠けていた3点を導入:
  1. `mode_integral_limit`=1200(RM系max_iout相当の積分独立クランプ。固着中に積分が
     ±2000まで溜まって解放時に跳ぶ経路を遮断。Ki=200発振の一因への対策)
  2. 合成電流飽和時のモード比例スケーリング(m1/m2個別クランプによる操舵/駆動トルク比の
     歪みを解消)+飽和次周期の積分凍結。`torque_scaling_active`をログ出力に追加
  3. `wheel_accel_rpm_per_s`=200(駆動目標のランプ。値は未実測、実走テストで調整)
- 詳細と採用しなかった項目は `docs/CONTROL_LOOP_TUNING.md`「RoboMaster系オープン実装との
  比較と取り込み」参照。「mA」表記が実はC620生値(±16384=±20A)という単位注意も記録。
- Debugビルド成功(FLASH 4736B / RAM 1168B)。**実機未検証**(機構の手回し点検待ちのため
  通電試験は中断中のまま)。`CLOSED_LOOP_TEST_ENABLED=0`維持。

次: 手回し点検 → イテレーション3構成の再現確認(本変更込み。挙動差はiLimit=2000で切り分け)
→ Ki/angle_kpの詰め → 駆動実走。

## 方針更新(2026-07-06 CAN-G474主試験機)

- 購入済みMatek CAN-G474(STM32G474CE、CAN 2系統)を今後の主試験機とする。
- 購入済みCAN-L431は中央CANの対向ノード、NUCLEO-G474REは書込み復旧と回帰確認の予備とする。
- 現行ファームはNUCLEO固定ピンであり、そのままではCAN-G474へ移せない。CAN1 PA11/PA12は共通だが、
  CAN2をPB12/PB13からPB5/PB6へ、AMT22をSPI3 PC10/PC11/PC12+PD2から
  SPI2 PB13/PB14/PB15+PB12へ切り替えるボード定義が必要。
- G474CE(512KB Flash)のメモリ容量は現行G474REと同じだが、パッケージと露出ピン、LED、
  デバッグUARTが異なる。SWDまたはUART1 DFUで最小bring-upを完了してからモーターへ接続する。
- `docs/MATEK_CAN_G474_PORT.md`を作成。ArduPilot hwdef/AP_Periphの参照範囲、GPLコードを
  直接コピーしない方針、底面SWD+ST-LINKの配線、工場ブートローダとFlash配置の競合、
  復旧準備、段階bring-up、ボード別platform実装タスクを記録した。

次: CAN-G474実機の電源・SWD・Device ID/Option Bytes確認と工場ファーム復旧手段の確保 → ボード別ピン定義 → LED/GPIO実行確認 → CAN 2系統試験。

## 完了(2026-07-05 モード座標制御・ゲイン調整)

- unit_controllerをモード座標PI(操舵=和/駆動=差)へ書き換え。摩擦FFは
  実測ばらつき(150〜950mA、角度依存)を理由に廃止し、積分のみで吸収する方針に確定。
- 電流ランプ式の摩擦特性化テストを実装・実測(4方向×4試行)。
- テストアプリをB1保持式から起動時自動開始+B1中断ラッチ式へ変更。
- ゲイン調整4イテレーション実施。ベスト構成(Kp=5/Ki=100、steer_min_rpm=2、
  accel=50、limit=2000)で+10°を約3.5秒・終端誤差0.37°・オーバーシュートなし。
- **Ki=200は±2°の激発振(NG確定)。** 発振直後の試験で角度が-114°逆走して発散停止。
  機構損傷の可能性があり、通電試験を中断。**次回はユーザーの手回し点検から。**
- ST-LINK VCPの滞留バッファが古いログを再生する罠を確認(START行より前は捨てる)。
- 調整ループを他モデルへ委譲できるよう整備:
  `.claude/skills/gain-tuning/SKILL.md`(ランブック)と
  `.claude/agents/gain-tuner.md`(sonnet固定エージェント)。
- 詳細は `docs/CONTROL_LOOP_TUNING.md` の実験ログ参照。
- `CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で引き渡し。

次: 手回し点検 → イテレーション3構成の再現確認 → gain-tunerエージェントで
Ki 100〜150 / angle_kp の詰め → 駆動モード実走テスト。

## 完了(2026-07-05 C620 CAN受信テスト実装)

- C620公式フィードバック形式(標準ID 0x201〜0x208、8byte、角度/rpm/トルク電流/温度)のデコーダを追加。
- FDCAN2を通常モード/クラシックCAN 1Mbpsで起動し、電流指令を送らず受信だけ行うテストアプリへ変更。
- 受信全件を処理し、ID 1/2の最新値・フレーム数・受信経過時間・PSRをVCPへ250ms周期で表示。
- Debugビルド成功(FLASH 3372B / RAM 1080B)、NUCLEO-G474REへの書き込み・verify・reset成功。
- COM15実測: ID 1/2ともfeedbackなし、unknown=0、PSR=0x70f。CANフレーム未検出。
- MCP2551の5V給電を修正後、ID1/ID2ともC620フィードバック受信に成功。
  age=1ms、温度28/27℃、静止rpm=0を確認し、手回しで角度・rpmが変化した。
  PSR=0x708/0x710、unknown=0。電流指令は未送信。ベンチ段階2合格。
- ベンチ段階3開始。B1押下中のみID1へ指令値+200(約0.24A)、最大500msでゼロへ戻す
  ガード付きテストを実施。C620 #1は微小動作し、モーター上部から見て時計回りを確認。
- 同じガード条件でC620 #2も微小動作し、モーター上部から見て時計回りを確認。
  両モーターのフィードバックと低電流指令動作を実機確認し、ベンチ段階3合格。
- テスト後は誤操作防止のため、ID1〜4へ10ms周期で0電流だけを送る安全待機アプリへ変更。

次: ベンチ段階3。ホイールを浮かせ、安全な電流上限を実装してから0x200へ微小電流指令を送る。

## 進行中(2026-07-05 差動閉ループ・自動同定)

- 目標ホイールrpm/目標ステア角を入力とする制御層を追加。角度P、ステア速度/加速度制限、
  操舵優先rpm配分、差動逆運動学、2モーターrpm PI、静止摩擦補償を実装。
- B1長押し中のみ現在角+10°を指令し、解放/2秒/AMT異常/C620受信途絶/角度発散で0電流へ戻す安全ゲートを実装。
- 高ゲインPIでは低速域で電流が正負飽和して振動したため、ゲイン推測を止め、共通モードの
  ブレークアウェイ電流を300〜800で自動測定する同定アプリへ変更。
- 正負両方向とも指令800までrpm=0、AMT角度変化=0。C620実トルク電流は指令へ追従
  (例: cmd=-800, fbI1=-794, fbI2=-789)しており、CAN/指令生成は正常。
- それ以前の固定-800試験ではステア軸が2〜3周動作しているため、現在は電源CC制限・24V降下・
  機械拘束など実機条件が変化した可能性が高い。追加増流は禁止し、実機切り分け待ち。
- 原因は安定化電源の電流制限(CC)だったことをユーザー確認。C620実トルク電流が指令へ追従しても
  電源側で出力が制限され、rpm/AMTが動かなかった。電源設定修正後の再同定待ち。
- 電源CC設定修正後、個別ブレークアウェイを自動測定。Motor 1は約814〜1009、Motor 2は
  約814〜1022で始動し、初期キック1125を設定した。
- 個別rpm PI+瞬時rpm閾値によるキック切替は、静止付近のrpmノイズで左右非同期になり振動した。
  目標+10°に対して有意な角度移動は得られず、2秒タイムアウトで安全停止した。
- 次回方針を`docs/CONTROL_LOOP_TUNING.md`へ記録。モーター個別PIをやめ、操舵(和)/駆動(差)の
  モードPI、rpmフィルタ、同期キック(固定時間+ヒステリシス)へ変更する。
- セッション終了時、`CLOSED_LOOP_TEST_ENABLED=0`としてB1動作を無効化。安全待機で引き渡す。

次: `docs/CONTROL_LOOP_TUNING.md`に従いモード座標制御を実装し、監督付き試験時のみ
`CLOSED_LOOP_TEST_ENABLED=1`へ変更して+10°応答を再確認する。

## 完了(2026-07-04 AMT22ベンチテスト実装)

- SPI3(PC10=SCK、PC11=MISO、PC12=MOSI、PD2=CS_N)のAMT222A-Vドライバを追加。
- SPI Mode 0 / 1MHz、CS前後・バイト間3us、2バイト個別転送、チェックビット検証を実装。
- 12bit位置と角度を100ms周期でST-LINK VCP(115200bps)へ出力するテストアプリへ変更。
- NUCLEO CN7配線を起動ログへ表示し、起動後250msの静止待ちを追加。
- Debugビルド成功(FLASH 2976B / RAM 1032B)。実機書き込みとVCPログ確認は未実施。
- 書き込み試行時、接続されていたのは想定のNUCLEO-G474REではなくNUCLEO-G431RB
  (ST-LINK SN `0031004E3532510831333430`, VCP COM14)だった。G474向けHEXの書き込みと
  verify/resetまでは成功したが、対象不一致のためAMT22実機評価は中止。正しいG474REへ
  接続し直して再書き込みが必要。
- NUCLEO-G474REへ交換後、SN `0033003E3532510731333430` / 3.32V / 512KBとして検出し、
  AMT22テストファームの書き込み・verify・resetに成功。VCPはCOM15。
- `scripts/serial-monitor.ps1`を追加。ST-LINK VCP自動検出または`-Port COM15`指定で常時表示可能。
- COM15実測は`raw=0x0 pos=0 angle=0.0 deg check=ERROR spi=OK`。MCU側SPI転送は完了するが
  AMT222から有効応答を受信できていない。5V/GND、Pico-Lockのピン番号、MISO配線を実測確認する。
- 配線再確認後、AMT222のセンサー値取得を実機確認済み(2026-07-04、ユーザー確認)。
  次は手回しで`check=OK`の継続、0〜4095の範囲、回転方向、一周時のラップを記録する。

次: AMT222A-VをCN7へ配線し、`scripts/flash.ps1`で書き込み、VCPログの`check=OK`と手回し時の角度変化を確認する。

## 完了(2026-07-02 ベンチ段階1)

- `platform/uart.c` を追加: LPUART1(PA2/PA3、ST-LINK VCP直結)115200bps、最小printf(%s %c %d %u %x)。
- `platform/fdcan.c` を追加: G4固定メッセージRAMレイアウト対応のベアメタルFDCANドライバ。
  - クラシックCAN 1Mbps(HSI16 PCLK直、BRP=1、16tq、サンプルポイント87.5%)
  - FDCAN1(中央CAN、PA11/PA12 AF9)、FDCAN2(C620、PB12/PB13 AF9)
  - 内部ループバックモード、全受信→FIFO0、送信3スロットFIFO、ポーリング送受信
- `stm32g4xx_min.h` を拡張: RCC(APB1ENR1/2、CCIPR)、GPIOB、LPUART1、FDCANレジスタ定義。
- main.cを段階1テストアプリに変更(両バスのループバック検証、LED表示、5秒ハートビート)。
- **実機確認済み**: NUCLEO-G474REで両FDCANともPASS。
  VCP実ログ: `[FDCAN1/central] PASS (id=123 dlc=8 PSR=708)` / `[FDCAN2/C620] PASS` / `result: ALL PASS`。
  PSRのLEC=0(プロトコルエラーなし)。COM13でハートビート継続動作確認。

次: ベンチ計画の段階2(MCP2551配線→C620フィードバック受信)。C620プロトコルのエンコード/デコード実装が必要。

## 完了(2026-07-02)

- Arm GNU Toolchain 14.2.Rel1をwingetで導入した(`C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\14.2 rel1`)。
- `scripts/toolchain.ps1`を追加した。STM32Cube拡張バンドル(`%LOCALAPPDATA%\stm32cube\bundles`)のCMake/Ninja/Programmer/GDBとArm GCCを自動発見してPATHへ載せる。build.ps1/flash.ps1から自動で読み込まれるため、手動PATH設定は不要になった。
- `.vscode/launch.json`にgdb/GDBサーバ/Programmerの実体パスを明示した(従来はPATH頼みでデバッグ起動不可だった)。
- CMakeのPOST_BUILDを相対パス化した。日本語を含む作業パス(`趣味`)がcmd.exe経由で文字化けし、objcopyが失敗する問題の回避。
- Debugビルドが通ることを確認した(FLASH 848B / RAM 1032B、ELF/HEX/BIN/MAP生成)。
- `flash.ps1`でNUCLEO-G474RE(SN 004F002C3532510731333430)のFlashへ書き込み、ベリファイ成功、リセット実行した。Flash上のSTデモは本ファームで上書きされた。

## 完了(2026-07-01以前)

- firmwareプロジェクトのGCC/CMake/Ninja構成を作成した。
- テスト対象をNUCLEO-G474RE / STM32G474RET6へ変更した。
- B1 USER (PC13、押下High) とLD2 (PA5、High点灯) の実機ピンを確認した。
- B1を押している間だけLD2を点灯する処理と20 msデバウンスを実装した。
- PowerShell/POSIXのビルド・書き込みスクリプトを追加した。
- VS Code、CMake Preset、ST-LINKデバッグ設定を追加した。
- SRAM診断コードを正規ベクタ付きで高位SRAMから実行し、B1→LD2動作を実機確認した。
- ST-LINK firmwareをV3J9M3からV3J17M10へ更新した。
- STM32CubeProgrammer 2.22.0で再認識を確認した。
- ST-LINK GDB Server 7.13.0が接続待機まで進むことを確認した。
- Bring-up、書き込み時の注意、エンコーダ段階テストを`docs/BOARD_BRINGUP.md`へ記録した。

## 現在の実機状態

- Flashには本プロジェクトのB1→LD2ファーム(Debugビルド)が書き込み済み。ベリファイ・リセットまで確認。
- 人手での実機動作確認(B1を押している間だけLD2点灯、RESET後も維持)が未実施。

## 未完了・次の作業

1. RESET後もB1を押している間だけLD2が点灯することを実機で確認する(人手)。
2. エンコーダはAMT22で確定(絶対値SPI、5V、Mode 0、≤2MHz、バイト間2.5µs/リード間40µs/CS解放前3µs、上位2bitチェックビット)。詳細は `docs/electrical/CARRIER_BOARD_REQUIREMENTS.md` 参照。全信号3.3V直結でよい。
3. AMT22のSPI読み取りを実装する(`docs/BOARD_BRINGUP.md`の段階テスト準拠)。
4. ~~搭載ボードを確定する~~ → **2026-07-02時点ではNUCLEO-G474RE、2026-07-06に主試験機をMatek CAN-G474へ変更。** 中央通信の2バスCAN構成は維持し、NUCLEOは予備とする。startupファイルは `startup_stm32g4xx.s` にリネームし、CMakeLists更新済み。
5. FDCAN1/FDCAN2のピン割当をCubeMXで確定し、morphoに出ていることを確認する(`docs/electrical/CARRIER_BOARD_REQUIREMENTS.md`参照)。

## 環境上の注意

- 現セッションでは`.git/index`が読み取り専用で、Gitコミットを作成できなかった。
- firmware、`.vscode`、`.gitignore`の変更はワークツリーへ保存済み。
- CADや既存docsの別作業変更は今回のfirmware作業へ含めないこと。

## wheel staircase試験(2026-07-07)

- `invoke-hardware-session.ps1`経由で実機試験を2回実行し、各回とも終了後に
  `CLOSED_LOOP_TEST_ENABLED=0`のsafe-idleをflash/verify/resetした。最終状態もsafe-idle。
- 標準staircase(40/45/50/60/75/100/150rpm、drive Kp/Ki=5/20、steer Kp/Ki=50/20):
  全stepが`STEP_OK`で完走。`firmware/logs/staircase-2026-07-07T04-31-33-622Z.log`。
  `STEP_OK`直前1秒の代表値:
  - 40rpm: 31.06〜46.13rpm、平均40.74rpm、角度誤差max 0.97°
  - 45rpm: 43.94〜51.99rpm、平均47.78rpm、角度誤差max 1.76°
  - 50rpm: 45.00〜59.00rpm、平均49.57rpm、角度誤差max 1.58°
  - 60rpm: 51.51〜68.58rpm、平均60.91rpm、角度誤差max 1.58°
  - 75rpm: 69.67〜84.93rpm、平均80.27rpm、角度誤差max 0.53°
  - 100rpm: 85.54〜104.89rpm、平均92.52rpm、角度誤差max 0.62°
  - 150rpm: 131.29〜159.61rpm、平均151.50rpm、角度誤差max 0.88°
- 低速staircase(一時的に25/30/35/40rpmへ変更):
  `firmware/logs/staircase-lowrpm-2026-07-07T04-34-11-016Z.log`。
  25rpmと35rpmは`STEP_OK`、30rpmと40rpmはtimeout。角度誤差は最大10.37°まで出たが、
  12°の停止ガードには届かなかった。結果が非単調なため、低速限界は単純なrpmしきい値ではなく
  始動角・局所摩擦・駆動→操舵カップリングに依存している可能性が高い。
- 暫定判断: 現ゲインでは正転・無負荷・この姿勢の「一発通過」なら40rpm以上は動くが、
  30〜40rpm帯は再現性未確定。最低安定rpmとして採用するには、角度誤差ガードを厳しめ
  (例: step内6°程度)にして、正逆・開始角を変えた複数回試験が必要。

次:
1. 低速境界を詰めるなら、同一rpm単点を開始角を変えて3回ずつ実施し、30/35/40rpmの再現性を判定。
2. 角度外乱が大きいので、次のゲイン調整はdrive Kiを上げる前に操舵保持側
   (`angle_kp_rpm_per_deg`、`steer_max_rpm`、`steer_mode_ki`)を少し戻す試験を優先。
3. ログへ`torque_scaling_active`を出して、STEP_OK判定と集計で飽和有無を直接確認できるようにする。

## wheel staircase試験(2026-07-07 追加: 操舵保持強化と中高速)

- 試験ハーネスを更新:
  - `torque_scaling_active`を`scale=`としてログ出力。
  - `compact-test-log.ps1`でstep別の電流スケーリング率を集計。
  - step内角度誤差が6°を300ms超えたら、そのstepを`STEP_FAIL: angle`として次へ進める
    ガードを追加(12°超の即停止ガードは維持)。
- 操舵保持を少し強化:
  - `steer_max_rpm`: 0.5 -> 1.0
  - `angle_kp_rpm_per_deg`: 0.1 -> 0.2
  - `steer_mode_ki`: 20 -> 30
- 低速再試験(30/35/40rpm): `firmware/logs/staircase-lowrpm-steerhold-2026-07-07T04-42-02-928Z.log`
  - 30rpm: timeout、終了時 measured 0rpm、angleErr -1.406°
  - 35rpm: timeout、終了時 measured 0.001rpm相当、angleErr 0.176°
  - 40rpm: `STEP_OK`、直前1秒平均39.37rpm、p-p 11.94rpm、角度誤差max 0.44°
  - 全体の最大角度誤差は3.43°、`scale=1`は0%。操舵外乱は大きく改善したが、
    30/35rpmは角度ではなく駆動側stick-slipで不合格。
- 中高速試験(40/75/150/250/350rpm): `firmware/logs/staircase-highrpm-steerhold-2026-07-07T04-44-49-432Z.log`
  - 全stepが`STEP_OK`で完走、`scale=1`は全step 0%。
  - 直前1秒:
    - 40rpm: 平均39.36rpm、p-p 9.34rpm、角度誤差max 0.70°
    - 75rpm: 平均69.23rpm、p-p 11.18rpm、角度誤差max 0.79°
    - 150rpm: 平均148.84rpm、p-p 20.77rpm、角度誤差max 0.53°
    - 250rpm: 平均239.55rpm、p-p 50.40rpm、角度誤差max 1.14°
    - 350rpm: 平均345.75rpm、p-p 81.13rpm、角度誤差max 0.79°
- 暫定判断:
  - 下限は40rpm。30/35rpmは現状の無負荷正転では採用しない。
  - 350rpmまでは電流飽和なし・操舵保持良好で通過。速度p-pは高速ほど増えるため、
    次は500/750/1000rpm級へ段階拡張し、`motor_max_rpm`由来のwheel上限(約1360rpm)に近づける。
- 最終状態:
  - 実機は`CLOSED_LOOP_TEST_ENABLED=0`のsafe-idleをflash/verify/reset済み。
  - `firmware/src/main.c`は次回用に40/75/150/250/350rpm staircase、操舵保持強化、
    step角度FAIL、`scale=`ログを残し、`CLOSED_LOOP_TEST_ENABLED=0`。

## wheel 長時間・拘束領域試験(2026-07-07)

- ユーザー指摘により、従来の1秒安定判定では定常評価が短すぎるため試験ハーネスを変更:
  - `STEP_TIMEOUT_MS=25000`
  - `STEP_MIN_DWELL_MS=10000`
  - `STEP_STABLE_MS=3000`
  - 拘束時に要求rpmとの差でtimeoutしないよう、安定判定を要求targetではなく
    `output.wheel_rpm_command`基準へ変更。
  - `STEP_OK/STEP_FAIL`へ`cmd=`を追加。
- 長時間staircase(500/750/1000/1200/1400rpm要求):
  `firmware/logs/staircase-long-highrpm-constraint-2026-07-07T04-49-46-624Z.log`
  - 全step `STEP_OK`、実機は終了後safe-idleをflash/verify/reset済み。
  - 直前1秒:
    - 500rpm: 平均500.03rpm、p-p 5.06rpm、角度誤差max 0.53°、scale 0%
    - 750rpm: 平均749.72rpm、p-p 3.99rpm、角度誤差max 0.62°、scale 0%
    - 1000rpm: 平均1000.10rpm、p-p 2.96rpm、角度誤差max 0.62°、scale 0%
    - 1200rpm: 平均1200.27rpm、p-p 2.50rpm、角度誤差max 0.62°、scale 0%
    - 1400rpm要求: `cmd`平均約1363rpm、実測平均1363.49rpm、p-p 1.86rpm、
      角度誤差max 0.62°、scale直前1秒0%
  - step全体のfinal-half集計では1400rpm要求stepで`scale=1`が0.8%。ただし安定窓では0%。
- 判断:
  - 500〜1200rpmは10秒保持後に非常に安定。無負荷・正転ではdrive PIは十分。
  - 1400rpm要求は`motor_max_rpm=469`とdrive比32/11によるwheel上限約1364rpmに拘束され、
    制御器の`wheel_rpm_command`も約1363rpmへ制限される。拘束領域でも角度保持は良好。
  - 現時点の無負荷正転レンジ: 下限40rpm、上限は約1360rpm(機構/設定上限)。30/35rpmは不採用。
- 次:
  1. 正転だけでなく逆転(-40/-500/-1000/-1400)を同じ長時間保持で確認。
  2. `STOP: `が空で出るログ行を修正し、完走時は`STOP: staircase complete`を確実に出す。
  3. 接地・拘束状態へ移る前に温度ログを集計へ追加し、長時間高負荷で温度上昇を見る。

## wheel 逆転代表点試験(2026-07-07)

- 逆転側の代表点として -40/-500/-1400rpm 要求を長時間保持で試験。
  `firmware/logs/staircase-reverse-representative-2026-07-07T04-55-26-552Z.log`
- 負方向の安定判定で許容幅が常に10rpmになる問題を修正:
  `wheel_tolerance`を`abs(effective_target)`基準へ変更。
- 結果:
  - 全step `STEP_OK`、実機は終了後safe-idleをflash/verify/reset済み。
  - 直前1秒:
    - -40rpm: 平均 -42.39rpm、p-p 9.02rpm、角度誤差max 0.53°、scale 0%
    - -500rpm: 平均 -500.31rpm、p-p 1.90rpm、角度誤差max 0.62°、scale 0%
    - -1400rpm要求: `cmd`約 -1363rpm、実測平均 -1362.55rpm、p-p 2.26rpm、
      角度誤差max 0.70°、scale 0%
- 判断:
  - 逆転代表点でも問題なし。無負荷では正逆とも `|wheel rpm|=40〜約1360rpm` を
    `ωw, θs` 指令で制御できる状態。
  - 次は接地/拘束状態での温度・電流余裕・低速stick-slipの再評価。

## wheel 500rpm + steer +10deg 同時指令試験(2026-07-07)

- 接地試験ができないため、次段階として「`ωw`を出しながら`θs`を動かす」確認へ移行。
- 試験内容: 起動角から`θs=+10°`、同時に`ωw=500rpm`。長時間保持ハーネスを流用し、
  1stepのみ実行。
- 初回ログ: `firmware/logs/theta-step-wheel500-2026-07-07T05-01-36-470Z.log`
  - `θs=+10°` stepを入れた直後に、既存のstep内角度誤差6°/300ms FAILが働き、
    評価前に終了。角度step試験ではこのガードは不適切。
- 再試験:
  - `STEP_ANGLE_FAIL_DEG_MILLI`を一時的に12000へ緩和。
  - ログ: `firmware/logs/theta-step-wheel500-retry-2026-07-07T05-02-45-975Z.log`
  - `START: angle=185.186° target=195.186° wheelTarget=500`
  - `STEP_OK: target=500 cmd=500.000rpm measured=499.349rpm angleErr=0.156°`
  - 100msログ基準で、角度誤差は約0.9sで2°以内、約1.0sで1°以内/0.5°以内へ到達。
  - final-half wheel: 平均500.111rpm、p-p 9.914rpm、角度誤差max 0.771°、
    scale 0%、maxTemp 29°C。
- 判断:
  - 無負荷では`ωw=500rpm`を維持しながら`θs=+10°`へ収束できる。
  - 次は`ωw=500rpm`で`θs`を+10/-10/0へ往復させる、または低速/高速代表点
    (`ωw=40/1200rpm`)で同じ角度stepを確認する。

## wheel 500rpm + steer +90deg 切り分け試験(2026-07-07)

- ユーザー指摘: +10°/20°では角度変位が小さく、目視切り分けしにくい。
  `ωw=500rpm`のまま`θs=+90°`へ変更して試験。
- 試験1: `steer_min_rpm=2`のまま。
  `firmware/logs/theta90-wheel500-2026-07-07T05-10-13-158Z.log`
  - ログ上は約0.9sで角度誤差1°以内まで到達。
  - ただし終端で`steer_min_rpm=2`由来のリミットサイクルが出て、±2〜3°程度で揺れ、
    3秒安定判定に入れずtimeout。
- 試験2: `steer_min_rpm=0`へ変更。
  `firmware/logs/theta90-wheel500-nomin-2026-07-07T05-11-51-426Z.log`
  - `STEP_OK`。ログ上のAMT角は49.922° -> 138.516°付近へ約90°変化。
  - 約0.9sで1°以内、保持時は角度誤差0.1〜0.4°程度。
  - final-half wheel平均500.013rpm、p-p 6.845rpm、角度誤差max 0.439°、
    scale 0%、maxTemp 30°C。
- 重要な未解決点:
  - ユーザー目視ではステア変化が見えなかった。ログ上のAMT角は約90°変わっているため、
    「AMTが見ている軸」と「実際にステアとして見ている出力」の間にズレ/滑り/観察点違いが
    ある可能性がある。
  - 次は通電試験ではなく、無通電でステア出力を手で90°動かし、AMT角が同じだけ変わるかを
    確認する。AMTだけ変わって出力が変わらない場合は、機械結合/エンコーダ取付を点検する。

## wheel 500rpm定常 + steer 90deg刻み試験(2026-07-07)

- ユーザー提案により、wheel立ち上がり過渡を切り離すため、先に`ωw=500rpm, θs=base`
  で定常化してから、`θs=base+90/+180/+270/+0°`へ90°刻みでstepする試験に変更。
  step間で`unit_controller_reset()`は呼ばず、wheel状態と積分を維持。
- ログ: `firmware/logs/steer-90deg-steps-wheel500-2026-07-07T05-16-32-974Z.log`
- 結果:
  - step0 base: `STEP_OK`、final-half wheel平均500.08rpm、p-p 6.88rpm、角度誤差max 0.53°
  - step1 +90°: `STEP_OK`、final-half wheel平均500.01rpm、p-p 5.81rpm、角度誤差max 0.53°
  - step2 +180°: `STEP_OK`、final-half wheel平均499.85rpm、p-p 8.13rpm、角度誤差max 0.62°
  - step3 +270°: `STEP_OK`、final-half wheel平均500.03rpm、p-p 5.91rpm、角度誤差max 0.62°
  - step4 +0°: `STEP_OK`、ただしユーザーが最終stepでホイールに触れたため外乱あり。
    final-half wheel p-p 93rpmは速度制御評価から除外する。角度誤差は0.53°以内。
- 判断:
  - 少なくともstep0〜3では、`ωw=500rpm`定常中に90°刻みで`θs`を変更しても、
    AMT角ログ上は各目標へ収束し、wheel速度も維持できている。
  - ユーザー目視でもステア出力は良さそうとのこと。AMT角ログと物理ステア出力は概ね一致している
    扱いで次へ進める。ただし最終stepはホイール接触外乱ありのため速度評価から除外。

## wheel 40/1200rpm定常 + steer 90deg刻み試験(2026-07-07)

- 500rpmで成立した90°刻み試験を、低速代表40rpmと高速代表1200rpmへ展開。
- 40rpm: `firmware/logs/steer-90deg-steps-wheel40-2026-07-07T05-22-52-902Z.log`
  - 全step完走。角度は概ね追従し、step0〜3の角度誤差maxは0.7°以内。
  - ただしwheel p-pが大きい(step0 41rpm、step3 85rpm、step4 129rpm)。
    40rpmは機構摩擦を超える瞬間のオーバーシュート/stick-slip境界と判断。
  - 実用下限は40rpmではなく75rpmから扱う方針へ変更。
- 1200rpm: `firmware/logs/steer-90deg-steps-wheel1200-2026-07-07T05-27-36-868Z.log`
  - 全step `STEP_OK`、scale 0%。
  - step0 base: final-half wheel平均1202.65rpm、p-p 37.98rpm、角度誤差max 0.53°
    (立ち上がり/定常化込み)
  - step1 +90°: 平均1199.86rpm、p-p 3.60rpm、角度誤差max 0.70°
  - step2 +180°: 平均1200.25rpm、p-p 3.57rpm、角度誤差max 0.70°
  - step3 +270°: 平均1199.96rpm、p-p 3.54rpm、角度誤差max 0.70°
  - step4 +0°: 平均1200.15rpm、p-p 3.58rpm、角度誤差max 0.70°
  - maxTempは30°Cから36°Cまで上昇。
- 判断:
  - 実用域は暫定`|ωw| >= 75rpm`。
  - 1200rpm定常中の90°刻み`θs`変更は非常に安定。無負荷単体ユニットでは
    `ωw, θs`指令制御は成立。

## 中央CAN(FDCAN1)受信ログ準備(2026-07-07)

- NUCLEO-G474REの中央CAN用FDCAN1(PA11=RX/CN10-14、PA12=TX/CN10-12)に
  2個目のCANトランシーバを接続した前提で、ファームにFDCAN1初期化を追加。
- `CLOSED_LOOP_TEST_ENABLED=0`のsafe-idleのまま、FDCAN1で受信した全フレームをVCPへ
  `CENTRAL_RX id=... dlc=... data=...`として表示する。
- `0x100 + unitId(=1)`、DLC 8を`SET_TARGET`としてlittle-endian int32 x2で仮decodeし、
  `SET_TARGET_RX steer=... wheel=...`を表示する。まだ制御には接続しない。
  - byte0-3: `targetSteerMdeg`
  - byte4-7: `targetWheelRpmMilli`
- `docs/communication/COMMUNICATION_NAMING_AND_IDS.md`へSET_TARGETのlittle-endian規約を追記。
- Debugビルド成功後、実機へflash/verify/reset済み。最終状態はsafe-idle。
- CAN受信確認時に邪魔になるため、`run=0`の100ms周期ログは止め、従来テレメトリは
  `active`時のみ出すように変更。再ビルド・flash/verify/reset済み。

次:
1. PCのCANableから中央CANへ`0x101` DLC8を送信し、G474 VCPで`CENTRAL_RX`と
   `SET_TARGET_RX`が出ることを確認。
2. 受信確認後、enable/timeout付きで`SET_TARGET`を`unit_controller_set_target()`へ接続する。

## 中央CAN(CANable -> FDCAN1)受信確認(2026-07-07)

- PCにCANableをUSB-C接続。Windows上では追加シリアル`COM16`として認識、G474 VCPは`COM15`。
- CANable(SLCAN)へ以下を送信:
  - `C`
  - `S8` (1Mbps)
  - `O`
  - `t1018905F010020A10700`
- payloadは`SET_TARGET`:
  - steer=90000mdeg (`90 5F 01 00`)
  - wheel=500000rpm*1000 (`20 A1 07 00`)
- G474 VCP実測:
  - `CENTRAL_RX id=101 dlc=8 data=90 5f 1 0 20 a1 7 0`
  - `SET_TARGET_RX steer=90000 wheel=500000`
- 判断:
  - CANable -> 中央CANトランシーバ -> G474 FDCAN1(PA11/PA12)の受信経路は成立。
  - 次は`SET_TARGET`をenable/timeout付きで制御目標へ接続する。
